"""
Agent 8: Risk Assessment Agent
Evaluates findings from previous agents to assign a Case Risk Level (Low, Medium, High, Critical).
Placed before Intelligence Fusion.
"""
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, InvestigationContext

class RiskAssessmentAgent(BaseAgent):
    name = "Risk Assessment Agent"
    description = "Evaluates findings from all forensic vectors to assign an overall Case Risk Level."
    capabilities = ["Risk Scoring", "Anomaly Aggregation", "Threat Assessment"]

    def execute(self, context: InvestigationContext) -> Dict[str, Any]:
        start = time.time()
        reasoning: List[str] = []
        
        try:
            privacy_res = context.agent_results.get("Privacy Shield Agent", {}).get("output", {})
            enf_res = context.agent_results.get("ENF Physics Agent", {}).get("output", {})
            corneal_res = context.agent_results.get("Corneal Specular Topology Agent", {}).get("output", {})
            
            risk_factors = []
            
            # Check Privacy Risks
            faces = privacy_res.get("count", 0)
            if faces > 0:
                risk_factors.append(f"Contains {faces} human subjects (PII exposure risk).")
            
            # Check Synthesis Risks
            enf_auth = enf_res.get("is_authentic", True)
            if not enf_auth:
                risk_factors.append("ENF grid hum anomaly detected (High likelihood of deepfake/synthesis).")
                
            corneal_auth = corneal_res.get("is_authentic", True)
            if not corneal_auth:
                risk_factors.append("Corneal reflection asymmetry detected (High likelihood of deepfake/synthesis).")
            
            # Determine Risk Level
            if len(risk_factors) >= 2 or (not enf_auth or not corneal_auth):
                risk_level = "CRITICAL"
                confidence = 95.0
            elif len(risk_factors) == 1:
                risk_level = "MEDIUM"
                confidence = 80.0
            else:
                risk_level = "LOW"
                confidence = 99.0
                risk_factors.append("No significant forensic anomalies or PII risks detected.")
                
            reasoning.append(f"Risk Assessment completed. Level: {risk_level}")
            for factor in risk_factors:
                reasoning.append(f"Factor: {factor}")
                
            context.add_reasoning(self.name, f"Assigned Risk Level: {risk_level}")
            
            output = {
                "risk_level": risk_level,
                "risk_factors": risk_factors
            }
            
            return self.format_response(
                status="completed",
                processing_time=time.time() - start,
                confidence=confidence,
                input_data={"faces_detected": faces, "enf_authentic": enf_auth, "corneal_authentic": corneal_auth},
                output_data=output,
                reasoning=reasoning,
                recommend_next=["IntelligenceFusionAgent"]
            )
            
        except Exception as e:
            err_msg = f"Risk Assessment failed: {str(e)}"
            context.add_reasoning(self.name, err_msg)
            return self.format_response(
                status="failed",
                processing_time=time.time() - start,
                confidence=0.0,
                input_data={},
                output_data={"risk_level": "UNKNOWN", "risk_factors": []},
                reasoning=reasoning,
                recommend_next=["IntelligenceFusionAgent"],
                error=err_msg
            )
