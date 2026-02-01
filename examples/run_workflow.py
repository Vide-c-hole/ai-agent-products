"""Example: Run the Workflow Agent with content pipeline."""
import sys
sys.path.insert(0, "..")

from agents.workflow import WorkflowAgent, EXAMPLE_WORKFLOWS
from core import AgentConfig

# Configure
config = AgentConfig(
    provider="anthropic",
    verbose=True,
    output_dir="output",
)

# Run content pipeline workflow
agent = WorkflowAgent(config)
result = agent.run(
    workflow=EXAMPLE_WORKFLOWS["content_pipeline"],
    variables={
        "topic": "Building AI Agents with Python",
        "audience": "Software developers learning AI",
    }
)

print(f"Steps executed: {result['steps_executed']}")
print(f"Steps failed: {result['steps_failed']}")
print(result["summary"])
