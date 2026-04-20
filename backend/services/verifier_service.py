"""
Verification service for ensuring the integrity of decision context evidence.

This module provides functionality to validate that all evidence keys referenced in
decision context claims actually exist in the retrieved facts, preventing hallucinations.
"""

import logging
from typing import List, Set

from backend.data.schemas import DecisionContext, ExtractedFact

logger = logging.getLogger("janus_backend")


def verify_decision_integrity(
    decision: DecisionContext, 
    retrieved_facts: List[ExtractedFact]
) -> DecisionContext:
    """
    Verifies that all evidence keys in the decision context exist in the retrieved facts.
    
    Args:
        decision: The decision context to verify
        retrieved_facts: List of facts retrieved from the database
        
    Returns:
        The verified decision context with invalid claims removed
    """
    # 1. Create a set of all available fact keys for O(1) lookup
    available_keys: Set[str] = {fact.canonical_key for fact in retrieved_facts}
    
    # 2. Check all recommendations in the decision
    for candidate in decision.recommendations:
        # Check pros
        valid_pros = []
        for claim in candidate.pros:
            # A claim is valid only if ALL its evidence keys exist
            if all(key in available_keys for key in claim.evidence_keys):
                valid_pros.append(claim)
            else:
                logger.warning(
                    f"[VERIFIER] Hallucination detected! Claim '{claim.claim_description}' "
                    f"references missing keys: {claim.evidence_keys}"
                )
        
        candidate.pros = valid_pros

        # Check cons
        valid_cons = []
        for claim in candidate.cons:
            if all(key in available_keys for key in claim.evidence_keys):
                valid_cons.append(claim)
            else:
                logger.warning(
                    f"[VERIFIER] Hallucination detected! Claim '{claim.claim_description}' "
                    f"references missing keys: {claim.evidence_keys}"
                )
        
        candidate.cons = valid_cons

        # Log if a candidate has no valid claims left after verification
        if not candidate.pros and not candidate.cons:
            logger.info(
                f"[VERIFIER] Candidate {candidate.candidate_name} has no valid claims "
                "after verification."
            )

    return decision

async def verify_vision_memory_consistency(vision_desc: str, facts: List[ExtractedFact], api_key: str, provider: str) -> List[str]:
    """Prüft semantisch, ob Bildbeschreibung und Fakten sich widersprechen."""
    if not facts or not vision_desc: return []
    
    from backend.services import llm_gateway
    fact_list = "\n".join([f"- {f.canonical_key}: {f.fact}" for f in facts])
    prompt = (
        f"BILDANALYSE: {vision_desc}\n\n"
        f"GESPEICHERTE FAKTEN:\n{fact_list}\n\n"
        f"Gibt es HARTE Widersprüche (z.B. anderes Geschlecht, andere Tierart, andere Haarfarbe)?\n"
        f"Antworte NUR mit den betroffenen canonical_keys, getrennt durch Komma. Wenn keine Widersprüche vorliegen, antworte mit 'OK'."
    )
    
    try:
        # Nutze ein schnelles Modell für diese interne Prüfung
        model = "gpt-5.4-nano" if provider == "openai" else "gemini-3-flash-preview"
        resp = await llm_gateway.get_provider(provider).generate_response(
            api_key=api_key, model=model, 
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.get("text", "").strip()
        if "OK" in raw: return []
        return [key.strip() for key in raw.split(",")]
    except:
        return []