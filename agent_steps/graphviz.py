import graphviz

from agent_steps.graph import StepNode


def graph_to_dotviz(root_node: StepNode):
    """
    Convert a graph of steps to a dotviz graph.
    """
    dot = graphviz.Digraph(comment=root_node.step.fn.__name__)
    dot.attr(compound="true")
    dot.attr(rankdir="TB")

    def add_node_to_graph(node, parent=None):
        node_id = node.step.fn.__name__
        label = node_id

        if node.children:
            with dot.subgraph(name=f"cluster_{node_id}") as c:
                phantom = f"__phantom_{node_id}"
                c.node(phantom, "", shape="none", width="0", height="0")

                c.attr(label=node_id, style="rounded,filled", color="lightgrey")

                for i, child in enumerate(node.children):
                    if child.node.step.fn.__name__ != node_id:
                        child_id = child.node.step.fn.__name__
                        if i == 0:
                            # so that phantom is on top
                            c.edge(phantom, child_id, style="invis")

                        c.node(child_id, child_id, shape="box", style="rounded,filled")

                for child in node.children:
                    if child.node.step.fn.__name__ != node_id:
                        for input_node in child.node.inputs:
                            input_id = input_node.node.fn.__name__
                            if input_id in [
                                n.node.step.fn.__name__ for n in node.children
                            ]:
                                c.edge(
                                    input_id,
                                    child.node.step.fn.__name__,
                                    style="dashed" if child.conditional else "",
                                )

                if node.self_called:
                    c.edge(child_id, phantom)
        else:
            dot.node(node_id, label, shape="box", style="rounded,filled")

            for input_node in node.inputs:
                input_id = input_node.fn.__name__
                dot.edge(input_id, node_id)

    add_node_to_graph(root_node)
    return dot
