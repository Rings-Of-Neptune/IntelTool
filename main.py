# zkill_ingestion_service/main.py

import asyncio
import json
import websockets
import os
import psycopg2
from datetime import datetime

# Load config from environment variables
ZKILL_WS_URL = "wss://zkillboard.com/websocket/"
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']

WATCHED_CORPS = set(map(int, os.environ.get("WATCHED_CORP_IDS", "").split(",")))

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

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

        cursor.execute("""
            INSERT INTO killmails (killmail_id, character_id, character_name, victim_corp, victim_alliance, system, ship_type, kill_time, zkb_url)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (killmail_id) DO NOTHING;
        """, (kill_id, character_id, character_name, corp_id, alliance_id, system_name, ship_type, time, url))

        conn.commit()
        print(f"Stored killmail {kill_id} in {system_name}")

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
