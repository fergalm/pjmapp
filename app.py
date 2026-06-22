from flask import Flask
from foo import main
app = Flask(__name__)

@app.route("/query/<iso>")
def query(iso):
    return main.query(iso)
