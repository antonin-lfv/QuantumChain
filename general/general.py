from flask import Flask, Blueprint, render_template, jsonify
import json

BLP_general = Blueprint('BLP_general', __name__,
                        template_folder='templates/general')


@BLP_general.route('/')
def home():
    return render_template('index.html', title='Dashboard')

@BLP_general.route('/miners')
def miners():
    # Get all miners from the file Blockchain/miners.json
    with open('Blockchain/miners.json') as json_file:
        miners = json.load(json_file)
    print(miners)
    
    return render_template('miners.html', title='Miners', miners=miners)

@BLP_general.route('/get_miners')
def get_miners():
  with open('Blockchain/miners.json') as json_file:
    miners = json.load(json_file)
  
  return jsonify({"miners": miners})