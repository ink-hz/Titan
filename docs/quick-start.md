# Quick Start — Your First Super-Agent in 5 Minutes

This guide walks you through building and launching a fully functional AI Security Super-Agent using Titan's `security` template. By the end, you'll have a running product with Panorama visualization, a workspace, and a chat interface.

---

## Prerequisites

- Python 3.11+
- An LLM API key (DeepSeek, OpenAI, Anthropic, or any OpenAI-compatible endpoint)

---

## 1. Install Titan

```bash
pip install titan-agent
```

Verify the installation:

```bash
titan --version
# titan 0.1.0
```

---

## 2. Initialize from a Template

```bash
titan init --template security my-security-agent
cd my-security-agent
```

This generates the following project structure:

```
my-security-agent/
├── titan.yaml              # Project configuration
├── tools/
│   ├── waf.py              # WAF management tool (MCP-compatible)
│   ├── threat_intel.py     # Threat intelligence queries
│   ├── log_analyzer.py     # Log search and analysis
│   └── incident.py         # Incident lifecycle management
├── agents/
│   ├── brain.yaml          # Agent Brain configuration
│   ├── threat_detector.yaml    # Specialist: threat detection
│   ├── incident_responder.yaml # Specialist: incident response
│   └── rule_factory.yaml       # Factory: produces detection rules
├── schemas/
│   ├── detection_rule.yaml # Schema for auto-produced rules
│   ├── response_plan.yaml  # Schema for response plans
│   └── workflow.yaml       # Schema for solidified workflows
└── experience/             # Auto-populated at runtime
    ├── solidified/
    └── memory/
```

---

## 3. Define Tools

Tools are standard Python functions decorated with `@titan.tool`. Titan auto-discovers them via the MCP (Model-Context Protocol) standard.

Open `tools/waf.py` — the template gives you a working example:

```python
from titan import tool

@tool(
    name="block_ip",
    description="Block an IP address at the WAF layer",
    schema={
        "ip": {"type": "string", "format": "ipv4"},
        "duration": {"type": "string", "enum": ["1h", "24h", "7d", "permanent"]},
        "reason": {"type": "string"}
    }
)
def block_ip(ip: str, duration: str = "24h", reason: str = "") -> dict:
    """Block an IP address. Replace with your actual WAF API call."""
    # TODO: integrate with your WAF (Cloudflare, AWS WAF, nginx, etc.)
    return {"status": "blocked", "ip": ip, "duration": duration}


@tool(
    name="list_blocked_ips",
    description="List all currently blocked IP addresses"
)
def list_blocked_ips() -> list:
    """Return current blocklist. Replace with your actual WAF query."""
    # TODO: query your WAF
    return []
```

Add your own tools by dropping `.py` files into `tools/`. Titan discovers them at startup.

---

## 4. Define Agents

Agents are declared in YAML. Open `agents/brain.yaml`:

```yaml
kind: AgentBrain
name: SecurityBrain
model: deepseek-r1           # or gpt-4o, claude-sonnet, etc.
description: >
  AI Security Super-Agent. Understands security intents,
  decomposes complex requests, delegates to specialists,
  and solidifies proven response patterns.

delegates_to:
  - threat_detector
  - incident_responder
  - rule_factory

solidify: true                # Enable experience solidification
memory: persistent            # Remember across sessions

system_prompt: |
  You are the brain of an AI security super-agent.
  Your job is to understand the user's security intent,
  break it into actionable steps, and delegate to your
  specialist agents. Always explain what you're doing
  and why.
```

A specialist agent (`agents/threat_detector.yaml`):

```yaml
kind: SpecialistAgent
name: threat_detector
model: deepseek-r1
description: Detects threats by analyzing logs, traffic patterns, and intelligence feeds.

tools:
  - log_analyzer.search_logs
  - log_analyzer.aggregate
  - threat_intel.lookup_ip
  - threat_intel.lookup_domain

system_prompt: |
  You are a threat detection specialist. Given a detection task,
  use your tools to investigate and produce a clear finding.
  Be specific: include IPs, timestamps, and evidence.
```

A factory agent (`agents/rule_factory.yaml`):

```yaml
kind: FactoryAgent
name: rule_factory
model: deepseek-r1
description: Produces new detection rules under schema constraints.

produces:
  - schema: schemas/detection_rule.yaml
    target: rules/
    auto_validate: true       # Validate output against schema before deployment
    auto_test: true           # Run generated test cases

system_prompt: |
  You are a detection rule factory. When asked to create a rule,
  produce it according to the detection_rule schema. Include
  test cases. If validation fails, fix the rule and retry.
```

---

## 5. Configure Schemas

Schemas define the **bounded solution space** for factory agents. Open `schemas/detection_rule.yaml`:

```yaml
kind: Schema
name: detection_rule
version: v1
description: Schema for auto-produced threat detection rules

spec:
  type: object
  required: [name, description, condition, action, severity, tags]
  properties:
    name:
      type: string
      pattern: "^[a-z][a-z0-9_]{2,48}$"
    description:
      type: string
      maxLength: 500
    condition:
      type: object
      required: [field, operator, value]
      properties:
        field:
          type: string
          enum: [src_ip, dst_ip, path, method, status_code,
                 user_agent, country, request_rate]
        operator:
          type: string
          enum: [eq, neq, gt, lt, gte, lte, contains, regex, in]
        value: {}
    action:
      type: string
      enum: [block, alert, throttle, captcha, log]
    severity:
      type: string
      enum: [critical, high, medium, low, info]
    tags:
      type: array
      items:
        type: string
    ttl:
      type: string
      pattern: "^[0-9]+(h|d|w)$"
      default: "7d"
```

