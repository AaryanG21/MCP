# MCP Agent Dashboard

A complete local MCP-style agent system built with Python + React, running entirely inside Antigravity — no external MCP clients, no API keys, no Claude Desktop required.

## 📺 Demo

[![Watch the demo on YouTube](https://img.youtube.com/vi/_6IH4-OC3J8/0.jpg)](https://youtu.be/_6IH4-OC3J8)

## Overview

This project implements an autonomous agent system that:
- **Fetches live company data** from Wikipedia using Requests + BeautifulSoup
- **Saves results** to local JSON files via a file management tool
- **Streams real-time execution logs** to a React dashboard over WebSockets

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python, FastAPI, WebSockets, Uvicorn |
| Scraping  | Requests, BeautifulSoup4            |
| Frontend  | React, Vite                         |

## Project Structure

```
project/
├── dashboard/          # React + Vite frontend
│   └── src/
│       ├── App.jsx     # Main app with all components
│       └── index.css   # Dark-themed UI styles
├── server/
│   ├── data/           # Auto-created; stores scraped JSON files
│   ├── mcp_app.py      # Backend: tools, WebSocket server, agent logic
│   └── requirements.txt
└── test_ws.py          # WebSocket test script
```

## Tools

- **`fetch_company_data(company_name)`** — Scrapes Wikipedia for founders, ownership, headquarters, industry
- **`file_manager(operation, filename)`** — CRUD operations on local `.json` files in `server/data/`
- **`push_to_dashboard(payload)`** — Broadcasts real-time updates to the frontend via WebSocket on port `8765`

## Local Run Instructions

**Terminal 1 — Start the backend:**
```bash
cd server
python3 -m pip install -r requirements.txt
python3 mcp_app.py
```

**Terminal 2 — Start the frontend:**
```bash
cd dashboard
npm install
npm run dev
```

Then open the Vite URL (typically `http://localhost:5173`) in your browser.

## Example Prompts

- `Find the ownership details of Tata Sons, save those details in a local file, and display them on the dashboard.`
- `Search the internet live for company details of Infosys`
- `Find details of Tesla, Inc. using fetch_company_data`

## Notes

- No external MCP clients or Claude Desktop needed
- No paid APIs or API keys required
- Works with Python 3.13+
- If the server fails to start with "address already in use", run: `lsof -ti :8765 | xargs kill -9`
