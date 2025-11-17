#!/usr/bin/env python3
"""
Mock DynamoDB utilities for testing and offline development.

This module provides mock implementations of DynamoDB operations that can be used
across multiple plugins when the real DynamoDB service is not available.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger('mock_dynamo')

class MockDynamoTable:
    """Mock implementation of DynamoDB table for offline/testing use."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.items = []
        self._persistence_file = f".mock_dynamo_{table_name}.json"
        self._load_persisted_data()
        print(f"[DynamoDB] Using mock table: {table_name}")
    
    def _load_persisted_data(self):
        """Load persisted mock data from file if it exists."""
        try:
            if os.path.exists(self._persistence_file):
                with open(self._persistence_file, 'r') as f:
                    data = json.load(f)
                    self.items = data.get('items', [])
                    logger.info(f"Loaded {len(self.items)} items from {self._persistence_file}")
        except Exception as e:
            logger.warning(f"Could not load persisted data: {e}")
            self.items = []
    
    def _persist_data(self):
        """Persist mock data to file for future sessions."""
        try:
            data = {
                'table_name': self.table_name,
                'last_updated': datetime.utcnow().isoformat(),
                'items': self.items
            }
            with open(self._persistence_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not persist data: {e}")
    
    def put_item(self, Item: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of put_item."""
        # Convert any datetime objects to strings for JSON serialization
        item_copy = self._serialize_item(Item)
        
        # Check if item already exists (by primary key if available)
        existing_index = self._find_item_index(item_copy)
        
        if existing_index >= 0:
            # Update existing item
            self.items[existing_index] = item_copy
            action = "updated"
        else:
            # Add new item
            self.items.append(item_copy)
            action = "stored"
        
        print(f"[DynamoDB] Item {action} in mock table (total: {len(self.items)})")
        
        # Persist data periodically (every 10 items to avoid too much I/O)
        if len(self.items) % 10 == 0:
            self._persist_data()
        
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}
    
    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of get_item."""
        for item in self.items:
            if all(str(item.get(k)) == str(v) for k, v in Key.items()):
                return {"Item": item}
        return {}
    
    def scan(self, **kwargs) -> Dict[str, Any]:
        """Mock implementation of scan operation."""
        filtered_items = []
        
        # Get FilterExpression if provided
        filter_expr = kwargs.get('FilterExpression')
        
        if filter_expr:
            # Simple mock filtering - check for common patterns
            for item in self.items:
                if self._matches_filter(item, filter_expr):
                    filtered_items.append(item)
        else:
            filtered_items = self.items[:]
        
        # Apply Limit if specified
        limit = kwargs.get('Limit')
        if limit:
            filtered_items = filtered_items[:limit]
        
        return {
            'Items': filtered_items,
            'Count': len(filtered_items),
            'ScannedCount': len(self.items)
        }
    
    def query(self, **kwargs) -> Dict[str, Any]:
        """Mock implementation of query operation."""
        # For simplicity, treat query like scan for now
        # In a real implementation, this would use KeyConditionExpression
        return self.scan(**kwargs)
    
    def delete_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of delete_item."""
        initial_count = len(self.items)
        self.items = [item for item in self.items 
                     if not all(str(item.get(k)) == str(v) for k, v in Key.items())]
        
        deleted_count = initial_count - len(self.items)
        if deleted_count > 0:
            print(f"[DynamoDB] Deleted {deleted_count} item(s) from mock table")
            self._persist_data()
        
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}
    
    def batch_write_item(self, RequestItems: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of batch_write_item."""
        table_requests = RequestItems.get(self.table_name, [])
        processed_count = 0
        
        for request in table_requests:
            if 'PutRequest' in request:
                self.put_item(request['PutRequest']['Item'])
                processed_count += 1
            elif 'DeleteRequest' in request:
                self.delete_item(request['DeleteRequest']['Key'])
                processed_count += 1
        
        print(f"[DynamoDB] Batch processed {processed_count} items")
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}
    
    def _serialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert item to JSON-serializable format."""
        serialized = {}
        for key, value in item.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized
    
    def _find_item_index(self, item: Dict[str, Any]) -> int:
        """Find index of existing item with same primary key."""
        # Try common primary key patterns
        primary_keys = [
            'id', 'pk', 'partition_key', 'hash_key',
            'trade_id', 'news_id', 'sentiment_id', 'coin_sentiment_id',
            'summary_id', 'overall_sentiment_id'
        ]
        
        for pk in primary_keys:
            if pk in item:
                for i, existing_item in enumerate(self.items):
                    if existing_item.get(pk) == item[pk]:
                        return i
        
        return -1  # Not found
    
    def _matches_filter(self, item: Dict[str, Any], filter_expr) -> bool:
        """Simple mock filter matching."""
        # This is a very basic implementation
        # In reality, FilterExpression is a complex boto3 condition object
        
        # Convert filter to string for basic pattern matching
        filter_str = str(filter_expr).lower()
        
        # Check for common patterns
        if 'type' in filter_str:
            # Look for type filters like Attr('type').eq('sentiment')
            if "'news_sentiment'" in filter_str and item.get('type') == 'news_sentiment':
                return True
            elif "'coin_sentiment'" in filter_str and item.get('type') == 'coin_sentiment':
                return True
            elif "'sentiment_summary'" in filter_str and item.get('type') == 'sentiment_summary':
                return True
            elif "'overall_sentiment'" in filter_str and item.get('type') == 'overall_sentiment':
                return True
        
        # Check timestamp ranges (very basic)
        if 'timestamp' in filter_str and 'between' in filter_str:
            # For now, return True for timestamp filters
            return True
        
        # Check specific coin filters
        if 'coin' in filter_str and item.get('coin'):
            return True
        
        # Default: include item if no specific filters matched
        return len(filter_str) == 0 or 'type' not in filter_str
    
    def clear_all_data(self):
        """Clear all data (useful for testing)."""
        self.items = []
        if os.path.exists(self._persistence_file):
            os.remove(self._persistence_file)
        print(f"[DynamoDB] Cleared all data from mock table {self.table_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the mock table."""
        type_counts = {}
        for item in self.items:
            item_type = item.get('type', 'unknown')
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        return {
            'table_name': self.table_name,
            'total_items': len(self.items),
            'type_breakdown': type_counts,
            'persistence_file': self._persistence_file
        }


class MockDynamoResource:
    """Mock implementation of DynamoDB resource."""
    
    def __init__(self):
        self._tables = {}
        print("[DynamoDB] Using mock DynamoDB resource")
    
    def Table(self, name: str) -> MockDynamoTable:
        """Get or create a mock table."""
        if name not in self._tables:
            self._tables[name] = MockDynamoTable(name)
        return self._tables[name]
    
    def create_table(self, **kwargs) -> MockDynamoTable:
        """Mock table creation."""
        table_name = kwargs.get('TableName', 'unknown')
        print(f"[DynamoDB] Mock table '{table_name}' created")
        return self.Table(table_name)
    
    def list_tables(self) -> Dict[str, List[str]]:
        """List all mock tables."""
        return {'TableNames': list(self._tables.keys())}


def setup_mock_dynamodb(table_name: str = "trading_trades") -> MockDynamoTable:
    """Set up and return a mock DynamoDB table."""
    return MockDynamoTable(table_name)


def get_mock_dynamo_stats(table_name: str = "trading_trades") -> Dict[str, Any]:
    """Get statistics from the mock DynamoDB table."""
    table = MockDynamoTable(table_name)
    return table.get_stats()


def clear_mock_dynamo_data(table_name: str = "trading_trades"):
    """Clear all data from the mock DynamoDB table."""
    table = MockDynamoTable(table_name)
    table.clear_all_data()


# Example usage and testing
if __name__ == "__main__":
    # Test the mock DynamoDB functionality
    print("Testing Mock DynamoDB...")
    
    table = setup_mock_dynamodb("test_table")
    
    # Test put_item
    test_item = {
        'id': 'test_1',
        'timestamp': datetime.utcnow().isoformat(),
        'data': 'test data',
        'type': 'test'
    }
    
    table.put_item(Item=test_item)
    
    # Test get_item
    result = table.get_item(Key={'id': 'test_1'})
    print(f"Retrieved item: {result}")
    
    # Test scan
    scan_result = table.scan()
    print(f"Scan result: {len(scan_result['Items'])} items")
    
    # Test stats
    stats = table.get_stats()
    print(f"Table stats: {stats}")
    
    print("Mock DynamoDB test complete!")
