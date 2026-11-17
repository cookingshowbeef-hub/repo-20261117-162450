---
name: no-openai-image-generation
description: Do not use the OpenAI API key (MCP - Key/.env) to generate images for videos
metadata:
  node_type: memory
  type: feedback
  originSessionId: 23ce7530-a04c-46c3-83c1-2d1fcfd971c6
  modified: 2026-11-06T07:46:06.390Z
---

Do not call the OpenAI image API (gpt-image-*) with the key in `D:\4. bot\MCP - Key\.env` to create illustrations.

**Why:** On 2026-11-06 the user explicitly stopped it mid-task ("không dùng key openai để tạo hình") while building the dino doodle prototype.

**How to apply:** For doodle illustrations ask the user which source to use (their own drawings, another tool they name) before generating anything; never fall back to OpenAI image generation on your own. Related: [[dino-doodle-channel]]