When the Rule Factory Agent produces a rule, Titan validates it against this schema **before** deployment. Invalid outputs trigger self-correction, not failures.

---

## 6. Set Your LLM Key and Launch

```bash
export TITAN_LLM_API_KEY="sk-..."        # Your LLM API key
export TITAN_LLM_BASE_URL="https://..."   # Optional: custom endpoint

titan serve
```

You should see:

```
 _____ _ _
|_   _(_) |_ __ _ _ __
  | | | | __/ _` | '_ \
  | | | | || (_| | | | |
  |_| |_|\__\__,_|_| |_|  v0.1.0

[brain]     SecurityBrain loaded (deepseek-r1)
[specialist] threat_detector loaded (3 tools)
[specialist] incident_responder loaded (4 tools)
[factory]   rule_factory loaded (schema: detection_rule.v1)
[tools]     7 MCP tools auto-discovered
[solidify]  Experience engine ON (0 solidified workflows)
[ui]        Panorama:  http://localhost:8086/panorama
[ui]        Workspace: http://localhost:8086/workspace
[ui]        Chat:      http://localhost:8086/chat
[ready]     Super-Agent is live.
```

---

## 7. Explore — Panorama Mode

Open **http://localhost:8086/panorama** in your browser.

You'll see a real-time architecture visualization:

```
┌──────────────────────────────────────────────────┐
│                  PANORAMA VIEW                    │
│                                                  │
│         ┌──────────────────┐                     │
│         │  SecurityBrain   │                     │
│         │    (idle)        │                     │
│         └───┬────┬────┬───┘                     │
│             │    │    │                          │
│    ┌────────▼┐ ┌─▼────────┐ ┌──▼─────────┐     │
│    │ threat  │ │ incident │ │  rule      │     │
│    │ detector│ │ responder│ │  factory   │     │
│    │  (idle) │ │  (idle)  │ │  (idle)    │     │
│    └────┬────┘ └────┬─────┘ └─────┬──────┘     │
│         │           │             │              │
│    ┌────▼───────────▼─────────────▼──────┐      │
│    │          7 MCP Tools                │      │
│    │  waf(2) threat_intel(2) log(2) inc(1)│     │
│    └─────────────────────────────────────┘      │
│                                                  │
│    Solidified Workflows: 0  │  Rules: 0          │
└──────────────────────────────────────────────────┘
```

Agents light up when active. Click any node to inspect its config, tools, and recent activity.

---

## 8. Try It — Chat Mode

Open **http://localhost:8086/chat** and type:

```
Show me all IPs that hit /admin more than 50 times in the last hour
```

Watch what happens:

1. **Brain** parses the intent → delegates to `threat_detector`
2. **threat_detector** calls `log_analyzer.search_logs` and `log_analyzer.aggregate`
3. Results appear in the **Workspace** (a sortable table of IPs, counts, geolocations)
4. Brain summarizes in **Chat**

Now try something that triggers production:

```
Create a detection rule that blocks any IP hitting /admin more than 100 times per hour
```

1. **Brain** delegates to `rule_factory`
2. **rule_factory** produces a rule conforming to `detection_rule.v1`
3. Titan **validates** the rule against the schema
4. Rule appears in **Workspace** for review
5. Approve it → deployed to `rules/`

---

## 9. Watch Solidification in Action

Repeat similar intents a few times:

```
Block IP 203.0.113.42
Block IP 198.51.100.17
Block IP 192.0.2.99
```

After the third time, check the console:

```
[solidify] Pattern detected: "block single IP"
[solidify] Solidifying into deterministic workflow...
[solidify] Workflow saved: experience/solidified/block_single_ip.v1.yaml
```

The next time you say "Block IP x.x.x.x", Titan skips the LLM entirely and executes the solidified workflow. **50ms instead of 3 seconds. $0 instead of $0.02.**

View solidified workflows in Panorama or inspect the YAML directly:

```yaml
# experience/solidified/block_single_ip.v1.yaml
kind: SolidifiedWorkflow
name: block_single_ip
version: v1
trigger:
  intent_pattern: "block (single )?(ip|IP) *"
  extract:
    ip: { pattern: "\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b" }
steps:
  - tool: waf.block_ip
    args:
      ip: "{{ ip }}"
      duration: "24h"
      reason: "Manual block via chat"
  - respond: "Blocked {{ ip }} for 24h."
stats:
  times_used: 3
  avg_latency_ms: 47
  created: 2026-03-26T10:32:00Z
```

---

## What's Next

| Topic | Link |
|-------|------|
| Add custom tools | `docs/tools.md` |
| Build specialist agents | `docs/agents.md` |
| Design production schemas | `docs/schemas.md` |
| Tune solidification thresholds | `docs/solidification.md` |
| Connect multiple Super-Agents | `docs/collaboration.md` |
| Deploy to production | `docs/deployment.md` |
| Build from the philosophy | `docs/philosophy.md` |

---

<p align="center">
  <b>Titan</b> — Stop building agent demos. Start shipping agent products.
</p>
