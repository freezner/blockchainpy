#!/usr/local/bin/python3

import hashlib
import json
import requests
from time import time

class Blockchain(object):
    # 체인블럭 구조체 초기화 : 최초의 블럭(제네시스 블럭)을 생성한다.
    def __init__(self):
        # 체인과 트랜잭션 리스트를 초기화
        self.chain = []

        # 트랜젝션 정보를 담는 리스트 (*사용하지 않음)
        self.current_transaction = []

        # 마지막 Block의 정보를 담는데 사용
        self.last_block = None

        # nodes는 노드 주소 정보의 중복을 허용하지 않도록 set(집합자료형)으로 초기화한다.
        self.nodes = set()

        # 제네시스 블럭을 생성한다.
        self.make_block(proof=100, previous_hash=1)

    # 새로운 블럭 생성
    def make_block(self, proof, previous_hash=None):
        """
        index : 블럭의 높이(Height)
        timestamp : 블럭의 생성 시각
        data : 트랜잭션 데이터
        proof : 증명값
        previous_hash : 이전 블럭의 해시값
        """

        block_index = len(self.chain) + 1

        block = {
            'index': block_index,
            'timestamp': time(),
            'data': self.current_transaction,
            'proof': proof,
            'previous_hash': previous_hash,
        }

        # 현재 트랜잭션의 구조체를 초기화한다.
        self.current_transaction = []

        # 블럭체인에 생성된 블럭을 등록한다.
        self.chain.append(block)

        # last_block을 갱신
        self.last_block = self.chain[-1]

        # 블럭 생성 메세지 출력
        print("Generated new block #", block_index)

        # 블럭 구조체 리턴
        return block

    # 이웃 노드로 부터 받은 블럭체인 데이터를 검증
    def vaild_chain(self, chain):
        # 블럭의 prev_hash 정보로 블럭과 블럭이 정상적으로 연결되었는지를 검증하기 위해 last_block에 정의한다.
        last_block = chain[0]

        print("vaild_chain : ", chain[0])

        # 검증할 블럭의 인덱스는 1로 시작한다.
        current_index = 1

        # 블럭 데이터 전체를 while 반복문을 실행하여 검증 로직을 태운다.
        while(current_index < len(chain)):
            # 검증 할 블럭을 정의한다.
            block = chain[current_index]

            # 이전 블럭 정보
            print("last_block info")
            print(f'{last_block}')

            # 검증할 현재 블럭 정보
            print("block info")
            print(f'{block}')
            print("\n-------------------\n")

            # 현재 블럭의 prev_hash 정보와 이전 블럭의 해시값을 비교하여 다르면 체인이 깨진 것으로 간주하고 검증을 종료한다.
            if block['previous_hash'] != self.hash(last_block):
                print("해시 불일치")
                return False

            # 작업 증명(proof)값에 대한 검증이 실패한 경우 유효한 블럭이 아닌 것으로 간주하고 검증을 종료한다. 
            if not self.valid_proof(last_block['proof'], block['proof']):
                print("증명값 불일치")
                return False

            # 마지막 블럭에 현재 블럭을 대입한다.
            last_block = block

            # 블럭체인의 인덱스(높이)를 1만큼 증가 시킨다.
            current_index += 1

        # 체인블럭에 대한 검증이 완료되면 True 리턴
        return True
        
    # 이웃으로 등록된 노드로 부터 블럭체인의 정보를 동기화 한다.
    def consensus(self):
        # 이웃 노드에 대한 json 데이터를 neighbour 변수에 정의한다.
        neighbour = self.nodes

        # 압데이트 할 블럭체인 정보를 담을 변수를 초기화한다.
        new_chain = None

        """
        내가 가지고 있는 체인블럭의 높이를 max_length에 정의한다.
        이것은 자신의 체인블럭과 이웃에게 받은 체인블럭의 높이와 비교하여 짧으면 이웃으로부터 동기화함을 허용하는 조건으로 사용된다.
        """
        max_length = len(self.chain)

        """
        이웃의 노드 주소 정보를 가져온다.
        이웃 노드가 2개 이상인 경우 반복문을 통해 가장 높이가 높은 이웃의 체인블럭을 찾는다.
        가장 높은 높이의 체인블럭을 찾음으로써 최신의 블럭체인 정보로 동기화함을 의미한다.
        """

        for node in neighbour:
            # 노드 주소 정보 확인용
            print("HTTP Request to node API : ", 'http://%s/chain'%(node))

            # 이웃 노드의 chain API를 사용하여 체인 정보를 가져온다.
            response = requests.get('http://%s/chain'%(node))

            # 정상적으로 정보를 받아오게 되면 자신의 체인 정보와 비교하여 반영한다.
            if response.status_code == 200:
                print("status OK")

                try:
                    # 이웃 체인의 높이를 length로 정의
                    length = response.json()['length']

                    # 이웃 체인의 데이터를 chain으로 정의
                    chain = response.json()['chain']
                except:
                    # 블럭 정보를 가져오는데 실패했다면 갱신되지 않도록 Response받은 체인 길이와 체인 리스트를 초기화
                    length = 0
                    chain = []

                # 현재 내가 가진 체인보다 이웃의 체인 높이가 크고 체인 검증에 성공했다면
                # max_length와 new_chain 변수에 업데이트 할 이웃 노드의 체인 정보를 반영한다.
                if length > max_length and self.vaild_chain(chain):
                    max_length = length
                    new_chain = chain

                    print("체인 갱신 완료")
                else:
                    print("체인 변동 없음")

        # new_chain에 정보가 존재한다면 자신의 체인 정보를 new_chain(검증된 이웃 체인 정보)로 업데이트하고 True를 리턴한다.
        if new_chain:
            self.chain = new_chain
            return True

        # 업데이트 할 내용이 없다면 (이미 자신의 체인 정보가 최신의 것이거나 이웃 노드보다 길이가 길다면) False를 리턴한다.
        return False

    # 트랜잭션(거래 장부) 리스트 추가 (*사용하지 않음)
    def make_transaction(self, tx_input, tx_output, amount):
        # 보내는 사람의 지갑 해시와 받는 사람의 지값 해시, 그리고 거래 금액을 정의한다.
        self.current_transaction.append({
            'input': tx_input,
            'output': tx_output,
            'amount': amount,
        })

        # 현재 블럭의 길이를 1만큼 증가시킨다.
        return self.last_block['index'] + 1

    # Hashing 함수 : Block을 sha256으로 Hashing 하는데 사용한다.
    @staticmethod
    def hash(block):
        # 블럭 데이터를 json.dumps를 이용해 문자열로 인코딩 한다.
        blockString = json.dumps(block, sort_keys=True).encode()

        # 문자열로 변환된 블럭 데이터를 sha256으로 Hashing하여 리턴.
        return hashlib.sha256(blockString).hexdigest()

    # 작업 검증 (PoW)
    def pow(self, last_proof, stream = 0, limit_count_works = 10000, trace=False):
        print("작업 검증 시작..")

        # 증명 값은 0부터 시작
        if stream == 0:
            proof = 0
        else:
            proof = limit_count_works

        # 이전 블럭의 proof 값과 대조하여 nonce 값을 찾는다.
        while self.valid_proof(last_proof, proof) == None:
            # nonce를 찾지 못했다면 None이 리턴되고 proof 값을 변화시켜 다시 nonce 값을 찾는다.
            if stream == 0:
                if proof >= limit_count_works:
                    print("검색 횟수 초과!")
                    # return False

                proof += 1
            else:
                if proof == 0:
                    print("검색 횟수 초과!")
                    # return False

                proof -= 1

            if trace == True:
                # proof 값을 출력
                print(proof, "번째 찾는 중..")

        # nonce 값을 찾은 경우 메세지 출력
        print("완료 - Proof : ", proof)

        # nonce 값을 찾았다면 작업 검증 성공에 대해 결과 값을 출력
        return proof

    # 해시 검증
    @staticmethod
    def valid_proof(last_proof, proof):
        # nonce 값 설정
        nonce = "0000"

        # 이전 블럭의 proof(x) 값과 현재 블럭의 proof(y) 값을 곱한 후 문자열로 인코딩한다.
        guess = str(last_proof * proof).encode()

        # 두 블럭의 proof 값을 곱한 문자열을 sha256으로 해싱한다.
        guessHash = hashlib.sha256(guess).hexdigest()

        """
        이 코드에서 구현되진 않았지만 비트코인에서는 이 nonce 값을 마이닝 시간을 비교하여 난이도를 조절하는데 사용된다.
        블럭 1개가 마이닝되는 시간(10분)을 기준으로 기준 시간 미만으로 완료되는 난이도 상승, 초과하면 난이도 하락
        nonce의 자릿수가 증가함에 따라 난이도는 기하급수적으로 상승한다.
        """
        if guessHash[:len(nonce)] == nonce:
            return nonce
        else:
            return None

