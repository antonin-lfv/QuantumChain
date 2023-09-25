from flask import Flask, Blueprint, render_template, jsonify
import json

BLP_general = Blueprint('BLP_general', __name__,
                        template_folder='templates/general')


@BLP_general.route('/')
def home():
  # Get blockchain from the file Blockchain/num_blocks.json
  with open('Blockchain/blockchain_data.json') as json_file:
    data = json.load(json_file)
    number_blocks = len(data)
    first_block_mined_date = data[0]['end_time']
    last_block_mined_date = data[-1]['end_time']
  
  # Get miners from the file Blockchain/miners.json
  with open('Blockchain/miners.json') as json_file:
    miners = json.load(json_file)
    number_miners = len(miners)
  
  # Get config from the file Blockchain/config.json
  with open('Blockchain/config.json') as json_file:
    config = json.load(json_file)
    reward_per_block = config['REWARD_TOKEN']
    
  return render_template('index.html', title='Dashboard', number_blocks=number_blocks, number_miners=number_miners,
                         first_block_mined_date=first_block_mined_date, last_block_mined_date=last_block_mined_date,
                         reward_per_block=reward_per_block, data=data[-10:])

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