---
applyTo: "**"
---

# Agent Rules

## Core Development Principles

- **DRY & KISS**: Apply DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid) principles judiciously to all generated code. Follow the "Rule of Three" - refactor only after the third repetition to avoid premature abstraction.
- **Minimal Changes**: Minimize the files modified to only those that are absolutely required for the task.
- **Single Responsibility**: Keep functions small and focused on a single, well-defined task.
- **Preserve Structure**: Keep the original logic and structure intact unless a bug is present or explicit refactoring is requested. However, favor modern language features and idioms when they improve clarity and maintainability.

## Code Quality Standards

- **Documentation**: Write clear and concise comments to explain complex code, business logic, and non-obvious decisions. Prefer self-documenting code over excessive comments.
- **Naming Conventions**: Use descriptive, self-documenting variable and function names that clearly indicate their purpose. Follow language-specific conventions (e.g., snake_case for Python).
- **Error Handling**: Always implement proper error handling and validation for user inputs and external dependencies. Use language-appropriate exception handling patterns.
- **Type Safety**: Use static type annotations and validation where supported by the language. For Python, leverage type hints and consider validation libraries for runtime checks at boundaries.

## Change Management

- **Conservative Approach**: Avoid renaming functions, variables, or components unless necessary for the requested feature.
- **Scope Control**: Do not restructure or refactor unrelated code unless explicitly requested.
- **Impact Minimization**: Prefer extending existing functionality over replacing it when possible.
- **Backwards Compatibility**: Maintain backwards compatibility unless breaking changes are explicitly required.
- **Modern Language Features**: When making changes, favor modern language idioms and features that improve readability and maintainability without breaking existing contracts.

## Testing & Validation

- **Test Coverage**: Ensure new code has appropriate test coverage and existing tests continue to pass.
- **Manual Testing**: Test critical paths manually after implementation to verify functionality.
- **Edge Cases**: Consider and handle edge cases and error scenarios proactively.

## Security & Performance

- **Security First**: Apply security best practices including input validation, sanitization, and proper authentication/authorization.
- **Performance Awareness**: Consider performance implications of changes, especially for database queries and API calls.
- **Resource Management**: Properly manage resources like database connections, file handles, and memory.

## Communication & Documentation

- **Clear Explanations**: Provide clear explanations of what changes were made and why.
- **Context Preservation**: Maintain context about business requirements and technical constraints.
- **Decision Rationale**: Document the reasoning behind technical decisions and trade-offs.

## Standards Compliance

- **Coding Standards**: Ensure all code adheres to the project's coding standards and style guidelines.
- **Best Practices**: Follow established patterns and conventions already present in the codebase.
- **Code Reviews**: Write code as if it will be reviewed by senior developers.
