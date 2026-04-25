import streamlit as st
import networkx as nx
import pandas as pd
import json
import plotly.graph_objects as go

from graph_utils import draw_graph, draw_highlight_subgraph, draw_path_subgraph
from io_utils import load_ppr_from_json, load_ppr_from_xml
from validation import validate_graph
from crud_utils import valid_ppr_connection
from export_utils import export_graphviz_image
from pyvis_utils import show_pyvis_graph
from algorithms import (
    check_car_design_requirements,
    get_view_specific_dependencies,
    find_similarly_structured_elements,
    find_disconnected_segments,
    find_subgraphs_with_min_nodes
)
from analytics_utils import (
    plot_oee_comparison,
    plot_quality_distribution,
    plot_threshold_vs_value,
    show_kpi_dashboard,
    plot_cost_vs_oee
)

def show_table(df, use_container_width=True):
    df = df.copy()
    df.index = range(1, len(df) + 1)
    st.dataframe(df, use_container_width=use_container_width)

st.set_page_config(page_title="PPR Tool", layout="wide")


# INIT GRAPH

if "G" not in st.session_state:
    st.session_state.G = nx.DiGraph()

G = st.session_state.G


# DEMO GRAPH

def create_demo_ppr():
    G = nx.DiGraph()


    # PRODUCTS

    G.add_node("P1", label="Chassis", type="Product")
    G.add_node("P2", label="Cabin", type="Product")
    G.add_node("P3", label="Axles (x3)", type="Product")
    G.add_node("P4", label="Wheels (x6)", type="Product")
    G.add_node("P5", label="Heavy Transport Vehicle", type="Product")


    # PROCESSES

    G.add_node("PR1", label="Prepare Base Structure", type="Process")
    G.add_node("PR2", label="Install Cabin", type="Process")
    G.add_node("PR3", label="Mount Axles", type="Process")
    G.add_node("PR4", label="Assemble Wheels", type="Process")
    G.add_node("PR5", label="Final Inspection", type="Process")


    # RESOURCES

    G.add_node("R1", label="Assembly Worker", type="Resource")
    G.add_node("R2", label="Tool Box", type="Resource")
    G.add_node("R3", label="Quality Control Unit", type="Resource")


    # PROCESS FLOW

    G.add_edge("PR1", "PR2", type="flow")
    G.add_edge("PR2", "PR3", type="flow")
    G.add_edge("PR3", "PR4", type="flow")
    G.add_edge("PR4", "PR5", type="flow")


    # PRODUCT OUTPUTS

    G.add_edge("PR1", "P1", type="output")
    G.add_edge("PR2", "P2", type="output")
    G.add_edge("PR3", "P3", type="output")
    G.add_edge("PR4", "P4", type="output")
    G.add_edge("PR5", "P5", type="output")


    # PRODUCT INPUTS

    G.add_edge("P1", "PR2", type="input")
    G.add_edge("P2", "PR5", type="input")
    G.add_edge("P3", "PR4", type="input")
    G.add_edge("P4", "PR5", type="input")


    # RESOURCE CONNECTIONS

    G.add_edge("R1", "PR1", type="uses")
    G.add_edge("R1", "PR2", type="uses")
    G.add_edge("R1", "PR3", type="uses")
    G.add_edge("R1", "PR4", type="uses")

    G.add_edge("R2", "PR1", type="uses")
    G.add_edge("R2", "PR3", type="uses")
    G.add_edge("R2", "PR4", type="uses")

    G.add_edge("R3", "PR5", type="uses")

    return G

def export_ppr_to_json(G):
    data = {
        "nodes": [],
        "edges": []
    }

    for node_id, attrs in G.nodes(data=True):
        data["nodes"].append({
            "id": node_id,
            "name": attrs.get("label", ""),
            "type": attrs.get("type", "")
        })

    for source, target, attrs in G.edges(data=True):
        data["edges"].append({
            "source": source,
            "target": target,
            "relation": attrs.get("type", "")
        })

    return data


# SIDEBAR

st.sidebar.title("⚙️ Control Panel")

