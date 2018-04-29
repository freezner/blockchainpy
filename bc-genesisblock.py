#!/usr/local/bin/python

import hashlib as hasher
import datetime as date

from bc import Block

def create_genesis_block():
    return Block(0, date.datetime.now(), "Genesis Block", "0")

def next_block(last_block):
    this_index = last_block.index + 1
    this_timestamp = date.datetime.now()
    this_data = "I'm Block " + str(this_index)
    this_hash = last_block.hash

    return Block(this_index, this_timestamp, this_data, this_hash)


###########################################################################


num_of_blocks_to_add = 10

blockchain = [create_genesis_block()]
previous_block = blockchain[0]

blockchain = []

for i in range(0, num_of_blocks_to_add):
    block_to_add = next_block(previous_block)
    blockchain.append(block_to_add)
    previous_block = block_to_add

    print("Block : #{}번째 블록 생성".format(block_to_add.index))
    print("Hash : {}\n".format(block_to_add.hash))