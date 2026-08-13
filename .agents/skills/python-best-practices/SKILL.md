---
name: python-best-practices
description: >
  Use when the user explicitly asks for Python best practices, style guidance,
  typing, docstrings, imports, or error-handling review in this repository.
  This is fallback guidance only. Do NOT use instead of ML task skills,
  python-performance-optimization, or python-simplifier.
compatibility: opencode
---

# Python Best Practices

## Precedence

Follow, in order:

1. Explicit user requirements
2. `AGENTS.md` and repository tool configuration
3. The relevant specialized skill
4. This fallback guidance

## Project Baseline

- Use built-in generics and modern unions: `list[str]`, `dict[str, int]`, `X | None`.
- Use Google-style docstrings for public APIs; document behavior, not syntax.
- Follow existing package import style and never use wildcard imports.
- Use `snake_case` for functions and variables, `PascalCase` for classes, and
  `UPPER_SNAKE_CASE` for constants.

## Error Handling

- Catch specific exceptions; never use bare `except`.
- Do not silently discard failures.
- Add custom exceptions only when callers need meaningful domain-level handling.
- Preserve causes with `raise ... from exc` when translating exceptions.
- Use context managers for resources.

## Scope

- Prefer the standard library and existing project helpers.
- Preserve existing behavior unless the task explicitly changes it.
- Avoid speculative abstractions and unrelated cleanup.
- Follow `AGENTS.md` for project testing and verification.