# MODEL MANAGEMENT
with st.sidebar.expander("📁 Model Management", expanded=True):

    if st.button("Load Demo PPR"):
        st.session_state.G = create_demo_ppr()

    if st.button("Reset Graph"):
        st.session_state.G = nx.DiGraph()

        if "file_loaded" in st.session_state:
            del st.session_state["file_loaded"]

        st.rerun()

    file = st.sidebar.file_uploader("Upload JSON/XML", type=["json", "xml"])

    if file and "file_loaded" not in st.session_state:
        new_graph = load_ppr_from_json(file) if file.name.endswith(".json") else load_ppr_from_xml(file)

        st.session_state.G = new_graph
        st.session_state.file_loaded = True  # 🔥 IMPORTANT FLAG

        st.sidebar.success("Model loaded")
        st.rerun()

    # DATA INPUT (MOVED HERE)
with st.sidebar.expander("📥 Engineering & Quality Data", expanded=True):

    excel_file = st.file_uploader(
        "Upload Combined Engineering + Quality Excel",
        type=["xlsx"],
        key="sidebar_excel"
    )

    if excel_file:
        try:
            eng_df = pd.read_excel(excel_file, sheet_name="Engineering_Data")
            qual_df = pd.read_excel(excel_file, sheet_name="Quality_Data")
        except ValueError:
            st.error("❌ Sheet not found.")
            st.stop()
        eng_df["ID"] = eng_df["ID"].astype(str).str.strip().str.upper()
        qual_df["ID"] = qual_df["ID"].astype(str).str.strip().str.upper()
        st.session_state["eng_df"] = eng_df
        st.session_state["qual_df"] = qual_df

        st.success("Engineering & Quality data loaded")


# MODEL SUMMARY
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Model Summary")

product_count = sum(1 for _, d in G.nodes(data=True) if d["type"] == "Product")
process_count = sum(1 for _, d in G.nodes(data=True) if d["type"] == "Process")
resource_count = sum(1 for _, d in G.nodes(data=True) if d["type"] == "Resource")
edge_count = G.number_of_edges()

col1, col2 = st.sidebar.columns(2)

with col1:
    st.metric("🟦 Products", product_count)
    st.metric("🟧 Resources", resource_count)

with col2:
    st.metric("🟩 Processes", process_count)
    st.metric("🔗 Edges", edge_count)

# INFO
st.sidebar.markdown("---")
st.sidebar.info("Upload PPR → Add data → Analyze model")
st.sidebar.caption("PPR Modeling Tool v1.0")


# TITLE

st.title("🚛 PPR Modeling Tool")


# TABS

home_tab, tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Home",
    "💻 Visualization",
    "🛠 CRUD",
    "📋 Engineering & Quality",
    "🧠 Graph Analysis"
])


# HOME TAB

with home_tab:
    st.header("Welcome to the PPR Modeling Tool")

    st.markdown("""
    This tool is designed to create, visualize, validate, and analyze a **PPR model**.

    **PPR means:**
    - **Product**: the physical or technical object
    - **Process**: the operation or activity performed
    - **Resource**: the machine, worker, tool, or system used
    """)

    st.divider()

    st.subheader("🚀 How to Start")

    st.markdown("""
    **Option 1: Load Demo Model**
    1. Go to the left sidebar.
    2. Click **Load Demo PPR**.
    3. Open the **Visualization** tab to view the model.

    **Option 2: Upload Existing Model**
    1. Go to the left sidebar.
    2. Upload a **JSON** or **XML** file.
    3. The graph will be loaded automatically.
    4. Open the **Visualization** tab to check the graph.

    **Option 3: Create New PPR Model**
    1. Open the **CRUD** tab.
    2. Click **Create New PPR**.
    3. Add Product, Process, and Resource nodes.
    4. Add valid connections between them.
    """)

    st.divider()

    st.subheader("🛠 How to Build the PPR Model")

    st.markdown("""
    **Step 1: Add Nodes**
    - Add a **Product** node for parts, components, or outputs.
    - Add a **Process** node for operations or activities.
    - Add a **Resource** node for workers, machines, tools, or equipment.

    **Step 2: Add Edges**
    Valid PPR connections are:
    - Product → Process
    - Process → Product
    - Process → Resource

    **Step 3: Validate Model**
    - Open the **Visualization** or **Graph Analysis** tab.
    - Check whether the model is acyclic.
    - Check missing PPR types and disconnected segments.
    """)

    st.divider()

    st.subheader("📥 Engineering & Quality Data")

    st.markdown("""
    To use the Engineering & Quality tab:

    1. Upload the Excel file.
    2. The Excel file should contain these two sheets:
       - **Engineering_Data**
       - **Quality_Data**
    3. Make sure the **ID** column matches the node IDs in your PPR model.
    4. Select a node to view engineering and quality information.
    """)

    st.divider()

    st.subheader("📊 Available Analysis Features")

    st.markdown("""
    The tool provides:
    - Graph visualization
    - Interactive Graph View
    - PNG/PDF graph export
    - Node type distribution
    - Engineering KPI dashboard
    - OEE comparison
    - Cost vs OEE analysis
    - Quality status distribution
    - Dependency analysis
    - Disconnected segment detection
    - Similar structure detection
    """)

    st.info("Recommended workflow: Home → Load/Create Model → Visualization → Engineering & Quality → Graph Analysis")


