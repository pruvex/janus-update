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
    severity: str = "PASS"  # "PASS", "WARNING", "CRITICAL_FAIL"
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
        elif validator_type == "fuzzy_contains":
            return self._validate_fuzzy_contains(result, validation_spec)
        elif validator_type == "key_exists":
            return self._validate_key_exists(result, validation_spec)
        elif validator_type == "type_match":
            return self._validate_type_match(result, validation_spec)
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
                message=f"Unknown validator type: {validator_type}",
                severity="CRITICAL_FAIL"
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
                severity="CRITICAL_FAIL",
                details={"field": field, "expected": expected_value, "actual": actual_value}
            )
        
        if actual_value == expected_value:
            return ValidationResult(
                passed=True,
                validator_type="contains",
                message=f"Field '{field}' contains expected value '{expected_value}'",
                severity="PASS",
                details={"field": field, "expected": expected_value, "actual": actual_value}
            )
        else:
            return ValidationResult(
                passed=False,
                validator_type="contains",
                message=f"Field '{field}' does not contain expected value. Expected: '{expected_value}', Actual: '{actual_value}'",
                severity="CRITICAL_FAIL",
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


    def _validate_fuzzy_contains(self, result: Dict[str, Any], spec: Dict[str, Any]) -> ValidationResult:
        """
        Fuzzy substring match: case-insensitive, whitespace-tolerant.
        Passes if expected value is a substring of the actual field value.
        
        Args:
            result: Test result
            spec: Validation spec with 'field' and 'value'
        
        Returns:
            ValidationResult with WARNING severity on mismatch (not CRITICAL)
        """
        field = spec.get("field")
        expected_value = spec.get("value", "")
        
        if not field:
            return ValidationResult(
                passed=False,
                validator_type="fuzzy_contains",
                message="Missing 'field' in validation spec",
                severity="CRITICAL_FAIL"
            )
        
        actual_value = result.get(field)
        
        if actual_value is None:
            return ValidationResult(
                passed=False,
                validator_type="fuzzy_contains",
                message=f"Field '{field}' is None",
                severity="WARNING",
                details={"field": field, "expected_substring": expected_value, "actual": actual_value}
            )
        
        # Normalize: lowercase + strip whitespace
        actual_str = str(actual_value).lower().strip()
        expected_str = str(expected_value).lower().strip()
        
        if expected_str in actual_str:
            return ValidationResult(
                passed=True,
                validator_type="fuzzy_contains",
                message=f"Field '{field}' fuzzy-matches '{expected_value}'",
                severity="PASS",
                details={"field": field, "expected_substring": expected_value, "actual": actual_value}
            )
        else:
            return ValidationResult(
                passed=False,
                validator_type="fuzzy_contains",
                message=f"Field '{field}' does not fuzzy-match '{expected_value}'. Actual: '{actual_value}'",
                severity="WARNING",
                details={"field": field, "expected_substring": expected_value, "actual": actual_value}
            )
    
    def _validate_key_exists(self, result: Dict[str, Any], spec: Dict[str, Any]) -> ValidationResult:
        """
        Check that a key exists in the result dict, regardless of its value.
        Used for dynamic data (e.g., weather, search results) where value is unpredictable.
        
        Args:
            result: Test result
            spec: Validation spec with 'field' (key name to check)
        
        Returns:
            ValidationResult — CRITICAL_FAIL if key missing, PASS if present
        """
        field = spec.get("field")
        
        if not field:
            return ValidationResult(
                passed=False,
                validator_type="key_exists",
                message="Missing 'field' in validation spec",
                severity="CRITICAL_FAIL"
            )
        
        if field in result:
            actual_value = result[field]
            return ValidationResult(
                passed=True,
                validator_type="key_exists",
                message=f"Key '{field}' exists in result",
                severity="PASS",
                details={"field": field, "actual": actual_value}
            )
        else:
            return ValidationResult(
                passed=False,
                validator_type="key_exists",
                message=f"Key '{field}' is missing from result",
                severity="CRITICAL_FAIL",
                details={"field": field, "available_keys": list(result.keys())}
            )
    
    def _validate_type_match(self, result: Dict[str, Any], spec: Dict[str, Any]) -> ValidationResult:
        """
        Validate that a field's value matches an expected Python type.
        
        Supported type strings: 'str', 'int', 'float', 'list', 'dict', 'bool'
        
        Args:
            result: Test result
            spec: Validation spec with 'field' and 'expected_type'
        
        Returns:
            ValidationResult — WARNING severity on type mismatch (not CRITICAL)
        """
        field = spec.get("field")
        expected_type_str = spec.get("expected_type", "str")
        
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "bool": bool,
        }
        
        if not field:
            return ValidationResult(
                passed=False,
                validator_type="type_match",
                message="Missing 'field' in validation spec",
                severity="CRITICAL_FAIL"
            )
        
        expected_type = type_map.get(expected_type_str)
        if expected_type is None:
            return ValidationResult(
                passed=False,
                validator_type="type_match",
                message=f"Unknown expected_type: '{expected_type_str}'. Use: {list(type_map.keys())}",
                severity="CRITICAL_FAIL"
            )
        
        if field not in result:
            return ValidationResult(
                passed=False,
                validator_type="type_match",
                message=f"Key '{field}' is missing from result",
                severity="CRITICAL_FAIL",
                details={"field": field, "available_keys": list(result.keys())}
            )
        
        actual_value = result[field]
        actual_type = type(actual_value).__name__
        
        if isinstance(actual_value, expected_type):
            return ValidationResult(
                passed=True,
                validator_type="type_match",
                message=f"Field '{field}' is of expected type '{expected_type_str}'",
                severity="PASS",
                details={"field": field, "expected_type": expected_type_str, "actual_type": actual_type}
            )
        else:
            return ValidationResult(
                passed=False,
                validator_type="type_match",
                message=f"Field '{field}' type mismatch. Expected: '{expected_type_str}', Actual: '{actual_type}'",
                severity="WARNING",
                details={"field": field, "expected_type": expected_type_str, "actual_type": actual_type, "value": str(actual_value)[:100]}
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
