#!/usr/bin/env python3
"""
Example: Advanced Analysis - Transaction Graph
Demonstrates transaction chain analysis, ancestry, and double-spend detection
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import TransactionGraph


def build_transaction_graph(blk_file: str, max_blocks: int = 100):
    """
    Build transaction dependency graph from blocks
    
    Args:
        blk_file: Path to blk*.dat file
        max_blocks: Maximum number of blocks to analyze
    """
    print(f"Parsing {blk_file}...")
    parser = BlkParser(blk_file)
    blocks = parser.parse_file(max_blocks=max_blocks)
    
    print(f"Found {len(blocks)} blocks")
    print("Building transaction graph...\n")
    
    graph = TransactionGraph()
    total_txs = 0
    
    # Process all blocks and transactions
    for block_idx, block in enumerate(blocks):
        for tx in block.transactions:
            graph.add_transaction(
                txid=tx.txid,
                inputs=tx.inputs,
                block_height=block_idx
            )
            total_txs += 1
    
    print(f"Processed {total_txs:,} transactions")
    print()
    
    return graph


def analyze_transaction_chain(graph: TransactionGraph, txid: str, depth: int = 5):
    """
    Analyze the chain of transactions leading to a specific transaction
    
    Args:
        graph: TransactionGraph instance
        txid: Transaction ID to analyze
        depth: How many generations back to trace
    """
    print("=" * 70)
    print(f"TRANSACTION CHAIN ANALYSIS: {txid}")
    print("=" * 70)
    
    chain = graph.get_transaction_chain(txid, depth=depth)
    
    print(f"Chain depth: {len(chain)} transactions\n")
    
    for idx, tx_id in enumerate(chain):
        tx_info = graph.transactions.get(tx_id, {})
        indent = "  " * idx
        
        print(f"{indent}└─ Generation {idx}")
        print(f"{indent}   TXID: {tx_id}")
        print(f"{indent}   Block: {tx_info.get('block_height', 'Unknown')}")
        print(f"{indent}   Inputs: {tx_info.get('input_count', 'Unknown')}")
        print()
    
    print("=" * 70 + "\n")


def analyze_transaction_descendants(graph: TransactionGraph, txid: str, depth: int = 5):
    """
    Analyze all transactions that spend outputs from a specific transaction
    
    Args:
        graph: TransactionGraph instance
        txid: Transaction ID to analyze
        depth: How deep to trace descendants
    """
    print("=" * 70)
    print(f"TRANSACTION DESCENDANTS: {txid}")
    print("=" * 70)
    
    descendants = graph.get_transaction_descendants(txid, depth=depth)
    
    print(f"Total descendants: {len(descendants)} transactions\n")
    
    if descendants:
        for idx, desc_txid in enumerate(descendants[:20], 1):  # Show first 20
            tx_info = graph.transactions.get(desc_txid, {})
            print(f"{idx:2d}. {desc_txid}")
            print(f"    Block: {tx_info.get('block_height', 'Unknown')}")
            print(f"    Inputs: {tx_info.get('input_count', 'Unknown')}")
        
        if len(descendants) > 20:
            print(f"\n... and {len(descendants) - 20} more")
    else:
        print("No descendants found (coin still unspent or not in analyzed blocks)")
    
    print()
    print("=" * 70 + "\n")


def find_double_spends(graph: TransactionGraph):
    """
    Detect potential double-spend attempts
    
    Args:
        graph: TransactionGraph instance
    """
    print("=" * 70)
    print("DOUBLE-SPEND DETECTION")
    print("=" * 70)
    
    double_spends = graph.find_double_spend_attempts()
    
    print(f"Found {len(double_spends)} potential double-spend attempts\n")
    
    if double_spends:
        for idx, attempt in enumerate(double_spends[:10], 1):  # Show first 10
            print(f"{idx}. Output: {attempt['output']}")
            print(f"   Spent by {attempt['count']} transactions:")
            for spender in attempt['spenders']:
                print(f"   - {spender}")
            print()
        
        if len(double_spends) > 10:
            print(f"... and {len(double_spends) - 10} more double-spend attempts")
    else:
        print("No double-spend attempts detected in analyzed blocks")
    
    print()
    print("=" * 70 + "\n")


def print_graph_statistics(graph: TransactionGraph):
    """
    Print overall transaction graph statistics
    
    Args:
        graph: TransactionGraph instance
    """
    print("=" * 70)
    print("TRANSACTION GRAPH STATISTICS")
    print("=" * 70)
    
    total_txs = len(graph.transactions)
    total_edges = len(graph.graph)
    
    # Calculate average connections
    total_children = sum(len(children) for children in graph.graph.values())
    avg_children = total_children / total_edges if total_edges > 0 else 0
    
    # Find transaction with most descendants
    max_children_tx = max(
        graph.graph.items(),
        key=lambda x: len(x[1]),
        default=(None, [])
    )
    
    print(f"Total Transactions: {total_txs:,}")
    print(f"Transactions with Children: {total_edges:,}")
    print(f"Average Children per Transaction: {avg_children:.2f}")
    
    if max_children_tx[0]:
        print(f"Transaction with Most Children: {max_children_tx[0]}")
        print(f"  Children Count: {len(max_children_tx[1])}")
    
    print()
    print("=" * 70 + "\n")


def export_graph_to_json(graph: TransactionGraph, output_file: str, limit: int = 1000):
    """
    Export transaction graph to JSON
    
    Args:
        graph: TransactionGraph instance
        output_file: Path to output JSON file
        limit: Maximum number of transactions to export
    """
    print(f"Exporting transaction graph to {output_file}...")
    
    graph_data = {
        'total_transactions': len(graph.transactions),
        'transactions': {},
        'edges': []
    }
    
    # Export transactions
    for idx, (txid, tx_info) in enumerate(list(graph.transactions.items())[:limit]):
        graph_data['transactions'][txid] = {
            'block_height': tx_info.get('block_height'),
            'input_count': tx_info.get('input_count'),
        }
    
    # Export edges (limited to avoid large file)
    edge_count = 0
    for parent_txid, children in graph.graph.items():
        for child_txid in children:
            if edge_count >= limit:
                break
            graph_data['edges'].append({
                'from': parent_txid,
                'to': child_txid
            })
            edge_count += 1
        if edge_count >= limit:
            break
    
    with open(output_file, 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"Exported graph to {output_file}")
    print(f"  Transactions: {len(graph_data['transactions'])}")
    print(f"  Edges: {len(graph_data['edges'])}")
    print()


if __name__ == "__main__":
    # Setup
    print("=" * 70)
    print("TRANSACTION GRAPH ANALYSIS EXAMPLE")
    print("=" * 70)
    print()
    
    # Replace with your actual blk file path
    BLK_FILE = "/path/to/bitcoin/blocks/blk00000.dat"
    OUTPUT_FILE = "transaction_graph.json"
    
    print("SETUP INSTRUCTIONS:")
    print("-" * 70)
    print("1. Update BLK_FILE variable to point to your blk*.dat file")
    print("   - Linux: ~/.bitcoin/blocks/blk00000.dat")
    print("   - macOS: ~/Library/Application Support/Bitcoin/blocks/blk00000.dat")
    print("   - Windows: %APPDATA%\\Bitcoin\\blocks\\blk00000.dat")
    print()
    print("2. Run the script:")
    print("   python examples/analyze_transaction_graph.py")
    print()
    print("3. The script will:")
    print("   - Build transaction dependency graph")
    print("   - Analyze transaction chains and ancestors")
    print("   - Detect double-spend attempts")
    print("   - Export graph to JSON")
    print("-" * 70)
    print()
    
    # Run analysis (uncomment to execute)
    # graph = build_transaction_graph(BLK_FILE, max_blocks=100)
    # print_graph_statistics(graph)
    # find_double_spends(graph)
    # export_graph_to_json(graph, OUTPUT_FILE)
    
    # Analyze specific transactions
    # analyze_transaction_chain(graph, "example_txid", depth=5)
    # analyze_transaction_descendants(graph, "example_txid", depth=5)
    
    print("To run this example:")
    print(f"1. Update BLK_FILE = \"{BLK_FILE}\"")
    print(f"2. Uncomment the main code section at the bottom")
    print(f"3. Run: python examples/analyze_transaction_graph.py")
