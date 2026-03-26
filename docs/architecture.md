# Titan Architecture Guide

> This document describes the structural architecture of Titan -- the layers, data flows, extension points, and UI modes. For **why** these decisions were made, see [philosophy.md](./philosophy.md).

---

## 1. Architecture Overview

```
+============================================================================+
|                           USER INTERACTION LAYER                           |
|                                                                            |
|   +------------------+  +------------------+  +----------------------+     |
|   |   Panorama Mode  |  | Conversation Mode|  |   Workspace Mode     |     |
|   |   (full picture) |  |  (dialog + viz)  |  | (deep-dive artifacts)|     |
|   +--------+---------+  +--------+---------+  +----------+-----------+     |
|            |                     |                        |                 |
|            +---------------------+------------------------+                |
|                                  |                                         |
+==================================|=========================================+
                                   v
+============================================================================+
|                            AGENT BRAIN LAYER                               |
|                        (the operating system)                              |
|                                                                            |
|   +----------------+  +---------------+  +--------------+  +----------+   |
|   | Intent Parser  |  | Task Planner  |  | Dispatcher   |  | Memory   |   |
|   | (understand)   |  | (decompose)   |  | (delegate)   |  | (recall) |   |
|   +----------------+  +---------------+  +--------------+  +----------+   |
|                                                                            |
+============================================================================+
          |                        |                        |
          v                        v                        v
+==================+  +=====================+  +========================+
| SPECIALIST AGENTS|  |   FACTORY AGENTS    |  |   SOLIDIFIED SKILLS    |
|                  |  |                     |  |                        |
| Investigation    |  | Rule Factory        |  | Deterministic DAGs     |
| Policy Tuning    |  | Agent Factory       |  | (zero-token execution) |
| Behavior Analysis|  | Workflow Factory     |  |                        |
| Risk Assessment  |  | Payload Factory     |  |                        |
+========+=========+  +==========+==========+  +============+===========+
         |                       |                           |
         +-----------------------+---------------------------+
                                 |
                                 v
+============================================================================+
|                         CAPABILITY LAYER (MCP / CLI)                       |
|                                                                            |
|  +----------+ +----------+ +----------+ +----------+ +----------+         |
|  | Perceive | | Decide   | | Execute  | | Present  | | Remember |         |
|  | alert    | | CORR     | | policy   | | chart    | | memory   |         |
|  | log      | | JM       | | push     | | table    | | workflow |         |
|  | asset    | | ULRA.deep| | asset    | | report   | | case     |         |
|  | gateway  | | risk     | | im       | | timeline | |          |         |
|  | ULRA     | |          | | claw     | | dashboard| |          |         |
|  | WDCS     | |          | | factory  | |          | |          |         |
|  +----------+ +----------+ +----------+ +----------+ +----------+         |
|                                                                            |
+============================================================================+
                                 |
                                 v
+============================================================================+
|                     ARTIFACT & VERIFICATION LAYER                          |
|                                                                            |
|   +----------------+     +------------------------------------------------+|
|   | Schema Registry|     |         Verification Pipeline                  ||
|   | (structural    |     |                                                ||
|   |  contracts)    |     | Schema Check -> Sandbox Test -> Replay Check   ||
|   +-------+--------+     |     -> Canary Deploy -> Effect Monitoring      ||
|           |              +---------------------+--------------------------+|
|           v                                    |                           |
|   +----------------+                           v                           |
|   | Artifact Store |              +------------------------+               |
|   | draft -> active|              |   Human Approval Gate  |               |
|   |   -> retired   |              | (L2/L3 trust actions)  |               |
|   +----------------+              +------------------------+               |
|                                                                            |
+============================================================================+
                                 |
                                 v
+============================================================================+
|                           RUNTIME SUBSTRATE                                |
|                                                                            |
|   +-------------+  +-----------+  +------------+  +------------------+    |
|   | Conversation |  | MCP Tool  |  | Data Lake  |  | Domain Modules   |    |
|   | Engine +     |  | Bus       |  | (Pulsar,   |  | (ULRA, WDCS,     |    |
|   | AG-UI Render |  |           |  | ClickHouse)|  |  CORR, JM, etc.) |    |
|   +-------------+  +-----------+  +------------+  +------------------+    |
|                                                                            |
+============================================================================+
                                 |
                                 v
+============================================================================+
|                       EXTERNAL COLLABORATION                               |
|                                                                            |
|   +---------------------+          +----------------------------------+    |
|   | A2A Transport       |          | External Super-Agents            |    |
|   | (intent-level       | <------> | (DevOps, Knowledge Base,         |    |
|   |  communication)     |          |  Digital Human, etc.)            |    |
|   +---------------------+          +----------------------------------+    |
|                                                                            |
+============================================================================+
```

