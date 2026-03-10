
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
from datetime import datetime

app = FastAPI()

rooms = {}

html = """
<!DOCTYPE html>
<html>
<head>
<title>Professional Realtime Chat</title>

<style>

body{
font-family:Segoe UI, Arial;
background:linear-gradient(135deg,#1f4037,#99f2c8);
height:100vh;
display:flex;
justify-content:center;
align-items:center;
margin:0;
}

.container{
width:520px;
background:white;
padding:20px;
border-radius:15px;
box-shadow:0 10px 30px rgba(0,0,0,0.3);
}

h2{
text-align:center;
margin-bottom:20px;
color:#333;
}

input,select{
width:100%;
padding:10px;
border-radius:8px;
border:1px solid #ccc;
font-size:14px;
}

button{
background:#1f8f6f;
color:white;
border:none;
padding:10px;
border-radius:8px;
cursor:pointer;
width:100%;
margin-top:10px;
font-size:15px;
}

button:hover{
background:#166b53;
}

#chat{
height:320px;
overflow-y:auto;
border-radius:10px;
border:1px solid #ddd;
padding:10px;
background:#f7f7f7;
margin-bottom:10px;
}

.msg{
margin:8px 0;
padding:8px 12px;
background:#e3f2fd;
border-radius:10px;
display:inline-block;
max-width:80%;
}

.msg b{
color:#0d47a1;
}

.system{
text-align:center;
color:#777;
font-style:italic;
margin:5px;
}

.time{
font-size:10px;
color:#555;
margin-left:5px;
}

#typing{
color:#0f9d58;
font-weight:bold;
margin-top:5px;
}

.message-area{
display:flex;
gap:5px;
}

.message-area input{
flex:1;
}

.message-area button{
width:90px;
}

</style>

</head>

<body>

<div class="container">

<h2>Realtime Chat Application</h2>

<div id="login">

<input id="username" placeholder="Enter username"><br><br>

<select id="room">
<option value="General">General</option>
<option value="Tech">Tech</option>
<option value="Random">Random</option>
</select>

<button onclick="join()">Join Chat</button>

</div>

<div id="chatbox" style="display:none">

<div id="chat"></div>

<div class="message-area">
<input id="msg" placeholder="Type message..." onkeypress="typing()">
<button onclick="send()">Send</button>
</div>

<div id="typing"></div>

</div>

</div>

<script>

let socket
let username
let room

function join(){

username=document.getElementById("username").value
room=document.getElementById("room").value

socket=new WebSocket(`ws://127.0.0.1:8000/ws/${username}/${room}`)

socket.onmessage=function(event){

const data=JSON.parse(event.data)

const chat=document.getElementById("chat")
const div=document.createElement("div")

if(data.type==="chat"){

div.className="msg"
div.innerHTML="<b>"+data.username+"</b>: "+data.message+
" <span class='time'>"+data.time+"</span>"

}

if(data.type==="system"){

div.className="system"
div.innerText=data.message

}

if(data.type==="typing"){

const typing=document.getElementById("typing")
typing.innerText=data.username+" is typing..."

setTimeout(()=>{
typing.innerText=""
},1200)

return
}

chat.appendChild(div)
chat.scrollTop=chat.scrollHeight

}

document.getElementById("login").style.display="none"
document.getElementById("chatbox").style.display="block"

}

function send(){

const input=document.getElementById("msg")

if(input.value==="") return

socket.send(input.value)

input.value=""

}

function typing(){

if(socket && socket.readyState===WebSocket.OPEN){

socket.send(JSON.stringify({"type":"typing"}))

}

}

</script>

</body>
</html>
"""

@app.get("/")
async def home():
    return HTMLResponse(html)


async def broadcast(room, data):
    for connection in rooms.get(room, []):
        await connection.send_text(json.dumps(data))


@app.websocket("/ws/{username}/{room}")
async def websocket_endpoint(websocket: WebSocket, username: str, room: str):

    await websocket.accept()

    if room not in rooms:
        rooms[room] = []

    rooms[room].append(websocket)

    await broadcast(room,{
        "type":"system",
        "message":f"{username} joined {room}"
    })

    try:

        while True:

            data = await websocket.receive_text()

            try:
                obj = json.loads(data)

                if obj.get("type") == "typing":
                    await broadcast(room,{
                        "type":"typing",
                        "username":username
                    })
                    continue

            except:
                pass

            await broadcast(room,{
                "type":"chat",
                "username":username,
                "message":data,
                "time":datetime.now().strftime("%H:%M")
            })

    except WebSocketDisconnect:

        rooms[room].remove(websocket)

        await broadcast(room,{
            "type":"system",
            "message":f"{username} left the chat"
        })