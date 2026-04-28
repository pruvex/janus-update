"""
Test Runner for Janus-Skills Quality System.

Executes test blueprints with escalation and logs results to D10 telemetry.
Generates AI Studio compatible health reports.
"""

import json
import asyncio
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from uuid import uuid4

from .test_generator import TestGenerator
from .validation import ValidationEngine, ValidationResult
from ..routing.escalation import EscalationEngine, EscalationSummary
from ..routing.model_router import ModelRouter

# Import D10 logging
from backend.services.logging.logger_core import log_event
from backend.data.schemas_logging import LogEventCreate

logger = logging.getLogger("janus_backend")


class BudgetGuard:
    """
    Budget Guard for D21 Full Fleet Calibration.
    
    Tracks API costs and error counts to prevent runaway spending.
    Stops execution when thresholds are exceeded.
    """
    
    def __init__(self, max_cost_eur: float = 5.0, max_api_errors: int = 20):
        self.max_cost_eur = max_cost_eur
        self.max_api_errors = max_api_errors
        self.total_cost_eur = 0.0
        self.api_error_count = 0
        self.test_count = 0
        
    def record_api_call(self, cost_eur: float = 0.0, success: bool = True) -> bool:
        """
        Record an API call and check if budget is exceeded.
        
        Args:
            cost_eur: Cost of the API call in EUR (estimated or actual)
            success: Whether the API call was successful
            
        Returns:
            True if budget is still within limits, False if exceeded
        """
        self.total_cost_eur += cost_eur
        if not success:
            self.api_error_count += 1
        self.test_count += 1
        
        # Check budget limits
        if self.total_cost_eur >= self.max_cost_eur:
            logger.error(f"[BUDGETGUARD] Cost threshold exceeded: {self.total_cost_eur:.2f}€ >= {self.max_cost_eur:.2f}€")
            return False
        
        if self.api_error_count >= self.max_api_errors:
            logger.error(f"[BUDGETGUARD] API error threshold exceeded: {self.api_error_count} >= {self.max_api_errors}")
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current budget guard status."""
        return {
            "total_cost_eur": round(self.total_cost_eur, 4),
            "api_error_count": self.api_error_count,
            "test_count": self.test_count,
            "cost_remaining_eur": round(self.max_cost_eur - self.total_cost_eur, 4),
            "errors_remaining": self.max_api_errors - self.api_error_count,
            "budget_exceeded": self.total_cost_eur >= self.max_cost_eur or self.api_error_count >= self.max_api_errors
        }


class CalibrationWinner:
    """
    Winner-Logic for D21 Full Fleet Calibration (Strict Provider-Silos).
    
    Analyzes test results to determine optimal model assignments per skill per provider.
    STRICT SILO RULES:
    - OpenAI Silo: ONLY gpt-5.4-nano, gpt-5.4-mini, gpt-5.4 (standard). Pro is FORBIDDEN.
    - Gemini Silo: ONLY gemini-3-flash-preview, gemini-3.1-pro-preview.
    - NO Provider-Mixing: Data from one provider never influences the other.
    
    Primary: Highest pass-rate (from 10 runs).
    Secondary: Lowest latency.
    Fallback: Best alternative model WITHIN THE SAME SILO.
    Escalation: Best model WITHIN THE SAME SILO.
    """
    
    def __init__(self):
        self.model_provider_map = {
            "gpt-5.4-nano": "openai",
            "gpt-5.4-mini": "openai",
            "gpt-5.4": "openai",
            "gpt-5.4-pro": "openai",
            "gpt-4o-mini": "openai",
            "gpt-4o": "openai",
            "gemini-3-flash-preview": "gemini",
            "gemini-3.1-pro-preview": "gemini",
            "gemini-3-pro-preview": "gemini",
            "gemini-3-pro": "gemini",
            "gemini-3.1-pro": "gemini"
        }
        
        # STRICT SILO: Only these models are allowed per provider
        self.silo_allowed_models = {
            "openai": {"gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"},  # Pro is FORBIDDEN
            "gemini": {"gemini-3-flash-preview", "gemini-3.1-pro-preview"}
        }
    
    def analyze_calibration_results(
        self, 
        calibration_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze calibration results to determine optimal model assignments per provider-silo.
        
        Args:
            calibration_data: Dictionary with skill_id -> model -> results mapping
            
        Returns:
            Dictionary with optimal model assignments per skill per provider
            Structure: {skill_id: {provider: {primary: {...}, fallback: {...}, escalation: {...}}}}
        """
        optimal_assignments = {}
        
        # Step 1: Group results by provider, then by skill
        provider_skill_data = {}  # {provider: {skill_id: {model: results}}}
        
        for skill_id, model_results in calibration_data.items():
            if not model_results:
                continue
            
            for model, results in model_results.items():
                if not results:
                    continue
                
                provider = self.model_provider_map.get(model, "openai")
                if provider not in provider_skill_data:
                    provider_skill_data[provider] = {}
                if skill_id not in provider_skill_data[provider]:
                    provider_skill_data[provider][skill_id] = {}
                provider_skill_data[provider][skill_id][model] = results
        
        # Step 2: For each provider, determine best chain per skill (STRICT SILO)
        for provider, skill_data in provider_skill_data.items():
            # Get allowed models for this provider
            allowed_models = self.silo_allowed_models.get(provider, set())
            
            for skill_id, model_results in skill_data.items():
                if not model_results:
                    continue
                
                # Filter to ONLY allowed models for this silo
                filtered_model_results = {
                    model: results for model, results in model_results.items()
                    if model in allowed_models
                }
                
                if not filtered_model_results:
                    continue
                
                # Calculate metrics for each allowed model within this provider
                model_metrics = {}
                for model, results in filtered_model_results.items():
                    if not results:
                        continue
                    
                    # Aggregate metrics across all runs
                    total_tests = sum(r.get("test_count", 0) for r in results)
                    total_passed = sum(r.get("passed_count", 0) for r in results)
                    total_latency = sum(r.get("avg_latency_ms", 0) for r in results if r.get("avg_latency_ms"))
                    run_count = len(results)
                    
                    pass_rate = total_passed / total_tests if total_tests > 0 else 0.0
                    avg_latency = total_latency / run_count if run_count > 0 else 0.0
                    
                    model_metrics[model] = {
                        "pass_rate": pass_rate,
                        "avg_latency_ms": avg_latency,
                        "run_count": run_count
                    }
                
                if not model_metrics:
                    continue
                
                # Sort models by (pass_rate, -latency) to determine chain
                sorted_models = sorted(
                    model_metrics.items(),
                    key=lambda x: (x[1]["pass_rate"], -x[1]["avg_latency_ms"]),
                    reverse=True
                )
                
                # Select primary: best model
                primary_model = sorted_models[0][0]
                
                # Select fallback: second best model (within same provider)
                fallback_model = sorted_models[1][0] if len(sorted_models) > 1 else primary_model
                
                # Select escalation: best model (same as primary for now)
                escalation_model = primary_model
                
                # Initialize skill entry if needed
                if skill_id not in optimal_assignments:
                    optimal_assignments[skill_id] = {}
                
                # Assign provider-specific chain
                optimal_assignments[skill_id][provider] = {
                    "primary": {"model": primary_model},
                    "fallback": {"model": fallback_model},
                    "escalation": {"model": escalation_model},
                    "metrics": model_metrics
                }
        
        return optimal_assignments
    
    def generate_model_routing_json(
        self,
        optimal_assignments: Dict[str, Any],
        default_tiers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate model_routing.json from optimal assignments (Provider-Silo structure).
        
        Args:
            optimal_assignments: Dictionary with optimal model assignments per skill per provider
                Structure: {skill_id: {provider: {primary: {...}, fallback: {...}, escalation: {...}}}}
            default_tiers: Optional default tiers to include
            
        Returns:
            Complete model_routing.json structure with nested provider keys
        """
        routing_config = {
            "default_tiers": default_tiers or {
                "openai": {
                    "primary": {"model": "gpt-5.4-nano"},
                    "fallback": {"model": "gpt-5.4-mini"},
                    "escalation": {"model": "gpt-5.4"}
                },
                "gemini": {
                    "primary": {"model": "gemini-3-flash-preview"},
                    "fallback": {"model": "gemini-3.1-pro-preview"},
                    "escalation": {"model": "gemini-3.1-pro-preview"}
                }
            },
            "skill_mappings": {}
        }
        
        # STRONGEST MODELS per silo for escalation (safety net, independent of test results)
        strongest_models = {
            "openai": {"model": "gpt-5.4"},
            "gemini": {"model": "gemini-3.1-pro-preview"}
        }
        
        for skill_id, provider_assignments in optimal_assignments.items():
            skill_mapping = {}
            
            for provider, assignment in provider_assignments.items():
                skill_mapping[provider] = {
                    "primary": assignment["primary"],
                    "fallback": assignment["fallback"],
                    "escalation": strongest_models.get(provider, assignment["escalation"])  # Force strongest model
                }
            
            routing_config["skill_mappings"][skill_id] = skill_mapping
        
        return routing_config


def _map_input_to_args(skill_id: str, input_value: Any) -> Dict[str, Any]:
    """
    Map skill ID to appropriate argument name for tool execution.
    
    Args:
        skill_id: The skill identifier (e.g., "filesystem.list_directory")
        input_value: The input value from the test blueprint
    
    Returns:
        Dictionary with the appropriate argument name and value
    """
    if skill_id.startswith("filesystem."):
        return {"path": input_value}
    if skill_id == "system.weather":
        return {"location": input_value}
    # Fallback for all other skills
    return {"query": input_value}


def discover_skills(skills_dir: str = "backend/skills") -> List[str]:
    """
    Discover all skills from the skills directory (recursive).
    
    Uses module-based absolute paths to work regardless of CWD.
    Uses Path.rglob to find every *.json file at any nesting depth.
    The namespace is derived from the first directory component relative
    to skills_dir (e.g. backend/skills/filesystem/read_file.json → filesystem.read_file).
    
    Args:
        skills_dir: Path to the skills directory (relative to project root)
    
    Returns:
        Sorted list of skill_ids in format "namespace.action"
    """
    # FORENSIC LOGGING
    print(f"[FORENSIC] __file__ = {__file__}")
    
    # Module-based absolute path resolution
    # __file__ = backend/services/testing/test_runner.py
    module_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[FORENSIC] module_dir = {module_dir}")
    
    # module_dir = backend/services/testing/
    services_dir = os.path.dirname(module_dir)
    print(f"[FORENSIC] services_dir = {services_dir}")
    
    # services_dir = backend/services/
    backend_dir = os.path.dirname(services_dir)
    print(f"[FORENSIC] backend_dir = {backend_dir}")
    
    # backend_dir = backend/
    project_root = os.path.dirname(backend_dir)
    print(f"[FORENSIC] project_root = {project_root}")
    
    skills_path = Path(project_root) / skills_dir
    print(f"[FORENSIC] skills_path = {skills_path}")
    print(f"[FORENSIC] skills_path.exists() = {skills_path.exists()}")
    
    # Log parent directory contents
    parent_dir = str(skills_path.parent)
    print(f"[FORENSIC] parent_dir = {parent_dir}")
    try:
        parent_contents = os.listdir(parent_dir)
        print(f"[FORENSIC] parent_dir contents = {parent_contents}")
    except Exception as e:
        print(f"[FORENSIC] ERROR listing parent_dir: {e}")
    
    skill_ids = []
    
    logger.info(f"[discover_skills] Scanning skills from: {skills_path.absolute()}")
    
    if not skills_path.exists():
        logger.warning(f"[discover_skills] Skills directory does not exist: {skills_path.absolute()}")
        return skill_ids
    
    for skill_file in skills_path.rglob("*.json"):
        # Relative path from skills root, e.g. filesystem/read_file.json
        rel = skill_file.relative_to(skills_path)
        parts = rel.parts  # ('filesystem', 'read_file.json') or deeper
        
        if len(parts) < 2:
            # JSON directly in skills root — skip (no namespace)
            continue
        
        namespace = parts[0]
        skill_name = skill_file.stem
        skill_id = f"{namespace}.{skill_name}"
        skill_ids.append(skill_id)
    
    skill_ids.sort()
    logger.info(f"[discover_skills] Discovered {len(skill_ids)} skills")
    print(f"[FORENSIC] Final skill_ids count = {len(skill_ids)}")
    return skill_ids


class TestRunner:
    """Runs skill tests with escalation and D10 telemetry integration."""
    
    def __init__(self, test_dir: str = "config/skill_tests", budget_guard: Optional[BudgetGuard] = None):
        self.test_dir = Path(test_dir)
        self.validation_engine = ValidationEngine()
        self.escalation_engine = EscalationEngine()
        self.model_router = ModelRouter()
        self.test_results: List[Dict[str, Any]] = []
        self.budget_guard = budget_guard
    
    async def run_testset(
        self,
        skill_id: str,
        tool_call_fn: Callable,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run all tests for a skill with escalation and D10 logging.
        
        Args:
            skill_id: Unique skill identifier
            tool_call_fn: Function to execute (should accept provider, model, **kwargs)
            session_id: Optional session identifier for D10 logging
            trace_id: Optional trace identifier for individual test tracking (D20)
        
        Returns:
            Test summary with all results and health metrics
        """
        # Reset circuit breaker for each skill — batch tests are independent
        self.escalation_engine.reset_circuit_breaker()
        
        # Load test blueprint
        blueprint = self._load_blueprint(skill_id)
        if not blueprint:
            return {"error": f"No test blueprint found for skill_id: {skill_id}"}
        
        # Run each test
        test_results = []
        tests = blueprint.get("tests", {})
        
        for test_type, test_spec in tests.items():
            result = await self._run_single_test(
                skill_id=skill_id,
                test_type=test_type,
                test_spec=test_spec,
                tool_call_fn=tool_call_fn,
                session_id=session_id
            )
            test_results.append(result)
        
        # Generate health summary
        health_summary = self.generate_health_summary(skill_id, test_results)
        
        return {
            "skill_id": skill_id,
            "test_count": len(test_results),
            "passed_count": sum(1 for r in test_results if r.get("passed")),
            "results": test_results,
            "health_summary": health_summary
        }
    
    def _load_blueprint(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Load test blueprint from file."""
        filename = f"{skill_id.replace('.', '_')}_test.json"
        filepath = self.test_dir / filename
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    async def _run_single_test(
        self,
        skill_id: str,
        test_type: str,
        test_spec: Dict[str, Any],
        tool_call_fn: Callable,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a single test with escalation and D10 logging.
        
        Args:
            skill_id: Unique skill identifier
            test_type: Type of test (happy_path, edge_case, failure_case)
            test_spec: Test specification with input and validation
            tool_call_fn: Function to execute
            session_id: Optional session identifier
        
        Returns:
            Test result dict
        """
        trace_id = str(uuid4())
        start_time = datetime.utcnow()
        
        # Debug log to track tool_call_fn binding
        print(f"[TEST-RUNNER-DEBUG] Running test for {skill_id} - tool_call_fn type: {type(tool_call_fn).__name__}, id: {id(tool_call_fn)}")
        
        try:
            # Generate tool_calls payload for ToolExecutor
            test_input = test_spec.get("input", {})
            # Extract the actual input value (could be nested in "input" key or direct)
            input_value = test_input.get("input", test_input) if isinstance(test_input, dict) else test_input
            
            # Map skill ID to appropriate argument name
            arguments = _map_input_to_args(skill_id, input_value)
            
            # Guard: Replace None or empty skill_id with safe default for Gemini compatibility
            # Gemini requires alphanumeric (a-z, A-Z, 0-9) or underscores (_) in tool names
            safe_tool_name = skill_id if skill_id and isinstance(skill_id, str) else "matrix_test_skill"
            if skill_id != safe_tool_name:
                logger.warning(f"[D21-TOOL-NAME-GUARD] Invalid tool_name '{skill_id}' replaced with '{safe_tool_name}' for Gemini compatibility")
            
            # Format as tool_calls structure expected by ToolExecutor
            tool_calls = [{
                "name": safe_tool_name,
                "arguments": arguments
            }]
            
            # Execute with escalation
            escalation_summary = await self.escalation_engine.execute_with_escalation(
                skill_id=skill_id,
                tool_call_fn=tool_call_fn,
                validation_fn=lambda r: self._validate_result(r, test_spec.get("validation")).passed,
                tool_calls=tool_calls
            )
            
            # Get final result
            final_attempt = escalation_summary.attempts[-1] if escalation_summary.attempts else None
            final_model = final_attempt.model if final_attempt else "unknown"
            final_provider = final_attempt.provider if final_attempt else "unknown"
            
            # Validate result with None guard
            result_to_validate = final_attempt.result if final_attempt else {}
            if result_to_validate is None:
                result_to_validate = {"status": "error", "message": "Result was None"}
            
            validation_result = self._validate_result(
                result_to_validate,
                test_spec.get("validation")
            )
            
            # Log to D10
            await self._log_to_d10(
                skill_id=skill_id,
                test_type=test_type,
                status="passed" if validation_result.passed else "failed",
                model=final_model,
                provider=final_provider,
                latency_ms=escalation_summary.total_latency_ms,
                trace_id=trace_id,
                session_id=session_id,
                errors=[final_attempt.error] if final_attempt and final_attempt.error else [],
                final_tier=escalation_summary.final_tier,
                attempts_count=len(escalation_summary.attempts),
                result_data=result_to_validate
            )
            
            return {
                "test_type": test_type,
                "passed": validation_result.passed,
                "validation": validation_result,
                "escalation_summary": {
                    "final_success": escalation_summary.final_success,
                    "final_tier": escalation_summary.final_tier,
                    "attempts_count": len(escalation_summary.attempts),
                    "total_latency_ms": escalation_summary.total_latency_ms
                },
                "trace_id": trace_id
            }
        
        except Exception as e:
            # Log error to D10
            await self._log_to_d10(
                skill_id=skill_id,
                test_type=test_type,
                status="error",
                model="unknown",
                provider="unknown",
                latency_ms=0,
                trace_id=trace_id,
                session_id=session_id,
                errors=[str(e)]
            )
            
            return {
                "test_type": test_type,
                "passed": False,
                "error": str(e),
                "trace_id": trace_id
            }
    
    def _validate_result(self, result: Any, validation_spec: Optional[Dict[str, Any]]) -> ValidationResult:
        """Validate a result against its specification."""
        if not validation_spec:
            return ValidationResult(
                passed=True,
                validator_type="none",
                message="No validation specified"
            )
        
        # Parse JSON string results before validation
        import json
        parsed_result = result
        if isinstance(result, str):
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                pass  # Leave as string, validation engine will mark as error
        
        return self.validation_engine.validate(parsed_result, validation_spec)
    
    async def _log_to_d10(
        self,
        skill_id: str,
        test_type: str,
        status: str,
        model: str,
        provider: str,
        latency_ms: float,
        trace_id: str,
        session_id: Optional[str],
        errors: List[str],
        final_tier: str = "primary",
        attempts_count: int = 1,
        result_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log test result to D10 telemetry system.
        
        Args:
            skill_id: Unique skill identifier
            test_type: Type of test
            status: Test status (passed, failed, error)
            model: Model used
            provider: Provider used
            latency_ms: Latency in milliseconds
            trace_id: Trace identifier
            session_id: Session identifier
            errors: List of errors if any
            result_data: Actual tool execution result for forensic analysis
        """
        payload = {
            "test_type": test_type,
            "errors": errors,
            "final_tier": final_tier,
            "attempts_count": attempts_count
        }
        
        # Include result data for forensic analysis if provided
        if result_data:
            payload["result_data"] = result_data
            # Map to output_summary for D10 logging visibility (first 500 chars)
            payload["output_summary"] = str(result_data)[:500]
        
        event = LogEventCreate(
            event_type="skill_test",
            skill=skill_id,
            status=status,
            provider=provider,
            model=model,
            latency_ms=int(latency_ms),
            trace_id=trace_id,
            session_id=session_id,
            payload=payload
        )
        
        await log_event(event)
    
    def generate_health_summary(self, skill_id: str, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate AI Studio compatible health summary.
        
        Args:
            skill_id: Unique skill identifier
            test_results: List of test results
        
        Returns:
            Health summary dict
        """
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.get("passed"))
        failed_tests = total_tests - passed_tests
        
        # Calculate average latency
        latencies = [
            r.get("escalation_summary", {}).get("total_latency_ms", 0)
            for r in test_results
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Count escalation attempts
        total_attempts = sum(
            r.get("escalation_summary", {}).get("attempts_count", 0)
            for r in test_results
        )
        
        # Calculate health score (0.0 to 1.0)
        health_score = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return {
            "skill_id": skill_id,
            "health_score": health_score,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "avg_latency_ms": round(avg_latency, 2),
            "total_escalation_attempts": total_attempts,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"
        }
    
    async def run_batch_tests(
        self,
        tool_call_fn: Callable,
        skill_ids: Optional[List[str]] = None,
        skills_dir: str = "backend/skills",
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run tests for multiple skills in batch.
        
        Args:
            tool_call_fn: Function to execute (should accept provider, model, **kwargs)
            skill_ids: Optional list of skill_ids to test. If None, discovers all skills.
            skills_dir: Path to the skills directory (for auto-discovery)
            session_id: Optional session identifier for D10 logging
            trace_id: Optional trace identifier for individual test tracking (D20)
        
        Returns:
            Batch test summary with all results and health metrics
        """
        # Discover skills if not provided
        if skill_ids is None:
            skill_ids = discover_skills(skills_dir)
        
        if not skill_ids:
            return {
                "error": "No skills found for batch testing",
                "skills_tested": 0,
                "results": []
            }
        
        # Initialize test generator
        test_generator = TestGenerator()
        
        # Run tests for each skill
        batch_results = []
        total_passed = 0
        total_failed = 0
        
        for skill_id in skill_ids:
            # Check budget guard before running each skill
            if self.budget_guard and self.budget_guard.get_status()["budget_exceeded"]:
                logger.warning(f"[BUDGETGUARD] Budget exceeded, stopping batch test. Status: {self.budget_guard.get_status()}")
                break
            
            try:
                # Generate testset if not exists
                skill_type = skill_id.split('.')[0] if '.' in skill_id else "tool"
                test_generator.generate_testset(skill_id, skill_type)
                
                # Run testset
                test_summary = await self.run_testset(
                    skill_id=skill_id,
                    tool_call_fn=tool_call_fn,
                    session_id=session_id,
                    trace_id=trace_id
                )
                
                batch_results.append(test_summary)
                total_passed += test_summary.get("passed_count", 0)
                total_failed += test_summary.get("test_count", 0) - test_summary.get("passed_count", 0)
                
            except Exception as e:
                batch_results.append({
                    "skill_id": skill_id,
                    "error": str(e),
                    "test_count": 0,
                    "passed_count": 0
                })
        
        # Calculate batch health metrics
        total_tests_run = sum(r.get("test_count", 0) for r in batch_results)
        overall_pass_rate = total_passed / total_tests_run if total_tests_run > 0 else 0.0
        
        return {
            "skills_tested": len(batch_results),
            "total_tests_run": total_tests_run,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_pass_rate": round(overall_pass_rate, 4),
            "results": batch_results,
            "generated_at": datetime.utcnow().isoformat()
        }


async def run_testset(
    skill_id: str,
    tool_call_fn: Callable,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to run a testset.
    
    Args:
        skill_id: Unique skill identifier
        tool_call_fn: Function to execute
        session_id: Optional session identifier
        trace_id: Optional trace identifier for individual test tracking (D20)
    
    Returns:
        Test summary with health metrics
    """
    runner = TestRunner()
    return await runner.run_testset(skill_id, tool_call_fn, session_id, trace_id)
