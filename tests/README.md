# SVG Processor Tests

This directory contains unit tests for the SVG Processor application.

## Structure

- `test_config_manager.py`: Tests for the ConfigManager class functionality
- `test_svg_processor.py`: Tests for SVG processing functionality
- `test_scada_export.py`: Tests for SCADA project export functionality
- `run_tests.py`: Script to run all tests

## Running Tests

### Running All Tests

To run all tests, use the `run_tests.py` script:

```bash
python run_tests.py
```

Or use the Python unittest discovery:

```bash
python -m unittest discover
```

### Running Specific Test Files

To run tests from a specific file:

```bash
python -m unittest test_config_manager.py
```

### Running with Coverage

To run tests with coverage reporting:

```bash
# Install coverage first
pip install -r ../test-requirements.txt

# Run tests with coverage
coverage run run_tests.py

# Generate a report
coverage report -m
```

## Test Dependencies

Make sure you have the required test dependencies installed:

```bash
pip install -r ../test-requirements.txt
```

## Writing New Tests

When adding new functionality to the application, please also add corresponding tests.
Follow these guidelines:

1. Create test methods with descriptive names that explain what they test
2. Use setup and teardown methods for common test initialization and cleanup
3. Mock external dependencies whenever possible
4. Test both successful execution and error handling cases
5. Keep tests isolated from each other 