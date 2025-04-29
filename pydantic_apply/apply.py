import warnings
from typing import Any, Union, cast

import pydantic

from pydantic_apply._compat import PydanticCompat
from pydantic_apply.utils import assignment_validation_context, is_pydantic_apply_annotation


class ApplyModelMixin(pydantic.BaseModel):
    """Mixin to allow models to apply partly changes to their data."""

    def model_apply(
        self,
        changes: Union[pydantic.BaseModel, dict[str, Any]],
    ) -> None:
        """Apply (partly) changes to the model data."""

        self_compat = PydanticCompat(self)

        if isinstance(changes, pydantic.BaseModel):
            # Convert model to dict. Do not use `changes.model_dump()` because it
            # would convert nested models to dicts, too. We don't want that yet.
            changes = {
                key: value
                for key, value
                in changes.__dict__.items()
                if key in PydanticCompat(changes).__pydantic_fields_set__
            }

        # Prepare the changes
        prepared_changes = {}
        for field_name, model_field in self_compat.model_fields.items():
            # Make sure the field exists in the changes and
            # get changed field value
            if field_name in changes:
                changed_field_value = changes[field_name]
            elif model_field.alias in changes:
                changed_field_value = changes[model_field.alias]
            else:
                # Field will not be changed
                continue

            # Handle ApplyModelMixin fields:
            # Field type must be ApplyModelMixin....
            field_annotation = self_compat.get_model_field_info_annotation(model_field)

            if is_pydantic_apply_annotation(field_annotation):
                current_value = getattr(self, field_name)
                if (
                    # ...AND current attribute value must be a instance
                    #        of ApplyModelMixin (not None)...
                    isinstance(current_value, ApplyModelMixin)
                    # ...AND type of changed value must allow patching.
                    and (
                        isinstance(changed_field_value, dict)
                        or isinstance(changed_field_value, pydantic.BaseModel)
                    )
                ):
                    # When validation on assignment is enabled we need to
                    # copy the current value first. Otherwise, the validation
                    # might have issues, see below.
                    if self_compat.get_model_config_value("validate_assignment"):
                        current_value = PydanticCompat(current_value).model_copy()

                    # ...then use `.apply(...)` on the current value to prepare changes
                    cast(ApplyModelMixin, current_value).model_apply(changed_field_value)
                    prepared_changes[field_name] = current_value
                    continue

            # Default apply: Just set new value
            prepared_changes[field_name] = changed_field_value

        with assignment_validation_context(self_compat, prepared_changes) as changes_in_context:
            for field_name, field_value in changes_in_context.items():
                setattr(self, field_name, field_value)

    def apply(
        self,
        changes: Union[pydantic.BaseModel, dict[str, Any]],
    ) -> None:
        warnings.warn(
            "apply(...) is deprecated, use model_apply(...) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.model_apply(changes)
