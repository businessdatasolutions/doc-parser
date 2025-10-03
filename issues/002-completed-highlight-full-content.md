# Issue #002: Add Highlights to Search Terms in Full Text

**Status**: Completed
**Priority**: High
**Created**: 2025-10-03
**Completed**: 2025-10-03
**Assigned**: Claude

## Description

When users expand "Show Full Content" in search results, the search terms should be highlighted within the full text content, not just in the snippet.

## Implementation Summary

Implemented server-side Elasticsearch full-field highlighting. When `include_content=true` and `include_highlights=true`, Elasticsearch returns the entire content field with `<mark>` tags around matched terms. The frontend uses this highlighted content when available.

## Problem

Currently:
- Search term highlighting works in the snippet (short preview)
- When viewing full content, no highlighting is applied
- Users must manually scan long documents to find where their search terms appear
- This significantly reduces the usability of the full content view

## Current Behavior

1. User searches for "motor replacement"
2. Snippet shows: "To perform <mark>motor replacement</mark>..."
3. User clicks "Show Full Content"
4. Full content displays but NO highlighting - user can't find where "motor replacement" appears

## Proposed Solution

### Option A: Client-Side Highlighting (Quick Fix)
1. Extract search query from current search state
2. When full content is displayed, use JavaScript to highlight terms
3. Use same `<mark>` tags as snippet highlighting
4. Pros: No backend changes, immediate implementation
5. Cons: May not handle stop words correctly, client-side performance

### Option B: Server-Side Full Content Highlighting
1. Modify search API to return highlighted full content
2. Add `highlight_full_content` parameter to search request
3. Configure Elasticsearch to highlight entire content field (not just fragments)
4. Return highlighted HTML with `<mark>` tags
5. Pros: Consistent with snippet highlighting, handles stop words correctly
6. Cons: Larger response payload, backend changes needed

### Recommended: Hybrid Approach
1. Use Elasticsearch full-field highlighting (no fragment limit)
2. Include highlighted full content in search response when `include_content=true`
3. Cache highlighted content on client side
4. Add scroll-to-highlight feature to jump to first match

## Technical Implementation

### Backend Changes (search_service.py)
```python
if request.include_content and request.include_highlights:
    es_query["highlight"]["fields"]["content"] = {
        "number_of_fragments": 0,  # Return full field, not fragments
        "pre_tags": ["<mark>"],
        "post_tags": ["</mark>"]
    }
```

### Frontend Changes (index.html)
```javascript
// When showing full content, use highlighted version if available
if (result.highlighted_content) {
    contentDiv.innerHTML = result.highlighted_content;
} else {
    contentDiv.textContent = result.content;
}

// Auto-scroll to first highlight
const firstMark = contentDiv.querySelector('mark');
if (firstMark) {
    firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
```

## Acceptance Criteria

- [x] Search terms are highlighted in full content view
- [x] Highlighting uses same visual style as snippets (`<mark>` tag with yellow background)
- [x] Multiple occurrences of search terms are all highlighted
- [x] Highlighting handles multi-word queries correctly
- [ ] User can navigate between highlighted terms (optional: next/previous buttons) - Not implemented
- [x] Performance remains acceptable for large documents

## Performance Considerations

- Highlighting full content increases response size
- Consider lazy-loading highlighted content (only when expanded)
- May need pagination or virtual scrolling for very large documents

## Dependencies

None (can be implemented independently)

## Related Issues

- #001 (improved highlighting may reduce need for user feedback)

## Notes

- Current snippet highlighting already works well - need to extend to full content
- Stop words issue noted but not blocking (both "motor replacement" and "motor and replacement" return correct docs)
