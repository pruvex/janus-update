import pytest
from backend.services.rules_engine import score_and_rank_candidates_from_keys

# Helper class to simulate Pydantic/SQLAlchemy objects
class MockFact:
    def __init__(self, canonical_key, fact):
        self.canonical_key = canonical_key
        self.fact = fact
    
    # Simulates .dict() method from Pydantic v1 or Model-Dump
    def dict(self):
        return {"canonical_key": self.canonical_key, "fact": self.fact}
    
    # Simulates attribute access
    def __getitem__(self, item):
        return getattr(self, item)

def test_aquila_scenario_budget_constraint(db_session):
    """
    Scenario: User wants performance but has no budget.
    Expectation: SQL should win against In-Memory (due to cost factor).
    """
    # 1. Setup: Simulate facts
    facts = [
        MockFact("hat_prioritaet|projekt:aquila|leistung", "Performance ist wichtig"),
        MockFact("hat_budget|projekt:aquila|niedrig", "Das Budget ist sehr klein"),
        MockFact("hat_technologie|projekt:aquila|lts", "Wir brauchen Langzeit-Support")
    ]
    
    query = "Soll ich In-Memory oder SQL nutzen?"
    
    # 2. Action: Feed the rules engine
    candidates = score_and_rank_candidates_from_keys(
        relevant_keys=[],
        db=db_session,
        query_context=query,
        direct_facts=facts  # IMPORTANT: Use direct injection
    )
    
    # 3. Assertions (The verification)
    assert len(candidates) >= 2
    
    # Find the candidates in the list
    sql_candidate = next(c for c in candidates if "sql" in c.candidate_identifier)
    in_memory_candidate = next(c for c in candidates if "in_memory" in c.candidate_identifier)
    
    # CHECK: SQL must have a higher score
    print(f"Scores -> SQL: {sql_candidate.final_score}, InMemory: {in_memory_candidate.final_score}")
    assert sql_candidate.final_score > in_memory_candidate.final_score
    
    # CHECK: In-Memory must have a warning about budget
    in_mem_cons = [c['description'] for c in in_memory_candidate.cons]
    assert any("Budget" in con or "teuer" in con for con in in_mem_cons)

def test_startup_scenario_performance_only(db_session):
    """
    Scenario: Money doesn't matter, only speed counts.
    Expectation: In-Memory should win.
    """
    facts = [
        MockFact("hat_prioritaet|projekt:x|leistung", "Maximale Geschwindigkeit"),
        MockFact("hat_budget|projekt:x|hoch", "Budget ist unbegrenzt")
    ]
    
    candidates = score_and_rank_candidates_from_keys(
        relevant_keys=[], 
        db=db_session, 
        query_context="Datenbank Entscheidung", 
        direct_facts=facts
    )
    
    in_memory_candidate = next(c for c in candidates if "in_memory" in c.candidate_identifier)
    
    # CHECK: Score must be very high (>70)
    assert in_memory_candidate.final_score > 70
    assert in_memory_candidate.is_viable is True
