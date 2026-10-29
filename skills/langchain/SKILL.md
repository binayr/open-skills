---
name: langchain-agent-builder
description: Build LangChain agents using create_agent with tools, middleware, structured output, human-in-the-loop, checkpointing, and LangGraph subgraph integration.
---

<langchain-agent-builder>
# LangChain `create_agent` — Skill Reference

**Version:** langchain >= 1.0
**Source:** [`langchain.agents.create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent)

---

## What `create_agent` does

`create_agent` compiles a **LangGraph `StateGraph`** that runs the ReAct loop:

```
Human message
    │
    ▼
  model node  ──── AIMessage with tool_calls? ──YES──► tools node ──┐
    ▲                                                                │
    └────────────────── ToolMessages appended ◄─────────────────────┘
    │
    NO (no tool_calls)
    │
    ▼
 Final response   [+ structured_response if response_format set]
```

The compiled graph is a standard `CompiledStateGraph`. It can be `invoke()`-d directly **or dropped as a subgraph node** into a larger LangGraph `StateGraph` — which is the typical usage when building multi-step pipelines where each agent is one node.

---

## How agents are laid out in this repo

**Since 2026-09-16 (refactor P3) each agent is a package, not a module.** One
directory per agent, holding everything that agent needs:

```
src/agents/
├── parsing/                 parse_order       GCSS payload -> ParsedData + FROs
│   ├── __init__.py          re-exports the entry point; agent-level docstring
│   ├── agent.py             create_agent(...) + the LangGraph node function
│   ├── prompts.py           SYSTEM_PROMPT for this agent
│   ├── tools.py             the `tools` list bound to this agent
│   ├── constants.py         dependency-free constants (AGENT_NAME, thresholds)
│   ├── extractors.py        ─┐
│   ├── containers.py         │ private helpers, one module per concern
│   ├── segments.py           │
│   └── persistence.py       ─┘
├── planning/                plan_order        vendor selection + rate locking
├── validation/              validate_order    address + equipment validation
├── triage/                  triage_order      diagnose/remediate stuck orders
├── pod_validation/          validate_pod      POD charge review (NO LLM)
├── execution_agent.py       execute_order / execute_milestone  (single module)
├── middleware/              shared across agents — hitl, planning_tool_logging
└── prompts/                 execution_prompts.py only (execution_agent's prompt)
```

Import an agent from its package — never from a module inside it:

```python
from agents.parsing import parse_order        # correct
from agents.parsing.agent import parse_order  # reaches past the package API
```

### Where each piece goes

| Piece | File | Notes |
|---|---|---|
| `create_agent(...)` + node function | `agent.py` | The only module that compiles the graph |
| `SYSTEM_PROMPT` | `prompts.py` | One prompt per agent, versioned independently of logic |
| `tools = [...]` | `tools.py` | The **binding**, not the implementations — see §2 |
| `AGENT_NAME`, thresholds | `constants.py` | Must import nothing: the helpers import it, so any dependency creates a cycle |
| Everything else | one module per concern | `extractors.py`, `persistence.py`, `input_builder.py`, … |

**`logger` is per-module** — every module does its own
`logger = structlog.get_logger(__name__)`. Never import `logger` from a sibling.
That was the source of four import cycles when these packages were first
generated: helpers import from `agent.py` while `agent.py` imports the helpers,
so anything shared has to live in a leaf module (`constants.py`) or be created
locally.

### The two-part pattern inside `agent.py`

```python
# ── 1. Compile the agent once at import time ──────────────────────────────────
import structlog
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig

from agents.extraction.constants import AGENT_NAME
from agents.extraction.input_builder import build_input
from agents.extraction.prompts import EXTRACTION_AGENT_PROMPT
from agents.extraction.tools import tools
from models.extraction import ExtractionResult

logger = structlog.get_logger(__name__)

agent = create_agent(
    model,
    tools,
    system_prompt=EXTRACTION_AGENT_PROMPT,
    response_format=ExtractionResult,    # result["structured_response"] is ExtractionResult
)


# ── 2. Async LangGraph node function ──────────────────────────────────────────
async def extract_order(state: OverallState, config: RunnableConfig) -> dict:
    result = await agent.ainvoke(
        {"messages": [("human", build_input(state))]},
        config=config,                    # always pass config through — carries thread_id
    )
    typed_output: ExtractionResult = result["structured_response"]
    return {"extraction_result": typed_output}
```

**Rules:**
- Compile the agent at **module level** — it is a compiled graph and safe to share across calls.
- The node function is `async def` and accepts `(state, config)`.
- Always pass `config` through to `ainvoke` — it threads the LangGraph `thread_id` and checkpointer.
- Typed output is at `result["structured_response"]` — only present when `response_format` is set.
- Importing an agent package **constructs a `ChatOpenAI` at import time** (via
  `harness.utils.model`). Callers that must not pay that cost import the entry
  point lazily inside a function — `api/routes/order_triage.py` and
  `services/order_triage_service.py` both do this deliberately.

### Not every package under `agents/` is a LangChain agent

`pod_validation` has **no `create_agent`, no LLM and no `tools.py`** — it is
deterministic charge arithmetic. The architecture rule it follows: only the
Parsing Agent uses an LLM for extraction, everything else is deterministic
Python. Don't add `create_agent` to a package just because it lives in `agents/`.

### `execution_agent.py` is still a single module

Deliberately not split. Its prompt therefore stays at
`agents/prompts/execution_prompts.py`, which is the only reason that package
still exists. If you do split it later, move that prompt to
`agents/execution/prompts.py` and delete `agents/prompts/`.

---

## Full `create_agent` signature

```python
create_agent(
    model,                    # str | BaseChatModel                         REQUIRED
    tools=None,               # list[BaseTool | Callable | dict] | None
    *,
    system_prompt=None,       # str | SystemMessage | None
    middleware=(),            # Sequence[AgentMiddleware]
    response_format=None,     # type[PydanticModel] | ToolStrategy | ProviderStrategy | dict | None
    state_schema=None,        # type[AgentState] — must be TypedDict
    context_schema=None,      # type[dataclass]
    checkpointer=None,        # Checkpointer | None
    store=None,               # BaseStore | None
    interrupt_before=None,    # list[str]  — node names to pause BEFORE
    interrupt_after=None,     # list[str]  — node names to pause AFTER
    debug=False,              # bool
    name=None,                # str — node name when used as LangGraph subgraph
    cache=None,               # BaseCache
) -> CompiledStateGraph
```

---

## 1. Model

### Static model

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-opus-4-6", temperature=0)
agent = create_agent(model, tools)
```

String shorthand is also accepted — the provider is inferred:

```python
agent = create_agent("anthropic:claude-opus-4-6", tools)
agent = create_agent("openai:gpt-4o", tools)
```

Use `temperature=0` for deterministic agents that must produce consistent structured output.

### Dynamic model selection (via middleware)

Select a model at runtime based on conversation state — e.g., use a lightweight model for simple turns and a larger model for complex ones:

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain_anthropic import ChatAnthropic

fast_model  = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
smart_model = ChatAnthropic(model="claude-opus-4-6",           temperature=0)

@wrap_model_call
def route_by_complexity(request: ModelRequest, handler) -> ModelResponse:
    """Use the larger model once the conversation has multiple turns."""
    msg_count = len(request.state["messages"])
    selected = smart_model if msg_count > 6 else fast_model
    return handler(request.override(model=selected))

agent = create_agent(
    model=fast_model,                   # default; overridden per-call by middleware
    tools=tools,
    middleware=[route_by_complexity],
)
```

> Do not call `bind_tools()` on a model used with dynamic model middleware — `create_agent` handles tool binding internally.

---

## 2. Tools

### Defining tools with `@tool`

```python
from langchain_core.tools import tool
from typing import Any

@tool
async def search_records(query: str) -> list[dict[str, Any]]:
    """
    Search the database for records matching the query string.
    Returns a list of matching record dicts.
    """
    return await db.search(query=query)

@tool
async def send_notification(recipient_email: str, subject: str, body: str) -> dict[str, Any]:
    """
    Send an email notification to the specified recipient.
    Returns a dict with keys: notification_id, status, sent_at.
    """
    return await mailer.send(to=recipient_email, subject=subject, body=body)

@tool
async def update_record(record_id: str, changes: dict[str, Any]) -> dict[str, Any]:
    """
    Apply field-level changes to an existing record.
    Returns the updated record.
    """
    return await db.update(record_id=record_id, changes=changes)
```

**Rules:**
- The docstring **is** the tool description the LLM sees — write it precisely.
- Prefer `async def` tools; `create_agent` handles both sync and async.
- Tool names default to the function name. Use `snake_case` — some providers reject spaces or special characters.
- Keep tools single-purpose. Too many tools in one agent degrades model accuracy.

### Tool organisation convention — shared implementations, per-agent binding

`@tool` implementations live **once**, in `harness/utils/lc_tools.py`. Each agent
then *binds* the subset it needs in its own `tools.py`:

```python
# src/agents/planning/tools.py
from harness.agent_tools import publish_hitl_pause
from harness.utils.lc_tools import (
    db_get_zone,
    get_mre_rate,
    get_vendor_list,
    save_vendor_ranked_list,
)

tools = [
    get_vendor_list,          # cloud DB: vendors ranked by rate for the lane
    get_mre_rate,             # cloud DB: market reference rate
    db_get_zone,              # operational DB: zone_master trip-type lookup
    save_vendor_ranked_list,  # operational DB: persist the list for re-tender
    publish_hitl_pause,       # amendments only: COST_APPROVAL pause
]
```

```python
# src/agents/planning/agent.py
from agents.planning.tools import tools

agent = create_agent(model, tools, system_prompt=PLANNING_AGENT_PROMPT, ...)
```

**Why implementations are not moved into the agent packages.** `lc_tools.py`
holds three process-global connectors, set once at startup:

```python
_api_connector   = None
_db_connector    = None
_cloud_db_connector = None      # set via _set_connectors() during app start-up
```

Copying tool implementations per agent would duplicate those globals, each agent
would initialise its own connector, and the "initialise once" contract would
break silently. Keep the implementations single-sourced; make `tools.py` the
composition point.

Keep the inline comment on each entry saying **which datastore the tool hits** —
that is the fastest way to see an agent's blast radius.

### Dynamic tool filtering (via middleware)

Filter which tools the model can see based on state, user role, or workflow stage:

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def read_before_write(request: ModelRequest, handler) -> ModelResponse:
    """Only expose write tools once the read/extraction phase is confirmed complete."""
    extraction_done = request.state.get("extraction_complete", False)

    if not extraction_done:
        # Read-only phase — suppress any tool that mutates state
        safe_tools = [t for t in request.tools if not t.name.startswith(("update_", "send_"))]
        request = request.override(tools=safe_tools)

    return handler(request)

agent = create_agent(model, tools, middleware=[read_before_write])
```

### Tool error handling (via middleware)

```python
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

@wrap_tool_call
def handle_tool_errors(request, handler):
    """Return a descriptive error message instead of crashing the agent loop."""
    try:
        return handler(request)
    except Exception as exc:
        return ToolMessage(
            content=f"Tool failed — check your inputs and try again. ({exc})",
            tool_call_id=request.tool_call["id"],
        )

agent = create_agent(model, tools, middleware=[handle_tool_errors])
```

---

## 3. System Prompt

### Static prompt string

```python
SYSTEM_PROMPT = """
You are a data extraction assistant.

Your task is to extract structured information from the provided free-text input.
...
"""

agent = create_agent(model, tools, system_prompt=SYSTEM_PROMPT)
```

Store the prompt as a constant in the agent package's own `prompts.py` (e.g.
`agents/extraction/prompts.py`). Keeping prompts separate from agent logic lets
them be versioned and swapped without touching application code — and keeping
them *inside* the agent package means an agent is self-contained.

### Dynamic prompt (via middleware)

Adjust the system prompt at invocation time based on context — e.g. user role, locale, or document type:

```python
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str:
    ctx = request.runtime.context if request.runtime else {}
    doc_type = ctx.get("document_type", "standard")
    base = "You are a data extraction assistant."

    if doc_type == "invoice":
        return f"{base} Focus on line items, totals, and payment terms."
    if doc_type == "contract":
        return f"{base} Focus on parties, obligations, and key dates."
    return base

agent = create_agent(model, tools, middleware=[context_aware_prompt])
```

---

## 4. Structured Output with Pydantic (`response_format`)

Pass a Pydantic `BaseModel` class as `response_format`. The agent will emit a typed, validated instance at `result["structured_response"]`.

### Defining the response schema

```python
from pydantic import BaseModel

class ContactInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None

class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float

class InvoiceResult(BaseModel):
    """Structured output emitted by the invoice extraction agent."""
    invoice_number: str | None = None
    vendor_name: str | None = None
    total_amount: float | None = None
    line_items: list[LineItem] = []
    contact: ContactInfo | None = None
    extraction_notes: list[str] = []
```

### Wiring it in

```python
agent = create_agent(
    model,
    tools,
    system_prompt=SYSTEM_PROMPT,
    response_format=InvoiceResult,       # pass the class, not an instance
)

result = await agent.ainvoke(
    {"messages": [("human", document_text)]},
    config=config,
)

invoice: InvoiceResult = result["structured_response"]  # fully typed and validated
print(invoice.total_amount, invoice.vendor_name)
```

### Strategy selection

By default (`langchain >= 1.0`) passing a Pydantic class uses **`ProviderStrategy`** (provider-native structured output) when available, and falls back to **`ToolStrategy`** (artificial tool call) otherwise. You can be explicit:

```python
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy

# Works with any tool-calling model:
agent = create_agent(model, tools, response_format=ToolStrategy(InvoiceResult))

# Provider-native structured output (Claude, GPT-4o, Gemini):
agent = create_agent(model, tools, response_format=ProviderStrategy(InvoiceResult))
```

### System prompt output contract

When `response_format` is set, include an explicit output contract in the system prompt so the model knows exactly what schema to emit:

```
## Output contract

Return your findings using this exact JSON schema:

{
  "invoice_number": "<string or null>",
  "vendor_name":    "<string or null>",
  "total_amount":   <float or null>,
  "line_items":     [{ "description": "...", "quantity": 1, "unit_price": 0.0 }],
  "extraction_notes": ["<any uncertainty or ambiguity worth flagging>"]
}

Never invent values. Leave a field null if it cannot be determined from the input.
```

---

## 5. Middleware

Middleware intercepts the agent loop at six hook points:

```
invoke()
   │
   ├── before_agent     ← runs ONCE before the loop starts (setup, auth checks)
   │       │
   │   ┌── before_model     ← inject context, trim messages, mutate state
   │   │       │
   │   │   model node       (LLM call — wrapped by wrap_model_call)
   │   │       │
   │   │   after_model      ← validate response, guardrails, HITL interrupt check
   │   │       │
   │   │   tools node       (execute tool calls — each wrapped by wrap_tool_call)
   │   │       │
   │   └── [loop back to before_model if more tool_calls]
   │
   └── after_agent      ← runs ONCE after the loop ends (cleanup, audit logging)
```

Each hook has a sync and async variant (`before_agent` / `abefore_agent`, `before_model` / `abefore_model`, `after_agent` / `aafter_agent`, `wrap_model_call` / `awrap_model_call`, `wrap_tool_call` / `awrap_tool_call`).

### Class-based middleware (full control)

```python
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.agents import AgentState
from typing import Any
import logging

logger = logging.getLogger(__name__)

class AuditMiddleware(AgentMiddleware):
    """Log every model call and tool invocation."""

    def before_agent(self, state: AgentState, runtime) -> dict[str, Any] | None:
        """Runs once before the agent loop starts."""
        logger.info("agent_starting", extra={"message_count": len(state["messages"])})
        return None  # return None for no state mutation; return a dict to update state

    def before_model(self, state: AgentState, runtime) -> dict[str, Any] | None:
        logger.info("model_call_starting", extra={"message_count": len(state["messages"])})
        return None

    def after_model(self, state: AgentState, runtime) -> dict[str, Any] | None:
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            logger.info("tool_calls_proposed", extra={"tools": [tc["name"] for tc in last_msg.tool_calls]})
        return None

    def after_agent(self, state: AgentState, runtime) -> dict[str, Any] | None:
        """Runs once after the agent loop completes."""
        logger.info("agent_completed", extra={"final_message_count": len(state["messages"])})
        return None

agent = create_agent(model, tools, middleware=[AuditMiddleware()])
```

### Decorator-based middleware (concise)

```python
from langchain.agents.middleware import before_model, after_model

@before_model
def trim_message_history(state, runtime):
    """Keep only the last 20 messages to stay within the context window."""
    if len(state["messages"]) > 20:
        return {"messages": state["messages"][-20:]}
    return None

@after_model
def enforce_response_length(state, runtime):
    """Guardrail: raise if the model produces an unusually long response."""
    last = state["messages"][-1]
    if len(getattr(last, "content", "") or "") > 8000:
        raise ValueError("Model response too long — possible runaway generation.")
    return None
```

### Built-in middleware

| Middleware | Import | Purpose |
|---|---|---|
| `HumanInTheLoopMiddleware` | `langchain.agents.middleware` | Pause on specific tool calls for human review |
| `SummarizationMiddleware` | `langchain.agents.middleware` | Auto-summarise long message histories |
| `LLMToolSelectorMiddleware` | `langchain.agents.middleware` | Use an LLM to decide which tools to surface |
| `ToolRetryMiddleware` | `langchain.agents.middleware` | Retry failed tool calls with back-off |
| `ModelFallbackMiddleware` | `langchain.agents.middleware` | Fall back to a secondary model on API failure |
| `ModelCallLimitMiddleware` | `langchain.agents.middleware` | Cap LLM calls per invocation |
| `PIIDetectionMiddleware` | `langchain.agents.middleware` | Detect / redact PII before the model call |

Multiple middleware can be composed in order — they are applied left-to-right:

```python
agent = create_agent(
    model,
    tools,
    middleware=[
        AuditMiddleware(),
        ToolRetryMiddleware(max_retries=2),
        HumanInTheLoopMiddleware(interrupt_on={"write_to_database": True}),
    ],
    checkpointer=checkpointer,
)
```

---

## 6. Human-in-the-Loop (HITL)

### Approach A — `HumanInTheLoopMiddleware` (tool-level gate)

Pauses the agent when the model proposes a specific tool call, before executing it. Requires a `checkpointer`.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver           # dev / test
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # production

agent = create_agent(
    model,
    tools=[search_records, send_notification, update_record],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                # True → all decisions allowed: approve / edit / reject / respond
                "update_record":      True,
                # InterruptOnConfig dict — restrict allowed decisions
                "send_notification":  {"allowed_decisions": ["approve", "reject"]},
                # False → always auto-execute, never interrupt
                "search_records":     False,
            },
            # description_prefix default is 'Tool execution requires approval'
            description_prefix="Review required before execution",
        )
    ],
    checkpointer=InMemorySaver(),
    system_prompt=SYSTEM_PROMPT,
    response_format=ExtractionResult,
)
```

**Invoke and handle the interrupt:**

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "session-abc-123"}}

# Run until interrupt or completion
result = agent.invoke(
    {"messages": [("human", user_input)]},
    config=config,
    version="v2",                         # v2 returns GraphOutput with .interrupts
)

if result.interrupts:
    action = result.interrupts[0].value["action_requests"][0]
    print(f"Pending approval: {action['name']}  args={action['arguments']}")

    # Approve — execute as proposed:
    agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )

    # Edit — modify args before execution:
    agent.invoke(
        Command(resume={"decisions": [{
            "type": "edit",
            "edited_action": {
                "name": "update_record",
                "args": {"record_id": "rec-001", "changes": {"status": "reviewed"}},
            },
        }]}),
        config=config,
        version="v2",
    )

    # Reject — skip execution and give feedback to the agent:
    agent.invoke(
        Command(resume={"decisions": [{
            "type": "reject",
            "message": "Do not update this record — the source data is still unverified.",
        }]}),
        config=config,
        version="v2",
    )
```

