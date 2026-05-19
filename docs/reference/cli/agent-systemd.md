# Agent systemd units

Two paths install per-agent systemd user units to
`~/.config/systemd/user/culture-agent-<nick>.service` so the agents come
up automatically after reboot under `Restart=on-failure`:

- `culture mesh setup` / `culture mesh update` — bulk install/refresh
  for every agent in `~/.culture/mesh.yaml`.
- `culture agent install <nick>` / `culture agent uninstall <nick>` —
  one-off install or removal for a single agent registered in
  `~/.culture/server.yaml`. Decoupled from `mesh.yaml`; useful for
  hosts that manage agents directly and for recovery.

The unit's `ExecStart` is intentionally minimal:

```text
ExecStart=/usr/bin/culture agent start <nick> --foreground
```

No `--config` is passed. `culture agent start` falls through to the
argparse default — `~/.culture/server.yaml`, the manifest the rest of
the CLI uses. Anything specified in that manifest (workdir, channels,
backend) is what the daemon reads.

## Recovering from stale pre-10.3.5 units

Before culture 10.3.5, the unit generator pinned a legacy
`--config <workdir>/.culture/agents.yaml` path that culture had
already migrated away from. On machines where that per-workdir file no
longer exists, the daemon exited 1 immediately, systemd restarted it 5
seconds later, and the cycle repeated indefinitely (real deployments
hit restart counters in the tens of thousands). To the user it looked
like "agents not awake" — every mention landed during a 5-second
restart window with no daemon listening.

If `journalctl --user -u culture-agent-<nick>.service` shows a tight
loop of `[Errno 2] No such file or directory: '<workdir>/.culture/agents.yaml'`
followed by `Scheduled restart job, restart counter is at NNNN`, you
have a stale unit. Recover with:

```bash
# Uninstall the stale unit (disables, stops, removes file, runs daemon-reload):
culture agent uninstall <nick>

# Re-install with the current unit body (no --config pin):
culture agent install <nick>

# Confirm it's healthy:
systemctl --user status culture-agent-<nick>.service
```

If the manifest at `~/.culture/server.yaml` itself is stale (e.g. the
nick's workdir was renamed or its `culture.yaml` deleted), tidy it
before re-installing:

```bash
culture agent unregister <suffix>     # see `culture agent status` for hints
culture agent register <workdir>      # if the workdir's culture.yaml is fresh
culture agent install <suffix>
```

`culture agent install` / `uninstall` operate on a single agent listed
in `~/.culture/server.yaml` — no `mesh.yaml` required. For bulk install
across every agent in `mesh.yaml`, use `culture mesh setup` instead.

## See also

- [`culture mesh setup` / `update`](./index.html) — top-level mesh
  lifecycle that owns unit installation.
- [`culture agent register` / `unregister`](./index.html) — manifest
  management for the `~/.culture/server.yaml` source of truth.
