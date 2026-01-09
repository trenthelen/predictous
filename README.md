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
