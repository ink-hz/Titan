# Titan Design Philosophy

> Titan is the generic Agent product framework extracted from AEGIS (AI Business Security Super-Agent). This document explains **why** Titan is designed the way it is -- not how to use it.

---

## 1. The Problem: Agent Frameworks ≠ Agent Products

LangChain, CrewAI, AutoGen, and similar frameworks have solved a real problem: **how to orchestrate agents** -- chaining LLM calls, managing tool invocations, coordinating multi-agent conversations. They are excellent middleware.

But none of them solve a different, equally hard problem: **how to ship an agent as a product to end users.**

The gap is not incremental. It is categorical:

| Dimension | Agent Frameworks | Agent Products |
|-----------|-----------------|----------------|
| **Interaction paradigm** | Developer writes orchestration code | End user expresses intent in natural language |
| **Capability production** | Developer adds tools and prompts | The system itself produces new capabilities on demand |
| **Experience accumulation** | Every run starts from scratch | Repeated patterns solidify into deterministic workflows |
| **UI/UX** | Terminal output or chat widget | Context-aware information primitives embedded in conversation |
| **Trust model** | "The developer trusts the agent" | Graduated trust hierarchy -- humans approve, agents execute |

An agent framework is a chassis. Titan is the blueprint for the entire vehicle -- engine, steering, dashboard, and safety systems included.

**Titan exists because the distance from "working agent demo" to "production agent product" is not a weekend of glue code. It is a design space that nobody has mapped.**

---

## 2. First Principles: Intent, Not Journey

Traditional product design is built on user journeys: menu -> page -> form -> confirmation -> dashboard. A user journey is, at its core, a **hardcoded prediction of user intent**. The product manager guesses what the user will want to do, in what order, and builds a fixed path for it.

This works when the problem space is bounded. It breaks when the user might say something the product manager never imagined -- which is exactly the nature of agent-powered products.

Titan returns to first principles:

```
Traditional product:  PM predicts intent -> encodes it as a journey -> user follows the path
Titan product:        User expresses intent -> Agent Brain understands -> tools execute -> result appears
```

**"Kill the user journey."** This does not mean "kill all UI." It means:

- **Keep** information presentation primitives -- charts, tables, timelines, forms. Users still need to see and interact with structured data.
- **Kill** navigation-based UI -- menus, breadcrumbs, multi-step wizards, fixed dashboards. These are crutches for a world where the system cannot understand what you want.

The conversation is the universal entry point. When the user says something no PM ever anticipated, the conversation handles it naturally. A fixed UI cannot.

**Schema-constrained presentation primitives** (see Section 3) replace fixed pages. The Agent Brain selects the right primitive -- a line chart, a data table, a timeline -- and embeds it in the conversation at the moment the user needs it. No page design, no frontend sprint, no release cycle.

---

## 3. Schema-Constrained AI Production

Unstructured AI generation (write arbitrary code, produce free-form output) has an infinite solution space. Infinite solution spaces are unverifiable, unpredictable, and untrustworthy. This is why "let GPT write code and deploy it" is not a product strategy.

Titan constrains AI generation to **schemas**:

```
Unconstrained:   AI generates arbitrary code   -> infinite solution space -> unverifiable
Titan:           AI generates schema-bound artifacts -> finite solution space -> auto-verifiable
```

A schema is a **structural contract** that tells the AI: "The thing you produce must look exactly like this." A detection rule schema defines the fields, operators, thresholds, and output format. A workflow schema defines the DAG structure, node types, and transition conditions. A presentation schema defines the chart type, axes, data bindings, and interaction hooks.

This gives Titan three properties that unconstrained generation cannot achieve:

1. **Automatic validation.** If it conforms to the schema, it is structurally correct. No human review needed for structural integrity.
2. **Hot-loading.** Schema-conformant artifacts can be loaded into the runtime without restart, because the runtime already knows how to interpret that schema.
3. **Bounded blast radius.** A schema-constrained artifact can only do what the schema allows. It cannot accidentally delete a database or expose credentials.

**This is why Titan is more reliable than general-purpose AI programming.** The AI is not writing arbitrary code. It is filling in a well-defined structure, and the structure is automatically verified before it takes effect.

Every artifact in Titan -- detection rules, sub-agents, workflows, presentation views, attack payloads -- is schema-constrained. The Schema Registry is the single source of truth for what artifacts can exist and what they can contain.

---

## 4. Experience Solidification: The Flywheel

