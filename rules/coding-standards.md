# Coding Standards

> Generic engineering standards for any code this harness produces. Stack-agnostic. Foundational
> principles (reuse-before-invent, minimal-intervention) live in rules/core-principles.md.

- **Readability.** Code self-explanatory, cognitive load low. Minimal comments — only where
  critically important. Never simplify / cut down just for readability; complete tasks fully,
  production-ready.
- **Naming.** Classes / methods / variables named by purpose, no abbreviations (except common ones:
  DTO, API, ID, URL, HTTP).
- **Structure.** Extract magic strings / parameters into constants or config. Imports explicit (no
  wildcards). Minimize duplication (shared checks, mappers, utilities). Type-safe: extract into
  types / classes / configs rather than passing untyped values.
- **Separation of responsibility (SRP in code).** Separate responsibility between classes /
  services / layers — even a service with one method. Each class / package owns its domain only. No
  cyclic dependencies.
- **Error handling.** Centralized, standardized error objects, unified codes. An error always
  carries **code, object, field, value**. Messages actionable: what went wrong AND how to fix it.
- **Logging.** Significant actions logged with context (who, operation id). Structured logging + a
  trace / correlation id.
- **Validation.** Validate all input before business logic. Validators contain no business logic,
  only checks. Validate at system boundaries (user input, external APIs); trust internal code.
- **Testability.** Design for testing: minimal dependencies, explicit interfaces, composition over
  inheritance. Critical logic covered by unit + integration tests, quick to run. Integration tests
  hit real dependencies, not mocks, unless the dependency is external and unstable.
- **No brittle tests.** A test that can't be verified, swallows a real failure mode, or depends on a
  fragile fixture you don't fully understand is **worse than no test**. Cover decisive logic with a
  reliable unit; trust integration to a real environment.
- **Entropy prevention.** Prefer shared utility packages over one-off helpers. Fixing a bug → check
  whether the same pattern exists elsewhere, fix all instances. Every workaround has a comment
  explaining WHY and WHEN it can be removed.
