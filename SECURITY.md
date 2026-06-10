# Security Policy

## Supported versions

This is a portfolio project; the latest `main` is the only supported version.

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Instead, report privately via one of:

- GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  (**Security → Report a vulnerability** on this repo), or
- email **houghtongilbert@gmail.com**.

Please include steps to reproduce and the potential impact. I aim to acknowledge
reports within a few days and will keep you updated on the fix.

## Scope notes

This project ships intentionally simple defaults for demonstration (e.g. SQLite,
a development `SECRET_KEY` in examples). Never deploy it with example secrets —
see the README's configuration section.
