# Bitcoin Data Extractor

A Python tool to extract and parse data from Bitcoin Core blockchain files including block data, chainstate, and undo records.

## Features

- **Block Data Extraction** (`blk*.dat` files)
  - Parse complete blocks with headers and transactions
  - Extract transaction details (inputs, outputs, scripts)
  - Calculate transaction hashes (TXID)
  - Export to JSON format

- **Chainstate Parser** (LevelDB)
  - Extract UTXO (Unspent Transaction Output) data
  - Decode compacted amounts and scripts
  - Retrieve UTXO statistics
  - Track block height and coinbase status

- **Undo Data Parser** (`rev*.dat` files)
  - Parse blockchain reorganization (reorg) undo data
  - Extract per-transaction undo information
  - Analyze block undo statistics

## Installation

### Requirements
- Python 3.7+
- Bitcoin Core (for access to blockchain data files)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Mystique74/bitcoin-data-extractor.git
cd bitcoin-data-extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Extract Block Data

```python
from bitcoin_parser.blk_parser import BlkParser

# Parse blocks from a blk file
parser = BlkParser("/path/to/blk00000.dat")
blocks = parser.parse_file(max_blocks=100)

# Access block data
for block in blocks:
    print(f"Block: {block.header.block_hash}")
    print(f"Transactions: {len(block.transactions)}")
    
    for tx in block.transactions:
        print(f"  TXID: {tx.txid}")
        print(f"  Inputs: {len(tx.inputs)}")
        print(f"  Outputs: {len(tx.outputs)}")
```

### Extract UTXO Data from Chainstate

```python
from bitcoin_parser.leveldb_parser import LevelDBParser

# Open chainstate database
parser = LevelDBParser("/path/to/.bitcoin/chainstate")

# Get UTXO statistics
stats = parser.get_utxo_stats()
print(f"Total UTXOs: {stats['total_utxos']}")
print(f"Total Value: {stats['total_value']} satoshis")

# Extract specific UTXOs
utxos = parser.get_all_utxos(limit=1000)
for utxo in utxos:
    print(f"TXID: {utxo.txid}")
    print(f"Amount: {utxo.amount} satoshis")
    print(f"Script: {utxo.script.hex()}")

parser.close()
```

### Extract Undo Data

```python
from bitcoin_parser.rev_parser import RevParser

# Parse undo blocks from a rev file
parser = RevParser("/path/to/rev00000.dat")
block_undos = parser.parse_file(max_blocks=50)

# Access undo data
for block_undo in block_undos:
    for undo in block_undo.undo_entries:
        print(f"Output {undo.output_index}: {undo.amount} satoshis")
        print(f"Block Height: {undo.block_height}")
        print(f"Script: {undo.script.hex()}")

# Get statistics
stats = parser.get_undo_stats(block_undos)
print(f"Total undo entries: {stats['total_undo_entries']}")
```

## Examples

Run the example scripts to see the extractors in action:

```bash
# Extract and display blocks
python examples/extract_blocks.py

# Extract and display UTXO data
python examples/extract_chainstate.py

# Extract and display undo data
python examples/extract_undo.py
```

## Bitcoin Core File Paths

- **Linux**: `~/.bitcoin/blocks/blk*.dat`, `~/.bitcoin/blocks/rev*.dat`, `~/.bitcoin/chainstate/`
- **macOS**: `~/Library/Application Support/Bitcoin/blocks/`, etc.
- **Windows**: `%APPDATA%\Bitcoin\blocks\`, etc.

## File Format Details

### BLK Files (`blk*.dat`)
- Magic bytes: `f9beb4d9` (mainnet)
- Block size (4 bytes, little-endian)
- Block header (80 bytes)
- Transaction count (varint)
- Transactions

### REV Files (`rev*.dat`)
- Block undo data (per block)
- Transaction count (varint)
- Undo entries for each transaction

### Chainstate (LevelDB)
- Key type 'c': UTXO entries
- Key: txid (32 bytes) + output index (varint)
- Value: amount (varint) + script + height/coinbase flags

## API Reference

### BlkParser
- `parse_file(max_blocks=None)` - Parse all blocks from file
- `parse_block(data, offset)` - Parse single block
- `parse_transaction(data, offset)` - Parse single transaction
- `read_varint(data, offset)` - Read variable-length integer
- `double_sha256(data)` - Calculate block/transaction hash

### LevelDBParser
- `get_all_utxos(limit=None)` - Extract all UTXOs
- `get_utxo_stats()` - Calculate UTXO set statistics
- `parse_utxo_value(key, value)` - Parse single UTXO
- `close()` - Close database connection

### RevParser
- `parse_file(max_blocks=None)` - Parse all undo blocks
- `parse_block_undo(data, offset)` - Parse block undo data
- `parse_undo_data(data, offset)` - Parse single undo entry
- `get_undo_stats(block_undos)` - Calculate undo statistics

## Data Structures

### Block
```python
{
    'header': BlockHeader,
    'transaction_count': int,
    'transactions': List[Transaction]
}
```

### Transaction
```python
{
    'version': int,
    'inputs': List[TransactionInput],
    'outputs': List[TransactionOutput],
    'locktime': int,
    'txid': str,
    'size': int
}
```

### UTXO
```python
{
    'txid': str,
    'output_index': int,
    'amount': int,
    'script_length': int,
    'script': bytes,
    'block_height': int,
    'is_coinbase': bool
}
```

## Notes

- This tool reads Bitcoin Core files directly. Ensure Bitcoin Core is not running when accessing chainstate, as it uses LevelDB which may lock the database.
- Amounts are stored in satoshis (1 BTC = 100,000,000 satoshis)
- Transaction hashes are double SHA256 of the transaction data
- Script data is provided as raw bytes; interpretation depends on script type (P2PKH, P2SH, etc.)

## License

MIT License

## Contributing

Contributions welcome! Feel free to submit issues and pull requests.
