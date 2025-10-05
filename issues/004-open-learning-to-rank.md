# Issue #004: Implement Learning to Rank (LTR) for Search Results

**Status**: Open
**Priority**: Low (Future Enhancement)
**Created**: 2025-10-04
**Assigned**: Unassigned

## Description

Implement a Machine Learning-based Learning to Rank (LTR) system to automatically learn optimal search result rankings from user feedback and interaction data. This would replace the current simple score boosting with a sophisticated ML model that combines multiple relevance signals.

## Problem

**Current System (Simple Boosting)**:
- Uses fixed formula: `final_score = BM25_score × (1.0 + net_votes × 0.1)`
- Single signal (thumbs up/down)
- Manual tuning required
- Global boost per page (not query-specific)
- Cannot learn complex relevance patterns

**Limitations**:
- A page that's great for "motor replacement" but bad for "oil filter" gets conflicting feedback
- Cannot combine multiple signals (BM25, feedback, CTR, dwell time, etc.)
- No automatic optimization of ranking weights

## Proposed Solution

Implement a full Learning to Rank pipeline with three main components:

### 1. Feature Engineering
Extract multiple relevance signals:

**Query Features**:
- Query length (word count)
- Has part number (boolean)
- Has model number (boolean)
- Query type classification (technical, general, part lookup)

**Document Features**:
- BM25 score (baseline relevance)
- Page number (position in document)
- Document length (total pages)
- Category (maintenance, operations, spare_parts)
- Has tables/images (structure indicators)
- Document age (days since upload)

**Query-Document Interaction**:
- Exact phrase match (boolean)
- Term match count (how many query words matched)
- Field match indicators (which fields matched: title, content, summary, part_numbers)
- Term proximity score (how close together are matches)

**Historical Features** (from user behavior):
- Click-through rate (CTR): `clicks / impressions`
- Positive feedback rate: `thumbs_up / total_feedback`
- Negative feedback rate: `thumbs_down / total_feedback`
- Average dwell time (seconds spent viewing)
- Bounce rate (immediately returned to search)
- Total impressions (times shown in results)

**Context Features**:
- Result position (where shown in list)
- Time of day (morning, afternoon, evening)
- User role (optional: sales_agent, technician, manager)

### 2. Training Data Collection

**Implicit Labels from User Behavior**:
```python
Label 2 (Highly Relevant):
  - Thumbs up + clicked + dwell time >30s

Label 1 (Somewhat Relevant):
  - Clicked + dwell time >10s (no explicit feedback)

Label 0 (Not Relevant):
  - Thumbs down OR (clicked + dwell time <5s)

Label -1 (Unknown):
  - Shown but not clicked, no feedback
  - Exclude from training
```

**Minimum Data Requirements**:
- 100+ unique queries with feedback
- 500+ labeled query-document pairs
- Ongoing collection for model updates

### 3. Model Selection

**Option A: LambdaMART (Recommended)**
- Gradient Boosted Decision Trees for ranking
- Industry standard (used by Bing, Yahoo)
- Works well with sparse data
- Interpretable (feature importance)
- Fast inference (~5-10ms)

**Option B: RankNet (Neural Network)**
- Deep learning pairwise ranking
- Better with large datasets (>10K queries)
- Captures complex non-linear patterns
- Black box (harder to debug)

**Option C: Elasticsearch LTR Plugin**
- Native Elasticsearch integration
- Uses uploaded feature sets and models
- Seamless with existing infrastructure
- Requires Elasticsearch 7.0+

### 4. Implementation Phases

#### **Phase 1: Data Collection & Infrastructure** (2-3 weeks)
- [ ] Add click tracking to search UI
- [ ] Add dwell time tracking (time on page)
- [ ] Extend feedback table with additional fields:
  - `clicked` (boolean)
  - `dwell_time_seconds` (integer)
  - `result_position` (integer - where shown in list)
  - `timestamp` (already exists)
- [ ] Create `search_impressions` table to track what was shown
- [ ] Build ETL pipeline to extract features from logs
- [ ] Create feature extraction service

#### **Phase 2: Feature Engineering** (2-3 weeks)
- [ ] Implement feature extractors for all feature types
- [ ] Create feature storage (PostgreSQL table or cache)
- [ ] Build feature logging during search
- [ ] Validate feature quality (no nulls, correct ranges)
- [ ] Create feature documentation

