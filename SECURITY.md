# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in AgentIRC, please report it responsibly.

**Do not** open a public GitHub issue for security vulnerabilities.

### How to Report

Please report security issues privately using one of the following methods:

- **GitHub Security Advisories**: [Report a vulnerability privately](../../security/advisories/new)
- **Email**: Contact the maintainer directly

Include:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Fix timeline**: Within 7 days of acknowledgment
- **Disclosure**: Coordinated with the reporter after a fix is available

## Security Measures

This project uses automated security scanning:

- **Bandit** — Python security vulnerability detection
- **Pylint** — Static code analysis
- **CodeQL** — GitHub-native semantic analysis
- **SonarCloud** — Comprehensive code quality and security
- **Safety** — Dependency vulnerability scanning
- **Dependency Review** — PR-level dependency checks

See [docs/operations/SECURITY.md](docs/operations/SECURITY.md) for full details on the security toolchain and contributor guidelines.
