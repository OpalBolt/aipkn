# Overview

> Related specs: [data-model](data-model.md) · [architecture](architecture.md) · [workflows](workflows.md)

## Problem & Goals

Build a personal knowledge base on top of an existing Obsidian vault, where an AI agent (Claude) handles the cognitive overhead of organizing, linking, and surfacing knowledge. The goal is a system where:

- Capturing new knowledge requires minimal friction (drop a file, paste text, clip a page)
- The vault stays clean and connected without manual tagging or linking
- You can ask natural-language questions and get answers with direct references to source notes
- Everything operates from the terminal or Claude Code — no GUI required for the agent workflows

This repo (`AI-knowledge`) is **tooling only** — scripts, prompts, and Claude config. The Obsidian vault lives in a separate directory (path TBD, must be configured).

---

## Non-Goals

- Building a custom Obsidian plugin
- Replacing Obsidian as the reading/editing UI
- Real-time sync or background daemon (all workflows are manually triggered)
- Handling binary attachments (images, PDFs) in the first version
