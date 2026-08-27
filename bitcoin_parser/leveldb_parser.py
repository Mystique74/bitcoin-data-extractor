"""
Parser for Bitcoin Core LevelDB chainstate database
Extracts UTXO (Unspent Transaction Output) data
"""

import plyvel
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import struct


@dataclass
class UTXO:
    """Represents an Unspent Transaction Output"""
    txid: str
    output_index: int
    amount: int
    script_length: int
    script: bytes
    block_height: int
    is_coinbase: bool


class LevelDBParser:
    """Parser for Bitcoin Core LevelDB chainstate database"""
    
    def __init__(self, db_path: str):
        """
        Initialize LevelDB parser
        Args:
            db_path: Path to the chainstate LevelDB directory
        """
        self.db = plyvel.DB(db_path, create_if_missing=False)
    
    def decode_varint(self, data: bytes, offset: int = 0) -> Tuple[int, int]:
        """
        Decode a variable-length integer
        Returns: (value, bytes_read)
        """
        value = 0
        shift = 0
        i = 0
        
        while True:
            byte = data[offset + i]
            value |= (byte & 0x7f) << shift
            i += 1
            
            if (byte & 0x80) == 0:
                break
            
            shift += 7
        
        return value, i
    
    def decode_amount(self, data: bytes) -> int:
        """Decode a compacted amount value"""
        if data == b'':
            return 0
        
        value, _ = self.decode_varint(data)
        
        if value == 0:
            return 0
        
        value -= 1
        
        if value % 2 == 0:
            return value // 2
        else:
            return -((value + 1) // 2)
    
    def parse_utxo_value(self, key: bytes, value: bytes) -> Optional[UTXO]:
        """
        Parse a UTXO from LevelDB key-value pair
        Key format: 'c' + txid (32 bytes) + output_index (4 bytes in varint)
        Value format: amount + script + height + is_coinbase flags
        """
        try:
            if key[0:1] != b'c':  # Only parse UTXO entries (key type 'c')
                return None
            
            # Parse key
            txid = key[1:33][::-1].hex()  # Reverse for display
            offset = 33
            
            output_index, varint_len = self.decode_varint(key, offset)
            
            # Parse value
            offset = 0
            amount_data_len = 0
            
            # Find script start (amount is varint-encoded)
            temp_offset = 0
            while temp_offset < len(value):
                byte = value[temp_offset]
                temp_offset += 1
                amount_data_len = temp_offset
                if (byte & 0x80) == 0:
                    break
            
            amount_varint = value[0:amount_data_len]
            amount = self.decode_amount(amount_varint)
            
            # Parse script
            script_offset = amount_data_len
            script_len, varint_len = self.decode_varint(value, script_offset)
            script_offset += varint_len
            script = value[script_offset:script_offset+script_len]
            
            # Parse height and coinbase flag
            height_offset = script_offset + script_len
            if height_offset < len(value):
                height_val, _ = self.decode_varint(value, height_offset)
                block_height = height_val >> 1
                is_coinbase = (height_val & 1) == 1
            else:
                block_height = 0
                is_coinbase = False
            
            return UTXO(
                txid=txid,
                output_index=output_index,
                amount=amount,
                script_length=script_len,
                script=script,
                block_height=block_height,
                is_coinbase=is_coinbase
            )
        
        except Exception as e:
            print(f"Error parsing UTXO: {e}")
            return None
    
    def get_all_utxos(self, limit: Optional[int] = None) -> List[UTXO]:
        """
        Extract all UTXOs from the chainstate database
        Args:
            limit: Maximum number of UTXOs to extract (None for all)
        Returns:
            List of UTXO objects
        """
        utxos = []
        count = 0
        
        for key, value in self.db.items():
            if key[0:1] == b'c':  # UTXO entries start with 'c'
                utxo = self.parse_utxo_value(key, value)
                if utxo:
                    utxos.append(utxo)
                    count += 1
                    
                    if limit and count >= limit:
                        break
        
        return utxos
    
    def get_utxo_stats(self) -> Dict:
        """Calculate statistics about the UTXO set"""
        stats = {
            'total_utxos': 0,
            'total_value': 0,
            'average_value': 0,
            'coinbase_utxos': 0,
        }
        
        for key, value in self.db.items():
            if key[0:1] == b'c':
                utxo = self.parse_utxo_value(key, value)
                if utxo:
                    stats['total_utxos'] += 1
                    stats['total_value'] += utxo.amount
                    if utxo.is_coinbase:
                        stats['coinbase_utxos'] += 1
        
        if stats['total_utxos'] > 0:
            stats['average_value'] = stats['total_value'] / stats['total_utxos']
        
        return stats
    
    def close(self):
        """Close the LevelDB connection"""
        self.db.close()