**Decision types:**

| Type | What happens | Typical use |
|---|---|---|
| `approve` | Tool executes as proposed | Standard sign-off |
| `edit` | Tool executes with modified args | Reviewer tweaks a value before it goes through |
| `reject` | Tool is skipped; feedback returned to agent as context | Agent made the wrong call |
| `respond` | Human reply returned directly as the tool result | "Ask user" clarification tools |

### Approach B — `interrupt()` primitive (workflow-level gate)

Use when the entire LangGraph thread should pause — not just a single tool call — and resume only after an external decision (e.g. a REST API callback from an approval service):

```python
from langgraph.types import interrupt
from langchain_core.runnables import RunnableConfig

async def extraction_node(state: WorkflowState, config: RunnableConfig) -> dict:
    result = await agent.ainvoke(
        {"messages": [("human", build_input(state))]},
        config=config,
    )
    output: ExtractionResult = result["structured_response"]

    # Apply results to shared state
    state["extraction_result"] = output

    # ── Suspend the whole thread until an external party confirms ─────────────
    # The graph checkpoints here. Resume by calling graph.invoke(Command(resume=...))
    # with the same thread_id from the approval callback.
    if output.extraction_notes:
        interrupt({
            "reason": "extraction_flagged_for_review",
            "thread_id": config["configurable"]["thread_id"],
            "notes": output.extraction_notes,
        })
    # ── Execution continues here once the thread is resumed ───────────────────

    return {"extraction_result": output, "stage": "validation"}
```

