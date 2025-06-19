import asyncio
import json
import websockets
import os
from flask import Flask
import threading

ZKILL_WS_URL = "wss://zkillboard.com/websocket/"
WATCHED_CORPS = set(map(int, os.environ.get("WATCHED_CORP_IDS", "").split(",")))

app = Flask(__name__)

@app.route("/")
def health():
    return "zkill listener is running"

async def process_killmail(killmail):
    try:
        zkb = killmail.get('zkb', {})
        victim = killmail['victim']
        system = killmail['solarSystem']

        if victim['corporation_id'] not in WATCHED_CORPS:
            return

        kill_id = killmail['killID']
        character_name = victim.get('character_name', 'Unknown')
        system_name = system['name']
        ship_type = victim['ship_type']
        time = killmail['killmail_time']
        url = zkb.get('url')

        print(f"Match: killmail {kill_id} | {character_name} in {ship_type} @ {system_name} | {time}")
        print(f"{url}\n")

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

def run_websocket():
    asyncio.run(listen_to_zkill())

if __name__ == "__main__":
    print("Starting Flask + zKill listener service...")
    threading.Thread(target=run_websocket, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
