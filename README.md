# Predictous

This is an open-source and free project, that aims to deliver a fully functional
forecasting system build on Bittensor Sunbet 6: Numinous.

The main modules:
1. Agent Collector - integrates with the Numinous API
2. Agent Runner (Sandbox) - safe environment to run agents locally
3. Predictor - orchestrates agent fetching and execution

## Agent Collector

Fetches agent code from Numinous API with caching.

### Usage

```python
from agent_collector import AgentCollector

collector = AgentCollector()

# By rank (0-indexed)
uid, hotkey = collector.get_miner_by_rank(0)

# Get agent (tries newest first, falls back on 4XX)
result = collector.get_agent(uid, hotkey)
if result:
    version_id, code = result
```

### Caching

| Data | TTL | Storage |
|------|-----|---------|
| Leaderboard | Until 11 PM UTC | Memory |
| Agent list | Until 11 PM UTC | Memory |
| Agent code (success) | Forever | `./agents/{version_id}.py` |
| Agent code (4XX) | Until 11 PM UTC | Memory |

---

## Agent Runner (Sandbox)

Runs numinous-compatible agents in isolated Docker containers with cost tracking.

### Usage

```python
from sandbox import SandboxManager

with SandboxManager(gateway_url="http://localhost:8000") as manager:
    result = manager.run_agent(
        agent_code=open("my_agent.py").read(),
        event_data={"event_id": "123", "title": "Will X happen?"},
    )
    print(f"Prediction: {result.output['prediction']}, Cost: ${result.cost:.4f}")
```

### Agent Interface

Agents must define `agent_main(event_data: dict) -> dict`:

```python
def agent_main(event_data):
    return {
        "event_id": event_data["event_id"],
        "prediction": 0.75,  # 0.0 to 1.0
        "reasoning": "optional explanation",
    }
```

### Resource Limits

| Resource | Limit |
|----------|-------|
| Memory | 768 MB |
| CPU | 0.5 cores |
| Timeout | 120s (configurable) |
| Chutes budget | $0.02 (configurable) |
| Desearch budget | $0.10 (configurable) |

### Configuration

```python
SandboxManager(
    gateway_url="http://localhost:8000",  # gateway API
    chutes_budget=0.02,                   # LLM cost limit per run
    desearch_budget=0.10,                 # search/crawl cost limit per run
    proxy_port=8888,                      # cost-tracking proxy port
)
```

### Result

```python
result.status      # "success" or "error"
result.output      # {"event_id", "prediction", "reasoning"}
result.cost        # total cost in USD
result.error       # error message if failed
result.error_type  # TIMEOUT | CONTAINER_ERROR | INVALID_OUTPUT | AGENT_ERROR | BUDGET_EXCEEDED
result.logs        # container stdout
```

---

## Predictor

Orchestrates agent fetching and execution to produce predictions. Three modes available.

### Usage

```python
from predictor import Predictor, PredictionRequest
from agent_collector import AgentCollector
from sandbox import SandboxManager

collector = AgentCollector()
with SandboxManager(gateway_url="http://localhost:8000") as manager:
    predictor = Predictor(collector, manager)

    request = PredictionRequest(
        question="Will X happen?",
        resolution_criteria="X is true if...",
        resolution_date="2026-01-31",  # optional
        categories=["topic1"],          # optional
    )

    # Champion mode: top agent only
    result = predictor.predict_champion(request)

    # Council mode: top 3 agents, averaged (runs in parallel)
    result = predictor.predict_council(request)

    # Selected mode: specific miner by UID
    result = predictor.predict_selected(request, miner_uid=123)
```

### Modes

| Mode | Agents | Aggregation | Failure Threshold |
|------|--------|-------------|-------------------|
| Champion | Top 1 | None | Must succeed |
| Council | Top 3 | Average | At least 2 must succeed |
| Selected | By UID | None | Must succeed |

### Result

```python
result.status             # "success" or "error"
result.prediction         # aggregated prediction (0.0-1.0)
result.agent_predictions  # list of AgentPrediction
result.failures           # list of AgentFailure
result.total_cost         # total cost in USD
result.error              # error message if failed
```