# VIEW TAB


with tab1:
    G = st.session_state.G


    # SYSTEM OVERVIEW

    st.markdown("## 📊 System Overview")

    product_count = sum(1 for _, d in G.nodes(data=True) if d["type"] == "Product")
    process_count = sum(1 for _, d in G.nodes(data=True) if d["type"] == "Process")
    resource_count = sum(1 for _, d in G.nodes(data=True) if d["type"] == "Resource")
    edge_count = G.number_of_edges()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🟦 Products", product_count)
    col2.metric("🟩 Processes", process_count)
    col3.metric("🟧 Resources", resource_count)
    col4.metric("🔗 Edges", edge_count)

    st.divider()


    # GRAPH VISUALIZATION

    subtab1, subtab2 = st.tabs([
        "📈 Graph Visualization",
        "🌐 Interactive Graph View"
    ])

    with subtab1:
        st.markdown("## 📈 Graph Visualization")

        if len(G.nodes) > 0:
            st.graphviz_chart(draw_graph(G), use_container_width=True)
        else:
            st.info("Load a model to begin visualization")
        dot = draw_graph(G)

        # PNG Export
        png_buffer = export_graphviz_image(dot, format="png")

        st.download_button(
            "Download PNG",
            data=png_buffer,
            file_name="ppr_graph.png",
            mime="image/png"
        )
        png_buffer.seek(0)
        pdf_buffer = export_graphviz_image(dot, format="pdf")

        st.download_button(
            "Download PDF",
            data=pdf_buffer,
            file_name="ppr_graph.pdf",
            mime="application/pdf"
        )
        st.divider()
    with subtab2:
        st.subheader("Interactive PyVis View")
        if G.number_of_nodes() > 0:
            show_pyvis_graph(G, st.session_state.get("eng_df"))
        else:
            st.info("No graph available for interactive view.")

        st.divider()

    st.markdown("## 📉 Graph Insights")

    col1, col2 = st.columns([2, 1])

    # PIE CHART
    with col1:
        st.subheader("Node Type Distribution")

        dist_df = pd.DataFrame({
            "Type": ["Product", "Process", "Resource"],
            "Count": [product_count, process_count, resource_count]
        })

        st.plotly_chart(
            {
                "data": [{
                    "labels": dist_df["Type"],
                    "values": dist_df["Count"],
                    "type": "pie",
                    "hole": 0.3
                }],
                "layout": {"margin": {"l": 0, "r": 0, "t": 0, "b": 0}}
            },
            use_container_width=True
        )


    with col2:
        if len(G.nodes) > 0:

            degrees = dict(G.degree())
            max_node = max(degrees, key=degrees.get)

            st.write(f"🔥 Most connected node: **{max_node}** (degree = {degrees[max_node]})")

            if nx.is_directed_acyclic_graph(G):
                st.success("✅ Graph is acyclic (Valid production flow)")
            else:
                st.error("❌ Graph contains cycles")

    st.divider()


    # VALIDATION

    st.markdown("## ✅ Validation")

    for msg in validate_graph(G):
        st.write(msg)


# CRUD TAB

