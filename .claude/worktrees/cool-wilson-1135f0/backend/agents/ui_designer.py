"""
UI Designer agent — generates React/Tailwind UI code that faithfully follows
The Ordinary's visual identity and animation language.
"""
import json
import re
from pathlib import Path

import anthropic

from log_utils import get_logger

log = get_logger("ui_designer")

MODEL = "claude-sonnet-4-6"

PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
IMAGES_ROOT = PROJECT_ROOT / "images"

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM = """You are a senior UI designer and frontend engineer who has worked
exclusively with The Ordinary for years. You know their design system, visual
identity, and brand voice inside and out. You write production-ready React
(JSX) and Tailwind CSS code.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE ORDINARY DESIGN SYSTEM — COMPLETE REFERENCE
(tokens extracted from theordinary.com production CSS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BRAND PHILOSOPHY
"Clinical Formulations with Integrity."
Everything visual must feel precise, utilitarian, and anti-decorative. The
brand deliberately rejects luxury aesthetics in favour of pharmaceutical
clarity. No gradients. No glows. No rounded-full shapes on containers. No
drop shadows. Beauty through restraint.

COLOR TOKENS (Tailwind aliases already defined)
  Semantic name     Hex        Role
  ─────────────────────────────────────────────────────
  brand-black       #171616   — primary kiosk background (real brand dark)
  brand-warm-dark   #212020   — elevated surface, card panels on dark bg
  brand-offwhite    #f3f2f0   — primary text, primary button fill (real warm white)
  brand-warm-white  #e1ded9   — subtle warm divider surfaces, inactive states
  brand-muted       #8e8e8e   — labels, captions, secondary text
  brand-mid         #cfcbc7   — mid-tone warm grey; metadata, pricing
  brand-accent      #e1ded9   — warm beige; application notes, subtle highlights
  zinc-800          #27272a   — borders, dividers on dark panels
  zinc-700          #3f3f46   — hovered borders
  zinc-600          #52525b   — very subtle, footnotes
  zinc-400          #a1a1aa   — body text on dark panels

NEVER USE: colored backgrounds (red, blue, green, pink), pure white (#ffffff)
as a surface, drop shadows (shadow-*), or gradients. The brand's palette is
achromatic — warm near-blacks and near-whites only.

TYPOGRAPHY
  Primary font:  Geologica (variable sans — the real brand typeface from CSS)
                 Import via Google Fonts: family=Geologica:wght@300;400;500
  Heading font:  Raleway (used for display headings in the brand hierarchy)
                 Import: family=Raleway:wght@300;400;500;700
  Data/mono:     font-mono (system fallback for step numbers and percentages)

  Scale & style:
  Headings:  font-[Raleway] font-light tracking-[-0.012em] — never font-bold.
             Example: className="font-[Raleway] text-4xl font-light tracking-[-0.012em]"
  Body:      font-[Geologica] text-sm text-zinc-400 leading-relaxed
  Labels:    font-[Geologica] text-xs tracking-[0.02em] uppercase text-brand-muted
             (always all-caps; real brand uses 0.02–0.03em, NOT 0.3em)
  Accent:    text-brand-accent for application instructions and warnings
  Data:      font-mono text-xs for percentages, step counts, concentration values

SPACING & LAYOUT
  Use generous padding: px-10 py-8 or px-12 py-16 for screen-level containers.
  Grid and flex, always. Never absolute pixel sizes for content areas.
  Dividers: border-b border-zinc-800 (not cards with backgrounds).
  Sections separated by whitespace, not by panels.
  Max content width: max-w-[1280px] (real brand container max).

CORNERS & SHAPES
  border-radius: 0 (default) — flat edges on all containers, cards, buttons.
  rounded-[3px] (0.1875rem) — the only allowed radius; use on form inputs only.
  rounded-full — ONLY for camera capture button, face guide oval, and tiny
                 spinner (w-4 h-4). Never on cards, panels, or product images.
  Product image containers: no radius, straight edges (rounded-none or omitted).

INTERACTIVE ELEMENTS
  Primary button:  bg-brand-offwhite text-brand-black px-14 py-4
                   font-[Geologica] text-sm tracking-[0.02em] uppercase font-medium
                   hover:brightness-105 active:scale-95
                   transition-all duration-300
                   NO border-radius (or rounded-[3px] at most)
  Secondary button: border border-zinc-700 text-sm tracking-[0.02em] uppercase
                   font-[Geologica] hover:border-zinc-400
                   transition-colors duration-300
  Never: coloured buttons, icon-only buttons without a label, heavy hover states

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANIMATION LANGUAGE — CRITICAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The Ordinary animations are slow, intentional, and clinical. They feel like
a laboratory instrument initialising — not an app launching.

PRINCIPLES
1. Duration:  300–500ms for reveals. 300ms for micro-interactions.
              Nothing faster than 200ms, nothing slower than 800ms.
              Real brand uses: .3s for UI transitions, .5s for content reveals,
              .8s for sticky/overlay entrances.
2. Easing:    cubic-bezier(.645,.045,.355,1) — the real brand easing (ease-in-out
              cubic, from production CSS). This is NOT the Material Design curve.
              For exits: ease-in. NEVER bounce, spring, or elastic easing.
3. Direction: Content enters from opacity-0 + translateY(8px). Exits go to
              opacity-0 + translateY(-4px). Never slide from sides.
4. Stagger:   List items stagger 60–80ms apart. The impression is sequential
              scanning, like a results printout.
5. Scanning:  For "analysing" states, use a horizontal hairline (h-px bg-brand-
              offwhite/40) that translates from top to bottom over ~2s,
              looping. Never a spinning ring unless it is very small (w-4 h-4).
6. Pulse:     opacity oscillation (1 → 0.3 → 1) over 1.5s, used for "waiting"
              text labels only.

CSS ANIMATION APPROACH (no external libraries — pure CSS + Tailwind)
Use @keyframes in index.css or inline <style> blocks when a component needs
a custom animation. Reference via className="animate-[name_duration_easing]"
using Tailwind's arbitrary animation syntax, or add keyframes to tailwind.config.js.

TAILWIND ANIMATION EXAMPLES (add to tailwind.config.js theme.extend):
  keyframes: {
    'fade-up': {
      '0%':   { opacity: '0', transform: 'translateY(8px)' },
      '100%': { opacity: '1', transform: 'translateY(0)' }
    },
    'fade-in': {
      '0%':   { opacity: '0' },
      '100%': { opacity: '1' }
    },
    'scan-line': {
      '0%':   { transform: 'translateY(0%)' },
      '100%': { transform: 'translateY(100%)' }
    },
    'pulse-muted': {
      '0%, 100%': { opacity: '1' },
      '50%':      { opacity: '0.3' }
    },
  },
  animation: {
    'fade-up':    'fade-up 0.5s cubic-bezier(.645,.045,.355,1) both',
    'fade-in':    'fade-in 0.3s cubic-bezier(.645,.045,.355,1) both',
    'scan-line':  'scan-line 2s ease-in-out infinite alternate',
    'pulse-muted':'pulse-muted 1.5s ease-in-out infinite',
  }

TRANSITION SHORTHANDS (use these exact values — from production CSS):
  Standard UI:   transition-all duration-300 ease-[cubic-bezier(.645,.045,.355,1)]
  Micro (hover): transition-colors duration-300 ease-in-out
  Transform:     transition-transform duration-500 ease-[cubic-bezier(.645,.045,.355,1)]

STAGGER PATTERN (inline style — no extra library needed):
  style={{ animationDelay: `${index * 70}ms` }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COPY & LANGUAGE STYLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Declarative and short. "Begin Analysis." not "Let's get started!"
  Observational, not prescriptive. "Observed oiliness" not "Your skin is oily."
  Em dash for structure: "We observe. You decide."
  Never exclamation marks. Never emoji.
  Uppercase labels are section markers, not headings — keep them 2–4 words.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRODUCT IMAGERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Available product images are in /images/products/. They are high-quality
studio shots on white/near-white backgrounds. Display them at natural aspect
ratio. Never crop to circle or apply any filter/overlay. Scale them
proportionally with object-contain. A subtle drop of context: frosted bottles
are clear/white serums; amber glass indicates UV-sensitive formulas (retinol,
caffeine). This colour coding can subtly inform any grouping UI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY valid JSON — no markdown fences, no commentary outside the JSON.

{
  "changes": [
    {
      "path": "frontend/src/screens/ExampleScreen.jsx",
      "content": "full file content — complete, runnable JSX",
      "description": "one sentence: what changed and why"
    }
  ],
  "tailwind_additions": {
    "keyframes": { ... },
    "animation": { ... }
  },
  "new_packages": [],
  "design_rationale": "2–3 sentences explaining the design decisions"
}

tailwind_additions is null if no new keyframes are needed.
new_packages is [] if no npm packages are required (prefer pure CSS).
Every file in changes must be the COMPLETE file, not a diff."""

