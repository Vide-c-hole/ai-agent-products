"""Code Review Agent - Automated code review and quality analysis.

Price: $79
Target: Dev teams, solo developers, code reviewers

Features:
- Code quality analysis
- Security vulnerability detection
- Performance suggestions
- Best practices recommendations
- PR-ready feedback
"""
import argparse
from pathlib import Path
from datetime import datetime

from core import BaseAgent, AgentConfig


class CodeReviewAgent(BaseAgent):
    """Agent that reviews code for quality, security, and best practices."""
    
    SUPPORTED_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", 
        ".java", ".cpp", ".c", ".rb", ".php", ".swift", ".kt"
    }
    
    @property
    def system_prompt(self) -> str:
        return """You are a senior software engineer conducting code reviews.

Your review should cover:
1. **Code Quality**: Readability, maintainability, DRY principles
2. **Security**: Vulnerabilities, injection risks, auth issues
3. **Performance**: Efficiency, memory usage, algorithmic complexity
4. **Best Practices**: Language idioms, design patterns, testing
5. **Bugs**: Logic errors, edge cases, race conditions

Be constructive and specific. For each issue:
- Explain WHY it's a problem
- Show HOW to fix it
- Rate severity: 🔴 Critical, 🟡 Warning, 🔵 Suggestion

Format output as markdown with clear sections."""
    
    def run(
        self,
        path: str | Path,
        focus: str = "all",  # all, security, performance, quality
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> str:
        """
        Review code in a directory or file.
        
        Args:
            path: Path to file or directory
            focus: Review focus area
            include_patterns: Glob patterns to include
            exclude_patterns: Glob patterns to exclude
        
        Returns:
            Code review report
        """
        path = Path(path)
        
        if path.is_file():
            files = [path]
        else:
            files = self._collect_files(path, include_patterns, exclude_patterns)
        
        self.logger.info(f"Reviewing {len(files)} files")
        
        # Review each file
        reviews = []
        for file in files[:20]:  # Limit to 20 files per run
            review = self._review_file(file, focus)
            reviews.append((file, review))
        
        # Synthesize overall report
        report = self._create_summary(reviews, focus)
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"code_review_{timestamp}.md"
        self.save_output(report, filename)
        
        return report
    
    def _collect_files(
        self,
        directory: Path,
        include: list[str] | None,
        exclude: list[str] | None,
    ) -> list[Path]:
        """Collect code files from directory."""
        files = []
        
        exclude = exclude or ["node_modules", "venv", ".git", "__pycache__", "dist", "build"]
        
        for file in directory.rglob("*"):
            if not file.is_file():
                continue
            if file.suffix not in self.SUPPORTED_EXTENSIONS:
                continue
            if any(ex in str(file) for ex in exclude):
                continue
            if include and not any(file.match(inc) for inc in include):
                continue
            files.append(file)
        
        return sorted(files)
    
    def _review_file(self, file: Path, focus: str) -> str:
        """Review a single file."""
        self.logger.info(f"Reviewing: {file.name}")
        
        try:
            content = file.read_text()
        except Exception as e:
            return f"Error reading file: {e}"
        
        # Skip very large files
        if len(content) > 50000:
            return "File too large for review (>50KB)"
        
        # Skip empty files
        if not content.strip():
            return "Empty file"
        
        focus_instruction = {
            "all": "Review all aspects: quality, security, performance, best practices",
            "security": "Focus primarily on security vulnerabilities and risks",
            "performance": "Focus primarily on performance and efficiency",
            "quality": "Focus primarily on code quality and maintainability",
        }.get(focus, "Review all aspects")
        
        prompt = f"""Review this code file: {file.name}

{focus_instruction}

```{file.suffix[1:]}
{content}
```

Provide a structured review with:
1. Summary (1-2 sentences)
2. Issues found (with severity ratings)
3. Specific improvement suggestions with code examples
4. What's done well (positive feedback)"""
        
        return self.ask(prompt)
    
    def _create_summary(self, reviews: list[tuple[Path, str]], focus: str) -> str:
        """Create overall review summary."""
        review_text = "\n\n".join([
            f"### {file.name}\n{review}" 
            for file, review in reviews
        ])
        
        prompt = f"""Create an executive summary of this code review.

Individual file reviews:
{review_text}

Create a summary with:
1. **Overview**: Overall code health assessment
2. **Critical Issues**: Must-fix problems (🔴)
3. **Warnings**: Should-fix problems (🟡)
4. **Suggestions**: Nice-to-have improvements (🔵)
5. **Statistics**: Issue counts by severity
6. **Priority Actions**: Top 5 things to fix first

Be concise but actionable."""
        
        summary = self.ask(prompt)
        
        # Combine summary with individual reviews
        return f"""# Code Review Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Focus: {focus}
Files reviewed: {len(reviews)}

---

{summary}

---

# Individual File Reviews

{review_text}
"""


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Code Review Agent")
    parser.add_argument("--path", "-p", required=True, help="Path to review")
    parser.add_argument("--focus", "-f", choices=["all", "security", "performance", "quality"], default="all")
    parser.add_argument("--include", "-i", nargs="+", help="Include patterns")
    parser.add_argument("--exclude", "-e", nargs="+", help="Exclude patterns")
    parser.add_argument("--output", "-o", default="output")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--provider", choices=["groq", "anthropic", "openai"], default="groq")
    
    args = parser.parse_args()
    
    config = AgentConfig(
        provider=args.provider,
        output_dir=args.output,
        verbose=args.verbose,
    )
    
    agent = CodeReviewAgent(config)
    report = agent.run(
        path=args.path,
        focus=args.focus,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
    )
    
    print(report)


if __name__ == "__main__":
    main()
