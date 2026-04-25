import networkx as nx

def validate_graph(G):
    messages = []

    types = [d["type"] for _, d in G.nodes(data=True)]

    if not all(t in types for t in ["Product", "Process", "Resource"]):
        messages.append("❌ Missing PPR types")

    if nx.is_directed_acyclic_graph(G):
        messages.append("✅ Graph is acyclic")
    else:
        messages.append("❌ Graph has cycles")

    return messages