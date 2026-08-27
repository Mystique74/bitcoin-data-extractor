"""
Data persistence tools for Bitcoin blockchain data
Export to SQLite, PostgreSQL, and CSV formats
"""

import sqlite3
import csv
import json
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import asdict


class SQLitePersistence:
    """Export blockchain data to SQLite database"""
    
    def __init__(self, db_path: str):
        """
        Initialize SQLite persistence
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database connection and initialize tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Create all necessary tables"""
        # Blocks table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_hash TEXT PRIMARY KEY,
                block_height INTEGER UNIQUE NOT NULL,
                version INTEGER,
                previous_block_hash TEXT,
                merkle_root TEXT,
                timestamp INTEGER,
                bits INTEGER,
                nonce INTEGER,
                transaction_count INTEGER,
                total_input_value INTEGER,
                total_output_value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                txid TEXT PRIMARY KEY,
                block_hash TEXT NOT NULL,
                block_height INTEGER NOT NULL,
                version INTEGER,
                input_count INTEGER,
                output_count INTEGER,
                locktime INTEGER,
                size INTEGER,
                is_coinbase BOOLEAN,
                total_input_value INTEGER,
                total_output_value INTEGER,
                fee INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(block_hash) REFERENCES blocks(block_hash)
            )
        ''')
        
        # Inputs table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txid TEXT NOT NULL,
                input_index INTEGER NOT NULL,
                previous_output_hash TEXT,
                previous_output_index INTEGER,
                script_length INTEGER,
                script_hex TEXT,
                sequence INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(txid, input_index),
                FOREIGN KEY(txid) REFERENCES transactions(txid)
            )
        ''')
        
        # Outputs table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txid TEXT NOT NULL,
                output_index INTEGER NOT NULL,
                value INTEGER NOT NULL,
                script_length INTEGER,
                script_hex TEXT,
                script_type TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(txid, output_index),
                FOREIGN KEY(txid) REFERENCES transactions(txid)
            )
        ''')
        
        # Addresses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                address TEXT PRIMARY KEY,
                script_type TEXT,
                balance INTEGER DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                first_seen_block INTEGER,
                last_seen_block INTEGER,
                is_change BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Address transactions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS address_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                txid TEXT NOT NULL,
                amount INTEGER,
                is_input BOOLEAN,
                block_height INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(address, txid, is_input),
                FOREIGN KEY(address) REFERENCES addresses(address),
                FOREIGN KEY(txid) REFERENCES transactions(txid)
            )
        ''')
        
        # Fees table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fees (
                txid TEXT PRIMARY KEY,
                fee INTEGER,
                fee_rate REAL,
                input_count INTEGER,
                output_count INTEGER,
                size INTEGER,
                block_height INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(txid) REFERENCES transactions(txid)
            )
        ''')
        
        # Create indexes for better query performance
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_height ON blocks(block_height)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_block ON transactions(block_hash)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_height ON transactions(block_height)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_address ON addresses(address)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_addr_txs ON address_transactions(address)')
        
        self.conn.commit()
    
    def insert_block(self, block) -> bool:
        """
        Insert a block into database
        
        Args:
            block: Block object
        
        Returns:
            True if successful
        """
        try:
            self.cursor.execute('''
                INSERT INTO blocks (
                    block_hash, block_height, version, previous_block_hash,
                    merkle_root, timestamp, bits, nonce, transaction_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                block.header.block_hash,
                0,  # Will be updated when we know the height
                block.header.version,
                block.header.previous_block_hash,
                block.header.merkle_root,
                block.header.timestamp,
                block.header.bits,
                block.header.nonce,
                block.transaction_count
            ))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error inserting block: {e}")
            return False
    
    def insert_transaction(self, txid: str, block_hash: str, block_height: int, 
                          tx_data: Dict) -> bool:
        """
        Insert a transaction into database
        
        Args:
            txid: Transaction ID
            block_hash: Block hash containing this transaction
            block_height: Block height
            tx_data: Transaction data dictionary
        
        Returns:
            True if successful
        """
        try:
            self.cursor.execute('''
                INSERT INTO transactions (
                    txid, block_hash, block_height, version, input_count,
                    output_count, locktime, size, is_coinbase,
                    total_input_value, total_output_value, fee
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                txid,
                block_hash,
                block_height,
                tx_data.get('version', 1),
                tx_data.get('input_count', 0),
                tx_data.get('output_count', 0),
                tx_data.get('locktime', 0),
                tx_data.get('size', 0),
                tx_data.get('is_coinbase', False),
                tx_data.get('total_input_value', 0),
                tx_data.get('total_output_value', 0),
                tx_data.get('fee', 0)
            ))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error inserting transaction: {e}")
            return False
    
    def insert_input(self, txid: str, input_index: int, input_data: Dict) -> bool:
        """Insert a transaction input"""
        try:
            self.cursor.execute('''
                INSERT INTO inputs (
                    txid, input_index, previous_output_hash, previous_output_index,
                    script_length, script_hex, sequence
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                txid,
                input_index,
                input_data.get('previous_output_hash'),
                input_data.get('previous_output_index'),
                input_data.get('script_length', 0),
                input_data.get('script_hex'),
                input_data.get('sequence', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting input: {e}")
            return False
    
    def insert_output(self, txid: str, output_index: int, output_data: Dict) -> bool:
        """Insert a transaction output"""
        try:
            self.cursor.execute('''
                INSERT INTO outputs (
                    txid, output_index, value, script_length,
                    script_hex, script_type, address
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                txid,
                output_index,
                output_data.get('value', 0),
                output_data.get('script_length', 0),
                output_data.get('script_hex'),
                output_data.get('script_type'),
                output_data.get('address')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting output: {e}")
            return False
    
    def insert_address(self, address_data: Dict) -> bool:
        """Insert an address"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO addresses (
                    address, script_type, balance, transaction_count,
                    first_seen_block, last_seen_block
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                address_data.get('address'),
                address_data.get('script_type'),
                address_data.get('balance', 0),
                address_data.get('transaction_count', 0),
                address_data.get('first_seen_block'),
                address_data.get('last_seen_block')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting address: {e}")
            return False
    
    def insert_fee(self, fee_data: Dict) -> bool:
        """Insert fee analysis data"""
        try:
            self.cursor.execute('''
                INSERT INTO fees (
                    txid, fee, fee_rate, input_count, output_count,
                    size, block_height
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                fee_data.get('txid'),
                fee_data.get('fee', 0),
                fee_data.get('fee_rate', 0),
                fee_data.get('input_count', 0),
                fee_data.get('output_count', 0),
                fee_data.get('size', 0),
                fee_data.get('block_height', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting fee: {e}")
            return False
    
    def query_top_addresses(self, limit: int = 100) -> List[Dict]:
        """Get top addresses by balance"""
        try:
            self.cursor.execute('''
                SELECT address, script_type, balance, transaction_count
                FROM addresses
                ORDER BY balance DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error querying addresses: {e}")
            return []
    
    def query_block_statistics(self, block_height: int) -> Optional[Dict]:
        """Get statistics for a specific block"""
        try:
            self.cursor.execute('''
                SELECT 
                    b.block_hash,
                    b.timestamp,
                    COUNT(t.txid) as transaction_count,
                    SUM(t.size) as total_size,
                    SUM(t.fee) as total_fees,
                    AVG(t.fee_rate) as avg_fee_rate
                FROM blocks b
                LEFT JOIN transactions t ON b.block_hash = t.block_hash
                WHERE b.block_height = ?
                GROUP BY b.block_hash
            ''', (block_height,))
            
            columns = [description[0] for description in self.cursor.description]
            row = self.cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except Exception as e:
            print(f"Error querying block: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class CSVExporter:
    """Export blockchain data to CSV files"""
    
    def __init__(self, output_dir: str = "."):
        """
        Initialize CSV exporter
        
        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_blocks(self, blocks: List, filename: str = "blocks.csv"):
        """Export blocks to CSV"""
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'block_hash', 'timestamp', 'version', 'nonce',
                    'transaction_count', 'previous_hash'
                ])
                
                for block in blocks:
                    writer.writerow([
                        block.header.block_hash,
                        block.header.timestamp,
                        block.header.version,
                        block.header.nonce,
                        block.transaction_count,
                        block.header.previous_block_hash
                    ])
            
            print(f"Exported {len(blocks)} blocks to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting blocks: {e}")
            return False
    
    def export_transactions(self, transactions_data: List[Dict], 
                          filename: str = "transactions.csv"):
        """Export transactions to CSV"""
        filepath = self.output_dir / filename
        
        try:
            if not transactions_data:
                return False
            
            with open(filepath, 'w', newline='') as f:
                fieldnames = list(transactions_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(transactions_data)
            
            print(f"Exported {len(transactions_data)} transactions to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting transactions: {e}")
            return False
    
    def export_addresses(self, addresses: Dict, filename: str = "addresses.csv"):
        """Export addresses to CSV"""
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'address', 'script_type', 'balance', 'balance_btc',
                    'transaction_count', 'first_seen_block', 'last_seen_block'
                ])
                
                for address, info in sorted(addresses.items(), 
                                          key=lambda x: x[1].balance, 
                                          reverse=True):
                    writer.writerow([
                        address,
                        info.script_type,
                        info.balance,
                        info.balance / 1e8,
                        info.transaction_count,
                        info.first_seen_block,
                        info.last_seen_block
                    ])
            
            print(f"Exported {len(addresses)} addresses to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting addresses: {e}")
            return False
    
    def export_fees(self, fee_analyses: List, filename: str = "fees.csv"):
        """Export fee analysis to CSV"""
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'txid', 'fee', 'fee_rate', 'input_count',
                    'output_count', 'size', 'block_height'
                ])
                
                for analysis in fee_analyses:
                    writer.writerow([
                        analysis.txid,
                        analysis.fee,
                        f"{analysis.fee_rate:.4f}",
                        analysis.input_count,
                        analysis.output_count,
                        analysis.size,
                        analysis.block_height
                    ])
            
            print(f"Exported {len(fee_analyses)} fee records to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting fees: {e}")
            return False
    
    def export_statistics(self, stats_dict: Dict, filename: str = "statistics.json"):
        """Export statistics to JSON"""
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(stats_dict, f, indent=2)
            
            print(f"Exported statistics to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting statistics: {e}")
            return False


class JSONExporter:
    """Export blockchain data to JSON files"""
    
    def __init__(self, output_dir: str = "."):
        """
        Initialize JSON exporter
        
        Args:
            output_dir: Directory to save JSON files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_blocks(self, blocks: List, filename: str = "blocks.json"):
        """Export blocks to JSON"""
        filepath = self.output_dir / filename
        
        try:
            blocks_data = []
            for block in blocks:
                block_dict = {
                    'header': {
                        'block_hash': block.header.block_hash,
                        'version': block.header.version,
                        'previous_hash': block.header.previous_block_hash,
                        'merkle_root': block.header.merkle_root,
                        'timestamp': block.header.timestamp,
                        'bits': block.header.bits,
                        'nonce': block.header.nonce
                    },
                    'transaction_count': block.transaction_count
                }
                blocks_data.append(block_dict)
            
            with open(filepath, 'w') as f:
                json.dump(blocks_data, f, indent=2)
            
            print(f"Exported {len(blocks)} blocks to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting blocks: {e}")
            return False
    
    def export_addresses(self, addresses: Dict, filename: str = "addresses.json"):
        """Export addresses to JSON"""
        filepath = self.output_dir / filename
        
        try:
            addresses_data = []
            for address, info in sorted(addresses.items(),
                                       key=lambda x: x[1].balance,
                                       reverse=True):
                addresses_data.append({
                    'address': address,
                    'script_type': info.script_type,
                    'balance': info.balance,
                    'balance_btc': info.balance / 1e8,
                    'transaction_count': info.transaction_count,
                    'first_seen_block': info.first_seen_block,
                    'last_seen_block': info.last_seen_block
                })
            
            with open(filepath, 'w') as f:
                json.dump(addresses_data, f, indent=2)
            
            print(f"Exported {len(addresses)} addresses to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting addresses: {e}")
            return False
    
    def export_statistics(self, stats: Dict, filename: str = "statistics.json"):
        """Export statistics to JSON"""
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"Exported statistics to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting statistics: {e}")
            return False
