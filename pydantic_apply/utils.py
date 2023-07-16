from typing import Union, get_args, get_origin

import pydantic_apply


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
