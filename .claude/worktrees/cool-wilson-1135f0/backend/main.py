import logging
import os

import anthropic
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

log = logging.getLogger("main")

app = FastAPI(title="The Ordinary Skin Kiosk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from agents.skin_vision import UnusableImageError, analyze as _analyze_image
from agents.regimen import build_regimen as _build_regimen
from agents.ui_designer import design as _design

_USE_MOCKS = not os.environ.get("ANTHROPIC_API_KEY")

# ── Mock data (used when ANTHROPIC_API_KEY is not set) ────────────────────────

MOCK_SKIN_VISION = {
    "image_quality": {"usable": True, "issues": [], "confidence": 0.95},
    "zones": {
        "forehead": {
            "concerns": [
                {"type": "oiliness", "severity": "moderate", "confidence": 0.82},
                {"type": "enlarged_pores", "severity": "mild", "confidence": 0.75},
            ]
        },
        "nose": {
            "concerns": [
                {"type": "oiliness", "severity": "pronounced", "confidence": 0.91},
                {"type": "congestion", "severity": "mild", "confidence": 0.68},
            ]
        },
        "cheeks": {
            "concerns": [
                {"type": "dehydration", "severity": "mild", "confidence": 0.77},
                {"type": "redness", "severity": "mild", "confidence": 0.65},
            ]
        },
        "under_eye": {
            "concerns": [
                {"type": "dark_circles", "severity": "moderate", "confidence": 0.85},
            ]
        },
        "chin": {
            "concerns": [
                {"type": "occasional_breakout", "severity": "mild", "confidence": 0.72},
            ]
        },
        "jawline": {
            "concerns": [
                {"type": "congestion", "severity": "mild", "confidence": 0.69},
            ]
        },
    },
    "top_concerns": [
        {"type": "oiliness", "severity": "moderate", "confidence": 0.88},
        {"type": "dark_circles", "severity": "moderate", "confidence": 0.85},
        {"type": "dehydration", "severity": "mild", "confidence": 0.77},
    ],
    "disclaimer": "This is a visual observation, not a medical diagnosis.",
}

MOCK_REGIMEN = {
    "am_routine": [
        {
            "step": 1,
            "product_id": "hyaluronic-acid-2-b5",
            "name": "Hyaluronic Acid 2% + B5",
            "rationale": "Addresses dehydration observed across cheeks and forehead.",
            "application": "Apply to damp skin before moisturiser.",
        },
        {
            "step": 2,
            "product_id": "niacinamide-10-zinc-1",
            "name": "Niacinamide 10% + Zinc 1%",
            "rationale": "Targets oiliness and enlarged pores visible on T-zone.",
            "application": "Apply after water-based hydrators.",
        },
        {
            "step": 3,
            "product_id": "natural-moisturizing-factors-ha",
            "name": "Natural Moisturizing Factors + HA",
            "rationale": "Seals in hydration and supports barrier function.",
            "application": "Apply as final step. Follow with SPF.",
        },
    ],
    "pm_routine": [
        {
            "step": 1,
            "product_id": "lactic-acid-10-ha",
            "name": "Lactic Acid 10% + HA",
            "rationale": "Gently exfoliates rough texture and dullness. Use 2–3x per week.",
            "application": "Apply to clean, dry skin. Do not combine with retinol on same night.",
        },
        {
            "step": 2,
            "product_id": "caffeine-solution-5-egcg",
            "name": "Caffeine Solution 5% + EGCG",
            "rationale": "Targets dark circles noted in under-eye zone.",
            "application": "Apply to under-eye area before moisturiser.",
        },
        {
            "step": 3,
            "product_id": "retinol-0-5-squalane",
            "name": "Retinol 0.5% in Squalane",
            "rationale": "Supports skin renewal. Use on alternate nights to Lactic Acid.",
            "application": "Apply on nights without acid exfoliant. Start 1x per week.",
        },
        {
            "step": 4,
            "product_id": "natural-moisturizing-factors-ha",
            "name": "Natural Moisturizing Factors + HA",
            "rationale": "Locks in moisture overnight.",
            "application": "Apply as final step.",
        },
    ],
    "layering_notes": [
        "Do not use Lactic Acid and Retinol on the same night.",
        "Always apply SPF in the morning as the final step.",
    ],
    "disclaimer": "This is a product recommendation, not a medical treatment plan.",
}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "mock" if _USE_MOCKS else "live"}


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    if _USE_MOCKS:
        await image.read()
        return MOCK_SKIN_VISION

    image_bytes = await image.read()
    media_type = image.content_type or "image/jpeg"
    try:
        return _analyze_image(image_bytes, media_type)
    except UnusableImageError as e:
        raise HTTPException(status_code=422, detail={"unusable": True, "issues": e.issues})
    except anthropic.APIStatusError as e:
        raise HTTPException(
            status_code=503,
            detail={"upstream": "anthropic", "status": e.status_code, "message": "Service temporarily unavailable. Please try again."},
        )


@app.post("/recommend")
async def recommend(skin_vision: dict):
    if _USE_MOCKS:
        return MOCK_REGIMEN

    try:
        return _build_regimen(skin_vision)
    except anthropic.APIStatusError as e:
        raise HTTPException(
            status_code=503,
            detail={"upstream": "anthropic", "status": e.status_code, "message": "Service temporarily unavailable. Please try again."},
        )
    except Exception as e:
        log.exception("Unhandled error in /recommend")
        raise HTTPException(status_code=500, detail={"error": type(e).__name__, "message": str(e)})


class DesignRequest(dict):
    pass


@app.post("/design")
async def design(body: dict):
    """
    UI design agent endpoint. Accepts a free-form design request and returns
    file changes, optional Tailwind additions, and a design rationale.

    Body: { "request": "description of what to build or change" }

    The response can be applied directly to the frontend source tree.
    This endpoint is only available in live mode (requires ANTHROPIC_API_KEY).
    """
    if _USE_MOCKS:
        raise HTTPException(
            status_code=503,
            detail={"message": "Design agent requires a live ANTHROPIC_API_KEY — not available in mock mode."},
        )

    request_text = body.get("request", "").strip()
    if not request_text:
        raise HTTPException(status_code=422, detail={"message": "'request' field is required and must not be empty."})

    try:
        return _design(request_text)
    except anthropic.APIStatusError as e:
        raise HTTPException(
            status_code=503,
            detail={"upstream": "anthropic", "status": e.status_code, "message": "Service temporarily unavailable. Please try again."},
        )
    except Exception as e:
        log.exception("Unhandled error in /design")
        raise HTTPException(status_code=500, detail={"error": type(e).__name__, "message": str(e)})
