"""
A.E.G.I.S. Abstract LLM Provider Layer
Supports Groq (Llama-3), Gemini, and Procedural Fallback with automatic provider priority selection and failover.

Strict Rule: LLM Providers ONLY handle orchestration reasoning, state evaluation, goal progression, and agent selection.
They NEVER generate forensic verdicts or alter physical vector findings.
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional

# Valid Agent Keys
VALID_AGENTS = [
    "EvidenceIntakeAgent",
    "PrivacyShieldAgent",
    "ENFPhysicsAgent",
    "CornealTopologyAgent",
    "VisionIntelligenceAgent",
    "KnowledgeGraphAgent",
    "RiskAssessmentAgent",
    "IntelligenceFusionAgent",
    "LegalReasoningAgent",
    "FINISH"
]

SYSTEM_PROMPT = """You are the Investigation Orchestrator Supervisor for A.E.G.I.S.
You examine the current Investigation State, Investigation Goals, Agent Capability Manifests, and Evidence Confidence Evolution.

Your task is to perform Planner Self-Evaluation and select the EXACT NEXT specialized forensic agent to run.

SELF-EVALUATION QUESTIONS TO ANSWER IN YOUR HEAD:
1. What do I know?
2. What don't I know?
3. Which hypothesis is currently strongest?
4. Which agent can reduce uncertainty the most?
5. What evidence is still required?
6. Should the investigation finish?

RULES:
1. Always start with 'EvidenceIntakeAgent' if intake is not completed.
2. Next run 'PrivacyShieldAgent' if privacy is not completed.
3. After PrivacyShieldAgent completes: if input is VIDEO, run 'ENFPhysicsAgent'. If input is IMAGE, run 'CornealTopologyAgent'.
4. Next run 'VisionIntelligenceAgent' to extract environmental background entities.
5. Next run 'KnowledgeGraphAgent' to compile relationship graph.
6. Next run 'RiskAssessmentAgent' to evaluate threat level.
7. Next run 'IntelligenceFusionAgent' to synthesize evidence narrative.
8. Always run 'LegalReasoningAgent' last to draft Section 63 BSA certificate.
9. When LegalReasoningAgent has completed, return 'FINISH'.

