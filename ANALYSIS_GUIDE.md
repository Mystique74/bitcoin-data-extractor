# Advanced Analysis Guide

This guide provides detailed instructions for using the advanced Bitcoin blockchain analysis tools.

## Table of Contents

1. [Address Tracking](#address-tracking)
2. [Transaction Graph Analysis](#transaction-graph-analysis)
3. [Fee Analysis](#fee-analysis)
4. [Setup Instructions](#setup-instructions)
5. [Complete Examples](#complete-examples)

---

## Address Tracking

### Overview

Address tracking tools analyze Bitcoin transactions to identify and monitor addresses, track their balances, and categorize them by script type (P2PKH, P2SH, P2WPKH, etc.).

### Features

- **Script Type Classification**: Automatically identify address types (P2PKH, P2SH, SegWit, etc.)
- **Balance Tracking**: Track total balance received by each address
- **Activity Analysis**: Monitor when addresses first and last appear in the blockchain
- **Transaction Counting**: Track number of transactions per address
- **Top Address Identification**: Find richest addresses in analyzed blocks

### Key Classes

#### `ScriptAnalyzer`
Analyzes Bitcoin scripts to determine address types and extract address data.

**Methods:**
- `extract_pubkey_hash(script)` - Extract hash from P2PKH scripts
- `extract_script_hash(script)` - Extract hash from P2SH scripts
- `extract_witness_pubkey(script)` - Extract hash from P2WPKH scripts
- `extract_witness_script(script)` - Extract hash from P2WSH scripts
- `classify_script(script)` - Determine script type

#### `AddressTracker`
Tracks all addresses and their activity across transactions.

**Methods:**
- `add_transaction(txid, inputs, outputs, block_height)` - Process a transaction
- `get_address_info(address)` - Get information about specific address
- `get_top_addresses(limit)` - Get richest addresses
- `get_address_stats()` - Get overall statistics

**Data Structures:**

```python
AddressInfo:
  - address: str                    # Address identifier
  - script_type: str                # P2PKH, P2SH, P2WPKH, etc.
  - balance: int                    # Total satoshis received
  - transaction_count: int          # Number of transactions
  - first_seen_block: int           # First block containing address
  - last_seen_block: int            # Most recent block with address
  - is_change: bool                 # Whether it's a change address
  - related_addresses: Set[str]     # Associated addresses
```

### Usage Example

```python
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import AddressTracker

# Parse blocks
parser = BlkParser("/path/to/blk00000.dat")
blocks = parser.parse_file(max_blocks=100)

# Create tracker
tracker = AddressTracker()

# Process blocks
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        tracker.add_transaction(
            txid=tx.txid,
            inputs=tx.inputs,
            outputs=tx.outputs,
            block_height=block_idx
        )

# Get statistics
stats = tracker.get_address_stats()
print(f"Total Addresses: {stats['total_unique_addresses']}")
print(f"Total Balance: {stats['total_balance']} satoshis")

# Get top addresses
top_addresses = tracker.get_top_addresses(limit=10)
for address, balance in top_addresses:
    print(f"{address}: {balance} satoshis")

# Analyze specific address
info = tracker.get_address_info("P2PKH-abc123...")
print(f"Balance: {info.balance} satoshis")
print(f"Transactions: {info.transaction_count}")
```

### Running the Address Tracking Example

```bash
# 1. Edit examples/analyze_addresses.py
# 2. Update BLK_FILE variable with your blk*.dat file path
# 3. Uncomment the main code section
# 4. Run:
python examples/analyze_addresses.py

# Output will show:
# - Total unique addresses
# - Address distribution by type
# - Top 20 addresses by balance
# - JSON export of all addresses
```

### Output Format

When exported to JSON, address data looks like:

```json
[
  {
    "address": "P2PKH-a1b2c3d4e5f6...",
    "script_type": "P2PKH",
    "balance": 50000000,
    "balance_btc": 0.50000000,
    "transaction_count": 5,
    "first_seen_block": 0,
    "last_seen_block": 50
  },
  ...
]
```

---

## Transaction Graph Analysis

### Overview

Transaction graph analysis builds a directed graph of how Bitcoin transactions connect to each other through their inputs and outputs. This allows tracing transaction chains, finding ancestors/descendants, and detecting double-spend attempts.

### Features

- **Chain Analysis**: Trace transaction ancestry back through inputs
- **Descendant Tracking**: Find all transactions spending a transaction's outputs
- **Double-Spend Detection**: Identify outputs spent by multiple transactions
- **Graph Statistics**: Analyze transaction connectivity patterns

### Key Classes

#### `TransactionGraph`
Builds and analyzes transaction dependency graph.

**Methods:**
- `add_transaction(txid, inputs, block_height)` - Add transaction to graph
- `get_transaction_chain(txid, depth)` - Get ancestor chain (parents)
- `get_transaction_descendants(txid, depth)` - Get descendant transactions
- `find_double_spend_attempts()` - Detect double-spends

**Data Structures:**

```python
graph: Dict[str, List[str]]           # txid -> [child_txids]
reverse_graph: Dict[str, List[str]]   # txid -> [parent_txids]
transactions: Dict[str, Dict]         # txid -> {block_height, input_count, chain_length}
```

### Usage Example

```python
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import TransactionGraph

# Parse blocks
parser = BlkParser("/path/to/blk00000.dat")
blocks = parser.parse_file(max_blocks=100)

# Create graph
graph = TransactionGraph()

# Build graph
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        graph.add_transaction(
            txid=tx.txid,
            inputs=tx.inputs,
            block_height=block_idx
        )

# Analyze transaction chain (ancestors)
chain = graph.get_transaction_chain("some_txid", depth=5)
print(f"Transaction chain depth: {len(chain)}")
for tx in chain:
    print(f"  - {tx}")

# Analyze descendants (spending this transaction's outputs)
descendants = graph.get_transaction_descendants("some_txid", depth=5)
print(f"Found {len(descendants)} descendant transactions")

# Find double-spend attempts
double_spends = graph.find_double_spend_attempts()
for attempt in double_spends:
    print(f"Output {attempt['output']} spent by {attempt['count']} transactions:")
    for spender in attempt['spenders']:
        print(f"  - {spender}")
```

### Running the Transaction Graph Example

```bash
# 1. Edit examples/analyze_transaction_graph.py
# 2. Update BLK_FILE variable with your blk*.dat file path
# 3. Uncomment the main code section
# 4. Run:
python examples/analyze_transaction_graph.py

# Output will show:
# - Transaction graph statistics
# - Double-spend attempts
# - Transaction chains and descendants
# - JSON export of graph
```

### Output Format

Graph statistics:

```
TRANSACTION GRAPH STATISTICS
Total Transactions: 2,543
Transactions with Children: 1,892
Average Children per Transaction: 1.34
Transaction with Most Children: abc123def456...
  Children Count: 42
```

Transaction chain example:

```
TRANSACTION CHAIN ANALYSIS: abc123def456...
Chain depth: 5 transactions

└─ Generation 0
   TXID: abc123def456...
   Block: 100
   Inputs: 1

  └─ Generation 1
     TXID: def456ghi789...
     Block: 98
     Inputs: 2
     ...
```

---

## Fee Analysis

### Overview

Fee analysis tools calculate and analyze transaction fees, identify trends, and help understand the fee market in analyzed blocks.

### Features

- **Fee Calculation**: Calculate actual fees (input value - output value)
- **Fee Rate Analysis**: Calculate satoshis per byte
- **Distribution Analysis**: Analyze fee distribution patterns
- **Trend Analysis**: Track fee changes over blocks
- **High-Fee Detection**: Identify unusually expensive transactions
- **Fee Statistics**: Average, median, min, max, percentiles

### Key Classes

#### `FeeAnalyzer`
Analyzes transaction fees and fee rates.

**Methods:**
- `analyze_transaction(txid, inputs, outputs, block_height)` - Analyze single transaction
- `get_fee_statistics()` - Get overall fee statistics
- `get_fee_by_block()` - Get statistics grouped by block
- `get_fee_distribution(buckets)` - Analyze fee distribution

**Data Structures:**

```python
FeeAnalysis:
  - txid: str              # Transaction ID
  - fee: int               # Total fee in satoshis
  - fee_rate: float        # Satoshis per byte
  - input_count: int       # Number of inputs
  - output_count: int      # Number of outputs
  - size: int              # Transaction size in bytes
  - block_height: int      # Block containing transaction
```

### Usage Example

```python
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import FeeAnalyzer

# Parse blocks
parser = BlkParser("/path/to/blk00000.dat")
blocks = parser.parse_file(max_blocks=100)

# Create analyzer
analyzer = FeeAnalyzer()

# Analyze all transactions
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        # Skip coinbase transactions
        if len(tx.inputs) == 1 and tx.inputs[0].previous_output_hash == "0" * 64:
            continue
        
        analyzer.analyze_transaction(
            txid=tx.txid,
            inputs=tx.inputs,
            outputs=tx.outputs,
            block_height=block_idx
        )

# Get statistics
stats = analyzer.get_fee_statistics()
print(f"Average Fee: {stats['average_fee']:.2f} satoshis")
print(f"Average Fee Rate: {stats['average_fee_rate']:.4f} sat/byte")

# Get statistics by block
block_stats = analyzer.get_fee_by_block()
for block_height, stats in sorted(block_stats.items()):
    print(f"Block {block_height}: avg fee {stats['average_fee']:.2f} sat")
```

### Running the Fee Analysis Example

```bash
# 1. Edit examples/analyze_fees.py
# 2. Update BLK_FILE variable with your blk*.dat file path
# 3. Uncomment the main code section
# 4. Run:
python examples/analyze_fees.py

# Output will show:
# - Overall fee statistics
# - Fee statistics by block
# - Fee distribution analysis
# - High-fee transaction identification
# - Fee trend analysis
# - JSON export
```

### Output Format

Fee statistics:

```
OVERALL FEE STATISTICS
Transaction Count: 1,234
Total Fees: 12,345,678 satoshis (0.12345678 BTC)
Average Fee: 9,999.90 satoshis
Median Fee: 8,500.00 satoshis
Min Fee: 100 satoshis
Max Fee: 500,000 satoshis
Average Fee Rate: 25.50 sat/byte
```

Fee by block:

```
FEE STATISTICS BY BLOCK
Block    Tx Count     Avg Fee        Total Fees
0        45           8,500.00       382,500
1        52           9,200.00       478,400
2        38           7,800.00       296,400
```

---

## Setup Instructions

### Prerequisites

1. **Python 3.7+** installed
2. **Bitcoin Core** running with blockchain data available
3. **Dependencies installed**:

```bash
pip install -r requirements.txt
```

### Locating Bitcoin Data Files

**Linux:**
```bash
~/.bitcoin/blocks/blk00000.dat
~/.bitcoin/blocks/rev00000.dat
~/.bitcoin/chainstate/
```

**macOS:**
```bash
~/Library/Application Support/Bitcoin/blocks/blk00000.dat
~/Library/Application Support/Bitcoin/blocks/rev00000.dat
~/Library/Application Support/Bitcoin/chainstate/
```

**Windows:**
```
%APPDATA%\Bitcoin\blocks\blk00000.dat
%APPDATA%\Bitcoin\blocks\rev00000.dat
%APPDATA%\Bitcoin\chainstate\
```

### General Setup Steps

1. **Locate your Bitcoin data directory**
   - See paths above for your operating system
   - Ensure Bitcoin Core has synced and is stopped before accessing chainstate

2. **Update example scripts**
   - Edit the example file you want to run
   - Change the file path variables at the top:
     ```python
     BLK_FILE = "/path/to/bitcoin/blocks/blk00000.dat"
     CHAINSTATE_PATH = "/path/to/bitcoin/chainstate"
     REV_FILE = "/path/to/bitcoin/blocks/rev00000.dat"
     OUTPUT_FILE = "output.json"
     ```

3. **Uncomment the main code**
   - Each example has a `if __name__ == "__main__":` section
   - Uncomment the function calls you want to run

4. **Run the script**
   - Execute from the project directory:
     ```bash
     python examples/analyze_addresses.py
     python examples/analyze_transaction_graph.py
     python examples/analyze_fees.py
     python examples/extract_chainstate.py
     ```

### Important Notes

- **Bitcoin Core Must Be Stopped**: When accessing chainstate LevelDB, Bitcoin Core must not be running (it locks the database)
- **Large Datasets**: Processing many blocks can use significant memory
- **First Block**: Block 0 is the genesis block and has special properties
- **Coinbase Transactions**: Some analysis tools skip coinbase transactions (mining rewards)

---

## Complete Examples

### Example 1: Analyze First 1000 Blocks for Addresses and Fees

```python
#!/usr/bin/env python3
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import AddressTracker, FeeAnalyzer

# Parse blocks
parser = BlkParser("/path/to/bitcoin/blocks/blk00000.dat")
blocks = parser.parse_file(max_blocks=1000)

# Create analyzers
address_tracker = AddressTracker()
fee_analyzer = FeeAnalyzer()

# Process blocks
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        # Track addresses
        address_tracker.add_transaction(tx.txid, tx.inputs, tx.outputs, block_idx)
        
        # Skip coinbase for fee analysis
        if not (len(tx.inputs) == 1 and tx.inputs[0].previous_output_hash == "0" * 64):
            fee_analyzer.analyze_transaction(tx.txid, tx.inputs, tx.outputs, block_idx)

# Print results
addr_stats = address_tracker.get_address_stats()
fee_stats = fee_analyzer.get_fee_statistics()

print(f"Addresses: {addr_stats['total_unique_addresses']}")
print(f"Total Balance: {addr_stats['total_balance'] / 1e8} BTC")
print(f"Avg Fee: {fee_stats['average_fee']:.2f} satoshis")
print(f"Avg Fee Rate: {fee_stats['average_fee_rate']:.4f} sat/byte")
```

### Example 2: Find Top 100 Addresses and Export

```python
#!/usr/bin/env python3
import json
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import AddressTracker

parser = BlkParser("/path/to/bitcoin/blocks/blk00000.dat")
blocks = parser.parse_file(max_blocks=500)

tracker = AddressTracker()
for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        tracker.add_transaction(tx.txid, tx.inputs, tx.outputs, block_idx)

# Export top 100 addresses
top_addresses = tracker.get_top_addresses(limit=100)
top_data = []
for address, balance in top_addresses:
    info = tracker.get_address_info(address)
    top_data.append({
        'address': address,
        'balance': balance,
        'balance_btc': balance / 1e8,
        'type': info.script_type,
        'transactions': info.transaction_count,
    })

with open('top_addresses.json', 'w') as f:
    json.dump(top_data, f, indent=2)

print(f"Exported {len(top_data)} addresses")
```

### Example 3: Trace Transaction Ancestry

```python
#!/usr/bin/env python3
from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import TransactionGraph

parser = BlkParser("/path/to/bitcoin/blocks/blk00000.dat")
blocks = parser.parse_file(max_blocks=2000)

graph = TransactionGraph()
txid_map = {}

for block_idx, block in enumerate(blocks):
    for tx in block.transactions:
        graph.add_transaction(tx.txid, tx.inputs, block_idx)
        txid_map[tx.txid] = block_idx

# Find a transaction with inputs (not coinbase)
sample_txid = None
for tx in blocks[100].transactions:
    if len(tx.inputs) > 1:
        sample_txid = tx.txid
        break

if sample_txid:
    chain = graph.get_transaction_chain(sample_txid, depth=10)
    print(f"Transaction chain for {sample_txid}:")
    for i, tx in enumerate(chain):
        print(f"  {i}: {tx}")
```

---

## Troubleshooting

### "Permission Denied" Error When Accessing Chainstate
**Solution**: Stop Bitcoin Core before accessing chainstate database

### "ModuleNotFoundError" When Running Examples
**Solution**: Ensure you're running from project root directory:
```bash
cd /path/to/bitcoin-data-extractor
python examples/analyze_addresses.py
```

### Out of Memory Error
**Solution**: Process fewer blocks at a time:
```python
blocks = parser.parse_file(max_blocks=100)  # Reduce this number
```

### No Data in Output
**Solution**: Verify the blk file path is correct and contains data:
```bash
ls -lh /path/to/bitcoin/blocks/blk*.dat
```

### Chainstate LevelDB Error
**Solution**: 
1. Stop Bitcoin Core
2. Wait a few seconds
3. Run analysis script
4. Bitcoin Core may show lock errors on startup - just wait for it to recover

---

## Performance Tips

- **Batch Processing**: Process multiple files in sequence
- **Limit Blocks**: Start with fewer blocks to test setup
- **Filter Transactions**: Skip coinbase/irrelevant transactions
- **Stream Processing**: Don't load all data into memory
- **Use Indexes**: Cache frequently accessed data

For optimal performance, consider:
- Using a solid-state drive (SSD) for blockchain data
- Running on a machine with 8GB+ RAM
- Closing other applications
- Using a fast Python implementation (PyPy)

---

## Next Steps

After mastering these advanced analysis tools:

1. **Data Persistence**: Export results to databases
2. **Visualization**: Create charts and graphs of analysis results
3. **Real-time Monitoring**: Monitor blockchain as new blocks arrive
4. **Machine Learning**: Use analysis data for pattern detection
5. **Web Interface**: Build API endpoints for analysis results

For more advanced features, see the full documentation in the main [README.md](../README.md).
