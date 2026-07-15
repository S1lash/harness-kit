# Security Baseline

Minimal security hygiene for frontend code. Not a full security audit — just the rules that prevent the most common client-side vulnerabilities.

- **`textContent` over `innerHTML`** — always. When HTML rendering is needed, use `setHTML()` (Sanitizer API) if available, or a trusted sanitizer library. Never `innerHTML` with untrusted input.
- **`postMessage`**: always validate `event.origin` with strict equality. Always specify target origin in `postMessage()` calls — **never `"*"`**.
- **Cookie attributes**: `SameSite=Lax` for standard cookies. `__Host-` prefix when possible (requires `Secure`, `Path=/`, no `Domain`).
- **No inline event handlers** (`onclick="..."`) — use `addEventListener`. Inline handlers break CSP and are an XSS vector.
- **Never assign model/API output to `innerHTML`** — use `textContent`. This applies to any AI/LLM integration in the frontend.
