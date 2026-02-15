# Unit Tests for JAV.bundle

This directory contains unit tests for all JAV.bundle agents.

## Setup

### Prerequisites
- Python 2.7 (same as Plex agent runtime)
- pip

### Installation

1. Install test dependencies:
```bash
pip install -r requirements_test.txt
```

## Running Tests

### Command Line

Run all tests:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Run a specific test file:
```bash
python -m unittest tests.test_javdb
```

Run a specific test class:
```bash
python -m unittest tests.test_javdb.TestJavDBQuery
```

Run a specific test method:
```bash
python -m unittest tests.test_javdb.TestJavDBQuery.test_query
```

### With Coverage

Run tests with coverage report:
```bash
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```

Generate HTML coverage report:
```bash
coverage html
```

### VS Code

The project is configured to use VS Code's Python testing features:

1. Open the Testing panel (flask icon in the sidebar)
2. Tests will be automatically discovered
3. Click the play button to run tests
4. Click the debug icon to debug tests

You can also use the launch configurations:
- **Python: All Tests** - Run all tests
- **Python: Current Test File** - Run the currently open test file
- **Python: Specific Test** - Run a specific test (edit the test name in launch.json)

## Test Structure

### Base Classes

- `BaseAgentTest`: Base class for all agent tests
- `QueryAgentTest`: Base class for testing query functionality
- `MetadataAgentTest`: Base class for testing metadata retrieval

### Test Files

Each agent has its own test file:

- `test_ave.py` - AVEntertainments agent
- `test_caribbean.py` - Caribbean agent
- `test_caribpr.py` - CaribbeanPr agent
- `test_fc2.py` - FC2 agent
- `test_heyzo.py` - Heyzo agent
- `test_javdb.py` - JavDB agent (CloudFlare protected)
- `test_javlibrary.py` - JAVLibrary agent (CloudFlare protected)
- `test_pondo.py` - Pondo agent
- `test_tokyohot.py` - TokyoHot agent
- `test_waap.py` - Waap agent

### Mock Files

CloudFlare-protected sites use mock HTML responses stored in `tests/mocks/`:

- `javdb_query.html` - JavDB search results
- `javdb_metadata.html` - JavDB movie details
- `javlibrary_query.html` - JAVLibrary search results
- `javlibrary_metadata.html` - JAVLibrary movie details

## Adding Test Cases

### For QueryAgent

Edit the `test_cases` list in the appropriate test file:

```python
test_cases = [
    ("KEYWORD", {
        'name': 'Expected Title Substring',
        'year': 2020,
        'score_min': 90
    }),
]
```

### For MetadataAgent

Edit the `test_cases` list in the appropriate test file:

```python
test_cases = [
    ("AGENT_ID", {
        'title': 'Expected Full Title',
        'studio': 'Studio Name',
        'genres': ['Genre1', 'Genre2'],
    }),
]
```

### For CloudFlare-Protected Sites

1. Manually retrieve the HTML response from the website
2. Save it to the appropriate mock file in `tests/mocks/`
3. Add your test cases to the test file

## Continuous Integration

Tests automatically run on every push via GitHub Actions. See `.github/workflows/test.yml` for configuration.

## Troubleshooting

### Import Errors

If you encounter import errors, ensure:
- The `Contents/Libraries/Shared` directory is in your Python path
- All required dependencies are installed

### CloudFlare Tests Failing

If CloudFlare-protected tests fail:
1. Ensure the mock HTML files in `tests/mocks/` are populated with actual response data
2. Verify the HTML structure matches what the agent expects
3. Check that the mock session is properly set up in the test's `setUp` method

### Python 2.7 Compatibility

All code must be compatible with Python 2.7:
- Use `from __future__ import` for Python 3 features
- Use `mock` library instead of `unittest.mock`
- Use `unicode` strings where necessary
- Use `__builtin__` instead of `builtins`
