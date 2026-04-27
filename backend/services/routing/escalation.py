"""
Escalation Logic for Janus-Skills Quality System.

Implements execute_with_escalation: Primary -> Fallback -> Escalation chain.
Tracks costs and provides circuit breaker protection.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field

from .model_router import ModelRouter

logger = logging.getLogger("janus_backend")


@dataclass
class EscalationResult:
    """Result of an escalation attempt."""
    success: bool
    tier_used: str
    model: str
    provider: str
    result: Any
    latency_ms: float
    cost_estimate: float = 0.0
    error: Optional[str] = None
    validation_passed: bool = True  # Track validation status separately


@dataclass
class EscalationSummary:
    """Summary of full escalation chain execution."""
    final_success: bool
    attempts: list[EscalationResult] = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_cost_estimate: float = 0.0
    final_tier: str = "none"
    error: Optional[str] = None


class EscalationEngine:
    """Engine for executing tool calls with automatic escalation."""
    
    def __init__(self, router: Optional[ModelRouter] = None):
        self.router = router or ModelRouter()
        self.circuit_breaker_tripped = False
    
    async def execute_with_escalation(
        self,
        skill_id: str,
        tool_call_fn: Callable,
        validation_fn: Optional[Callable] = None,
        provider: str = "openai",
        **kwargs
    ) -> EscalationSummary:
        """
        Execute tool call with automatic escalation chain (Provider-Silo).
        
        Args:
            skill_id: Unique skill identifier
            tool_call_fn: Function to execute (should accept model/provider kwargs)
            validation_fn: Optional validation function (returns bool)
            provider: Provider key (\"openai\" or \"gemini\")
            **kwargs: Additional arguments for tool_call_fn
        
        Returns:
            EscalationSummary with all attempt results
        """
        if self.circuit_breaker_tripped:
            return EscalationSummary(
                final_success=False,
                final_tier="circuit_breaker",
                attempts=[],
                error="Circuit breaker tripped - no attempts made"
            )
        
        # Get routing configuration for the provider
        routing_config = self.router.get_routing_config(skill_id, provider)
        
        # Try Primary -> Fallback -> Escalation
        tiers = ["primary", "fallback", "escalation"]
        attempts = []
        
        for tier in tiers:
            model_config = routing_config.get(tier)
            if not model_config:
                continue
            
            result = await self._execute_at_tier(
                skill_id=skill_id,
                tier=tier,
                model_config=model_config,
                tool_call_fn=tool_call_fn,
                validation_fn=validation_fn,
                provider=provider,
                **kwargs
            )
            
            attempts.append(result)
            
            # Debug logging
            print(f"[DEBUG-ESCALATION] Tier {tier} result: {result.success}, valid: {result.validation_passed}")
            
            # If successful AND validation passed, stop escalation
            if result.success and result.validation_passed:
                return EscalationSummary(
                    final_success=True,
                    attempts=attempts,
                    total_latency_ms=sum(r.latency_ms for r in attempts),
                    total_cost_estimate=sum(r.cost_estimate for r in attempts),
                    final_tier=tier
                )
            
            # Log validation failure and continue escalation
            if not result.validation_passed:
                logger.warning(f"[ESCALATION] Validation failed for tier={tier}, model={result.model}. Escalating to next tier...")
        
        # All tiers failed
        total_latency = sum(r.latency_ms for r in attempts)
        total_cost = sum(r.cost_estimate for r in attempts)
        
        # Circuit breaker: if all tiers failed, trip the breaker
        self.circuit_breaker_tripped = True
        
        return EscalationSummary(
            final_success=False,
            attempts=attempts,
            total_latency_ms=total_latency,
            total_cost_estimate=total_cost,
            final_tier="escalation_exhausted"
        )
    
    async def _execute_at_tier(
        self,
        skill_id: str,
        tier: str,
        model_config: Dict[str, str],
        tool_call_fn: Callable,
        validation_fn: Optional[Callable],
        provider: str,
        **kwargs
    ) -> EscalationResult:
        """
        Execute tool call at a specific tier (Provider-Silo).
        
        Args:
            tier: Tier name (primary, fallback, escalation)
            model_config: Model configuration (model only, provider is separate)
            tool_call_fn: Function to execute
            validation_fn: Optional validation function
            provider: Provider key (\"openai\" or \"gemini\")
            **kwargs: Additional arguments
        
        Returns:
            EscalationResult
        """
        model = model_config.get("model", "unknown")
        
        # Debug log to verify tool_calls is passed
        tool_calls = kwargs.get("tool_calls", [])
        print(f"[ESCALATION-DEBUG] {skill_id} - Calling tool_call_fn with provider={provider}, model={model}, tool_calls={len(tool_calls)} items")
        
        start_time = time.time()  # Initialize before try so except handler always has it
        try:
            # Execute tool call with model configuration
            result = tool_call_fn(provider=provider, model=model, **kwargs)
            
            # Await if result is a coroutine - measure actual LLM call latency
            if asyncio.iscoroutine(result):
                start_time = time.time()  # Start time immediately before await
                result = await result
                latency_ms = (time.time() - start_time) * 1000  # End time immediately after await
                print(f"[LATENCY-AUDIT] {skill_id} LLM call latency: {latency_ms:.2f}ms (provider={provider}, model={model})")
            else:
                # Synchronous execution - measure total time
                start_time = time.time()
                latency_ms = (time.time() - start_time) * 1000
                print(f"[LATENCY-AUDIT] {skill_id} sync execution latency: {latency_ms:.2f}ms")
            
            # Check validation if provided — must be bool, not ValidationResult object
            validation_passed = True
            if validation_fn:
                vr = validation_fn(result)
                validation_passed = bool(getattr(vr, 'passed', vr))
            
            # Check for explicit error status
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                success = status == "ok" or status == "success"
            else:
                success = validation_passed
            
            # Estimate cost (simplified - actual cost depends on token usage)
            cost_estimate = self._estimate_cost(provider, model, result)
            
            return EscalationResult(
                success=success,
                tier_used=tier,
                model=model,
                provider=provider,
                result=result,
                latency_ms=latency_ms,
                cost_estimate=cost_estimate,
                error=None,
                validation_passed=validation_passed
            )
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"[ESCALATION-EXCEPTION] {skill_id} tier={tier} model={model} EXCEPTION: {e}", exc_info=True)
            
            return EscalationResult(
                success=False,
                tier_used=tier,
                model=model,
                provider=provider,
                result=None,
                latency_ms=latency_ms,
                error=str(e),
                validation_passed=False  # Validation fails on exception
            )
    
    def _estimate_cost(self, provider: str, model: str, result: Any) -> float:
        """
        Estimate cost for a model execution.
        
        Args:
            provider: Model provider
            model: Model name
            result: Execution result
        
        Returns:
            Estimated cost in USD
        """
        # Simplified cost estimation (actual implementation would count tokens)
        cost_map = {
            "gpt-4o-mini": 0.0001,
            "gpt-4o": 0.001,
            "gpt-4-turbo": 0.005
        }
        
        return cost_map.get(model, 0.001)
    
    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to allow new attempts."""
        self.circuit_breaker_tripped = False


async def execute_with_escalation(
    skill_id: str,
    tool_call_fn: Callable,
    validation_fn: Optional[Callable] = None,
    provider: str = "openai",
    **kwargs
) -> EscalationSummary:
    """
    Convenience function to execute with escalation (Provider-Silo).
    
    Args:
        skill_id: Unique skill identifier
        tool_call_fn: Function to execute
        validation_fn: Optional validation function
        provider: Provider key (\"openai\" or \"gemini\")
        **kwargs: Additional arguments
    
    Returns:
        EscalationSummary
    """
    engine = EscalationEngine()
    return await engine.execute_with_escalation(skill_id, tool_call_fn, validation_fn, provider, **kwargs)
