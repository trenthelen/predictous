"""
Sandbox module for running Python agents in isolated Docker containers.

Usage:
    from sandbox import SandboxManager

    with SandboxManager(gateway_url="http://host.docker.internal:8000") as manager:
        result = manager.run_agent(
            agent_code=open("my_agent.py").read(),
            event_data={"event_id": "123", "title": "Will X happen?"},
            timeout=120,
        )
        print(result)
"""

from sandbox.manager import SandboxManager
from sandbox.models import SandboxResult, SandboxErrorType

__all__ = ["SandboxManager", "SandboxResult", "SandboxErrorType"]
