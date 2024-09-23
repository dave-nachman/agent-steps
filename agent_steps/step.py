from typing import Callable, Optional

from agent_steps.runtime import ExecutedNode, _runtime


class Step:
    """
    A step in the pipeline, wrapping a function call.
    """

    def __init__(self, fn: Callable, model: Optional[str] = None, max_loops: int = 10):
        self.fn = fn
        self.model = model
        self.max_loops = max_loops

    def __call__(self, *args, **kwargs):
        runtime = _runtime.get()
        runtime._invocations[self.fn.__name__] += 1

        if self.max_loops and runtime._invocations[self.fn.__name__] > self.max_loops:
            raise ValueError(
                f"Step {self.fn.__name__} has been called more than {self.max_loops} times"
            )

        if self.model:
            result = runtime.make_model_call(self.model, self.fn, *args, **kwargs)
        else:
            result = self.fn(*args, **kwargs)

        executed_node = ExecutedNode(self.fn.__name__, self, args, result)
        runtime.executed_nodes.append(executed_node)
        return executed_node

    def __repr__(self):
        return f"Step(fn={self.fn.__name__})"


def step(model: Optional[str] = None, max_loops: Optional[int] = None):
    """
    Decorator to wrap a function call in a step.
    """

    def wrapper(fn: Callable):
        return Step(fn, model=model, max_loops=max_loops)

    return wrapper
