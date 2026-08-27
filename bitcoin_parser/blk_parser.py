"""
Parser for Bitcoin Core blk*.dat files
Extracts block headers, transactions, and transaction details
"""

import struct
import hashlib
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TransactionInput:
    """Represents a transaction input (txin)"""
    previous_output_hash: str
    previous_output_index: int
    script_length: int
    script: bytes
    sequence: int


@dataclass
class TransactionOutput:
    """Represents a transaction output (txout)"""
    value: int
    script_length: int
    script: bytes


@dataclass
class Transaction:
    """Represents a Bitcoin transaction"""
    version: int
    inputs: List[TransactionInput]
    outputs: List[TransactionOutput]
    locktime: int
    txid: str
    size: int


@dataclass
class BlockHeader:
    """Represents a Bitcoin block header"""
    version: int
    previous_block_hash: str
    merkle_root: str
    timestamp: int
    bits: int
    nonce: int
    block_hash: str


@dataclass
class Block:
    """Represents a complete Bitcoin block"""
    header: BlockHeader
    transaction_count: int
    transactions: List[Transaction]


class BlkParser:
    """Parser for Bitcoin blk*.dat files"""
    
    MAGIC_BYTES = b'\xf9\xbe\xb4\xd9'  # Mainnet magic bytes
    
    def __init__(self, filepath: str):
        """Initialize parser with a blk*.dat file"""
        self.filepath = filepath
        
    def read_varint(self, data: bytes, offset: int) -> Tuple[int, int]:
        """
        Read a variable-length integer from data
        Returns: (value, new_offset)
        """
        first_byte = data[offset]
        
        if first_byte < 0xfd:
            return first_byte, offset + 1
        elif first_byte == 0xfd:
            value = struct.unpack('<H', data[offset+1:offset+3])[0]
            return value, offset + 3
        elif first_byte == 0xfe:
            value = struct.unpack('<I', data[offset+1:offset+5])[0]
            return value, offset + 5
        else:  # 0xff
            value = struct.unpack('<Q', data[offset+1:offset+9])[0]
            return value, offset + 9
    
    def double_sha256(self, data: bytes) -> str:
        """Calculate double SHA256 hash"""
        return hashlib.sha256(hashlib.sha256(data).digest()).digest()[::-1].hex()
    
    def parse_transaction(self, data: bytes, offset: int) -> Tuple[Transaction, int]:
        """
        Parse a single transaction from binary data
        Returns: (transaction, new_offset)
        """
        start_offset = offset
        
        # Version (4 bytes)
        version = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        # Input count (varint)
        input_count, offset = self.read_varint(data, offset)
        
        # Parse inputs
        inputs = []
        for _ in range(input_count):
            # Previous output hash (32 bytes)
            prev_hash = data[offset:offset+32][::-1].hex()
            offset += 32
            
            # Previous output index (4 bytes)
            prev_index = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            
            # Script length (varint)
            script_len, offset = self.read_varint(data, offset)
            
            # Script
            script = data[offset:offset+script_len]
            offset += script_len
            
            # Sequence (4 bytes)
            sequence = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            
            inputs.append(TransactionInput(
                previous_output_hash=prev_hash,
                previous_output_index=prev_index,
                script_length=script_len,
                script=script,
                sequence=sequence
            ))
        
        # Output count (varint)
        output_count, offset = self.read_varint(data, offset)
        
        # Parse outputs
        outputs = []
        for _ in range(output_count):
            # Value (8 bytes)
            value = struct.unpack('<Q', data[offset:offset+8])[0]
            offset += 8
            
            # Script length (varint)
            script_len, offset = self.read_varint(data, offset)
            
            # Script
            script = data[offset:offset+script_len]
            offset += script_len
            
            outputs.append(TransactionOutput(
                value=value,
                script_length=script_len,
                script=script
            ))
        
        # Locktime (4 bytes)
        locktime = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        # Calculate transaction hash
        tx_data = data[start_offset:offset]
        txid = self.double_sha256(tx_data)
        
        transaction = Transaction(
            version=version,
            inputs=inputs,
            outputs=outputs,
            locktime=locktime,
            txid=txid,
            size=len(tx_data)
        )
        
        return transaction, offset
    
    def parse_block(self, data: bytes, offset: int) -> Tuple[Block, int]:
        """
        Parse a single block from binary data
        Returns: (block, new_offset)
        """
        block_start = offset
        
        # Block header (80 bytes)
        version = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        prev_hash = data[offset:offset+32][::-1].hex()
        offset += 32
        
        merkle_root = data[offset:offset+32][::-1].hex()
        offset += 32
        
        timestamp = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        bits = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        nonce = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        # Calculate block hash
        header_data = data[block_start:block_start+80]
        block_hash = self.double_sha256(header_data)
        
        header = BlockHeader(
            version=version,
            previous_block_hash=prev_hash,
            merkle_root=merkle_root,
            timestamp=timestamp,
            bits=bits,
            nonce=nonce,
            block_hash=block_hash
        )
        
        # Transaction count (varint)
        tx_count, offset = self.read_varint(data, offset)
        
        # Parse transactions
        transactions = []
        for _ in range(tx_count):
            tx, offset = self.parse_transaction(data, offset)
            transactions.append(tx)
        
        block = Block(
            header=header,
            transaction_count=tx_count,
            transactions=transactions
        )
        
        return block, offset
    
    def parse_file(self, max_blocks: Optional[int] = None) -> List[Block]:
        """
        Parse all blocks from the blk file
        Args:
            max_blocks: Maximum number of blocks to parse (None for all)
        Returns:
            List of parsed blocks
        """
        blocks = []
        
        with open(self.filepath, 'rb') as f:
            data = f.read()
        
        offset = 0
        block_count = 0
        
        while offset < len(data):
            # Look for magic bytes
            if data[offset:offset+4] != self.MAGIC_BYTES:
                offset += 1
                continue
            
            offset += 4
            
            # Block size (4 bytes)
            if offset + 4 > len(data):
                break
            
            block_size = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            
            # Parse block
            if offset + block_size > len(data):
                break
            
            try:
                block, new_offset = self.parse_block(data, offset)
                blocks.append(block)
                offset = new_offset
                block_count += 1
                
                if max_blocks and block_count >= max_blocks:
                    break
            except Exception as e:
                print(f"Error parsing block: {e}")
                offset += block_size
        
        return blocks