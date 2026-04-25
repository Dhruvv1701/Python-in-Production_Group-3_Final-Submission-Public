from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile, os, networkx as nx

NODE_STYLES = {
    "Product": {"color": "#AED6F1", "border": "#2980B9", "shape": "ellipse", "size": 28},
    "Process": {"color": "#A9DFBF", "border": "#1E8449", "shape": "box", "size": 32},
    "Resource": {"color": "#FAD7A0", "border": "#CA6F1E", "shape": "diamond", "size": 28},
}
EDGE_COLORS = {
    "uses": "#E67E22",
    "input": "#B7950B",
    "output": "#1A5276",
    "flow": "#8E44AD",
    "inspect": "#C0392B"
}

# Columns spaced to fit well in the viewport
COL_X = {"Resource": -420, "Process": 0, "Product": 420}
Y_GAP = 120


def _order_by_precedes(G, processes):
    sub = nx.DiGraph()
    sub.add_nodes_from(processes)
    for u, v, d in G.edges(data=True):
        rel = d.get("type", d.get("relation", ""))
        if rel == "Precedes" and u in processes and v in processes:
            sub.add_edge(u, v)
    try:
        return list(nx.topological_sort(sub))
    except Exception:
        return processes


def build_pyvis_graph(G, eng_df=None):
    node_data_map = {}

    if eng_df is not None and not eng_df.empty:
        eng_df = eng_df.copy()
        eng_df.columns = eng_df.columns.str.strip().str.replace(" ", "_")
        eng_df["ID"] = eng_df["ID"].astype(str).str.strip().str.upper()

        node_data_map = eng_df.set_index("ID").to_dict("index")

    net = Network(height="720px", width="100%", directed=True,
                  bgcolor="#FFFFFF", font_color="#111111")
    net.toggle_physics(False)

    # Count per column
    col_counts = {t: sum(1 for _, d in G.nodes(data=True) if d.get("type") == t)
                  for t in ["Resource", "Process", "Product"]}

    # Order processes
    processes    = [n for n, d in G.nodes(data=True) if d.get("type") == "Process"]
    ordered_proc = _order_by_precedes(G, processes)

    col_idx = {t: 0 for t in ["Resource", "Process", "Product"]}

    for node, data in G.nodes(data=True):
        ntype = data.get("type", "Unknown")
        label = data.get("label", node)
        style = NODE_STYLES.get(ntype, {"color": "#DDD", "border": "#999",
                                        "shape": "dot", "size": 24})

        x = COL_X.get(ntype, 0)

        if ntype == "Process" and node in ordered_proc:
            idx = ordered_proc.index(node)
        else:
            idx = col_idx.get(ntype, 0)

        total = col_counts.get(ntype, 1)
        y     = idx * Y_GAP - (total - 1) * Y_GAP / 2
        col_idx[ntype] = col_idx.get(ntype, 0) + 1

        node_id_clean = str(node).strip().upper()
        excel_row = node_data_map.get(node_id_clean, {})

        cost = excel_row.get("Cost_(€)", excel_row.get("Cost", "N/A"))
        kpi = excel_row.get("KPI", "N/A")

        title = (
            f"Cost: {cost}; "
            f"KPI: {kpi}"
        )


        net.add_node(
            node, label=label, title=title,
            color={"background": style["color"], "border": style["border"],
                   "highlight": {"background": "#E74C3C", "border": "#922B21"}},
            shape=style["shape"], size=style["size"],
            font={"size": 13, "face": "Helvetica"},
            x=x, y=y, physics=False, borderWidth=2,
        )

    for src, tgt, data in G.edges(data=True):
        rel    = data.get("type", data.get("relation", ""))
        color  = EDGE_COLORS.get(rel, "#AAAAAA")
        dashes = rel in ("Check", "Precedes")
        net.add_edge(
            src, tgt, label=rel,
            color={"color": color, "highlight": "#E74C3C", "opacity": 0.9},
            dashes=dashes,
            arrows={"to": {"enabled": True, "scaleFactor": 0.85}},
            font={"size": 11, "color": color, "face": "Helvetica",
                  "strokeWidth": 3, "strokeColor": "#ffffff"},
            width=2,
            smooth={"type": "straightCross", "roundness": 0},
        )

    return net


def show_pyvis_graph(G, eng_df=None):
    net = build_pyvis_graph(G, eng_df)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w",
                                     encoding="utf-8") as f:
        temp_path = f.name

    net.save_graph(temp_path)

    with open(temp_path, "r", encoding="utf-8") as f:
        html = f.read()

    fit_script = """
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        setTimeout(function() {
            if (typeof network !== 'undefined') {
                network.fit({ animation: { duration: 500, easingFunction: "easeInOutQuad" } });
            }
        }, 300);
    });
    </script>
    """
    html = html.replace("</body>", fit_script + "</body>")

    components.html(html, height=740, scrolling=False)
    os.remove(temp_path)
