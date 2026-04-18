"""
Benchmark Harness Wrapper

Standardized interface for running DAB queries and computing scores.
Handles logging, tracing, and result validation.

Integrates with the Sentinel evaluation harness pattern from Week 5.
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class TerminateReason(Enum):
    """Reasons for agent termination."""
    SUCCESS = "success"
    NO_TOOL_CALL = "no_tool_call"
    MAX_ITERATIONS = "max_iterations"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ToolCall:
    """Record of a single tool call."""
    timestamp: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    duration_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class QueryTrace:
    """Complete trace of a query execution."""
    query_id: str
    dataset: str
    run_number: int
    start_time: str
    end_time: str
    duration_ms: float
    terminate_reason: TerminateReason
    final_answer: Any
    tool_calls: List[ToolCall] = field(default_factory=list)
    llm_calls: List[Dict] = field(default_factory=list)
    context_used: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating an agent answer."""
    query_id: str
    dataset: str
    run_number: int
    is_valid: bool
    reason: str
    ground_truth: Any
    llm_answer: Any
    timestamp: str


class BenchmarkHarness:
    """
    Wrapper for running DAB benchmark queries with full tracing.
    
    Features:
    - Standardized query execution interface
    - Full tool call and LLM call tracing
    - Result validation against ground truth
    - Pass@1 score computation
    - Sentinel-compatible trace format
    """
    
    def __init__(
        self,
        dab_path: str = "DataAgentBench",
        results_dir: str = "results",
        logs_dir: str = "logs"
    ):
        """
        Initialize harness with DAB paths.
        
        Args:
            dab_path: Path to DataAgentBench repository
            results_dir: Directory for storing results
            logs_dir: Directory for execution logs
        """
        self.dab_path = Path(dab_path)
        self.results_dir = Path(results_dir)
        self.logs_dir = Path(logs_dir)
        
        # Create directories
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load DAB validation modules
        self._validation_cache: Dict[str, Any] = {}
    
    def _get_query_dir(self, dataset: str, query_id: str) -> Path:
        """Get path to query directory."""
        return self.dab_path / f"query_{dataset}" / f"query{query_id}"
    
    def _load_ground_truth(self, dataset: str, query_id: str) -> Any:
        """Load ground truth for a query."""
        query_dir = self._get_query_dir(dataset, query_id)
        gt_path = query_dir / "ground_truth.csv"
        
        if gt_path.exists():
            import pandas as pd
            df = pd.read_csv(gt_path)
            return df.to_dict(orient='records')
        
        # Try JSON format
        gt_json = query_dir / "ground_truth.json"
        if gt_json.exists():
            with open(gt_json, 'r') as f:
                return json.load(f)
        
        # Try text format
        gt_txt = query_dir / "ground_truth.txt"
        if gt_txt.exists():
            with open(gt_txt, 'r') as f:
                return f.read().strip()
        
        return None
    
    def _load_validator(self, dataset: str, query_id: str):
        """Load validation function for a query."""
        cache_key = f"{dataset}_{query_id}"
        
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
        query_dir = self._get_query_dir(dataset, query_id)
        validate_path = query_dir / "validate.py"
        
        if not validate_path.exists():
            # Default validator
            def default_validate(llm_output: str, ground_truth: Any) -> Tuple[bool, str]:
                """Default string matching validation."""
                if isinstance(ground_truth, str):
                    is_valid = str(llm_output).strip().lower() == ground_truth.strip().lower()
                    return is_valid, "Exact match" if is_valid else "Value mismatch"
                return False, "No validator available"
            
            self._validation_cache[cache_key] = default_validate
            return default_validate
        
        # Load custom validator
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate", validate_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        validator = module.validate
        self._validation_cache[cache_key] = validator
        return validator
    
    def run_query(
        self,
        agent,  # Your agent instance
        dataset: str,
        query_id: str,
        run_number: int = 0,
        max_iterations: int = 100,
        use_hints: bool = False,
        context_builder=None  # Optional MultiPassRetriever
    ) -> QueryTrace:
        """
        Run a single query with full tracing.
        
        Args:
            agent: Data agent instance with run(query, context) method
            dataset: Dataset name
            query_id: Query identifier (e.g., "1")
            run_number: Run number for multi-trial evaluation
            max_iterations: Maximum agent iterations
            use_hints: Whether to use dataset hints
            context_builder: Optional MultiPassRetriever instance
            
        Returns:
            Complete QueryTrace
        """
        start_time = datetime.now()
        start_timestamp = start_time.isoformat()
        
        # Load query
        query_dir = self._get_query_dir(dataset, query_id)
        query_path = query_dir / "query.json"
        
        with open(query_path, 'r') as f:
            query_data = json.load(f)
            query_text = query_data.get("query", query_data)
        
        # Load hints if requested
        context = None
        if use_hints:
            hints_path = self.dab_path / f"query_{dataset}" / "db_description_with_hint.txt"
            if hints_path.exists():
                with open(hints_path, 'r') as f:
                    context = f.read()
        
        # Use context builder if provided
        if context_builder and not use_hints:
            try:
                from utils.multi_pass_retrieval import MultiPassRetriever
                if isinstance(context_builder, MultiPassRetriever):
                    context = context_builder.build_context(
                        dataset, query_text, PassLevel.SCHEMA_ONLY
                    ).to_prompt()
            except ImportError:
                pass
        
        # Execute query with agent
        tool_calls = []
        llm_calls = []
        
        try:
            # Assumes agent.run returns (answer, trace)
            answer, trace = agent.run(query_text, context)
            
            # Extract tool calls from trace
            for step in trace:
                if step.get('type') == 'tool_call':
                    tool_calls.append(ToolCall(
                        timestamp=step.get('timestamp', datetime.now().isoformat()),
                        tool_name=step.get('tool', 'unknown'),
                        parameters=step.get('parameters', {}),
                        result=step.get('result'),
                        duration_ms=step.get('duration_ms', 0),
                        success=step.get('success', True),
                        error=step.get('error')
                    ))
                elif step.get('type') == 'llm_call':
                    llm_calls.append(step)
            
            terminate_reason = TerminateReason.SUCCESS
            
        except Exception as e:
            answer = None
            trace = []
            terminate_reason = TerminateReason.ERROR
            error_message = str(e)
        
        end_time = datetime.now()
        
        return QueryTrace(
            query_id=query_id,
            dataset=dataset,
            run_number=run_number,
            start_time=start_timestamp,
            end_time=end_time.isoformat(),
            duration_ms=(end_time - start_time).total_seconds() * 1000,
            terminate_reason=terminate_reason,
            final_answer=answer,
            tool_calls=tool_calls,
            llm_calls=llm_calls,
            context_used=context,
            error_message=error_message if terminate_reason == TerminateReason.ERROR else None
        )
    
    def validate_result(
        self,
        trace: QueryTrace,
        dataset: str,
        query_id: str
    ) -> ValidationResult:
        """
        Validate agent answer against ground truth.
        
        Args:
            trace: Query trace from run_query
            dataset: Dataset name
            query_id: Query identifier
            
        Returns:
            ValidationResult
        """
        # Load ground truth
        ground_truth = self._load_ground_truth(dataset, query_id)
        
        # Load validator
        validator = self._load_validator(dataset, query_id)
        
        # Validate
        if trace.terminate_reason == TerminateReason.NO_TOOL_CALL:
            is_valid = False
            reason = "Agent made no tool calls"
        elif trace.terminate_reason == TerminateReason.ERROR:
            is_valid = False
            reason = f"Agent error: {trace.error_message}"
        else:
            try:
                is_valid, reason = validator(str(trace.final_answer), ground_truth)
            except Exception as e:
                is_valid = False
                reason = f"Validation error: {str(e)}"
        
        return ValidationResult(
            query_id=query_id,
            dataset=dataset,
            run_number=trace.run_number,
            is_valid=is_valid,
            reason=reason,
            ground_truth=ground_truth,
            llm_answer=trace.final_answer,
            timestamp=datetime.now().isoformat()
        )
    
    def save_trace(self, trace: QueryTrace) -> Path:
        """Save query trace to logs directory."""
        log_dir = self.logs_dir / f"query_{trace.dataset}" / f"query{trace.query_id}" / f"run_{trace.run_number}"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Save full trace
        trace_path = log_dir / "final_agent.json"
        with open(trace_path, 'w') as f:
            json.dump(asdict(trace), f, indent=2, default=str)
        
        # Save tool calls separately
        tools_path = log_dir / "tool_calls.jsonl"
        with open(tools_path, 'w') as f:
            for tc in trace.tool_calls:
                f.write(json.dumps(asdict(tc), default=str) + '\n')
        
        # Save LLM calls separately
        llm_path = log_dir / "llm_calls.jsonl"
        with open(llm_path, 'w') as f:
            for lc in trace.llm_calls:
                f.write(json.dumps(lc, default=str) + '\n')
        
        return trace_path
    
    def run_benchmark(
        self,
        agent,
        dataset: str,
        trials: int = 50,
        query_ids: Optional[List[str]] = None,
        context_builder=None
    ) -> Dict[str, Any]:
        """
        Run full benchmark for a dataset.
        
        Args:
            agent: Data agent instance
            dataset: Dataset name
            trials: Number of trials per query
            query_ids: Specific query IDs to run (None = all)
            context_builder: Optional MultiPassRetriever instance
            
        Returns:
            Results dictionary with all traces and validation results
        """
        # Get query list
        if query_ids is None:
            query_dir = self.dab_path / f"query_{dataset}"
            query_ids = [
                d.name.replace("query", "")
                for d in query_dir.iterdir()
                if d.is_dir() and d.name.startswith("query")
            ]
        
        all_traces = []
        all_validations = []
        
        for query_id in query_ids:
            for run in range(trials):
                print(f"Running {dataset} query {query_id} trial {run + 1}/{trials}")
                
                trace = self.run_query(
                    agent=agent,
                    dataset=dataset,
                    query_id=query_id,
                    run_number=run,
                    context_builder=context_builder
                )
                
                self.save_trace(trace)
                all_traces.append(trace)
                
                validation = self.validate_result(trace, dataset, query_id)
                all_validations.append(validation)
        
        return {
            'dataset': dataset,
            'trials': trials,
            'query_ids': query_ids,
            'traces': [asdict(t) for t in all_traces],
            'validations': [asdict(v) for v in all_validations]
        }
    
    def compute_pass_at_1(self, dataset: str, results_dir: Optional[str] = None) -> float:
        """
        Compute Pass@1 score from run logs.
        
        Args:
            dataset: Dataset name
            results_dir: Directory containing run logs
            
        Returns:
            Pass@1 score (0.0 to 1.0)
        """
        if results_dir is None:
            results_dir = self.logs_dir
        
        log_path = Path(results_dir) / f"query_{dataset}"
        
        if not log_path.exists():
            return 0.0
        
        correct = 0
        total = 0
        
        for query_dir in log_path.iterdir():
            if not query_dir.is_dir():
                continue
            
            for run_dir in query_dir.glob("run_*"):
                trace_path = run_dir / "final_agent.json"
                if trace_path.exists():
                    with open(trace_path, 'r') as f:
                        trace = json.load(f)
                    
                    query_id = query_dir.name.replace("query", "")
                    validation = self.validate_result(
                        QueryTrace(**trace),
                        dataset,
                        query_id
                    )
                    
                    if validation.is_valid:
                        correct += 1
                    total += 1
        
        return correct / total if total > 0 else 0.0
    
    def generate_submission_json(
        self,
        agent_name: str,
        traces: List[QueryTrace],
        output_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate DAB leaderboard submission JSON.
        
        Args:
            agent_name: Name of the agent
            traces: All query traces from benchmark runs
            output_path: Optional path to save JSON file
            
        Returns:
            List of submission entries
        """
        submission = []
        
        for trace in traces:
            entry = {
                "dataset": trace.dataset,
                "query": trace.query_id,
                "run": trace.run_number,
                "answer": str(trace.final_answer) if trace.final_answer else ""
            }
            submission.append(entry)
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(submission, f, indent=2)
        
        return submission
    
    def score_log_entry(
        self,
        dataset: str,
        baseline_score: float,
        current_score: float,
        notes: str = ""
    ) -> str:
        """
        Generate a score log entry in required format.
        
        Args:
            dataset: Dataset name
            baseline_score: Initial Pass@1 score
            current_score: Current Pass@1 score
            notes: Additional notes
            
        Returns:
            Markdown table row
        """
        delta = current_score - baseline_score
        delta_str = f"+{delta:.1%}" if delta >= 0 else f"{delta:.1%}"
        
        return f"| {datetime.now().strftime('%b %d')} | {dataset} | {baseline_score:.1%} | {current_score:.1%} | {delta_str} | {notes} |"


# Convenience functions
def run_dab_query(
    agent,
    dataset: str,
    query_id: str,
    trials: int = 1,
    dab_path: str = "DataAgentBench"
) -> List[QueryTrace]:
    """
    Run a DAB query with standard configuration.
    
    Args:
        agent: Data agent instance
        dataset: Dataset name
        query_id: Query identifier
        trials: Number of trials
        dab_path: Path to DAB repository
        
    Returns:
        List of query traces
    """
    harness = BenchmarkHarness(dab_path=dab_path)
    
    traces = []
    for run in range(trials):
        trace = harness.run_query(agent, dataset, query_id, run_number=run)
        harness.save_trace(trace)
        traces.append(trace)
    
    return traces


def compute_pass_at_1(dataset: str, logs_dir: str = "logs") -> float:
    """
    Compute Pass@1 score from logs directory.
    
    Args:
        dataset: Dataset name
        logs_dir: Directory containing run logs
        
    Returns:
        Pass@1 score
    """
    harness = BenchmarkHarness(logs_dir=logs_dir)
    return harness.compute_pass_at_1(dataset, results_dir=logs_dir)