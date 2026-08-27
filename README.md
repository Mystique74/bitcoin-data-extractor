# Bitcoin Data Extractor

A Python tool to extract and parse data from Bitcoin Core blockchain files including block data, chainstate, and undo records. Includes advanced analysis tools for address tracking, transaction graph analysis, and fee analysis.

## Features

### Core Extraction Tools
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

### Advanced Analysis Tools
- **Address Tracking**
  - Identify and classify Bitcoin addresses by script type (P2PKH, P2SH, P2WPKH, etc.)
  - Track address balances and activity
  - Find top addresses by balance
  - Monitor transaction counts per address

- **Transaction Graph Analysis**
  - Build transaction dependency graphs
  - Trace transaction ancestry (parents/inputs)
  - Find transaction descendants (coins spent in later transactions)
  - Detect potential double-spend attempts

- **Fee Analysis**
  - Calculate transaction fees and fee rates
  - Analyze fee distributions across blocks
  - Identify high-fee transactions
  - Track fee trends over time
  - Generate fee market statistics

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

## Quick Start

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

### Track Bitcoin Addresses

```python
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import AddressTracker

parser = BlkParser("/path/to/blk00000.dat")
blocks = parser.parse_file(max_blocks=100)

tracker = AddressTracker()
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        tracker.add_transaction(tx.txid, tx.inputs, tx.outputs, block_idx)

# Get top addresses by balance
top_addresses = tracker.get_top_addresses(limit=10)
for address, balance in top_addresses:
    print(f"{address}: {balance} satoshis")

# Get statistics
stats = tracker.get_address_stats()
print(f"Total Addresses: {stats['total_unique_addresses']}")
print(f"Total Balance: {stats['total_balance']} satoshis")
```

### Analyze Transaction Fees

```python
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import FeeAnalyzer

parser = BlkParser("/path/to/blk00000.dat")
blocks = parser.parse_file(max_blocks=100)

analyzer = FeeAnalyzer()
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        if len(tx.inputs) > 0:  # Skip coinbase
            analyzer.analyze_transaction(
                tx.txid, tx.inputs, tx.outputs, block_idx
            )

# Get fee statistics
stats = analyzer.get_fee_statistics()
print(f"Average Fee: {stats['average_fee']:.2f} satoshis")
print(f"Average Fee Rate: {stats['average_fee_rate']:.4f} sat/byte")
```

### Analyze Transaction Graphs

```python
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import TransactionGraph

parser = BlkParser("/path/to/blk00000.dat")
blocks = parser.parse_file(max_blocks=100)

graph = TransactionGraph()
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        graph.add_transaction(tx.txid, tx.inputs, block_idx)

# Trace transaction ancestry
chain = graph.get_transaction_chain("some_txid", depth=5)
print(f"Transaction chain: {chain}")

# Find descendant transactions
descendants = graph.get_transaction_descendants("some_txid")
print(f"Found {len(descendants)} descendants")

# Detect double-spends
double_spends = graph.find_double_spend_attempts()
print(f"Found {len(double_spends)} potential double-spends")
```

## Examples

Run the example scripts to see all features in action:

### Basic Examples

```bash
# Extract and display blocks
python examples/extract_blocks.py

# Extract and display UTXO data
python examples/extract_chainstate.py

# Extract and display undo data
python examples/extract_undo.py
```

### Advanced Analysis Examples

```bash
# Analyze Bitcoin addresses
python examples/analyze_addresses.py

# Analyze transaction graphs
python examples/analyze_transaction_graph.py

# Analyze transaction fees
python examples/analyze_fees.py
```

Each example includes:
- Setup instructions
- Detailed comments
- Multiple analysis functions
- JSON export capabilities
- Customizable parameters

## Documentation

### Main Resources
- **[README.md](README.md)** - This file, overview and quick start
- **[ANALYSIS_GUIDE.md](ANALYSIS_GUIDE.md)** - Comprehensive guide to advanced analysis tools

