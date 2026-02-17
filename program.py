from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from datetime import datetime
import uvicorn

app = FastAPI(
    title="Chatterbox WebSocket Server",
    version="1.2.0",
    description="Enhanced WebSocket server with message counter"
)

@app.get("/")
async def root():
    return {
        "project": "Chatterbox WebSocket Server",
        "status": "Running",
        "version": "1.2.0"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    print("Client connected.")

    # 🔥 NEW: Message counter
    message_count = 0

    await websocket.send_text("Connected to Enhanced Chatterbox Server.")

    try:
        while True:
            message = await websocket.receive_text()
            message_count += 1   # Increment counter

            print(f"Message {message_count}: {message}")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            response = (
                f"[{timestamp}] "
                f"Message #{message_count} -> {message}"
            )

            await websocket.send_text(response)

    except WebSocketDisconnect:
        print("Client disconnected.")

    except Exception as error:
        print(f"Unexpected error: {error}")

if __name__ == "__main__":
    uvicorn.run(
        "program:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