Traditional agent systems reason from scratch on every invocation. Token cost grows linearly with usage. The 1000th identical request costs the same as the 1st.

Titan introduces **experience solidification** -- a flywheel that converts repeated agent behavior into deterministic, zero-token workflows:

```
Phase 1: Agent Brain reasons through a task, calling tools step by step
         -> action trace is recorded

Phase 2: ULRA (dual-purpose) analyzes action traces across invocations
         -> identifies recurring patterns (e.g., "for this type of alert, the agent always does A -> B -> C -> D")

Phase 3: Pattern is distilled into a deterministic workflow (DAG)
         -> proposed to human for approval

Phase 4: Approved workflow executes deterministically
         -> zero LLM tokens, millisecond latency, 100% reproducible
```

The flywheel effect:

- **The more you use it, the faster it gets.** Common paths solidify into instant execution.
- **The more you use it, the cheaper it gets.** Solidified workflows consume zero tokens.
- **The more you use it, the more reliable it gets.** Deterministic workflows have no stochastic variance.

The agent still handles novel, unseen situations through full reasoning. But the 80% of routine work gradually migrates from expensive LLM inference to free deterministic execution.

### ULRA Dual-Purpose

ULRA (User-LLM Runtime Analyzer) was originally designed to analyze the behavior of **the entities being served** (e.g., users interacting with AI systems). Titan repurposes it to also analyze **the agent's own behavior** -- the same analytical engine watches the agent work and identifies solidification opportunities. One engine, two perspectives:

1. **Outward-facing:** Analyze the behavior of users/systems the agent protects or serves.
2. **Inward-facing:** Analyze the agent's own action traces to drive experience solidification.

---

## 5. Trust Hierarchy: Humans Approve, Agents Execute

Autonomous agent execution without trust boundaries is a liability, not a feature. "The AI can do anything" sounds powerful until it deletes production data or sends an embarrassing message to a customer.

Titan enforces a strict **trust hierarchy** with four levels:

| Level | Name | Behavior | Example |
|-------|------|----------|---------|
| **L0** | Full Autonomy | Agent executes without notification | Read-only queries, log searches |
| **L1** | Post-hoc Report | Agent executes, then reports to human | Routine alert triage, status summaries |
| **L2** | Pre-approval | Agent proposes, human approves, then agent executes | Policy changes, rule deployment, new artifact activation |
| **L3** | Forbidden | Agent cannot perform this action under any circumstances | Data deletion, credential access, irreversible operations |

### Implementation: Hook Mechanism

Every tool in Titan is bound to a trust level through **hooks**:

```
Tool registration:
  name: "policy.update"
  trust_level: L2          # requires pre-approval
  pre_hook: approval_gate  # blocks execution until human approves
  post_hook: audit_log     # records action for compliance

Tool registration:
  name: "log.search"
  trust_level: L0          # full autonomy
  post_hook: audit_log     # still recorded
```

Trust levels are **not suggestions**. They are enforced at the runtime level. An agent cannot bypass an L2 gate by rephrasing its request or reasoning around it. The hook mechanism is outside the agent's control.

**The trust hierarchy is non-negotiable.** In a production agent product, the question is never "should we trust the agent?" It is "how much autonomy does each action deserve, and who approves when autonomy is exceeded?"

---

## 6. Multi-Agent Hierarchy, Not Flat Orchestra

Titan does not use a single omniscient agent. Nor does it use a flat pool of equal-weight agents that negotiate with each other.

Titan uses a **hierarchical multi-agent architecture**:

```
                    +-------------------+
                    |    Agent Brain    |    (the operating system)
                    | Intent, Planning, |
                    | Global Awareness  |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
        +-----+----+  +-----+----+  +------+-----+
        | Specialist|  | Specialist|  | Factory    |
        | Agent A   |  | Agent B   |  | Agent      |
        | (executor)|  | (executor)|  | (producer) |
        +-----------+  +-----------+  +------------+
```

Three roles:

1. **Agent Brain** -- the operating system. Understands user intent, plans task decomposition, maintains global context and long-term memory, dispatches work to specialists.
2. **Specialist Agents** -- executors. Each handles a specific domain (investigation, policy tuning, risk assessment, behavior analysis). They call tools, reason within their domain, and return conclusions to the Brain.
3. **Factory Agents** -- producers. They create new artifacts: detection rules, sub-agent definitions, workflows, attack payloads. Their output goes through schema validation and human approval before activation.

### Why Hierarchy, Not Flat?

Three reasons:

