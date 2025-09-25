# Contributing

## Workflow
- Create feature branches from main
- Write tests and update docs for any behavioral change
- Ensure `pytest -q` passes locally

## Commit style
- Conventional-ish: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## PR checklist
- [ ] Tests added/updated
- [ ] Service README updated if API/behavior changes
- [ ] Docs site builds locally (mkdocs)

## Local tasks
```bash
make test   # run tests
make docs   # build docs site locally
```
