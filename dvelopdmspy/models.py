from typing import List, Dict, Optional
from uuid import UUID
from enum import Enum


class Result:
    def __init__(self, status_code: int, message: str = '', data: List[Dict] = None):
        self.status_code = int(status_code)
        self.message = str(message)
        self.data = data if data else []


class Links:
    links_self: str
    preview_readonly: str
    delete_with_reason: str
    mainblobcontent: str
    pdfblobcontent: str
    update_with_content: str
    update: str
    versions: str
    display_version: str
    notes: str

    def __init__(self, links_self: Dict,
                 preview_readonly: Dict,
                 delete_with_reason: Dict,
                 mainblobcontent: Dict,
                 pdfblobcontent: Dict,
                 update_with_content: Dict,
                 update: Dict,
                 versions: Dict,
                 display_version: Dict,
                 notes: Dict) -> None:
        self.links_self = links_self.get("href")
        self.preview_readonly = preview_readonly.get("href")
        self.delete_with_reason = delete_with_reason.get("href")
        self.mainblobcontent = mainblobcontent.get("href")
        self.pdfblobcontent = pdfblobcontent.get("href")
        self.update_with_content = update_with_content.get("href")
        self.update = update.get("href")
        self.versions = versions.get("href")
        self.display_version = display_version.get("href")
        self.notes = notes.get("href")


class SourceProperty:
    key: str
    value: str
    values: Optional[list]
    is_multi_value: bool
    display_value: Optional[str]

    def __init__(self, key: str, value: str, is_multi_value: bool, display_value: Optional[str] = None,
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

    def __init__(self, links: Links, id_: str, source_properties: List[Dict],
                 source_categories: List[str]) -> None:
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
    key: str
    type_: TypeEnum
    display_name: str

    def __init__(self, key: str, type_: TypeEnum, display_name: str) -> None:
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
