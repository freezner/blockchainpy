#!/usr/local/bin/python3

from flask import Flask, jsonify, request, redirect
import json
import requests

from blockchain import Blockchain

block = Blockchain()

node = Flask(__name__)
# node.debug = True

"""
1. Genesis Block을 생성한다.
2. Nonce 값을 찾기 위해 마이닝을 진행한다.
3. Nonce 값을 찾으면 Chain에 Block을 추가한다.
4. 각 Node에 /update_chain API를 호출한다. (현재 상대 노드는 1개)
5. /update_chain API를 받은 Node는 Consensus를 진행한다.
6. Chain Update가 끝나면 다음 BLock을 생성한다.
"""

# 자신이 사용할 Port
my_port = 5001

# 전파 할 Node의 IP Address, Port
peer_nodes = ['127.0.0.1:5000']

# Chain 정보 조회
@node.route('/chain', methods=['GET'])
def chain():
    response = {
        'chain' : block.chain,
        'length' : len(block.chain)
    }

    return jsonify(response), 200

# Mining
@node.route('/mine', methods=['GET'])
def mine():
    last_block = block.last_block
    last_proof = last_block['proof']

    # Proof of work 진행
    proof = block.pow(last_proof)

    if proof > 0:
        try:
            # Response를 기다릴 경우 상대 노드에서 Request.get으로 요청이 들어 올때 무한 대기 상태에 빠짐. 강제 타임아웃을 줌
            requests.get('http://{}/update_chain'.format(peer_nodes[0]), timeout=1)      
        except:
            print("continue")

        print('Noti Complete.')

        # 새 Block 생성을 위한 Previous Block Hash를 구함
        previous_hash = block.hash(last_block)

        # 다음 Block 생성
        block.make_block(proof, previous_hash)

        response = {
            'message' : 'Complete!',
            'block' : block.chain
        }
    else:
        response = {
            'message' : 'Failed!',
            'block' : None
        }

    return jsonify(response), 200 

# 상대 Node들에게 Miining 완료를 알림
@node.route('/update_chain', methods=['GET'])
def update_chain():
    # Consensus 과정에서 알림을 보낸 Node의 블럭 
    block.nodes = peer_nodes

    block.consensus()

    response = {
        'message' : 'update new chain',
        'chain' : block.chain,
        'length' : len(block.chain)
    }

    return jsonify(response), 200

if __name__ == '__main__':
    node.run(host='127.0.0.1', port=my_port)