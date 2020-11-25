import colorama
import eventlet
import os
import random
import socketio


sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    "/": {"content_type": "text/html", "filename": "index.html"}
})

waitingQueue = []
currentRooms = {}
assignedRoom = {}


def specialPrint(*args):
    """
    Function for debugging
    """
    st = " ".join(str(i) for i in args)
    print(colorama.Back.MAGENTA, st)
    print(colorama.Style.RESET_ALL)


@sio.event
def connect(sid, environ):
    """
    Handle when a new socket connected
    """

    # print debug
    specialPrint(sid, "connected")

    # find oppo
    if len(waitingQueue) > 0:
        # if found
        oppo_sid = waitingQueue[0]
        assignedRoomId = oppo_sid + sid
        # remove from queue
        waitingQueue.pop()
        # enter room
        sio.enter_room(oppo_sid, assignedRoomId)
        sio.enter_room(sid, assignedRoomId)
        # cache data
        currentRooms[assignedRoomId] = (sid, oppo_sid)
        assignedRoom[oppo_sid] = assignedRoomId
        assignedRoom[sid] = assignedRoomId
        # set roles
        blackIndex = random.randint(0, 1)
        whiteIndex = 1 - blackIndex
        specialPrint("black:", currentRooms[assignedRoomId][blackIndex], "white:", currentRooms[assignedRoomId][whiteIndex])
        sio.emit("role", "black", currentRooms[assignedRoomId][blackIndex])
        sio.emit("role", "white", currentRooms[assignedRoomId][whiteIndex])

        specialPrint("in rooms", currentRooms)
    else:
        # add to queue
        waitingQueue.append(sid)
        specialPrint("in wait", waitingQueue)


def relayMessage(sid, _event, message):
    sio.emit(room=assignedRoom[sid], event=_event, data=message)
    specialPrint("emitted", message, "to room", assignedRoom[sid])


@sio.on("bmove")
def blackMoveRelay(sid, state):
    specialPrint(sid, "moves", state)
    if int(state) == 0:
        return
    relayMessage(sid, "bmove", state)


@sio.on("wmove")
def whiteMoveRelay(sid, state):
    specialPrint(sid, "moves", state)
    if int(state) == 0:
        return
    relayMessage(sid, "wmove", state)


@sio.on("ended")
def gameEnded(sid):
    """
    When the game ended
    """
    # disconnect players
    sio.disconnect(sid)


@sio.on("chat")
def chatRelay(sid, msg):
    specialPrint(sid, "said", msg)
    relayMessage(sid, "chat", msg)


@sio.event
def disconnect(sid):
    """
    Handle when a socket disconnect
    """

    # print debug
    specialPrint(sid, "disconnected")

    # if still in queue
    if sid in waitingQueue:
        waitingQueue.pop(waitingQueue.index(sid))
        return

    # get the room id
    assignedRoomId = assignedRoom[sid]
    specialPrint("deleting", assignedRoom)

    # disconnect other socket in room
    removeQueue = currentRooms.get(assignedRoomId, [])
    for uid in removeQueue:
        sio.disconnect(uid)
        assignedRoom.pop(uid)
    
    # remove cache data
    assignedRoom.pop(sid)
    currentRooms.pop(assignedRoom)
    specialPrint("in rooms", currentRooms)


if __name__ == "__main__":
    PORT = int(os.getenv("PORT"))
    eventlet.wsgi.server(eventlet.listen(('', PORT)), app)