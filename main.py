# main.py

import asyncio
import json
import websockets
import os
from datetime import datetime

# Load config from environment variables
ZKILL_WS_URL = "wss://zkillboard.com/websocket/"
WATCHED_CORPS = set(map(int, os.environ.get("WATCHED_CORP_IDS", "").split(",")))

async def process_killmail(killmail):
    try:
        zkb = killmail.get('zkb', {})
        victim = killmail['victim']
        system = killmail['solarSystem']
        if victim['corporation_id'] not in WATCHED_CORPS:
            return  # skip unmonitored corps

        kill_id = killmail['killID']
        character_id = victim.get('character_id')
        character_name = victim.get('character_name', 'Unknown')
        corp_id = victim['corporation_id']
        alliance_id = victim.get('alliance_id')
        system_name = system['name']
        ship_type = victim['ship_type']
        time = killmail['killmail_time']
        url = zkb.get('url')

        print(f"Match: killmail {kill_id} in {system_name} | {character_name} in {ship_type} at {time}")
        print(f"zKill URL: {url}\n")

    except Exception as e:
        print(f"Error processing killmail: {e}")

async def listen_to_zkill():
    async with websockets.connect(ZKILL_WS_URL) as ws:
        await ws.send(json.dumps({"action": "sub", "channel": "killstream"}))
        print("Connected to zKillboard WebSocket.")
        while True:
            try:
                message = await ws.recv()
                killmail = json.loads(message)
                await process_killmail(killmail)
            except Exception as e:
                print(f"WebSocket error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    print("Starting zKillboard listener service...")
    asyncio.run(listen_to_zkill())

from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def healthcheck():
    return "zkill listener running"

def run_websocket_listener():
    asyncio.run(listen_to_zkill())

if __name__ == "__main__":
    print("Starting listener + web server...")
    threading.Thread(target=run_websocket_listener, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