**Resume the thread (e.g. from an approval service callback):**

```python
from langgraph.types import Command

graph.invoke(
    Command(resume={"approved": True, "reviewer": "user@example.com"}),
    config={"configurable": {"thread_id": "session-abc-123"}},
)
```

**When to use each approach:**

| Scenario | Approach |
|---|---|
| Pause before a specific tool executes | `HumanInTheLoopMiddleware` |
| Pause the whole thread after agent output is applied | `interrupt()` primitive |
| Resume via external REST callback / approval service | `interrupt()` primitive |
| Auto-approve safe tools, review only risky ones | `HumanInTheLoopMiddleware` with `interrupt_on` map |

---

## 7. Memory and Custom State

Custom state extends the default `messages` list with domain-specific fields that tools and middleware can read and write throughout the agent loop.

### Adding custom fields via `state_schema`

```python
from langchain.agents import AgentState, create_agent
from typing import TypedDict

class MyAgentState(AgentState):
    document_id: str
    extraction_complete: bool

agent = create_agent(
    model,
    tools,
    state_schema=MyAgentState,
    system_prompt=SYSTEM_PROMPT,
    response_format=ExtractionResult,
)

result = agent.invoke({
    "messages": [("human", document_text)],
    "document_id": "doc-xyz-001",
    "extraction_complete": False,
})
```

