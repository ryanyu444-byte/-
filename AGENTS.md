# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

TrendRadar is a Chinese hot news aggregation and analysis tool (Python 3.12, managed with `uv`). It crawls trending news from 11+ platforms, filters by keywords or AI, generates HTML reports, and sends notifications. It also ships an MCP server for AI assistant integration.

### Running services

| Service | Command | Notes |
|---|---|---|
| Main crawler (one-shot) | `uv run python -m trendradar` | Crawls all platforms, generates HTML in `output/html/` |
| Doctor check | `uv run python -m trendradar --doctor` | Validates config, storage, Python version |
| Show schedule | `uv run python -m trendradar --show-schedule` | Displays current scheduling state |
| MCP server (HTTP) | `uv run python -m mcp_server.server --transport http --host 0.0.0.0 --port 3333` | FastMCP 2.0, endpoint at `/mcp` |
| Serve HTML reports | `python3 -m http.server 8080 -d output/html/latest/` | Simple dev server for generated reports |

### Non-obvious caveats

- **AI features require `AI_API_KEY`**: AI analysis, translation, and AI-based filtering all fail gracefully without an API key. The crawler and report generation still work. Set `AI_API_KEY` env var or configure in `config/config.yaml` under `ai.api_key`.
- **No lint or test suite**: This project has no automated tests or linter configuration. The `--doctor` command serves as the primary health check.
- **Filter method default is `ai`**: `config/config.yaml` sets `filter.method: "ai"` by default. Without an AI API key, it automatically falls back to keyword matching.
- **RSS failures are expected**: Some RSS feeds (Reddit, Anthropic, The Verge) may return 403/404 errors depending on network conditions. This is non-blocking.
- **MCP server endpoint**: The HTTP MCP endpoint is at `http://localhost:3333/mcp` (not the root `/`). Clients must send `Accept: application/json, text/event-stream` header.
- **Output directory**: All data is stored under `output/` (SQLite DBs in `output/news/` and `output/rss/`, HTML reports in `output/html/`).
