"""backend/logging-service/app.py — Port 5005"""
import os, logging
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
from log_routes import log_bp

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.socketio = socketio
app.register_blueprint(log_bp)
if __name__ == "__main__":
    port = int(os.getenv("SDLS_LOGGING_SERVICE_PORT", 5005))
    socketio.run(
    app,
    host="0.0.0.0",
    port=port,
    allow_unsafe_werkzeug=True
)
