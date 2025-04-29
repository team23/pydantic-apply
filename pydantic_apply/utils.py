from contextlib import contextmanager
from typing import Any, Union, get_args, get_origin

import pydantic_apply

from ._compat import PYDANTIC_GE_V2_11, PydanticCompat


def is_pydantic_apply_annotation(annotation: type) -> bool:
    """Returns True if the given annotation is a ApplyModelMixin annotation."""

    # if annotation is an ApplyModelMixin everything is easy
    if (
        isinstance(annotation, type)
        and issubclass(annotation, pydantic_apply.ApplyModelMixin)
    ):
        return True

    # Otherwise we may need to handle typing arguments
    origin = get_origin(annotation)
    if origin is Union:
        # Note: This includes Optional, as Optional[...] is just Union[..., None]
        return any(
            is_pydantic_apply_annotation(arg)
            for arg in get_args(annotation)
        )

    # If we did not detect an ApplyModelMixin annotation, return False
    return False


def prepare_validate_assignment_config(
    self_compat: PydanticCompat,
    state_cache: dict[str, Any],
    prepared_changes: dict[str, Any],
) -> None:
    """
    Create a temporary model to validate and prepare the values.
    """

    had_validate_assignment = self_compat.get_model_config_value("validate_assignment")
    state_cache["validate_assignment"] = had_validate_assignment
    if had_validate_assignment:
        # Disable validation on assignment so we can apply the whole set of
        # changes without validation problems while the data changes. This
        # is necessary as validators may depend on other fields. When we change
        # the fields one by one, the validators may fail as the temporary
        # combination of two values will not validate. But the validator might
        # have passed when we would have had the chance to set both values.
        self_compat.set_model_config_value("validate_assignment", False)

        # Run validation as if all changes were applied. We do this by creating
        # a new (temporary) instance of the model class, just to run the
        # validation.
        changed_self = self_compat.obj.__class__(
            **{
                **self_compat.model_dump(),
                **prepared_changes,
            },
        )

        # Update the changes with the validated values we now have from the
        # temporary instance.
        prepared_changes = {
            key: value
            for key, value
            in changed_self.__dict__.items()
            if key in prepared_changes.keys()
        }


def reset_validate_assigment_config(
    self_compat: PydanticCompat,
    state_cache: dict[str, Any],
    prepared_changes: dict[str, Any],  # noqa: ARG001 unused argument
) -> None:
    """
    Ensure that the validate_assignment flag is reset to its original value.
    """

    self_compat.set_model_config_value(
        "validate_assignment",
        state_cache.pop("validate_assignment", None),
    )


def prepare_setattr_handler_cache(
    self_compat: PydanticCompat,
    state_cache: dict[str, Any],
    prepared_changes: dict[str, Any],  # noqa: ARG001 unused argument
) -> None:
    """
    Empty the cache of setattr handlers.

    This is needed, because otherwise assigning multiple attributes could fail
    if the respective validators already have been initialized.
    """

    state_cache["__pydantic_setattr_handlers__"] = {}
    if PYDANTIC_GE_V2_11:
        state_cache["__pydantic_setattr_handlers__"] = self_compat.obj.__class__.__pydantic_setattr_handlers__
        self_compat.obj.__class__.__pydantic_setattr_handlers__ = {}


def reset_setattr_handler_cache(
    self_compat: PydanticCompat,
    state_cache: dict[str, Any],
    prepared_changes: dict[str, Any],  # noqa: ARG001 unused argument
) -> None:
    """Reset the setattr handler cache to its original state."""

    if PYDANTIC_GE_V2_11:
        self_compat.obj.__class__.__pydantic_setattr_handlers__ = state_cache.pop(
            "__pydantic_setattr_handlers__",
            {},
        )


@contextmanager
def assignment_validation_context(
    self_compat: PydanticCompat,
    prepared_changes: dict[str, Any],
) -> None:
    """
    Context for assigning values.

    This context handles assigning multiple values at once while providing
    compatibility across pydantic versions.
    This requires some temporary changes, we need to reset on exit.
    """

    old_prepared_changes = prepared_changes
    state_cache = {}
    try:
        prepare_validate_assignment_config(self_compat, state_cache, old_prepared_changes)
        prepare_setattr_handler_cache(self_compat, state_cache, old_prepared_changes)

        yield

    finally:
        reset_validate_assigment_config(self_compat, state_cache, old_prepared_changes)
        reset_setattr_handler_cache(self_compat, state_cache, old_prepared_changes)

        prepared_changes = old_prepared_changes
