"""backend/payment-service/app.py — Port 5002"""
import os, logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
from payment_routes import payment_bp

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
app = Flask(__name__)
CORS(app)
app.register_blueprint(payment_bp)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("SDLS_PAYMENT_SERVICE_PORT",5002)),
            debug=os.getenv("FLASK_DEBUG","0")=="1", threaded=True, use_reloader=False)
