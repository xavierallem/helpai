# Hybrid RAG Configuration Guide

## Overview

The system now supports **Hybrid RAG** with **reranking** for improved retrieval quality. Hybrid RAG combines:

1. **Dense Retrieval** (Vector/Semantic Search) - Uses ChromaDB with sentence embeddings
2. **Sparse Retrieval** (Keyword/BM25 Search) - Uses BM25 algorithm for keyword matching
3. **Reranking** - Uses FlashRank cross-encoder to rerank combined results

## Architecture

```
Query → Dense Search (ChromaDB)    ─┐
                                     ├─→ RRF Fusion → Reranking → Top-K Results
Query → Sparse Search (BM25)       ─┘
```

### Reciprocal Rank Fusion (RRF)

Results from dense and sparse retrieval are merged using RRF:

```
score(doc) = Σ (weight / (k + rank(doc)))
```

Where:
- `k` = RRF constant (default: 60)
- `rank` = position in the ranked list
- `weight` = configurable weight for each retrieval method

## Configuration

All settings can be configured via environment variables or the `.env` file:

### Enable/Disable Features

```bash
# Enable hybrid search (default: True)
ENABLE_HYBRID_SEARCH=true

# Enable reranking (default: True)
ENABLE_RERANKING=true
```

### Reranking Model

Choose from available FlashRank models:

```bash
# Reranking model (default: ms-marco-MiniLM-L-12-v2)
RERANKER_MODEL=ms-marco-MiniLM-L-12-v2

# Other options:
# - ms-marco-MiniLM-L-12-v2 (balanced speed/quality, recommended)
# - ms-marco-MultiBERT-L-12 (multilingual support)
# - rank-T5-flan (higher quality, slower)
```

### Retrieval Parameters

```bash
# Number of final results to return (default: 5)
NUM_RETRIEVAL_RESULTS=5

# Number of dense (vector) results for fusion (default: 20)
DENSE_RETRIEVAL_TOP_K=20

# Number of sparse (BM25) results for fusion (default: 20)
SPARSE_RETRIEVAL_TOP_K=20
```

### RRF Parameters

```bash
# RRF constant parameter (default: 60)
RRF_K=60

# Weight for dense retrieval (default: 0.5)
DENSE_WEIGHT=0.5

# Weight for sparse retrieval (default: 0.5)
SPARSE_WEIGHT=0.5
```

## Example Configuration

### Scenario 1: Prioritize Semantic Search

```bash
ENABLE_HYBRID_SEARCH=true
ENABLE_RERANKING=true
DENSE_WEIGHT=0.7
SPARSE_WEIGHT=0.3
```

### Scenario 2: Prioritize Keyword Search

```bash
ENABLE_HYBRID_SEARCH=true
ENABLE_RERANKING=true
DENSE_WEIGHT=0.3
SPARSE_WEIGHT=0.7
```

### Scenario 3: Balanced (Default)

```bash
ENABLE_HYBRID_SEARCH=true
ENABLE_RERANKING=true
DENSE_WEIGHT=0.5
SPARSE_WEIGHT=0.5
```

### Scenario 4: Dense Only (Original Behavior)

```bash
ENABLE_HYBRID_SEARCH=false
ENABLE_RERANKING=false
```

## Performance Considerations

### Speed vs Quality Trade-offs

1. **Fastest**: Dense only (`ENABLE_HYBRID_SEARCH=false`)
   - Single vector search
   - ~50-100ms per query

2. **Balanced**: Hybrid with MiniLM reranker (default)
   - Dense + Sparse + Reranking
   - ~150-300ms per query

3. **Highest Quality**: Hybrid with T5 reranker
   - Dense + Sparse + T5 Reranking
   - ~300-500ms per query

### Memory Usage

- **BM25 Index**: ~10-20MB per 10,000 chunks (in-memory)
- **Reranker Model**:
  - MiniLM: ~130MB
  - MultiBERT: ~180MB
  - T5-flan: ~250MB

