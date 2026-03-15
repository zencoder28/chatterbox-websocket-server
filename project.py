from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
from datetime import datetime

app = FastAPI()

rooms = {}
users = {}

html = """
<!DOCTYPE html>
<html>
<head>
<title>Realtime Chat Application</title>

<style>

body{
font-family:Segoe UI;
background:linear-gradient(135deg,#1e3c72,#2a5298);
height:100vh;
display:flex;
justify-content:center;
align-items:center;
margin:0;
}

/* LOGIN BOX */

.login{
width:350px;
background:white;
padding:20px;
border-radius:10px;
box-shadow:0 10px 25px rgba(0,0,0,0.2);
}

.login input,select{
width:100%;
padding:10px;
margin-top:10px;
border-radius:6px;
border:1px solid #ccc;
}

/* MAIN CONTAINER */

.container{
display:flex;
width:900px;
height:520px;
background:white;
border-radius:12px;
box-shadow:0 15px 40px rgba(0,0,0,0.3);
overflow:hidden;
}

/* SIDEBAR */

.sidebar{
width:250px;
background:#111827;
color:white;
padding:20px;
}

.sidebar h3{
margin-top:0;
border-bottom:1px solid rgba(255,255,255,0.2);
padding-bottom:5px;
}

.user{
padding:6px 0;
}

/* CHAT AREA */

.chat-area{
flex:1;
display:flex;
flex-direction:column;
padding:15px;
}

#chat{
flex:1;
overflow-y:auto;
background:#f3f4f6;
border-radius:8px;
padding:15px;
border:1px solid #ddd;
}

.msg{
background:#2563eb;
color:white;
padding:10px 14px;
border-radius:18px;
margin:8px 0;
max-width:70%;
}

.system{
text-align:center;
color:#6b7280;
font-style:italic;
}

.time{
font-size:10px;
margin-left:5px;
}

.typing{
color:#22c55e;
font-weight:bold;
}

/* MESSAGE INPUT */

.message-area{
display:flex;
gap:10px;
margin-top:10px;
}

.message-area input{
flex:1;
padding:10px;
border-radius:20px;
border:1px solid #ccc;
}

button{
background:#2563eb;
color:white;
border:none;
padding:10px 15px;
border-radius:20px;
cursor:pointer;
}

button:hover{
background:#1d4ed8;
}

</style>
</head>

<body>

<div id="login" class="login">

<h2>Join Chat</h2>

<input id="username" placeholder="Enter username">

<select id="room">
<option value="General">General</option>
<option value="Tech">Tech</option>
<option value="Random">Random</option>
</select>

<button onclick="join()">Join</button>

</div>

<div id="chatbox" style="display:none">

<div class="container">

<div class="sidebar">

<h3 id="roomname"></h3>

<p id="activeusers"></p>

<h3>Online Users</h3>

<div id="userlist"></div>

</div>

<div class="chat-area">

<div id="chat"></div>

<div class="message-area">
<input id="msg" placeholder="Type message..." onkeypress="typing()">
<button onclick="send()">Send</button>
</div>

<div id="typing"></div>

</div>

</div>

</div>

<script>

let socket
let username
let room

function join(){

username=document.getElementById("username").value
room=document.getElementById("room").value

if(username===""){
alert("Enter username")
return
}

socket=new WebSocket(`ws://127.0.0.1:8000/ws/${username}/${room}`)

document.getElementById("roomname").innerText="Room: "+room

socket.onmessage=function(event){

const data=JSON.parse(event.data)

const chat=document.getElementById("chat")

if(data.type==="chat"){

const div=document.createElement("div")
div.className="msg"

div.innerHTML="<b>"+data.username+"</b>: "+data.message+
" <span class='time'>"+data.time+"</span>"

chat.appendChild(div)

}

if(data.type==="system"){

const div=document.createElement("div")
div.className="system"
div.innerText=data.message

chat.appendChild(div)

}

if(data.type==="typing"){

const typing=document.getElementById("typing")

typing.innerHTML="<span class='typing'>"+data.username+" is typing...</span>"

setTimeout(()=>{typing.innerHTML=""},1000)

}

if(data.type==="users"){

document.getElementById("activeusers").innerText="Active Users: "+data.count

const list=document.getElementById("userlist")

list.innerHTML=""

data.list.forEach(user=>{

const div=document.createElement("div")
div.className="user"
div.innerText="🟢 "+user

list.appendChild(div)

})

}

chat.scrollTop=chat.scrollHeight

}

document.getElementById("login").style.display="none"
document.getElementById("chatbox").style.display="block"

}

function send(){

const msg=document.getElementById("msg")

if(msg.value==="") return

socket.send(msg.value)

msg.value=""

}

function typing(){

socket.send(JSON.stringify({"type":"typing"}))

}

</script>

</body>
</html>
"""

@app.get("/")
async def home():
    return HTMLResponse(html)

async def broadcast(room,data):
    for ws in rooms.get(room,[]):
        await ws.send_text(json.dumps(data))

async def update_users(room):

    user_list=[users[ws] for ws in rooms.get(room,[])]

    await broadcast(room,{
        "type":"users",
        "count":len(user_list),
        "list":user_list
    })

@app.websocket("/ws/{username}/{room}")
async def websocket_endpoint(ws:WebSocket,username:str,room:str):

    await ws.accept()

    if room not in rooms:
        rooms[room]=[]

    rooms[room].append(ws)
    users[ws]=username

    await broadcast(room,{
        "type":"system",
        "message":f"{username} joined {room}"
    })

    await update_users(room)

    try:

        while True:

            data=await ws.receive_text()

            try:
                obj=json.loads(data)

                if obj["type"]=="typing":

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

        rooms[room].remove(ws)
        users.pop(ws)

        await broadcast(room,{
            "type":"system",
            "message":f"{username} left the chat"
        })

        await update_users(room)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("project:app", host="127.0.0.1", port=8000, reload=True)