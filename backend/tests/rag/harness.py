"""
RAG V2 Eval Harness

Baseline metrics for the current knowledge.query pipeline.
Calculates MRR@10, Recall@5, and P@1 against golden queries.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from backend.utils.paths import get_app_data_dir
from chromadb.utils import embedding_functions

logger = logging.getLogger("janus_backend")

# Constants from legacy RAG
CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "janus_global_documents"


def get_embedding_function():
    """Lazy load embedding function."""
    global _embedding_function
    if _embedding_function is None:
        logger.info(f"Loading embedding model '{EMBEDDING_MODEL}'...")
        _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
    return _embedding_function


_embedding_function = None


def load_golden_queries(jsonl_path: str) -> List[Dict[str, Any]]:
    """Load golden queries from JSONL file."""
    queries = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    logger.info(f"Loaded {len(queries)} golden queries")
    return queries


def query_collection(query_text: str, n_results: int = 10) -> Dict[str, Any]:
    """Query the legacy ChromaDB collection (read-only)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
    )
    
    return results


def is_relevant(result_metadata: Dict[str, Any], expected_paths: List[str]) -> bool:
    """Check if a result is relevant based on expected file paths or skill IDs."""
    # Check filename (for PDF documents)
    source = result_metadata.get("filename", "")
    for expected in expected_paths:
        if expected in source or source in expected:
            return True
    
    # Check skill_id (for skill routing index)
    skill_id = result_metadata.get("skill_id", "")
    for expected in expected_paths:
        if "janus_skill_index" in expected and skill_id:
            return True
    
    return False


def calculate_metrics(
    queries: List[Dict[str, Any]],
    n_results: int = 10
) -> Dict[str, Any]:
    """Calculate MRR@10, Recall@5, P@1 for all queries."""
    mrr_scores = []
    recall_at_5_scores = []
    precision_at_1_scores = []
    
    results_by_query = []
    
    for i, query in enumerate(queries):
        query_text = query["query"]
        expected_paths = query["expected_paths"]
        min_rank = query.get("min_rank", 5)
        query_type = query.get("query_type", "unknown")
        
        logger.info(f"Query {i+1}/{len(queries)} [{query_type}]: {query_text}")
        
        start = time.perf_counter()
        results = query_collection(query_text, n_results=n_results)
        elapsed = time.perf_counter() - start
        
        metadatas = results.get("metadatas", [[]])[0]
        
        # Calculate metrics for this query
        relevant_ranks = []
        for rank, metadata in enumerate(metadatas[:n_results], start=1):
            if is_relevant(metadata, expected_paths):
                relevant_ranks.append(rank)
        
        # MRR@10
        if relevant_ranks:
            mrr = 1.0 / relevant_ranks[0]
        else:
            mrr = 0.0
        mrr_scores.append(mrr)
        
        # Recall@5
        relevant_in_top_5 = sum(1 for rank in relevant_ranks if rank <= 5)
        recall_at_5 = relevant_in_top_5 / len(expected_paths) if expected_paths else 0.0
        recall_at_5_scores.append(recall_at_5)
        
        # P@1
        precision_at_1 = 1.0 if relevant_ranks and relevant_ranks[0] == 1 else 0.0
        precision_at_1_scores.append(precision_at_1)
        
        results_by_query.append({
            "query": query_text,
            "query_type": query_type,
            "expected_paths": expected_paths,
            "relevant_ranks": relevant_ranks,
            "mrr": mrr,
            "recall_at_5": recall_at_5,
            "precision_at_1": precision_at_1,
            "elapsed_seconds": elapsed,
        })
        
        logger.info(f"  MRR: {mrr:.4f}, Recall@5: {recall_at_5:.4f}, P@1: {precision_at_1:.4f}, Time: {elapsed:.3f}s")
    
    # Aggregate metrics
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    avg_recall_at_5 = sum(recall_at_5_scores) / len(recall_at_5_scores) if recall_at_5_scores else 0.0
    avg_precision_at_1 = sum(precision_at_1_scores) / len(precision_at_1_scores) if precision_at_1_scores else 0.0
    
    # Breakdown by query type
    by_type = {}
    for result in results_by_query:
        qtype = result["query_type"]
        if qtype not in by_type:
            by_type[qtype] = {"mrr": [], "recall": [], "precision": []}
        by_type[qtype]["mrr"].append(result["mrr"])
        by_type[qtype]["recall"].append(result["recall_at_5"])
        by_type[qtype]["precision"].append(result["precision_at_1"])
    
    by_type_agg = {}
    for qtype, metrics in by_type.items():
        by_type_agg[qtype] = {
            "mrr": sum(metrics["mrr"]) / len(metrics["mrr"]),
            "recall_at_5": sum(metrics["recall"]) / len(metrics["recall"]),
            "precision_at_1": sum(metrics["precision"]) / len(metrics["precision"]),
            "count": len(metrics["mrr"]),
        }
    
    return {
        "avg_mrr_at_10": avg_mrr,
        "avg_recall_at_5": avg_recall_at_5,
        "avg_precision_at_1": avg_precision_at_1,
        "total_queries": len(queries),
        "by_query_type": by_type_agg,
        "detailed_results": results_by_query,
    }


