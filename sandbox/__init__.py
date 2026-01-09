"""
Sandbox module for running Python agents in isolated Docker containers.

Features:
- Docker-based isolation with resource limits
- Cost tracking with split budgets (chutes/LLM and desearch)
- Compatible with numinous subnet agents

Usage:
    from sandbox import SandboxManager

    with SandboxManager(
        gateway_url="http://localhost:8000",
        chutes_budget=0.02,  # $0.02 for LLM calls
        desearch_budget=0.10,  # $0.10 for search/crawl
    ) as manager:
        result = manager.run_agent(
            agent_code=open("my_agent.py").read(),
            event_data={"event_id": "123", "title": "Will X happen?"},
            timeout=120,
        )
        print(f"Prediction: {result.output['prediction']}, Cost: ${result.cost:.4f}")
"""

from sandbox.manager import SandboxManager
from sandbox.models import SandboxResult, SandboxErrorType

__all__ = ["SandboxManager", "SandboxResult", "SandboxErrorType"]
