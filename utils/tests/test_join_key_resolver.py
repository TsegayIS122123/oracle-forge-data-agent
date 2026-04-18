"""
Tests for join_key_resolver.py
"""

import pytest
from utils.join_key_resolver import (
    JoinKeyResolver,
    KeyFormat,
    KeyConversion,
    normalize_key,
    detect_format_mismatch
)


class TestKeyFormat:
    """Tests for KeyFormat enum."""
    
    def test_key_format_values(self):
        assert KeyFormat.INTEGER.value == "integer"
        assert KeyFormat.STRING.value == "string"
        assert KeyFormat.CUST_PREFIXED.value == "cust_prefixed"
        assert KeyFormat.ORD_PREFIXED.value == "ord_prefixed"
        assert KeyFormat.UUID.value == "uuid"
        assert KeyFormat.OBJECT_ID.value == "object_id"


class TestJoinKeyResolverFormatDetection:
    """Tests for format detection."""
    
    @pytest.fixture
    def resolver(self):
        return JoinKeyResolver()
    
    def test_detect_integer(self, resolver):
        assert resolver.detect_format(123) == KeyFormat.INTEGER
        assert resolver.detect_format("456") == KeyFormat.INTEGER
        assert resolver.detect_format("007") == KeyFormat.INTEGER
    
    def test_detect_cust_prefixed(self, resolver):
        assert resolver.detect_format("CUST-00123") == KeyFormat.CUST_PREFIXED
        assert resolver.detect_format("cust-00001") == KeyFormat.CUST_PREFIXED
        assert resolver.detect_format("CUST-99999") == KeyFormat.CUST_PREFIXED
    
    def test_detect_ord_prefixed(self, resolver):
        assert resolver.detect_format("ORD-2024-00123") == KeyFormat.ORD_PREFIXED
        assert resolver.detect_format("ord-2023-00001") == KeyFormat.ORD_PREFIXED
    
    def test_detect_uuid(self, resolver):
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        assert resolver.detect_format(uuid_str) == KeyFormat.UUID
    
    def test_detect_object_id(self, resolver):
        oid = "507f1f77bcf86cd799439011"
        assert resolver.detect_format(oid) == KeyFormat.OBJECT_ID
    
    def test_detect_string(self, resolver):
        assert resolver.detect_format("abc123") == KeyFormat.STRING
        assert resolver.detect_format("some-random-value") == KeyFormat.STRING
    
    def test_detect_none(self, resolver):
        assert resolver.detect_format(None) == KeyFormat.STRING


class TestJoinKeyResolverConversions:
    """Tests for format conversions."""
    
    @pytest.fixture
    def resolver(self):
        return JoinKeyResolver()
    
    def test_int_to_cust_prefixed(self, resolver):
        assert resolver.int_to_cust_prefixed(123) == "CUST-00123"
        assert resolver.int_to_cust_prefixed(1) == "CUST-00001"
        assert resolver.int_to_cust_prefixed(99999) == "CUST-99999"
        assert resolver.int_to_cust_prefixed("456") == "CUST-00456"
    
    def test_cust_prefixed_to_int(self, resolver):
        assert resolver.cust_prefixed_to_int("CUST-00123") == 123
        assert resolver.cust_prefixed_to_int("CUST-00001") == 1
        assert resolver.cust_prefixed_to_int("cust-00123") == 123
        assert resolver.cust_prefixed_to_int("CUST-00123") == 123
    
    def test_cust_prefixed_to_int_invalid(self, resolver):
        with pytest.raises(ValueError, match="Cannot parse"):
            resolver.cust_prefixed_to_int("INVALID-00123")
    
    def test_ord_prefixed_to_int(self, resolver):
        assert resolver.ord_prefixed_to_int("ORD-2024-00123") == 123
        assert resolver.ord_prefixed_to_int("ORD-2023-00001") == 1
    
    def test_ord_prefixed_to_int_invalid(self, resolver):
        with pytest.raises(ValueError, match="Cannot parse"):
            resolver.ord_prefixed_to_int("INVALID-2024-00123")
    
    def test_identity(self, resolver):
        assert resolver.identity("test") == "test"
        assert resolver.identity(123) == 123
        assert resolver.identity(None) is None


