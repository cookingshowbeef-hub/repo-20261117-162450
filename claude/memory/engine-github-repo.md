---
name: engine-github-repo
description: The doc-pipeline engine is a public GitHub repo (made public by the user 2026-11-18); new machines set up from its link via README/SETUP_CLAUDE.md
metadata:
  node_type: memory
  type: reference
  originSessionId: e4b95b47-46ab-4b3e-a120-066e572cfda3
  modified: 2026-11-17T09:26:06.286Z
---

The engine folder (`06. Kịch bản & Công cụ Code - Scripts & Engine\03. Doc Pipeline - Quy trình Phim tài liệu`) is a git repo, branch `main`. It was pushed on 2026-11-17 to https://github.com/cookingshowbeef-hub/repo-20261117-162450. It started private; on 2026-11-18 the user had made it **public**, so anyone can read it, including `claude/memory/`. Never commit keys or personal details there.

On a new machine the user sends this link, and Claude clones it and follows SETUP_CLAUDE.md steps 1–9.

Keys and machine paths are not in the repo. They live in `~/.docpipe/keys.env` and `~/.docpipe/settings.env` (DOCPIPE_PROJECTS, DOCPIPE_BGM, DOCPIPE_LIBRARY, RESOLVE_MCP_DIR, REMOTION_NODE).

The repo carries a copy of these memories in `claude/memory/`, and the skill source in `claude/skills/doc-pipeline/`.

**How to apply:** after changing the engine, skill or memory, refresh `claude/memory/` from this memory folder, commit and push. Do this only when the user asks to push.

See [[doc-pipeline-engine]].
