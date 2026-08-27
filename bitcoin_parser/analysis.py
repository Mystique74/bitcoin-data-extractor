"""
Advanced analysis tools for Bitcoin blockchain data
Includes address tracking, transaction graphs, and fee analysis
"""

import hashlib
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class AddressInfo:
    """Information about a Bitcoin address"""
    address: str
    script_type: str  # P2PKH, P2SH, P2WPKH, P2WSH, etc.
    balance: int = 0  # in satoshis
    transaction_count: int = 0
    first_seen_block: int = 0
    last_seen_block: int = 0
    is_change: bool = False
    related_addresses: Set[str] = field(default_factory=set)


@dataclass
class TransactionFlow:
    """Represents flow of funds between addresses"""
    from_address: str
    to_address: str
    amount: int
    txid: str
    block_height: int


@dataclass
class FeeAnalysis:
    """Transaction fee analysis"""
    txid: str
    fee: int  # in satoshis
    fee_rate: float  # satoshis per byte
    input_count: int
    output_count: int
    size: int
    block_height: int


class ScriptAnalyzer:
    """Analyze Bitcoin scripts to determine address types and extract addresses"""
    
    # Script patterns
    OP_DUP = 0x76
    OP_HASH160 = 0xa9
    OP_EQUAL = 0x87
    OP_EQUALVERIFY = 0x88
    OP_CHECKSIG = 0xac
    OP_CHECKMULTISIG = 0xae
    
    @staticmethod
    def extract_pubkey_hash(script: bytes) -> Optional[str]:
        """
        Extract pubkey hash from P2PKH script
        P2PKH format: OP_DUP OP_HASH160 <pubkeyhash> OP_EQUALVERIFY OP_CHECKSIG
        """
        if len(script) == 25 and script[0] == 0x76 and script[1] == 0xa9 and script[2] == 0x14:
            pubkey_hash = script[3:23]
            return pubkey_hash.hex()
        return None
    
    @staticmethod
    def extract_script_hash(script: bytes) -> Optional[str]:
        """
        Extract script hash from P2SH script
        P2SH format: OP_HASH160 <scripthash> OP_EQUAL
        """
        if len(script) == 23 and script[0] == 0xa9 and script[1] == 0x14 and script[2] == 0x87:
            script_hash = script[3:23]
            return script_hash.hex()
        return None
    
    @staticmethod
    def extract_witness_pubkey(script: bytes) -> Optional[str]:
        """
        Extract pubkey hash from P2WPKH script (SegWit v0)
        P2WPKH format: OP_0 <20-byte-pubkeyhash>
        """
        if len(script) == 22 and script[0] == 0x00 and script[1] == 0x14:
            pubkey_hash = script[2:22]
            return pubkey_hash.hex()
        return None
    
    @staticmethod
    def extract_witness_script(script: bytes) -> Optional[str]:
        """
        Extract script hash from P2WSH script (SegWit v0)
        P2WSH format: OP_0 <32-byte-scripthash>
        """
        if len(script) == 34 and script[0] == 0x00 and script[1] == 0x20:
            script_hash = script[2:34]
            return script_hash.hex()
        return None
    
    @staticmethod
    def classify_script(script: bytes) -> str:
        """Classify script type"""
        if len(script) == 25 and script[0] == 0x76 and script[1] == 0xa9:
            return "P2PKH"
        elif len(script) == 23 and script[0] == 0xa9:
            return "P2SH"
        elif len(script) == 22 and script[0] == 0x00 and script[1] == 0x14:
            return "P2WPKH"
        elif len(script) == 34 and script[0] == 0x00 and script[1] == 0x20:
            return "P2WSH"
        elif script[0] == 0x51 and len(script) >= 22:  # OP_1 for Taproot
            return "P2TR"
        elif script[0] in [0x51, 0x52, 0x53, 0x54]:  # OP_1 through OP_4
            return "Multisig"
        elif len(script) == 0:
            return "Empty"
        else:
            return "Unknown"


