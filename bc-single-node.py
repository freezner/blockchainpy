#!/usr/local/bin/python3

import json
from blockchain import Blockchain

block = Blockchain()

# Mining
def mine():
    last_block = block.last_block
    last_proof = last_block['proof']

    # Proof of work 진행
    proof = block.pow(last_proof, 0, 10000, True)

    if proof > 0:
        response = {
            'message' : 'Complete!',
            'block' : block.chain
        }
    else:
        response = {
            'message' : 'Failed!',
            'block' : None
        }

    print(response)

mine()