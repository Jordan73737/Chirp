from app import create_app, socketio
import app.socket_events 

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

