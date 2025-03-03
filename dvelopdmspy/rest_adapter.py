import logging

import requests
import requests.packages
import requests.utils
import requests_cache
from typing import Dict

from jsonmerge import Merger

from dvelopdmspy.exceptions import DvelopDMSPyException
from dvelopdmspy.models import Result
from json import JSONDecodeError


class RestAdapter:
    logger = logging.getLogger(__name__)

    def __init__(self, hostname: str, api_key: str, repository: str,
                 logger: logging.Logger = None, user_agent: str = None):

        requests_cache.install_cache(backend='memory', expire_after=10800)
        if user_agent is None:
            self.user_agent = requests.utils.default_headers().get('User-Agent')
        else:
            self.user_agent = user_agent
        self._logger = logger or logging.getLogger(__name__)
        self.host_base = hostname
        self.repolist_url = f"https://{hostname}/dms/r/"
        self.api_key = api_key

        # Wird kein Repository angegeben, wird das erste ausgelesen und gesetzt
        if repository is None:
            t_repos = self.get(endpoint="", base_url=self.repolist_url)
            self.repository = t_repos.data.get("repositories")[0].get("id")
        else:
            self.repository = repository

        self.config_url = f"https://{hostname}/dmsconfig/r/{self.repository}/"
        self.identity_url = f"https://{hostname}/identityprovider/"
        self.url = f"https://{hostname}/dms/r/{self.repository}/"

    def get_identity(self, endpoint: str):
        return self.get(endpoint=endpoint, base_url=self.identity_url)

    def get(self, endpoint: str, ep_params: Dict = None, base_url: str = None, binary: bool = False,
            limit: int = None) -> Result:
        return self._do(http_method='GET', endpoint=endpoint, ep_params=ep_params, base_url=base_url, binary=binary,
                        limit=limit)

    def post(self, endpoint: str, ep_params: Dict = None, data: Dict = None, binary_upload: bool = False,
             upload_file_path: str = None) -> Result:
        return self._do(http_method='POST', endpoint=endpoint, ep_params=ep_params, data=data,
                        binary_upload=binary_upload, upload_file_path=upload_file_path)

    def put(self, endpoint: str, ep_params: Dict = None, data: Dict = None, binary_upload: bool = False,
            upload_file_path: str = None) -> Result:
        return self._do(http_method='PUT', endpoint=endpoint, ep_params=ep_params, data=data,
                        binary_upload=binary_upload, upload_file_path=upload_file_path)

    def delete(self, endpoint: str, ep_params: Dict = None, data: Dict = None) -> Result:
        return self._do(http_method='DELETE', endpoint=endpoint, ep_params=ep_params, data=data)

    def _do(self, http_method: str, endpoint: str, ep_params: Dict = None, data: Dict = None,
            base_url: str = None, binary: bool = False, limit: int = None, binary_upload: bool = False,
            upload_file_path: str = None) -> Result:

        if base_url is None:
            base_url = self.url

        if ep_params is None:
            ep_params = {}

        ep_params["apiKey"] = self.api_key

        full_url = base_url + endpoint
        headers = {
            'User-Agent': self.user_agent,
            'Authorization': f'Bearer {self.api_key}'
        }

        if binary:
            headers['Accept'] = 'application/octet-stream'
        else:
            headers['Accept'] = 'application/hal+json'

        if http_method == 'POST':
            headers['Origin'] = f'https://{self.host_base}'

        blobdata = None
        if binary_upload:
            headers['Content-Type'] = 'application/octet-stream'

            try:
                with open(upload_file_path, 'rb') as f:
                    blobdata = f.read()
            except IOError as e:
                self._logger.debug(msg=(str(e)))
                raise DvelopDMSPyException("Blob upload failed") from e

        log_line_pre = f"method={http_method}, url={full_url}"
        log_line_post = ', '.join((log_line_pre, "success={}, status_code={}, message={}"))
        merge_schema = {"mergeStrategy": "append"}
        merger = Merger(schema=merge_schema)

        try:
            self._logger.debug(msg=log_line_pre)
            response = requests.request(method=http_method, url=full_url, headers=headers, params=ep_params, json=data,
                                        data=blobdata)
        except requests.exceptions.RequestException as e:
            self._logger.debug(msg=(str(e)))
            raise DvelopDMSPyException("Request failed") from e

        if not binary and not binary_upload:
            data_out = None
            try:
                jsresp = response.json()
                data_out = jsresp
                try:
                    if "items" in jsresp.keys():
                        data_out = jsresp.get("items")
                    else:
                        data_out = jsresp
                except (ValueError, JSONDecodeError) as e:
                    self._logger.debug(msg=log_line_post.format(False, None, e))
                    raise DvelopDMSPyException(f"Bad JSON in response --> {response.text}") from e

                if "_links" in jsresp.keys():
                    doc_count = len(data_out)
                    while "next" in response.json()['_links']:
                        if limit is not None and doc_count >= limit:
                            break
                        response = requests.request(method=http_method,
                                                    url=f"https://"
                                                        f"{self.host_base}{response.json()['_links']['next']['href']}",
                                                    headers=headers)
                        data_out = merger.merge(data_out, response.json()['items'])
                        doc_count = len(data_out)
            except JSONDecodeError:
                pass
        else:
            data_out = None

        is_success = 200 <= response.status_code <= 299
        log_line = log_line_post.format(is_success, response.status_code, response.reason)
        if is_success:
            self._logger.debug(msg=log_line)
            if binary:
                raw = response
            else:
                raw = None
            return Result(response.status_code, message=response.reason, data=data_out, raw=raw,
                          headers=response.headers)
        self._logger.debug(msg=log_line)
        raise DvelopDMSPyException(f"{response.status_code}: {response.reason} --> {response.text}")
