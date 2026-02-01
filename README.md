# AI Agent Products

Production-ready AI agents for automation and productivity.

## Products

| Agent | Use Case | Price |
|-------|----------|-------|
| **Research Agent** | Automated research & report generation | $49 |
| **Code Review Agent** | PR reviews, code quality analysis | $79 |
| **Data Analysis Agent** | Dataset insights, trend detection | $99 |
| **Workflow Agent** | Multi-step task automation | $149 |
| **Full Suite** | All 4 agents + updates | $299 |

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run any agent
python -m agents.research.agent --topic "AI trends 2026"
python -m agents.code_review.agent --repo ./my-project
python -m agents.data_analysis.agent --file data.csv
python -m agents.workflow.agent --config workflow.yaml
```

## Why These Agents?

- **Production-ready** - Error handling, rate limiting, retries
- **Configurable** - YAML configs, CLI args, environment variables
- **Extensible** - Clean base class, easy to customize
- **Cost-efficient** - Smart caching, token optimization

## Architecture

```
ai-agents/
├── core/               # Shared agent framework
│   ├── base.py         # Base agent class
│   ├── llm.py          # LLM provider abstraction
│   ├── tools.py        # Common tools (web, file, etc.)
│   └── config.py       # Configuration management
├── agents/
│   ├── research/       # Research Agent
│   ├── code_review/    # Code Review Agent
│   ├── data_analysis/  # Data Analysis Agent
│   └── workflow/       # Workflow Agent
└── examples/           # Usage examples
```

## License

Personal/Commercial use included. No resale of agents.