### Detailed Guides
- Address Tracking - See [ANALYSIS_GUIDE.md#address-tracking](ANALYSIS_GUIDE.md#address-tracking)
- Transaction Graphs - See [ANALYSIS_GUIDE.md#transaction-graph-analysis](ANALYSIS_GUIDE.md#transaction-graph-analysis)
- Fee Analysis - See [ANALYSIS_GUIDE.md#fee-analysis](ANALYSIS_GUIDE.md#fee-analysis)
- Setup Instructions - See [ANALYSIS_GUIDE.md#setup-instructions](ANALYSIS_GUIDE.md#setup-instructions)
- Complete Examples - See [ANALYSIS_GUIDE.md#complete-examples](ANALYSIS_GUIDE.md#complete-examples)
- Troubleshooting - See [ANALYSIS_GUIDE.md#troubleshooting](ANALYSIS_GUIDE.md#troubleshooting)

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

### Core Parsers

#### BlkParser
```python
parser = BlkParser(filepath)
blocks = parser.parse_file(max_blocks=None)
block, offset = parser.parse_block(data, offset)
tx, offset = parser.parse_transaction(data, offset)
value, offset = parser.read_varint(data, offset)
hash = parser.double_sha256(data)
```

#### LevelDBParser
```python
parser = LevelDBParser(db_path)
utxos = parser.get_all_utxos(limit=None)
stats = parser.get_utxo_stats()
utxo = parser.parse_utxo_value(key, value)
parser.close()
```

#### RevParser
```python
parser = RevParser(filepath)
block_undos = parser.parse_file(max_blocks=None)
block_undo, offset = parser.parse_block_undo(data, offset)
undo_data, offset = parser.parse_undo_data(data, offset)
stats = parser.get_undo_stats(block_undos)
```

### Analysis Tools

#### AddressTracker
```python
tracker = AddressTracker()
tracker.add_transaction(txid, inputs, outputs, block_height)
info = tracker.get_address_info(address)
top = tracker.get_top_addresses(limit=100)
stats = tracker.get_address_stats()
```

#### TransactionGraph
```python
graph = TransactionGraph()
graph.add_transaction(txid, inputs, block_height)
chain = graph.get_transaction_chain(txid, depth=10)
descendants = graph.get_transaction_descendants(txid, depth=10)
double_spends = graph.find_double_spend_attempts()
```

#### FeeAnalyzer
```python
analyzer = FeeAnalyzer()
analysis = analyzer.analyze_transaction(txid, inputs, outputs, block_height)
stats = analyzer.get_fee_statistics()
block_stats = analyzer.get_fee_by_block()
```

#### ScriptAnalyzer
```python
script_type = ScriptAnalyzer.classify_script(script)
pubkey_hash = ScriptAnalyzer.extract_pubkey_hash(script)
script_hash = ScriptAnalyzer.extract_script_hash(script)
witness_pubkey = ScriptAnalyzer.extract_witness_pubkey(script)
witness_script = ScriptAnalyzer.extract_witness_script(script)
```

## Data Structures

### Block
```python
Block:
  - header: BlockHeader
    - version: int
    - previous_block_hash: str
    - merkle_root: str
    - timestamp: int
    - bits: int
    - nonce: int
    - block_hash: str
  - transaction_count: int
  - transactions: List[Transaction]
```

### Transaction
```python
Transaction:
  - version: int
  - inputs: List[TransactionInput]
    - previous_output_hash: str
    - previous_output_index: int
    - script_length: int
    - script: bytes
    - sequence: int
  - outputs: List[TransactionOutput]
    - value: int
    - script_length: int
    - script: bytes
  - locktime: int
  - txid: str
  - size: int
```

### UTXO
```python
UTXO:
  - txid: str
  - output_index: int
  - amount: int
  - script_length: int
  - script: bytes
  - block_height: int
  - is_coinbase: bool
```

### AddressInfo
```python
AddressInfo:
  - address: str
  - script_type: str (P2PKH, P2SH, P2WPKH, P2WSH, etc.)
  - balance: int
  - transaction_count: int
  - first_seen_block: int
  - last_seen_block: int
  - is_change: bool
  - related_addresses: Set[str]
```

### FeeAnalysis
```python
FeeAnalysis:
  - txid: str
  - fee: int
  - fee_rate: float
  - input_count: int
  - output_count: int
  - size: int
  - block_height: int
```

## Important Notes

- **Bitcoin Core Must Be Stopped**: When accessing chainstate LevelDB, Bitcoin Core must not be running (it locks the database)
- **Amounts in Satoshis**: All amounts are in satoshis (1 BTC = 100,000,000 satoshis)
- **Transaction Hashes**: Double SHA256 of the transaction data
- **Script Data**: Provided as raw bytes; interpretation depends on script type (P2PKH, P2SH, etc.)
- **Large Datasets**: Processing many blocks can use significant memory - start with smaller block ranges

## Performance Tips

- Use an SSD for faster blockchain data access
- Start with fewer blocks to test your setup
- Process blocks in batches
- Close other applications to free up memory
- Filter unnecessary transactions
- Use PyPy for faster Python execution (if compatible)

## Troubleshooting

### "Permission Denied" when accessing chainstate
Stop Bitcoin Core before accessing the chainstate database.

### "ModuleNotFoundError" in examples
Ensure you're running from the project root directory.

### Out of Memory
Process fewer blocks at a time by reducing `max_blocks` parameter.

### No data extracted
Verify the file path is correct and the file contains data:
```bash
ls -lh /path/to/bitcoin/blocks/blk*.dat
```

See [ANALYSIS_GUIDE.md#troubleshooting](ANALYSIS_GUIDE.md#troubleshooting) for more help.

## Project Structure

```
bitcoin-data-extractor/
├── bitcoin_parser/
│   ├── __init__.py
│   ├── blk_parser.py          # Block file parser
│   ├── leveldb_parser.py       # Chainstate LevelDB parser
│   ├── rev_parser.py           # Undo file parser
│   └── analysis.py             # Advanced analysis tools
├── examples/
│   ├── extract_blocks.py       # Block extraction example
│   ├── extract_chainstate.py   # Chainstate extraction example
│   ├── extract_undo.py         # Undo extraction example
│   ├── analyze_addresses.py    # Address tracking example
│   ├── analyze_transaction_graph.py  # Graph analysis example
│   └── analyze_fees.py         # Fee analysis example
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── ANALYSIS_GUIDE.md          # Comprehensive analysis guide
```

## License

MIT License

## Contributing

Contributions welcome! Feel free to submit issues and pull requests.

## Roadmap

Future enhancements:
- [ ] Command-line interface (CLI)
- [ ] REST API endpoints
- [ ] Web dashboard
- [ ] Database export (SQLite, PostgreSQL)
- [ ] CSV export
- [ ] Real-time blockchain monitoring
- [ ] Script disassembler
- [ ] Witness data parser (SegWit)
- [ ] Taproot (P2TR) support
- [ ] Machine learning analysis
- [ ] Performance benchmarks
- [ ] Unit and integration tests

## Support

For issues, questions, or suggestions:
1. Check [ANALYSIS_GUIDE.md](ANALYSIS_GUIDE.md) for detailed documentation
2. Review example scripts in `examples/` directory
3. Open a GitHub issue with detailed information

## Related Resources

- [Bitcoin Core Documentation](https://bitcoin.org/en/developer-documentation)
- [Bitcoin Script Guide](https://en.bitcoin.it/wiki/Script)
- [Bitcoin Transaction Format](https://en.bitcoin.it/wiki/Transaction)
- [Bitcoin Block Format](https://en.bitcoin.it/wiki/Block)