with tab2:
    G = st.session_state.G
    st.header("🛠 Manage PPR Model")

    col_create, col_export = st.columns([1, 1])

    with col_create:
        if st.button("➕ Create New PPR"):
            st.session_state.G = nx.DiGraph()

            if "file_loaded" in st.session_state:
                del st.session_state["file_loaded"]

            st.session_state.file_loaded = False
            st.session_state.go_to_crud = True

            st.rerun()

    with col_export:
        json_data = export_ppr_to_json(G)
        json_string = json.dumps(json_data, indent=4)

        st.download_button(
            label="⬇️ Export PPR as JSON",
            data=json_string,
            file_name="generated_ppr_model.json",
            mime="application/json"
        )

    if st.session_state.get("go_to_crud", False):
        st.success("Ready to create new PPR model 👇")
        st.session_state.go_to_crud = False
    G = st.session_state.G

    with st.expander("➕ Create", expanded=True):

        col1, col2 = st.columns(2)

        with col1:
            with st.form("create_node_form", clear_on_submit=True):
                nid = st.text_input("ID", key="create_id")
                label = st.text_input("Label", key="create_label")
                ntype = st.selectbox("Type", ["Product", "Process", "Resource"], key="c_type")

                if st.form_submit_button("Add Node"):
                    if nid not in G.nodes:
                        G.add_node(nid, label=label, type=ntype)
                        st.session_state.G = G
                        st.success("Node added")
                        st.rerun()

                    else:
                        st.error("Node already exists")

        with col2:
            with st.form("create_edge_form"):
                nodes = list(G.nodes)
                disabled = len(nodes) == 0

                s = st.selectbox("From", nodes, key="edge_from")
                t = st.selectbox("To", nodes, key="edge_to")
                rel = st.text_input("Relation", key="edge_rel")

                if st.form_submit_button("Add Edge"):
                    if disabled:
                        st.error("No nodes available")
                    elif valid_ppr_connection(G, s, t):
                        G.add_edge(s, t, type=rel)
                        st.session_state.G = G
                        st.success("Edge added")
                        st.rerun()

                    else:
                        st.error("Invalid PPR connection")

    with st.expander("✏️ Update"):

        col1, col2 = st.columns(2)


        # UPDATE NODE

        with col1:
            st.subheader("Update Node")

            nodes = list(G.nodes)
            disabled = len(nodes) == 0

            node = st.selectbox(
                "Select Node",
                nodes if nodes else ["No nodes"],
                key="u_node",
                disabled=disabled
            )

            new_label = st.text_input("New Label", key="u_label", disabled=disabled)

            new_type = st.selectbox(
                "New Type",
                ["Product", "Process", "Resource"],
                key="u_type",
                disabled=disabled
            )

            if st.button("Update Node"):
                if not disabled:
                    G.nodes[node]["label"] = new_label
                    G.nodes[node]["type"] = new_type
                    st.session_state.G = G
                    st.success("Node updated")
                    st.rerun()


        # UPDATE EDGE

        with col2:
            st.subheader("Update Edge")

            edges = list(G.edges)

            if len(edges) > 0:

                edge = st.selectbox(
                    "Select Edge",
                    edges,
                    key="u_edge"
                )

                current_type = G.edges[edge].get("type", "")

                new_relation = st.text_input(
                    "New Relation",
                    value=current_type,
                    key="u_edge_rel"
                )

                if st.button("Update Edge"):
                    G.edges[edge]["type"] = new_relation
                    st.session_state.G = G
                    st.success("Edge updated")
                    st.rerun()

            else:
                st.info("No edges available")


    with st.expander("🗑 Delete"):

        col1, col2 = st.columns(2)

        with col1:
            nodes = list(G.nodes)
            node = st.selectbox("Delete Node", nodes if nodes else ["No nodes"], key="d_node")

            if st.button("Delete Node"):
                if len(nodes) > 0:
                    G.remove_node(node)
                    st.session_state.G = G
                    st.success("Node deleted")
                    st.rerun()


        with col2:
            edges = list(G.edges)
            edge = st.selectbox("Delete Edge", edges if edges else [("None", "None")], key="d_edge")

            if st.button("Delete Edge"):
                if len(edges) > 0:
                    G.remove_edge(edge[0], edge[1])
                    st.session_state.G = G
                    st.success("Edge deleted")
                    st.rerun()


    st.divider()
    st.subheader("📊 Live Graph View")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.graphviz_chart(draw_graph(G))

    with col2:
        st.metric("Nodes", G.number_of_nodes())
        st.metric("Edges", G.number_of_edges())

    st.subheader("Validation")
    for msg in validate_graph(G):
        st.write(msg)


