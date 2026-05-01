# HookBus Dashboard Enterprise

Standalone operator UI for HookBus Enterprise.

The dashboard reads live HookBus API endpoints for events, stats, publishers,
and subscriber state. Auditor SQLite is optional fallback only; HookBus is the
primary event source.

## Runtime

By default the dashboard connects to:

```bash
HOOKBUS_API_URL=http://localhost:18800
```

Equivalent environment variables are also accepted:

```bash
HOOKBUS_BASE_URL=http://localhost:18800
HOOKBUS_URL=http://localhost:18800/event
```

If HookBus authentication is enabled, set:

```bash
HOOKBUS_TOKEN=<your-hookbus-token>
```

Start locally:

```bash
hookbus-dashboard-enterprise --port 8901
```

Open:

```text
http://localhost:8901
```

## Scope

This repository contains the Enterprise dashboard UI and live HookBus API
monitor. It does not contain HookBus LLM, private policy packs, customer data,
deployment secrets, or enterprise subscriber source code.

## Licence
Source-available. NOT MIT. Production commercial use requires an
agreement with Agentic Thinking Limited. Free for non-production evaluation.