---

## 2. Layer Responsibilities

### 2.1 User Interaction Layer

The only surface end users touch. No menus, no navigation trees -- the conversation is the universal entry point. Three modes (detailed in Section 5) serve different information density needs.

**Responsibilities:**
- Accept natural language input from users
- Render schema-constrained presentation primitives (charts, tables, timelines) inline
- Switch between Panorama / Conversation / Workspace modes based on context
- Display agent reasoning traces (optional, toggleable)
- Surface approval requests for L2 trust-level actions

### 2.2 Agent Brain Layer

The operating system of the entire product. It receives user intent, decomposes it into executable tasks, dispatches work to specialist/factory agents or solidified skills, and assembles the final response.

**Responsibilities:**
- **Intent Parser:** Understand what the user wants, even when phrased ambiguously or in ways no PM anticipated.
- **Task Planner:** Decompose complex intents into ordered sub-tasks. Decide which agents or skills to invoke.
- **Dispatcher:** Route tasks to the right specialist agent, factory agent, or solidified skill. Handle handoffs between agents.
- **Memory:** Maintain long-term memory (cross-session context, user preferences, historical decisions). Feed relevant memory into planning.

**Key constraint:** The Brain does not call tools directly for domain work. It delegates to specialists. The Brain only calls meta-level tools (memory, presentation, agent management).

### 2.3 Specialist Agent Layer

Domain-specific executors. Each specialist agent has a focused role, a limited tool set, and a potentially different underlying model.

**Responsibilities:**
- Execute domain-specific reasoning (investigation, policy analysis, risk assessment)
- Call capability-layer tools within their permitted scope
- Return structured conclusions to the Brain
- Emit action traces for experience solidification

**Key constraint:** Specialists cannot see each other's context. They communicate only through the Brain. This enforces context isolation and least privilege.

### 2.4 Factory Agent Layer

Producers that create new artifacts. They do not execute operational tasks -- they manufacture capabilities.

**Responsibilities:**
- **Rule Factory:** Generate detection rules from threat descriptions, false-positive samples, or gap analysis.
- **Agent Factory:** Generate new specialist agent definitions (role, tool set, permissions, system prompt).
- **Workflow Factory:** Analyze action traces and distill recurring patterns into deterministic DAGs.
- **Payload Factory:** Generate test payloads (attack variants, edge cases) for verification.

**Key constraint:** All factory output goes through the Artifact & Verification Layer. Nothing a factory produces takes effect without schema validation and (for L2+ actions) human approval.

### 2.5 Solidified Skills

The output of experience solidification. These are deterministic workflows (DAGs) that execute without LLM invocation.

**Responsibilities:**
- Execute routine, previously-identified patterns at zero token cost
- Report execution results back to the Brain
- Flag deviations (when real-world data no longer matches the solidified pattern) for re-evaluation

### 2.6 Capability Layer (MCP / CLI)

The unified tool registry. Every capability in the system is registered here with a schema, trust level, and hooks.

**Responsibilities:**
- Expose tools via MCP (for agents) and CLI (for humans and agent bash execution)
- Enforce trust-level hooks (L0-L3) on every invocation
- Route tool calls to the appropriate runtime module
- Record all invocations for audit and solidification analysis

**Five tool categories:**
| Category | Purpose | Side Effects |
|----------|---------|-------------|
| **Perceive** | Read state -- alerts, logs, assets, behavior data | None (read-only) |
| **Decide** | Analyze and judge -- correlation, risk scoring, deep analysis | None (read-only) |
| **Execute** | Change state -- update policies, push configs, notify humans | **Yes** (write) |
| **Present** | Render information -- charts, tables, reports, timelines | None (render-only) |
| **Remember** | Persist knowledge -- memory, workflows, case records | Yes (write to memory) |

### 2.7 Artifact & Verification Layer

The quality gate for all AI-produced artifacts.