> Custom state schemas **must be `TypedDict`** — Pydantic models and dataclasses are not supported as of `langchain 1.0`.

Define state via **middleware** when the custom fields are tightly coupled to a specific middleware hook — this keeps state extensions scoped to the relevant middleware rather than leaking into the global agent state.

### Runtime context via `context_schema`

Read-only data injected per invocation — good for user identity, feature flags, or locale without polluting the persistent state:

```python
from dataclasses import dataclass

@dataclass
class RequestContext:
    user_id: str
    user_role: str    # "admin" | "reviewer" | "viewer"
    locale: str

agent = create_agent(model, tools, context_schema=RequestContext)

result = agent.invoke(
    {"messages": [("human", user_input)]},
    context=RequestContext(user_id="u-001", user_role="reviewer", locale="en-US"),
)
```

Inside middleware, access via `request.runtime.context`:

```python
@wrap_model_call
def role_based_tools(request: ModelRequest, handler) -> ModelResponse:
    role = request.runtime.context.user_role if request.runtime else "viewer"
    if role != "admin":
        tools = [t for t in request.tools if not t.name.startswith("delete_")]
        request = request.override(tools=tools)
    return handler(request)
```

---

## 8. Checkpointing

A checkpointer persists graph state between invocations. Required for HITL and for long-running workflows that span multiple turns or wait for external events.

