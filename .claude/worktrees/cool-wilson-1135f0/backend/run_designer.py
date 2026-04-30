"""One-shot runner: invoke the ui_designer agent and print the result as JSON."""
import json, sys, os

sys.path.insert(0, os.path.dirname(__file__))
from agents.ui_designer import design

REQUEST = """
Refresh ALL frontend screens to match the updated design system tokens that are
now in tailwind.config.js and described in your system prompt. The codebase uses
three screens (ConsentScreen, CaptureScreen, ResultsScreen) plus App.jsx and
index.css. Here is exactly what must change:

1. FONTS — replace every occurrence of font-[Inter] or default sans with
   font-[Geologica]. Replace heading elements (h1, h2) with font-[Raleway].
   Remove any reference to JetBrains Mono; use font-mono for data values.

2. BACKGROUND / SURFACE COLORS
   - bg-brand-black stays but the token now maps to #171616 (already in tailwind)
   - Where elevated panels or cards appear, use bg-brand-warm-dark (#212020)
   - Replace any bg-zinc-900 surfaces with bg-brand-warm-dark

3. LETTER-SPACING — fix ALL label text:
   - tracking-[0.3em] → tracking-[0.02em]  (this was 10× too wide)
   - tracking-widest  → tracking-[0.02em]  (same fix)
   Keep heading elements at tracking-[-0.012em].

4. EASING — every transition-all, hover:bg-white, hover:brightness-105 should
   use duration-300 ease-[cubic-bezier(.645,.045,.355,1)] (the brand easing).

5. ANIMATIONS — CaptureScreen analysing overlay: replace the full spinner
   (border-t-transparent rounded-full animate-spin) with the brand scan-line
   pattern: a horizontal h-px line in bg-brand-offwhite/40 that animates from
   top to bottom using animate-scan-line (already defined in tailwind.config.js).
   Keep a tiny w-4 h-4 opacity pulse for the "Analysing" label using
   animate-pulse-muted.

6. ENTRANCE ANIMATIONS — add animate-fade-up (already in tailwind.config.js)
   to the primary content blocks on ConsentScreen and ResultsScreen. On
   ResultsScreen, stagger ConcernBadge items with animationDelay index * 70ms
   and RoutineStep items with index * 60ms.

7. APP.JSX — ensure the root wrapper has bg-brand-black text-brand-offwhite
   (no change needed to logic, just verify class names match new tokens).

8. INDEX.CSS — update the html/body/#root block:
   - background-color: #171616  (brand-black)
   - color: #f3f2f0             (brand-offwhite)
   - font-family: 'Geologica', system-ui, sans-serif
   Add a @import or <link> note comment for the Google Fonts URL needed:
   https://fonts.googleapis.com/css2?family=Geologica:wght@300;400;500&family=Raleway:wght@300;400;500;700&display=swap

9. INDEX.HTML (frontend/index.html) — add the Google Fonts <link> preconnect
   and stylesheet tags in the <head> so Geologica and Raleway actually load.

Return changes for: frontend/index.html, frontend/src/index.css,
frontend/src/App.jsx, frontend/src/screens/ConsentScreen.jsx,
frontend/src/screens/CaptureScreen.jsx, frontend/src/screens/ResultsScreen.jsx.
"""

result = design(REQUEST)
print(json.dumps(result, indent=2))
