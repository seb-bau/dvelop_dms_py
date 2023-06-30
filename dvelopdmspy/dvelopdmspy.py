import json
import logging
import humps
import pickle
from dvelopdmspy.rest_adapter import RestAdapter
from dvelopdmspy.exceptions import DvelopDMSPyException
from dvelopdmspy.models import *


class DvelopDmsPy:
    def __init__(self, hostname: str, api_key: str, repository: str = None,
                 logger: logging.Logger = None):
        self._rest_adapter = RestAdapter(hostname, api_key, repository, logger)
        self._source_mappings = self.get_mappings()

    def get_mappings(self) -> Mappings:
        t_result = self._rest_adapter.get(endpoint='source')
        t_result.data = dict(humps.decamelize(t_result.data))
        t_result.data["id_"] = t_result.data.pop("id")
        return Mappings(**t_result.data)

    def _get_property_key_from_name(self, property_name: str) -> str:
        for prop in self._source_mappings.properties:
            if prop.display_name.lower() == property_name.lower():
                return prop.key

    def add_search_property(self, display_name: str, pvalue, pdict: dict = None) -> dict:
        if pdict is None:
            pdict = {}
        t_key = self._get_property_key_from_name(display_name)
        if type(pvalue) != list:
            pvalue = [pvalue]
        pdict[t_key] = pvalue
        return pdict

    def get_documents(self,
                      properties: dict[SearchProperty] = None,
                      categories: list[str] = None) -> List[DmsDocument]:
        ret_docs = []
        params = {
            "sourceid": f"/dms/r/{self._rest_adapter.repository}/source"
        }
        if properties is not None:
            params["sourceproperties"] = json.dumps(properties)
        print(params.get("sourceproperties"))

        result = self._rest_adapter.get(endpoint="srm", ep_params=params)
        for doc in result.data:
            doc = dict(humps.decamelize(doc))
            doc["id_"] = doc.pop("id")
            doc["links"] = doc.pop("_links")
            t_doc = DmsDocument(**doc)
            ret_docs.append(t_doc)

        return ret_docs
