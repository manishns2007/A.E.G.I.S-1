"""
Agent 9: Legal Reasoning Agent
Wraps legal_docket.py. Reads all previous agent outputs from the InvestigationContext 
and generates a court-admissible BSA 2023 Section 63 forensic certificate.
"""
import time
import os
import sys
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import legal_docket

class LegalReasoningAgent(BaseAgent):
    name = "Legal Reasoning Agent"
    description = "Generates Bharatiya Sakshya Adhiniyam (BSA) 2023 Section 63 compliant forensic certificate."
    capabilities = ["Statutory Admissibility Reporting", "Cryptographic Hash Sealing", "Multi-Agent Synthesis"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []

        try:
            # 1. Gather all required outputs from context
            privacy_summary = context.agent_results.get("Privacy Shield Agent", {}).get("output", {})
            enf_summary = context.agent_results.get("ENF Physics Agent", {}).get("output", {})
            corneal_summary = context.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
            vlm_summary = context.agent_results.get("Vision Intelligence Agent", {}).get("output", {})
            fusion_summary = context.fusion_output
            
            reasoning.append("Drafting Section 63 BSA 2023 Forensic Admissibility Certificate...")
            reasoning.append(f"Sealing chain of custody with SHA-256 hash: {context.sha256[:12]}...")

            # 2. Generate Docket
            docket_res = legal_docket.generate_bsa_legal_docket(
                case_id=context.case_id,
                investigator_id="AEGIS-ORCHESTRATOR",
                media_filename=context.original_filename,
                media_bytes=context.file_bytes,
                privacy_summary=privacy_summary,
                enf_summary=enf_summary,
                corneal_summary=corneal_summary,
                vlm_summary=vlm_summary
            )

            context.legal_docket = docket_res

            # Incorporate Fusion Intelligence if available
            is_auth = fusion_summary.get("is_authentic", docket_res.get("is_authentic", True))
            verdict_badge = fusion_summary.get("verdict_badge", docket_res.get("verdict_badge", "VERDICT UNAVAILABLE"))

            docket_res["is_authentic"] = is_auth
            docket_res["verdict_badge"] = verdict_badge

            reasoning.append(f"Final Judicial System Verdict: {verdict_badge}")
            reasoning.append("Legal Docket generation successful. Admissibility reporting complete.")

            context.add_reasoning(self.name, "Legal Report drafted. Investigation complete.")

            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=100.0,
                input_data={"case_id": context.case_id},
                output_data=docket_res,
                reasoning=reasoning
            )

        except Exception as e:
            err_msg = f"Legal Docket generation failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={},
                output_data={},
                reasoning=reasoning,
                error=err_msg
            )
