import ast
import inspect

from agent_steps.step import Step


class StepNode:
    """
    A node in the graph of steps.
    """

    def __init__(self, step, inputs):
        self.step = step

        # inputs are other steps that are used as inputs to this step
        self.inputs = inputs

        # children are steps that are potentially called during the execution of this step
        self.children = []

        # self_called is true if this step calls itself
        self.self_called = False

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return f"StepNode(fn={self.step.fn.__name__}, children={self.children}, inputs={self.inputs})"


class StepEdge:
    """
    An edge from one step to another.
    """

    def __init__(self, node, conditional):
        # target node
        self.node = node

        # true if this edge is conditionally called
        self.conditional = conditional


# based on https://stackoverflow.com/questions/34570992/getting-parent-of-ast-node-in-python
class AddParent(ast.NodeTransformer):
    current_parent = None

    def visit(self, node):
        node.parent, self.current_parent = self.current_parent, node
        return node


def make_graph(step, module) -> StepNode:
    """
    Make a graph of the steps in the module by walking the AST
    """
    root_node = StepNode(step, [])
    steps_by_name = {
        name: obj for name, obj in module.__dict__.items() if isinstance(obj, Step)
    }
    variable_source = {}
    variable_usage = {}

    def is_conditional(node):
        current = node
        while current:
            # TODO: handle the test vs. body appropriately
            if isinstance(current, ast.If) and not isinstance(
                current.parent, ast.FunctionDef
            ):
                return True

            current = getattr(current, "parent", None)
        return False

    def walk_function(step, parent_node, visited):
        if step in visited:
            return

        visited.add(step)
        source = inspect.getsource(step.fn)
        tree = ast.parse(source)

        tree = AddParent().visit(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in steps_by_name:
                    child_step = steps_by_name[func_name]
                    child_variable_useds = [
                        arg.id for arg in node.args if isinstance(arg, ast.Name)
                    ]
                    child_inputs = []

                    for input in child_variable_useds:
                        if input in variable_source:
                            edge = StepEdge(
                                steps_by_name[variable_source[input]],
                                is_conditional(node),
                            )
                            child_inputs.append(edge)

                    child_node = StepEdge(
                        StepNode(child_step, child_inputs), is_conditional(node)
                    )
                    parent_node.add_child(child_node)
                    walk_function(child_step, child_node, visited)

                    if step == child_step:
                        parent_node.self_called = True

            elif isinstance(node, ast.Assign):
                value = node.value.func.id
                target = node.targets[0]
                variable_source[target.id] = value

                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id not in variable_usage:
                            variable_usage[target.id] = set()
                        variable_usage[target.id].add(parent_node)

    walk_function(step, root_node, set())

    return root_node
