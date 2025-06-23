from fastapi import FastAPI, WebSocket
from loguru import logger
import json
import asyncio
import threading
import uvicorn
import sys
import os
import queue
import time

# Ensure the path to the library is included
sys.path.append("./libreria/")

import mock

from fake_news_detector.fake_news_detector import FakeNewsDetector

app = FastAPI()
clients = set()

fnd = FakeNewsDetector()

# Handle status updates for all clients
def handle_status(msg_queue: queue.Queue):
    fnd.register_callback(status_callback)
    logger.info("Callback registered for status updates.")
    
    while True:
        if not msg_queue.empty():
            url = msg_queue.get()
            logger.info(f"Received analysis request from queue: {url}")
            
            if url != "mock":
                try:
                    fnd.run(url)
                except Exception as e:
                    logger.error(f"Error during analysis: {e}")
            else:
                logger.info("Using mock data for testing.")
                mock.run_mocks(fnd, status_callback)
        else:
            time.sleep(1)  # Sleep to avoid busy waiting
    
def status_callback(data: str =None):
    if len(clients) == 0:
        logger.warning("No clients connected to send status updates.")
        return
    
    for c in list(clients):
        try:
            logger.info(f"Sending status update to client.")
            asyncio.run(c.send_json(data))
        except Exception as e:
            logger.error(f"Error while sending status to client: {e}")

msg_queue = queue.Queue()
thread = threading.Thread(target=handle_status, args=(msg_queue,))
thread.start()

# Handle requests
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the WebSocket connection and add it to the clients set
    await websocket.accept()
    clients.add(websocket)
    
    logger.info(f"New WebSocket connection: {websocket.client}")
    
    try:
        while True:
            if fnd.is_running():
                await asyncio.sleep(1)
                continue
            
            data_raw = await websocket.receive_text()
            data = json.loads(data_raw)
            
            logger.info(f"Received data from client: {data}")
            
            url = data.get("url")
            msg_queue.put(url)
            
            logger.debug(f"URL added to queue.")
            
    except Exception as e:
        print(f"WebSocket connection closed with error: {e}")
    finally:
        clients.remove(websocket)
        #await websocket.close()
        
if __name__ == "__main__":
    logger.info("Starting WebSocket server on ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")