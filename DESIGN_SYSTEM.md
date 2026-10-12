# DESIGN_SYSTEM.md — jade on cream

Goal: look like a calm, premium editorial tool — not a default Gradio template. Applies to the Gradio app and every chart.

## Palette

### Base
| token | hex | use |
|---|---|---|
| `cream-100` | `#FFF2D7` | page background |
| `cream-50` | `#FFF8EA` | cards, input fields |
| `cream-200` | `#F3E3C0` | borders, dividers |

### Jade scale (text + accents)
| token | hex | use |
|---|---|---|
| `jade-900` | `#0B3D2E` | headings, primary text |
| `jade-700` | `#146B4F` | body text, primary button |
| `jade-500` | `#2E9E77` | links, focus ring, active states |
| `jade-300` | `#8FD3B6` | subtle highlights, chart secondary |
| `jade-100` | `#DDF3E9` | highlighted evidence background |

### Verdict colors (only for verdicts)
| verdict | text | background |
|---|---|---|
| SUPPORTS | `#146B4F` (jade-700) | `#DDF3E9` |
| REFUTES | `#9E3B22` (terracotta) | `#F8E1D8` |
| NOT ENOUGH INFO | `#8A6414` (ochre) | `#F6EACB` |

Never rely on color alone: every verdict also shows its label in text and an icon (✓ / ✕ / ?).

Contrast: jade-900 and jade-700 on cream-100 both pass WCAG AA for body text. jade-300 is decoration only — never for text.

## Typography

| role | font | size / weight |
|---|---|---|
| Headings | **Fraunces** (serif, Google Fonts) | H1 36/600, H2 24/600, H3 18/600 |
| UI + body | **Inter** | 16/400 body, 14/500 labels |
| Logs, ids, timings | **JetBrains Mono** | 13/400 |

Line height 1.5 body, 1.2 headings. Max text width 720 px.

## Spacing + shape

- Spacing scale: 4, 8, 12, 16, 24, 32, 48 px. Nothing else.
- Radius: 12 px cards, 8 px inputs/buttons, 999 px pills.
- Borders: 1 px `cream-200`. No drop shadows except a single soft one on the verdict card: `0 2px 12px rgba(11,61,46,0.08)`.

## Components

**Claim input** — large textarea, `cream-50` fill, placeholder in jade-700 at 60% opacity, char counter (mono) bottom-right, max 300.

**Verify button** — `jade-700` fill, cream-50 text, hover `jade-900`. One primary button on the page, ever.

**Example chips** — 4 pill buttons under the input (one Supported, one Refuted, one NEI, one tricky). Outline jade-500.

**Verdict card** — verdict pill (verdict colors) + icon, explanation in Inter 16, then "Evidence" list.

**Evidence item** — page title (Fraunces 16, linked to Wikipedia), sentence text, `[n]` marker in mono. Cited sentences get `jade-100` background + 3 px `jade-500` left border. Uncited ones shown muted.

**Status line** — mono 13, jade-700: `retrieving… 0.8s · reasoning… 2.1s · done`.

**Footer** — one line: dataset, model name, "Wikipedia snapshot 2017 — claims about later events will be NEI." Plus GitHub link.

## Charts (matplotlib)

- Background `#FFF2D7`, axes/text `#0B3D2E`, grid `#F3E3C0`.
- Method colors: dense `#146B4F`, BM25 `#8A6414`, hybrid `#2E9E77`.
- Condition colors: with evidence `#146B4F`, no evidence `#9E3B22`.
- No top/right spines. Direct labels on bars instead of legends where possible. Title in serif.

## Gradio implementation

Use `gr.themes.Base()` with these overrides plus a small CSS block loading the three Google Fonts. Hide the default footer. Set `analytics_enabled=False`.

## Don'ts

No gradients, no emoji in UI text, no dark-mode-only colors, no more than one accent per screen region, no default orange Gradio buttons.
