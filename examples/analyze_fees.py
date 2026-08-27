#!/usr/bin/env python3
"""
Example: Advanced Analysis - Fee Analysis
Demonstrates transaction fee analysis and trends
"""

import sys
from pathlib import Path
import json
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitcoin_parser.blk_parser import BlkParser
from bitcoin_parser.analysis import FeeAnalyzer


def analyze_fees_in_blocks(blk_file: str, max_blocks: int = 100):
    """
    Analyze transaction fees across blocks
    
    Args:
        blk_file: Path to blk*.dat file
        max_blocks: Maximum number of blocks to analyze
    """
    print(f"Parsing {blk_file}...")
    parser = BlkParser(blk_file)
    blocks = parser.parse_file(max_blocks=max_blocks)
    
    print(f"Found {len(blocks)} blocks")
    print("Analyzing transaction fees...\n")
    
    analyzer = FeeAnalyzer()
    total_txs = 0
    
    # Process all blocks and transactions
    for block_idx, block in enumerate(blocks):
        for tx in block.transactions:
            # Skip coinbase transactions (no input value)
            if len(tx.inputs) == 1 and all(
                inp.previous_output_hash == "0" * 64 for inp in tx.inputs
            ):
                continue
            
            # Analyze transaction fees
            analyzer.analyze_transaction(
                txid=tx.txid,
                inputs=tx.inputs,
                outputs=tx.outputs,
                block_height=block_idx
            )
            total_txs += 1
    
    print(f"Analyzed {total_txs:,} transactions")
    print()
    
    return analyzer


def print_fee_statistics(analyzer: FeeAnalyzer):
    """
    Print overall fee statistics
    
    Args:
        analyzer: FeeAnalyzer instance
    """
    stats = analyzer.get_fee_statistics()
    
    print("=" * 70)
    print("OVERALL FEE STATISTICS")
    print("=" * 70)
    print(f"Transaction Count: {stats['transaction_count']:,}")
    print(f"Total Fees: {stats['total_fees']:,} satoshis ({stats['total_fees'] / 1e8:.8f} BTC)")
    print(f"Average Fee: {stats['average_fee']:,.2f} satoshis")
    print(f"Median Fee: {stats['median_fee']:,.2f} satoshis")
    print(f"Min Fee: {stats['min_fee']:,} satoshis")
    print(f"Max Fee: {stats['max_fee']:,} satoshis")
    print(f"Average Fee Rate: {stats['average_fee_rate']:.4f} sat/byte")
    print("=" * 70 + "\n")


def print_fee_by_block(analyzer: FeeAnalyzer):
    """
    Print fee statistics grouped by block
    
    Args:
        analyzer: FeeAnalyzer instance
    """
    block_stats = analyzer.get_fee_by_block()
    
    print("=" * 70)
    print("FEE STATISTICS BY BLOCK")
    print("=" * 70)
    print(f"{'Block':<8} {'Tx Count':<12} {'Avg Fee':<15} {'Total Fees':<20}")
    print("-" * 70)
    
    for block_height in sorted(block_stats.keys()):
        stats = block_stats[block_height]
        print(
            f"{block_height:<8} "
            f"{stats['transaction_count']:<12} "
            f"{stats['average_fee']:<15,.2f} "
            f"{stats['total_fees']:<20,}"
        )
    
    print("=" * 70 + "\n")


def analyze_fee_distribution(analyzer: FeeAnalyzer, buckets: int = 10):
    """
    Analyze distribution of fees
    
    Args:
        analyzer: FeeAnalyzer instance
        buckets: Number of distribution buckets
    """
    if not analyzer.fee_data:
        print("No fee data available\n")
        return
    
    fees = [f.fee for f in analyzer.fee_data]
    min_fee = min(fees)
    max_fee = max(fees)
    
    # Calculate bucket size
    bucket_size = (max_fee - min_fee) / buckets if max_fee > min_fee else 1
    
    # Distribute fees into buckets
    distribution = defaultdict(int)
    for fee in fees:
        if bucket_size > 0:
            bucket = int((fee - min_fee) / bucket_size)
        else:
            bucket = 0
        distribution[bucket] += 1
    
    print("=" * 70)
    print("FEE DISTRIBUTION")
    print("=" * 70)
    print(f"{'Bucket':<20} {'Range (sat)':<30} {'Count':<12} {'Percentage':<12}")
    print("-" * 70)
    
    total = sum(distribution.values())
    for bucket in sorted(distribution.keys()):
        count = distribution[bucket]
        percentage = (count / total) * 100
        
        range_start = int(min_fee + bucket * bucket_size)
        range_end = int(min_fee + (bucket + 1) * bucket_size)
        
        print(
            f"{bucket:<20} "
            f"{range_start}-{range_end:<28} "
            f"{count:<12} "
            f"{percentage:<12.2f}%"
        )
    
    print("=" * 70 + "\n")


