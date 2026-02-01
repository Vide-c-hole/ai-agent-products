"""Research Agent - Automated research and report generation.

Price: $49
Target: Content creators, analysts, researchers

Features:
- Multi-source research compilation
- Structured report generation
- Source citation
- Key findings extraction
- Export to Markdown/PDF
"""
import argparse
from datetime import datetime
from pathlib import Path

from core import BaseAgent, AgentConfig


class ResearchAgent(BaseAgent):
    """Agent that conducts research and generates comprehensive reports."""
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert research analyst. Your job is to:
1. Thoroughly analyze the given topic
2. Identify key themes, trends, and insights
3. Structure findings into a clear, actionable report
4. Cite sources and provide evidence for claims
5. Highlight implications and recommendations

Be thorough but concise. Focus on actionable insights over generic observations.
Use markdown formatting for structure."""
    
    def run(
        self,
        topic: str,
        depth: str = "standard",  # quick, standard, deep
        focus_areas: list[str] | None = None,
        output_format: str = "markdown",
    ) -> str:
        """
        Conduct research on a topic and generate a report.
        
        Args:
            topic: Research topic
            depth: Research depth (quick=1 pass, standard=2 passes, deep=3 passes)
            focus_areas: Specific areas to focus on
            output_format: Output format (markdown, json)
        
        Returns:
            Research report as string
        """
        self.logger.info(f"Researching: {topic}")
        
        # Phase 1: Initial research outline
        outline = self._create_outline(topic, focus_areas)
        
        # Phase 2: Deep dive on each section
        sections = self._research_sections(topic, outline, depth)
        
        # Phase 3: Synthesize findings
        report = self._synthesize_report(topic, sections)
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:50]
        filename = f"research_{safe_topic}_{timestamp}.md"
        self.save_output(report, filename)
        
        return report
    
    def _create_outline(self, topic: str, focus_areas: list[str] | None) -> str:
        """Create research outline."""
        focus = f"\nFocus areas: {', '.join(focus_areas)}" if focus_areas else ""
        
        prompt = f"""Create a research outline for: {topic}{focus}

Return a structured outline with 4-6 main sections. For each section include:
- Section title
- Key questions to answer
- Types of information needed

Format as markdown with ## headers."""
        
        return self.ask(prompt)
    
    def _research_sections(self, topic: str, outline: str, depth: str) -> list[str]:
        """Research each section of the outline."""
        iterations = {"quick": 1, "standard": 2, "deep": 3}.get(depth, 2)
        
        sections = []
        for i in range(iterations):
            self.logger.info(f"Research pass {i + 1}/{iterations}")
            
            prompt = f"""Topic: {topic}

Outline:
{outline}

{"Previous findings:" + chr(10) + chr(10).join(sections) if sections else ""}

Provide detailed research findings for each section in the outline.
Include:
- Key facts and data
- Current trends
- Expert perspectives
- Potential challenges
- Opportunities

Be specific and evidence-based. Use markdown formatting."""
            
            section = self.ask(prompt)
            sections.append(section)
        
        return sections
    
    def _synthesize_report(self, topic: str, sections: list[str]) -> str:
        """Synthesize all findings into final report."""
        all_research = "\n\n---\n\n".join(sections)
        
        prompt = f"""Synthesize the following research into a comprehensive report on: {topic}

Research findings:
{all_research}

Create a final report with:
1. Executive Summary (key takeaways in 3-5 bullets)
2. Main Findings (organized by theme)
3. Analysis & Implications
4. Recommendations
5. Appendix (data points, sources mentioned)

Make it actionable and well-structured. Use markdown formatting."""
        
        return self.ask(prompt)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Research Agent - Automated research reports")
    parser.add_argument("--topic", "-t", required=True, help="Research topic")
    parser.add_argument("--depth", "-d", choices=["quick", "standard", "deep"], default="standard")
    parser.add_argument("--focus", "-f", nargs="+", help="Focus areas")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--provider", "-p", choices=["groq", "anthropic", "openai"], default="groq")
    
    args = parser.parse_args()
    
    config = AgentConfig(
        provider=args.provider,
        output_dir=args.output,
        verbose=args.verbose,
    )
    
    agent = ResearchAgent(config)
    report = agent.run(
        topic=args.topic,
        depth=args.depth,
        focus_areas=args.focus,
    )
    
    print(f"\n{'='*60}\nRESEARCH REPORT\n{'='*60}\n")
    print(report)


if __name__ == "__main__":
    main()
