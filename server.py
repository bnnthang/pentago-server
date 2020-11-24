import eventlet
import socketio
import os
import random

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

waitingQueue = []
currentRooms = {}


@sio.event
def connect(sid, environ):
    print(sid, "connected")

    # find oppo
    if len(waitingQueue) > 0:
        # if found
        assignedRoom = waitingQueue[0]
        # remove from queue
        waitingQueue.pop()
        # enter room
        sio.enter_room(sid, assignedRoom)
        sio.leave_room(sid, sid)
        # cache data
        currentRooms[assignedRoom] = (sid, assignedRoom)
        # set roles
        blackIndex = random.randint(0, 1)
        whiteIndex = 1 - blackIndex
        sio.emit("role", "black", currentRooms[assignedRoom][blackIndex])
        sio.emit("role", "white", currentRooms[assignedRoom][whiteIndex])

        print("in rooms", currentRooms)
    else:
        # add to queue
        waitingQueue.append(sid)
        print("in wait", waitingQueue)


def relayMessage(sid, _event, message):
    sio.emit(room=sio.rooms(sid)[0], event=_event, data=message)


@sio.on("bmove")
def blackMoveRelay(sid, state):
    print(sid, "moves", state)
    if int(state) == 0:
        return
    relayMessage(sid, "bmove", state)

@sio.on("wmove")
def whiteMoveRelay(sid, state):
    print(sid, "moves", state)
    if int(state) == 0:
        return
    relayMessage(sid, "wmove", state)

@sio.on("ended")
def gameEnded(sid):
    # disconnect players
    sio.disconnect(sid)

@sio.on("chat")
def chatRelay(sid, msg):
    print(sid, "said", msg)
    relayMessage(sid, "chat", msg)

@sio.event
def message(sid, data):
    print(f"receive {data} from {sid}")
    sio.send("hi there", room=sid)

@sio.event
def disconnect(sid):
    print(sid, "disconnected")

    assignedRoom = sio.rooms(sid)[0]
    removeQueue = currentRooms.get(assignedRoom, [])
    for uid in removeQueue:
        sio.disconnect(uid)
    
    currentRooms.pop(assignedRoom)
    print("in rooms", currentRooms)


if __name__ == '__main__':
    PORT = int(os.getenv("PORT"))
    # print(PORT)
    # PORT = 4602
    eventlet.wsgi.server(eventlet.listen(('', PORT)), app)