def generate_report(metrics: Dict[str, Any], output_path: str):
    """Generate baseline metrics report."""
    report_lines = [
        "# RAG V1 Baseline Metrics",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Overall Metrics",
        f"- **MRR@10**: {metrics['avg_mrr_at_10']:.4f}",
        f"- **Recall@5**: {metrics['avg_recall_at_5']:.4f}",
        f"- **P@1**: {metrics['avg_precision_at_1']:.4f}",
        f"- **Total Queries**: {metrics['total_queries']}",
        "",
        "## Metrics by Query Type",
    ]
    
    for qtype, agg in metrics["by_query_type"].items():
        report_lines.extend([
            f"### {qtype.upper()} (n={agg['count']})",
            f"- MRR@10: {agg['mrr']:.4f}",
            f"- Recall@5: {agg['recall_at_5']:.4f}",
            f"- P@1: {agg['precision_at_1']:.4f}",
            "",
        ])
    
    report_lines.extend([
        "## Detailed Results",
        "",
        "| Query | Type | MRR | Recall@5 | P@1 | Time (s) | Relevant Ranks |",
        "|-------|------|-----|----------|-----|---------|----------------|",
    ])
    
    for result in metrics["detailed_results"]:
        query_short = result["query"][:50] + "..." if len(result["query"]) > 50 else result["query"]
        report_lines.append(
            f"| {query_short} | {result['query_type']} | "
            f"{result['mrr']:.4f} | {result['recall_at_5']:.4f} | "
            f"{result['precision_at_1']:.4f} | {result['elapsed_seconds']:.3f} | "
            f"{result['relevant_ranks'] if result['relevant_ranks'] else 'None'} |"
        )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report written to {output_path}")


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Paths
    golden_queries_path = os.path.join(os.path.dirname(__file__), "golden_queries.jsonl")
    report_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "documentation", "tasks", "rag-v2", "baseline_metrics.md")
    
    logger.info("Starting RAG V1 Baseline Evaluation")
    logger.info(f"Golden queries: {golden_queries_path}")
    logger.info(f"Report output: {report_path}")
    
    # Load queries
    queries = load_golden_queries(golden_queries_path)
    
    # Calculate metrics
    logger.info("Calculating metrics...")
    metrics = calculate_metrics(queries, n_results=10)
    
    # Generate report
    logger.info("Generating report...")
    generate_report(metrics, report_path)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("BASELINE METRICS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"MRR@10:        {metrics['avg_mrr_at_10']:.4f}")
    logger.info(f"Recall@5:      {metrics['avg_recall_at_5']:.4f}")
    logger.info(f"P@1:           {metrics['avg_precision_at_1']:.4f}")
    logger.info(f"Total Queries: {metrics['total_queries']}")
    logger.info("=" * 60)
    
    return metrics


if __name__ == "__main__":
    metrics = main()