class TestJoinKeyResolverNormalization:
    """Tests for key normalization."""
    
    @pytest.fixture
    def resolver(self):
        return JoinKeyResolver()
    
    def test_normalize_customer_id_sqlite_to_postgres(self, resolver):
        result = resolver.normalize_key(
            "CUST-00123",
            "sqlite",
            "postgres",
            "customer_id"
        )
        assert result == 123
    
    def test_normalize_customer_id_postgres_to_sqlite(self, resolver):
        result = resolver.normalize_key(
            123,
            "postgres",
            "sqlite",
            "customer_id"
        )
        assert result == "CUST-00123"
    
    def test_normalize_no_conversion_needed(self, resolver):
        result = resolver.normalize_key(
            "abc123",
            "duckdb",
            "mongodb",
            "business_id"
        )
        assert result == "abc123"
    
    def test_normalize_with_cache(self, resolver):
        # First call caches
        result1 = resolver.normalize_key(
            "CUST-00123",
            "sqlite",
            "postgres",
            "customer_id"
        )
        
        # Second call should use cache
        result2 = resolver.normalize_key(
            "CUST-00456",
            "sqlite",
            "postgres",
            "customer_id"
        )
        
        assert result1 == 123
        assert result2 == 456
        assert "customer_id_sqlite_postgres" in resolver._conversion_cache
    
    def test_normalize_order_id(self, resolver):
        result = resolver.normalize_key(
            "ORD-2024-00123",
            "sqlite",
            "postgres",
            "order_id"
        )
        assert result == 123


class TestJoinKeyResolverMismatch:
    """Tests for mismatch detection."""
    
    @pytest.fixture
    def resolver(self):
        return JoinKeyResolver()
    
    def test_detect_mismatch_true(self, resolver):
        values = ["CUST-001", "CUST-002", "CUST-003"]
        has_mismatch, desc = resolver.detect_format_mismatch(values, KeyFormat.INTEGER)
        
        assert has_mismatch is True
        assert "Expected integer" in desc
        assert "cust_prefixed" in desc
    
    def test_detect_mismatch_false(self, resolver):
        values = [123, 456, 789]
        has_mismatch, desc = resolver.detect_format_mismatch(values, KeyFormat.INTEGER)
        
        assert has_mismatch is False
        assert desc is None
    
    def test_detect_mismatch_empty(self, resolver):
        values = []
        has_mismatch, desc = resolver.detect_format_mismatch(values, KeyFormat.INTEGER)
        
        assert has_mismatch is False
    
    def test_detect_mismatch_sample_size(self, resolver):
        values = ["CUST-001", 123, "CUST-003", 456, "CUST-005", 789]
        has_mismatch, desc = resolver.detect_format_mismatch(values, KeyFormat.INTEGER)
        
        # Should detect mismatch from first 5 values
        assert has_mismatch is True


class TestJoinKeyResolverBatch:
    """Tests for batch operations."""
    
    @pytest.fixture
    def resolver(self):
        return JoinKeyResolver()
    
    def test_batch_normalize(self, resolver):
        values = ["CUST-001", "CUST-002", "CUST-003"]
        result = resolver.batch_normalize(
            values,
            "sqlite",
            "postgres",
            "customer_id"
        )
        
        assert result == [1, 2, 3]
    
    def test_batch_normalize_empty(self, resolver):
        result = resolver.batch_normalize([], "sqlite", "postgres", "customer_id")
        assert result == []
    
    def test_create_join_mapping(self, resolver):
        source_keys = [1, 2, 3, 4]
        target_keys = ["CUST-001", "CUST-003", "CUST-005"]
        
        mapping = resolver.create_join_mapping(
            source_keys,
            target_keys,
            "postgres",
            "sqlite",
            "customer_id"
        )
        
        assert 1 in mapping
        assert 3 in mapping
        assert 2 not in mapping
        assert 4 not in mapping


class TestJoinKeyResolverDatasetConversions:
    """Tests for dataset-specific conversions."""
    
    @pytest.fixture
    def resolver(self):
        return JoinKeyResolver()
    
    def test_get_conversion_rule_exists(self, resolver):
        rule = resolver.get_conversion_rule(
            "crmarenapro",
            "customer_id",
            "cust_id"
        )
        
        assert rule is not None
        assert rule.source_format == KeyFormat.INTEGER
        assert rule.target_format == KeyFormat.CUST_PREFIXED
    
    def test_get_conversion_rule_not_found(self, resolver):
        rule = resolver.get_conversion_rule(
            "unknown",
            "field1",
            "field2"
        )
        
        assert rule is None


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_normalize_key_function(self):
        # Direct function call without creating resolver
        result = normalize_key("CUST-00123", "sqlite", "postgres", "customer_id")
        assert result == 123
    
    def test_detect_format_mismatch_function(self):
        values = ["CUST-001", "CUST-002"]
        has_mismatch, desc = detect_format_mismatch(values, "integer")
        
        assert has_mismatch is True
    
    def test_detect_format_mismatch_no_mismatch(self):
        values = [1, 2, 3]
        has_mismatch, desc = detect_format_mismatch(values, "integer")
        
        assert has_mismatch is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])