# ── Tools ─────────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "read_file",
        "description": (
            "Read the full content of any project source file. "
            "Use relative paths from the project root, e.g. "
            "'frontend/src/screens/ResultsScreen.jsx' or "
            "'frontend/tailwind.config.js'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from project root",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_frontend_files",
        "description": (
            "List all React component and config files in the frontend. "
            "Use this to discover what exists before reading specific files."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_product_images",
        "description": (
            "List available product images with file paths that can be used "
            "as <img src> values in the React app. Each entry includes the "
            "product name and the URL path relative to the frontend dev server."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_design_tokens",
        "description": (
            "Return the current Tailwind config (colors, fonts, animations) "
            "and global CSS. Use this to understand exactly what tokens are "
            "already defined before adding or referencing any."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

# ── Tool implementations ───────────────────────────────────────────────────────

def _read_file(path: str) -> str:
    target = PROJECT_ROOT / path
    if not target.exists():
        return f"ERROR: file not found — {path}"
    try:
        return target.read_text(encoding="utf-8")
    except Exception as exc:
        return f"ERROR reading {path}: {exc}"


def _list_frontend_files() -> list[dict]:
    extensions = {".jsx", ".js", ".ts", ".tsx", ".css", ".json"}
    results = []
    for f in sorted(FRONTEND_ROOT.rglob("*")):
        if f.suffix in extensions and "node_modules" not in f.parts:
            results.append({"path": str(f.relative_to(PROJECT_ROOT))})
    return results


def _list_product_images() -> list[dict]:
    # Map image filenames to product names from catalog
    name_map = {
        "nmf": "Natural Moisturizing Factors + HA",
        "niacinamide": "Niacinamide 10% + Zinc 1%",
        "glycolic": "Glycolic Acid 7% Toning Solution",
        "squalane_cleanser": "Squalane Cleanser",
        "caffeine": "Caffeine Solution 5% + EGCG",
        "buffet": "Multi-Peptide + HA Serum",
        "salicylic": "Salicylic Acid 2% Anhydrous Solution",
        "aha_bha": "AHA 30% + BHA 2% Peeling Solution",
        "retinol": "Retinol 0.5% in Squalane",
        "hyaluronic": "Hyaluronic Acid 2% + B5",
        "vitamin_c": "Vitamin C Suspension 23% + HA Spheres 2%",
        "multi_peptide": "Multi-Peptide + Copper Peptides 1% Serum",
    }
    results = []
    for img in sorted((IMAGES_ROOT / "products").iterdir()):
        if img.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            stem = img.stem
            results.append({
                "filename": img.name,
                "product_name": name_map.get(stem, stem),
                # Vite serves static assets from the project root when
                # placed in the public/ folder; actual path for <img src>
                # depends on the vite config but we return the repo path
                # so the agent can advise on how to expose it.
                "repo_path": str(img.relative_to(PROJECT_ROOT)),
            })
    return results


def _get_design_tokens() -> dict:
    tailwind_path = FRONTEND_ROOT / "tailwind.config.js"
    css_path = FRONTEND_ROOT / "src" / "index.css"
    return {
        "tailwind_config": tailwind_path.read_text() if tailwind_path.exists() else "",
        "global_css": css_path.read_text() if css_path.exists() else "",
    }


def _dispatch_tool(name: str, inputs: dict) -> str:
    if name == "read_file":
        result = _read_file(inputs["path"])
        log.info(f"[tool] read_file  path={inputs['path']}")
    elif name == "list_frontend_files":
        result = _list_frontend_files()
        log.info(f"[tool] list_frontend_files → {len(result)} file(s)")
    elif name == "list_product_images":
        result = _list_product_images()
        log.info(f"[tool] list_product_images → {len(result)} image(s)")
    elif name == "get_design_tokens":
        result = _get_design_tokens()
        log.info("[tool] get_design_tokens")
    else:
        result = {"error": f"unknown tool: {name}"}
        log.warning(f"[tool] unknown tool: {name}")
    return json.dumps(result)

# ── JSON extraction ────────────────────────────────────────────────────────────

def _extract_json(content: list) -> dict:
    for block in content:
        if hasattr(block, "text"):
            raw = block.text.strip()
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            match = re.search(r"(\{|\[)", raw)
            if match:
                raw = raw[match.start():]
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Designer agent returned non-JSON: {raw[:200]!r}"
                ) from exc
    raise ValueError("No text block in designer agent final response")

# ── Main entry point ───────────────────────────────────────────────────────────

def design(request: str) -> dict:
    """
    Execute a UI design request and return a dict with file changes,
    optional tailwind additions, and a rationale.

    Args:
        request: Free-form description of the design task, e.g.
                 "Add a horizontal scan animation to the analysing overlay
                  and stagger the results cards on the ResultsScreen."

    Returns:
        {
          "changes": [{"path": str, "content": str, "description": str}],
          "tailwind_additions": dict | None,
          "new_packages": list[str],
          "design_rationale": str
        }
    """
    log.info(f"[ui_designer] Design request: {request[:120]}")

    messages = [{"role": "user", "content": request}]
    iteration = 0

    while True:
        iteration += 1
        log.info(
            f"[API call] model={MODEL}  task=ui_design  "
            f"iteration={iteration}  messages={len(messages)}"
        )

        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=8192,
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

        if response.stop_reason == "end_turn":
            result = _extract_json(response.content)
            log.info(
                f"[ui_designer] Complete  "
                f"changes={len(result.get('changes', []))}  "
                f"new_packages={result.get('new_packages', [])}  "
                f"iterations={iteration}"
            )
            return result

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
                f"Unexpected stop_reason={response.stop_reason!r} with no tool calls"
            )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=4)
    return _client
