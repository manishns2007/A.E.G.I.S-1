"""
Visuo-Acoustic Knowledge Graphing Extractor for Project A.E.G.I.S.

Parses redacted background environments into structured forensic entities using
the Google Gemini Vision API.

Design contract
---------------
- If Gemini (or a future VLM) is available and returns valid JSON: entities
  from the real response are forwarded directly to the knowledge graph.
- If the API key is missing, the API is unreachable, or the response cannot be
  parsed: the function returns the canonical OFFLINE response below.
  It NEVER fabricates entities, invents objects, or returns placeholder data.

Canonical offline response
--------------------------
{
    "status": "offline",
    "scene_type": null,
    "environmental_objects": [],
    "spatial_layout": null,
    "lighting_type": null,
    "forensic_signature_hash": null,
    "error": "<reason string>"
}

The dashboard must check for status == "offline" and display
"Semantic extraction unavailable." accordingly.
"""

import os
import json
import warnings
from PIL import Image
import cv2

warnings.filterwarnings("ignore", category=FutureWarning)


# ---------------------------------------------------------------------------
# Canonical offline/unavailable response
# ---------------------------------------------------------------------------

def _offline(reason: str) -> dict:
    """Returns the canonical offline sentinel. No entities are invented."""
    return {
        "status": "offline",
        "scene_type": None,
        "environmental_objects": [],
        "spatial_layout": None,
        "lighting_type": None,
        "forensic_signature_hash": None,
        "error": reason
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_background_environment(image_path_or_bgr, api_key: str = None) -> dict:
    """
    Attempt to extract forensic environmental entities from the supplied image
    using the Gemini Vision API.

    Parameters
    ----------
    image_path_or_bgr : str | numpy.ndarray | None
        Either an absolute file path (str) or a BGR numpy array produced by
        OpenCV, or None if no image is available.
    api_key : str | None
        Optional Gemini API key. If None the function also checks the
        GEMINI_API_KEY and GOOGLE_API_KEY environment variables.

    Returns
    -------
    dict
        On success: the parsed JSON dict returned by Gemini containing at
        minimum the keys scene_type, environmental_objects, spatial_layout,
        lighting_type, forensic_signature_hash.
        On failure: the canonical offline dict (see module docstring).
    """
    # ── 1. Validate / load input image ───────────────────────────────────
    if image_path_or_bgr is None:
        return _offline("No image supplied to VLM extractor.")

    if isinstance(image_path_or_bgr, str):
        if not os.path.exists(image_path_or_bgr):
            return _offline(f"Image path does not exist: {image_path_or_bgr}")
        img_bgr = cv2.imread(image_path_or_bgr)
        if img_bgr is None:
            return _offline(f"cv2.imread failed for: {image_path_or_bgr}")
    else:
        img_bgr = image_path_or_bgr

    if img_bgr is None or img_bgr.size == 0:
        return _offline("Image array is empty or unreadable.")

    # ── 2. Convert to PIL for the Gemini SDK ─────────────────────────────
    try:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
    except Exception as e:
        return _offline(f"Image colour conversion failed: {e}")

    # ── 3. Resolve API key ────────────────────────────────────────────────
    api_key_to_use = (
        api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    if not api_key_to_use:
        return _offline(
            "No Gemini API key provided. Set GEMINI_API_KEY or supply the key "
            "in the sidebar to enable semantic entity extraction."
        )

    # ── 4. Gemini Vision call ─────────────────────────────────────────────
    prompt = (
        "You are a forensic environment analyst. Examine the background of this "
        "image (ignore any persons). Extract every identifiable object, surface, "
        "fixture, or texture visible in the scene background. "
        "Return ONLY valid JSON with this exact schema:\n"
        "{\n"
        "  \"scene_type\": \"<string>\",\n"
        "  \"environmental_objects\": [\n"
        "    {\"entity\": \"<name>\", \"attributes\": [\"<attr1>\", \"<attr2>\"]}\n"
        "  ],\n"
        "  \"spatial_layout\": \"<string>\",\n"
        "  \"lighting_type\": \"<string>\",\n"
        "  \"forensic_signature_hash\": \"<string>\"\n"
        "}\n"
        "Do not include any commentary, markdown, or code fences outside the JSON."
    )

    raw_text = None
    last_error = "Unknown Gemini error."

    # Use modern google-genai SDK directly
    try:
        from google import genai
        client = genai.Client(api_key=api_key_to_use)
        
        sdk_success = False
        quota_error = None
        
        for model_name in ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, pil_img]
                )
                if response and response.text:
                    raw_text = response.text.strip()
                    sdk_success = True
                    break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    quota_error = f"Gemini API Free Tier Quota Exceeded (429 RESOURCE_EXHAUSTED) for model {model_name}. Please upgrade your Gemini API key or wait for rate-limit reset."
                last_error = f"Gemini API error ({model_name}): {e}"
        
        if not sdk_success:
            raise Exception(quota_error or last_error)

    except Exception as e_sdk:
        last_error = f"{e_sdk}"

    if raw_text is None:
        print(f"[A.E.G.I.S. VLM ERROR] {last_error}")
        return _offline(f"Gemini API call failed: {last_error}")

    # ── 5. Strip optional markdown fences ────────────────────────────────
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    # ── 6. Parse JSON ─────────────────────────────────────────────────────
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        return _offline(
            f"Gemini returned non-JSON response (parse error: {e}). "
            f"Raw prefix: {raw_text[:120]!r}"
        )

    # ── 7. Sanity-check required keys ─────────────────────────────────────
    if not isinstance(result, dict):
        return _offline("Gemini JSON root is not an object.")

    # Guarantee environmental_objects is always a list
    if "environmental_objects" not in result or not isinstance(
        result["environmental_objects"], list
    ):
        result["environmental_objects"] = []

    # Propagate online status so the dashboard can distinguish
    result.setdefault("status", "online")
    result.setdefault("scene_type", None)
    result.setdefault("spatial_layout", None)
    result.setdefault("lighting_type", None)
    result.setdefault("forensic_signature_hash", None)

    return result
