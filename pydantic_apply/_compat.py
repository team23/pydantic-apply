from typing import Any

import pydantic
from packaging.version import Version
from pydantic.fields import FieldInfo
from pydantic.version import VERSION as PYDANTIC_VERSION

PYDANTIC_V1 = PYDANTIC_VERSION.startswith("1.")
PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")
PYDANTIC_GE_V2_11 = Version(PYDANTIC_VERSION) >= Version("2.11")


if PYDANTIC_V1:  # pragma: no cover
    class PydanticCompat:  # type: ignore
        obj: pydantic.BaseModel

        def __init__(
            self,
            obj: pydantic.BaseModel,
        ) -> None:
            self.obj = obj

        @property
        def model_fields(self) -> dict[str, FieldInfo]:
            return self.obj.__fields__

        @property
        def __pydantic_fields_set__(self) -> set[str]:
            return self.obj.__fields_set__

        def get_model_field_info_annotation(self, model_field: FieldInfo) -> type:
            return model_field.type_  # type: ignore

        def get_model_config_value(self, key: str) -> Any:
            return getattr(self.obj.__config__, key)  # type: ignore

        def set_model_config_value(self, key: str, value: Any) -> None:
            setattr(self.obj.__config__, key, value)  # type: ignore

        def model_copy(self, **kwargs: Any) -> pydantic.BaseModel:
            return self.obj.copy(**kwargs)

        def model_dump(self, **kwargs: Any) -> dict[str, Any]:
            return self.obj.dict(**kwargs)


elif PYDANTIC_V2:  # pragma: no cover
    class PydanticCompat:  # type: ignore
        obj: pydantic.BaseModel

        def __init__(
            self,
            obj: pydantic.BaseModel,
        ) -> None:
            self.obj = obj

        @property
        def model_fields(self) -> dict[str, FieldInfo]:
            return self.obj.__class__.model_fields

        @property
        def __pydantic_fields_set__(self) -> set[str]:
            return self.obj.__pydantic_fields_set__

        def get_model_field_info_annotation(self, model_field: FieldInfo) -> type[Any]:
            if model_field.annotation is None:
                raise RuntimeError("model field has not typing annotation")
            return model_field.annotation

        def get_model_config_value(self, key: str) -> Any:
            return self.obj.model_config.get(key, None)

        def set_model_config_value(self, key: str, value: Any) -> None:
            self.obj.model_config[key] = value  # type: ignore

        def model_copy(self, **kwargs: Any) -> pydantic.BaseModel:
            return self.obj.model_copy(**kwargs)

        def model_dump(self, **kwargs: Any) -> dict[str, Any]:
            return self.obj.model_dump(**kwargs)
