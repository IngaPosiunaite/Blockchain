# Blockchain

# Python Blockchain Project

This project implements a simple blockchain in Python. It includes the basic functionalities of a blockchain, such as Proof of Work, transaction management, and consensus algorithm, alongside a Flask API for easy interaction.

## Features

- **Blockchain Structure:** A linked sequence of blocks that includes transaction data, proof (PoW), timestamp, and hash of the previous block.
- **Proof of Work (PoW):** Uses a simple Proof of Work algorithm to secure the blockchain.
- **Transaction Management:** Ability to create new transactions that will be added to future blocks.
- **Consensus Algorithm:** Resolves conflicts by ensuring the longest valid chain is adopted across network nodes.
- **Flask API:** Expose endpoints to interact with the blockchain (e.g., mine new blocks, register nodes, submit transactions).

## Endpoints

### 1. `/mine` (GET)
Mines a new block by solving the Proof of Work and adds it to the blockchain. A reward transaction is included for the miner.

**Response:**
- Index of the new block
- Transactions in the block
- Proof and previous hash

### 2. `/transactions/new` (POST)
Adds a new transaction to the list of pending transactions that will be included in the next mined block.

**Request Body (JSON):**
```json
{
    "sender": "sender_address",
    "recipient": "recipient_address",
    "amount": 50
}


