from typing import Optional, Union

import pydantic

from pydantic_apply import ApplyModelMixin
from pydantic_apply.utils import is_pydantic_apply_annotation


class SomeModel(ApplyModelMixin, pydantic.BaseModel):
    pass


class OtherModel(pydantic.BaseModel):
    pass


def test_direct_types():
    assert is_pydantic_apply_annotation(int) is False
    assert is_pydantic_apply_annotation(str) is False
    assert is_pydantic_apply_annotation(Union[int, str]) is False  # noqa: UP007
    assert is_pydantic_apply_annotation(int | str) is False
    assert is_pydantic_apply_annotation(OtherModel) is False

    assert is_pydantic_apply_annotation(ApplyModelMixin) is True
    assert is_pydantic_apply_annotation(SomeModel) is True


def test_optional_types():
    assert is_pydantic_apply_annotation(Optional[int]) is False  # noqa: UP045
    assert is_pydantic_apply_annotation(int | None) is False
    assert is_pydantic_apply_annotation(Optional[OtherModel]) is False  # noqa: UP045
    assert is_pydantic_apply_annotation(OtherModel | None) is False

    assert is_pydantic_apply_annotation(Optional[SomeModel]) is True  # noqa: UP045
    assert is_pydantic_apply_annotation(SomeModel | None) is True


def test_union_types():
    assert is_pydantic_apply_annotation(Union[int, None]) is False  # noqa: UP007
    assert is_pydantic_apply_annotation(int | None) is False
    assert is_pydantic_apply_annotation(Union[OtherModel, int]) is False  # noqa: UP007
    assert is_pydantic_apply_annotation(OtherModel | int) is False
    assert is_pydantic_apply_annotation(Union[OtherModel, None]) is False  # noqa: UP007
    assert is_pydantic_apply_annotation(OtherModel | None) is False

    assert is_pydantic_apply_annotation(Union[SomeModel, None]) is True  # noqa: UP007
    assert is_pydantic_apply_annotation(SomeModel | None) is True
    assert is_pydantic_apply_annotation(Union[SomeModel, int]) is True  # noqa: UP007
    assert is_pydantic_apply_annotation(SomeModel | int) is True
    assert is_pydantic_apply_annotation(Union[SomeModel, OtherModel]) is True  # noqa: UP007
    assert is_pydantic_apply_annotation(SomeModel | OtherModel) is True
