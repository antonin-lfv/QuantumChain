from flask import Flask

from general.general import BLP_general

app = Flask(__name__, template_folder='templates')

app.register_blueprint(BLP_general)
