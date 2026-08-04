"""
Agent 6.5 / 7: Knowledge Graph Agent
Wraps knowledge_graph.py. Takes environmental entities extracted by VisionIntelligenceAgent
and builds an interactive NetworkX knowledge graph mapping objects, attributes, and cross-case links.
"""
import time
import os
import sys
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import knowledge_graph

class KnowledgeGraphAgent(BaseAgent):
    name = "Knowledge Graph Agent"
    purpose = "Compiles extracted environmental entities into NetworkX knowledge graph nodes and Plotly visualization figures."
    inputs = ["VLM Environmental Objects List", "Case ID"]
    outputs = ["NetworkX Graph Data", "Plotly Figure Dict", "Node/Edge Counts"]
    capabilities = ["NetworkX Topological Graphing", "Plotly Figure Generation", "Cross-Case Node Correlation"]
    produces = ["NetworkX Environmental Relationship Graph", "Plotly Interactive Network Figure", "Cross-Case Correlation Graph Nodes"]
    consumes = ["Vision Intelligence Environmental Entities"]
    dependencies = ["Vision Intelligence Agent"]
    limitations = ["Dependent on Vision Intelligence entity extraction."]
    typical_runtime_sec = 0.3

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            vision_res = context.agent_results.get("Vision Intelligence Agent", {}).get("output", {})
            entities = vision_res.get("environmental_objects", [])

            reasoning.append(f"Compiling NetworkX topological knowledge graph for target Case '{context.case_id}'...")
            
            G = knowledge_graph.build_case_knowledge_graph(
                current_case_id=context.case_id,
                current_entities=entities
            )

            node_count = G.number_of_nodes()
            edge_count = G.number_of_edges()
            reasoning.append(f"Knowledge graph constructed with {node_count} nodes and {edge_count} directional relationship edges.")

            fig = knowledge_graph.generate_plotly_network_figure(G)
            context.knowledge_graph_fig = fig.to_dict()

            correlations = knowledge_graph.analyze_cross_case_correlations(
                G, current_case_id=context.case_id, historical_db_connected=False
            )
            
            if correlations == knowledge_graph.HISTORICAL_DB_UNAVAILABLE:
                reasoning.append("Cross-case historical database is disconnected (Reporting historical DB unavailable).")
                corr_status = "unavailable"
            else:
                corr_status = "completed"

            context.add_reasoning(self.name, f"Graph compiled ({node_count} nodes).")

            output = {
                "nodes": node_count,
                "edges": edge_count,
                "historical_db_status": corr_status,
                "entities_mapped": [e["entity"] if isinstance(e, dict) else str(e) for e in entities],
                "fig": context.knowledge_graph_fig
            }

            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=95.0,
                input_data={"case_id": context.case_id, "entities_count": len(entities)},
                output_data=output,
                reasoning=reasoning,
                recommend_next=["RiskAssessmentAgent"]
            )

        except Exception as e:
            err_msg = f"Knowledge Graph compilation failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={"case_id": context.case_id},
                output_data={"nodes": 0, "edges": 0},
                reasoning=reasoning,
                error=err_msg
            )
