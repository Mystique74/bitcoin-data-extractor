#!/usr/bin/env python3
"""
Example: Extract UTXO data from LevelDB chainstate
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitcoin_parser.leveldb_parser import LevelDBParser


def export_utxos_to_json(chainstate_path: str, output_file: str, limit: int = 1000):
    """
    Extract UTXOs from chainstate LevelDB and export to JSON
    
    Args:
        chainstate_path: Path to chainstate directory
        output_file: Path to output JSON file
        limit: Maximum number of UTXOs to extract
    """
    print(f"Opening chainstate database at {chainstate_path}...")
    parser = LevelDBParser(chainstate_path)
    
    print(f"Extracting up to {limit} UTXOs...")
    utxos = parser.get_all_utxos(limit=limit)
    print(f"Extracted {len(utxos)} UTXOs")
    
    # Convert to JSON-serializable format
    utxos_data = []
    for utxo in utxos:
        utxo_dict = {
            'txid': utxo.txid,
            'output_index': utxo.output_index,
            'amount': utxo.amount,
            'amount_btc': utxo.amount / 1e8,
            'script_length': utxo.script_length,
            'script': utxo.script.hex(),
            'block_height': utxo.block_height,
            'is_coinbase': utxo.is_coinbase,
        }
        utxos_data.append(utxo_dict)
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(utxos_data, f, indent=2)
    
    print(f"Exported {len(utxos_data)} UTXOs to {output_file}")
    
    parser.close()


def print_utxo_statistics(chainstate_path: str):
    """
    Parse and print UTXO statistics
    
    Args:
        chainstate_path: Path to chainstate directory
    """
    print(f"Opening chainstate database at {chainstate_path}...")
    parser = LevelDBParser(chainstate_path)
    
    print("Calculating statistics...")
    stats = parser.get_utxo_stats()
    
    print("\n" + "=" * 60)
    print("UTXO SET STATISTICS")
    print("=" * 60)
    print(f"Total UTXOs: {stats['total_utxos']:,}")
    print(f"Total Value: {stats['total_value']:,} satoshis ({stats['total_value'] / 1e8:.8f} BTC)")
    print(f"Average UTXO Value: {stats['average_value']:.2f} satoshis")
    print(f"Coinbase UTXOs: {stats['coinbase_utxos']:,}")
    print("=" * 60 + "\n")
    
    parser.close()


def print_sample_utxos(chainstate_path: str, sample_size: int = 10):
    """
    Print sample of UTXOs
    
    Args:
        chainstate_path: Path to chainstate directory
        sample_size: Number of UTXOs to display
    """
    print(f"Opening chainstate database at {chainstate_path}...")
    parser = LevelDBParser(chainstate_path)
    
    print(f"Extracting {sample_size} sample UTXOs...\n")
    utxos = parser.get_all_utxos(limit=sample_size)
    
    for i, utxo in enumerate(utxos, 1):
        print(f"UTXO #{i}")
        print(f"  TXID: {utxo.txid}")
        print(f"  Output Index: {utxo.output_index}")
        print(f"  Amount: {utxo.amount} satoshis ({utxo.amount / 1e8:.8f} BTC)")
        print(f"  Script Length: {utxo.script_length} bytes")
        print(f"  Script: {utxo.script.hex()}")
        print(f"  Block Height: {utxo.block_height}")
        print(f"  Coinbase: {utxo.is_coinbase}")
        print()
    
    parser.close()


if __name__ == "__main__":
    # Example usage
    # Replace with your actual chainstate path
    CHAINSTATE_PATH = "/path/to/bitcoin/.bitcoin/chainstate"
    
    # Print statistics
    print("=" * 60)
    print("CHAINSTATE EXTRACTION EXAMPLE")
    print("=" * 60)
    print_utxo_statistics(CHAINSTATE_PATH)
    
    # Print sample UTXOs
    print_sample_utxos(CHAINSTATE_PATH, sample_size=5)
    
    # Export to JSON
    # export_utxos_to_json(CHAINSTATE_PATH, "utxos.json", limit=10000)