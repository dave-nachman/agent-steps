import json
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar

from litellm import completion
from pydantic import BaseModel

# keep track of the current runtime
_runtime = ContextVar("runtime", default=None)


class ExecutedNode:
    """
    The result of executing a step
    """

    def __init__(self, name, step, arguments, result):
        self.name = name
        self.step = step
        self.arguments = arguments
        self.result = result

    def __getattr__(self, item):
        return getattr(self.result, item)

    def __repr__(self):
        return repr(self.result)


class Runtime:
    def __init__(self, logging_fn=None):
        self.executed_nodes = []
        self.logging_fn = logging_fn
        self._invocations = Counter()

    def make_model_call(self, model, fn, *args, **kwargs):
        response_type = fn.__annotations__.get("return", None)
        messages = []
        # if docstring is present, use it as the prompt
        if fn.__doc__:
            messages.append({"role": "system", "content": fn.__doc__})

        function_result = fn(*args, **kwargs)

        # convert to string if not already
        if not isinstance(function_result, str):
            if isinstance(function_result, BaseModel):
                function_result = function_result.model_dump_json()
            else:
                function_result = str(function_result)

        messages.append({"role": "user", "content": function_result})

        if self.logging_fn:
            self.logging_fn(f"Making model call to {model} with messages: {messages}")

        if issubclass(response_type, BaseModel):
            response = completion(
                model=model,
                messages=messages,
                response_format=response_type,
                **kwargs,
            )
            content = response["choices"][0]["message"]["content"]
            instance = response_type.model_validate(json.loads(content))
            if self.logging_fn:
                self.logging_fn(f"Received response: {instance}")
            return instance
        else:
            # TODO: handle primitive types
            response = completion(
                model=model,
                messages=messages,
                **kwargs,
            )
            content = response["choices"][0]["message"]["content"]
            if self.logging_fn:
                self.logging_fn(f"Received response: {content}")
            return content


@contextmanager
def runtime(logging_fn=None):
    existing_runtime = _runtime.get(None)
    r = Runtime(logging_fn)
    _runtime.set(r)
    try:
        yield _runtime.get()
    finally:
        _runtime.set(existing_runtime)
