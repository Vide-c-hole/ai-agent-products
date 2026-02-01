"""Example: Run the Research Agent."""
import sys
sys.path.insert(0, "..")

from agents.research import ResearchAgent
from core import AgentConfig

# Configure
config = AgentConfig(
    provider="anthropic",
    verbose=True,
    output_dir="output",
)

# Run
agent = ResearchAgent(config)
report = agent.run(
    topic="AI Agents in Production: Best Practices 2026",
    depth="standard",
    focus_areas=["architecture", "deployment", "monitoring"],
)

print(report)
