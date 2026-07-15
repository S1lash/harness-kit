# Component Rules

*Single reusable UI pieces: semantic API, tokens over hardcoded values, seed-then-customize for design systems.*

## Architecture
- Prefer semantic props (`variant="destructive"`) over raw classNames.
- Components own their visual logic. No business logic inside UI components.
- Composable: compound components > monolithic props objects.
- Design tokens as CSS variables — components consume tokens, never hardcode values.

## When Building a Design System
- Seed with shadcn/ui or Radix, then customize.
- One markdown file listing all available components (for context efficiency).
- Constrain the API surface — LLMs use whatever props are available.
