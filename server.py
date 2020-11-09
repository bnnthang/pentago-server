import eventlet
import socketio
import os

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

@sio.event
def connect(sid, environ):
    print('connect ', sid, environ)

@sio.on("say hello")
def response(sid, msg):
    print(sid, "said", msg)
    sio.emit(room=sid, event="hello back", data="welcome to server")

@sio.event
def message(sid, data):
    print(f"receive {data} from {sid}")
    sio.send("hi there", room=sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

if __name__ == '__main__':
    PORT = int(os.getenv("PORT"))
    # print(PORT)
    # PORT = 4602
    eventlet.wsgi.server(eventlet.listen(('', PORT)), app)