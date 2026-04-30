import base64
import json
import re

import anthropic

from log_utils import get_logger

log = get_logger("skin_vision")

MODEL = "claude-opus-4-7"

SYSTEM = """You are a cosmetic skin observation tool for a retail kiosk. You make descriptive visual
observations of facial skin from camera images. You are NOT a medical device and must never make
medical diagnoses.

RULES
1. DESCRIPTIVE ONLY. Never use clinical condition names. Banned: acne, rosacea, eczema, melasma,
   dermatitis, seborrhea, psoriasis, or any other clinical diagnosis term.
2. Use ONLY this closed concern vocabulary:
   dehydration, oiliness, redness, enlarged_pores, uneven_tone, hyperpigmentation, dark_circles,
   dullness, fine_lines, rough_texture, occasional_breakout, congestion, flaking, visible_sensitivity
3. Severity values: mild | moderate | pronounced
4. Confidence scores: 0.0–1.0. Lower scores when lighting, angle, or quality limits certainty.
5. Check image quality FIRST. If unusable, set image_quality.usable=false, populate issues, stop.
6. Analyse all six zones: forehead, nose, cheeks, under_eye, chin, jawline.
7. Be equally accurate across ALL skin tones. Skin tone must not influence concern scoring.
8. Return ONLY valid JSON — no markdown fences, no commentary.

REQUIRED OUTPUT SHAPE
{
  "image_quality": {
    "usable": true,
    "issues": [],
    "confidence": 0.95
  },
  "zones": {
    "forehead":  { "concerns": [{ "type": "...", "severity": "...", "confidence": 0.0 }] },
    "nose":      { "concerns": [...] },
    "cheeks":    { "concerns": [...] },
    "under_eye": { "concerns": [...] },
    "chin":      { "concerns": [...] },
    "jawline":   { "concerns": [...] }
  },
  "top_concerns": [...],
  "disclaimer": "This is a visual observation, not a medical diagnosis."
}

image_quality.issues values (use only): too_dark, too_bright, blurry, face_not_detected,
partial_face, obstructed
top_concerns: up to 5 entries, ordered by combined severity+confidence, drawn from all zones."""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # max_retries handles transient 429/500/502/503/504/529 with exponential backoff
        _client = anthropic.Anthropic(max_retries=6)
    return _client


class UnusableImageError(Exception):
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__(f"Image unusable: {issues}")


def analyze(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    log.info(
        f"[API call] model={MODEL}  task=skin_analysis  "
        f"image_size={len(image_bytes):,} bytes  media_type={media_type}"
    )

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {
                        "type": "text",
                        "text": "Observe this face image and return your structured JSON analysis.",
                    },
                ],
            }
        ],
    )

    log.info(
        f"[API response] stop_reason={response.stop_reason}  "
        f"input_tokens={response.usage.input_tokens}  "
        f"output_tokens={response.usage.output_tokens}"
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    result = json.loads(raw)

    iq = result.get("image_quality", {})
    log.info(
        f"[skin_vision] image_usable={iq.get('usable')}  "
        f"quality_confidence={iq.get('confidence')}  "
        f"issues={iq.get('issues', [])}"
    )

    if not iq.get("usable", False):
        log.warning(f"[skin_vision] Image rejected — issues: {iq.get('issues', [])}")
        raise UnusableImageError(iq.get("issues", []))

    top = result.get("top_concerns", [])
    log.info(
        f"[skin_vision] top_concerns({len(top)}): "
        + ", ".join(f"{c['type']}:{c['severity']}" for c in top)
    )

    zones = result.get("zones", {})
    for zone_name, zone_data in zones.items():
        concerns = zone_data.get("concerns", [])
        if concerns:
            log.debug(
                f"[skin_vision] zone={zone_name}  concerns="
                + ", ".join(f"{c['type']}({c['severity']},conf={c['confidence']:.2f})" for c in concerns)
            )

    return result