### Recommendations

- **Small datasets (<1000 docs)**: Use hybrid with reranking
- **Medium datasets (1000-10000 docs)**: Use hybrid with MiniLM reranker
- **Large datasets (>10000 docs)**: Consider dense only or increase candidate sizes
- **Real-time requirements (<100ms)**: Use dense only

## API Usage

### Query Endpoint

```bash
POST /api/query
Content-Type: application/json

{
  "query_text": "What are the contract termination conditions?",
  "session_id": "optional-session-uuid"
}
```

The hybrid search is automatically applied based on configuration settings.

### Response Format

```json
{
  "response_text": "According to the documents...",
  "source_documents": [
    {
      "document_id": "uuid",
      "chunk_id": "chunk-uuid",
      "content": "Relevant text...",
      "page_number": 5,
      "similarity_score": 0.987
    }
  ],
  "session_id": "session-uuid",
  "processing_time_ms": 245.3
}
```

Note: `similarity_score` represents:
- Dense only: Vector similarity (cosine)
- Hybrid: RRF score (pre-reranking) or reranker score (post-reranking)

## Monitoring

Check logs for retrieval method being used:

```
INFO:src.services.query.processor:Using hybrid retrieval (dense + sparse + reranking)
```

Or:

```
INFO:src.services.query.processor:Using dense retrieval only
```

## Testing

Run the test suite to verify the implementation:

```bash
python test_hybrid_rag.py
```

Expected output:
```
Testing BM25 Retriever... ✓
Testing Reranker... ✓
Testing Hybrid Retriever... ✓
All tests passed! ✓
```

## Troubleshooting

### Issue: Slow queries

- Reduce `DENSE_RETRIEVAL_TOP_K` and `SPARSE_RETRIEVAL_TOP_K` (e.g., to 10)
- Disable reranking: `ENABLE_RERANKING=false`
- Use faster reranker model: `RERANKER_MODEL=ms-marco-MiniLM-L-12-v2`

### Issue: Poor retrieval quality

- Enable hybrid search: `ENABLE_HYBRID_SEARCH=true`
- Enable reranking: `ENABLE_RERANKING=true`
- Increase candidate sizes: `DENSE_RETRIEVAL_TOP_K=30`, `SPARSE_RETRIEVAL_TOP_K=30`
- Use better reranker: `RERANKER_MODEL=rank-T5-flan`

### Issue: High memory usage

- Disable hybrid search: `ENABLE_HYBRID_SEARCH=false`
- Use smaller reranker: `RERANKER_MODEL=ms-marco-MiniLM-L-12-v2`

## Implementation Details

### New Components

1. **BM25Retriever** (`src/services/retrieval/bm25_retriever.py`)
   - Tokenizes and indexes all document chunks
   - Provides BM25 keyword search
   - Automatically synced with ChromaDB operations

2. **Reranker** (`src/services/retrieval/reranker.py`)
   - Uses FlashRank for fast cross-encoder reranking
   - Loads model on initialization
   - Provides fallback if model fails to load

3. **HybridRetriever** (`src/services/retrieval/hybrid_retriever.py`)
   - Implements RRF fusion algorithm
   - Coordinates dense, sparse, and reranking steps
   - Configurable weights and parameters

### Updated Components

- **ChromaDBClient**: Now manages BM25 index alongside vector store
- **QueryProcessor**: Routes queries through hybrid retrieval when enabled
- **Settings**: New configuration parameters for hybrid RAG

## Benefits of Hybrid RAG

1. **Better Recall**: Combines semantic and keyword matching
2. **Improved Ranking**: Cross-encoder reranking for relevance
3. **Robust**: Handles both conceptual and exact-match queries
4. **Flexible**: Configurable weights and parameters
5. **Fallback**: Gracefully degrades to dense-only if hybrid fails

## Next Steps

1. Monitor query performance and adjust parameters
2. Experiment with different reranker models
3. Fine-tune RRF weights for your use case
4. Consider caching for frequently asked questions
