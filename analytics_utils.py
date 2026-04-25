import plotly.graph_objects as go
import streamlit as st

def show_kpi_dashboard(eng_df):
    if eng_df.empty:
        st.warning("No Engineering data available")
        return

    avg_oee = eng_df["OEE"].mean() if "OEE" in eng_df.columns else None
    total_cost = eng_df["Total_Cost_(€)"].sum() if "Total_Cost_(€)" in eng_df.columns else None
    avg_kpi = eng_df["KPI"].mean() if "KPI" in eng_df.columns else None
    total_components = eng_df["Number_of_Components"].sum() if "Number_of_Components" in eng_df.columns else None

    st.markdown("### 📊 KPI Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("⚙️ Avg OEE", f"{avg_oee:.2f}%" if avg_oee is not None else "N/A")
    col2.metric("💰 Total Production Cost", f"€{total_cost:.2f}" if total_cost else "N/A")
    col3.metric("📈 Average KPI", f"{avg_kpi:.2f}" if avg_kpi else "N/A")
    col4.metric("🔢 Total Components", f"{total_components:.0f}" if total_components else "N/A")

def plot_oee_comparison(eng_df, selected_node):
    if "OEE" not in eng_df.columns:
        st.warning("OEE column not found")
        return

    df_plot = eng_df.dropna(subset=["OEE"]).copy()

    colors = [
        "red" if row["ID"] == selected_node else "lightblue"
        for _, row in df_plot.iterrows()
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot["OEE"],
        y=df_plot["ID"],
        orientation='h',
        marker=dict(color=colors),
        text=df_plot["OEE"].apply(lambda x: f"{x:.2f}%"),
        textposition="outside"
    ))

    fig.update_layout(
        title="OEE Comparison Across Nodes",
        xaxis_title="OEE (%)",
        yaxis_title="Node ID",
        height=400,
        xaxis=dict(ticksuffix="%")
    )
    st.plotly_chart(fig, use_container_width=True)

# QUALITY STATUS DISTRIBUTION
def plot_quality_distribution(qual_df):
    if "Status_(OK/NOK)" not in qual_df.columns:
        st.warning("Status column not found")
        return

    status_counts = qual_df["Status_(OK/NOK)"].value_counts()

    fig = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.4,
        marker=dict(colors=["green", "red"])
    )])

    fig.update_layout(title="Quality Status Distribution")

    st.plotly_chart(fig, use_container_width=True)


# THRESHOLD VS VALUE
def plot_threshold_vs_value(qual_df, selected_node):
    if "Threshold" not in qual_df.columns or "Actual_Value" not in qual_df.columns:
        st.warning("Required columns not found")
        return

    df_plot = qual_df.dropna(subset=["Threshold", "Actual_Value"]).copy()

    colors_threshold = [
        "red" if row["ID"] == selected_node else "lightblue"
        for _, row in df_plot.iterrows()
    ]

    colors_value = [
        "darkred" if row["ID"] == selected_node else "orange"
        for _, row in df_plot.iterrows()
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_plot["ID"],
        y=df_plot["Threshold"],
        name="Threshold",
        marker_color=colors_threshold
    ))

    fig.add_trace(go.Bar(
        x=df_plot["ID"],
        y=df_plot["Actual_Value"],
        name="Actual Value",
        marker_color=colors_value
    ))

    fig.update_layout(
        title="Threshold vs Actual Value",
        xaxis_title="Node ID",
        yaxis_title="Value",
        barmode='group',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_cost_vs_oee(eng_df, selected_node):

    if "OEE" not in eng_df.columns or "Total_Cost_(€)" not in eng_df.columns:
        st.warning("Required columns not found")
        return

    df_plot = eng_df.dropna(subset=["OEE", "Total_Cost_(€)"]).copy()

    colors = [
        "red" if row["ID"] == selected_node else "blue"
        for _, row in df_plot.iterrows()
    ]

    sizes = [
        15 if row["ID"] == selected_node else 10
        for _, row in df_plot.iterrows()
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_plot["Total_Cost_(€)"],
        y=df_plot["OEE"],
        mode='markers+text',
        text=df_plot["ID"],
        textposition="top center",
        marker=dict(
            size=sizes,
            color=colors
        ),
        hovertemplate=
        "<b>ID:</b> %{text}<br>" +
        "<b>Cost:</b> %{x}<br>" +
        "<b>OEE:</b> %{y:.2f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Cost vs OEE Analysis",
        xaxis_title="Total Cost (€)",
        yaxis_title="OEE (%)",
        height=450,
        yaxis=dict(ticksuffix="%")
    )

    st.plotly_chart(fig, use_container_width=True)