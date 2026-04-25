import networkx as nx

def get_color(node_type):
    return {
        "Product": "lightblue",
        "Process": "lightgreen",
        "Resource": "orange"
    }.get(node_type, "gray")

def draw_graph(G):
    dot = """
    digraph G {
        rankdir=LR;
        splines=true;
        nodesep=0.8;
        ranksep=1;
        node [fontname="Helvetica"];
        edge [fontname="Helvetica"];
    """


    # GROUP NODES BY TYPE

    products = [n for n, d in G.nodes(data=True) if d["type"] == "Product"]
    processes = [n for n, d in G.nodes(data=True) if d["type"] == "Process"]
    resources = [n for n, d in G.nodes(data=True) if d["type"] == "Resource"]


    # RESOURCE LAYER

    dot += "{rank=same;\n"
    for node in resources:
        label = G.nodes[node]["label"]
        dot += f'"{node}" [label="{label}", shape=diamond, sides=3, orientation=0, style=filled, fillcolor={get_color("Resource")}];\n'
    dot += "}\n"


    # PROCESS LAYER

    dot += "{rank=same;\n"
    for node in processes:
        label = G.nodes[node]["label"]
        dot += f'"{node}" [label="{label}", shape=box, style=filled, fillcolor={get_color("Process")}];\n'
    dot += "}\n"


    # PRODUCT LAYER

    dot += "{rank=same;\n"
    for node in products:
        label = G.nodes[node]["label"]
        dot += f'"{node}" [label="{label}", shape=ellipse, style=filled, fillcolor={get_color("Product")}];\n'
    dot += "}\n"


    # EDGES

    for u, v, data in G.edges(data=True):
        dot += f'"{u}" -> "{v}" [label="{data.get("type", data.get("relation", ""))}"];\n'

    dot += "}"
    return dot

def draw_highlight_subgraph(G, selected_node):
    dot = """
    digraph G {
        rankdir=LR;
        splines=polyline;
        nodesep=0.8;
        ranksep=1.5;
        node [fontname="Helvetica"];
        edge [fontname="Helvetica"];
    """

    products = [n for n, d in G.nodes(data=True) if d["type"] == "Product"]
    processes = [n for n, d in G.nodes(data=True) if d["type"] == "Process"]
    resources = [n for n, d in G.nodes(data=True) if d["type"] == "Resource"]


    # RESOURCE LAYER

    dot += "{rank=same;\n"
    for node in resources:
        data = G.nodes[node]
        color = "red" if node == selected_node else get_color(data["type"])
        style = "filled,bold" if node == selected_node else "filled"

        dot += f'"{node}" [label="{data["label"]}", shape=diamond, sides=3, orientation=0, style="{style}", fillcolor={color}];\n'
    dot += "}\n"


    # PROCESS LAYER

    dot += "{rank=same;\n"
    for node in processes:
        data = G.nodes[node]
        color = "red" if node == selected_node else get_color(data["type"])
        style = "filled,bold" if node == selected_node else "filled"

        dot += f'"{node}" [label="{data["label"]}", shape=box, style="{style}", fillcolor={color}];\n'
    dot += "}\n"


    # PRODUCT LAYER

    dot += "{rank=same;\n"
    for node in products:
        data = G.nodes[node]
        color = "red" if node == selected_node else get_color(data["type"])
        style = "filled,bold" if node == selected_node else "filled"

        dot += f'"{node}" [label="{data["label"]}", shape=ellipse, style="{style}", fillcolor={color}];\n'
    dot += "}\n"


    # EDGES

    for u, v, d in G.edges(data=True):
        dot += f'"{u}" -> "{v}" [label="{d.get("type","")}"];\n'

    dot += "}"
    return dot

def draw_path_subgraph(G, path_nodes, source=None, target=None):
    dot = "digraph G {\n"
    dot += "rankdir=LR;\n"
    dot += "splines=polyline;\n"
    dot += 'node [fontname="Helvetica"];\n'

    if not path_nodes or len(path_nodes) < 1:
        return dot + "}"

    nodes_to_draw = path_nodes


    # NODES

    for n in nodes_to_draw:
        data = G.nodes[n]
        label = data.get("label", n)
        ntype = data.get("type", "")

        # shape
        if ntype == "Process":
            shape = "box"
        elif ntype == "Resource":
            shape = "diamond"
        else:
            shape = "ellipse"

        # COLOR LOGIC
        fill_color = get_color(ntype)

        if n == source or n == target:
            border_color = "red"
            penwidth = 0.5
        else:
            border_color = "black"
            penwidth = 1

        dot += f'"{n}" [label="{label}", shape={shape}, style=filled, fillcolor="{fill_color}", color="{border_color}", penwidth={penwidth}];\n'


    # EDGES

    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]

        if G.has_edge(u, v):
            edge_data = G.get_edge_data(u, v)
            rel = edge_data.get("type", edge_data.get("relation", ""))

            dot += f'"{u}" -> "{v}" [label="{rel}", color="black", penwidth=2];\n'
        else:
            dot += f'"{u}" -> "{v}" [color="black"];\n'

    dot += "}"
    return dot