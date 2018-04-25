#!/usr/local/bin/python3

import hashlib
import json
import requests
from time import time
from uuid import uuid4
from urllib.parse import urlparse

class Block(object):
    # 체인블럭 구조체 초기화 : 최초의 블럭(제네시스 블럭)을 생성한다.
    def __init__(self):
        # 체인과 트랜잭션 리스트를 초기화
        self.chain = []
        self.current_transaction = []

        # 블럭을 생성한다.
        self.newBlock(prevHash=1, proof=100)

        # nodes는 노드 주소 정보의 중복을 허용하지 않도록 set(집합자료형)으로 초기화한다.
        self.nodes = set()

    # 노드 주소 등록 : 블럭체인 정보를 전파할 이웃 노드를 등록할때 사용한다.
    def registerNode(self, address):
        # address로 들어온 파라미터를 url 형태의 정제를 위해 urlparse 합수를 적용한다.
        parseUrl = urlparse(address)

        # urlparse를 적용한 address(parseUrl)를 netloc 메서드를 이용해 host:port 형식으로 받는다.
        # 그리고 노드에 추가한다. 여기서 nodes는 set() 초기화 되었기 때문에 중복되는 주소는 들어갈 수 없다.
        self.nodes.add(parseUrl.netloc)

    # 이웃 노드로 부터 받은 블럭체인 데이터를 검증
    def vaildChain(self, chain):
        # 블럭의 prevHash 정보로 블럭과 블럭이 정상적으로 연결되었는지를 검증하기 위해 lastBlock에 정의한다.
        lastBlock = chain[0]

        # 검증할 블럭의 인덱스는 1로 시작한다.
        currentIndex = 1

        # 블럭 데이터 전체를 while 반복문을 실행하여 검증 로직을 태운다.
        while(currentIndex < len(chain)):
            # 검증 할 블럭을 정의한다.
            block = chain[currentIndex]

            # 이전 블럭 정보
            print(f'{lastBlock}')

            # 검증할 현재 블럭 정보
            print(f'{block}')
            print("\n-------------------\n")

            # 현재 블럭의 prevHash 정보와 이전 블럭의 해시값을 비교하여 다르면 체인이 깨진 것으로 간주하고 검증을 종료한다.
            if block['prevHash'] != self.hash(lastBlock):
                return False

            # 작업 증명(proof)값에 대한 검증이 실패한 경우 유효한 블럭이 아닌 것으로 간주하고 검증을 종료한다. 
            if not self.validProof(lastBlock['proof'], block['proof']):
                return False

            # 마지막 블럭에 현재 블럭을 대입한다.
            lastBlock = block

            # 블럭체인의 인덱스(높이)를 1만큼 증가 시킨다.
            currentIndex += 1

        # 체인블럭에 대한 검증이 완료되면 True 리턴
        return True

    # 이웃으로 등록된 노드로 부터 블럭체인의 정보를 동기화 한다.
    def resolveConflict(self):
        # 이웃 노드에 대한 json 데이터를 neighbour 변수에 정의한다.
        neighbour = self.nodes

        # 압데이트 할 블럭체인 정보를 담을 변수를 초기화한다.
        newChain = None

        """
        내가 가지고 있는 체인블럭의 높이를 maxLength에 정의한다.
        이것은 자신의 체인블럭과 이웃에게 받은 체인블럭의 높이와 비교하여 짧으면 이웃으로부터 동기화함을 허용하는 조건으로 사용된다.
        """
        maxLength = len(self.chain)

        """
        이웃의 노드 주소 정보를 가져온다.
        이웃 노드가 2개 이상인 경우 반복문을 통해 가장 높이가 높은 이웃의 체인블럭을 찾는다.
        가장 높은 높이의 체인블럭을 찾음으로써 최신의 블럭체인 정보로 동기화함을 의미한다.
        """
        for node in neighbour:
            # 노드 주소 정보 확인용
            print("node is : ", node)

            # 이웃 노드의 chain API를 사용하여 체인 정보를 가져온다.
            response = requests.get('http://%s/chain'%(node))

            # 정상적으로 정보를 받아오게 되면 자신의 체인블럭정보와 비교하여 반영한다.
            if response.status_code == 200:
                # 이웃 블럭체인의 높이를 length로 정의
                length = response.json()['length']

                # 이웃 블럭체인의 블럭데이터를 chain으로 정의
                chain = response.json()['chain']

                """
                현재 내가 가진 체인블럭보다 이웃의 체인블럭 높이가 크고 블럭체인 검증에 성공했다면
                maxLength와 newChain 변수에 업데이트 할 이웃 노드의 블럭체인 정보를 넣는다.
                """
                if length > maxLength and self.vaildChain(chain):
                    maxLength = length
                    newChain = chain

        # newChain에 정보가 존재한다면 자신 노드의 블럭체인 정보를 newChain(검증된 이웃 블럭체인 정보)로 업데이트하고 True를 리턴한다.
        if newChain:
            self.chain = newChain
            return True

        # 업데이트 할 내용이 없다면 (이미 자신의 블럭체인 정보가 최신의 것이라면) False를 리턴한다.
        return False

    # 새로운 블럭 생성
    def newBlock(self, proof, prevHash=None):
        """
        index : 블럭의 높이(Height)
        genTime : 블럭의 생성 시각
        tran : 현재 트랜잭션(?)
        proof : 증명값(?)
        prevHash : 이전 블럭의 해시값 (최초 등록되는 블럭은 prevHash가 없으므로 제네시스 블럭이 된다.)
        """
        blockObject = {
            'index': len(self.chain) + 1,
            'genTime': time(),
            'tran': self.current_transaction,
            'proof': proof,
            'prevHash': prevHash,
        }

        # 현재 트랜잭션의 구조체를 초기화한다.
        self.current_transaction = []

        # 블럭체인에 생성된 블럭을 등록한다.
        self.chain.append(blockObject)

        # 블럭 생성 메세지 출력
        print("Generated new block")

        # 블럭 구조체 리턴
        return blockObject

    # 트랜잭션(거래 장부) 리스트 추가
    def newTransaction(self, sender, receiver, amount):
        # 보내는 사람의 지갑 해시와 받는 사람의 지값 해시, 그리고 거래 금액을 정의한다.
        self.current_transaction.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
        })

        # 현재 블럭의 길이를 1만큼 증가시킨다.
        return self.lastBlock['index'] + 1

    # 블럭 해시 : 블럭을 sha256으로 해싱하는데 사용한다.
    @staticmethod
    def hash(block):
        # 블럭 데이터를 json.dumps를 이용해 문자열로 인코딩 한다.
        blockString = json.dumps(block, sort_keys=True).encode()

        # 문자열로 변환된 블럭 데이터를 sha256으로 해싱한다.
        return hashlib.sha256(blockString).hexdigest()

    # 마지막 블럭에 대한 정보
    @property
    def lastBlock(self):
        # 현재 체인블럭의 마지막 인덱스를 가진 블럭
        return self.chain[-1]

    # 작업 검증 (PoW)
    def proofOfWork(self, lastProof, stream = 0, maxWorkCount = 1000):
        # 증명 값은 0부터 시작
        if stream == 0:
            proof = 0
        else:
            proof = maxWorkCount

        # 이전 블럭의 proof 값과 대조하여 nonce 값을 찾는다.
        while self.validProof(lastProof, proof) is False:
            # nonce를 찾지 못했다면 False가 리턴되고 proof 값을 변화시켜 다시 nonce 값을 찾는다.
            # 단, 횟수는 10000번으로 제한한다.
            if stream == 0:
                if proof == maxWorkCount:
                    print("못찾겠다!")
                    # return False

                proof += 1
            else:
                if proof == 0:
                    print("못찾겠다!")
                    # return False

                proof -= 1

            # proof 값을 출력
            print(proof, " 번째 찾는 중..")

        # nonce 값을 찾은 경우 메세지 출력
        print("내가 찾았지롱", proof)

        # nonce 값을 찾았다면 작업 검증 성공에 대해 proof(증명) 값을 출력
        return proof

    # 해시 검증
    @staticmethod
    def validProof(lastProof, proof):
        # nonce 값 정의
        nonce = "000"

        # 이전 블럭의 proof(x) 값과 현재 블럭의 proof(y) 값을 곱한 후 문자열로 인코딩한다.
        guess = str(lastProof * proof).encode()

        # 두 블럭의 proof 값을 곱한 문자열을 sha256으로 해싱한다.
        guessHash = hashlib.sha256(guess).hexdigest()

        """
        이 코드에서 구현되진 않았지만 비트코인에서는 이 nonce 값을 마이닝 시간을 비교하여 난이도를 조절하는데 사용된다.
        블럭 1개가 마이닝되는 시간(10분)을 기준으로 기준 시간 미만으로 완료되는 난이도 상승, 초과하면 난이도 하락
        nonce의 자릿수가 증가함에 따라 난이도는 기하급수적으로 상승한다.
        이 코드에서는 해시 앞 n자리 값이 nonce 값이 되어야 작업 증명이 완료된다.
        """
        return guessHash[:len(nonce)] == nonce

