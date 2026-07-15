# Forms Contract

This contract fires only when the surface has a `<form>`.

Forms are the highest-friction surface in any app. Browser integration makes or breaks the experience.

## Autocomplete (password managers and autofill)
- Sign-in: `autocomplete="username"` on email/login field + `autocomplete="current-password"` on password field — **mandatory** for password manager integration.
- Sign-up: `autocomplete="new-password"` (distinct from `current-password` — password managers generate suggestions).
- Address: `autocomplete="street-address"`, `"postal-code"`, `"country"`, etc. — enables one-click autofill.
- Payment: `autocomplete="cc-number"`, `"cc-exp"`, `"cc-csc"` on card fields.
- **Never** `autocomplete="off"` on credential, address, or payment fields — it fights the browser and frustrates users.
- `id` attributes must match autocomplete intent (`id="current-password"`, not `id="input-3"`).

## Structure
- Single `<form>` element wrapping all fields — not divs with JS handlers. Browser/password manager integration requires real `<form>`.
- `<button type="submit">` for form submission, `<button type="button">` for non-submit actions.
- `required` on mandatory fields — enables native validation and screen reader announcements.
- `enterkeyhint` attribute for mobile keyboard enter key label (`"send"`, `"search"`, `"next"`, `"done"`).

## Password UX
- **Never disable paste** on password fields — it breaks password managers and is a security anti-pattern.
- Show/hide password toggle is required UX — implement with `type` toggle between `"password"` and `"text"`.

## Validation
- Validate after interaction, not on page load — use `blur` or `submit` events, not `input` for error display.
- Field-level errors under the field, not in a banner at the top.
- Error messages: what went wrong + how to fix it. Never just "Invalid input".
