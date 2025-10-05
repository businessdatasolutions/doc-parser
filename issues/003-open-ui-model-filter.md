# Issue #003: Add General Client-Side Filter Mechanism to Search UI

**Status**: Open
**Priority**: Medium
**Created**: 2025-10-04
**Updated**: 2025-10-04 (Expanded to general filtering)
**Assigned**: Unassigned

## Description

Add a general client-side filtering mechanism to the search UI that allows users to dynamically filter loaded search results by multiple criteria. This provides a flexible, reusable filter system that can be extended with new filter types.

## Problem

Currently, users can only filter by category before searching (server-side). Once results are loaded, there's no way to narrow down results without performing a new search. Users need to quickly filter results by:
- Machine model
- Document category
- Date range
- Document filename
- Any other metadata available in results

A general filtering mechanism is more valuable than a single-purpose filter.

## Proposed Solution

Implement a **general client-side filtering framework** with initial filters:

### Phase 1: Core Framework
1. **Filter State Management**: JavaScript object to track active filters
2. **Filter Function**: Generic function that applies multiple filter conditions
3. **UI Components**: Reusable filter dropdown/input components
4. **Result Counter**: Show "Showing X of Y results" when filters are active

### Phase 2: Initial Filters
1. **Machine Model Filter**: Dropdown populated from results
2. **Category Filter**: Dropdown with available categories
3. **Filename Filter**: Text input for partial matching
4. **Clear Filters Button**: Reset all filters

### Phase 3: Advanced (Optional)
1. **Date Range Filter**: Min/max date pickers
2. **Score Range Filter**: Min/max score sliders
3. **Part Number Filter**: Text input for part numbers
4. **Multi-select Support**: Filter by multiple values

## Technical Design

### Filter State Object
```javascript
const activeFilters = {
    machineModel: null,        // null = all, or specific model
    category: null,            // null = all, or specific category
    filename: '',              // empty = all, or partial match
    dateRange: { min: null, max: null },
    scoreRange: { min: 0, max: 100 }
};
```

### Generic Filter Function
```javascript
function applyFilters(results, filters) {
    return results.filter(result => {
        // Machine model filter
        if (filters.machineModel && result.machine_model !== filters.machineModel) {
            return false;
        }

        // Category filter
        if (filters.category && result.category !== filters.category) {
            return false;
        }

        // Filename filter (case-insensitive partial match)
        if (filters.filename && !result.filename.toLowerCase().includes(filters.filename.toLowerCase())) {
            return false;
        }

        // Date range filter
        if (filters.dateRange.min && new Date(result.upload_date) < filters.dateRange.min) {
            return false;
        }
        if (filters.dateRange.max && new Date(result.upload_date) > filters.dateRange.max) {
            return false;
        }

        // Score range filter
        if (result.score < filters.scoreRange.min || result.score > filters.scoreRange.max) {
            return false;
        }

        return true;
    });
}
```

### Dynamic Filter Population
```javascript
function extractUniqueValues(results, field) {
    const values = results
        .map(r => r[field])
        .filter(v => v != null && v !== '');
    return [...new Set(values)].sort();
}
```

## UI Design

### Filter Bar (appears below search box when results loaded)
```
Search Results (45 total, showing 12 after filters)

┌─────────────────────────────────────────────────────────────┐
│ Filters:  [Machine Model: All ▼]  [Category: All ▼]        │
│          [Filename: ___________]  [Clear All Filters]       │
└─────────────────────────────────────────────────────────────┘

Result 1: SPEC_AIR-XL_EN_LR.pdf - Page 3
...
```

## Technical Considerations

- **Performance**: Client-side filtering is fast for <1000 results
- **State Management**: Store original results separately from filtered results
- **Reset Behavior**: Clear filters when new search is performed
- **Null Handling**: Gracefully handle missing/null field values
- **Extensibility**: Easy to add new filter types
- **URL Params** (Optional): Persist filter state in URL query params

## Acceptance Criteria

### Phase 1: Core Framework
- [ ] Filter state object manages active filters
- [ ] Generic `applyFilters()` function implemented
- [ ] Original results stored separately from filtered results
- [ ] Result counter shows "Showing X of Y results" when filtered
- [ ] Filters clear when new search is performed

### Phase 2: Initial Filters
- [ ] Machine model dropdown filter (populated from results)
- [ ] Category dropdown filter (populated from results)
- [ ] Filename text input filter (partial case-insensitive match)
- [ ] "Clear All Filters" button resets to show all results
- [ ] Filters work independently and in combination

### Phase 3: UI/UX
- [ ] Filter bar appears only when results are loaded
- [ ] Filter dropdowns show "(No results)" when no values available
- [ ] Filters handle null/undefined values gracefully
- [ ] Visual feedback when filters are active
- [ ] Responsive design for mobile devices

## Implementation Notes

1. Store original search results in `originalResults` variable
2. Store filtered results in `filteredResults` variable
3. Re-render only filtered results
4. Update result counter dynamically
5. Keep pagination working with filtered results

## UI Mockup (Updated)

```
┌────────────────────────────────────────────────────────────────┐
│  Search: [User Requirement Specification] [Search]             │
│                                                                 │
│  ▼ Filters                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Machine Model: [All Models ▼]  Category: [All ▼]        │  │
│  │ Filename: [______________]      [Clear All Filters]      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Showing 12 of 45 results for "User Requirement Specification" │
│                                                                 │
│  Result 1: urs-1-20.pdf - Page 5                               │
│  Category: operations  |  Model: URS                           │
│  Score: 7.90  [👍] [👎]                                         │
│  ...                                                            │
└────────────────────────────────────────────────────────────────┘
```

## Dependencies

None

## Related Issues

None
