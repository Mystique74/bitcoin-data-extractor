#!/usr/bin/env python3
"""
Example: Extract block data from blk*.dat files
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitcoin_parser.blk_parser import BlkParser


def export_blocks_to_json(blk_file: str, output_file: str, max_blocks: int = 10):
    """
    Extract blocks from a blk*.dat file and export to JSON
    
    Args:
        blk_file: Path to blk*.dat file
        output_file: Path to output JSON file
        max_blocks: Maximum number of blocks to extract
    """
    print(f"Parsing {blk_file}...")
    parser = BlkParser(blk_file)
    
    blocks = parser.parse_file(max_blocks=max_blocks)
    print(f"Found {len(blocks)} blocks")
    
    # Convert to JSON-serializable format
    blocks_data = []
    for block in blocks:
        block_dict = {
            'header': {
                'version': block.header.version,
                'previous_block_hash': block.header.previous_block_hash,
                'merkle_root': block.header.merkle_root,
                'timestamp': block.header.timestamp,
                'bits': block.header.bits,
                'nonce': block.header.nonce,
                'block_hash': block.header.block_hash,
            },
            'transaction_count': block.transaction_count,
            'transactions': []
        }
        
        for tx in block.transactions:
            tx_dict = {
                'version': tx.version,
                'txid': tx.txid,
                'input_count': len(tx.inputs),
                'output_count': len(tx.outputs),
                'locktime': tx.locktime,
                'size': tx.size,
                'inputs': [
                    {
                        'previous_output_hash': inp.previous_output_hash,
                        'previous_output_index': inp.previous_output_index,
                        'script_length': inp.script_length,
                        'script': inp.script.hex(),
                        'sequence': inp.sequence,
                    }
                    for inp in tx.inputs
                ],
                'outputs': [
                    {
                        'value': out.value,
                        'script_length': out.script_length,
                        'script': out.script.hex(),
                    }
                    for out in tx.outputs
                ]
            }
            block_dict['transactions'].append(tx_dict)
        
        blocks_data.append(block_dict)
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(blocks_data, f, indent=2)
    
    print(f"Exported {len(blocks_data)} blocks to {output_file}")


def print_block_summary(blk_file: str, max_blocks: int = 5):
    """
    Parse and print summary of blocks
    
    Args:
        blk_file: Path to blk*.dat file
        max_blocks: Maximum number of blocks to display
    """
    print(f"Parsing {blk_file}...")
    parser = BlkParser(blk_file)
    
    blocks = parser.parse_file(max_blocks=max_blocks)
    print(f"\nFound {len(blocks)} blocks\n")
    
    for i, block in enumerate(blocks):
        print(f"Block #{i}")
        print(f"  Hash: {block.header.block_hash}")
        print(f"  Previous Hash: {block.header.previous_block_hash}")
        print(f"  Timestamp: {block.header.timestamp}")
        print(f"  Transactions: {len(block.transactions)}")
        
        total_inputs = sum(len(tx.inputs) for tx in block.transactions)
        total_outputs = sum(len(tx.outputs) for tx in block.transactions)
        total_value = sum(sum(out.value for out in tx.outputs) for tx in block.transactions)
        
        print(f"  Total Inputs: {total_inputs}")
        print(f"  Total Outputs: {total_outputs}")
        print(f"  Total Value: {total_value} satoshis ({total_value / 1e8} BTC)")
        print()


if __name__ == "__main__":
    # Example usage
    # Replace with your actual blk file path
    BLK_FILE = "/path/to/bitcoin/blocks/blk00000.dat"
    
    # Print block summary
    print("=" * 60)
    print("BLOCK EXTRACTION EXAMPLE")
    print("=" * 60)
    print_block_summary(BLK_FILE, max_blocks=2)
    
    # Export to JSON
    # export_blocks_to_json(BLK_FILE, "blocks.json", max_blocks=10)