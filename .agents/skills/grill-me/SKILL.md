---
name: grill-me
description: >
  Use ONLY when the user explicitly says "grill me", invokes the grill-me skill,
  or asks for adversarial requirements interrogation of an existing plan. Ask one
  high-impact question at a time, challenge contradictions, and record decisions.
  Do NOT auto-trigger for ordinary planning, brainstorming, ML experiment design,
  or implementation.
compatibility: opencode
---

# Grill Me

Interrogate an existing proposal until its material decisions are clear.

## Process

1. Read the proposal and relevant project context.
2. Identify unresolved decisions that could change scope, correctness, cost, or risk.
3. Ask exactly one highest-impact question at a time.
4. Briefly record each answer before continuing.
5. Challenge contradictions and name dependencies between decisions.
6. Stop when no material ambiguity remains or the user asks to stop.

## Rules

- Do not ask questions already answered by the repository or conversation.
- Prefer concise multiple-choice questions when the options are known.
- If the user delegates a decision, make the smallest reasonable default and record it.
- Do not explore speculative branches that cannot affect the outcome.
- Do not implement or modify files.

## Final Summary

Return:

- Confirmed decisions
- Assumptions
- Remaining open questions
- Material risks
