---
name: stage-per-session
description: Doc films must run one pipeline stage per session (script+voice / pictures / build / each EDL round) with a HANDOVER.md
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1d05ea34-c362-4d7c-b3aa-7f09501ae93b
  modified: 2026-11-17T00:53:56.357Z
---

Run each doc-pipeline stage in its own new session, handing over through `05_Renders/HANDOVER.md`; never carry a whole film through one session.

**Why:** film 13 (China, 17 Nov 2026) ran end to end in one session and used roughly 70–110% of a Pro 5-hour window (context grew to 373k tokens). The target is ≤25% per film. The user asked for the skill to enforce the split.

**How to apply:** at the end of a stage, write HANDOVER.md, stop, and offer a New-task card for the next stage. The stage table is in the doc-pipeline SKILL.md ("Một chặng = một session"). See [[doc-pipeline-engine]].

The skill is installed as a copy at `C:\Users\Admin\.claude\skills\doc-pipeline\SKILL.md` (17 Nov 2026). The source of truth is the engine copy in `claude/skills/doc-pipeline`; re-copy after editing it.
