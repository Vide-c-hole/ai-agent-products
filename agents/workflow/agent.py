"""Workflow Agent - Multi-step task automation.

Price: $149
Target: Productivity users, teams, automation enthusiasts

Features:
- YAML workflow definitions
- Step chaining with context passing
- Conditional execution
- Error handling and retries
- Output aggregation
"""
import argparse
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

from core import BaseAgent, AgentConfig


class WorkflowAgent(BaseAgent):
    """Agent that executes multi-step workflows defined in YAML."""
    
    @property
    def system_prompt(self) -> str:
        return """You are an intelligent workflow executor. Your job is to:
1. Execute tasks step by step
2. Pass context between steps
3. Make decisions based on conditions
4. Handle errors gracefully
5. Aggregate and format outputs

Follow instructions precisely. Use context from previous steps.
Format outputs clearly and concisely."""
    
    def run(
        self,
        workflow: str | Path | dict,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow: Path to YAML file, YAML string, or workflow dict
            variables: Variables to inject into workflow
        
        Returns:
            Workflow execution results
        """
        # Load workflow
        wf = self._load_workflow(workflow)
        if not wf:
            return {"error": "Failed to load workflow"}
        
        self.logger.info(f"Running workflow: {wf.get('name', 'unnamed')}")
        
        # Initialize context
        context = {
            "variables": variables or {},
            "steps": {},
            "outputs": [],
        }
        
        # Execute steps
        steps = wf.get("steps", [])
        for i, step in enumerate(steps):
            step_name = step.get("name", f"step_{i}")
            self.logger.info(f"Executing: {step_name}")
            
            # Check condition
            if not self._check_condition(step, context):
                self.logger.info(f"Skipping {step_name}: condition not met")
                continue
            
            # Execute step
            try:
                result = self._execute_step(step, context)
                context["steps"][step_name] = {
                    "status": "success",
                    "output": result
                }
                context["outputs"].append(result)
            except Exception as e:
                self.logger.error(f"Step {step_name} failed: {e}")
                context["steps"][step_name] = {
                    "status": "error",
                    "error": str(e)
                }
                if step.get("on_error") == "stop":
                    break
        
        # Generate summary
        summary = self._create_summary(wf, context)
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wf_name = wf.get("name", "workflow").replace(" ", "_")
        filename = f"workflow_{wf_name}_{timestamp}.md"
        self.save_output(summary, filename)
        
        return {
            "name": wf.get("name"),
            "steps_executed": len([s for s in context["steps"].values() if s["status"] == "success"]),
            "steps_failed": len([s for s in context["steps"].values() if s["status"] == "error"]),
            "summary": summary,
            "context": context,
        }
    
    def _load_workflow(self, workflow: str | Path | dict) -> dict | None:
        """Load workflow from various sources."""
        if isinstance(workflow, dict):
            return workflow
        
        if isinstance(workflow, Path) or (isinstance(workflow, str) and Path(workflow).exists()):
            path = Path(workflow)
            with open(path) as f:
                return yaml.safe_load(f)
        
        if isinstance(workflow, str):
            try:
                return yaml.safe_load(workflow)
            except:
                return None
        
        return None
    
    def _check_condition(self, step: dict, context: dict) -> bool:
        """Check if step condition is met."""
        condition = step.get("condition")
        if not condition:
            return True
        
        # Simple condition evaluation
        prompt = f"""Evaluate this condition and return ONLY 'true' or 'false':

Condition: {condition}

Context:
- Variables: {context['variables']}
- Previous step results: {list(context['steps'].keys())}

Return only 'true' or 'false', nothing else."""
        
        result = self.ask(prompt).strip().lower()
        return result == "true"
    
    def _execute_step(self, step: dict, context: dict) -> str:
        """Execute a single workflow step."""
        step_type = step.get("type", "prompt")
        
        if step_type == "prompt":
            return self._execute_prompt(step, context)
        elif step_type == "transform":
            return self._execute_transform(step, context)
        elif step_type == "aggregate":
            return self._execute_aggregate(step, context)
        else:
            raise ValueError(f"Unknown step type: {step_type}")
    
    def _execute_prompt(self, step: dict, context: dict) -> str:
        """Execute a prompt step."""
        prompt_template = step.get("prompt", "")
        
        # Inject context
        prompt = self._inject_context(prompt_template, context)
        
        # Get custom system prompt if specified
        system = step.get("system")
        if system:
            # Temporarily override system prompt
            original_system = self.system_prompt
            result = self.ask(prompt, system=system)
        else:
            result = self.ask(prompt)
        
        return result
    
    def _execute_transform(self, step: dict, context: dict) -> str:
        """Transform previous output."""
        transform = step.get("transform", "")
        input_step = step.get("input")
        
        if input_step and input_step in context["steps"]:
            input_data = context["steps"][input_step].get("output", "")
        else:
            input_data = context["outputs"][-1] if context["outputs"] else ""
        
        prompt = f"""Transform this data:

Input:
{input_data}

Transformation: {transform}

Apply the transformation and return the result."""
        
        return self.ask(prompt)
    
    def _execute_aggregate(self, step: dict, context: dict) -> str:
        """Aggregate multiple outputs."""
        inputs = step.get("inputs", [])
        format_spec = step.get("format", "bullet_points")
        
        # Collect inputs
        data = []
        for inp in inputs:
            if inp in context["steps"]:
                data.append(f"## {inp}\n{context['steps'][inp].get('output', '')}")
        
        if not data:
            data = [f"## Output {i+1}\n{out}" for i, out in enumerate(context["outputs"])]
        
        prompt = f"""Aggregate and format these outputs:

{chr(10).join(data)}

Format: {format_spec}

Create a cohesive summary that combines all the information."""
        
        return self.ask(prompt)
    
    def _inject_context(self, template: str, context: dict) -> str:
        """Inject context variables into template."""
        result = template
        
        # Inject variables
        for key, value in context["variables"].items():
            result = result.replace(f"{{{{variables.{key}}}}}", str(value))
            result = result.replace(f"${{{key}}}", str(value))
        
        # Inject previous outputs
        for step_name, step_data in context["steps"].items():
            if step_data["status"] == "success":
                result = result.replace(f"{{{{steps.{step_name}}}}}", step_data["output"])
        
        # Inject last output
        if context["outputs"]:
            result = result.replace("{{last_output}}", context["outputs"][-1])
        
        return result
    
    def _create_summary(self, workflow: dict, context: dict) -> str:
        """Create workflow execution summary."""
        steps_summary = []
        for name, data in context["steps"].items():
            status = "✓" if data["status"] == "success" else "✗"
            steps_summary.append(f"- {status} {name}")
        
        return f"""# Workflow Execution Report

**Workflow**: {workflow.get('name', 'Unnamed')}
**Description**: {workflow.get('description', 'N/A')}
**Executed**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Execution Summary

{chr(10).join(steps_summary)}

## Outputs

{"---".join([f"### {name}{chr(10)}{data.get('output', 'No output')[:500]}" for name, data in context["steps"].items() if data["status"] == "success"])}
"""


# Example workflow templates
EXAMPLE_WORKFLOWS = {
    "content_pipeline": """
name: Content Pipeline
description: Research topic and create content

steps:
  - name: research
    type: prompt
    prompt: |
      Research the following topic thoroughly:
      {{variables.topic}}
      
      Provide key findings, trends, and insights.

  - name: outline
    type: prompt
    prompt: |
      Based on this research:
      {{steps.research}}
      
      Create a detailed outline for a blog post about {{variables.topic}}.

  - name: draft
    type: prompt
    prompt: |
      Using this outline:
      {{steps.outline}}
      
      Write a complete blog post. Make it engaging and informative.
      Target audience: {{variables.audience}}

  - name: social
    type: prompt
    prompt: |
      Based on this blog post:
      {{steps.draft}}
      
      Create 3 LinkedIn posts promoting the key insights.
""",
    
    "code_documentation": """
name: Code Documentation
description: Analyze code and generate documentation

steps:
  - name: analyze
    type: prompt
    prompt: |
      Analyze this codebase structure:
      {{variables.code_path}}
      
      Identify main components, patterns, and architecture.

  - name: api_docs
    type: prompt
    prompt: |
      Based on this analysis:
      {{steps.analyze}}
      
      Generate API documentation for the public interfaces.

  - name: readme
    type: prompt
    prompt: |
      Create a comprehensive README.md including:
      {{steps.analyze}}
      
      Include: Overview, Installation, Usage, API Reference, Contributing.
""",
}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Workflow Agent")
    parser.add_argument("--workflow", "-w", required=True, help="Workflow YAML file or template name")
    parser.add_argument("--var", "-v", action="append", nargs=2, metavar=("KEY", "VALUE"),
                       help="Variables (can be used multiple times)")
    parser.add_argument("--output", "-o", default="output")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--list-templates", action="store_true", help="List example templates")
    parser.add_argument("--provider", choices=["groq", "anthropic", "openai"], default="groq")
    
    args = parser.parse_args()
    
    if args.list_templates:
        print("Available templates:")
        for name in EXAMPLE_WORKFLOWS:
            print(f"  - {name}")
        return
    
    # Load workflow
    if args.workflow in EXAMPLE_WORKFLOWS:
        workflow = EXAMPLE_WORKFLOWS[args.workflow]
    else:
        workflow = args.workflow
    
    # Parse variables
    variables = {}
    if args.var:
        for key, value in args.var:
            variables[key] = value
    
    config = AgentConfig(
        provider=args.provider,
        output_dir=args.output,
        verbose=args.verbose,
    )
    
    agent = WorkflowAgent(config)
    result = agent.run(workflow=workflow, variables=variables)
    
    print(f"\nWorkflow completed:")
    print(f"  Steps executed: {result['steps_executed']}")
    print(f"  Steps failed: {result['steps_failed']}")
    print(f"\n{result['summary']}")


if __name__ == "__main__":
    main()