Respond with ONLY valid JSON containing:
{
  "what_i_know": ["<fact1>", "<fact2>"],
  "what_i_dont_know": ["<uncertainty1>", "<uncertainty2>"],
  "strongest_hypothesis": "<name of strongest hypothesis>",
  "next_agent": "<AgentClassName or FINISH>",
  "reasoning": "<1-2 sentence explanation of why this agent was selected based on evidence state and recommendations>",
  "expected_outcome": "<what outcome is expected from this agent dispatch>"
}
"""

class LLMProvider(ABC):
    """Abstract interface for LLM Orchestration Providers."""
    name: str = "BaseProvider"

    @abstractmethod
    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        """
        Observes InvestigationState and returns (next_agent_name, reasoning_explanation, self_eval_dict).
        """
        pass


class GroqProvider(LLMProvider):
    """Groq LPU accelerated provider using Llama-3.3-70b / Llama-3.1-8b."""
    name = "Groq (Llama-3.3-70B)"

    def __init__(self, api_key: str):
        import groq
        self.client = groq.Groq(api_key=api_key)

    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        state_summary = {
            "case_id": state.get("case_id"),
            "media_type": state.get("media_type", "IMAGE"),
            "completed_agents": state.get("completed_agents", []),
            "current_goal": state.get("goals", [{}])[state.get("current_goal_idx", 0)].get("goal", "Authenticate Media"),
            "hypotheses": state.get("hypotheses", {}),
            "unresolved_issues": state.get("investigation_memory", {}).get("unresolved_issues", []),
            "active_vectors": state.get("active_vectors", []),
            "court_ready": state.get("court_ready", False)
        }

        user_msg = f"Current Investigation State:\n{json.dumps(state_summary, indent=2)}\nSelect next agent in JSON."

        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                res = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                text = res.choices[0].message.content
                data = json.loads(text)
                next_agent = data.get("next_agent", "FINISH")
                reasoning = data.get("reasoning", f"Groq ({model}) selected {next_agent} based on evidence state.")
                full_reasoning = f"[Groq {model}] {reasoning}"
                return next_agent, full_reasoning, data
            except Exception as e:
                last_err = e

        raise Exception(f"Groq API call failed: {last_err}")


class GeminiProvider(LLMProvider):
    """Gemini Provider using google-genai SDK and gemini-flash-latest."""
    name = "Gemini (gemini-flash-latest)"

    def __init__(self, api_key: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)

    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        state_summary = {
            "case_id": state.get("case_id"),
            "media_type": state.get("media_type", "IMAGE"),
            "completed_agents": state.get("completed_agents", []),
            "current_goal": state.get("goals", [{}])[state.get("current_goal_idx", 0)].get("goal", "Authenticate Media"),
            "hypotheses": state.get("hypotheses", {}),
            "unresolved_issues": state.get("investigation_memory", {}).get("unresolved_issues", []),
            "active_vectors": state.get("active_vectors", []),
            "court_ready": state.get("court_ready", False)
        }

        user_msg = f"{SYSTEM_PROMPT}\n\nCurrent State:\n{json.dumps(state_summary, indent=2)}\nSelect next agent in JSON."

        for model in ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash"]:
            try:
                res = self.client.models.generate_content(
                    model=model,
                    contents=user_msg
                )
                text = res.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                data = json.loads(text.strip())
                next_agent = data.get("next_agent", "FINISH")
                reasoning = data.get("reasoning", f"Gemini ({model}) selected {next_agent}.")
                full_reasoning = f"[Gemini {model}] {reasoning}"
                return next_agent, full_reasoning, data
            except Exception as e:
                last_err = e

        raise Exception(f"Gemini API call failed: {last_err}")


class ProceduralFallbackProvider(LLMProvider):
    """Deterministic fallback provider when LLMs are unavailable or rate-limited."""
    name = "Procedural Fallback Engine"

    def plan_next_agent(self, state: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        completed = state.get("completed_agents", [])
        is_video = state.get("is_video", False)

        ordered = [
            "EvidenceIntakeAgent",
            "PrivacyShieldAgent",
            "ENFPhysicsAgent" if is_video else "CornealTopologyAgent",
            "VisionIntelligenceAgent",
            "KnowledgeGraphAgent",
            "RiskAssessmentAgent",
            "IntelligenceFusionAgent",
            "LegalReasoningAgent"
        ]

        for agent in ordered:
            if agent not in completed:
                reason = f"Procedural Rule: Next required pipeline stage for {'video' if is_video else 'image'} evidence."
                eval_dict = {
                    "what_i_know": ["Media registered", f"Type is {'video' if is_video else 'image'}"],
                    "what_i_dont_know": ["Remaining vector findings"],
                    "strongest_hypothesis": "Authentic Media Record",
                    "next_agent": agent,
                    "reasoning": reason,
                    "expected_outcome": "Generate forensic vector data."
                }
                return agent, f"[Procedural Engine] {reason}", eval_dict

        eval_dict = {
            "what_i_know": ["All stages complete"],
            "what_i_dont_know": [],
            "strongest_hypothesis": "Investigation Finalized",
            "next_agent": "FINISH",
            "reasoning": "All forensic pipeline stages completed. Finalizing legal docket.",
            "expected_outcome": "Court-ready certificate ready."
        }
        return "FINISH", "[Procedural Engine] All forensic pipeline stages completed. Finalizing legal docket.", eval_dict


class ProviderFactory:
    """Factory that resolves provider priority (Groq -> Gemini -> Fallback) with automatic runtime failover."""

    @staticmethod
    def get_provider() -> LLMProvider:
        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if groq_key:
            try:
                provider = GroqProvider(groq_key)
                return provider
            except Exception:
                pass

        if gemini_key:
            try:
                provider = GeminiProvider(gemini_key)
                return provider
            except Exception:
                pass

        return ProceduralFallbackProvider()
