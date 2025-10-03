# Issue #001: Allow User to Score Results and System Learning

**Status**: Open
**Priority**: Medium
**Created**: 2025-10-03
**Assigned**: Unassigned

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

- [ ] Users can rate search results (thumbs up/down minimum)
- [ ] Ratings are stored persistently
- [ ] Search results ranking improves based on historical ratings
- [ ] Admin dashboard to view feedback metrics (optional)
- [ ] Feedback can be anonymous or user-attributed

## Resources

- Elasticsearch Learning to Rank plugin
- Click models for search ranking
- Implicit feedback signals (dwell time, clicks)

## Dependencies

None

## Related Issues

- #002 (better highlighting might reduce need for feedback)
