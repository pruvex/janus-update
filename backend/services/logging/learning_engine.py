"""
Learning Engine (D14) — Weekly Learning Engine for System Performance Analysis

Analyzes historical insights from D12 Insight Engine to identify trends and
generate system improvement recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger("janus_backend")


class TrendDirection(str, Enum):
    """Trend direction for metrics."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


class LearningEngine:
    """
    Weekly Learning Engine for analyzing system performance trends.
    
    Uses D12 Insights as data source to calculate trends and generate
    system improvement recommendations.
    """
    
    def __init__(self):
        self.hours = 7 * 24  # 7 days default
    
    async def fetch_historical_data(self, days: int = 14) -> List[Dict[str, Any]]:
        """
        Fetch historical insights from D12 logs_insights table.
        
        Args:
            days: Number of days to look back (default: 14 for 2 weeks comparison)
        
        Returns:
            List of insight records
        """
        try:
            from backend.services.logging.supabase_client import get_supabase_client
            
            supabase = get_supabase_client()
            
            # Fetch insights from the last N days
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            response = (
                supabase
                .table("logs_insights")
                .select("*")
                .gte("generated_at", cutoff.isoformat())
                .order("generated_at", desc=True)
                .execute()
            )
            
            insights = response.data if response.data else []
            
            logger.info(f"[LEARNING-ENGINE] Fetched {len(insights)} insights from last {days} days")
            return insights
            
        except Exception as e:
            logger.error("[LEARNING-ENGINE] Failed to fetch historical data: %s", e, exc_info=True)
            return []
    
    def calculate_trends(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trends from historical insights using Week N vs Week N-1 delta logic.
        
        Compares current period (Week N) with baseline period (Week N-1) to identify
        rising, falling, or stable trends for key metrics.
        
        Regression Triggers:
        - Trend "worsening" when ErrorRate_diff > 0.05 (5% increase) OR Latency_diff > 20%
        - Trend "falling" (improvement) when values decrease
        
        Args:
            insights: List of insight records from fetch_historical_data()
        
        Returns:
            Dictionary with trend analysis results
        """
        if not insights:
            return {"trends": [], "summary": "No data available for trend analysis"}
        
        # Split data into Week N (current, last 7 days) and Week N-1 (baseline, previous 7 days)
        week_n_cutoff = datetime.utcnow() - timedelta(days=7)
        week_n = [i for i in insights if datetime.fromisoformat(i.get('generated_at', '')) >= week_n_cutoff]
        week_n_minus_1 = [i for i in insights if datetime.fromisoformat(i.get('generated_at', '')) < week_n_cutoff]
        
        # Guardrail: If baseline data is missing, return stable trend
        if not week_n_minus_1:
            logger.warning("[LEARNING-ENGINE] Missing baseline data (Week N-1), returning stable trends")
            return {"trends": [], "summary": "Insufficient data: missing baseline period", "baseline_missing": True}
        
        # Group insights by skill and model for both weeks
        def group_by_skill_model(insights_list):
            grouped = {}
            for insight in insights_list:
                key = f"{insight.get('skill', 'unknown')}_{insight.get('model', 'unknown')}"
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(insight)
            return grouped
        
        grouped_n = group_by_skill_model(week_n)
        grouped_n_minus_1 = group_by_skill_model(week_n_minus_1)
        
        # Calculate trends for each skill/model combination
        trends = []
        for key in set(list(grouped_n.keys()) + list(grouped_n_minus_1.keys())):
            current_insights = grouped_n.get(key, [])
            baseline_insights = grouped_n_minus_1.get(key, [])
            
            # Guardrail: Skip if insufficient data in either period
            if len(current_insights) < 2 or len(baseline_insights) < 2:
                continue
            
            # Calculate averages for current period
            current_errors = [i.get('error_rate', 0) for i in current_insights if i.get('error_rate') is not None]
            current_latencies = [i.get('avg_latency_ms', 0) for i in current_insights if i.get('avg_latency_ms') is not None]
            current_calls = sum(i.get('calls', 0) for i in current_insights)
            
            # Calculate averages for baseline period
            baseline_errors = [i.get('error_rate', 0) for i in baseline_insights if i.get('error_rate') is not None]
            baseline_latencies = [i.get('avg_latency_ms', 0) for i in baseline_insights if i.get('avg_latency_ms') is not None]
            baseline_calls = sum(i.get('calls', 0) for i in baseline_insights)
            
            # Calculate averages
            avg_current_error = sum(current_errors) / len(current_errors) if current_errors else 0
            avg_baseline_error = sum(baseline_errors) / len(baseline_errors) if baseline_errors else 0
            avg_current_latency = sum(current_latencies) / len(current_latencies) if current_latencies else 0
            avg_baseline_latency = sum(baseline_latencies) / len(baseline_latencies) if baseline_latencies else 0
            
            # Calculate deltas
            error_rate_diff = avg_current_error - avg_baseline_error
            latency_diff_pct = ((avg_current_latency - avg_baseline_latency) / avg_baseline_latency * 100) if avg_baseline_latency > 0 else 0
            
            # Determine trend direction using regression triggers
            if error_rate_diff > 0.05 or latency_diff_pct > 20:
                trend = TrendDirection.RISING  # worsening
            elif error_rate_diff < -0.05 or latency_diff_pct < -20:
                trend = TrendDirection.FALLING  # improving
            else:
                trend = TrendDirection.STABLE
            
            skill, model = key.split('_', 1)
            
            trends.append({
                "scope": f"skill:{skill}",
                "model": model,
                "metric": "error_rate",
                "current_avg": avg_current_error,
                "baseline_avg": avg_baseline_error,
                "error_rate_diff": error_rate_diff,
                "current_latency": avg_current_latency,
                "baseline_latency": avg_baseline_latency,
                "latency_diff_pct": latency_diff_pct,
                "current_calls": current_calls,
                "baseline_calls": baseline_calls,
                "trend": trend.value,
                "trend_trigger": "error_rate" if abs(error_rate_diff) > 0.05 else "latency" if abs(latency_diff_pct) > 20 else "none"
            })
        
        # Generate summary
        rising_count = sum(1 for t in trends if t["trend"] == "rising")
        falling_count = sum(1 for t in trends if t["trend"] == "falling")
        stable_count = sum(1 for t in trends if t["trend"] == "stable")
        
        summary = f"Trend analysis: {rising_count} worsening, {falling_count} improving, {stable_count} stable"
        
        return {
            "trends": trends,
            "summary": summary,
            "week_n_count": len(week_n),
            "week_n_minus_1_count": len(week_n_minus_1),
            "total_insights": len(insights),
            "analyzed_combinations": len(trends)
        }
    
    def generate_improvements(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate system improvement recommendations using deterministic rules.
        
        Recommendation Engine Rules:
        - ErrorRate > 0.3 + Trend == worsening → Action: MODEL_SWITCH
        - Latency > 3000ms + Trend == worsening → Action: TIMEOUT_ADJUST
        - Calls > 100 + ErrorRate == 0 → Action: COST_OPTIMIZE
        
        Args:
            trends: List of trend analysis results from calculate_trends()
        
        Returns:
            List of improvement recommendations
        """
        improvements = []
        
        for trend in trends:
            current_error = trend.get('current_avg', 0)
            current_latency = trend.get('current_latency', 0)
            current_calls = trend.get('current_calls', 0)
            trend_direction = trend.get('trend', 'stable')
            scope = trend.get('scope', '')
            model = trend.get('model', 'unknown')
            
            # Rule 1: ErrorRate > 0.3 + Trend == worsening → MODEL_SWITCH
            if current_error > 0.3 and trend_direction == 'rising':
                improvements.append({
                    "scope": scope,
                    "model": model,
                    "issue": f"Error rate worsening ({current_error:.2f}) above threshold (0.3)",
                    "trend": "worsening",
                    "recommendation": f"MODEL_SWITCH: Escalate to stronger model for {model}. Current error rate is {current_error:.2f}.",
                    "action_type": "MODEL_SWITCH",
                    "priority": "HIGH",
                    "metric_value": current_error,
                    "threshold": 0.3
                })
            
            # Rule 2: Latency > 3000ms + Trend == worsening → TIMEOUT_ADJUST
            elif current_latency > 3000 and trend_direction == 'rising':
                improvements.append({
                    "scope": scope,
                    "model": model,
                    "issue": f"Latency worsening ({current_latency:.0f}ms) above threshold (3000ms)",
                    "trend": "worsening",
                    "recommendation": f"TIMEOUT_ADJUST: Increase timeout settings for {scope}. Current latency is {current_latency:.0f}ms.",
                    "action_type": "TIMEOUT_ADJUST",
                    "priority": "MEDIUM",
                    "metric_value": current_latency,
                    "threshold": 3000
                })
            
            # Rule 3: Calls > 100 + ErrorRate == 0 → COST_OPTIMIZE
            elif current_calls > 100 and current_error == 0:
                improvements.append({
                    "scope": scope,
                    "model": model,
                    "issue": f"High call volume ({current_calls}) with zero error rate - potential for cost optimization",
                    "trend": "stable",
                    "recommendation": f"COST_OPTIMIZE: Consider downgrade to Speed-Tier model for {scope}. High volume ({current_calls} calls) with perfect reliability suggests cost savings possible.",
                    "action_type": "COST_OPTIMIZE",
                    "priority": "LOW",
                    "metric_value": current_calls,
                    "threshold": 100
                })
            
            # Rule 4: Trend == falling (improvement) → Maintain current settings
            elif trend_direction == 'falling':
                improvements.append({
                    "scope": scope,
                    "model": model,
                    "issue": f"System improving (error rate: {current_error:.2f}, latency: {current_latency:.0f}ms)",
                    "trend": "improving",
                    "recommendation": f"MAINTAIN: Current configuration working well for {model}. Continue monitoring trends.",
                    "action_type": "MONITOR",
                    "priority": "LOW",
                    "metric_value": current_error,
                    "threshold": 0
                })
        
        return improvements
    
    def format_report_to_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format the learning report to AI Studio Markdown format.
        
        Args:
            report: Complete learning report from generate_weekly_report()
        
        Returns:
            Formatted Markdown report for AI Studio
        """
        lines = []
        
        # Header
        lines.append("# 📊 Weekly Learning Report")
        lines.append("")
        lines.append(f"**Generated:** {report.get('generated_at', 'N/A')}")
        lines.append(f"**Period:** {report.get('period_start', 'N/A')} to {report.get('period_end', 'N/A')}")
        lines.append("")
        
        # Summary
        lines.append("## 📈 Summary")
        lines.append("")
        lines.append(report.get('global_summary', 'No summary available'))
        lines.append("")
        
        # Trends
        trends = report.get('trend_analysis', {}).get('trends', [])
        if trends:
            lines.append("## 🔍 Trend Analysis")
            lines.append("")
            
            # Group by trend direction
            rising = [t for t in trends if t['trend'] == 'rising']
            falling = [t for t in trends if t['trend'] == 'falling']
            stable = [t for t in trends if t['trend'] == 'stable']
            
            if rising:
                lines.append("### ⚠️ Worsening Trends")
                lines.append("")
                for trend in rising:
                    lines.append(f"**{trend['scope']} / {trend['model']}**")
                    lines.append(f"- Error Rate: {trend['current_avg']:.3f} (Δ {trend['error_rate_diff']:+.3f})")
                    lines.append(f"- Latency: {trend['current_latency']:.0f}ms (Δ {trend['latency_diff_pct']:+.1f}%)")
                    lines.append(f"- Trigger: {trend['trend_trigger']}")
                    lines.append("")
            
            if falling:
                lines.append("### ✅ Improving Trends")
                lines.append("")
                for trend in falling:
                    lines.append(f"**{trend['scope']} / {trend['model']}**")
                    lines.append(f"- Error Rate: {trend['current_avg']:.3f} (Δ {trend['error_rate_diff']:+.3f})")
                    lines.append(f"- Latency: {trend['current_latency']:.0f}ms (Δ {trend['latency_diff_pct']:+.1f}%)")
                    lines.append("")
            
            if stable:
                lines.append("### ➡️ Stable Trends")
                lines.append("")
                for trend in stable:
                    lines.append(f"**{trend['scope']} / {trend['model']}**")
                    lines.append(f"- Error Rate: {trend['current_avg']:.3f} (Δ {trend['error_rate_diff']:+.3f})")
                    lines.append(f"- Latency: {trend['current_latency']:.0f}ms (Δ {trend['latency_diff_pct']:+.1f}%)")
                    lines.append("")
        
        # Recommendations
        improvements = report.get('improvements', [])
        if improvements:
            lines.append("## 💡 Recommendations")
            lines.append("")
            
            # Group by priority
            high = [i for i in improvements if i.get('priority') == 'HIGH']
            medium = [i for i in improvements if i.get('priority') == 'MEDIUM']
            low = [i for i in improvements if i.get('priority') == 'LOW']
            
            if high:
                lines.append("### 🔴 HIGH PRIORITY")
                lines.append("")
                for imp in high:
                    lines.append(f"**{imp['scope']} / {imp['model']}**")
                    lines.append(f"- **Issue:** {imp['issue']}")
                    lines.append(f"- **Action:** {imp['action_type']}")
                    lines.append(f"- **Recommendation:** {imp['recommendation']}")
                    lines.append("")
            
            if medium:
                lines.append("### 🟡 MEDIUM PRIORITY")
                lines.append("")
                for imp in medium:
                    lines.append(f"**{imp['scope']} / {imp['model']}**")
                    lines.append(f"- **Issue:** {imp['issue']}")
                    lines.append(f"- **Action:** {imp['action_type']}")
                    lines.append(f"- **Recommendation:** {imp['recommendation']}")
                    lines.append("")
            
            if low:
                lines.append("### 🟢 LOW PRIORITY")
                lines.append("")
                for imp in low:
                    lines.append(f"**{imp['scope']} / {imp['model']}**")
                    lines.append(f"- **Issue:** {imp['issue']}")
                    lines.append(f"- **Action:** {imp['action_type']}")
                    lines.append(f"- **Recommendation:** {imp['recommendation']}")
                    lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by D14 Weekly Learning Engine*")
        
        return "\n".join(lines)
    
    async def generate_weekly_report(self, days: int = 14) -> Dict[str, Any]:
        """
        Generate a complete weekly learning report.
        
        Args:
            days: Number of days to analyze (default: 14 for 2-week comparison)
        
        Returns:
            Complete learning report with trends and improvements
        """
        # Fetch historical data
        insights = await self.fetch_historical_data(days=days)
        
        # Calculate trends
        trend_analysis = self.calculate_trends(insights)
        
        # Generate improvements
        improvements = self.generate_improvements(trend_analysis.get("trends", []))
        
        # Build report
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)
        
        report = {
            "report_type": "weekly",
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "global_summary": trend_analysis.get("summary", "No data available"),
            "insights": insights[:50],  # Limit to 50 most recent insights
            "improvements": improvements,
            "trend_analysis": trend_analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"[LEARNING-ENGINE] Generated weekly report with {len(improvements)} improvements")
        return report