class AddressTracker:
    """Track Bitcoin addresses and their activity"""
    
    def __init__(self):
        self.addresses: Dict[str, AddressInfo] = {}
        self.address_to_txids: Dict[str, Set[str]] = defaultdict(set)
        self.flows: List[TransactionFlow] = []
        self.script_analyzer = ScriptAnalyzer()
    
    def add_transaction(self, txid: str, inputs: List, outputs: List, block_height: int):
        """
        Add transaction to tracking
        
        Args:
            txid: Transaction ID
            inputs: List of transaction inputs
            outputs: List of transaction outputs
            block_height: Block height containing this transaction
        """
        # Track outputs (receiving addresses)
        for output_idx, output in enumerate(outputs):
            script = output.script
            script_type = self.script_analyzer.classify_script(script)
            
            # Extract address based on script type
            if script_type == "P2PKH":
                address = "P2PKH-" + self.script_analyzer.extract_pubkey_hash(script)
            elif script_type == "P2SH":
                address = "P2SH-" + self.script_analyzer.extract_script_hash(script)
            elif script_type == "P2WPKH":
                address = "P2WPKH-" + self.script_analyzer.extract_witness_pubkey(script)
            elif script_type == "P2WSH":
                address = "P2WSH-" + self.script_analyzer.extract_witness_script(script)
            else:
                address = f"{script_type}-{script.hex()[:16]}"
            
            if address not in self.addresses:
                self.addresses[address] = AddressInfo(
                    address=address,
                    script_type=script_type,
                    first_seen_block=block_height
                )
            
            addr_info = self.addresses[address]
            addr_info.balance += output.value
            addr_info.transaction_count += 1
            addr_info.last_seen_block = block_height
            self.address_to_txids[address].add(txid)
    
    def get_address_info(self, address: str) -> Optional[AddressInfo]:
        """Get information about a specific address"""
        return self.addresses.get(address)
    
    def get_top_addresses(self, limit: int = 100) -> List[Tuple[str, int]]:
        """Get top addresses by balance"""
        sorted_addrs = sorted(
            self.addresses.items(),
            key=lambda x: x[1].balance,
            reverse=True
        )
        return [(addr, info.balance) for addr, info in sorted_addrs[:limit]]
    
    def get_address_stats(self) -> Dict:
        """Get overall address statistics"""
        return {
            'total_unique_addresses': len(self.addresses),
            'total_p2pkh': sum(1 for a in self.addresses.values() if a.script_type == 'P2PKH'),
            'total_p2sh': sum(1 for a in self.addresses.values() if a.script_type == 'P2SH'),
            'total_p2wpkh': sum(1 for a in self.addresses.values() if a.script_type == 'P2WPKH'),
            'total_balance': sum(a.balance for a in self.addresses.values()),
            'average_balance': sum(a.balance for a in self.addresses.values()) / len(self.addresses) if self.addresses else 0,
        }


