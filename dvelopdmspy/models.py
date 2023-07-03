from typing import List, Dict, Optional
from uuid import UUID
from enum import Enum

import requests


class Result:
    def __init__(self, status_code: int, message: str = '', data: List[Dict] = None, raw: requests.Response = None):
        self.status_code = int(status_code)
        self.message = str(message)
        self.data = data if data else []
        self.raw = raw


class Links:
    links_self: str
    preview_readonly: Optional[str]
    delete_with_reason: Optional[str]
    mainblobcontent: str
    pdfblobcontent: Optional[str]
    update_with_content: Optional[str]
    update: Optional[str]
    versions: str
    display_version: str
    notes: str

    def __init__(self, links_self: Dict,
                 mainblobcontent: Dict,

                 versions: Dict,
                 display_version: Dict,
                 notes: Dict,
                 pdfblobcontent: Dict = None,
                 update_with_content: Dict = None,
                 delete_with_reason: Dict = None,
                 update: Dict = None,
                 preview_readonly: Dict = None) -> None:
        self.links_self = links_self.get("href")
        if preview_readonly is not None:
            self.preview_readonly = preview_readonly.get("href")
        else:
            self.preview_readonly = None
        if update_with_content is not None:
            self.delete_with_reason = delete_with_reason.get("href")
        else:
            self.delete_with_reason = None
        self.mainblobcontent = mainblobcontent.get("href")
        if pdfblobcontent is not None:
            self.pdfblobcontent = pdfblobcontent.get("href")
        else:
            self.pdfblobcontent = None
        if update_with_content is not None:
            self.update_with_content = update_with_content.get("href")
        else:
            self.update_with_content = None
        if update is not None:
            self.update = update.get("href")
        else:
            self.update = None
        self.versions = versions.get("href")
        self.display_version = display_version.get("href")
        self.notes = notes.get("href")


class SourceProperty:
    key: str
    value: str
    values: Optional[list]
    is_multi_value: Optional[bool]
    display_value: Optional[str]

    def __init__(self, key: str, value: str, is_multi_value: bool = None, display_value: Optional[str] = None,
                 values: list = None) -> None:
        self.key = key
        self.value = value
        self.is_multi_value = is_multi_value
        self.display_value = display_value
        self.values = values


class SearchProperty:
    key: str
    values: list

    def __init__(self, key: str, values: list):
        self.key = key
        self.values = values


class DmsDocument:
    links: Links
    id_: str
    source_properties: List[SourceProperty]
    source_categories: List[str]

    def __init__(self, links: Dict, id_: str, source_properties: List[Dict],
                 source_categories: List[str]) -> None:
        if links is not None:
            links["links_self"] = links.pop("self")
            links = Links(**links)
        self.links = links
        self.id_ = id_
        tsource_properties = []
        for source_property in source_properties:
            tprop = SourceProperty(**source_property)
            tsource_properties.append(tprop)
        self.source_properties = tsource_properties
        self.source_categories = source_categories


class Category:
    key: UUID
    display_name: str

    def __init__(self, key: UUID, display_name: str) -> None:
        self.key = key
        self.display_name = display_name


class TypeEnum(Enum):
    COLOR_CODE = "ColorCode"
    DATE = "Date"
    DATE_TIME = "DateTime"
    DOUBLE = "Double"
    MONEY = "Money"
    STRING = "String"


class Property:
    key: UUID
    type_: TypeEnum
    display_name: str

    def __init__(self, key: UUID, type_: TypeEnum, display_name: str) -> None:
        self.key = key
        self.type_ = type_
        self.display_name = display_name


class Mappings:
    id_: str
    display_name: str
    properties: List[Property]
    categories: List[Category]

    def __init__(self, id_: str, display_name: str, properties: List[Dict], categories: List[Dict]) -> None:
        self.id_ = id_
        self.display_name = display_name
        props = []
        for prop in properties:
            prop["type_"] = prop.pop("type")
            props.append(Property(**prop))
        self.properties = props
        cats = []
        for cat in categories:
            cats.append(Category(**cat))
        self.categories = cats
