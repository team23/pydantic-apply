# pydantic-apply

## Installation

Just use `pip install pydantic-apply` to install the library.

## About

With `pydantic-apply` you can apply changes to your pydantic models by using
the `ApplyModelMixin` it provides:

```python
import pydantic

from pydantic_apply import ApplyModelMixin


class Something(ApplyModelMixin, pydantic.BaseModel):
    name: str
    age: int


obj = Something(name='John Doe', age=42)
obj.apply({
    "age": 43,
})
assert obj.age == 43
```

As the apply data you may pass any dictionary or other pydanic object as you
wish. pydantic objects will be converted to dict's when being applied - but will
only use fields that where explicitly set on the model instance. Also note
that `.apply()` will ignore all fields not present in the model, like the
model constructor would.

### Nested models

`pydantic-apply` will also know how to apply changes to nested models. If those
models are by themself subclasses of `ApplyModelMixin` it will call `apply()`
on those fields as well. Otherwise the whole attribute will be replaced.

### Apply changes when using `validate_assignment`

When your models have `validate_assignment` enabled it may become tricky to
apply changes to the model. This is due to the fact that you only can assign
fields once at a time. But with `validate_assignment` enabled this means each
field assignment will trigger its own validation and this validation might
fail as the model state is not completely changes and thus in a "broken"
intermediate state.

`pydantic-apply` will take care of this issue and disable the validation for
each assignment while applying the changes. It will also ensure the resulting
object will still pass the validation, so you don't have to care about this
case at all.

# Contributing

If you want to contribute to this project, feel free to just fork the project,
create a dev branch in your fork and then create a pull request (PR). If you
are unsure about whether your changes really suit the project please create an
issue first, to talk about this.