class TransactionGraph:
    """Build and analyze transaction dependency graph"""
    
    def __init__(self):
        self.graph: Dict[str, List[str]] = defaultdict(list)  # txid -> [child_txids]
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)  # txid -> [parent_txids]
        self.transactions: Dict[str, Dict] = {}
    
    def add_transaction(self, txid: str, inputs: List, block_height: int):
        """
        Add transaction to graph based on its inputs
        
        Args:
            txid: Current transaction ID
            inputs: List of inputs (each has previous_output_hash)
            block_height: Block height
        """
        self.transactions[txid] = {
            'block_height': block_height,
            'input_count': len(inputs),
            'chain_length': 0
        }
        
        # Connect to parent transactions
        for input_tx in inputs:
            parent_txid = input_tx.previous_output_hash
            self.graph[parent_txid].append(txid)
            self.reverse_graph[txid].append(parent_txid)
    
    def get_transaction_chain(self, txid: str, depth: int = 10) -> List[str]:
        """
        Get chain of transactions leading to this one
        
        Args:
            txid: Transaction ID
            depth: Maximum depth to traverse
        
        Returns:
            List of transaction IDs in chain
        """
        chain = [txid]
        current = txid
        
        for _ in range(depth):
            parents = self.reverse_graph.get(current, [])
            if not parents:
                break
            current = parents[0]  # Follow first parent
            chain.append(current)
        
        return chain
    
    def get_transaction_descendants(self, txid: str, depth: int = 10) -> List[str]:
        """
        Get all descendant transactions (coins spent in later transactions)
        
        Args:
            txid: Transaction ID
            depth: Maximum depth to traverse
        
        Returns:
            List of descendant transaction IDs
        """
        descendants = []
        to_process = [(txid, 0)]
        processed = set()
        
        while to_process:
            current, current_depth = to_process.pop(0)
            if current in processed or current_depth > depth:
                continue
            
            processed.add(current)
            children = self.graph.get(current, [])
            
            for child in children:
                descendants.append(child)
                to_process.append((child, current_depth + 1))
        
        return descendants
    
    def find_double_spend_attempts(self) -> List[Dict]:
        """
        Find potential double-spend attempts
        (outputs spent by multiple transactions)
        
        Returns:
            List of double-spend attempts with details
        """
        double_spends = []
        output_spenders: Dict[str, List[str]] = defaultdict(list)
        
        # Track which transaction outputs are spent
        for txid, parents in self.reverse_graph.items():
            for parent_txid in parents:
                output_key = f"{parent_txid}:*"  # Simplified
                output_spenders[output_key].append(txid)
        
        # Find outputs with multiple spenders
        for output_key, spenders in output_spenders.items():
            if len(spenders) > 1:
                double_spends.append({
                    'output': output_key,
                    'spenders': spenders,
                    'count': len(spenders)
                })
        
        return double_spends


class FeeAnalyzer:
    """Analyze transaction fees"""
    
    def __init__(self):
        self.fee_data: List[FeeAnalysis] = []
    
    def analyze_transaction(self, txid: str, inputs: List, outputs: List, 
                           block_height: int) -> FeeAnalysis:
        """
        Analyze fees for a transaction
        
        Args:
            txid: Transaction ID
            inputs: List of inputs
            outputs: List of outputs
            block_height: Block height
        
        Returns:
            FeeAnalysis object
        """
        input_value = sum(getattr(inp, 'value', 0) for inp in inputs)
        output_value = sum(out.value for out in outputs)
        
        fee = input_value - output_value
        size = sum(len(getattr(inp, 'script', b'')) for inp in inputs) + \
               sum(len(out.script) for out in outputs) + 10  # Approximate size
        
        fee_rate = fee / size if size > 0 else 0
        
        analysis = FeeAnalysis(
            txid=txid,
            fee=fee,
            fee_rate=fee_rate,
            input_count=len(inputs),
            output_count=len(outputs),
            size=size,
            block_height=block_height
        )
        
        self.fee_data.append(analysis)
        return analysis
    
    def get_fee_statistics(self) -> Dict:
        """Calculate fee statistics"""
        if not self.fee_data:
            return {}
        
        fees = [f.fee for f in self.fee_data]
        fee_rates = [f.fee_rate for f in self.fee_data]
        
        return {
            'total_fees': sum(fees),
            'average_fee': sum(fees) / len(fees),
            'median_fee': sorted(fees)[len(fees) // 2],
            'max_fee': max(fees),
            'min_fee': min(fees),
            'average_fee_rate': sum(fee_rates) / len(fee_rates),
            'transaction_count': len(self.fee_data),
        }
    
    def get_fee_by_block(self) -> Dict[int, Dict]:
        """Get fee statistics grouped by block height"""
        block_fees = defaultdict(list)
        
        for analysis in self.fee_data:
            block_fees[analysis.block_height].append(analysis)
        
        result = {}
        for block_height, analyses in block_fees.items():
            fees = [a.fee for a in analyses]
            result[block_height] = {
                'average_fee': sum(fees) / len(fees),
                'total_fees': sum(fees),
                'transaction_count': len(analyses),
            }
        
        return result