**Responsibilities:**
- **Schema Registry:** Define and version structural contracts for every artifact type.
- **Artifact Store:** Manage artifact lifecycle (draft -> under-review -> active -> retired).
- **Verification Pipeline:** Five-stage validation:
  1. Schema Check -- structural conformance
  2. Sandbox Test -- functional correctness in isolated environment
  3. Replay Check -- run against historical data to detect regressions
  4. Canary Deploy -- gradual rollout with A/B comparison
  5. Effect Monitoring -- continuous post-deployment tracking

- **Human Approval Gate:** Blocking gate for L2+ trust-level artifacts. No bypass.

### 2.8 Runtime Substrate

The foundation that everything runs on. In AEGIS, this is the existing PAIP V1 platform. In other Titan deployments, this is whatever domain infrastructure exists.

**Responsibilities:**
- Conversation engine and AG-UI renderer
- MCP tool bus (routing, rate limiting, circuit breaking)
- Data lake (event ingestion, storage, query)
- Domain modules (the actual functional engines -- detection, analysis, policy enforcement)

### 2.9 External Collaboration Layer

Intent-level communication with other super-agents via A2A protocol.

**Responsibilities:**
- Send and receive natural language intents to/from external super-agents
- Translate received intents into internal task plans
- Return conclusions in natural language (not raw data)

---

## 3. Data Flows

### 3.1 User Request Flow

```
User speaks
  -> [Interaction Layer] parse input
  -> [Agent Brain] understand intent, plan tasks
  -> [Brain] dispatch to Specialist Agent(s)
  -> [Specialist] call Capability Layer tools
  -> [Capability Layer] invoke Runtime Substrate
  -> [Runtime] return data
  -> [Specialist] reason, produce conclusion
  -> [Brain] assemble response, select presentation primitives
  -> [Interaction Layer] render response with embedded visualizations
  -> User sees result
```

### 3.2 Capability Production Flow

```
Brain identifies capability gap (or threat intelligence triggers it)
  -> [Brain] dispatch to Factory Agent
  -> [Factory] generate artifact (schema-constrained)
  -> [Artifact Layer] schema validation
  -> [Verification Pipeline] sandbox test -> replay check
  -> [Human Approval Gate] human reviews and approves (L2)
  -> [Artifact Store] status: draft -> active
  -> [Runtime] hot-load new artifact
  -> Capability is live (zero downtime)
```

### 3.3 Experience Solidification Flow

```
Specialist Agent executes a task
  -> [Capability Layer] action trace recorded
  -> [ULRA inward-facing] analyze traces across invocations
  -> Pattern detected (e.g., same 6-step sequence for 90% of similar alerts)
  -> [Workflow Factory] distill pattern into deterministic DAG
  -> [Artifact Layer] schema validation
  -> [Human Approval Gate] human reviews proposed workflow
  -> [Solidified Skills] new Skill registered
  -> Next matching request -> Skill executes (zero tokens, milliseconds)
```

### 3.4 Super-Agent Collaboration Flow

```
Brain determines it needs external help
  -> [Brain] formulate intent in natural language
  -> [A2A Transport] send intent to external super-agent
  -> [External Super-Agent] interprets, executes internally, returns conclusion
  -> [A2A Transport] receive response
  -> [Brain] integrate external conclusion into task plan
  -> Continue normal flow
```

---

## 4. Extension Points

### 4.1 Adding a New Tool

1. **Define the tool schema** in the Schema Registry (input/output JSON schema, description).
2. **Assign a trust level** (L0-L3) and configure hooks (pre-hook, post-hook).
3. **Assign a category** (Perceive / Decide / Execute / Present / Remember).
4. **Implement the handler** -- the function that executes when the tool is called.
5. **Register** in the Capability Layer. The tool is now available via MCP and CLI automatically.

```
# Example: registering a new tool
titan.capability.register(
    name="threat_intel.lookup",
    category="perceive",
    trust_level=TrustLevel.L0,
    schema=ThreatIntelLookupSchema,
    handler=threat_intel_lookup_handler,
    post_hook=audit_log,
)
```

### 4.2 Adding a New Specialist Agent

1. **Define the agent profile**: role description, permitted tools (subset of Capability Layer), system prompt.
2. **Choose a model**: the agent can use a different LLM than the Brain (smaller, cheaper, domain-optimized).
3. **Register with the Brain's dispatcher**: the Brain needs to know when to route tasks to this specialist.
4. **Set trust boundaries**: which tools can this agent call? What trust levels does it operate at?

