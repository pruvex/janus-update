import logging
from typing import List
from sqlalchemy.orm import Session
import pydantic

from backend.data.schemas import DecisionContext, ExtractedFact, CandidateAnalysis
from backend.services.rules_engine import score_and_rank_candidates_from_keys

logger = logging.getLogger("janus_backend")

# --- FINALER "ZERO-THINKING" PROMPT ---
# (Wird hier aktuell nicht direkt genutzt, bleibt aber für zukünftige Erweiterungen erhalten)
PLANNER_PROMPT_ZERO_THINK = """
Du bist eine Index-Matching-Engine. Deine einzige Aufgabe ist es, die NUMMERN der Fakten zurückzugeben, die zur Benutzeranfrage passen.
"""

def _extract_keywords(text: str) -> List[str]:
    """Extract and normalize keywords from user query for matching."""
    stopwords = {"und", "oder", "der", "die", "das", "ein", "eine", "einen", "dem", "den", 
                "des", "dass", "nicht", "auch", "sich", "ist", "sind", "war", "waren", "wie",
                "zu", "für", "mit", "auf", "an", "in", "von", "bei", "nach", "um", "als"}
    
    text = text.lower()
    for umlaut, replacement in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        text = text.replace(umlaut, replacement)
    
    words = []
    current_word = []
    for char in text:
        if char.isalnum() or char == '_':
            current_word.append(char)
        elif current_word:
            word = ''.join(current_word)
            if word and word not in stopwords and len(word) > 2:
                words.append(word)
            current_word = []
    
    if current_word:
        word = ''.join(current_word)
        if word and word not in stopwords and len(word) > 2:
            words.append(word)
    
    return words

def _get_relevant_indices(user_query: str, facts: List[ExtractedFact]) -> List[int]:
    """Find indices of facts that are relevant to the user query."""
    if not facts:
        return []
    
    query_keywords = _extract_keywords(user_query)
    if not query_keywords:
        return list(range(len(facts)))
    
    scored_facts = []
    for idx, fact in enumerate(facts):
        if not fact.canonical_key:
            continue
            
        fact_text = f"{fact.fact.lower()} {fact.canonical_key.lower()}"
        score = sum(1 for kw in query_keywords if kw in fact_text)
        
        key_parts = fact.canonical_key.lower().split('|')
        score += sum(1 for kw in query_keywords if any(kw in part for part in key_parts))
        
        if score > 0:
            scored_facts.append((idx, score))
    
    scored_facts.sort(key=lambda x: -x[1])
    return [idx for idx, _ in scored_facts]

async def generate_decision_context(
    db: Session,
    user_query: str,
    retrieved_facts: List[ExtractedFact],
    api_key: str,
    provider: str = "openai",
    model: str = "gpt-5-nano",
    query_context: str = "" # <--- PARAMETER HINZUGEFÜGT (Fix für TypeError)
) -> DecisionContext:
    """
    Generate decision context using Zero-Thinking approach + Rules Engine.
    """
    try:
        # Filter valid facts with canonical keys
        valid_facts = [f for f in retrieved_facts if f and f.canonical_key]
        
        if valid_facts:
            logger.info(f"Planner passing {len(valid_facts)} facts to Rules Engine")
        else:
            logger.info("No valid facts found, using synthetic generation")
        
        # Generate candidates and rank them using the rules engine
        ranked_candidates = score_and_rank_candidates_from_keys(
            relevant_keys=[],  # Not needed when using direct_facts
            db=db,
            query_context=query_context or user_query,
            direct_facts=valid_facts  # Pass facts directly to avoid DB lookup
        )
        
        # Handle case where no candidates were generated
        if not ranked_candidates:
            return DecisionContext(
                status="cannot_answer",
                task_summary=user_query,
                analysis_summary="Keine passenden Kandidaten gefunden.",
                recommendations=[]
            )

        # Get the top candidate's name for the summary
        top_candidate = ranked_candidates[0]
        top_name = getattr(top_candidate, 'candidate_name', 'Unbekannt')
        
        return DecisionContext(
            status="ok",
            task_summary=user_query,
            analysis_summary=f"Empfehlung: {top_name}.",
            recommendations=ranked_candidates
        )
        
    except Exception as e:
        logger.error(f"Fehler im Planner Service: {e}", exc_info=True)
        return DecisionContext(
            status="cannot_answer",
            task_summary=user_query,
            analysis_summary=f"Ein interner Fehler ist aufgetreten: {str(e)}",
            recommendations=[]
        )
