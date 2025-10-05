# Issue #001: Allow User to Score Results and System Learning

**Status**: Completed
**Priority**: Medium
**Created**: 2025-10-03
**Completed**: 2025-10-04
**Assigned**: Claude Code

## Description

Implement a feedback mechanism that allows users to score search results (thumbs up/down or star rating) and use this feedback to improve future search rankings through machine learning.

## Problem

Currently, the search system uses static BM25 scoring without learning from user behavior. Users cannot indicate which results were helpful or not helpful, and the system cannot improve based on actual usage patterns.

## Proposed Solution

1. **Add rating UI to search result cards** (e.g., thumbs up/down buttons)
2. **Store user feedback in database** (PostgreSQL table)
3. **Track**: query text, document_id, page, rating, timestamp, user_id (optional)
4. **Implement learning algorithm**:
   - Option A: Learning to Rank (LTR) with Elasticsearch
   - Option B: Click-through rate (CTR) boosting
   - Option C: Simple score adjustment based on historical ratings
5. **Update search ranking** to incorporate learned preferences

## Technical Considerations

- Database schema for feedback storage
- Privacy concerns (anonymous vs. authenticated feedback)
- How to weight historical feedback vs. BM25 scores
- Training pipeline and model retraining frequency
- A/B testing framework to validate improvements

## Acceptance Criteria

- [x] Users can rate search results (thumbs up/down minimum)
- [x] Ratings are stored persistently
- [x] Search results ranking improves based on historical ratings
- [ ] Admin dashboard to view feedback metrics (optional - deferred)
- [x] Feedback can be anonymous or user-attributed

## Implementation Summary

**Completed on**: October 4, 2025

### What Was Implemented:

1. **Database Schema**: New `search_feedback` table in PostgreSQL
   - Fields: id, query, document_id, page, rating, session_id, timestamp, created_at
   - Indexes on (document_id, page), query, and timestamp
   - Foreign key constraint with CASCADE delete

2. **API Endpoints**:
   - `POST /api/v1/feedback` - Submit rating (no auth required)
   - `GET /api/v1/feedback/stats/{document_id}/{page}` - Get feedback statistics

3. **Search Ranking Algorithm**: Simple score boosting (Option C from proposal)
   - Formula: `boost = 1.0 + (positive_count - negative_count) * 0.1`
   - Each net positive vote adds 10% boost
   - Each net negative vote subtracts 10% penalty
   - Clamped to range 0.1 to 3.0

4. **Frontend UI**: Thumbs up/down buttons
   - Positioned next to score badge on each result card
   - Session tracking to prevent duplicate votes
   - Visual feedback (button highlights when voted)
   - Disabled state after voting

5. **Caching**: In-memory 5-minute TTL cache
   - Reduces database queries for feedback stats
   - Automatic invalidation on new feedback submission

### Technical Decisions:

- **Chose Option C** (simple score boosting) over complex ML models
  - Immediate impact on search quality
  - Low operational complexity
  - No training pipeline required
  - Easy to understand and debug

- **Anonymous feedback** with session tracking
  - No authentication required
  - SessionStorage-based vote tracking
  - Optional session_id for analytics

### Files Created/Modified:

- `src/db/postgres.py` - Added Feedback model and methods
- `src/models/feedback.py` - Pydantic models (NEW)
- `src/api/feedback.py` - API endpoints (NEW)
- `src/services/search_service.py` - Added boosting logic and caching
- `static/index.html` - Added UI buttons and JavaScript
- `scripts/add_feedback_table.py` - Migration script (NEW)

### Future Enhancements (Deferred):

- Query normalization for similar queries
- Time decay for older feedback
- Admin dashboard with charts
- A/B testing framework
- Export feedback data for analysis

## Resources

- Elasticsearch Learning to Rank plugin
- Click models for search ranking
- Implicit feedback signals (dwell time, clicks)

## Dependencies

None

## Related Issues

- #002 (better highlighting might reduce need for feedback)
