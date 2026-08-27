#!/usr/bin/env python3
"""
Example: Extract undo data from rev*.dat files
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitcoin_parser.rev_parser import RevParser


def export_undo_to_json(rev_file: str, output_file: str, max_blocks: int = 100):
    """
    Extract undo data from a rev*.dat file and export to JSON
    
    Args:
        rev_file: Path to rev*.dat file
        output_file: Path to output JSON file
        max_blocks: Maximum number of blocks to extract
    """
    print(f"Parsing {rev_file}...")
    parser = RevParser(rev_file)
    
    block_undos = parser.parse_file(max_blocks=max_blocks)
    print(f"Found {len(block_undos)} blocks with undo data")
    
    # Convert to JSON-serializable format
    blocks_data = []
    for block_idx, block_undo in enumerate(block_undos):
        block_dict = {
            'block_index': block_idx,
            'undo_entries': []
        }
        
        for undo in block_undo.undo_entries:
            undo_dict = {
                'output_index': undo.output_index,
                'block_height': undo.block_height,
                'amount': undo.amount,
                'amount_btc': undo.amount / 1e8,
                'script_length': undo.script_length,
                'script': undo.script.hex(),
            }
            block_dict['undo_entries'].append(undo_dict)
        
        blocks_data.append(block_dict)
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(blocks_data, f, indent=2)
    
    print(f"Exported undo data for {len(blocks_data)} blocks to {output_file}")


def print_undo_summary(rev_file: str, max_blocks: int = 5):
    """
    Parse and print summary of undo data
    
    Args:
        rev_file: Path to rev*.dat file
        max_blocks: Maximum number of blocks to display
    """
    print(f"Parsing {rev_file}...")
    parser = RevParser(rev_file)
    
    block_undos = parser.parse_file(max_blocks=max_blocks)
    print(f"Found {len(block_undos)} blocks\n")
    
    stats = parser.get_undo_stats(block_undos)
    print("UNDO DATA STATISTICS")
    print("=" * 60)
    print(f"Total Blocks: {stats['total_blocks']}")
    print(f"Total Undo Entries: {stats['total_undo_entries']}")
    print(f"Total Value Undone: {stats['total_value_undone']} satoshis")
    print("=" * 60 + "\n")
    
    for i, block_undo in enumerate(block_undos[:max_blocks]):
        print(f"Block #{i}")
        print(f"  Undo Entries: {len(block_undo.undo_entries)}")
        
        total_value = sum(u.amount for u in block_undo.undo_entries)
        print(f"  Total Value: {total_value} satoshis ({total_value / 1e8:.8f} BTC)")
        
        # Show first few undo entries
        for j, undo in enumerate(block_undo.undo_entries[:3]):
            print(f"    Entry {j}: Output {undo.output_index}, Value {undo.amount} sat, Height {undo.block_height}")
        
        if len(block_undo.undo_entries) > 3:
            print(f"    ... and {len(block_undo.undo_entries) - 3} more entries")
        print()


if __name__ == "__main__":
    # Example usage
    # Replace with your actual rev file path
    REV_FILE = "/path/to/bitcoin/blocks/rev00000.dat"
    
    # Print undo summary
    print("=" * 60)
    print("UNDO DATA EXTRACTION EXAMPLE")
    print("=" * 60)
    print_undo_summary(REV_FILE, max_blocks=3)
    
    # Export to JSON
    # export_undo_to_json(REV_FILE, "undo.json", max_blocks=100)