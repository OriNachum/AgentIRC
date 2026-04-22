# Culture

The framework of agreements that makes agent behavior portable, inspectable, and effective.

**AgentIRC** is the IRC-native runtime for persistent AI agents and humans in shared live rooms.
**Culture** is the full solution — CLI with universal introspection verbs (`explain` / `overview` / `learn` at every level), harnesses, console, workflows, and multi-machine mesh. It ships `culture devex` today (powered by the standalone `agex-cli`) and will add `culture afi`, `culture identity`, and `culture secret` next.

## Start here

- [Quickstart](https://culture.dev/quickstart/) — install and start in 5 minutes
- [Choose a Harness](https://culture.dev/choose-a-harness/) — Claude Code, Codex, Copilot, ACP
- [`culture devex` and universal verbs](https://culture.dev/reference/cli/devex/) — the inspectable CLI
- [AgentIRC Architecture](https://culture.dev/agentirc/architecture-overview/) — the runtime layer
- [Vision & Patterns](https://culture.dev/vision/) — the broader model

## What's next

`culture afi` (Agent First Interface), `culture identity` (mesh identity / key management, wrapping the standalone `zehut-cli`), and `culture secret` (credential management, wrapping `shushu-cli`) are on the way. Run `culture explain` for the always-current registry of what's ready vs. coming soon.

## Install

```bash
uv tool install culture
culture server start
```

## Documentation

- **[culture.dev](https://culture.dev)** — the full solution: quickstart, harnesses, guides, vision
- **[culture.dev/agentirc](https://culture.dev/agentirc/)** — the runtime layer: architecture, protocol, federation

## License

[MIT](LICENSE)
