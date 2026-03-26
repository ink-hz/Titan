# Titan — Build Super-Intelligent Agent Products

> From Agent Framework to Agent Product. The last mile.

**Titan** is a production-grade framework for building **Super-Intelligent Agent Products** — not just agent orchestration, but the complete product stack: intent-driven interaction, self-producing capabilities, experience solidification, multi-agent hierarchy, and agent-native UI.

Extracted from [AEGIS](https://github.com/anthropic/aegis) (AI Business Security Super-Agent), Titan captures the universal patterns that make an agent system a **shippable product**.

### How Titan differs from LangChain / CrewAI / AutoGen

| | LangChain / CrewAI / AutoGen | Titan |
|---|---|---|
| **Focus** | Agent orchestration & chaining | Agent **product** delivery |
| **Interaction** | Developer defines user journeys | User expresses **intent**, agent figures out the rest |
| **Capabilities** | Hand-coded tools & chains | AI **self-produces** rules, sub-agents, workflows under schema constraints |
| **Performance** | Every request hits the LLM | Proven paths **solidify** into deterministic workflows — faster, cheaper, reliable |
| **Multi-Agent** | Flat or simple hierarchy | Brain + Specialist + Factory **layered hierarchy** |
| **Cross-Agent** | API integration | Natural-language **intent-level collaboration** |
| **UI** | Bring your own | Built-in **Agent-Native UI**: Panorama + Workspace + Chat |

---

## Why Titan

Every team building AI agents hits the same wall:

- **Orchestration frameworks** (LangChain, CrewAI, AutoGen) solve *"how to wire agents together"*
- **Nobody solves** *"how to ship agents as products"*

The gap is enormous: intent understanding, capability self-production, experience accumulation, multi-agent governance, and a UI that actually fits how agents work — not a chat box bolted onto a dashboard.

**Titan closes that gap.**

---

## 5 Lines to Launch a Super-Agent

```python
from titan import AgentBrain, serve

brain = AgentBrain(model="deepseek-r1")
brain.register_tools("./tools/")          # MCP tools auto-discovered
brain.enable_solidify()                    # Experience solidification ON
serve(brain, ui="panorama+chat+workspace", port=8086)
```

Open `http://localhost:8086` — you get a full agent product with Panorama architecture view, Manus-style workspace, and conversational interface. Out of the box.

---

## Core Concepts

### 1. Intent-Driven (No User Journey)

Traditional products force users through pre-designed journeys: click here, fill that, wait. Titan eliminates this entirely.

Users express **intent** in natural language. The Agent Brain decomposes the intent, routes to the right specialists, orchestrates execution, and delivers results. No menus, no forms, no workflows to memorize.

```
User: "Block all IPs from Russia that hit our login endpoint more than 100 times today"
Titan: decomposes → routes to ThreatIntel + WAFAgent → executes → confirms
```

### 2. Schema-Constrained AI Production

Agents in Titan don't just *use* tools — they **produce new capabilities**: detection rules, sub-agents, automation workflows. But not in an unconstrained, hallucination-prone way.

Every production act is bounded by a **Schema** — a formal contract that defines the solution space. The AI generates within that space; Titan validates automatically.

```yaml
# schema: detection_rule.v1
type: object
required: [name, condition, action, severity]
properties:
  condition:
    type: string
    pattern: "^(ip|path|header|body)\\."   # constrained vocabulary
  action:
    enum: [block, alert, throttle, captcha]
```

The AI produces a rule. Titan validates it against the schema. If it passes — deployed. If not — the AI self-corrects. **Bounded creativity, zero drift.**

### 3. Experience Solidification

The first time an agent handles an intent, it reasons step-by-step via LLM. Expensive, slow, but correct.

Titan watches. When the same pattern succeeds repeatedly, it **solidifies** the path into a deterministic workflow — no LLM needed. The agent gets faster and cheaper with every interaction.

```
Day 1:  "Block brute-force IPs" → LLM reasoning → 3s, $0.02
Day 30: "Block brute-force IPs" → solidified workflow → 50ms, $0.00
```

Solidified workflows are versioned, auditable, and can be manually edited. When the world changes, Titan detects drift and re-engages the LLM to adapt.

### 4. Multi-Agent Hierarchy

Titan organizes agents in a clear three-tier hierarchy:

```
┌─────────────────────────────────────────┐
│            Agent Brain                  │  ← Intent understanding, planning,
│         (Superintendent)                │    delegation, experience management
├──────────┬──────────┬───────────────────┤
│ Specialist│ Specialist│    ...           │  ← Domain-specific execution
│ Agent A   │ Agent B   │                 │    (Security, DevOps, Analytics...)
├──────────┴──────────┴───────────────────┤
│           Factory Agents                │  ← Produce new rules, agents,
│      (Rule / Agent / Workflow)          │    workflows under schema constraints
└─────────────────────────────────────────┘
```

- **Brain**: Understands intent, plans, delegates, learns
- **Specialists**: Deep domain expertise, stateful, tool-equipped
- **Factories**: Produce new capabilities — the system literally grows itself

### 5. Intent-Level Collaboration

Multiple Super-Agents (each a full Titan instance) collaborate by exchanging **natural-language intents** — not API calls, not rigid contracts.

```
SecurityAgent → DevOpsAgent:
  intent: "The service cart-api is under DDoS. Scale to 10 replicas
           and enable rate-limiting at the ingress."
```

No API design. No versioning headaches. The receiving agent understands the intent and acts. This is how humans collaborate — Titan brings the same pattern to agents.

### 6. Agent-Native UI

Titan ships with a built-in UI designed for how agents actually work:

| Mode | Purpose |
|------|---------|
| **Panorama** | Full architecture visualization — agents, tools, schemas, data flows. Like a war room. |
| **Workspace** | Manus-style working area — the agent shows its work: code, configs, dashboards, previews. |
| **Chat** | Conversational interface for intent expression and clarification. |

All three modes are live-linked. Click an agent in Panorama → see its workspace. Ask a question in Chat → watch agents light up in Panorama.

---

## Architecture

```
                          ┌─────────────────────────────┐
                          │     Agent-Native UI         │
                          │  Panorama | Workspace | Chat│
                          └────────────┬────────────────┘
                                       │
                          ┌────────────▼────────────────┐
                          │        Agent Brain          │
                          │  Intent Parser │ Planner    │
                          │  Delegator │ Memory │ Solidifier
                          └──┬─────────┬────────────┬───┘
                             │         │            │
                    ┌────────▼──┐ ┌────▼─────┐ ┌───▼────────┐
                    │ Specialist│ │ Specialist│ │  Factory   │
                    │ Agent     │ │ Agent     │ │  Agents    │
                    │ (domain)  │ │ (domain)  │ │ (produce)  │
                    └─────┬─────┘ └────┬──────┘ └─────┬──────┘
                          │            │              │
                    ┌─────▼────────────▼──────────────▼──────┐
                    │            Tool Layer (MCP)             │
                    │  Auto-discovered │ Schema-validated     │
                    └────────────────────────────────────────-┘
                                       │
                    ┌──────────────────-▼─────────────────────┐
                    │         Experience Store                │
                    │  Solidified Workflows │ Versioned Rules │
                    │  Agent Memories │ Performance Metrics   │
                    └────────────────────────────────────────-┘
```

---

## Quick Start

Build and launch a Super-Agent product in 5 minutes.

**[docs/quick-start.md](docs/quick-start.md)**

---

## Templates

Titan ships with production-ready templates for common domains:

| Template | Path | Description |
|----------|------|-------------|
| AI Security | `templates/security/` | Full AEGIS-style security super-agent: threat detection, incident response, WAF management |
| DevOps | `templates/devops/` | Infrastructure monitoring, deployment automation, incident triage |
| Customer Service | `templates/customer-service/` | Multi-channel support, knowledge base, escalation |
| Data Analysis | `templates/data-analysis/` | Natural-language queries, automated reporting, anomaly detection |

```bash
titan init --template security my-security-agent
cd my-security-agent
titan serve
```

---

## Philosophy

Titan is built on a single conviction:

> **The age of user journeys is over. The age of intent is here.**

Users should not adapt to software. Software — through agents — should adapt to users. Titan is the framework that makes this possible at production scale.

Read the full philosophy: **[docs/philosophy.md](docs/philosophy.md)**

---

## Roadmap

- [x] Agent Brain with intent decomposition
- [x] Schema-constrained production (rules, workflows)
- [x] Experience solidification engine
- [x] Multi-agent hierarchy (Brain / Specialist / Factory)
- [x] Agent-Native UI (Panorama + Workspace + Chat)
- [ ] Intent-level cross-instance collaboration
- [ ] Visual schema editor
- [ ] Solidification analytics dashboard
- [ ] Plugin marketplace for specialist agents

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

<p align="center">
  <b>Titan</b> — Stop building agent demos. Start shipping agent products.
</p>
