"""
Parser for Bitcoin Core rev*.dat (undo) files
Used for blockchain reorganizations
"""

import struct
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class UndoData:
    """Represents undo/revert information for a transaction"""
    txid: str
    output_index: int
    block_height: int
    amount: int
    script_length: int
    script: bytes


@dataclass
class BlockUndo:
    """Represents undo data for an entire block"""
    undo_entries: List[UndoData]


class RevParser:
    """Parser for Bitcoin Core rev*.dat files"""
    
    def __init__(self, filepath: str):
        """Initialize parser with a rev*.dat file"""
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
    
    def decode_amount(self, data: bytes) -> int:
        """Decode a compacted amount value from undo data"""
        if data == b'':
            return 0
        
        value, _ = self.read_varint(data, 0)
        
        if value == 0:
            return 0
        
        value -= 1
        
        # Decode based on odd/even
        if value % 2 == 0:
            return value // 2
        else:
            return -((value + 1) // 2)
    
    def parse_undo_data(self, data: bytes, offset: int) -> Tuple[UndoData, int]:
        """
        Parse undo data entry
        Returns: (undo_data, new_offset)
        """
        # Read output index
        output_index, offset = self.read_varint(data, offset)
        
        # Read amount (compacted)
        amount_len = 1
        while offset + amount_len < len(data) and (data[offset + amount_len - 1] & 0x80):
            amount_len += 1
        
        amount_data = data[offset:offset+amount_len]
        amount = self.decode_amount(amount_data)
        offset += amount_len
        
        # Read script length
        script_len, offset = self.read_varint(data, offset)
        
        # Read script
        script = data[offset:offset+script_len]
        offset += script_len
        
        # Read height and coinbase flag
        height_val, offset = self.read_varint(data, offset)
        block_height = height_val >> 1
        is_coinbase = (height_val & 1) == 1
        
        undo_data = UndoData(
            txid="",  # Will be populated by caller
            output_index=output_index,
            block_height=block_height,
            amount=amount,
            script_length=script_len,
            script=script
        )
        
        return undo_data, offset
    
    def parse_block_undo(self, data: bytes, offset: int) -> Tuple[BlockUndo, int]:
        """
        Parse undo data for a single block
        Returns: (block_undo, new_offset)
        """
        # Read transaction count
        tx_count, offset = self.read_varint(data, offset)
        
        undo_entries = []
        
        # Parse undo data for each transaction
        for _ in range(tx_count):
            # Read number of outputs for this transaction
            output_count, offset = self.read_varint(data, offset)
            
            # Parse each output's undo data
            for _ in range(output_count):
                undo_data, offset = self.parse_undo_data(data, offset)
                undo_entries.append(undo_data)
        
        block_undo = BlockUndo(undo_entries=undo_entries)
        return block_undo, offset
    
    def parse_file(self, max_blocks: Optional[int] = None) -> List[BlockUndo]:
        """
        Parse all undo blocks from the rev file
        Args:
            max_blocks: Maximum number of blocks to parse (None for all)
        Returns:
            List of parsed block undo data
        """
        block_undos = []
        
        with open(self.filepath, 'rb') as f:
            data = f.read()
        
        offset = 0
        block_count = 0
        
        while offset < len(data):
            try:
                block_undo, offset = self.parse_block_undo(data, offset)
                block_undos.append(block_undo)
                block_count += 1
                
                if max_blocks and block_count >= max_blocks:
                    break
            except Exception as e:
                print(f"Error parsing block undo at offset {offset}: {e}")
                break
        
        return block_undos
    
    def get_undo_stats(self, block_undos: List[BlockUndo]) -> dict:
        """Calculate statistics from parsed undo data"""
        stats = {
            'total_blocks': len(block_undos),
            'total_undo_entries': 0,
            'total_value_undone': 0,
        }
        
        for block_undo in block_undos:
            stats['total_undo_entries'] += len(block_undo.undo_entries)
            for undo in block_undo.undo_entries:
                stats['total_value_undone'] += undo.amount
        
        return stats