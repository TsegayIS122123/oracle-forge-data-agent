"""
Multi-Pass Retrieval Helper

Implements iterative query refinement with progressive context enrichment.
Based on Claude Code's hierarchical memory loading pattern.

Pass 1: Raw schema only (fast, low context)
Pass 2: Add join key glossary if cross-DB detected
Pass 3: Add domain terms if semantic ambiguity detected
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class PassLevel(Enum):
    """Context enrichment levels."""
    SCHEMA_ONLY = 1
    JOIN_KEYS = 2
    DOMAIN_TERMS = 3
    CORRECTIONS = 4


@dataclass
class QueryContext:
    """Context assembled for a query pass."""
    dataset: str
    query_text: str
    pass_level: PassLevel
    schema_info: str = ""
    join_key_glossary: str = ""
    domain_terms: str = ""
    corrections: str = ""
    
    def to_prompt(self) -> str:
        """Convert context to injectable prompt."""
        sections = []
        
        if self.schema_info:
            sections.append(f"## Schema Information\n{self.schema_info}")
        
        if self.join_key_glossary:
            sections.append(f"## Join Key Resolution\n{self.join_key_glossary}")
        
        if self.domain_terms:
            sections.append(f"## Domain Definitions\n{self.domain_terms}")
        
        if self.corrections:
            sections.append(f"## Previous Corrections\n{self.corrections}")
        
        sections.append(f"## Query\n{self.query_text}")
        
        return "\n\n".join(sections)


@dataclass
class PassResult:
    """Result from a single query pass."""
    pass_level: PassLevel
    answer: Any
    success: bool
    error_message: Optional[str] = None
    trace: List[Dict] = field(default_factory=list)
    context_used: QueryContext = None


class MultiPassRetriever:
    """
    Execute queries with progressive context enrichment.
    
    The retriever starts with minimal context (schema only) and progressively
    adds more context layers only when previous passes fail or indicate
    insufficient information.
    """
    
    def __init__(self, kb_path: str = "kb"):
        """
        Initialize the retriever with path to knowledge base.
        
        Args:
            kb_path: Root path to knowledge base directory
        """
        self.kb_path = kb_path
        self._schema_cache: Dict[str, str] = {}
        self._glossary_cache: Dict[str, str] = {}
        self._terms_cache: Dict[str, str] = {}
        self._corrections_cache: List[str] = []
    
    def detect_cross_database(self, query_text: str, dataset: str) -> bool:
        """
        Detect if query requires joining across multiple database systems.
        
        Args:
            query_text: Natural language query
            dataset: Dataset name
            
        Returns:
            True if cross-database join likely needed
        """
        # Keywords indicating cross-database joins
        cross_db_patterns = [
            r'join.*mongo.*postgres',
            r'across.*database',
            r'combine.*from',
            r'both.*and.*database',
            r'reviews.*businesses',  # Yelp: MongoDB + DuckDB
            r'tickets.*customers',   # CRMArenaPro: SQLite + PostgreSQL
            r'articles.*categories', # AG News: MongoDB + SQLite
        ]
        
        query_lower = query_text.lower()
        
        for pattern in cross_db_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check dataset-specific cross-DB indicators
        dataset_indicators = {
            'yelp': ['reviews', 'tips', 'checkins'],
            'crmarenapro': ['tickets', 'support', 'campaign'],
            'agnews': ['article', 'news', 'category'],
        }
        
        if dataset in dataset_indicators:
            for indicator in dataset_indicators[dataset]:
                if indicator in query_lower:
                    return True
        
        return False
    
    def detect_semantic_ambiguity(self, query_text: str) -> List[str]:
        """
        Detect ambiguous business terms requiring domain definitions.
        
        Args:
            query_text: Natural language query
            
        Returns:
            List of ambiguous terms found
        """
        ambiguous_terms = {
            'active': 'Definition varies by dataset',
            'churn': 'Time window definition required',
            'recent': 'Temporal scope ambiguous',
            'high_value': 'Threshold undefined',
            'loyal': 'Definition varies',
            'engaged': 'Metric undefined',
            'converted': 'Pipeline stage unclear',
        }
        
        found_terms = []
        query_lower = query_text.lower()
        
        for term in ambiguous_terms:
            if term in query_lower:
                found_terms.append(term)
        
        return found_terms
    
    def detect_join_key_mismatch(self, query_text: str, dataset: str) -> bool:
        """
        Detect if query involves tables with known format mismatches.
        
        Args:
            query_text: Natural language query
            dataset: Dataset name
            
        Returns:
            True if format mismatch likely
        """
        mismatch_indicators = {
            'crmarenapro': [
                ('customer', 'ticket'),
                ('cust_id', 'customer_id'),
                ('product_code', 'sku'),
            ],
            'bookreview': [
                ('book_id', 'id'),
                ('reviewer_id', 'user_id'),
            ],
            'agnews': [
                ('article', 'category'),
                ('title', 'article_title'),
            ],
        }
        
        if dataset not in mismatch_indicators:
            return False
        
        query_lower = query_text.lower()
        
        for indicators in mismatch_indicators[dataset]:
            if all(ind in query_lower for ind in indicators):
                return True
        
        return False
    
    def load_schema(self, dataset: str) -> str:
        """Load schema information from KB."""
        if dataset in self._schema_cache:
            return self._schema_cache[dataset]
        
        schema_path = f"{self.kb_path}/domain/schemas/{dataset}_schema.md"
        
        try:
            with open(schema_path, 'r') as f:
                schema = f.read()
                self._schema_cache[dataset] = schema
                return schema
        except FileNotFoundError:
            return f"Schema for {dataset} not found at {schema_path}"
    
    def load_join_glossary(self, dataset: str) -> str:
        """Load join key glossary for dataset."""
        cache_key = f"join_{dataset}"
        if cache_key in self._glossary_cache:
            return self._glossary_cache[cache_key]
        
        glossary_path = f"{self.kb_path}/domain/join_key_glossary.md"
        
        try:
            with open(glossary_path, 'r') as f:
                full_glossary = f.read()
                
                # Extract dataset-specific section
                pattern = rf'###+\s*{dataset.title()}.*?(?=###+|$)'
                match = re.search(pattern, full_glossary, re.DOTALL | re.IGNORECASE)
                
                if match:
                    glossary = match.group(0)
                else:
                    glossary = full_glossary
                
                self._glossary_cache[cache_key] = glossary
                return glossary
        except FileNotFoundError:
            return ""
    
    def load_domain_terms(self, terms: List[str]) -> str:
        """Load domain definitions for specific terms."""
        if not terms:
            return ""
        
        terms_key = ",".join(sorted(terms))
        if terms_key in self._terms_cache:
            return self._terms_cache[terms_key]
        
        terms_path = f"{self.kb_path}/domain/domain_terms.md"
        
        try:
            with open(terms_path, 'r') as f:
                full_terms = f.read()
                
                # Extract sections for requested terms
                relevant_sections = []
                for term in terms:
                    pattern = rf'###+\s*"{re.escape(term)}".*?(?=###+|$)'
                    match = re.search(pattern, full_terms, re.DOTALL | re.IGNORECASE)
                    if match:
                        relevant_sections.append(match.group(0))
                
                result = "\n\n".join(relevant_sections)
                self._terms_cache[terms_key] = result
                return result
        except FileNotFoundError:
            return ""
    
    def load_recent_corrections(self, limit: int = 3) -> str:
        """Load recent corrections from corrections log."""
        corrections_path = f"{self.kb_path}/corrections/CHANGELOG.md"
        
        try:
            with open(corrections_path, 'r') as f:
                content = f.read()
                
                # Extract most recent entries
                entries = re.findall(r'##\s*\[[\d-]+\].*?(?=##\s*\[|$)', content, re.DOTALL)
                
                if entries:
                    return "\n\n".join(entries[:limit])
                return ""
        except FileNotFoundError:
            return ""
    
    def build_context(
        self,
        dataset: str,
        query_text: str,
        pass_level: PassLevel,
        previous_result: Optional[PassResult] = None
    ) -> QueryContext:
        """
        Build context for a specific pass level.
        
        Args:
            dataset: Dataset name
            query_text: Natural language query
            pass_level: Current pass level
            previous_result: Result from previous pass (if any)
            
        Returns:
            Assembled QueryContext
        """
        context = QueryContext(
            dataset=dataset,
            query_text=query_text,
            pass_level=pass_level
        )
        
        # Pass 1: Schema only (always included)
        if pass_level.value >= PassLevel.SCHEMA_ONLY.value:
            context.schema_info = self.load_schema(dataset)
        
        # Pass 2: Add join key glossary if needed
        if pass_level.value >= PassLevel.JOIN_KEYS.value:
            if self.detect_cross_database(query_text, dataset):
                context.join_key_glossary = self.load_join_glossary(dataset)
            
            if self.detect_join_key_mismatch(query_text, dataset):
                if not context.join_key_glossary:
                    context.join_key_glossary = self.load_join_glossary(dataset)
        
        # Pass 3: Add domain terms if needed
        if pass_level.value >= PassLevel.DOMAIN_TERMS.value:
            ambiguous_terms = self.detect_semantic_ambiguity(query_text)
            if ambiguous_terms:
                context.domain_terms = self.load_domain_terms(ambiguous_terms)
        
        # Pass 4: Add corrections from previous failures
        if pass_level.value >= PassLevel.CORRECTIONS.value:
            context.corrections = self.load_recent_corrections()
            
            # Also include specific correction if previous pass failed
            if previous_result and not previous_result.success:
                # Search corrections for similar error
                error_type = previous_result.error_message
                if error_type:
                    context.corrections = f"**Previous Error:** {error_type}\n\n{context.corrections}"
        
        return context
    
    def should_continue(
        self,
        result: PassResult,
        max_passes: int
    ) -> Tuple[bool, Optional[PassLevel]]:
        """
        Determine if another pass should be attempted.
        
        Args:
            result: Current pass result
            max_passes: Maximum number of passes allowed
            
        Returns:
            (should_continue, next_pass_level)
        """
        # Stop if successful
        if result.success:
            return False, None
        
        # Stop if max passes reached
        if result.pass_level.value >= max_passes:
            return False, None
        
        # Determine next pass level
        current_level = result.pass_level
        
        if current_level == PassLevel.SCHEMA_ONLY:
            return True, PassLevel.JOIN_KEYS
        elif current_level == PassLevel.JOIN_KEYS:
            return True, PassLevel.DOMAIN_TERMS
        elif current_level == PassLevel.DOMAIN_TERMS:
            return True, PassLevel.CORRECTIONS
        else:
            return False, None
    
    def execute_with_agent(
        self,
        agent,  # Your agent instance
        dataset: str,
        query_text: str,
        max_passes: int = 3
    ) -> Tuple[Any, List[PassResult]]:
        """
        Execute query with progressive context enrichment.
        
        Args:
            agent: Data agent instance with a `run(query, context)` method
            dataset: Dataset name
            query_text: Natural language query
            max_passes: Maximum number of passes
            
        Returns:
            (final_answer, pass_history)
        """
        pass_history: List[PassResult] = []
        current_level = PassLevel.SCHEMA_ONLY
        
        while current_level.value <= max_passes:
            # Build context for this pass
            previous = pass_history[-1] if pass_history else None
            context = self.build_context(
                dataset, query_text, current_level, previous
            )
            
            # Execute query with agent
            try:
                # Assumes agent has a run method that accepts context
                answer, trace = agent.run(query_text, context.to_prompt())
                
                result = PassResult(
                    pass_level=current_level,
                    answer=answer,
                    success=True,
                    trace=trace,
                    context_used=context
                )
                pass_history.append(result)
                
                # Success! Return answer
                return answer, pass_history
                
            except Exception as e:
                error_msg = str(e)
                
                result = PassResult(
                    pass_level=current_level,
                    answer=None,
                    success=False,
                    error_message=error_msg,
                    context_used=context
                )
                pass_history.append(result)
                
                # Check if we should continue
                should_cont, next_level = self.should_continue(result, max_passes)
                
                if not should_cont:
                    # Return last error
                    raise Exception(f"Query failed after {current_level.value} passes: {error_msg}")
                
                current_level = next_level
        
        # Should not reach here
        raise Exception(f"Query failed after {max_passes} passes")


# Convenience function for simple usage
def iterative_query_refinement(
    agent,
    dataset: str,
    query_text: str,
    kb_path: str = "kb",
    max_passes: int = 3
) -> Tuple[Any, List[PassResult]]:
    """
    Execute query with progressive context enrichment.
    
    Args:
        agent: Data agent instance
        dataset: Dataset name (e.g., 'yelp', 'crmarenapro')
        query_text: Natural language query
        kb_path: Path to knowledge base
        max_passes: Maximum refinement passes
        
    Returns:
        (answer, pass_history)
    """
    retriever = MultiPassRetriever(kb_path)
    return retriever.execute_with_agent(agent, dataset, query_text, max_passes)