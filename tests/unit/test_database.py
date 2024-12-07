import pytest
import sqlite3
from datetime import datetime
from src.utils.database import DatabaseManager

@pytest.fixture
def db_manager():
    config = {
        'database': {
            'DB_PATH': ':memory:',
            'POOL_SIZE': 1
        }
    }
    manager = DatabaseManager(config)
    manager.setup_database()
    return manager

@pytest.fixture
def sample_owner():
    return {
        'license_plate': 'TEST123',
        'owner_name': 'John Doe',
        'email': 'john@example.com',
        'phone': '1234567890',
        'address': '123 Test St'
    }

@pytest.fixture
def sample_violation():
    return {
        'license_plate': 'TEST123',
        'violation_type': 'no_helmet',
        'fine_amount': 100.00,
        'image_path': 'violations/test.jpg',
        'location': 'Test Location'
    }

class TestDatabaseManager:
    def test_initialization(self, db_manager):
        """Test database initialization"""
        assert db_manager is not None
        
    def test_add_vehicle_owner(self, db_manager, sample_owner):
        """Test adding vehicle owner"""
        # Add owner
        success = db_manager.add_vehicle_owner(sample_owner)
        assert success
        
        # Verify owner was added
        owner = db_manager.get_vehicle_owner(sample_owner['license_plate'])
        assert owner['owner_name'] == sample_owner['owner_name']
        assert owner['email'] == sample_owner['email']
        
    def test_record_violation(self, db_manager, sample_owner, sample_violation):
        """Test recording violation"""
        # Add owner first
        db_manager.add_vehicle_owner(sample_owner)
        
        # Record violation
        violation_id = db_manager.record_violation(sample_violation)
        assert violation_id is not None
        
        # Verify violation was recorded
        violation = db_manager.get_violation(violation_id)
        assert violation['license_plate'] == sample_violation['license_plate']
        assert violation['violation_type'] == sample_violation['violation_type']
        
    def test_get_pending_violations(self, db_manager, sample_owner, sample_violation):
        """Test getting pending violations"""
        # Setup test data
        db_manager.add_vehicle_owner(sample_owner)
        db_manager.record_violation(sample_violation)
        
        # Get pending violations
        pending = db_manager.get_pending_violations()
        assert len(pending) > 0
        assert pending[0]['license_plate'] == sample_violation['license_plate']
        
    def test_mark_violation_processed(self, db_manager, sample_owner, sample_violation):
        """Test marking violation as processed"""
        # Setup test data
        db_manager.add_vehicle_owner(sample_owner)
        violation_id = db_manager.record_violation(sample_violation)
        
        # Mark as processed
        success = db_manager.mark_violation_processed(violation_id)
        assert success
        
        # Verify status
        violation = db_manager.get_violation(violation_id)
        assert violation['processed'] is True
        
    def test_violation_statistics(self, db_manager, sample_owner, sample_violation):
        """Test getting violation statistics"""
        # Setup test data
        db_manager.add_vehicle_owner(sample_owner)
        db_manager.record_violation(sample_violation)
        
        # Get statistics
        stats = db_manager.get_violation_statistics()
        assert stats['total_violations'] > 0
        assert stats['total_fines'] > 0
        assert 'no_helmet' in stats['violations_by_type']
        
    def test_payment_tracking(self, db_manager, sample_owner, sample_violation):
        """Test payment tracking"""
        # Setup test data
        db_manager.add_vehicle_owner(sample_owner)
        violation_id = db_manager.record_violation(sample_violation)
        
        # Record payment
        payment_data = {
            'violation_id': violation_id,
            'amount': sample_violation['fine_amount'],
            'payment_method': 'credit_card',
            'transaction_id': 'TXN123'
        }
        
        success = db_manager.record_payment(payment_data)
        assert success
        
        # Verify payment status
        violation = db_manager.get_violation(violation_id)
        assert violation['payment_status'] == 'paid'
        
    def test_concurrent_access(self, db_manager, sample_violation):
        """Test concurrent database access"""
        import threading
        
        def record_violations():
            for i in range(10):
                violation = sample_violation.copy()
                violation['license_plate'] = f"TEST{i}"
                db_manager.record_violation(violation)
                
        # Create multiple threads
        threads = [
            threading.Thread(target=record_violations)
            for _ in range(5)
        ]
        
        # Run threads
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
            
        # Verify all violations were recorded
        stats = db_manager.get_violation_statistics()
        assert stats['total_violations'] == 50  # 5 threads * 10 violations each
        
    @pytest.mark.parametrize("violation_type", [
        'no_helmet',
        'triple_riding',
        'no_license_plate'
    ])
    def test_different_violation_types(self, db_