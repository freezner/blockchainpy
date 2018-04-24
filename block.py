#!/usr/local/bin/python3

import hashlib
import json
import requests
from time import time
from uuid import uuid4
from urllib.parse import urlparse

class Block(object):

    def __init__(self):
        self.chain = []
        self.current_transaction = []

        # genesis block
        self.newBlock(prevHash=1, proof=100)

        self.nodes = set()

    def registerNode(self, address):
        parseUrl = urlparse(address)
        self.nodes.add(parseUrl.netloc)

    def vaildChain(self, chain):
        lastBlock = chain[0]
        currentIndex = 1

        while(currentIndex < len(chain)):
            block = chain[currentIndex]

            print(f'{lastBlock}')
            print(f'{block}')
            print("\n-------------------\n")

            if block['prevHash'] != self.hash(lastBlock):
                return False

            if not self.validProof(lastBlock['proof'], block['proof']):
                return False

            lastBlock = block
            currentIndex += 1

        return True

    def resolveConflict(self):
        neighbour = self.nodes
        newChain = None

        maxLength = len(self.chain)

        for node in neighbour:
            response = requests.get('http://{%s}/chain'%(node))

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > maxLength and self.vaildChain(chain):
                    maxLength = length
                    newChain = chain

        if newChain:
            self.chain = newChain
            return True

        return False

    def newBlock(self, proof, prevHash=None):
        blockObject = {
            'index': len(self.chain) + 1,
            'genTime': time(),
            'tran': self.current_transaction,
            'proof': proof,
            'prevHash': prevHash,
        }

        self.current_transaction = []
        self.chain.append(blockObject)

        return blockObject

    def newTransaction(self, sender, receiver, amount):
        self.current_transaction.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
        })

        return self.lastBlock['index'] + 1

    @staticmethod
    def hash(block):
        blockString = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(blockString).hexdigest()

    @property
    def lastBlock(self):
        return self.chain[-1]

    def proofOfWork(self, lastProof):
        proof = 0

        while self.validProof(lastProof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def validProof(lastProof, proof):
        guess = str(lastProof * proof).encode()
        guessHash = hashlib.sha256(guess).hexdigest()
        return guessHash[:4] == '0000'

