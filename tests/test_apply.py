from typing import Optional

import pydantic
import pytest

from pydantic_apply.apply import ApplyModelMixin


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

    model_config = pydantic.ConfigDict(populate_by_name=True)


class ApplyModelWithValidation(ApplyModel):
    @pydantic.model_validator(mode="before")
    def _validate(cls, data):
        if data.get("a", None) == data.get("b", None):
            raise ValueError("a and b must not be equal")
        return data

    model_config = pydantic.ConfigDict(validate_assignment=True)


class ApplyModelWithAfterValidation(ApplyModel):
    @pydantic.model_validator(mode="after")
    def _validate(self):
        if self.a == self.b:
            raise ValueError("a and b must not be equal")
        return self

    model_config = pydantic.ConfigDict(validate_assignment=True)


class PatchModel(pydantic.BaseModel):
    a: Optional[int] = None
    b: Optional[int] = None


def test_apply_with_dict():
    obj = ApplyModel(a=1, b=2)

    obj.model_apply({"a": 2})

    assert obj.a == 2
    assert obj.b == 2

    obj.model_apply({"b": 1})

    assert obj.a == 2
    assert obj.b == 1


def test_apply_with_patch_model():
    obj = ApplyModel(a=1, b=2)

    obj.model_apply(PatchModel(a=2))

    assert obj.a == 2
    assert obj.b == 2

    obj.model_apply(PatchModel(b=1))

    assert obj.a == 2
    assert obj.b == 1


def test_apply_works_with_aliases():
    obj = ApplyModel(a=1, b=2)

    obj.model_apply({"aliasA": 2})

    assert obj.a == 2
    assert obj.b == 2

    obj.model_apply({"aliasB": 1})

    assert obj.a == 2
    assert obj.b == 1


def test_apply_will_handle_validate_assignment():
    obj = ApplyModelWithValidation(a=1, b=2)

    obj.model_apply({"a": 2, "b": 1})

    assert obj.a == 2
    assert obj.b == 1


def test_apply_will_handle_validate_assignment_after_direct_access():
    """
    Test that model_apply works with initialized setattr cache.

    This is only necessary starting from pydantic v2.11, since when
    setattr uses a chache which stores the validate_assignment setting.
    """

    obj = ApplyModelWithAfterValidation(a=1, b=2)
    obj.a = 3  # First apply both values to initialize __pydantic_setattr_handlers__
    obj.b = 4

    # model_apply temporarily needs to disable the cache to skip the assignment validation
    obj.model_apply({"a": 4, "b": 3})

    assert obj.a == 4
    assert obj.b == 3


def test_apply_will_handle_trigger_errors_with_validate_assignment():
    obj = ApplyModelWithValidation(a=1, b=2)

    with pytest.raises(pydantic.ValidationError):
        obj.model_apply({"a": 3, "b": 3})


def test_apply_will_handle_inner_normal_model():
    obj = ApplyModel(a=1, b=2, inner=InnerModel(a=1))

    obj.model_apply({
        "inner": InnerModel(b=1),
    })

    assert obj.inner.a is None
    assert obj.inner.b == 1


def test_apply_will_handle_inner_apply_model():
    obj = ApplyModel(a=1, b=2, inner_with_apply=InnerWithApplyModel(a=1))
    inner_with_apply = obj.inner_with_apply

    obj.model_apply({
        "inner_with_apply": PatchModel(b=1),
    })

    assert obj.inner_with_apply.a == 1
    assert obj.inner_with_apply.b == 1
    assert inner_with_apply is obj.inner_with_apply


def test_apply_will_handle_inner_apply_model_with_validate_assignment():
    obj = ApplyModelWithValidation(a=1, b=2, inner_with_apply=InnerWithApplyModel(a=1))
    # Get the value of inner_with_apply afterwards because it might already have changed once
    inner_with_apply = obj.inner_with_apply

    obj.model_apply({
        "inner_with_apply": PatchModel(b=1),
    })

    assert obj.inner_with_apply.a == 1
    assert obj.inner_with_apply.b == 1
    # When using validate_assignment, the inner model is copied
    assert inner_with_apply is not obj.inner_with_apply


def test_apply_compatibility_works():
    obj = ApplyModel(a=1, b=2)

    with pytest.warns(DeprecationWarning):
        obj.apply({"a": 2})

    assert obj.a == 2
    assert obj.b == 2
