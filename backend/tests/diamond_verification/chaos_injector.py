"""
Diamond Verification Suite V1 — Chaos Injector
Injects chaos into log events for stress testing the Debug Compression Engine.
"""
import sys
from typing import List
from dataclasses import dataclass
import random

sys.path.insert(0, 'backend')

from data.schemas_logging import LogEventCreate


@dataclass
class ChaosConfig:
    """Configuration for chaos injection."""
    inject_none_skill: bool = False
    inject_negative_latency: bool = False
    inject_broken_json: bool = False
    inject_long_trace_id: bool = False
    inject_empty_message: bool = False
    inject_future_timestamp: bool = False
    inject_special_chars: bool = False


class ChaosInjector:
    """Injects chaos into log events for stress testing."""
    
    def __init__(self, config: ChaosConfig = None):
        self.config = config or ChaosConfig()
    
    def inject_chaos(self, events: List[LogEventCreate]) -> List[LogEventCreate]:
        """Inject chaos into log events based on configuration."""
        chaos_events = []
        
        for event in events:
            chaos_event = self._inject_single_chaos(event)
            chaos_events.append(chaos_event)
        
        return chaos_events
    
    def _inject_single_chaos(self, event: LogEventCreate) -> LogEventCreate:
        """Inject chaos into a single log event."""
        # Create a copy to avoid modifying the original
        chaos_event = LogEventCreate(
            timestamp=event.timestamp,
            event_type=event.event_type,
            skill=event.skill,
            latency_ms=event.latency_ms,
            trace_id=event.trace_id,
            status=event.status,
            payload=event.payload
        )
        
        # Apply chaos based on configuration
        if self.config.inject_none_skill and random.random() < 0.1:
            chaos_event.skill = None
        
        if self.config.inject_negative_latency and random.random() < 0.1:
            chaos_event.latency_ms = -random.randint(100, 1000)
        
        if self.config.inject_broken_json and random.random() < 0.1:
            chaos_event.payload = {"message": "Kaputtes JSON {invalid: syntax}"}
        
        if self.config.inject_long_trace_id and random.random() < 0.1:
            chaos_event.trace_id = "x" * 6000
        
        if self.config.inject_empty_message and random.random() < 0.1:
            chaos_event.payload = {}
        
        if self.config.inject_future_timestamp and random.random() < 0.05:
            from datetime import timedelta
            chaos_event.timestamp = chaos_event.timestamp + timedelta(days=1)
        
        if self.config.inject_special_chars and random.random() < 0.1:
            chaos_event.payload = {"message": "Special chars: \x00\x01\x02\x03"}
        
        return chaos_event
    
    def inject_error_status(self, events: List[LogEventCreate], error_rate: float = 0.1) -> List[LogEventCreate]:
        """Inject error status into a percentage of events."""
        error_events = []
        
        for event in events:
            if random.random() < error_rate:
                # Create error event
                error_event = LogEventCreate(
                    timestamp=event.timestamp,
                    event_type="log",
                    skill=event.skill,
                    latency_ms=event.latency_ms,
                    trace_id=event.trace_id,
                    status="error",
                    payload={"message": f"Error in {event.skill}"}
                )
                error_events.append(error_event)
            else:
                error_events.append(event)
        
        return error_events
    
    def inject_model_drift(self, events: List[LogEventCreate], drift_rate: float = 0.05) -> List[LogEventCreate]:
        """Inject model drift by changing providers within traces."""
        drift_events = []
        providers = ["openai", "gemini", "anthropic"]
        
        for event in events:
            if random.random() < drift_rate:
                # Change provider (simulated by changing trace_id suffix)
                if event.trace_id:
                    new_provider = random.choice(providers)
                    event.trace_id = f"{event.trace_id}_{new_provider}"
            drift_events.append(event)
        
        return drift_events
    
    def inject_latency_spikes(self, events: List[LogEventCreate], spike_rate: float = 0.05) -> List[LogEventCreate]:
        """Inject latency spikes (> 5 seconds)."""
        spike_events = []
        
        for event in events:
            if random.random() < spike_rate:
                spike_event = LogEventCreate(
                    timestamp=event.timestamp,
                    event_type=event.event_type,
                    skill=event.skill,
                    latency_ms=random.randint(5000, 10000),  # 5-10 seconds
                    trace_id=event.trace_id,
                    status=event.status,
                    payload=event.payload
                )
                spike_events.append(spike_event)
            else:
                spike_events.append(event)
        
        return spike_events
