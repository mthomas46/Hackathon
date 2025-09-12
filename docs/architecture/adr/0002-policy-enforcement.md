# ADR 0002: Policy Enforcement for Summarization

## Status
Accepted

## Context
We must restrict providers when content is sensitive; allow broader access when not.

## Decision
Secure Analyzer enforces provider selection based on detection. Override via `override_policy` when explicitly allowed.

## Consequences
- Safer defaults for regulated content
- Clear separation of detection vs policy enforcement
- Requires tests and docs to reflect policy
