from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import json

app = FastAPI()
connections = {}
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Chatterbox</title>
        <style>
            body {
                margin: 0;
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1f2937, #111827);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: white;
            }

            .login-box {
                background: #1e293b;
                padding: 40px;
                border-radius: 12px;
                width: 320px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            }

            input {
                width: 100%;
                padding: 10px;
                margin: 15px 0;
                border-radius: 8px;
                border: none;
                background: #0f172a;
                color: white;
            }

            button {
                width: 100%;
                padding: 10px;
                border-radius: 8px;
                border: none;
                background: #2563eb;
                color: white;
                cursor: pointer;
            }

            button:hover {
                background: #1d4ed8;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🚀 Chatterbox</h2>
            <form action="/chat" method="get">
                <input type="text" name="username" placeholder="Enter your name" required>
                <button type="submit">Join Chat</button>
            </form>
        </div>
    </body>
    </html>
    """
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(username: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chatterbox</title>
        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1f2937, #111827);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: white;
            }}

            .chat-container {{
                width: 420px;
                height: 600px;
                background: #1e293b;
                border-radius: 15px;
                display: flex;
                flex-direction: column;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            }}

            .header {{
                background: #0f172a;
                padding: 15px;
                text-align: center;
                font-weight: bold;
            }}

            .chat-box {{
                flex: 1;
                padding: 15px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}

            .message {{
                padding: 10px;
                border-radius: 12px;
                max-width: 70%;
            }}

            .me {{
                background: #2563eb;
                align-self: flex-end;
            }}

            .other {{
                background: #334155;
                align-self: flex-start;
            }}

            .system {{
                align-self: center;
                font-size: 12px;
                color: #94a3b8;
            }}

            .input-area {{
                display: flex;
                padding: 10px;
                background: #0f172a;
            }}

            input {{
                flex: 1;
                padding: 10px;
                border-radius: 8px;
                border: none;
                background: #1e293b;
                color: white;
            }}

            button {{
                margin-left: 8px;
                padding: 10px;
                border-radius: 8px;
                border: none;
                background: #2563eb;
                color: white;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="header">Welcome {username}</div>
            <div id="chat" class="chat-box"></div>
            <div class="input-area">
                <input id="messageInput" type="text" placeholder="Type message..."
                       onkeydown="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            const myUsername = "{username}";
            const socket = new WebSocket(`ws://${{location.host}}/ws/${{myUsername}}`);

            socket.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                const chat = document.getElementById("chat");
                const msg = document.createElement("div");

                if (data.type === "system") {{
                    msg.classList.add("system");
                    msg.textContent = data.message;
                }} else {{
                    msg.classList.add("message");
                    if (data.username === myUsername) {{
                        msg.classList.add("me");
                    }} else {{
                        msg.classList.add("other");
                    }}
                    msg.textContent = data.username + ": " + data.message;
                }}

                chat.appendChild(msg);
                chat.scrollTop = chat.scrollHeight;
            }};

            function sendMessage() {{
                const input = document.getElementById("messageInput");
                if (input.value.trim() !== "") {{
                    socket.send(input.value);
                    input.value = "";
                }}
            }}
        </script>
    </body>
    </html>
    """
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    connections[websocket] = username
    for connection in connections:
        await connection.send_text(json.dumps({
            "type": "system",
            "message": f"{username} joined the chat"
        }))

    try:
        while True:
            data = await websocket.receive_text()
            for connection in connections:
                await connection.send_text(json.dumps({
                    "type": "chat",
                    "username": username,
                    "message": data
                }))
    except WebSocketDisconnect:
        connections.pop(websocket)

        for connection in connections:
            await connection.send_text(json.dumps({
                "type": "system",
                "message": f"{username} left the chat"
            }))
