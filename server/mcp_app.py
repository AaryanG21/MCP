import asyncio
import json
import os
import re
import requests
from bs4 import BeautifulSoup
import websockets
from fastapi import FastAPI
import uvicorn

# 1. FastAPI App
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "MCP Server is running"}

# 2. Tool 1: Internet Tool
def fetch_company_data(company_name: str) -> dict:
    print(f"[Tool: fetch_company_data] Scraping Wikipedia for {company_name}...")
    url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(url, headers=headers)
    
    data = {
        "company_name": company_name,
        "founders": "",
        "ownership": "",
        "headquarters": "",
        "industry": ""
    }
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            for row in infobox.find_all('tr'):
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    header = th.text.lower()
                    # Clean up footnote references like [1]
                    for sup in td.find_all('sup'):
                        sup.decompose()
                    val = td.text.strip().replace('\n', ', ')
                    if 'founder' in header:
                        data['founders'] = val
                    elif 'owner' in header or 'parent' in header:
                        data['ownership'] = val
                    elif 'headquarters' in header:
                        data['headquarters'] = val
                    elif 'industry' in header:
                        data['industry'] = val
    else:
        print(f"[Error] Wikipedia page not found for {company_name}")
        
    return data

# 3. Tool 2: File CRUD Tool
def file_manager(operation: str, filename: str, content: str = None) -> dict:
    print(f"[Tool: file_manager] Operation: {operation} on {filename}")
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, filename)
    
    try:
        if operation in ('create', 'update'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content or "")
            return {"status": "success", "message": f"File {filename} successfully written to {data_dir}."}
        elif operation == 'read':
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return {"status": "success", "content": f.read()}
            else:
                return {"status": "error", "message": "File not found."}
        elif operation == 'delete':
            if os.path.exists(file_path):
                os.remove(file_path)
                return {"status": "success", "message": f"File {filename} deleted."}
            return {"status": "error", "message": "File not found."}
        else:
            return {"status": "error", "message": "Invalid operation."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 4. WebSocket Server & UI Communication
clients = set()

async def push_to_dashboard(payload: dict):
    if clients:
        message = json.dumps(payload)
        # Use asyncio.gather to broadcast
        await asyncio.gather(*(client.send(message) for client in clients), return_exceptions=True)

async def ws_handler(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if "prompt" in data:
                asyncio.create_task(run_agent(data["prompt"]))
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        clients.remove(websocket)

# 5. Orchestration Logic
async def run_agent(prompt: str):
    await push_to_dashboard({"type": "log", "message": f"Agent started with prompt: {prompt}"})
    
    # Dynamically extract company name
    match = re.search(r'(?:details of|data for|company|about) ([A-Z][a-zA-Z0-9\s,.]+)', prompt, re.IGNORECASE)
    if match:
        company_match = match.group(1).strip()
        for stop_word in [' using', ' and', ' save', ' display', ' the']:
            if stop_word in company_match:
                company_match = company_match.split(stop_word)[0]
    else:
        # Fallback to finding capitalized sequences
        capitalized = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', prompt)
        ignore = {'Search', 'Find', 'Run', 'Dashboard', 'Internet', 'Live', 'Agent', 'Details', 'Data'}
        company_match = next((w for w in capitalized if w not in ignore), "Unknown Company")
        
    company_match = company_match.strip(' ,.')
            
    await push_to_dashboard({"type": "log", "message": f"Running agent for {company_match}..."})
    await push_to_dashboard({"type": "log", "message": f"Extracted company: {company_match}"})
    
    # Step 1
    await push_to_dashboard({"type": "step", "step": 1, "message": f'Executing fetch_company_data("{company_match}")'})
    await push_to_dashboard({"type": "log", "message": f"Live HTTP request initiated to Wikipedia for {company_match}..."})
    company_data = fetch_company_data(company_match)
    await push_to_dashboard({"type": "log", "message": "Website response received"})
    await push_to_dashboard({"type": "log", "message": "Data extracted"})
    await push_to_dashboard({"type": "data", "data": company_data})
    
    # Step 2
    clean_name = company_match.replace(' ', '_').replace(',', '').replace('.', '').lower()
    filename = f"{clean_name}_data.json"
    await push_to_dashboard({"type": "step", "step": 2, "message": f"Executing file_manager('create', '{filename}')"})
    save_status = file_manager('create', filename, json.dumps(company_data, indent=2))
    await push_to_dashboard({"type": "log", "message": f"File created: {filename}"})
    await push_to_dashboard({"type": "file_status", "status": save_status})
    
    # Step 3
    await push_to_dashboard({"type": "step", "step": 3, "message": "Executing push_to_dashboard() - Syncing state to UI"})
    await push_to_dashboard({"type": "log", "message": "Dashboard updated"})
    await push_to_dashboard({"type": "log", "message": "Agent workflow finished successfully."})

# 6. Startup scripts
async def main():
    print("Starting WebSocket Server on port 8765...")
    ws_server = await websockets.serve(ws_handler, "localhost", 8765)
    
    print("Starting FastAPI Server on port 8000...")
    config = uvicorn.Config(app, host="localhost", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # Run both servers concurrently
    await asyncio.gather(
        ws_server.wait_closed(),
        server.serve()
    )

if __name__ == "__main__":
    asyncio.run(main())
