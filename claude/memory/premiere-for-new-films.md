---
name: premiere-for-new-films
description: From 2026-11-20 the user wants new films delivered to Adobe Premiere Pro (paid) instead of DaVinci Resolve; old films are not re-exported
metadata:
  node_type: memory
  type: project
  originSessionId: a8358dd7-33c5-44d8-8f07-2e1635df3bd5
  modified: 2026-11-20T01:26:10.698Z
---

On 2026-11-20 the user (who pays for Premiere Pro) asked for new films to go to Premiere instead of DaVinci Resolve. Films already delivered in Resolve stay as they are and are not re-exported.

**Why:** the user prefers editing in Premiere. The engine's `review` writes FCPXML (Final Cut X), which Premiere cannot import. Premiere needs FCP7 XML (xmeml).

**How to apply:** build a `premiere.py` xmeml writer next to `docpipe/resolve.py` that shares its timing, keyframe and audio logic. Keep the Resolve code for old films. The grade goes on one adjustment layer with Lumetri Input LUT. Feedback comes from a Premiere marker CSV, not an EDL. User suggested github.com/hetpatel-11/adobe_premiere_pro_mcp (CEP bridge) for automation. It is macOS-validated only and has telemetry on by default, so set PREMIERE_MCP_TELEMETRY=0. Related: [[doc-pipeline-engine]].
