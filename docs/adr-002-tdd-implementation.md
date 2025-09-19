# ADR-002: Test-Driven Development (TDD) Implementation

## Status
Accepted

## Context
The development policy (development-policy.mdc) mandates TDD as a core development practice. The current system lacks comprehensive test coverage, making it difficult to:

1. **Ensure Code Quality**: No automated verification of functionality
2. **Prevent Regressions**: Changes may break existing features
3. **Refactor Safely**: No safety net for architectural improvements
4. **Document Behavior**: Tests serve as living documentation

## Decision
We will implement a comprehensive TDD strategy following the development policy requirements:

### TDD Process

1. **Development Start**
   - 1.1 Write test code (unit/stub)
   - 1.2 Implement functionality
   - 1.3 Run tests
   - 1.4 Repeat until all tests pass

2. **Task Completion**
   - 2.1 Run all tests in the task scope
   - 2.2 Ensure 100% test pass rate
   - 2.3 Code review and merge

### Test Pyramid Structure

#### Unit Tests (80%+ Coverage Target)
- **Infrastructure Layer**: Logging, configuration, caching services
- **Data Layer**: Database repositories, ETL services
- **LLM Layer**: Text-to-SQL, report generation
- **Retrieval Layer**: RAG services, search functionality
- **Orchestration Layer**: Business logic, query processing
- **Presentation Layer**: UI components, state management

#### Integration Tests
- **ETL → MySQL**: Data pipeline integration
- **Text-to-SQL**: Natural language to SQL conversion
- **Hybrid Retrieval**: BM25 + Vector search integration
- **End-to-End**: Complete user workflows

#### Regression Tests
- **Critical Bug Cases**: Previously fixed issues
- **Performance Regression**: Response time monitoring
- **Security Regression**: SQL injection, prompt injection

### LLM-Specific Evaluation

#### Text-to-SQL Accuracy (≥90%)
- **Test Dataset**: 20 validation queries
- **Metrics**: Exact match, semantic equivalence
- **Automation**: Automated evaluation pipeline

#### RAG Evidence Citation (≥80%)
- **Metrics**: Source attribution accuracy
- **Validation**: Zero false source citations
- **Quality**: Relevance scoring

#### Performance Targets
- **Response Time**: P95 ≤ 3s (with caching)
- **Throughput**: Concurrent request handling
- **Resource Usage**: Memory and CPU monitoring

## Implementation Details

### Testing Framework
- **Primary**: pytest with pytest-cov for coverage
- **Mocking**: pytest-mock for dependency isolation
- **Type Checking**: mypy for static analysis
- **Code Quality**: black, flake8, isort

### Test Structure
```
tests/
├── unit/
│   ├── test_infrastructure.py
│   ├── test_data_layer.py
│   ├── test_llm_layer.py
│   ├── test_retrieval_layer.py
│   ├── test_orchestration_layer.py
│   └── test_presentation_layer.py
├── integration/
│   ├── test_etl_pipeline.py
│   ├── test_text_to_sql.py
│   ├── test_rag_pipeline.py
│   └── test_end_to_end.py
├── regression/
│   ├── test_critical_bugs.py
│   ├── test_performance.py
│   └── test_security.py
└── fixtures/
    ├── sample_data.py
    ├── mock_services.py
    └── test_config.py
```

### Continuous Integration
- **Pre-commit Hooks**: Run tests before commits
- **Pull Request**: Require 100% test pass
- **Coverage Gate**: Minimum 80% coverage
- **Performance Gate**: P95 ≤ 3s response time

## Consequences

### Positive
- **Higher Code Quality**: Automated verification of functionality
- **Reduced Bugs**: Early detection of issues
- **Safe Refactoring**: Confidence in code changes
- **Living Documentation**: Tests explain system behavior
- **Faster Development**: Immediate feedback on changes

### Negative
- **Initial Overhead**: More time for test writing
- **Maintenance Cost**: Tests need updates with code changes
- **Learning Curve**: Team needs TDD skills
- **Complexity**: More files and test infrastructure

### Risks
- **Test Brittleness**: Tests may break with minor changes
- **False Confidence**: 100% coverage doesn't guarantee correctness
- **Over-testing**: Testing implementation details instead of behavior
- **Performance Impact**: Test execution time

## Success Metrics

### Coverage Targets
- **Unit Tests**: 80%+ line coverage
- **Integration Tests**: Critical path coverage
- **Regression Tests**: 100% critical bug coverage

### Quality Metrics
- **Test Pass Rate**: 100% for all commits
- **Test Execution Time**: <5 minutes for full suite
- **Flaky Test Rate**: <1% of tests

### LLM Evaluation
- **Text-to-SQL Accuracy**: ≥90% on validation set
- **RAG Citation Rate**: ≥80% with zero false citations
- **Response Time**: P95 ≤ 3s with caching

## Implementation Timeline

### Phase 1: Infrastructure Testing (Week 1)
- [x] Set up testing framework
- [x] Implement infrastructure layer tests
- [x] Achieve 80%+ coverage for infrastructure

### Phase 2: Data Layer Testing (Week 2)
- [x] Implement data layer tests
- [x] Add integration tests for ETL pipeline
- [x] Achieve 80%+ coverage for data layer

### Phase 3: LLM Layer Testing (Week 3)
- [ ] Implement LLM layer tests
- [ ] Add Text-to-SQL evaluation suite
- [ ] Achieve 80%+ coverage for LLM layer

### Phase 4: End-to-End Testing (Week 4)
- [ ] Implement integration tests
- [ ] Add regression test suite
- [ ] Achieve overall 80%+ coverage

## References

- [Test-Driven Development by Example - Kent Beck](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [The Art of Unit Testing - Roy Osherove](https://www.artofunittesting.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Clean Code - Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
