# Document Search UI

A simple, single-page HTML interface for searching documents in the Elasticsearch database.

## Features

- **Modern Design**: Clean, gradient UI with responsive layout
- **Real-time Search**: Instant results with highlighted matches
- **Advanced Filters**:
  - Category filtering (Maintenance, Operations, Spare Parts)
  - Results per page (10, 20, 50)
- **Search Options**:
  - Fuzzy matching for typo tolerance
  - Highlighted snippets showing matched terms
- **Pagination**: Navigate through large result sets
- **Performance Metrics**: See total results and search time

## How to Use

1. **Start the server**:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open your browser**:
   Navigate to `http://localhost:8000`

3. **Search**:
   - Enter your query (e.g., "cartoner", "specification")
   - Optionally select filters
   - Click "Search" or press Enter

## Sample Queries

- `cartoner` - Find all pages about cartoner machines
- `specification` - Technical specifications
- `safety requirements` - Safety-related content
- `installation procedure` - Installation guides
- `part number 12345` - Search by part number

## Architecture

The UI is a pure HTML/JavaScript application that:
- Makes POST requests to `/api/v1/search`
- Displays results with highlighted snippets
- Handles pagination and filtering client-side
- No build process required

## API Integration

The UI calls the FastAPI search endpoint:

```javascript
POST http://localhost:8000/api/v1/search
Content-Type: application/json

{
  "query": "search terms",
  "page": 1,
  "page_size": 10,
  "enable_fuzzy": true,
  "include_highlights": true,
  "filters": {
    "category": "maintenance"
  }
}
```

## Customization

Edit `index.html` to customize:
- Colors (search for `#667eea` and `#764ba2`)
- Layout and spacing
- Result card formatting
- Filter options
