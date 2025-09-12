# CLI Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Interactive command-line interface for the ecosystem.

- **Usage**: `python services/cli/main.py [command]`
- **Tests**: [tests/unit/cli](../../tests/unit/cli)

## Overview and role in the ecosystem
- Human-friendly entry point to orchestrate workflows, manage prompts, and check service health.
- Wraps common flows behind typed commands and an interactive TUI.

## Commands
| Command | Description |
|---------|-------------|
| interactive | Start interactive TUI workflow |
| get-prompt <category> <name> [--content ...] | Retrieve and render a prompt |
| health | Check service health across the stack |
| list-prompts [--category ...] | List available prompts |
| test-integration | Run cross-service checks from CLI |

## Examples
```bash
python services/cli/main.py interactive
python services/cli/main.py get-prompt summarization default --content "hello"
python services/cli/main.py health
```

## Related
- Prompt Store: [../prompt-store/README.md](../prompt-store/README.md)
- Interpreter: [../interpreter/README.md](../interpreter/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## Testing
- Unit tests: [tests/unit/cli](../../tests/unit/cli)
- Strategies:
  - Async client mocks with `AsyncMock` for `get_json`/`post_json` and call counts
  - URL-based side-effects for multiple endpoints in workflows
  - Flexible assertions for graceful error paths (non-raising)
