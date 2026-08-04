"""
Agent 8: Knowledge Graph Agent
Wraps knowledge_graph.py. Translates extracted Vision entities into a NetworkX graph structure
and prepares visual artifacts for the A.E.G.I.S. Investigation Workspace.
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
    description = "Compiles semantic entities into an interactive NetworkX evidence graph."
    capabilities = ["NetworkX Graph Generation", "Node Entity Extraction", "Plotly Visualization"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            # Get VLM entities from context
            vision_res = context.agent_results.get("Vision Intelligence Agent", {}).get("output", {})
            environmental_objects = vision_res.get("environmental_objects", [])

            if not environmental_objects:
                reasoning.append("No environmental entities available from Vision Intelligence Agent to map.")
                status = "warning"
            else:
                reasoning.append(f"Ingesting {len(environmental_objects)} environmental entities into topological graph engine...")
                status = "completed"

            # Build Graph
            G = knowledge_graph.build_case_knowledge_graph(
                context.case_id,
                environmental_objects,
                None  # Explicitly NO historical DB to prevent fake cases
            )
            
            # Generate Visual Graph
            graph_fig = knowledge_graph.generate_plotly_network_figure(G)
            
            # Analyze Correlations
            graph_correlations = knowledge_graph.analyze_cross_case_correlations(G, context.case_id, False)

            node_count = G.number_of_nodes()
            edge_count = G.number_of_edges()

            reasoning.append(f"NetworkX graph compiled with {node_count} nodes and {edge_count} relationships.")
            reasoning.append("Cross-case historical database is not connected. Correlation analysis suspended.")

            context.add_reasoning(self.name, f"Graph compiled ({node_count} nodes).")
            
            context.knowledge_graph_fig = graph_fig

            output = {
                "nodes": node_count,
                "edges": edge_count,
                "graph_fig": graph_fig,
                "graph_correlations": graph_correlations,
                "historical_db_connected": False
            }

            return self.format_response(
                status=status,
                processing_time=time.time() - start,
                confidence=95.0 if environmental_objects else 0.0,
                input_data={"entity_count": len(environmental_objects)},
                output_data=output,
                reasoning=reasoning
            )

        except Exception as e:
            err_msg = f"Knowledge Graph generation failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={},
                output_data={"nodes": 0, "edges": 0, "historical_db_connected": False},
                reasoning=reasoning,
                error=err_msg
            )
