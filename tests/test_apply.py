from typing import Optional

import pydantic
import pytest

from pydantic_apply._compat import PYDANTIC_V1, PYDANTIC_V2
from pydantic_apply.apply import ApplyModelMixin

if PYDANTIC_V2:
    from pydantic import ConfigDict


class InnerModel(pydantic.BaseModel):
    a: Optional[int] = None
    b: Optional[int] = None


class InnerWithApplyModel(ApplyModelMixin, pydantic.BaseModel):
    a: Optional[int] = None
    b: Optional[int] = None


class ApplyModel(ApplyModelMixin, pydantic.BaseModel):
    a: int = pydantic.Field(..., alias="aliasA")
    b: int = pydantic.Field(..., alias="aliasB")

    inner: Optional[InnerModel] = None
    inner_with_apply: Optional[InnerWithApplyModel] = None

    if PYDANTIC_V1:
        class Config:
            allow_population_by_field_name = True

    if PYDANTIC_V2:
        model_config = ConfigDict(populate_by_name=True)


class ApplyModelWithValidation(ApplyModel):
    @pydantic.root_validator(pre=True)
    def _validate(cls, values):
        if values.get("a", None) == values.get("b", None):
            raise ValueError("a and b must not be equal")
        return values

    if PYDANTIC_V1:
        class Config:
            validate_assignment = True

    if PYDANTIC_V2:
        model_config = ConfigDict(validate_assignment=True)


class PatchModel(pydantic.BaseModel):
    a: Optional[int] = None
    b: Optional[int] = None


def test_apply_with_dict():
    obj = ApplyModel(a=1, b=2)

    obj.apply({"a": 2})

    assert obj.a == 2
    assert obj.b == 2

    obj.apply({"b": 1})

    assert obj.a == 2
    assert obj.b == 1


def test_apply_with_patch_model():
    obj = ApplyModel(a=1, b=2)

    obj.apply(PatchModel(a=2))

    assert obj.a == 2
    assert obj.b == 2

    obj.apply(PatchModel(b=1))

    assert obj.a == 2
    assert obj.b == 1


def test_apply_works_with_aliases():
    obj = ApplyModel(a=1, b=2)

    obj.apply({"aliasA": 2})

    assert obj.a == 2
    assert obj.b == 2

    obj.apply({"aliasB": 1})

    assert obj.a == 2
    assert obj.b == 1


def test_apply_will_handle_validate_assignment():
    obj = ApplyModelWithValidation(a=1, b=2)

    obj.apply({"a": 2, "b": 1})

    assert obj.a == 2
    assert obj.b == 1


def test_apply_will_handle_trigger_errors_with_validate_assignment():
    obj = ApplyModelWithValidation(a=1, b=2)

    with pytest.raises(pydantic.ValidationError):
        obj.apply({"a": 3, "b": 3})


def test_apply_will_handle_inner_normal_model():
    obj = ApplyModel(a=1, b=2, inner=InnerModel(a=1))

    obj.apply({
        "inner": InnerModel(b=1),
    })

    assert obj.inner.a is None
    assert obj.inner.b == 1


def test_apply_will_handle_inner_apply_model():
    obj = ApplyModel(a=1, b=2, inner_with_apply=InnerWithApplyModel(a=1))
    inner_with_apply = obj.inner_with_apply

    obj.apply({
        "inner_with_apply": PatchModel(b=1),
    })

    assert obj.inner_with_apply.a == 1
    assert obj.inner_with_apply.b == 1
    assert inner_with_apply is obj.inner_with_apply


def test_apply_will_handle_inner_apply_model_with_validate_assignment():
    obj = ApplyModelWithValidation(a=1, b=2, inner_with_apply=InnerWithApplyModel(a=1))
    inner_with_apply = obj.inner_with_apply

    obj.apply({
        "inner_with_apply": PatchModel(b=1),
    })

    assert obj.inner_with_apply.a == 1
    assert obj.inner_with_apply.b == 1
    # When using validate_assignment, the inner model is copied
    assert inner_with_apply is not obj.inner_with_apply
