"""Data Analysis Agent - Automated dataset analysis and insights.

Price: $99
Target: Business analysts, data teams, decision makers

Features:
- Automatic data profiling
- Statistical analysis
- Trend detection
- Anomaly identification
- Natural language insights
- Visualization suggestions
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core import BaseAgent, AgentConfig

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class DataAnalysisAgent(BaseAgent):
    """Agent that analyzes datasets and generates actionable insights."""
    
    @property
    def system_prompt(self) -> str:
        return """You are a senior data analyst. Your job is to:
1. Understand the data structure and quality
2. Identify patterns, trends, and anomalies
3. Provide actionable business insights
4. Suggest next steps for deeper analysis
5. Recommend visualizations

Be specific with numbers and examples. Focus on insights that drive decisions.
Format output as markdown with clear sections."""
    
    def run(
        self,
        file_path: str | Path,
        question: str | None = None,
        analysis_type: str = "comprehensive",  # quick, comprehensive, deep
    ) -> str:
        """
        Analyze a dataset and generate insights.
        
        Args:
            file_path: Path to CSV, JSON, or Parquet file
            question: Specific question to answer (optional)
            analysis_type: Type of analysis to perform
        
        Returns:
            Analysis report
        """
        if not HAS_PANDAS:
            return "Error: pandas required. Run: pip install pandas numpy"
        
        file_path = Path(file_path)
        self.logger.info(f"Analyzing: {file_path.name}")
        
        # Load data
        df = self._load_data(file_path)
        if df is None:
            return f"Error: Could not load {file_path}"
        
        # Generate data profile
        profile = self._profile_data(df)
        
        # Run analysis
        if question:
            analysis = self._answer_question(df, profile, question)
        else:
            analysis = self._comprehensive_analysis(df, profile, analysis_type)
        
        # Generate report
        report = self._create_report(file_path.name, profile, analysis)
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{file_path.stem}_{timestamp}.md"
        self.save_output(report, filename)
        
        return report
    
    def _load_data(self, path: Path) -> "pd.DataFrame | None":
        """Load data from file."""
        try:
            if path.suffix == ".csv":
                return pd.read_csv(path)
            elif path.suffix == ".json":
                return pd.read_json(path)
            elif path.suffix == ".parquet":
                return pd.read_parquet(path)
            elif path.suffix in [".xlsx", ".xls"]:
                return pd.read_excel(path)
            else:
                self.logger.error(f"Unsupported format: {path.suffix}")
                return None
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return None
    
    def _profile_data(self, df: "pd.DataFrame") -> dict[str, Any]:
        """Generate data profile."""
        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing": df.isnull().sum().to_dict(),
            "missing_pct": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        }
        
        # Numeric columns stats
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            profile["numeric_stats"] = df[numeric_cols].describe().to_dict()
        
        # Categorical columns
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(cat_cols) > 0:
            profile["categorical_stats"] = {
                col: {
                    "unique": df[col].nunique(),
                    "top_values": df[col].value_counts().head(5).to_dict()
                }
                for col in cat_cols[:10]  # Limit to 10 columns
            }
        
        # Date columns
        date_cols = df.select_dtypes(include=["datetime64"]).columns
        if len(date_cols) > 0:
            profile["date_range"] = {
                col: {"min": str(df[col].min()), "max": str(df[col].max())}
                for col in date_cols
            }
        
        # Sample data
        profile["sample"] = df.head(5).to_dict()
        
        return profile
    
    def _comprehensive_analysis(
        self,
        df: "pd.DataFrame",
        profile: dict[str, Any],
        analysis_type: str
    ) -> str:
        """Run comprehensive analysis."""
        profile_text = json.dumps(profile, indent=2, default=str)
        
        depth_instruction = {
            "quick": "Provide a quick overview with key insights only (3-5 main points)",
            "comprehensive": "Provide thorough analysis covering all aspects",
            "deep": "Provide exhaustive analysis with statistical tests and detailed patterns",
        }.get(analysis_type, "Provide thorough analysis")
        
        prompt = f"""Analyze this dataset:

Data Profile:
{profile_text}

{depth_instruction}

Cover these areas:
1. **Data Quality**: Missing values, outliers, data types
2. **Key Statistics**: Important metrics and distributions
3. **Patterns & Trends**: Correlations, time trends, groupings
4. **Anomalies**: Unusual values or patterns
5. **Business Insights**: Actionable findings
6. **Recommendations**: What to investigate further
7. **Visualization Suggestions**: Best charts for this data

Be specific with numbers. Reference actual column names and values."""
        
        return self.ask(prompt)
    
    def _answer_question(
        self,
        df: "pd.DataFrame",
        profile: dict[str, Any],
        question: str
    ) -> str:
        """Answer a specific question about the data."""
        profile_text = json.dumps(profile, indent=2, default=str)
        
        prompt = f"""Answer this question about the dataset:

Question: {question}

Data Profile:
{profile_text}

Provide a direct answer with:
1. The answer to the question
2. Supporting evidence from the data
3. Any caveats or limitations
4. Suggestions for deeper analysis

Be specific with numbers and reference actual data values."""
        
        return self.ask(prompt)
    
    def _create_report(
        self,
        filename: str,
        profile: dict[str, Any],
        analysis: str
    ) -> str:
        """Create final report."""
        return f"""# Data Analysis Report

**File**: {filename}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Rows**: {profile['rows']:,}
**Columns**: {profile['columns']}

---

## Data Overview

### Columns
| Column | Type | Missing | Missing % |
|--------|------|---------|-----------|
{self._columns_table(profile)}

---

## Analysis

{analysis}

---

## Technical Details

### Column Types
```json
{json.dumps(profile['dtypes'], indent=2)}
```
"""
    
    def _columns_table(self, profile: dict[str, Any]) -> str:
        """Generate columns table."""
        rows = []
        for col in profile['column_names']:
            dtype = profile['dtypes'].get(col, 'unknown')
            missing = profile['missing'].get(col, 0)
            missing_pct = profile['missing_pct'].get(col, 0)
            rows.append(f"| {col} | {dtype} | {missing:,} | {missing_pct}% |")
        return "\n".join(rows)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Data Analysis Agent")
    parser.add_argument("--file", "-f", required=True, help="Data file path")
    parser.add_argument("--question", "-q", help="Specific question to answer")
    parser.add_argument("--type", "-t", choices=["quick", "comprehensive", "deep"], default="comprehensive")
    parser.add_argument("--output", "-o", default="output")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--provider", choices=["groq", "anthropic", "openai"], default="groq")
    
    args = parser.parse_args()
    
    config = AgentConfig(
        provider=args.provider,
        output_dir=args.output,
        verbose=args.verbose,
    )
    
    agent = DataAnalysisAgent(config)
    report = agent.run(
        file_path=args.file,
        question=args.question,
        analysis_type=args.type,
    )
    
    print(report)


if __name__ == "__main__":
    main()
