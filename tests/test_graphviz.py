from agent_steps import graph_to_dotviz, make_graph

from . import example
from .example import create_recipe


def test_graphviz():
    graph = make_graph(create_recipe, example)
    output = graph_to_dotviz(graph)
    output.render("test_graphviz", format="png")
    assert output
