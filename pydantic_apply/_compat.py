from typing import Any, Dict, Optional, Set

import pydantic
from pydantic.fields import FieldInfo
from pydantic.version import VERSION as PYDANTIC_VERSION

PYDANTIC_V1 = PYDANTIC_VERSION.startswith("1.")
PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")


if PYDANTIC_V1:  # pragma: no cover
    class PydanticCompat:  # noqa: F811
        obj: Optional[pydantic.BaseModel]

        def __init__(
            self,
            obj: Optional[pydantic.BaseModel] = None,
        ) -> None:
            self.obj = obj

        @property
        def model_fields(self) -> Dict[str, FieldInfo]:
            return self.obj.__fields__

        @property
        def __pydantic_fields_set__(self) -> Set[str]:
            return self.obj.__fields_set__

        def get_model_field_info_annotation(self, model_field: FieldInfo) -> type:
            return model_field.type_

        def get_model_config_value(self, key: str) -> Any:
            return getattr(self.obj.__config__, key)

        def set_model_config_value(self, key: str, value: Any) -> None:
            setattr(self.obj.__config__, key, value)

        def model_copy(self, **kwargs: Any) -> pydantic.BaseModel:
            return self.obj.copy(**kwargs)

        def model_dump(self, **kwargs: Any) -> pydantic.BaseModel:
            return self.obj.dict(**kwargs)


if PYDANTIC_V2:  # pragma: no cover
    class PydanticCompat:  # noqa: F811
        obj: Optional[pydantic.BaseModel]

        def __init__(
            self,
            obj: Optional[pydantic.BaseModel] = None,
        ) -> None:
            self.obj = obj

        @property
        def model_fields(self) -> Dict[str, FieldInfo]:
            return self.obj.model_fields

        @property
        def __pydantic_fields_set__(self) -> Set[str]:
            return self.obj.__pydantic_fields_set__

        def get_model_field_info_annotation(self, model_field: FieldInfo) -> type:
            return model_field.annotation

        def get_model_config_value(self, key: str) -> Any:
            return self.obj.model_config.get(key, None)

        def set_model_config_value(self, key: str, value: Any) -> None:
            self.obj.model_config[key] = value

        def model_copy(self, **kwargs: Any) -> pydantic.BaseModel:
            return self.obj.model_copy(**kwargs)

        def model_dump(self, **kwargs: Any) -> pydantic.BaseModel:
            return self.obj.model_dump(**kwargs)
