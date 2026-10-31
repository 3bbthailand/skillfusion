# skillfusion

A Claude Code skill that turns an engineering drawing or picture (2D exercise, "3D DRAWING EXERCISE"
sheet, logo/outline) into an exact Autodesk Fusion model through the official Fusion MCP server.
It is written so that small models (e.g. Haiku) get the geometry exactly right.

## Contents

| File | What it is |
|---|---|
| `SKILL.md` | Rules and the 5-step workflow: READ (ledger) -> PLAN (expected volumes) -> BUILD -> CHECK -> FINISH |
| `fz.py` | Helper library over the Fusion API: mm, world coordinates, Z up; box/cyl/extrude/revolve/loft/pyramid/fillet/chamfer, 2D sketches with dimensions, `report`/`probe`/`view`/`color` checks |
| `drawtool.py` | Image helper (PIL): crop/zoom with a pixel grid, scan lines, pixel-to-mm scale, sample colours |
| `reference/drawings.md` | How to read third-angle views, symbols and dimensions |
| `reference/recipes.md` | Tested `fz` patterns for common features and expected-volume formulas |
| `examples/` | A worked 3D exercise and a dimensioned 2D sketch |

## Install

1. Enable Fusion's MCP server (Preferences > General > API > Fusion MCP Server) and register it:
   `claude mcp add --scope user --transport http fusion http://127.0.0.1:27182/mcp`
2. Clone this repo to `%USERPROFILE%\.claude\skills\skillfusion`.
3. The scripts use the absolute path `C:\Users\2263171\.claude\skills\skillfusion`. If your user
   folder is different, replace that path in `SKILL.md`, `fz.py` and `examples/`.
4. Requires Python with Pillow for `drawtool.py`.

Use it with `/skillfusion` or "skillfusion, make this drawing" plus the image.
