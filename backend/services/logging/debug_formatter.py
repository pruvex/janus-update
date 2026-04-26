"""
Debug Formatter for AI-Studio Integration.
Formats debug report data into structured markdown with standard sections.
"""
from typing import Dict, Any
from datetime import datetime


def format_debug_report(summary_data: Dict[str, Any]) -> str:
    """
    Format debug report data into structured markdown for AI-Studio.
    
    Sections:
    - SUMMARY: High-level overview
    - ROOT CAUSE: Technical root cause analysis
    - FINDINGS: Detailed heuristic findings
    - CONFIDENCE: Confidence score and interpretation
    - RECOMMENDED ACTION: Concrete action recommendations
    
    Args:
        summary_data: Dictionary containing debug analysis results with keys:
            - logs_analyzed: int
            - confidence_score: float
            - hard_errors: list
            - model_drift: list
            - latency_spikes: list
            - generated_at: str (ISO timestamp)
    
    Returns:
        str: Formatted markdown report.
    """
    lines = []
    
    # Header
    lines.append("# 🐛 Debug Report")
    lines.append("")
    lines.append(f"**Generated:** {summary_data.get('generated_at', datetime.utcnow().isoformat())}")
    lines.append(f"**Logs Analyzed:** {summary_data.get('logs_analyzed', 0)}")
    lines.append("")
    
    # SUMMARY
    lines.append("## 📊 SUMMARY")
    lines.append("")
    hard_errors = summary_data.get('hard_errors', [])
    model_drift = summary_data.get('model_drift', [])
    latency_spikes = summary_data.get('latency_spikes', [])
    
    if hard_errors:
        lines.append(f"- **Critical Issues:** {len(hard_errors)} hard error(s) detected")
    if model_drift:
        lines.append(f"- **Model Drift:** {len(model_drift)} drift event(s) detected")
    if latency_spikes:
        lines.append(f"- **Performance:** {len(latency_spikes)} latency spike(s) detected")
    if not any([hard_errors, model_drift, latency_spikes]):
        lines.append("- **Status:** No critical issues detected. System operating normally.")
    lines.append("")
    
    # ROOT CAUSE
    lines.append("## 🔍 ROOT CAUSE")
    lines.append("")
    if hard_errors:
        lines.append("Primary root cause analysis:")
        for error in hard_errors[:3]:  # Show top 3
            lines.append(f"- **{error.get('skill', 'Unknown Skill')}:** {error.get('error_code', 'Unknown error')} at {error.get('timestamp', 'Unknown time')}")
        if len(hard_errors) > 3:
            lines.append(f"- ... and {len(hard_errors) - 3} more error(s)")
    elif model_drift:
        lines.append("Root cause: Model/provider drift detected during execution")
        for drift in model_drift[:2]:
            if drift['type'] == 'provider_drift':
                lines.append(f"- Provider drift in trace {drift['trace_id']}: {drift['providers']}")
            else:
                lines.append(f"- Model drift in trace {drift['trace_id']}: {drift['models']}")
    elif latency_spikes:
        lines.append("Root cause: Performance degradation detected")
        for spike in latency_spikes[:2]:
            lines.append(f"- {spike['skill']}: {spike['latency_ms']}ms latency at {spike['timestamp']}")
    else:
        lines.append("No root cause identified. System is operating within normal parameters.")
    lines.append("")
    
    # FINDINGS
    lines.append("## 📋 FINDINGS")
    lines.append("")
    lines.append("### Hard Errors")
    if hard_errors:
        for error in hard_errors[:5]:
            lines.append(f"- `{error.get('timestamp', 'Unknown')}` | Skill: `{error.get('skill', 'Unknown')}` | Error: `{error.get('error_code', 'Unknown')}`")
        if len(hard_errors) > 5:
            lines.append(f"- ... and {len(hard_errors) - 5} more error(s)")
    else:
        lines.append("- None")
    lines.append("")
    
    lines.append("### Model Drift")
    if model_drift:
        for drift in model_drift[:5]:
            if drift['type'] == 'provider_drift':
                lines.append(f"- Trace `{drift['trace_id']}`: Provider drift → {drift['providers']}")
            else:
                lines.append(f"- Trace `{drift['trace_id']}`: Model drift → {drift['models']}")
        if len(model_drift) > 5:
            lines.append(f"- ... and {len(model_drift) - 5} more drift event(s)")
    else:
        lines.append("- None")
    lines.append("")
    
    lines.append("### Latency Spikes")
    if latency_spikes:
        for spike in latency_spikes[:5]:
            lines.append(f"- `{spike['timestamp']}` | Skill: `{spike['skill']}` | Latency: `{spike['latency_ms']}ms`")
        if len(latency_spikes) > 5:
            lines.append(f"- ... and {len(latency_spikes) - 5} more spike(s)")
    else:
        lines.append("- None")
    lines.append("")
    
    # CONFIDENCE
    lines.append("## 🎯 CONFIDENCE")
    lines.append("")
    confidence = summary_data.get('confidence_score', 0.0)
    lines.append(f"**Confidence Score:** {confidence:.2f}")
    lines.append("")
    
    if confidence >= 0.8:
        lines.append("**Interpretation:** High confidence in diagnosis. System state is well-understood.")
    elif confidence >= 0.5:
        lines.append("**Interpretation:** Moderate confidence. Some uncertainty in diagnosis due to limited data or mixed signals.")
    elif confidence >= 0.3:
        lines.append("**Interpretation:** Low confidence. Diagnosis may be incomplete or based on insufficient data.")
    else:
        lines.append("**Interpretation:** Very low confidence. Diagnosis is uncertain. Manual review recommended.")
    lines.append("")
    
    # RECOMMENDED ACTION
    lines.append("## ✅ RECOMMENDED ACTION")
    lines.append("")
    if hard_errors:
        lines.append("1. **Immediate:** Investigate hard errors listed in Findings section")
        lines.append("2. **Priority:** Address error codes and check for upstream dependencies")
        lines.append("3. **Monitor:** Watch for recurring error patterns")
    elif model_drift:
        lines.append("1. **Review:** Check model/provider configuration consistency")
        lines.append("2. **Stabilize:** Ensure consistent model selection across the session")
        lines.append("3. **Audit:** Review trace logs for drift patterns")
    elif latency_spikes:
        lines.append("1. **Investigate:** Check resource utilization and external dependencies")
        lines.append("2. **Optimize:** Review timeout configurations and retry logic")
        lines.append("3. **Monitor:** Track latency trends over time")
    else:
        lines.append("1. **Continue:** System is operating normally")
        lines.append("2. **Monitor:** Maintain regular log review practices")
        lines.append("3. **Document:** No immediate action required")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*Generated by D11 Debug Compression Engine*")
    
    return "\n".join(lines)
