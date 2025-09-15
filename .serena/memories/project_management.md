# Project Management for LLM Documentation Ecosystem

## Linear Workspace Configuration
- **Workspace**: Casey Webb's Linear workspace
- **Team**: LiveLaughDocument
- **Team ID**: 33309c69-7acf-4f4b-94d0-defff29cdf33
- **Main Project**: LLM Documentation Ecosystem
- **Project ID**: 04a70907-738a-49e4-80d8-ede8ff993573

## Project Details
- **Project Name**: LLM Documentation Ecosystem
- **Status**: Active
- **Target Date**: 2025-09-19
- **Description**: A comprehensive platform for documentation analysis, prompt management, and developer tooling

## Ticket Management Process

### Creating Tickets
1. Use `mcp__linear__create_issue` with the LiveLaughDocument team
2. Always assign to the LLM Documentation Ecosystem project
3. Include comprehensive task breakdowns with checkboxes
4. Add clear acceptance criteria
5. Specify technical requirements
6. Use relevant labels (frontend, backend, docker, ci-cd, setup, etc.)

### Ticket Structure Template
```markdown
# [Feature/Task Name]

## Overview
[Brief description of what needs to be done]

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Technical Requirements
- Requirement 1
- Requirement 2
```

### Common Labels
- frontend
- backend
- elm
- docker
- ci-cd
- setup
- documentation
- testing
- api

### Git Branch Naming
Linear automatically generates branch names following the pattern:
`feature/lld-[ticket-number]-[kebab-case-title]`

Example: `feature/lld-85-scaffold-hello-world-elm-app-in-frontend-service-with-docker`

## Workflow
1. Create tickets in Linear with proper project assignment
2. Use generated git branch names for feature development
3. Link commits and PRs to ticket numbers
4. Update ticket status as work progresses
5. Close tickets when features are merged and deployed

## Integration Points
- Git branches automatically named by Linear
- Ticket URLs: https://linear.app/caseywebb/issue/[ticket-id]
- Project tracking through Linear's project views
- Team collaboration through LiveLaughDocument team space
