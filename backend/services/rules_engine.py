"""
Rules Engine for deterministic scoring and ranking of candidates.
Hotfix 33: Hardened Budget Logic.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.data.database import Memory
from backend.data.schemas import CandidateAnalysis, ExtractedFact

logger = logging.getLogger("janus_backend")

def _extract_semantic_features(facts: List[Dict]) -> Dict[str, float]:
    features = {
        'priority_performance': 0.0,
        'priority_cost_efficiency': 0.0,
        'priority_scalability': 0.0,
        'priority_security': 0.0,
        'priority_maintainability': 0.0,
        'priority_longterm_support': 0.0,
        'budget_small': 0.0,
        'budget_medium': 0.0,
        'budget_large': 0.0,
        'budget_constrained': 0.0,
    }
    
    if not facts: return features
    
    predicate_mappings = {
        ('hat_prioritaet', 'leistung'): ('priority_performance', 1.0),
        ('hat_prioritaet', 'performance'): ('priority_performance', 1.0),
        ('hat_prioritaet', 'geschwindigkeit'): ('priority_performance', 1.0),
        ('hat_budget', 'niedrig'): [('budget_small', 1.0)],
        ('hat_budget', 'klein'): [('budget_small', 1.0)],
        ('hat_technologie', 'lts'): ('priority_longterm_support', 1.0),
    }
    
    text_patterns = {
        r'(?i)(hohe?|starke?|maximale?)\s+(leistung|performance|geschwindigkeit)': 'priority_performance',
        r'(?i)(klein[er]?|niedrig[er]?|begrenzt[er]?)\s+(budget|kosten)': 'budget_small',
        r'(?i)(langzeit|support|lts|stabil)': 'priority_longterm_support',
    }
    
    for fact in facts:
        if not isinstance(fact, dict): continue
        canonical_key = fact.get('canonical_key', '').lower().strip()
        fact_text = (fact.get('fact') or fact.get('text') or '').lower().strip()
        
        print(f"DEBUG: Analyzing Fact -> Key: '{canonical_key}', Text: '{fact_text}'")

        if canonical_key:
            key_parts = [p.strip() for p in canonical_key.split('|')]
            if len(key_parts) >= 2:
                predicate, value = key_parts[0], key_parts[-1]
                mapping = predicate_mappings.get((predicate, value))
                if mapping:
                    if isinstance(mapping, tuple):
                        features[mapping[0]] = max(features[mapping[0]], mapping[1])
                    elif isinstance(mapping, list):
                        for feat, weight in mapping:
                            features[feat] = max(features[feat], weight)

        if fact_text:
            for pattern, feature in text_patterns.items():
                import re
                if re.search(pattern, fact_text):
                    features[feature] = max(features[feature], 0.8)

    return features

def _generate_reasoning_summary(features: Dict[str, float]) -> Dict:
    reasoning_parts = []
    if features['priority_performance'] > 0.2: reasoning_parts.append("Fokus auf Leistung")
    if features['budget_small'] > 0.3: reasoning_parts.append("begrenztes Budget")
    return {'reasoning_summary': ", ".join(reasoning_parts)}

def _generate_synthetic_candidates(query_context: str) -> List[Dict]:
    if not query_context: return []
    query_lower = query_context.lower()
    synthetic_candidates = []
    
    if any(term in query_lower for term in ['datenbank', 'db', 'sql', 'nosql', 'speicher']):
        synthetic_candidates.append({
            'candidate_identifier': 'db:sql',
            'candidate_name': 'SQL-Datenbank',
            'is_viable': True,
            'reasoning_summary': 'Standard.',
            'pros': [],
            'cons': [],
            'final_score': 70.0,
            'metadata': {'features': {'performance': 0.6, 'cost': 0.9, 'support': 1.0}}
        })
        synthetic_candidates.append({
            'candidate_identifier': 'db:in_memory',
            'candidate_name': 'In-Memory-Datenbank',
            'is_viable': True,
            'reasoning_summary': 'Schnell.',
            'pros': [],
            'cons': [],
            'final_score': 60.0,
            'metadata': {'features': {'performance': 1.0, 'cost': 0.2, 'support': 0.5}}
        })
    return synthetic_candidates

def score_and_rank_candidates_from_keys(
    relevant_keys: List[str], 
    db: Session,
    query_context: str = "",
    direct_facts: Optional[List[Any]] = None
) -> List[Dict]:
    all_facts_dicts = []
    
    if relevant_keys:
        try:
            db_facts = db.query(Memory).filter(Memory.normalized_text.in_(relevant_keys)).all()
            for mem in db_facts:
                all_facts_dicts.append(json.loads(mem.snippet))
        except: pass
            
    if direct_facts:
        for f in direct_facts:
            if hasattr(f, 'dict'): f_dict = f.dict()
            elif hasattr(f, 'model_dump'): f_dict = f.model_dump()
            elif isinstance(f, dict): f_dict = f
            else: f_dict = {'canonical_key': getattr(f, 'canonical_key', ''), 'fact': getattr(f, 'fact', '')}
            all_facts_dicts.append(f_dict)
    
    project_features = _extract_semantic_features(all_facts_dicts)
    print(f"DEBUG: Extracted Features: {project_features}")

    candidates = _generate_synthetic_candidates(query_context)
    result_candidates = []
    
    for cand in candidates:
        cand_score = cand.get('final_score', 50.0)
        cand_feats = cand.get('metadata', {}).get('features', {})
        
        # 1. Performance Bonus
        if project_features.get('priority_performance', 0) > 0.2:
            perf_bonus = cand_feats.get('performance', 0.5) * 30
            cand_score += perf_bonus
            print(f"  -> {cand['candidate_name']} Perf Bonus: +{perf_bonus}")

        # 2. Budget Logic (HOTFIX 33)
        # Wenn Budget klein ist -> Teure Lösungen bestrafen, günstige belohnen
        if project_features.get('budget_small', 0) > 0.5:
            cost_efficiency = cand_feats.get('cost', 0.5)
            
            # Teuer (z.B. In-Memory: 0.2)
            if cost_efficiency < 0.4:
                malus = 40 # Strafe erhöht
                cand_score -= malus
                cand['cons'].append({'type': 'budget', 'description': 'Zu teuer für das Budget.', 'severity': 'high'})
                print(f"  -> {cand['candidate_name']} Budget Malus: -{malus}")
                
            # Günstig (z.B. SQL: 0.9)
            elif cost_efficiency > 0.7:
                bonus = 25
                cand_score += bonus
                cand['pros'].append({'type': 'budget', 'description': 'Passt perfekt ins Budget.', 'severity': 'high'})
                print(f"  -> {cand['candidate_name']} Budget Bonus: +{bonus}")
        
        # 3. Support Logic
        if project_features.get('priority_longterm_support', 0) > 0.5:
            support = cand_feats.get('support', 0.5)
            if support > 0.8:
                cand_score += 15
                cand['pros'].append({'type': 'support', 'description': 'LTS verfügbar.', 'severity': 'medium'})

        cand['final_score'] = max(0, min(100, cand_score))
        result_candidates.append(CandidateAnalysis(**cand))
        
    result_candidates.sort(key=lambda x: x.final_score, reverse=True)
    return result_candidates