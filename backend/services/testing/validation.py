"""
Validation Engine for Janus-Skills Quality System.

Deterministic validation rules for test results.
STRICTLY FORBIDDEN: No AI-based validation.
"""

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    validator_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationEngine:
    """Deterministic validation engine for skill test results."""
    
    def validate(self, result: Dict[str, Any], validation_spec: Dict[str, Any]) -> ValidationResult:
        """
        Validate a test result against a validation specification.
        
        Args:
            result: The actual test result
            validation_spec: The validation specification from the test blueprint
        
        Returns:
            ValidationResult with pass/fail status
        """
        # Guard against None or empty result
        if result is None:
            return ValidationResult(
                passed=False,
                validator_type="none_guard",
                message="Result is None - cannot validate"
            )
        
        if not isinstance(result, dict):
            return ValidationResult(
                passed=False,
                validator_type="type_guard",
                message=f"Result must be a dict, got {type(result).__name__}"
            )
        
        validator_type = validation_spec.get("type")
        
        if validator_type == "contains":
            return self._validate_contains(result, validation_spec)
        elif validator_type == "not_contains":
            return self._validate_not_contains(result, validation_spec)
        elif validator_type == "regex":
            return self._validate_regex(result, validation_spec)
        elif validator_type == "not_crash":
            return self._validate_not_crash(result, validation_spec)
        else:
            return ValidationResult(
                passed=False,
                validator_type="unknown",
                message=f"Unknown validator type: {validator_type}"
            )
    
    def _validate_contains(self, result: Dict[str, Any], spec: Dict[str, Any]) -> ValidationResult:
        """
        Validate that a field contains a specific value.
        
        Args:
            result: Test result
            spec: Validation spec with 'field' and 'value'
        
        Returns:
            ValidationResult
        """
        field = spec.get("field")
        expected_value = spec.get("value")
        
        if not field:
            return ValidationResult(
                passed=False,
                validator_type="contains",
                message="Missing 'field' in validation spec"
            )
        
        actual_value = result.get(field)
        
        # Handle None or empty actual_value
        if actual_value is None or actual_value == "":
            return ValidationResult(
                passed=False,
                validator_type="contains",
                message=f"Field '{field}' is None or empty, expected '{expected_value}'",
                details={"field": field, "expected": expected_value, "actual": actual_value}
            )
        
        if actual_value == expected_value:
            return ValidationResult(
                passed=True,
                validator_type="contains",
                message=f"Field '{field}' contains expected value '{expected_value}'",
                details={"field": field, "expected": expected_value, "actual": actual_value}
            )
        else:
            return ValidationResult(
                passed=False,
                validator_type="contains",
                message=f"Field '{field}' does not contain expected value. Expected: '{expected_value}', Actual: '{actual_value}'",
                details={"field": field, "expected": expected_value, "actual": actual_value}
            )
    
    def _validate_not_contains(self, result: Dict[str, Any], spec: Dict[str, Any]) -> ValidationResult:
        """
        Validate that a field does NOT contain a specific value.
        
        Args:
            result: Test result
            spec: Validation spec with 'field' and 'value'
        
        Returns:
            ValidationResult
        """
        field = spec.get("field")
        forbidden_value = spec.get("value")
        
        if not field:
            return ValidationResult(
                passed=False,
                validator_type="not_contains",
                message="Missing 'field' in validation spec"
            )
        
        actual_value = result.get(field)
        
        # Handle None or empty actual_value
        if actual_value is None or actual_value == "":
            return ValidationResult(
                passed=True,
                validator_type="not_contains",
                message=f"Field '{field}' is None or empty, which is not forbidden value '{forbidden_value}'",
                details={"field": field, "forbidden": forbidden_value, "actual": actual_value}
            )
        
        if actual_value != forbidden_value:
            return ValidationResult(
                passed=True,
                validator_type="not_contains",
                message=f"Field '{field}' does not contain forbidden value '{forbidden_value}'",
                details={"field": field, "forbidden": forbidden_value, "actual": actual_value}
            )
        else:
            return ValidationResult(
                passed=False,
                validator_type="not_contains",
                message=f"Field '{field}' contains forbidden value '{forbidden_value}'",
                details={"field": field, "forbidden": forbidden_value, "actual": actual_value}
            )
    
    def _validate_regex(self, result: Dict[str, Any], spec: Dict[str, Any]) -> ValidationResult:
        """
        Validate that a field matches a regex pattern.
        
        Args:
            result: Test result
            spec: Validation spec with 'field' and 'pattern'
        
        Returns:
            ValidationResult
        """
        field = spec.get("field")
        pattern = spec.get("pattern")
        
        if not field or not pattern:
            return ValidationResult(
                passed=False,
                validator_type="regex",
                message="Missing 'field' or 'pattern' in validation spec"
            )
        
        actual_value = result.get(field)
        
        # Handle None or empty actual_value
        if actual_value is None:
            actual_value = ""
        actual_value = str(actual_value)
        
        try:
            if re.search(pattern, actual_value):
                return ValidationResult(
                    passed=True,
                    validator_type="regex",
                    message=f"Field '{field}' matches pattern '{pattern}'",
                    details={"field": field, "pattern": pattern, "actual": actual_value}
                )
            else:
                return ValidationResult(
                    passed=False,
                    validator_type="regex",
                    message=f"Field '{field}' does not match pattern '{pattern}'",
                    details={"field": field, "pattern": pattern, "actual": actual_value}
                )
        except re.error as e:
            return ValidationResult(
                passed=False,
                validator_type="regex",
                message=f"Invalid regex pattern: {e}",
                details={"field": field, "pattern": pattern, "error": str(e)}
            )
    
    def _validate_not_crash(self, result: Dict[str, Any], spec: Dict[str, Any]) -> ValidationResult:
        """
        Validate that the result does not indicate a crash.
        
        Args:
            result: Test result
            spec: Validation spec (may contain description)
        
        Returns:
            ValidationResult
        """
        # Handle None result
        if result is None:
            return ValidationResult(
                passed=False,
                validator_type="not_crash",
                message="Result is None - potential crash",
                details={"result_snippet": "None"}
            )
        
        # Check for crash indicators
        crash_indicators = ["error", "exception", "crash", "panic", "fatal"]
        result_str = str(result).lower()
        
        for indicator in crash_indicators:
            if indicator in result_str:
                return ValidationResult(
                    passed=False,
                    validator_type="not_crash",
                    message=f"Result contains crash indicator: '{indicator}'",
                    details={"indicator": indicator, "result_snippet": result_str[:200]}
                )
        
        return ValidationResult(
            passed=True,
            validator_type="not_crash",
            message="No crash indicators detected",
            details={"result_snippet": result_str[:200]}
        )


def validate_result(result: Dict[str, Any], validation_spec: Dict[str, Any]) -> ValidationResult:
    """
    Convenience function to validate a test result.
    
    Args:
        result: The actual test result
        validation_spec: The validation specification
    
    Returns:
        ValidationResult
    """
    engine = ValidationEngine()
    return engine.validate(result, validation_spec)