#### **Phase 3: Model Training Pipeline** (3-4 weeks)
- [ ] Set up ML training environment (Python, scikit-learn, LightGBM)
- [ ] Implement label generation from user behavior
- [ ] Create train/validation/test split
- [ ] Train initial LambdaMART model
- [ ] Evaluate with ranking metrics (NDCG, MAP, MRR)
- [ ] Hyperparameter tuning
- [ ] Create model versioning system

#### **Phase 4: Integration & Deployment** (2-3 weeks)
- [ ] Create model serving API (FastAPI endpoint or inline)
- [ ] Update SearchService to use LTR scores
- [ ] Implement A/B testing framework
- [ ] Deploy model to production
- [ ] Monitor performance metrics
- [ ] Create model update schedule (weekly/monthly retraining)

#### **Phase 5: Monitoring & Iteration** (Ongoing)
- [ ] Build analytics dashboard for model performance
- [ ] Track online metrics (CTR, conversion, user satisfaction)
- [ ] Compare LTR vs baseline (simple boosting)
- [ ] Continuous model improvement based on new data
- [ ] Feature engineering iteration

## Technical Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Search Request                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Elasticsearch BM25 Search                       │
│              (Retrieve top 100 candidates)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Feature Extraction Service                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ For each result, extract:                            │  │
│  │  - BM25 score                                        │  │
│  │  - Historical features (from PostgreSQL)             │  │
│  │  - Query-doc interaction features                    │  │
│  │  - Context features                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   LTR Model Inference                        │
│         model.predict(features) → relevance_score            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Re-rank Results                             │
│           Sort by LTR score (descending)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Return Top N Results to User                    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Log Impressions & User Actions                  │
│     (for next training cycle)                                │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema Extensions

**New Table: `search_impressions`**
```sql
CREATE TABLE search_impressions (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    document_id VARCHAR(36) REFERENCES documents(id),
    page INTEGER NOT NULL,
    position INTEGER NOT NULL,           -- Position in results (1, 2, 3...)
    bm25_score FLOAT NOT NULL,
    ltr_score FLOAT,                     -- NULL if LTR not yet deployed
    clicked BOOLEAN DEFAULT FALSE,
    dwell_time_seconds INTEGER,          -- NULL until page exit
    session_id VARCHAR(36),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_impressions_query ON search_impressions(query);
CREATE INDEX idx_impressions_doc_page ON search_impressions(document_id, page);
CREATE INDEX idx_impressions_timestamp ON search_impressions(timestamp);
```

**Extend: `search_feedback` table**
```sql
ALTER TABLE search_feedback ADD COLUMN result_position INTEGER;
ALTER TABLE search_feedback ADD COLUMN clicked BOOLEAN DEFAULT FALSE;
ALTER TABLE search_feedback ADD COLUMN dwell_time_seconds INTEGER;
```

**New Table: `ltr_features`** (cached features)
```sql
CREATE TABLE ltr_features (
    document_id VARCHAR(36) NOT NULL,
    page INTEGER NOT NULL,
    query_hash VARCHAR(64) NOT NULL,     -- Hash of normalized query
    features JSONB NOT NULL,             -- All extracted features
    computed_at TIMESTAMP NOT NULL,
    PRIMARY KEY (document_id, page, query_hash)
);

CREATE INDEX idx_ltr_features_query ON ltr_features(query_hash);
```

## Evaluation Metrics

### Offline Metrics (Training/Validation)
- **NDCG@10** (Normalized Discounted Cumulative Gain): Measures ranking quality
- **MAP** (Mean Average Precision): Average precision across all queries
- **MRR** (Mean Reciprocal Rank): How quickly user finds first relevant result

### Online Metrics (Production)
- **Click-Through Rate (CTR)**: % of searches that result in clicks
- **Time to First Click**: How fast users find what they need
- **Session Success Rate**: % of sessions ending with positive feedback
- **Average Dwell Time**: Time spent on clicked results
- **Bounce Rate**: % returning to search immediately

### A/B Testing
- Control: Current simple boosting
- Treatment: LTR model
- Measure: CTR, satisfaction, conversion
- Decision: Deploy if >10% improvement on key metrics

## Technical Considerations

### Performance
- **Feature extraction**: 5-10ms per result (batch processing)
- **Model inference**: 5-10ms for 100 candidates
- **Total overhead**: 10-20ms added to search latency
- **Mitigation**: Cache features, use efficient model format (ONNX)

### Scalability
- **Training data growth**: ~1GB/month with 1000 queries/day
- **Model size**: 10-50MB (LambdaMART)
- **Retraining frequency**: Weekly or monthly
- **Feature computation**: Pre-compute and cache when possible