**Context isolation.** The Brain holds global context. Specialists hold domain context. Neither pollutes the other. A flat architecture either duplicates context across all agents (wasteful) or forces a single shared context (noisy).

**Least privilege.** Specialists only have access to the tools they need. The investigation agent cannot modify policies. The policy agent cannot trigger attacks. In a flat architecture, every agent has access to everything.

**Model differentiation.** The Brain can run on a frontier model (high reasoning, expensive). Specialists can run on smaller, faster, cheaper models optimized for their domain. Factory agents can run on code-generation-optimized models. A flat architecture forces the same model for every role.

---

## 7. Capability Layers: MCP / CLI / Skill

The same underlying capability should be accessible through different interfaces for different consumers. Titan exposes three capability layers on top of a single API substrate:

```
                +---------------------------+
                |     Single API Layer      |
                | (unified tool registry)   |
                +--+--------+--------+------+
                   |        |        |
              +----+--+ +---+---+ +--+----+
              |  MCP  | |  CLI  | | Skill |
              +-------+ +-------+ +-------+
```

### MCP (Model Context Protocol)

The **agent-native** interface. MCP tools are what the Agent Brain and specialist agents call during reasoning. They are also the interoperability surface -- external agents and super-agents invoke Titan's capabilities through MCP.

- Designed for programmatic invocation by LLMs
- Structured input/output (JSON schema)
- Supports cross-system interoperation (any MCP-compatible agent can call these tools)

### CLI (Command-Line Interface)

The **human-and-agent** interface. CLI commands can be executed by agents via bash, or by human operators directly. Same capability, different ergonomics.

- Designed for human readability and scriptability
- Supports piping, scripting, and automation
- Agents can fall back to CLI when MCP is not available

### Skill (Solidified Experience)

Skills are **not designed upfront**. They are the output of experience solidification (Section 4). When the system identifies a recurring agent behavior pattern and solidifies it into a deterministic workflow, that workflow becomes a Skill.

- Zero-token execution (no LLM invocation)
- Deterministic and reproducible
- Created by the system, not by developers
- Can be promoted, versioned, and retired like any other artifact

**The key insight:** MCP and CLI are designed by developers. Skills emerge from usage. The capability surface of a Titan-based product grows organically as the system learns.

---

## 8. Intent-Level Collaboration Between Super-Agents

The evolution of system interoperability:

```
Era 1: API coupling       -> System A calls System B's REST endpoint
                             (tight coupling, version hell, integration cost)

Era 2: Tool-level interop -> Agent A calls Agent B's MCP tool
                             (loose coupling, but A must know B's tool schema)

Era 3: Intent-level collab -> Super-Agent A tells Super-Agent B what it wants in natural language
                              (no coupling, no schema knowledge, just intent)
```

Titan is designed for Era 3.

When a Titan-based super-agent needs something from another super-agent, it does not browse an API catalog. It does not read an Agent Card to discover capabilities. It **expresses intent in natural language**:

```
AEGIS -> DevOps Super-Agent:
  "The AI gateway is experiencing 3x normal latency on inference requests.
   Please investigate whether this is infrastructure-related and remediate if possible."
```

The receiving super-agent interprets the intent, decides how to fulfill it using its own tools and knowledge, and returns a conclusion. Neither side needs to understand the other's internal architecture, tool inventory, or data model.

**A2A (Agent-to-Agent protocol) is the transport layer. Intent is the payload.**

This design choice has a profound consequence: **adding a new super-agent to the ecosystem requires zero integration work.** If it speaks A2A and understands natural language, it can collaborate. The collaboration surface scales with the number of super-agents without combinatorial integration complexity.

---

## Summary: The Seven Design Choices

| # | Principle | One-liner |
|---|-----------|-----------|
| 1 | Intent, not journey | Kill the user journey. Keep information primitives. |
| 2 | Schema-constrained production | Finite solution space + auto-verification > arbitrary code generation |
| 3 | Experience solidification | The more you use it, the faster and cheaper it gets |
| 4 | Trust hierarchy | Humans approve, agents execute. Non-negotiable. |
| 5 | Hierarchical multi-agent | Brain + Specialists + Factories. Not flat, not monolithic. |
| 6 | Triple capability layer | MCP for agents, CLI for humans, Skills from experience |
| 7 | Intent-level collaboration | Super-agents talk intent, not API calls |

These are not features. They are **design constraints** -- the boundaries within which every Titan feature, API, and architectural decision must fit. If a proposed feature violates any of these principles, the feature is wrong, not the principle.
