#!/usr/bin/env python3
"""
Example: Advanced Analysis - Address Tracking
Demonstrates how to track Bitcoin addresses and their activity
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import AddressTracker, ScriptAnalyzer


def analyze_addresses_in_blocks(blk_file: str, max_blocks: int = 100):
    """
    Parse blocks and track all addresses
    
    Args:
        blk_file: Path to blk*.dat file
        max_blocks: Maximum number of blocks to analyze
    """
    print(f"Parsing {blk_file}...")
    parser = BlkParser(blk_file)
    blocks = parser.parse_file(max_blocks=max_blocks)
    
    print(f"Found {len(blocks)} blocks")
    print("Tracking addresses...\n")
    
    tracker = AddressTracker()
    script_analyzer = ScriptAnalyzer()
    
    # Process all blocks and transactions
    for block_idx, block in enumerate(blocks):
        for tx in block.transactions:
            # Add transaction to tracker
            tracker.add_transaction(
                txid=tx.txid,
                inputs=tx.inputs,
                outputs=tx.outputs,
                block_height=block_idx
            )
    
    # Print statistics
    stats = tracker.get_address_stats()
    print("=" * 70)
    print("ADDRESS TRACKING STATISTICS")
    print("=" * 70)
    print(f"Total Unique Addresses: {stats['total_unique_addresses']:,}")
    print(f"P2PKH Addresses: {stats['total_p2pkh']:,}")
    print(f"P2SH Addresses: {stats['total_p2sh']:,}")
    print(f"P2WPKH Addresses: {stats['total_p2wpkh']:,}")
    print(f"Total Balance: {stats['total_balance']:,} satoshis ({stats['total_balance'] / 1e8:.8f} BTC)")
    print(f"Average Balance per Address: {stats['average_balance']:.2f} satoshis")
    print("=" * 70 + "\n")
    
    # Show top addresses by balance
    print("TOP 20 ADDRESSES BY BALANCE")
    print("=" * 70)
    top_addresses = tracker.get_top_addresses(limit=20)
    
    for idx, (address, balance) in enumerate(top_addresses, 1):
        addr_info = tracker.get_address_info(address)
        btc_value = balance / 1e8
        print(f"{idx:2d}. {address}")
        print(f"    Balance: {balance:,} satoshis ({btc_value:.8f} BTC)")
        print(f"    Type: {addr_info.script_type}")
        print(f"    Transactions: {addr_info.transaction_count}")
        print(f"    Active: Block {addr_info.first_seen_block} -> Block {addr_info.last_seen_block}")
        print()
    
    print("=" * 70 + "\n")
    
    return tracker


def export_addresses_to_json(tracker: AddressTracker, output_file: str):
    """
    Export all tracked addresses to JSON
    
    Args:
        tracker: AddressTracker instance
        output_file: Path to output JSON file
    """
    print(f"Exporting addresses to {output_file}...")
    
    addresses_data = []
    for address, info in tracker.addresses.items():
        addresses_data.append({
            'address': address,
            'script_type': info.script_type,
            'balance': info.balance,
            'balance_btc': info.balance / 1e8,
            'transaction_count': info.transaction_count,
            'first_seen_block': info.first_seen_block,
            'last_seen_block': info.last_seen_block,
        })
    
    # Sort by balance
    addresses_data.sort(key=lambda x: x['balance'], reverse=True)
    
    with open(output_file, 'w') as f:
        json.dump(addresses_data, f, indent=2)
    
    print(f"Exported {len(addresses_data)} addresses to {output_file}\n")


def analyze_specific_address(tracker: AddressTracker, address: str):
    """
    Get detailed information about a specific address
    
    Args:
        tracker: AddressTracker instance
        address: Address to analyze
    """
    info = tracker.get_address_info(address)
    
    if not info:
        print(f"Address not found: {address}\n")
        return
    
    print("=" * 70)
    print(f"ADDRESS DETAILS: {address}")
    print("=" * 70)
    print(f"Script Type: {info.script_type}")
    print(f"Balance: {info.balance:,} satoshis ({info.balance / 1e8:.8f} BTC)")
    print(f"Transaction Count: {info.transaction_count}")
    print(f"First Seen: Block {info.first_seen_block}")
    print(f"Last Seen: Block {info.last_seen_block}")
    print(f"Related Addresses: {len(info.related_addresses)}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Setup
    print("=" * 70)
    print("BITCOIN ADDRESS TRACKING EXAMPLE")
    print("=" * 70)
    print()
    
    # Replace with your actual blk file path
    BLK_FILE = "/path/to/bitcoin/blocks/blk00000.dat"
    OUTPUT_FILE = "addresses.json"
    
    print("SETUP INSTRUCTIONS:")
    print("-" * 70)
    print("1. Update BLK_FILE variable to point to your blk*.dat file")
    print("   - Linux: ~/.bitcoin/blocks/blk00000.dat")
    print("   - macOS: ~/Library/Application Support/Bitcoin/blocks/blk00000.dat")
    print("   - Windows: %APPDATA%\\Bitcoin\\blocks\\blk00000.dat")
    print()
    print("2. Run the script:")
    print("   python examples/analyze_addresses.py")
    print()
    print("3. The script will:")
    print("   - Parse blocks from the blk file")
    print("   - Track all addresses and their activity")
    print("   - Display top addresses by balance")
    print("   - Export all addresses to JSON")
    print("-" * 70)
    print()
    
    # Run analysis
    # tracker = analyze_addresses_in_blocks(BLK_FILE, max_blocks=100)
    # export_addresses_to_json(tracker, OUTPUT_FILE)
    
    # Analyze specific address (example)
    # analyze_specific_address(tracker, "P2PKH-abc123...")
    
    print("To run this example:")
    print(f"1. Update BLK_FILE = \"{BLK_FILE}\"")
    print(f"2. Uncomment the main code section at the bottom")
    print(f"3. Run: python examples/analyze_addresses.py")
