# Project: Attribute Lineage Agent

Portfolio project #1 of 2 planned. Project #2 (NL-to-schema-change agent) is tracked
but not started yet — see the Notion "Project Management" database, Project =
Portfolio Creation, for current task status on the broader portfolio effort.

## What this is

A public, from-scratch rebuild of the attribute-lineage-tracing pattern built at
Morgan Stanley, using public HMDA mortgage data instead of proprietary data/schemas.
DuckDB pipeline (Snowflake-swappable via one env var), sqlglot + networkx lineage
graph, optional Claude-narrated trace on top of a deterministic graph walk.

## Status

Built, tested (15/15 passing), pushed to GitHub, slide deck included.

- Repo: https://github.com/HimaniMehta425/attribute-lineage-agent
- README.md has full architecture/quickstart details — read that first for technical
  context before making changes.
- Linked live from the Projects section of the portfolio site (see `~/Projects/Portfolio`).

## Session handoff

Nothing in progress here right now. If resuming, check README.md and `git log` for
latest state. No open threads.