```python
# Development / testing
from langgraph.checkpoint.memory import InMemorySaver
agent = create_agent(model, tools, checkpointer=InMemorySaver())

# Production — persistent PostgreSQL checkpointer
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
    agent = create_agent(model, tools, checkpointer=checkpointer)
```

Always supply a `thread_id` in `config` when a checkpointer is active:

```python
config = {"configurable": {"thread_id": "unique-session-id"}}
result = await agent.ainvoke({"messages": [("human", user_input)]}, config=config)
```

---

## 9. Streaming

Stream intermediate steps and token chunks in real time:

```python
async for chunk in agent.astream(
    {"messages": [("human", user_input)]},
    config=config,
    stream_mode=["updates", "messages"],
    version="v2",
):
    if chunk["type"] == "messages":
        token, _ = chunk["data"]
        if token.content:
            print(token.content, end="", flush=True)   # stream token to UI
    elif chunk["type"] == "updates":
        if "__interrupt__" in chunk["data"]:
            print(f"\n[interrupt] {chunk['data']['__interrupt__']}")
```

Resume with streaming after a human decision:

```python
from langgraph.types import Command

async for chunk in agent.astream(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config,
    stream_mode=["updates", "messages"],
    version="v2",
):
    ...
```

---

## 10. Using as a LangGraph Subgraph Node

