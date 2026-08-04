"""
Knowledge Graphing Module for Project A.E.G.I.S.
Uses NetworkX to map environmental evidence (bedsheets, wall patterns, electrical sockets,
ceiling fans) as nodes and edges for a single case file.

Historical cross-case correlation is only performed when a caller provides a verified
external case database (list of dicts with 'case_id' and 'entities' keys).
If no historical database is supplied the module explicitly returns an unavailability
signal — it NEVER fabricates historical cases or fake forensic links.
"""

import networkx as nx
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# REMOVED: get_default_historical_cases()
# The three hardcoded fabricated case entries (CASE-KP-2025-101, CASE-KP-2026-204,
# CASE-KP-2026-309) that previously caused guaranteed cross-case correlation alerts
# on virtually every upload have been permanently deleted.
# ---------------------------------------------------------------------------

# Sentinel returned by analyze_cross_case_correlations when no real DB is available.
HISTORICAL_DB_UNAVAILABLE = "__HISTORICAL_DB_UNAVAILABLE__"


def normalize_entity_name(raw_name: str) -> str:
    """Normalises live computed entity strings for NetworkX graph node matching."""
    if "(" in raw_name:
        return raw_name.split("(")[0].strip()
    return raw_name.strip()


def build_case_knowledge_graph(current_case_id: str,
                                current_entities: list,
                                historical_cases: list = None):
    """
    Builds a NetworkX graph containing only the current case and its extracted
    environmental entities.

    historical_cases:
        If the caller passes a verified list of real historical case dicts
        (each with 'case_id': str and 'entities': list[str]) they will be
        included and cross-case correlation becomes meaningful.

        If None (the default) no historical nodes are added and
        analyze_cross_case_correlations will report the database as unavailable.

    Returns
    -------
    G : nx.Graph
        Graph with node attribute 'type' in:
          - "current_case"        — the active evidence file
          - "environmental_entity" — entity extracted from that file
          - "historical_case"     — a real historical case (only if DB supplied)
    """
    G = nx.Graph()

    # Current case node
    G.add_node(
        current_case_id,
        type="current_case",
        label=f"TARGET: {current_case_id}",
        color="#00d2ff",
        size=24
    )

    # Current-case environmental entity nodes (from live VLM extraction)
    for ent in current_entities:
        raw_name = ent["entity"] if isinstance(ent, dict) else str(ent)
        norm_name = normalize_entity_name(raw_name)
        if not G.has_node(norm_name):
            G.add_node(
                norm_name,
                type="environmental_entity",
                label=norm_name,
                color="#ffb703",
                size=16
            )
        G.add_edge(current_case_id, norm_name, weight=2)

    # Historical cases — only added when the caller supplies a real external DB
    if historical_cases:
        for case in historical_cases:
            c_id = case.get("case_id", "UNKNOWN")
            G.add_node(
                c_id,
                type="historical_case",
                label=f"HIST: {c_id}",
                color="#94a3b8",
                size=18
            )
            for ent_name in case.get("entities", []):
                norm_hist = normalize_entity_name(ent_name)
                if not G.has_node(norm_hist):
                    G.add_node(
                        norm_hist,
                        type="environmental_entity",
                        label=norm_hist,
                        color="#ffb703",
                        size=16
                    )
                G.add_edge(c_id, norm_hist, weight=1)

    return G


def generate_plotly_network_figure(G):
    """
    Generates a 2-D interactive Plotly graph figure for Streamlit rendering.
    Layout and styling are preserved from the original implementation.
    """
    pos = nx.spring_layout(G, k=0.6, seed=42)

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color="#2a364f"),
        hoverinfo="none",
        mode="lines"
    )

    node_x, node_y = [], []
    node_text, node_color, node_size = [], [], []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        data = G.nodes[node]
        node_text.append(data.get("label", str(node)))
        node_color.append(data.get("color", "#00d2ff"))
        node_size.append(data.get("size", 16))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=[G.nodes[n].get("label", "") for n in G.nodes()],
        textposition="top center",
        hoverinfo="text",
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line_width=2,
            line=dict(color="#0a0e17")
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text="<b>Visuo-Acoustic Environmental Intelligence Knowledge Graph</b>",
                font=dict(color="#00d2ff", size=18)
            ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=20, r=20, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor="#0a0e17",
            plot_bgcolor="#0a0e17"
        )
    )

    return fig


def analyze_cross_case_correlations(G, current_case_id: str,
                                     historical_db_connected: bool = False):
    """
    Finds real historical cases that share common environmental entity nodes with
    the current case.

    Parameters
    ----------
    G : nx.Graph
        The knowledge graph built by build_case_knowledge_graph.
    current_case_id : str
        Node ID of the active evidence case.
    historical_db_connected : bool
        Must be explicitly set to True by the caller when a real external
        historical database was passed to build_case_knowledge_graph.
        Defaults to False so that the system never silently fabricates matches.

    Returns
    -------
    HISTORICAL_DB_UNAVAILABLE : str sentinel
        Returned when historical_db_connected is False.
        The dashboard interprets this to display the "Unavailable" status.

    list[dict]
        Returned only when historical_db_connected is True.
        Each dict contains 'case_id', 'shared_count', 'shared_entities'.
    """
    # Explicit gate: no real DB → no correlations attempted
    if not historical_db_connected:
        return HISTORICAL_DB_UNAVAILABLE

    if not G.has_node(current_case_id):
        return []

    current_entities = set(G.neighbors(current_case_id))
    correlated = []

    for node in G.nodes():
        if G.nodes[node].get("type") == "historical_case":
            hist_entities = set(G.neighbors(node))
            shared = current_entities.intersection(hist_entities)
            if shared:
                correlated.append({
                    "case_id": node,
                    "shared_count": len(shared),
                    "shared_entities": list(shared)
                })

    return sorted(correlated, key=lambda c: c["shared_count"], reverse=True)
