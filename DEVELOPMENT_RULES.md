# Development Rules and Documentation Standard

These rules apply to all changes in this repository. They are intended to keep future developers informed and ensure continuous documentation.

- Bold titles are used in lists.

## Changelog Policy
- Always update `CHANGELOG.md` for every meaningful edit.
- Prefer the "Keep a Changelog" style with clear sections: Added, Changed, Fixed, Removed, Security.
- Use timestamps (ISO 8601) and reference file paths (e.g., `apps/hive_api/routers/ingest.py`).
- For scripting/automation, use `make changelog-watch` to auto-append changes every few seconds while editing.

## Label Every Aspect You Build
- For each new component, add a short internal doc comment and a section in the changelog entry labeling:
  - Component name (e.g., `CJDropshippingAdapter`)
  - Purpose and scope
  - Entry points (routes, CLIs, Make targets)
  - Configuration keys used (e.g., `settings.auth.first_superuser`)
  - Dependencies (internal modules and external packages)

## Source Code Documentation
- Add top-of-file module docs with purpose, main responsibilities, and how to integrate.
- Functions and classes must have concise docstrings stating inputs, outputs, and side effects.
- Reference related files using backticks, e.g., `packages/shared/config.py`.

## Configuration Access
- Access settings defensively. Assume optional keys may be missing.
- Do not crash on missing config; prefer safe defaults with clear log messages.

## Database Models
- Use SQLAlchemy 2.0 style: `Mapped[]`, `mapped_column()`, annotated relationships.
- Include `__repr__` for core models.

## Error Handling
- Never let background initialization failures crash startup.
- Return HTTP 200 with a clear "skipped" reason when integrations are intentionally unconfigured in dev.

## Testing and Verification
- Keep `scripts/verify_integrations.sh` passing at all times.
- Add a Make target for any manual workflow you introduce.

## Commit Hygiene
- Small, focused changes.
- Reference files and functions in commit messages.

## File Ownership and Notes for Future Devs
- At the top of new files, include a brief comment: author, date, context, and related modules.