The compiled agent graph can be embedded directly as a node inside a parent `StateGraph`. Use the `name` parameter to set the node identifier:

```python
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START
from typing import TypedDict

class PipelineState(TypedDict):
    input_text: str
    extraction_result: ExtractionResult | None
    stage: str

# Compile the agent
extraction_agent = create_agent(
    model,
    tools,
    system_prompt=SYSTEM_PROMPT,
    response_format=ExtractionResult,
    name="extraction_agent",             # becomes the node name in the parent graph
)

# Wrap it in a node function to map PipelineState ↔ AgentState
async def extraction_node(state: PipelineState, config) -> dict:
    result = await extraction_agent.ainvoke(
        {"messages": [("human", state["input_text"])]},
        config=config,
    )
    return {
        "extraction_result": result["structured_response"],
        "stage": "validation",
    }

# Wire into the parent graph
pipeline = (
    StateGraph(PipelineState)
    .add_node("extract", extraction_node)
    .add_node("validate", validation_node)
    .add_edge(START, "extract")
    .add_edge("extract", "validate")
    .compile()
)
```

---

## 11. Error Handling Pattern

Wrap the `ainvoke` call in try/except. On failure return a valid empty typed response and accumulate the error — never raise from a LangGraph node, as an uncaught exception terminates the entire thread.

