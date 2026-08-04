"""
Knowledge Graphing Module for Project A.E.G.I.S.
Uses NetworkX to map environmental evidence (bedsheets, wall patterns, electrical sockets, ceiling fans)
as nodes and edges across disparate case files to correlate real-world threats visually.
"""

import networkx as nx
import plotly.graph_objects as go

def get_default_historical_cases():
    """Returns sample historical Cyberdome case files for cross-case correlation demo."""
    return [
        {
            "case_id": "CASE-KP-2025-101",
            "date": "2025-11-14",
            "location": "Kochi Sub-District",
            "entities": [
                "Patterned Surface / Fabric",
                "Wall-Mounted Fixture ROI",
                "Ceiling Fixture / Overhead Mount"
            ]
        },
        {
            "case_id": "CASE-KP-2026-204",
            "date": "2026-02-02",
            "location": "Trivandrum Central",
            "entities": [
                "Wall Structural Texture Anomaly",
                "Wall-Mounted Fixture ROI",
                "Teak Wood Bed Frame"
            ]
        },
        {
            "case_id": "CASE-KP-2026-309",
            "date": "2026-05-19",
            "location": "Kozhikode North",
            "entities": [
                "Patterned Surface / Fabric",
                "Wall Structural Texture Anomaly",
                "Blue Floral Curtain"
            ]
        }
    ]

def normalize_entity_name(raw_name: str) -> str:
    """Normalizes live computed entity strings for NetworkX graph node matching."""
    if "(" in raw_name:
        return raw_name.split("(")[0].strip()
    return raw_name.strip()

def build_case_knowledge_graph(current_case_id: str, current_entities: list, historical_cases: list = None):
    """
    Builds a NetworkX graph connecting Case nodes to Environmental Entity nodes.
    """
    if historical_cases is None:
        historical_cases = get_default_historical_cases()
        
    G = nx.Graph()
    
    # Add Current Case node
    G.add_node(current_case_id, type="current_case", label=f"TARGET: {current_case_id}", color="#00d2ff", size=24)
    
    # Add current case entities
    for ent in current_entities:
        raw_name = ent["entity"] if isinstance(ent, dict) else str(ent)
        norm_name = normalize_entity_name(raw_name)
        if not G.has_node(norm_name):
            G.add_node(norm_name, type="environmental_entity", label=norm_name, color="#ffb703", size=16)
        G.add_edge(current_case_id, norm_name, weight=2)
        
    # Add historical cases
    for case in historical_cases:
        c_id = case["case_id"]
        G.add_node(c_id, type="historical_case", label=f"HIST: {c_id}", color="#94a3b8", size=18)
        for ent_name in case["entities"]:
            norm_hist = normalize_entity_name(ent_name)
            if not G.has_node(norm_hist):
                G.add_node(norm_hist, type="environmental_entity", label=norm_hist, color="#ffb703", size=16)
            G.add_edge(c_id, norm_hist, weight=1)
            
    return G

def generate_plotly_network_figure(G):
    """
    Generates a 2D interactive Plotly graph figure for Streamlit rendering.
    """
    pos = nx.spring_layout(G, k=0.6, seed=42)
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color='#2a364f'),
        hoverinfo='none',
        mode='lines'
    )
    
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    
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
        mode='markers+text',
        text=[G.nodes[n].get("label", "") for n in G.nodes()],
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line_width=2,
            line=dict(color='#0a0e17')
        )
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title=dict(
                        text='<b>Visuo-Acoustic Environmental Intelligence Knowledge Graph</b>',
                        font=dict(color='#00d2ff', size=18)
                    ),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=20, r=20, t=50),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#0a0e17'
                ))
                
    return fig

def analyze_cross_case_correlations(G, current_case_id: str):
    """
    Finds historical cases that share common environmental entity nodes with the current case.
    """
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
