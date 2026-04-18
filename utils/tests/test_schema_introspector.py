"""
Tests for schema_introspector.py
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from utils.schema_introspector import (
    SchemaIntrospector,
    DatabaseType,
    TableInfo,
    JoinPath,
    get_relevant_tables,
    get_join_path,
    generate_schema_prompt
)


class TestSchemaIntrospector:
    """Tests for SchemaIntrospector class."""
    
    @pytest.fixture
    def temp_kb(self):
        """Create temporary knowledge base for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = Path(tmpdir) / "kb"
            domain_path = kb_path / "domain"
            schemas_path = domain_path / "schemas"
            schemas_path.mkdir(parents=True)
            
            # Create test yelp schema
            yelp_schema = """# Yelp Dataset Schema
## DuckDB Tables

### Table: `businesses`
| Column | Type | Key | Description |
|--------|------|-----|-------------|
| business_id | VARCHAR | PK | Primary key |
| name | VARCHAR | | Business name |
| stars | FLOAT | | Average rating |

### Table: `users`
| Column | Type | Key | Description |
|--------|------|-----|-------------|
| user_id | VARCHAR | PK | Primary key |
| name | VARCHAR | | User name |

## MongoDB Collections

### Collection: `reviews`
| Field | Type | Description |
|-------|------|-------------|
| review_id | String | Review ID |
| business_id | String | FK to businesses |
| user_id | String | FK to users |
| text | String | Review text |
"""
            (schemas_path / "yelp_schema.md").write_text(yelp_schema)
            
            yield tmpdir
    
    def test_extract_keywords_yelp(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        query = "Find all reviews for businesses with more than 4 stars"
        keywords = introspector.extract_keywords(query)
        
        assert "review" in keywords
        assert "business" in keywords
    
    def test_extract_keywords_crm(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        query = "Customer spend by support ticket count"
        keywords = introspector.extract_keywords(query)
        
        assert "customer" in keywords
        assert "ticket" in keywords
    
    def test_extract_keywords_empty(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        query = "SELECT * FROM unknown_table"
        keywords = introspector.extract_keywords(query)
        
        assert len(keywords) == 0
    
    def test_get_relevant_tables_yelp(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        query = "Average stars for businesses with reviews"
        tables = introspector.get_relevant_tables("yelp", query)
        
        assert "businesses" in tables or "reviews" in tables
    
    def test_get_relevant_tables_no_match(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        query = "Unknown query with no keywords"
        tables = introspector.get_relevant_tables("yelp", query)
        
        # Should return all tables when no keywords match
        assert len(tables) > 0
    
    def test_get_all_tables(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        tables = introspector.get_all_tables("yelp")
        assert "businesses" in tables
        assert "users" in tables
        assert "reviews" in tables
        assert "tips" in tables
    
    def test_get_all_tables_unknown_dataset(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        tables = introspector.get_all_tables("unknown")
        assert tables == []
    
    def test_get_table_schema(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        schema = introspector.get_table_schema("yelp", "businesses")
        
        assert schema is not None
        assert schema.name == "businesses"
        assert "business_id" in schema.columns
        assert "name" in schema.columns
        assert "stars" in schema.columns
    
    def test_get_table_schema_mongodb(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        schema = introspector.get_table_schema("yelp", "reviews")
        
        assert schema is not None
        assert schema.name == "reviews"
        assert schema.db_type == DatabaseType.MONGODB
    
    def test_get_table_schema_not_found(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        schema = introspector.get_table_schema("yelp", "nonexistent")
        assert schema is None
    
    def test_get_join_path_yelp(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        path = introspector.get_join_path("yelp", "businesses", "reviews")
        
        assert path is not None
        assert path.source_table == "businesses"
        assert path.target_table == "reviews"
        assert path.source_db == DatabaseType.DUCKDB
        assert path.target_db == DatabaseType.MONGODB
    
    def test_get_join_path_crm(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        path = introspector.get_join_path("crmarenapro", "customers", "tickets")
        
        assert path is not None
        assert "format_conversion" in path.__dict__ or path.format_conversion is not None
    
    def test_get_join_path_not_found(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        path = introspector.get_join_path("yelp", "unknown1", "unknown2")
        assert path is None
    
    def test_get_all_join_paths(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        paths = introspector.get_all_join_paths("yelp", "businesses")
        
        assert len(paths) > 0
        for path in paths:
            assert path.source_table == "businesses" or path.target_table == "businesses"
    
    def test_generate_schema_prompt(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        prompt = introspector.generate_schema_prompt(
            dataset="yelp",
            query_text="Find businesses with reviews",
            include_all=False
        )
        
        assert "## Dataset: yelp" in prompt
        assert "businesses" in prompt
    
    def test_generate_schema_prompt_include_all(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        prompt = introspector.generate_schema_prompt(
            dataset="yelp",
            query_text="Query",
            include_all=True
        )
        
        assert "## Dataset: yelp" in prompt
        # Should include multiple tables
        assert "businesses" in prompt or "users" in prompt
    
    def test_infer_db_type_mongodb(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        db_type = introspector._infer_db_type("yelp", "reviews")
        assert db_type == DatabaseType.MONGODB
    
    def test_infer_db_type_postgres(self, temp_kb):
        introspector = SchemaIntrospector(kb_path=f"{temp_kb}/kb")
        
        db_type = introspector._infer_db_type("crmarenapro", "customers")
        assert db_type == DatabaseType.POSTGRESQL


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_get_relevant_tables_function(self):
        with patch('utils.schema_introspector.SchemaIntrospector') as MockIntrospector:
            mock_instance = Mock()
            mock_instance.get_relevant_tables.return_value = ["businesses", "reviews"]
            MockIntrospector.return_value = mock_instance
            
            tables = get_relevant_tables("yelp", "query", kb_path="/fake")
            
            assert tables == ["businesses", "reviews"]
            MockIntrospector.assert_called_once_with("/fake")
    
    def test_get_join_path_function(self):
        with patch('utils.schema_introspector.SchemaIntrospector') as MockIntrospector:
            mock_instance = Mock()
            mock_path = JoinPath(
                source_table="businesses",
                source_db=DatabaseType.DUCKDB,
                target_table="reviews",
                target_db=DatabaseType.MONGODB,
                join_keys=[("business_id", "business_id")],
                description="Test"
            )
            mock_instance.get_join_path.return_value = mock_path
            MockIntrospector.return_value = mock_instance
            
            path = get_join_path("yelp", "businesses", "reviews", kb_path="/fake")
            
            assert path == mock_path
    
    def test_generate_schema_prompt_function(self):
        with patch('utils.schema_introspector.SchemaIntrospector') as MockIntrospector:
            mock_instance = Mock()
            mock_instance.generate_schema_prompt.return_value = "Schema prompt"
            MockIntrospector.return_value = mock_instance
            
            prompt = generate_schema_prompt("yelp", "query", kb_path="/fake")
            
            assert prompt == "Schema prompt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])