```python
import time
import logging
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)
AGENT_NAME = "extraction_agent"

async def extraction_node(state: PipelineState, config: RunnableConfig) -> dict:
    started_at = time.monotonic()

    try:
        result = await agent.ainvoke(
            {"messages": [("human", state["input_text"])]},
            config=config,
        )
        output: ExtractionResult = result["structured_response"]
        elapsed_ms = (time.monotonic() - started_at) * 1000
        logger.info("agent_completed", extra={"agent": AGENT_NAME, "elapsed_ms": elapsed_ms})
        return {"extraction_result": output, "stage": "validation"}

    except Exception as exc:
        elapsed_ms = (time.monotonic() - started_at) * 1000
        logger.exception("agent_failed", extra={"agent": AGENT_NAME, "elapsed_ms": elapsed_ms, "error": str(exc)})
        # Return a valid empty result so downstream nodes can still run.
        # Accumulate errors for later reporting / exception handling.
        return {
            "extraction_result": ExtractionResult(),
            "stage": "validation",
            "errors": (state.get("errors") or []) + [f"{AGENT_NAME}: {exc}"],
        }
```

---

## 12. New Agent Checklist

```
[ ] 1.  mkdir src/agents/<name>/
[ ] 2.  <name>/__init__.py    — docstring describing the agent; re-export the
                                 entry point ONLY:  from agents.<name>.agent import <entry>
                                 plus __all__
[ ] 3.  <name>/prompts.py     — SYSTEM_PROMPT constant
[ ] 4.  <name>/constants.py   — AGENT_NAME and any thresholds. IMPORTS NOTHING.
[ ] 5.  <name>/tools.py       — `tools = [...]`, composed from
                                 harness/utils/lc_tools.py; add new @tool
                                 implementations THERE, not here
[ ] 6.  models/<name>.py      — <Name>Result(BaseModel) for structured output
[ ] 7.  <name>/agent.py       — logger = structlog.get_logger(__name__)
                                 agent = create_agent(model, tools,
                                     system_prompt=..., response_format=<Model>)
[ ] 8.  <name>/agent.py       — async def <entry>(state, config) -> dict
        ├── Guard / skip conditions at the top
        ├── Build the input string (put the builder in <name>/input_builder.py
        │   if it is more than ~30 lines)
        ├── result = await agent.ainvoke({...}, config=config)
        ├── typed_output = result["structured_response"]
        ├── try/except with graceful empty fallback — never raise from a node
        └── return partial state dict
[ ] 9.  Private helpers       — one module per concern (extractors.py,
                                 persistence.py, …), each with its own logger
[ ] 10. Register the node in the parent StateGraph (workflow/flows/)
[ ] 11. Add conditional routing if needed
[ ] 12. Add checkpointer if HITL is required
[ ] 13. Check the import graph: no helper may import from agent.py if agent.py
        imports it. Run `pytest tests/harness/test_import_graph.py` — it fails
        on self-imports and cycles.
```