# ENGINEERING + QUALITY VIEW

with tab3:
    G = st.session_state.G
    st.header("🛠 Engineering & Quality View")

    uploaded_excel = st.file_uploader(
        "Upload Combined Engineering + Quality Excel",
        type=["xlsx"],
        key="combined_upload"
    )

    if uploaded_excel:
        try:
            eng_df = pd.read_excel(uploaded_excel, sheet_name="Engineering_Data")
            qual_df = pd.read_excel(uploaded_excel, sheet_name="Quality_Data")
        except ValueError:
            st.error("❌ Sheet names not found in uploaded file.")
            st.stop()
        eng_df["ID"] = eng_df["ID"].astype(str).str.strip().str.upper()
        qual_df["ID"] = qual_df["ID"].astype(str).str.strip().str.upper()
        st.session_state["eng_df"] = eng_df
        st.session_state["qual_df"] = qual_df
        st.success("Data loaded successfully")

        with st.expander("📄 Raw Data"):
            st.write("Engineering Data")
            show_table(eng_df)

            st.write("Quality Data")
            show_table(qual_df)

    if "eng_df" in st.session_state and "qual_df" in st.session_state:
        eng_df = st.session_state["eng_df"]
        qual_df = st.session_state["qual_df"]
        nodes = list(G.nodes)
        eng_df.columns = eng_df.columns.str.strip().str.replace(" ", "_")
        qual_df.columns = qual_df.columns.str.strip().str.replace(" ", "_")

        id_to_name = {}
        if "Name" in eng_df.columns:
            id_to_name.update(dict(zip(eng_df["ID"], eng_df["Name"])))
        if "Name" in qual_df.columns:
            id_to_name.update(dict(zip(qual_df["ID"], qual_df["Name"])))

        if len(nodes) > 0:

            selected_node = st.selectbox("Select Node", nodes, key="combined_node")
            selected_node_clean = str(selected_node).strip().upper()
            eng_data = eng_df[eng_df["ID"] == selected_node_clean]
            qual_data = qual_df[qual_df["ID"] == selected_node_clean]
            eng_row = eng_data.iloc[0] if not eng_data.empty else None
            qual_row = qual_data.iloc[0] if not qual_data.empty else None

            col1, col2 = st.columns(2)

            # ENGINEERING VIEW

            with col1:
                st.subheader("🛠 Basic Engineering View")

                if eng_row is not None:
                    st.metric("💰 Cost (€)", eng_row.get("Cost_(€)", "N/A"))
                    st.metric("🔢 Number of Components", eng_row.get("Number_of_Components", "N/A"))
                    st.metric("💵 Total Cost (€)", eng_row.get("Total_Cost_(€)", "N/A"))
                    st.metric("🎯 Target", eng_row.get("Target", "N/A"))
                    st.metric("📊 KPI (1-10)", eng_row.get("KPI", "N/A"))
                    st.metric("⚙️ OEE (%)", eng_row.get("OEE", "N/A"))

                    st.write("🔗 Part Of:", eng_row.get("Part_of", "N/A"))
                    st.write("📈 Impact On:", eng_row.get("Impact_on", "N/A"))
                else:
                    st.warning("No Engineering data for this node")


            # QUALITY VIEW

            with col2:
                st.subheader("✅ Quality View")

                if qual_row is not None:
                    st.metric("Parameter", qual_row.get("Parameter", "N/A"))
                    st.metric("Threshold", qual_row.get("Threshold", "N/A"))
                    st.metric("Actual Value", qual_row.get("Actual_Value", "N/A"))
                    st.metric("Status", qual_row.get("Status_(OK/NOK)", "N/A"))

                    st.write("Influence:", qual_row.get("Influence", "N/A"))
                    st.write("Dependency:", qual_row.get("Dependency", "N/A"))
                else:
                    st.warning("No Quality data for this node")


            # DATA ANALYTICS

            st.divider()
            st.subheader("📊 Data Analytics")

            analysis_option = st.selectbox(
                "Select Analysis",
                [
                    "KPI Dashboard",
                    "OEE Comparison",
                    "Cost vs OEE",
                    "Quality Status Distribution",
                    "Threshold vs Value"
                ],
                key="analytics_select"
            )
            if analysis_option == "KPI Dashboard":
                show_kpi_dashboard(eng_df)

            elif analysis_option == "OEE Comparison":
                plot_oee_comparison(eng_df, selected_node)

            elif analysis_option == "Cost vs OEE":
                plot_cost_vs_oee(eng_df, selected_node)

            elif analysis_option == "Quality Status Distribution":
                plot_quality_distribution(qual_df)

            elif analysis_option == "Threshold vs Value":
                plot_threshold_vs_value(qual_df, selected_node)
            st.divider()

    else:
        st.info("Upload Excel to activate Engineering & Quality View")


