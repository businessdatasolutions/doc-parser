Here's a focused guide for building and hosting MCP servers using Python:

## Installation and Setup

Use the uv package manager for faster, lighter Python package management:

```bash
# Install uv (Mac/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project directory and navigate to it
mkdir my-mcp-server && cd my-mcp-server

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Mac/Linux
# or for Windows: .venv\Scripts\activate

# Install MCP dependencies
uv add mcp
```

## Basic MCP Server Implementation

Here's a complete example of a weather MCP server:

```python
from mcp.server import FastMCP

# Initialize MCP server
mcp = FastMCP("Weather Server")

@mcp.tool()
def get_forecast(location: str) -> str:
    """Get weather forecast for a location."""
    # Your API call logic here
    return f"Forecast for {location}: Sunny, 75°F"

@mcp.tool()
def get_alerts(state: str) -> str:
    """Get weather alerts for a state."""
    # Your API call logic here
    return f"No active alerts for {state}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

## Local Testing

Run your server locally to test it:

```bash
# Start the MCP server
uv run weather.py
```

To connect to Claude Desktop, configure your claude_desktop_config.json file at ~/Library/Application Support/Claude/claude_desktop_config.json with your server configuration.

## Remote Hosting with Python

For production deployment, create an HTTP/SSE server using FastAPI and Starlette:

```python
# app.py
import json
import logging
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

# Basic MCP server with example tools
mcp = FastMCP("Example MCP")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

# HTTP endpoints: /mcp for requests, /health for health checks
async def mcp_handler(request: Request):
    payload = await request.json()
    # Delegate to FastMCP to process the MCP message & return a response
    result = await mcp.handle_http(payload)
    return JSONResponse(result)

async def health(_request: Request):
    return PlainTextResponse("ok", status_code=200)

routes = [
    Route("/mcp", endpoint=mcp_handler, methods=["POST"]),
    Route("/health", endpoint=health, methods=["GET"])
]

# Add CORS middleware for web clients
middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
]

app = Starlette(routes=routes, middleware=middleware)
```

### Dependencies for Remote Hosting

Create a `requirements.txt` file:

```txt
mcp
starlette
uvicorn[standard]
```

### Running the Remote Server

```bash
# Install dependencies
uv add starlette uvicorn

# Run the server
uvicorn app:app --host 0.0.0.0 --port 8080
```

## Docker Deployment

Create a Dockerfile for containerized deployment:

```dockerfile
# Use a slim Python image
FROM python:3.12-slim

WORKDIR /app

# System deps (if needed) and security updates
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Northflank will pass PORT; default to 8080 for local runs
ENV PORT=8080
EXPOSE 8080

# Start the HTTP server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

Build and run:

```bash
# Build the container
docker build -t my-mcp-server .

# Run the container
docker run -p 8080:8080 my-mcp-server
```

## Advanced Example with External APIs

Here's a more comprehensive example that integrates with GitHub and Notion APIs:

```python
# pr_analyzer.py
from mcp.server import FastMCP
import requests
import os

mcp = FastMCP("GitHub PR Analyzer")

@mcp.tool()
def fetch_pr_details(repo_url: str, pr_number: int) -> str:
    """Fetch pull request details from GitHub."""
    # Extract repo info from URL
    repo_path = repo_url.replace("https://github.com/", "")
    
    # GitHub API call
    api_url = f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        pr_data = response.json()
        return f"PR #{pr_number}: {pr_data['title']}\n{pr_data['body']}"
    else:
        return f"Failed to fetch PR details: {response.status_code}"

@mcp.tool()
def save_to_notion(content: str, title: str) -> str:
    """Save analysis results to Notion."""
    # Notion API integration
    notion_url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": os.getenv('NOTION_DATABASE_ID')},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]}
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            }
        ]
    }
    
    response = requests.post(notion_url, headers=headers, json=data)
    if response.status_code == 200:
        return "Successfully saved to Notion"
    else:
        return f"Failed to save to Notion: {response.status_code}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

## Debugging and Troubleshooting

For debugging, check Claude's logs at ~/Library/Logs/Claude/mcp*.log:

```bash
# Follow MCP logs
tail -n 20 -f ~/Library/Logs/Claude/mcp*.log
```

## Key Python-Specific Considerations

1. **Environment Variables**: Use `os.getenv()` for API keys and sensitive data
2. **Error Handling**: Implement proper try-catch blocks for external API calls
3. **Dependencies**: Keep requirements.txt updated and use virtual environments
4. **Async Support**: Use `async/await` for I/O operations when using remote hosting

A production-ready MCP server should support both stdio and HTTP/SSE transport types to ensure compatibility with the widest range of clients.

This gives you everything you need to build, test, and deploy Python-based MCP servers both locally and remotely.