**Layout rules that the import-graph test enforces:**

- No module imports itself.
- No module-level import cycles anywhere in `src/`.
- Anything two modules in the package both need goes in `constants.py`
  (which imports nothing) — not in `agent.py`.

---

## Quick-Reference: `create_agent` Parameters

| Parameter | Type | Default | When to use |
|---|---|---|---|
| `model` | `str \| BaseChatModel` | — | Always. Use `temperature=0` for deterministic extraction agents |
| `tools` | `list` | `None` | Whenever the agent needs to call external systems |
| `system_prompt` | `str \| SystemMessage` | `None` | Always. Store in a dedicated prompts module |
| `response_format` | `type[BaseModel]` | `None` | Whenever typed structured output is needed. Access via `result["structured_response"]` |
| `middleware` | `list[AgentMiddleware]` | `()` | Logging, HITL, dynamic model/tools selection, guardrails |
| `checkpointer` | `Checkpointer` | `None` | Required with `HumanInTheLoopMiddleware` or multi-turn threads. Use `AsyncPostgresSaver` in production |
| `state_schema` | `TypedDict` subclass | `None` | Custom state fields beyond `messages` |
| `context_schema` | `dataclass` | `None` | Per-invocation read-only context (user role, locale, feature flags) |
| `interrupt_before` | `list[str]` | `None` | Pause before a named graph node |
| `interrupt_after` | `list[str]` | `None` | Pause after a named graph node |
| `name` | `str` | `None` | Required when embedding as a subgraph node. Use `snake_case` |
| `debug` | `bool` | `False` | Print every node transition during development |
| `store` | `BaseStore` | `None` | Long-term cross-thread memory (e.g. user preferences across sessions) |
| `cache` | `BaseCache` | `None` | Cache LLM responses for load testing or deterministic replay |

---

## Reference Links

- [create_agent API reference](https://reference.langchain.com/python/langchain/agents/factory/create_agent)
- [Agents docs](https://docs.langchain.com/oss/python/langchain/agents)
- [Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware/overview)
- [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangGraph interrupt primitive](https://reference.langchain.com/python/langgraph/types/interrupt)
- [AsyncPostgresSaver](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver)
</langchain-agent-builder>