### Model Maintenance
- **Model drift**: Performance degrades as user behavior changes
- **Monitoring**: Track online metrics daily
- **Retraining triggers**:
  - Performance drops >5%
  - New document types added
  - Scheduled monthly updates

### Data Quality
- **Label noise**: Users sometimes give wrong feedback
- **Selection bias**: Only clicked results get dwell time data
- **Cold start**: New documents have no historical features
- **Mitigation**: Use smoothing, fallback to BM25 for new docs

## Dependencies

**Software**:
- Python ML libraries: `lightgbm`, `scikit-learn`, `pandas`, `numpy`
- Model serving: `onnx`, `onnxruntime` (optional, for faster inference)
- Elasticsearch LTR plugin (optional): `ltr-query-dsl`

**Data Requirements**:
- Minimum 100 queries with feedback
- Minimum 500 labeled query-document pairs
- 2-4 weeks of user interaction logs

**Infrastructure**:
- Training environment (can be separate from production)
- Model storage (S3 or local filesystem)
- Feature cache (Redis or PostgreSQL)

## Acceptance Criteria

### Minimum Viable LTR (Phase 1-4)
- [ ] Click tracking implemented in UI
- [ ] Dwell time tracking implemented
- [ ] Training data collection pipeline working
- [ ] Feature extraction for all feature types
- [ ] LambdaMART model trained with NDCG@10 >0.7
- [ ] Model integrated into SearchService
- [ ] A/B testing shows >10% CTR improvement vs baseline
- [ ] Model retraining pipeline automated

### Advanced Features (Future)
- [ ] Query normalization and clustering
- [ ] Personalization (user-specific features)
- [ ] Multi-objective optimization (relevance + diversity)
- [ ] Real-time model updates (online learning)
- [ ] Elasticsearch LTR plugin integration

## Risks & Mitigations

### Risk 1: Insufficient Training Data
- **Impact**: Model underfits, poor performance
- **Mitigation**:
  - Start collecting data immediately
  - Use data augmentation techniques
  - Fall back to simple boosting until enough data

### Risk 2: Feature Engineering Complexity
- **Impact**: Slow development, bugs in features
- **Mitigation**:
  - Start with simple features (BM25 + feedback only)
  - Iteratively add features
  - Extensive testing and validation

### Risk 3: Model Performance Worse Than Baseline
- **Impact**: Users see worse results
- **Mitigation**:
  - Thorough A/B testing before full rollout
  - Keep simple boosting as fallback
  - Gradual rollout (10% → 50% → 100%)

### Risk 4: Increased Latency
- **Impact**: Slow search experience
- **Mitigation**:
  - Cache features aggressively
  - Use efficient model format (ONNX)
  - Asynchronous feature computation
  - Monitor p95 latency

### Risk 5: Model Maintenance Burden
- **Impact**: Model degrades, requires constant attention
- **Mitigation**:
  - Automate retraining pipeline
  - Set up monitoring alerts
  - Document processes thoroughly

## Cost Estimate

**Development Time**: 10-15 weeks (2.5-3.5 months)
- Phase 1: 3 weeks
- Phase 2: 3 weeks
- Phase 3: 4 weeks
- Phase 4: 3 weeks
- Phase 5: Ongoing

**Infrastructure Costs**: ~$50-100/month additional
- Training compute (periodic)
- Feature storage (PostgreSQL/Redis)
- Model storage (S3)

**Maintenance**: 4-8 hours/month
- Model retraining
- Performance monitoring
- Feature updates

## Success Criteria

LTR is successful if, after 3 months in production:

1. **Online Metrics**:
   - CTR improves by >10%
   - Average dwell time increases >15%
   - Positive feedback rate increases >20%

2. **Offline Metrics**:
   - NDCG@10 >0.75
   - MRR >0.6

3. **User Satisfaction**:
   - User complaints about search quality decrease
   - Qualitative feedback is positive

## Related Issues

- #001: User feedback system (completed) - Provides training data
- #003: Client-side filtering (open) - Can be combined with LTR

## References

**Academic Papers**:
- "Learning to Rank for Information Retrieval" (Liu, 2009)
- "From RankNet to LambdaRank to LambdaMART" (Burges, 2010)

**Implementation Guides**:
- Elasticsearch Learning to Rank Plugin: https://elasticsearch-learning-to-rank.readthedocs.io/
- LightGBM Ranker: https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMRanker.html

**Industry Examples**:
- Bing: Uses LambdaMART
- Airbnb: LTR for search ranking
- Etsy: Learning to rank blog series