def analyze_high_fee_transactions(analyzer: FeeAnalyzer, percentile: float = 95):
    """
    Analyze transactions with unusually high fees
    
    Args:
        analyzer: FeeAnalyzer instance
        percentile: Show transactions above this percentile (0-100)
    """
    if not analyzer.fee_data:
        print("No fee data available\n")
        return
    
    fees = sorted([f.fee for f in analyzer.fee_data])
    threshold_idx = int(len(fees) * (percentile / 100))
    threshold = fees[threshold_idx] if threshold_idx < len(fees) else 0
    
    high_fee_txs = [f for f in analyzer.fee_data if f.fee >= threshold]
    high_fee_txs.sort(key=lambda x: x.fee, reverse=True)
    
    print("=" * 70)
    print(f"HIGH FEE TRANSACTIONS (>{percentile}th percentile, threshold: {threshold:,} sat)")
    print("=" * 70)
    print(f"{'#':<4} {'TXID':<20} {'Fee (sat)':<15} {'Fee Rate':<15} {'Size':<10}")
    print("-" * 70)
    
    for idx, tx in enumerate(high_fee_txs[:20], 1):
        print(
            f"{idx:<4} "
            f"{tx.txid[:20]:<20} "
            f"{tx.fee:<15,} "
            f"{tx.fee_rate:<15.4f} "
            f"{tx.size:<10}"
        )
    
    if len(high_fee_txs) > 20:
        print(f"\n... and {len(high_fee_txs) - 20} more high-fee transactions")
    
    print()
    print("=" * 70 + "\n")


def analyze_fee_trends(analyzer: FeeAnalyzer):
    """
    Analyze fee trends over blocks
    
    Args:
        analyzer: FeeAnalyzer instance
    """
    if not analyzer.fee_data:
        print("No fee data available\n")
        return
    
    # Group by block and calculate average fee
    block_fees = defaultdict(list)
    for analysis in analyzer.fee_data:
        block_fees[analysis.block_height].append(analysis.fee_rate)
    
    print("=" * 70)
    print("FEE RATE TRENDS")
    print("=" * 70)
    print(f"{'Block':<8} {'Avg Fee Rate':<20} {'Min':<20} {'Max':<20} {'Tx Count':<10}")
    print("-" * 70)
    
    for block_height in sorted(block_fees.keys()):
        rates = block_fees[block_height]
        avg_rate = sum(rates) / len(rates)
        min_rate = min(rates)
        max_rate = max(rates)
        
        print(
            f"{block_height:<8} "
            f"{avg_rate:<20.4f} "
            f"{min_rate:<20.4f} "
            f"{max_rate:<20.4f} "
            f"{len(rates):<10}"
        )
    
    print("=" * 70 + "\n")


def export_fee_analysis_to_json(analyzer: FeeAnalyzer, output_file: str):
    """
    Export detailed fee analysis to JSON
    
    Args:
        analyzer: FeeAnalyzer instance
        output_file: Path to output JSON file
    """
    print(f"Exporting fee analysis to {output_file}...")
    
    # Get statistics
    stats = analyzer.get_fee_statistics()
    block_stats = analyzer.get_fee_by_block()
    
    # Prepare detailed transaction data
    transactions = []
    for analysis in analyzer.fee_data[:1000]:  # Export first 1000
        transactions.append({
            'txid': analysis.txid,
            'fee': analysis.fee,
            'fee_rate': analysis.fee_rate,
            'input_count': analysis.input_count,
            'output_count': analysis.output_count,
            'size': analysis.size,
            'block_height': analysis.block_height,
        })
    
    export_data = {
        'summary': {
            'total_transactions': len(analyzer.fee_data),
            'total_fees': stats['total_fees'],
            'average_fee': stats['average_fee'],
            'median_fee': stats['median_fee'],
            'min_fee': stats['min_fee'],
            'max_fee': stats['max_fee'],
            'average_fee_rate': stats['average_fee_rate'],
        },
        'by_block': block_stats,
        'transactions': transactions,
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Exported to {output_file}")
    print(f"  Transactions: {len(analyzer.fee_data)}")
    print(f"  Blocks: {len(block_stats)}")
    print()


if __name__ == "__main__":
    # Setup
    print("=" * 70)
    print("TRANSACTION FEE ANALYSIS EXAMPLE")
    print("=" * 70)
    print()
    
    # Replace with your actual blk file path
    BLK_FILE = "/path/to/bitcoin/blocks/blk00000.dat"
    OUTPUT_FILE = "fee_analysis.json"
    
    print("SETUP INSTRUCTIONS:")
    print("-" * 70)
    print("1. Update BLK_FILE variable to point to your blk*.dat file")
    print("   - Linux: ~/.bitcoin/blocks/blk00000.dat")
    print("   - macOS: ~/Library/Application Support/Bitcoin/blocks/blk00000.dat")
    print("   - Windows: %APPDATA%\\Bitcoin\\blocks\\blk00000.dat")
    print()
    print("2. Run the script:")
    print("   python examples/analyze_fees.py")
    print()
    print("3. The script will:")
    print("   - Parse blocks and extract transaction fees")
    print("   - Calculate fee statistics")
    print("   - Analyze fee distribution and trends")
    print("   - Identify high-fee transactions")
    print("   - Export detailed analysis to JSON")
    print("-" * 70)
    print()
    
    # Run analysis (uncomment to execute)
    # analyzer = analyze_fees_in_blocks(BLK_FILE, max_blocks=100)
    # print_fee_statistics(analyzer)
    # print_fee_by_block(analyzer)
    # analyze_fee_distribution(analyzer, buckets=10)
    # analyze_high_fee_transactions(analyzer, percentile=90)
    # analyze_fee_trends(analyzer)
    # export_fee_analysis_to_json(analyzer, OUTPUT_FILE)
    
    print("To run this example:")
    print(f"1. Update BLK_FILE = \"{BLK_FILE}\"")
    print(f"2. Uncomment the main code section at the bottom")
    print(f"3. Run: python examples/analyze_fees.py")
