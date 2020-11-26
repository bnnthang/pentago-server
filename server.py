import colorama
import eventlet
import os
import random
import socketio

sio = socketio.Server()
app = socketio.WSGIApp(sio,
                       static_files={
                           "/": {
                               "content_type": "text/html",
                               "filename": "index.html"
                           }
                       })

waitingId = None
currentRooms = {}
assignedRoom = {}


def specialPrint(*args):
    """
    Function for debugging
    """
    st = " ".join(str(i) for i in args)
    print(colorama.Back.BLUE, st, colorama.Style.RESET_ALL)


@sio.event
def connect(sid, environ):
    """
    Handle when a new socket connected
    """

    global waitingId

    # print debug
    specialPrint(sid, "connected")

    # find oppo
    if waitingId == None:
        # add to queue
        waitingId = sid
        specialPrint("in wait", waitingId)
    else:
        # if found
        oppo_sid = waitingId
        assignedRoomId = oppo_sid + sid
        # remove from queue
        waitingId = None
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
        specialPrint("black:", currentRooms[assignedRoomId][blackIndex],
                     "white:", currentRooms[assignedRoomId][whiteIndex])
        sio.emit("role", "black", currentRooms[assignedRoomId][blackIndex])
        sio.emit("role", "white", currentRooms[assignedRoomId][whiteIndex])

        specialPrint("in rooms", currentRooms)


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
    specialPrint("ended")
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

    global waitingId

    # if still in queue
    if sid == waitingId:
        waitingId = None
        return

    # get the room id
    assignedRoomId = assignedRoom[sid]
    specialPrint("deleting", assignedRoom)

    # remove cache data
    removeQueue = currentRooms.get(assignedRoomId, [])
    if sid in assignedRoom:
        assignedRoom.pop(sid)
    if assignedRoomId in currentRooms:
        currentRooms.pop(assignedRoomId)

    # disconnect other socket in room
    for uid in removeQueue:
        sio.disconnect(uid)
        if uid in assignedRoom:
            assignedRoom.pop(uid)

    specialPrint("in rooms", currentRooms)


if __name__ == "__main__":
    PORT = int(os.getenv("PORT"))
    eventlet.wsgi.server(eventlet.listen(('', PORT)), app)