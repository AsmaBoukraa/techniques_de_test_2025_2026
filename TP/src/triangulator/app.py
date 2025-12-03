# Flask app minimal (stub)
from flask import Flask

app = Flask(__name__)

@app.get("/healthz")
def healthz():
    return "ok"
