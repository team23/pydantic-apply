from packaging.version import Version
from pydantic.version import VERSION as PYDANTIC_VERSION

PYDANTIC_GE_V2_11 = Version(PYDANTIC_VERSION) >= Version("2.11")