# GRAPH ANALYSIS TAB

with tab4:
    st.header("📈 Graph-Based Analysis Dashboard")

    if G.number_of_nodes() == 0:
        st.info("Load demo data or upload a JSON/XML file to run analysis.")
        st.stop()


    # 1. SYSTEM OVERVIEW

    st.subheader("📊 System Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Nodes", G.number_of_nodes())
    col2.metric("Edges", G.number_of_edges())

    is_dag = nx.is_directed_acyclic_graph(G)
    col3.metric("Acyclic", "Yes" if is_dag else "No")

    components = list(nx.weakly_connected_components(G))
    col4.metric("Components", len(components))

    if not is_dag:
        st.error("❌ Graph contains cycles (Invalid production flow)")
    else:
        st.success("✅ Graph is acyclic (Valid production flow)")

    st.divider()


    # 2. REQUIREMENT VALIDATION

    with st.expander("✔ Requirement Validation", expanded=True):

        st.markdown("### Product Reachability")

        products = [n for n, d in G.nodes(data=True) if d["type"] == "Product"]
        processes = [n for n, d in G.nodes(data=True) if d["type"] == "Process"]

        unreachable = [
            p for p in products
            if not any(nx.has_path(G, pr, p) for pr in processes)
        ]

        if not unreachable:
            st.success("All products reachable ✅")
        else:
            st.error(f"Unreachable products: {unreachable}")

        st.markdown("### 🚛 Vehicle Design Requirement Checks")
        show_table(check_car_design_requirements(G, st.session_state.get("eng_df")))

    #  3. DEPENDENCY ANALYSIS

    with st.expander("🔗 Dependency Analysis"):

        nodes = list(G.nodes)

        if len(nodes) > 0:
            node = st.selectbox("Select Node", nodes, key="analysis_node")

            upstream = list(nx.ancestors(G, node))
            downstream = list(nx.descendants(G, node))

            col1, col2 = st.columns(2)

            with col1:
                records = []

                for n in upstream:
                    data = G.nodes[n]
                    records.append({
                        "Node ID": n,
                        "Name": data.get("label", "N/A"),
                        "Type": data.get("type", "N/A"),
                        "Direction": "Upstream"
                    })

                for n in downstream:
                    data = G.nodes[n]
                    records.append({
                        "Node ID": n,
                        "Name": data.get("label", "N/A"),
                        "Type": data.get("type", "N/A"),
                        "Direction": "Downstream"
                    })

                # Convert to DataFrame
                dep_df = pd.DataFrame(records)


                # DISPLAY TABLE

                st.markdown("### 📋 Dependency Table")

                if not dep_df.empty:
                    show_table(dep_df)
                else:
                    st.info("No dependencies found")
            with col2:
                st.markdown("### 🌐 Dependency Graph")
                sub_nodes = set([node] + upstream + downstream)
                subG = G.subgraph(sub_nodes).copy()

                st.graphviz_chart(
                    draw_highlight_subgraph(subG, node),
                    use_container_width=True
                )

        else:
            st.info("No nodes available")

    # PATH ANALYSIS

    with st.expander("🔀 Path Analysis"):
        nodes = list(G.nodes)
        if len(nodes) > 1:

            col1, col2 = st.columns(2)
            with col1:
                source = st.selectbox("Select Source Node", nodes, key="path_source")
            with col2:
                target = st.selectbox("Select Target Node", nodes, key="path_target")

            if source != target:


                # SHORTEST PATH

                st.markdown("### 🔍 Shortest Path")

                try:
                    shortest_path = nx.shortest_path(G, source=source, target=target)
                    if len(shortest_path) == 1:
                        st.warning("Only one node in path — graph not meaningful")

                    col1, col2 = st.columns([1, 2])

                    with col1:
                        records = []
                        for i, n in enumerate(shortest_path):
                            data = G.nodes[n]
                            records.append({
                                "Step": i + 1,
                                "Node ID": n,
                                "Name": data.get("label", ""),
                                "Type": data.get("type", "")
                            })

                        st.dataframe(
                            pd.DataFrame(records),
                            use_container_width=True,
                            hide_index=True
                        )

                    with col2:
                        st.graphviz_chart(
                            draw_path_subgraph(G, shortest_path, source, target),
                            use_container_width=True
                        )

                except nx.NetworkXNoPath:
                    st.error("No path exists between selected nodes")


                # LONGEST PATH

                st.markdown("### 🔍 Longest Path")

                if nx.is_directed_acyclic_graph(G):

                    all_paths = list(nx.all_simple_paths(G, source=source, target=target))

                    if all_paths:
                        longest_path = max(all_paths, key=len)
                        if len(longest_path) == 1:
                            st.warning("Only one node in path — graph not meaningful")

                        col1, col2 = st.columns([1, 2])

                        with col1:
                            records = []
                            for i, n in enumerate(longest_path):
                                data = G.nodes[n]
                                records.append({
                                    "Step": i + 1,
                                    "Node ID": n,
                                    "Name": data.get("label", ""),
                                    "Type": data.get("type", "")
                                })

                            st.dataframe(
                                pd.DataFrame(records),
                                use_container_width=True,
                                hide_index=True
                            )

                        with col2:
                            st.graphviz_chart(
                                draw_path_subgraph(G, longest_path, source, target),
                                use_container_width=True
                            )
                    else:
                        st.warning("No path found")

                else:
                    st.warning("Longest path requires acyclic graph")

            else:
                st.info("Select two different nodes")

        else:
            st.info("Not enough nodes in graph")

    # 4. STRUCTURAL INSIGHTS

    with st.expander("🔍 Structural Insights"):

        st.markdown("### Similar Node Structures")

        struct = {}
        for n in G.nodes:
            key = (G.in_degree(n), G.out_degree(n))
            struct.setdefault(key, []).append(n)

        similar_groups = [group for group in struct.values() if len(group) > 1]

        if similar_groups:
            show_table(pd.DataFrame({"Groups": similar_groups}))
        else:
            st.info("No similar structures found")

        st.markdown("### Subgraphs ≥ 5 Nodes")

        large_subgraphs = [list(c) for c in components if len(c) >= 5]

        if large_subgraphs:
            show_table(pd.DataFrame({"Subgraphs": large_subgraphs}))
        else:
            st.info("No large subgraphs found")


    # 5. CONNECTIVITY ANALYSIS

    with st.expander("⚠ Connectivity Analysis"):

        st.markdown("### Disconnected Segments")

        if len(components) > 1:
            for i, comp in enumerate(components):
                st.write(f"Segment {i+1}: {list(comp)}")
        else:
            st.success("Graph is fully connected")

        st.markdown("### 🔎 Disconnected Segment Table")
        show_table(find_disconnected_segments(G))


    # 6. ADVANCED ALGORITHMS

    with st.expander("🧪 Advanced Algorithm Insights"):

        st.markdown("### View-Specific Dependencies")

        selected_view = st.selectbox(
            "Select View",
            ["Basic Engineering", "Quality"],
            key="algo_view"
        )

        show_table(get_view_specific_dependencies(G, selected_view))

        st.markdown("### Similarly Structured Elements (Advanced)")
        show_table(find_similarly_structured_elements(G))

        st.markdown("### Subgraphs with Minimum Nodes (≥5)")
        show_table(find_subgraphs_with_min_nodes(G, min_nodes=5))

# SAVE

st.session_state.G = G