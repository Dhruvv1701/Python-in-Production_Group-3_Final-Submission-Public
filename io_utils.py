import json
import xml.etree.ElementTree as ET
import networkx as nx

def load_ppr_from_json(file):
    data = json.load(file)
    G = nx.DiGraph()

    if "products" in data:
        for p in data.get("products", []):
            G.add_node(p["id"], label=p.get("name", ""), type="Product")

        for pr in data.get("processes", []):
            G.add_node(pr["id"], label=pr.get("name", ""), type="Process")

        for r in data.get("resources", []):
            G.add_node(r["id"], label=r.get("name", ""), type="Resource")

        for rel in data.get("relations", []):
            G.add_edge(rel["from"], rel["to"], type=rel.get("type", ""))

    elif "nodes" in data:
        # Add nodes
        for node in data["nodes"]:
            G.add_node(
                node["id"],
                label=node.get("name", ""),
                type=node.get("type", "").strip().capitalize()
            )

        # Add edges
        for edge in data["edges"]:
            G.add_edge(
                edge["source"],
                edge["target"],
                type=edge.get("relation", "")
            )

    return G

def load_ppr_from_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    G = nx.DiGraph()

    for p in root.findall("./products/product"):
        G.add_node(p.get("id"), label=p.get("name"), type="Product")

    for pr in root.findall("./processes/process"):
        G.add_node(pr.get("id"), label=pr.get("name"), type="Process")

    for r in root.findall("./resources/resource"):
        G.add_node(r.get("id"), label=r.get("name"), type="Resource")

    for rel in root.findall("./relations/relation"):
        G.add_edge(rel.get("from"), rel.get("to"), type=rel.get("type"))

    return G