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
    
    async def fetch_historical_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch historical insights from D12 logs_insights table.
        
        Args:
            days: Number of days to look back (default: 7)
        
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
        Calculate trends from historical insights.
        
        Compares current period with previous period to identify
        rising, falling, or stable trends for key metrics.
        
        Args:
            insights: List of insight records from fetch_historical_data()
        
        Returns:
            Dictionary with trend analysis results
        """
        if not insights:
            return {"trends": [], "summary": "No data available for trend analysis"}
        
        # Group insights by skill and model
        grouped = {}
        for insight in insights:
            key = f"{insight.get('skill', 'unknown')}_{insight.get('model', 'unknown')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(insight)
        
        # Calculate trends for each skill/model combination
        trends = []
        for key, group_insights in grouped.items():
            # Split into two periods (first half vs second half)
            mid_point = len(group_insights) // 2
            if mid_point < 2:
                continue  # Not enough data points
            
            recent = group_insights[:mid_point]
            older = group_insights[mid_point:]
            
            # Calculate average error rates
            recent_errors = [i.get('error_rate', 0) for i in recent if i.get('error_rate') is not None]
            older_errors = [i.get('error_rate', 0) for i in older if i.get('error_rate') is not None]
            
            if not recent_errors or not older_errors:
                continue
            
            avg_recent = sum(recent_errors) / len(recent_errors)
            avg_older = sum(older_errors) / len(older_errors)
            
            # Determine trend direction
            if avg_recent > avg_older * 1.2:  # 20% increase
                trend = TrendDirection.RISING
            elif avg_recent < avg_older * 0.8:  # 20% decrease
                trend = TrendDirection.FALLING
            else:
                trend = TrendDirection.STABLE
            
            skill, model = key.split('_', 1)
            
            trends.append({
                "scope": f"skill:{skill}",
                "model": model,
                "metric": "error_rate",
                "recent_avg": avg_recent,
                "older_avg": avg_older,
                "trend": trend.value,
                "change_pct": ((avg_recent - avg_older) / avg_older * 100) if avg_older > 0 else 0
            })
        
        # Generate summary
        rising_count = sum(1 for t in trends if t["trend"] == "rising")
        falling_count = sum(1 for t in trends if t["trend"] == "falling")
        stable_count = sum(1 for t in trends if t["trend"] == "stable")
        
        summary = f"Trend analysis: {rising_count} rising, {falling_count} falling, {stable_count} stable"
        
        return {
            "trends": trends,
            "summary": summary,
            "total_insights": len(insights),
            "analyzed_combinations": len(grouped)
        }
    
    def generate_improvements(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate system improvement recommendations based on trends.
        
        Args:
            trends: List of trend analysis results from calculate_trends()
        
        Returns:
            List of improvement recommendations
        """
        improvements = []
        
        for trend in trends:
            if trend["trend"] == "rising":
                improvements.append({
                    "scope": trend["scope"],
                    "model": trend["model"],
                    "issue": f"Error rate rising by {trend['change_pct']:.1f}%",
                    "trend": "rising",
                    "recommendation": f"Consider model switch or prompt optimization for {trend['model']}"
                })
            elif trend["trend"] == "falling":
                improvements.append({
                    "scope": trend["scope"],
                    "model": trend["model"],
                    "issue": f"Error rate improving by {abs(trend['change_pct']):.1f}%",
                    "trend": "falling",
                    "recommendation": f"Current configuration working well for {trend['model']}. Maintain current settings."
                })
        
        return improvements
    
    async def generate_weekly_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate a complete weekly learning report.
        
        Args:
            days: Number of days to analyze (default: 7)
        
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
