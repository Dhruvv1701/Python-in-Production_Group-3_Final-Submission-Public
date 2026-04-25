import networkx as nx
import pandas as pd


def _get_rel(data):
    return data.get("type", data.get("relation", ""))


def check_car_design_requirements(G, eng_df=None):
    results = []

    nodes = G.nodes(data=True)
    labels = [d["label"].lower() for _, d in nodes]

    # 1. Wheel Requirement

    wheels = [n for n, d in nodes if "wheel" in d["label"].lower()]

    wheel_count = len(wheels)

    if eng_df is not None and not eng_df.empty:
        eng_df = eng_df.copy()
        eng_df.columns = eng_df.columns.str.strip().str.replace(" ", "_")
        eng_df["ID"] = eng_df["ID"].astype(str).str.strip().str.upper()

        for wheel_node in wheels:
            wheel_id = str(wheel_node).strip().upper()
            wheel_data = eng_df[eng_df["ID"] == wheel_id]

            if not wheel_data.empty and "Number_of_Components" in wheel_data.columns:
                wheel_count += int(wheel_data.iloc[0].get("Number_of_Components", 0)) - 1

    results.append({
        "Requirement": "Vehicle must have at least 6 wheels",
        "Status": "Pass" if wheel_count >= 6 else "Fail",
        "Details": f"Wheel quantity found: {wheel_count}"
    })


    # 2. Axle Requirement

    axles = [n for n, d in nodes if "axle" in d["label"].lower()]
    results.append({
        "Requirement": "Vehicle must have 3 axles",
        "Status": "Pass" if len(axles) >= 3 else "Fail",
        "Details": f"Axle nodes found: {len(axles)}"
    })

    # 3. Chassis Check

    chassis = any("chassis" in d["label"].lower() for _, d in nodes)
    results.append({
        "Requirement": "Chassis must be present",
        "Status": "Pass" if chassis else "Fail",
        "Details": "Chassis detected" if chassis else "Missing chassis"
    })

    # 4. Cabin Check

    cabin = any("cabin" in d["label"].lower() for _, d in nodes)
    results.append({
        "Requirement": "Cabin must be present",
        "Status": "Pass" if cabin else "Fail",
        "Details": "Cabin detected" if cabin else "Missing cabin"
    })

    # 5. Rear Support Check

    rear = any("rear support" in d["label"].lower() for _, d in nodes)
    results.append({
        "Requirement": "Rear support must exist",
        "Status": "Pass" if rear else "Fail",
        "Details": "Rear support detected" if rear else "Missing rear support"
    })

    # 6. Cargo Platform

    cargo = any("cargo" in d["label"].lower() for _, d in nodes)
    results.append({
        "Requirement": "Cargo platform required for load handling",
        "Status": "Pass" if cargo else "Fail",
        "Details": "Cargo system detected" if cargo else "Missing cargo platform"
    })

    # 7. Final Product Check

    final_product = any("final" in d["label"].lower() for _, d in nodes)
    results.append({
        "Requirement": "Final product is produced",
        "Status": "Pass" if final_product else "Fail",
        "Details": "Final product exists" if final_product else "Missing final product"
    })

    # 8. Process Flow Check

    processes = [n for n, d in nodes if d["type"] == "Process"]
    flow_ok = all(
        any(G.has_edge(p, other) for other in G.nodes if other != p)
        for p in processes
    )

    results.append({
        "Requirement": "All processes must be connected",
        "Status": "Pass" if flow_ok else "Fail",
        "Details": "All processes linked" if flow_ok else "Disconnected process found"
    })

    return pd.DataFrame(results)


def get_view_specific_dependencies(G, selected_view):
    if selected_view == "Basic Engineering":
        allowed = {"produce", "used in", "perform", "flow", "input", "output", "precedes"}
    elif selected_view == "Quality":
        allowed = {"check", "uses", "input", "output"}
    elif selected_view == "Sustainability":
        allowed = {"used in", "perform", "produce"}
    elif selected_view == "Reliability":
        allowed = {"perform", "used in", "check"}
    else:
        allowed = set()

    rows = []
    for u, v, d in G.edges(data=True):
        rel = _get_rel(d).strip().lower()
        if rel in allowed:
            rows.append({
                "source": G.nodes[u].get("label", u),
                "target": G.nodes[v].get("label", v),
                "relation": _get_rel(d),
                "source_type": G.nodes[u].get("type", ""),
                "target_type": G.nodes[v].get("type", "")
            })

    return pd.DataFrame(rows)


def find_similarly_structured_elements(G):
    groups = {}

    for node in G.nodes():
        node_type = G.nodes[node].get("type", "")
        in_degree = G.in_degree(node)
        out_degree = G.out_degree(node)

        signature = (node_type, in_degree, out_degree)
        groups.setdefault(signature, []).append(G.nodes[node].get("label", node))

    results = []
    for signature, nodes in groups.items():
        if len(nodes) > 1:
            results.append({
                "type": signature[0],
                "in_degree": signature[1],
                "out_degree": signature[2],
                "similar_nodes": ", ".join(nodes),
                "count": len(nodes)
            })

    return pd.DataFrame(results)


def find_disconnected_segments(G):
    UG = G.to_undirected()
    components = list(nx.connected_components(UG))

    results = []
    for i, comp in enumerate(components, start=1):
        results.append({
            "segment_no": i,
            "node_count": len(comp),
            "nodes": ", ".join(sorted([G.nodes[n].get("label", n) for n in comp]))
        })

    return pd.DataFrame(results)

def find_subgraphs_with_min_nodes(G, min_nodes=5):
    """Identify connected subgraphs (components) with at least min_nodes nodes."""
    UG = G.to_undirected()
    components = list(nx.connected_components(UG))

    results = []
    for i, comp in enumerate(components, start=1):
        if len(comp) >= min_nodes:
            results.append({
                "subgraph_no": i,
                "node_count": len(comp),
                "nodes": ", ".join(sorted([G.nodes[n].get("label", n) for n in comp]))
            })

    if not results:
        return pd.DataFrame([{"subgraph_no": "-", "node_count": 0,
                               "nodes": f"No subgraph with >= {min_nodes} nodes found"}])
    return pd.DataFrame(results)