```
# Example: registering a new specialist agent
titan.core.agents.register(
    name="compliance_auditor",
    role="Audit agent actions for regulatory compliance",
    permitted_tools=["log.search", "memory.read", "case.read"],
    model="qwen-2.5-32b",
    trust_ceiling=TrustLevel.L1,  # can only do L0 and L1 actions
    system_prompt=COMPLIANCE_AUDITOR_PROMPT,
)
```

### 4.3 Adding a New Factory Agent

1. **Define the artifact type** this factory produces.
2. **Create the artifact schema** in the Schema Registry.
3. **Implement the generation logic**: how does the factory agent produce artifacts?
4. **Configure the verification pipeline** for this artifact type (which stages apply, what sandbox tests to run).
5. **Register** with the Factory Agent layer.

### 4.4 Adding a New Schema

1. **Define the schema** as a JSON Schema document with:
   - Required and optional fields
   - Value constraints (types, ranges, enums)
   - Structural constraints (nesting, array bounds)
2. **Version it** (schemas are immutable per version; new versions are additive).
3. **Register** in the Schema Registry.
4. **Update the verification pipeline** to handle artifacts conforming to this schema.

```
# Example: schema lifecycle
v1: { type: "detection_rule", fields: [...] }       # initial
v2: { type: "detection_rule", fields: [..., new] }   # additive, backward-compatible
```

### 4.5 Adding a New Solidified Skill

Skills are **not manually created** in normal operation -- they emerge from experience solidification. However, for bootstrapping or migration, manual skill registration is supported:

1. **Define the DAG** (nodes = tool calls, edges = data dependencies, conditions = branching logic).
2. **Define the trigger condition** (what input pattern activates this skill).
3. **Register** as a Solidified Skill. The Brain will prefer this skill over agent reasoning for matching inputs.

---

## 5. UI Three Modes

Titan defines three interaction modes. All three share the same backend -- they differ only in information density and layout.

### 5.1 Panorama Mode

**Purpose:** Full-picture situational awareness at a glance.

```
+------------------------------------------------------------------+
|  Titan Panorama                                                   |
|  [capability overview] [system health] [active workflows]         |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+  +------------------+  +-----------------+  |
|  | Capability Map   |  | Active Agents    |  | Recent Actions  |  |
|  |                  |  |                  |  |                 |  |
|  | Perceive    (6)  |  | Brain     active |  | 14:02 alert     |  |
|  | Decide      (4)  |  | Invest.   idle   |  | 14:01 policy    |  |
|  | Execute     (6)  |  | Policy    active |  | 13:58 solidify  |  |
|  | Present     (5)  |  | Analysis  idle   |  | 13:55 rule.new  |  |
|  | Remember    (3)  |  | RuleFactory busy |  | 13:50 scan      |  |
|  +------------------+  +------------------+  +-----------------+  |
|                                                                    |
|  +-------------------------------------------------------------+  |
|  | Solidification Progress                                      |  |
|  | ████████████░░░░░░ 67% of routine tasks solidified           |  |
|  | Token savings this month: 2.4M tokens ($18.20)               |  |
|  +-------------------------------------------------------------+  |
|                                                                    |
|  [ Start Conversation ]                                           |
+------------------------------------------------------------------+
```

**When to use:** First login, executive briefing, system health check.

**Key elements:**
- Capability map (all tools, grouped by category)
- Active agent status
- Recent action log
- Solidification progress and cost savings
- Entry point into Conversation Mode

### 5.2 Conversation Mode

**Purpose:** The primary interaction mode. Natural language dialog with embedded presentation primitives.

