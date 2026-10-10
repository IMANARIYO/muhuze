from enum import StrEnum


class AttributeDataType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"  # one of the attribute's options
    MULTI_SELECT = "multi_select"  # any of the attribute's options


# Only these types have a list of allowed values.
OPTION_DATA_TYPES = frozenset({AttributeDataType.SELECT, AttributeDataType.MULTI_SELECT})

CATEGORY_NAME_MAX_LENGTH = 100
CATEGORY_SLUG_MAX_LENGTH = 120
CATEGORY_DESCRIPTION_MAX_LENGTH = 500
ATTRIBUTE_NAME_MAX_LENGTH = 100
ATTRIBUTE_CODE_MAX_LENGTH = 50
ATTRIBUTE_UNIT_MAX_LENGTH = 20
OPTION_VALUE_MAX_LENGTH = 100
SEARCH_QUERY_MAX_LENGTH = 100
