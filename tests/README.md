# Unit Tests for OpenLens AI Agents

This directory contains unit tests for the OpenLens AI agents.

## Structure

- `utils/` - Utility functions for testing
  - `test_setup.py` - Functions to set up and clean up test environments
- `unit/` - Unit test files for each agent
  - `test_artifact_publisher.py` - Tests for artifact_publisher.py
  - `test_coder.py` - Tests for coder.py
  - `test_data_analyzer.py` - Tests for data_analyzer.py
  - `test_latex_writer.py` - Tests for latex_writer.py
  - `test_literature_reviewer.py` - Tests for literature_reviewer.py
  - `test_supervisor.py` - Tests for supervisor.py
- `run_all_tests.py` - Script to run all unit tests

## Usage

### Running All Tests

To run all unit tests:

```bash
cd tests
python run_all_tests.py
```

### Running Individual Tests

To run a specific test file:

```bash
cd tests
python -m unittest unit.test_artifact_publisher
```

Or:

```bash
cd tests
python unit/test_artifact_publisher.py
```

## Test Design

The tests are designed to:

1. **Set up isolated test environments** - Each test creates a temporary copy of the test project with unique configuration
2. **Test graph building** - Verify that each agent's graph can be built successfully
3. **Test main function simulation** - Simulate the behavior of the `if __name__ == "__main__"` blocks
4. **Preserve test artifacts** - Test environments are preserved after test completion for inspection

## Test Environment Setup

The `setup_test_environment()` function in `utils/test_setup.py`:

1. Creates a unique test directory in `outputs/tests/`
2. Copies the test project from `tests/test_proj/`
3. Modifies the configuration file with test-specific settings
4. Returns the paths to the test project and config file

Each test uses this function to create an isolated environment that doesn't interfere with other tests or the main project.

## Mocking

The tests use Python's `unittest.mock` module to mock external dependencies like:

- Language model calls
- File system operations
- Network requests
- External APIs

This allows the tests to focus on the core logic of each agent without depending on external services.

## Notes

- All tests use English comments and documentation
- Tests focus on overall functionality rather than individual node testing
- Each test is self-contained and can be run independently
- Tests preserve artifacts for inspection rather than cleaning up automatically