```
+----------------------------------+-----------------------------------+
|  Conversation                    |  Workspace (collapsible)          |
|                                  |                                   |
|  User: What's the security       |  Agent Reasoning:                 |
|  posture for the last 24 hours?  |                                   |
|                                  |  1. Parse intent: posture query   |
|  Titan:                          |  2. [Perceive] alert.query  12ms  |
|  Over the past 24 hours, your    |  3. [Perceive] ULRA.analyze 89ms  |
|  AI systems processed 14,203     |  4. [Decide]   CORR.correlate 34ms|
|  requests with 247 security      |  5. [Present]  chart.line    8ms  |
|  events detected.                |                                   |
|                                  |  Tools invoked: 4                 |
|  +---------------------------+   |  Trust level: L0 (auto)           |
|  | [Line Chart: Events/Hour] |   |  Tokens used: 1,847              |
|  | ~~~~~/\~~~~~/\~~          |   |                                   |
|  +---------------------------+   |  Solidification hint:             |
|                                  |  Similar query handled 43 times.  |
|  3 events require attention:     |  Pattern similarity: 94%          |
|  +---------------------------+   |  -> Eligible for solidification   |
|  | [Table: Top 3 Alerts]     |   |                                   |
|  | Sev | Type    | Status    |   |                                   |
|  | P1  | Jailbrk | Open      |   |                                   |
|  | P2  | Inject  | Triaged   |   |                                   |
|  | P2  | Exfil   | Resolved  |   |                                   |
|  +---------------------------+   |                                   |
|                                  |                                   |
|  > [input field]                 |                                   |
+----------------------------------+-----------------------------------+
```

**When to use:** All normal interactions. This is the default mode.

**Key elements:**
- Left panel: conversation with embedded visualizations (charts, tables, timelines)
- Right panel (collapsible): agent reasoning trace, tool invocations, trust level indicators, solidification hints
- Presentation primitives are rendered inline, not on separate pages
- Approval requests appear inline with accept/reject controls

### 5.3 Workspace Mode

**Purpose:** Deep-dive into a specific artifact, workflow, or investigation. Full-screen working surface.

```
+------------------------------------------------------------------+
|  Workspace: Investigation #4721 - Progressive Role Hijack         |
|  [Back to Conversation]                                           |
+------------------------------------------------------------------+
|                                                                    |
|  +---------------------------+  +------------------------------+  |
|  | Evidence Chain             |  | Attack Timeline              |  |
|  |                           |  |                              |  |
|  | 1. Initial probe (benign) |  | 09:14 ----o probe           |  |
|  | 2. Role shift attempt     |  | 09:17 ------o role shift    |  |
|  | 3. Gradual escalation     |  | 09:23 --------o escalation  |  |
|  | 4. Payload delivery       |  | 09:31 ----------o payload   |  |
|  +---------------------------+  +------------------------------+  |
|                                                                    |
|  +-------------------------------------------------------------+  |
|  | Proposed Detection Rule (draft)                              |  |
|  |                                                               |  |
|  | Schema: detection_rule_v2                                     |  |
|  | Status: pending_approval                                      |  |
|  | Confidence: 0.94                                              |  |
|  |                                                               |  |
|  | [View Schema] [Approve] [Reject] [Request Changes]           |  |
|  +-------------------------------------------------------------+  |
|                                                                    |
|  +-------------------------------------------------------------+  |
|  | Verification Results                                         |  |
|  | Schema check:  PASS                                          |  |
|  | Sandbox test:  PASS (14/14 attack variants caught)           |  |
|  | Replay check:  PASS (0 false positives on 30-day history)    |  |
|  +-------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

**When to use:** When the user needs to examine, edit, or approve complex artifacts. The conversation triggers a workspace when depth is needed.

**Key elements:**
- Full-width layout for complex content
- Evidence chains, timelines, and multi-panel views
- Artifact review with inline approval controls
- Verification results displayed alongside the artifact
- One-click return to Conversation Mode

### Mode Transitions

```
Panorama ----[Start Conversation]----> Conversation
Conversation --[Deep-dive needed]----> Workspace
Workspace ----[Back to Conversation]--> Conversation
Conversation --[Show overview]-------> Panorama
```

Transitions are fluid. The Brain can suggest a mode switch ("This investigation has 12 evidence items -- would you like to open it in the workspace?"), or the user can switch manually. No data is lost during transitions.

---

## Summary

| Layer | Responsibility | Extension Point |
|-------|---------------|-----------------|
| User Interaction | Accept intent, render results | Add presentation schemas |
| Agent Brain | Understand, plan, dispatch, remember | Configure planning strategies |
| Specialist Agents | Domain-specific execution | Register new specialists |
| Factory Agents | Produce new artifacts | Register new factories + schemas |
| Solidified Skills | Zero-token deterministic execution | Manual skill registration (bootstrap) |
| Capability (MCP/CLI) | Unified tool registry | Register new tools |
| Artifact & Verification | Quality gate for AI output | Add schemas, verification stages |
| Runtime Substrate | Infrastructure foundation | Plug in domain modules |
| External Collaboration | Intent-level super-agent comms | Connect new super-agents via A2A |
