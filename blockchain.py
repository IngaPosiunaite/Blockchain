import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

# Define the Blockchain class to manage the entire blockchain logic
class Blockchain:
    def __init__(self):
        # List of transactions that are waiting to be added to a block
        self.current_transactions = []
        # The blockchain itself, which will hold all blocks
        self.chain = []
        # A set to hold all the nodes in the network
        self.nodes = set()

        # Create the genesis block (the first block in the blockchain)
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes in the blockchain network.

        :param address: The URL of the node. Example: 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Handles cases where the URL is provided without a scheme (e.g. '192.168.0.5:5000')
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Validate a blockchain by ensuring each block is correctly linked to the previous one.

        :param chain: The blockchain to validate
        :return: True if the chain is valid, False otherwise
        """
        last_block = chain[0]
        current_index = 1

        # Loop through all blocks in the chain to validate them
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")

            # Check if the block's previous hash matches the hash of the last block
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Validate the Proof of Work (PoW) for the block
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Consensus algorithm: Resolve conflicts by replacing the chain with the longest valid chain in the network.

        :return: True if the chain was replaced, False otherwise
        """
        neighbours = self.nodes
        new_chain = None

        # We are looking for chains that are longer than ours
        max_length = len(self.chain)

        # Retrieve and validate the chains from all nodes in the network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Replace our chain if the retrieved chain is longer and valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace the chain if a longer valid chain is found
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new block in the blockchain.

        :param proof: The proof from the Proof of Work (PoW) algorithm
        :param previous_hash: Hash of the previous block
        :return: The newly created block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),  # Record the current timestamp
            'transactions': self.current_transactions,  # Include all current transactions
            'proof': proof,  # Proof of Work for the new block
            'previous_hash': previous_hash or self.hash(self.chain[-1]),  # Link to the previous block
        }

        # Reset the list of transactions since they are now included in the block
        self.current_transactions = []

        # Append the block to the blockchain
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Create a new transaction that will go into the next mined block.

        :param sender: Address of the sender
        :param recipient: Address of the recipient
        :param amount: Amount of the transaction
        :return: The index of the block that will hold the transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        # Return the index of the next block where this transaction will be added
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # Return the last block in the blockchain
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Create a SHA-256 hash of a block.

        :param block: The block to hash
        :return: The SHA-256 hash of the block
        """
        # Ensure the block dictionary is ordered to get consistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Proof of Work (PoW) algorithm:
        - Find a number p' such that hash(pp') contains leading 4 zeroes
        - Where p is the previous proof, and p' is the new proof

        :param last_block: The last block in the chain
        :return: The proof that solves the PoW challenge
        """
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        # Try different proofs until a valid one is found
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validate the proof by checking if the hash of the concatenation of last_proof, proof, and last_hash has 4 leading zeroes.

        :param last_proof: The previous proof
        :param proof: The current proof
        :param last_hash: The hash of the last block
        :return: True if the proof is valid, False otherwise
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Flask web application setup
app = Flask(__name__)

# Generate a globally unique identifier for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain class
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # Run the Proof of Work algorithm to find the next proof
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # Reward the miner for finding the proof
    # Sender '0' signifies a new coin mined
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Create the new block and add it to the blockchain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    # Return the new block in the response
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Ensure the required fields are present
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    # Return the entire blockchain
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    # Retrieve the list of nodes from the request
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    # Register each node
    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    # Run the consensus algorithm to resolve conflicts
    replaced = blockchain.resolve_conflicts()

    # Return the result of the consensus
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    # Run the Flask web application
    app.run(host='0.0.0.0', port=5000)
