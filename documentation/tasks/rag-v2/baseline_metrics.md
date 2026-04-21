# RAG V1 Baseline Metrics
Generated: 2026-04-22 00:03:45

## Context Note
**Legacy Index State:** The baseline was measured against the current production ChromaDB index which contains:
- `janus_global_documents`: 1 PDF document (die.pdf - Skandinavien-Analyse)
- `janus_skill_index`: 66 skill definitions

The golden queries were adjusted to match this actual content (5 PDF queries + 25 skill queries). The baseline metrics reflect the current limited state of the legacy index. As V2 implementation progresses, this baseline will serve as the regression gate to ensure V2 does not degrade existing functionality.

## Overall Metrics
- **MRR@10**: 0.1724
- **Recall@5**: 0.1724
- **P@1**: 0.1724
- **Total Queries**: 29

## Metrics by Query Type
### PROSE (n=5)
- MRR@10: 1.0000
- Recall@5: 1.0000
- P@1: 1.0000

### CODE (n=24)
- MRR@10: 0.0000
- Recall@5: 0.0000
- P@1: 0.0000

## Detailed Results

| Query | Type | MRR | Recall@5 | P@1 | Time (s) | Relevant Ranks |
|-------|------|-----|----------|-----|---------|----------------|
| Skandinavien Hauptstadt | prose | 1.0000 | 1.0000 | 1.0000 | 8.674 | [1] |
| Schweden Hauptstadt Stockholm | prose | 1.0000 | 1.0000 | 1.0000 | 0.028 | [1] |
| Bevoelkerung Skandinavien | prose | 1.0000 | 1.0000 | 1.0000 | 0.032 | [1] |
| Hauptstaedte Skandinavien | prose | 1.0000 | 1.0000 | 1.0000 | 0.042 | [1] |
| Recherchierte Kerndaten | prose | 1.0000 | 1.0000 | 1.0000 | 0.041 | [1] |
| Skill knowledge query | code | 0.0000 | 0.0000 | 0.0000 | 0.036 | None |
| Skill filesystem find files | code | 0.0000 | 0.0000 | 0.0000 | 0.044 | None |
| Skill memory recall | code | 0.0000 | 0.0000 | 0.0000 | 0.032 | None |
| Skill video transcript | code | 0.0000 | 0.0000 | 0.0000 | 0.028 | None |
| Skill web search | code | 0.0000 | 0.0000 | 0.0000 | 0.028 | None |
| Skill rag query | code | 0.0000 | 0.0000 | 0.0000 | 0.029 | None |
| Skill pdf generator | code | 0.0000 | 0.0000 | 0.0000 | 0.108 | None |
| Skill execution engine | code | 0.0000 | 0.0000 | 0.0000 | 0.039 | None |
| Skill orchestrator | code | 0.0000 | 0.0000 | 0.0000 | 0.025 | None |
| Skill memory save | code | 0.0000 | 0.0000 | 0.0000 | 0.027 | None |
| Skill memory extract | code | 0.0000 | 0.0000 | 0.0000 | 0.031 | None |
| Skill project | code | 0.0000 | 0.0000 | 0.0000 | 0.028 | None |
| Skill video player | code | 0.0000 | 0.0000 | 0.0000 | 0.028 | None |
| Skill image analysis | code | 0.0000 | 0.0000 | 0.0000 | 0.028 | None |
| Skill audio | code | 0.0000 | 0.0000 | 0.0000 | 0.027 | None |
| Skill code | code | 0.0000 | 0.0000 | 0.0000 | 0.027 | None |
| Skill file system | code | 0.0000 | 0.0000 | 0.0000 | 0.026 | None |
| Skill database | code | 0.0000 | 0.0000 | 0.0000 | 0.025 | None |
| Skill api | code | 0.0000 | 0.0000 | 0.0000 | 0.026 | None |
| Skill router | code | 0.0000 | 0.0000 | 0.0000 | 0.022 | None |
| Skill selector | code | 0.0000 | 0.0000 | 0.0000 | 0.026 | None |
| Skill tool | code | 0.0000 | 0.0000 | 0.0000 | 0.024 | None |
| Skill workflow | code | 0.0000 | 0.0000 | 0.0000 | 0.026 | None |
| Skill integration | code | 0.0000 | 0.0000 | 0.0000 | 0.026 | None |