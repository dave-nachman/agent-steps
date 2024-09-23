from agent_steps import make_graph

from . import example
from .example import create_recipe


def test_graph():
    graph = make_graph(create_recipe, example)
    expected_children = 4
    assert len(graph.children) == expected_children
