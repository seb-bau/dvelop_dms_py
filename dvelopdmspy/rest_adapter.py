import logging

import requests
import requests.packages
from typing import Dict

from jsonmerge import Merger

from dvelopdmspy.exceptions import DvelopDMSPyException
from dvelopdmspy.models import Result
from json import JSONDecodeError


class RestAdapter:
    logger = logging.getLogger(__name__)

    def __init__(self, hostname: str, api_key: str, repository: str,
                 logger: logging.Logger = None):

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
        self.url = f"https://{hostname}/dms/r/{self.repository}/"
        print(f"Repository {self.repository}")

    def get(self, endpoint: str, ep_params: Dict = None, base_url: str = None) -> Result:
        return self._do(http_method='GET', endpoint=endpoint, ep_params=ep_params, base_url=base_url)

    def post(self, endpoint: str, ep_params: Dict = None, data: Dict = None) -> Result:
        return self._do(http_method='POST', endpoint=endpoint, ep_params=ep_params, data=data)

    def delete(self, endpoint: str, ep_params: Dict = None, data: Dict = None) -> Result:
        return self._do(http_method='DELETE', endpoint=endpoint, ep_params=ep_params, data=data)

    def _do(self, http_method: str, endpoint: str, ep_params: Dict = None, data: Dict = None,
            base_url: str = None) -> Result:

        if base_url is None:
            base_url = self.url

        if ep_params is None:
            ep_params = {}

        ep_params["apiKey"] = self.api_key

        full_url = base_url + endpoint
        headers = {
            'Accept': 'application/hal+json',
            'Authorization': f'Bearer {self.api_key}'
        }
        log_line_pre = f"method={http_method}, url={full_url}"
        log_line_post = ', '.join((log_line_pre, "success={}, status_code={}, message={}"))
        merge_schema = {"mergeStrategy": "append"}
        merger = Merger(schema=merge_schema)

        try:
            self._logger.debug(msg=log_line_pre)
            response = requests.request(method=http_method, url=full_url, headers=headers, params=ep_params, json=data)
        except requests.exceptions.RequestException as e:
            self._logger.error(msg=(str(e)))
            raise DvelopDMSPyException("Request failed") from e

        try:
            if "items" in response.json().keys():
                data_out = response.json().get("items")
            else:
                data_out = response.json()
        except (ValueError, JSONDecodeError) as e:
            self._logger.error(msg=log_line_post.format(False, None, e))
            raise DvelopDMSPyException("Bad JSON in response") from e

        if "_links" in response.json().keys():
            while "next" in response.json()['_links']:
                response = requests.request(method=http_method,
                                            url=f"https://{self.host_base}{response.json()['_links']['next']['href']}",
                                            headers=headers)
                data_out = merger.merge(data_out, response.json()['items'])

        is_success = 200 <= response.status_code <= 299
        log_line = log_line_post.format(is_success, response.status_code, response.reason)
        if is_success:
            self._logger.debug(msg=log_line)
            return Result(response.status_code, message=response.reason, data=data_out)
        self._logger.error(msg=log_line)
        raise DvelopDMSPyException(f"{response.status_code}: {response.reason}")
