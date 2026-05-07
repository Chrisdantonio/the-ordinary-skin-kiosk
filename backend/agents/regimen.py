import json
import re
import sys
from pathlib import Path

import anthropic

from log_utils import get_logger
from catalog_sync import fetch_popup_products

log = get_logger("regimen")

MODEL = "claude-sonnet-4-6"

# In a PyInstaller onedir binary sys.frozen is True and __file__ no longer
# points into the source tree — data files live next to sys.executable instead.
if getattr(sys, 'frozen', False):
    # PyInstaller 6.x: data files live in _internal/, which sys._MEIPASS points to.
    CATALOG_PATH = Path(sys._MEIPASS) / 'products' / 'catalog.json'
else:
    CATALOG_PATH = Path(__file__).parent.parent.parent / 'products' / 'catalog.json'

SYSTEM = """You are a skincare routine builder for The Ordinary brand kiosk. You create safe,
effective AM/PM routines using The Ordinary product catalog based on visual skin observations.

HARD RULES — never violate these:
1. Never combine retinol with AHA or BHA exfoliants on the same night.
2. Never layer L-ascorbic acid Vitamin C and niacinamide in the same routine step.
3. Apply pH-sensitive actives (AHA, BHA, Vitamin C) before other serums.
4. No more than one exfoliant per routine — no AHA+BHA stacking.
5. Keep language observational in rationale. Never say "treats", "cures", or name medical conditions.
   Say "addresses visible oiliness", not "treats acne".
6. Keep routines focused: 3–4 steps AM, 3–5 steps PM. Don't overwhelm the user.

PROCESS:
1. Call fetch_popup_products to retrieve the current products featured on The Ordinary's
   immersive pop-up page. Prefer these products when they match the user's concerns.
2. Call get_products_by_concern with the top concern types to retrieve relevant products
   from the local catalog.
3. Select products that form a safe, non-conflicting routine. Prioritise pop-up products
   when available and relevant; supplement with catalog products as needed.
4. Flag any same-night conflicts in layering_notes.
5. Return ONLY valid JSON — no markdown, no commentary.

REQUIRED OUTPUT SHAPE:
{
  "am_routine": [
    { "step": 1, "product_id": "...", "name": "...", "rationale": "...", "application": "..." }
  ],
  "pm_routine": [...],
  "layering_notes": ["..."],
  "disclaimer": "This is a product recommendation, not a medical treatment plan."
}"""

_client: anthropic.Anthropic | None = None
_catalog: list[dict] | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=6)
    return _client


def _load_catalog() -> list[dict]:
    global _catalog
    if _catalog is None:
        _catalog = json.loads(CATALOG_PATH.read_text())
    return _catalog


TOOLS = [
    {
        "name": "fetch_popup_products",
        "description": (
            "Fetch the current products featured on The Ordinary's immersive pop-up page "
            "(theordinary.com/en-us/the-ordinary-immersive-pop-up.html). "
            "Call this first to surface products highlighted by the brand before falling back "
            "to the local catalog."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_products_by_concern",
        "description": (
            "Return products from The Ordinary catalog that target one or more skin concerns. "
            "Use this to discover which products are relevant before building the routine."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concerns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Concern types from the closed vocabulary, e.g. ['oiliness', 'dehydration']",
                },
                "time_of_day": {
                    "type": "string",
                    "enum": ["AM", "PM", "any"],
                    "description": "Filter by routine slot. Defaults to 'any'.",
                },
            },
            "required": ["concerns"],
        },
    },
    {
        "name": "get_product_details",
        "description": "Return full details for a single product by its catalog ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
            },
            "required": ["product_id"],
        },
    },
]


def _get_products_by_concern(concerns: list[str], time_of_day: str = "any") -> list[dict]:
    catalog = _load_catalog()
    results = []
    for product in catalog:
        if any(c in product.get("targets", []) for c in concerns):
            if time_of_day == "any" or time_of_day in product.get("time_of_day", []):
                results.append(product)
    return results


def _get_product_details(product_id: str) -> dict | None:
    catalog = _load_catalog()
    return next((p for p in catalog if p["id"] == product_id), None)


def _dispatch_tool(name: str, inputs: dict) -> str:
    if name == "fetch_popup_products":
        result = fetch_popup_products()
        log.info(
            f"[tool] fetch_popup_products → {len(result)} product(s) from site"
        )
        if result:
            log.debug(
                "[tool] popup products: "
                + ", ".join(p.get("name", "?") for p in result[:5])
                + ("…" if len(result) > 5 else "")
            )
    elif name == "get_products_by_concern":
        result = _get_products_by_concern(
            inputs["concerns"], inputs.get("time_of_day", "any")
        )
        log.info(
            f"[tool] get_products_by_concern  concerns={inputs['concerns']}  "
            f"time_of_day={inputs.get('time_of_day', 'any')}  "
            f"→ {len(result)} match(es)"
        )
    elif name == "get_product_details":
        result = _get_product_details(inputs["product_id"])
        log.info(
            f"[tool] get_product_details  product_id={inputs['product_id']}  "
            f"→ {'found' if result else 'not found'}"
        )
    else:
        result = {"error": f"unknown tool: {name}"}
        log.warning(f"[tool] unknown tool called: {name}")
    return json.dumps(result)


def _extract_json(content: list) -> dict:
    for block in content:
        if hasattr(block, "text"):
            raw = block.text.strip()
            # Strip markdown code fences
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            # If the model added prose before the JSON, find the first { or [
            match = re.search(r"(\{|\[)", raw)
            if match:
                raw = raw[match.start():]
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Model returned non-JSON text: {raw[:200]!r}") from exc
    raise ValueError("No text block found in final response")


def build_regimen(skin_vision: dict) -> dict:
    top_concerns = [c["type"] for c in skin_vision.get("top_concerns", [])]

    log.info(
        f"[regimen] Starting regimen build  "
        f"top_concerns={top_concerns}"
    )

    user_message = (
        f"Build an AM/PM routine for these observed skin characteristics:\n"
        f"{json.dumps(skin_vision.get('top_concerns', []), indent=2)}\n\n"
        f"Top concern types: {top_concerns}\n\n"
        "Start by calling fetch_popup_products to check what The Ordinary is currently "
        "featuring, then use get_products_by_concern for the local catalog. "
        "Return the routine JSON."
    )

    messages = [{"role": "user", "content": user_message}]
    iteration = 0

    while True:
        iteration += 1
        log.info(
            f"[API call] model={MODEL}  task=regimen_build  "
            f"iteration={iteration}  messages_in_context={len(messages)}"
        )

        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        log.info(
            f"[API response] stop_reason={response.stop_reason}  "
            f"input_tokens={response.usage.input_tokens}  "
            f"output_tokens={response.usage.output_tokens}  "
            f"tool_calls={len(tool_calls)}"
        )
        for tc in tool_calls:
            log.debug(f"[API response] tool_use  name={tc.name}  input={tc.input}")

        if response.stop_reason == "end_turn":
            regimen = _extract_json(response.content)
            log.info(
                f"[regimen] Build complete  "
                f"am_steps={len(regimen.get('am_routine', []))}  "
                f"pm_steps={len(regimen.get('pm_routine', []))}  "
                f"layering_notes={len(regimen.get('layering_notes', []))}  "
                f"total_iterations={iteration}"
            )
            return regimen

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result_str = _dispatch_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

        if not tool_results:
            raise ValueError(
                f"Unexpected stop_reason={response.stop_reason!r} with no tool calls — "
                "model did not return a routine or call any tools"
            )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
