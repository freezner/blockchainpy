#!/usr/local/bin/python3

from flask import Flask, jsonify, request
import flask
import json
import hashlib
from textwrap import dedent
from uuid import uuid4

from block import Block

app = Flask(__name__)

nodeIdentifier = str(uuid4()).replace('-', '')

block = Block()

@app.route('/mine', methods=['GET'])
def mine():
    lastBlock = block.lastBlock
    lastProof = lastBlock['proof']

    proof = block.proofOfWork(lastProof)

    block.newTransaction(
        sender = '0',
        receiver = nodeIdentifier,
        amount = 1
    )

    prevHash = block.hash(lastBlock)
    blockObj = block.newBlock(proof, prevHash)

    response = {
        'message' : 'new block forged',
        'index' : blockObj['index'],
        'tran' : blockObj['tran'],
        'proof' : blockObj['proof'],
        'prevHash' : blockObj['prevHash']
    }

    return jsonify(response), 200

@app.route('/transaction/new', methods=['POST'])
def newTransaction():
    values = request.get_json(silent=True)

    if not values == None:
        print("served parameter", request.get_json())
        values = request.get_json()
    else:
        print("Not served parameter, Generating new TX")

        sender_data = 'New generating sender hash!'
        receiver_text = 'New generating receiver hash!' 
        sender_hash = hashlib.sha256(sender_data.encode()).hexdigest()
        receiver_hash = hashlib.sha256(receiver_text.encode()).hexdigest()
        amount = 5

        values = {
            "sender": sender_hash,
            "receiver": receiver_hash,
            "amount": amount
        }

    required = ['sender', 'receiver', 'amount']
    if not all(k in values for k in required):
        return 'missing values', 400

    index = block.newTransaction(values['sender'], values['receiver'], values['amount'])

    response = {'message': 'Transaction will be added to block {0}'.format(index)}

    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def fullChain():
    res = {
        'chain': block.chain,
        'length': len(block.chain),
    }

    return flask.jsonify(res), 200

@app.route('/nodes/register', methods=['POST'])
def registerNode():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error : 검증할 노드 리스트가 없습니다.", 400

    response = {
        'message' : '새로운 노드가 생성되었습니다.',
        'total_ndoes' : list(block.nodes),
    }

    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['POST'])
def consensus():
    replaced = block.resolveConflict()

    if replaced:
        response = {
            'message' : '체인이 변경 되었습니다.',
            'newChain' : block.chain,
        }
    else:
        response = {
            'message' : '체인이 검증 되었습니다.',
            'chain' : block.chain,
        }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)