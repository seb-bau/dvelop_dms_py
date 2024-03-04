import json
import logging
import os
import humps

from typing import List
from dvelopdmspy.rest_adapter import RestAdapter
from dvelopdmspy.exceptions import DvelopDMSPyException
from dvelopdmspy.models import DmsDocument, Mappings, DmsUser, Category


def sanitize_doc(doc_dict) -> DmsDocument:
    doc = dict(humps.decamelize(doc_dict))
    doc["id_"] = doc.pop("id")
    doc["links"] = doc.pop("_links")
    t_doc = DmsDocument(**doc)
    return t_doc


def sanitize_user(user_dict) -> DmsUser:
    user = dict(humps.decamelize(user_dict))
    user["id_"] = user.pop("id")
    name_dict = user.pop("name")
    user["first_name"] = name_dict.get("given_name")
    user["last_name"] = name_dict.get("family_name")
    mail_list = user.pop("emails")
    if len(mail_list) == 0:
        user["email_address"] = None
    else:
        user["email_address"] = mail_list[0].get("value")

    t_user = DmsUser(**user)
    return t_user


class DvelopDmsPy:
    def __init__(self, hostname: str, api_key: str, repository: str = None,
                 logger: logging.Logger = None, user_agent: str = "DvelopDmsPy/1.0"):
        self._rest_adapter = RestAdapter(hostname, api_key, repository, logger, user_agent)
        self._source_mappings = self.get_mappings()

    def get_mappings(self) -> Mappings:
        t_result = self._rest_adapter.get(endpoint='source')
        t_result.data = dict(humps.decamelize(t_result.data))
        t_result.data["id_"] = t_result.data.pop("id")
        return Mappings(**t_result.data)

    def _get_property_key_from_name(self, property_name: str) -> str:
        for prop in self._source_mappings.properties:
            if prop.display_name.lower() == property_name.lower():
                return str(prop.key)

    def _get_category_key_from_name(self, category_name: str) -> str:
        for cat in self._source_mappings.categories:
            if cat.display_name.lower() == category_name.lower():
                return str(cat.key)

    def add_property(self, display_name: str, pvalue, prop_guid: str = None, pdict: dict = None) -> dict:
        if pdict is None:
            pdict = {}
        if prop_guid is None:
            t_key = self._get_property_key_from_name(display_name)
        else:
            t_key = prop_guid
        if type(pvalue) is not list:
            pvalue = [pvalue]
        pdict[t_key] = pvalue
        return pdict

    def add_upload_property(self, display_name: str, pvalue, prop_guid: str = None, plist: list = None) -> list:
        if plist is None:
            plist = []
        if prop_guid is None:
            t_key = self._get_property_key_from_name(display_name)
        else:
            t_key = prop_guid
        if type(pvalue) is not list:
            pvalue = [pvalue]
        plist.append({
            'key': t_key,
            'values': pvalue
        })
        return plist

    def add_category(self, display_name, plist: list = None, category_guid: str = None) -> list:
        if plist is None:
            plist = []
        if category_guid is None:
            t_key = self._get_category_key_from_name(display_name)
        else:
            t_key = category_guid
        plist.append(t_key)
        return plist

    def update_properties(self, doc_id: str, properties: list, alteration_msg: str = None, state_change: bool = True):
        if not alteration_msg:
            alteration_msg = "Ohne Kommentar"

        post_body = {
            'alterationText': alteration_msg,
            'sourceId': f'/dms/r/{self._rest_adapter.repository}/source',
            'sourceProperties': {
                'properties': properties
            }
        }
        update_doc_endpoint = f"o2m/{doc_id}"
        if state_change:
            update_doc_endpoint = f"{update_doc_endpoint}/v/current"
        result = self._rest_adapter.put(endpoint=update_doc_endpoint, data=post_body)
        if result.status_code > 299:
            raise DvelopDMSPyException(result.message)
        return True

    def set_state_editor(self, doc_id: str, editor_id: str = None, state_string: str = None,
                         alteration_msg: str = None):
        if not editor_id and not state_string:
            return True
        try:
            the_doc: DmsDocument
            the_doc = self.get_documents(doc_id=doc_id)[0]
        except (TypeError, IndexError) as e:
            raise DvelopDMSPyException(str(e))

        if not editor_id:
            # Wenn kein Editor genannt wurde, soll der aktuelle beibehalten werden
            editor_id = the_doc.editor
        if not state_string:
            # Wenn kein State genannt wurde, soll der aktuelle beibehalten werden
            state_string = the_doc.state
        if not alteration_msg:
            alteration_msg = "changed state and/or editor by script"

        props = self.add_upload_property(display_name="", pvalue=editor_id, prop_guid="property_editor")
        props = self.add_upload_property(display_name="", pvalue=state_string, prop_guid="property_state", plist=props)
        return self.update_properties(doc_id=doc_id, properties=props, alteration_msg=alteration_msg)

    def archive_file(self,
                     filepath: str,
                     category_id: str,
                     properties: list[dict],
                     doc_id: str = None,
                     alteration_msg: str = None) -> str | bool:
        # Blob Upload
        blob_endpoint = "blob/chunk/"
        result = self._rest_adapter.post(endpoint=blob_endpoint, binary_upload=True, upload_file_path=filepath)
        if result.status_code != 201 or "location" not in result.headers:
            raise DvelopDMSPyException("BLOB upload failed. No blob location detected")
        blob_location = result.headers["location"]

        # Archivdokument erstellen und mit Blob verbinden
        blob_to_doc_endpoint = "o2m"
        if doc_id is not None:
            blob_to_doc_endpoint = f"{blob_to_doc_endpoint}/{doc_id}"
            if alteration_msg is None or len(alteration_msg) == 0:
                alteration_msg = "dvelopdmspy: New version"
        else:
            alteration_msg = None

        release_property = {
            'key': 'property_state',
            'values': [
                'Release'
            ]
        }
        properties.append(release_property)

        post_body = {
            'filename': os.path.basename(filepath),
            'sourceCategory': category_id,
            'sourceId': f'/dms/r/{self._rest_adapter.repository}/source',
            'contentLocationUri': blob_location,
            'sourceProperties': {
                'properties': properties
            }
        }

        if alteration_msg is not None:
            post_body["alterationText"] = alteration_msg
            result = self._rest_adapter.put(endpoint=blob_to_doc_endpoint, data=post_body)
        else:
            result = self._rest_adapter.post(endpoint=blob_to_doc_endpoint, data=post_body)
        if result.status_code > 299:
            raise DvelopDMSPyException(result.message)
        try:
            t_loc = result.headers.get("Location")
            t_doc_id = t_loc.split('?')[0].split('/')[-1]
        except (KeyError, ValueError, AttributeError):
            t_doc_id = "unknown"

        return t_doc_id

    def get_documents(self,
                      properties: dict = None,
                      categories: list = None,
                      limit: int = None,
                      doc_id: str = None) -> List[DmsDocument]:
        ret_docs = []
        params = {
            "sourceid": f"/dms/r/{self._rest_adapter.repository}/source"
        }
        if properties is not None:
            params["sourceproperties"] = json.dumps(properties)

        if categories is not None:
            params["sourcecategories"] = json.dumps(categories)

        # Wurde eine doc_id angegeben, brauchen wir keinen Recherche
        if doc_id is not None:
            endpoint = f"o2m/{doc_id}"
        else:
            endpoint = "srm"

        result = self._rest_adapter.get(endpoint=endpoint, ep_params=params, limit=limit)
        if type(result.data) is list:
            for doc in result.data:
                t_doc = sanitize_doc(doc)
                ret_docs.append(t_doc)
        else:
            t_doc = sanitize_doc(result.data)
            ret_docs.append(t_doc)

        return ret_docs

    def get_users(self) -> List[DmsUser]:
        ret_users = []
        endpoint = "scim/Users"
        result = self._rest_adapter.get_identity(endpoint=endpoint)
        resources = result.data.get("resources")
        for entry in resources:
            t_user = sanitize_user(entry)
            ret_users.append(t_user)
        return ret_users

    def get_categories(self) -> List[Category]:
        return self._source_mappings.categories

    def key_to_display_name(self, key) -> str:
        if type(key) is list:
            for tk in key:
                if len(tk) > 10:
                    key = tk
                    break
        for prop in self._source_mappings.properties:
            if str(prop.key) == key:
                return prop.display_name

        for cat in self._source_mappings.categories:
            if str(cat.key) == key:
                return cat.display_name

        return ""

    def download_doc_blob(self, doc_id: str, dest_file: str, dl_href: str = None) -> bool:
        # Wurde die Funktion aus einem Dokument heraus aufgerufen, kennen wir den Pfad zum Blob bereits
        if dl_href is None:
            t_docs = self.get_documents(doc_id=doc_id)
            if len(t_docs) == 0:
                raise DvelopDMSPyException("Document not found.")
            t_doc = t_docs[0]
            dl_href = t_doc.links.mainblobcontent

        host_base = f"https://{self._rest_adapter.host_base}"
        result = self._rest_adapter.get(endpoint=dl_href, base_url=host_base, binary=True)

        with open(dest_file, 'wb') as out_file:
            out_file.write(result.raw.content)

        return True

    def get_property_value(self, doc_obj: DmsDocument, prop_display_name: str):
        prop_key = self._get_property_key_from_name(prop_display_name)
        for prop in doc_obj.source_properties:
            if prop.key == prop_key:
                if prop.values is None:
                    return prop.value
                else:
                    return prop.values

    def get_property_value2(self, doc_obj: DmsDocument, prop_display_name: str = None, prop_guid: str = None) -> dict:
        ret_dict = {}
        if prop_guid is None:
            prop_guid = self._get_property_key_from_name(prop_display_name)
        for prop in doc_obj.source_properties:
            if prop.key == prop_guid:
                if prop.values is not None:
                    ret_dict["values"] = prop.values
                if prop.value is not None:
                    ret_dict["value"] = prop.value
                if prop.display_value is not None:
                    ret_dict["display_value"] = prop.display_value
                break
        return ret_dict
