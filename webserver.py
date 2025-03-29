from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8000))  # Usar variable PORT
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    server = Thread(target=run)
    server.start()