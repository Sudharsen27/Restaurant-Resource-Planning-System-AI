# Contributing

Thank you for contributing to the Restaurant Resource Planning System (RRPS).

## Ways to contribute

- Bug reports and reproducible issues
- Documentation improvements
- Tests and CI hardening
- Small, focused pull requests (no drive-by refactors)

## Development setup

1. Fork and clone the repository.
2. Copy `env/development.env.example` → local env / `Backend/.env`.
3. Prefer Docker Compose for parity:

```bash
docker compose up --build
```

4. Or run Backend + Frontend separately (see [docs/guides/local-development.md](docs/guides/local-development.md)).

## Branching

- `main` — stable release line
- Feature branches: `feat/...`, `fix/...`, `docs/...`, `chore/...`

## Pull requests

- Keep PRs focused; do not mix unrelated refactors.
- Ensure CI is green:
  - Backend: `pytest`
  - Frontend: `npm run lint` and `npm run build`
  - Docker builds (CI job)
- Do not commit secrets (`.env`, credentials, private keys).
- Update docs when behavior or env vars change.
- Follow existing code style (Python / React / TypeScript CDK).

## Commit messages

Prefer clear, imperative summaries:

```text
Fix Celery beat schedule path for Fargate ephemeral storage
Add AWS CDK ElastiCache Redis cache stack
```

## Code of conduct

Be respectful. Harassment or abusive behavior is not tolerated.

## Security issues

Do **not** open a public issue for vulnerabilities. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the MIT License.
