# Contributing

Thanks for your interest in improving this project! This guide covers local
setup, the quality bar, and the commit/PR conventions.

## Prerequisites

- Python 3.12+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Enable the pre-commit hooks (runs ruff on staged files before each commit)
pre-commit install
```

## Quality gate

These are the same checks CI runs — please make sure they pass before pushing:

```bash
ruff check .            # lint
ruff format --check .   # formatting
pytest                  # tests
```

You can run the hooks across the whole repo at any time:

```bash
pre-commit run --all-files
```

## Commit messages

This repository follows
[**Conventional Commits**](https://www.conventionalcommits.org/).

```
<type>(<optional scope>): <short summary>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`.

Examples:

```
feat(tasks): add pagination to the task list endpoint
fix(auth): reject expired JWTs with 401
docs(readme): add architecture diagram
chore(deps): bump bcrypt to 4.0.1
```

## Pull requests

1. Branch off `main` (`git switch -c feat/short-description`).
2. Keep changes focused; update tests and docs alongside code.
3. Ensure the quality gate passes.
4. Open a PR with a Conventional-Commits-style title and fill in the template.

## Reporting bugs / requesting features

Use the issue templates under **Issues → New issue**.
