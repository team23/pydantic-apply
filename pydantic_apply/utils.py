from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Union, get_args, get_origin

import pydantic

import pydantic_apply

from ._compat import PYDANTIC_GE_V2_11


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


@contextmanager
def assignment_validation_context(
    obj: pydantic.BaseModel,
    prepared_changes: dict[str, Any],
) -> Generator[dict[str, Any], None, None]:
    """
    Context for assigning values.

    This context handles assigning multiple values at once while providing
    compatibility across pydantic versions.
    This requires some temporary changes, we need to reset on exit.
    """

    had_validate_assignment = obj.model_config.get("validate_assignment", None)
    old_setattr_handlers = {}

    try:
        if had_validate_assignment:
            # Disable validation on assignment so we can apply the whole set of
            # changes without validation problems while the data changes. This
            # is necessary as validators may depend on other fields. When we change
            # the fields one by one, the validators may fail as the temporary
            # combination of two values will not validate. But the validator might
            # have passed when we would have had the chance to set both values.
            obj.model_config["validate_assignment"] = False

            # Run validation as if all changes were applied. We do this by creating
            # a new (temporary) instance of the model class, just to run the
            # validation.
            changed_self = obj.__class__(
                **{
                    **obj.model_dump(),
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

        # Empty the cache of setattr handlers.
        # This is needed, because otherwise assigning multiple attributes could fail
        # if the respective validators already have been initialized.
        if PYDANTIC_GE_V2_11:
            old_setattr_handlers = obj.__class__.__pydantic_setattr_handlers__
            obj.__class__.__pydantic_setattr_handlers__ = {}

        yield prepared_changes

    finally:
        # Reset `validate_assignment` to its original state
        if had_validate_assignment:
            obj.model_config["validate_assignment"] = had_validate_assignment

        # Reset the setattr handler cache
        if PYDANTIC_GE_V2_11:
            obj.__class__.__pydantic_setattr_handlers__ = old_setattr_handlers
