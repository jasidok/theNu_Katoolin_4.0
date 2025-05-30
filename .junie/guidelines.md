# Katoolin Development Guidelines

This document provides guidelines and information for developers working on the Katoolin project.

## Build/Configuration Instructions

### Prerequisites

- Python 3.10 or higher
- Ubuntu or Debian-based system (for full functionality)
- Root privileges (sudo access)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/0xGuigui/Katoolin3.git
   cd Katoolin3
   ```

2. Make the script executable:
   ```bash
   chmod +x katoolin3.py
   ```

3. Run the script with sudo:
   ```bash
   sudo ./katoolin3.py
   ```

### Project Structure

- `katoolin3.py`: Main script that provides the user interface
- `core/`: Directory containing core functionality
  - `__init__.py`: Python package initialization
  - `categories.py`: Contains the dictionary of tool categories and tools
  - `gear.py`: Contains utility functions for the main script

## Testing Information

### Setting Up the Testing Environment

1. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install testing dependencies:
   ```bash
   pip install pytest
   ```

### Running Tests

The project uses Python's unittest framework for testing. Tests are located in the `tests/` directory.

To run all tests:
```bash
python -m unittest discover tests
```

To run a specific test:
```bash
python tests/test_categories.py
```

### Adding New Tests

1. Create a new test file in the `tests/` directory with a name starting with `test_`.
2. Import the necessary modules and the code you want to test.
3. Create a class that inherits from `unittest.TestCase`.
4. Add test methods that start with `test_`.
5. Use assertions to verify expected behavior.

Example:
```python
#!/usr/bin/env python3

import unittest
import sys
import os

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.gear import format

class TestGear(unittest.TestCase):
    def test_format(self):
        """Test the format function in gear.py"""
        self.assertEqual(format("test_string"), "Test String")
        self.assertEqual(format("another_test"), "Another Test")

if __name__ == '__main__':
    unittest.main()
```

### Test Examples

The repository includes sample tests to demonstrate how testing works in this project:

1. `tests/test_categories.py` - Verifies the structure and content of the categories dictionary:
   ```bash
   ./tests/test_categories.py
   ```

2. `tests/test_simple.py` - A simple test that demonstrates basic unittest functionality:
   ```bash
   ./tests/test_simple.py
   ```

## Additional Development Information

### Code Style

- Follow PEP 8 guidelines for Python code.
- Use 4 spaces for indentation (not tabs).
- Keep line length to a maximum of 79 characters.
- Use meaningful variable and function names.

### Git Workflow

1. Create a new branch for each feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them with descriptive commit messages:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

3. Push your branch to the remote repository:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request for review.

### Debugging

- The script uses print statements for output.
- For debugging, you can add additional print statements with the `red`, `green`, `yellow`, or `cyan` color variables for better visibility.
- Example:
  ```python
  print(red + "Error: Something went wrong" + reset)
  ```

### Known Issues and Limitations

1. The script requires root privileges to run.
2. Some tools may be outdated or no longer available in the Kali repositories.
3. Adding Kali repositories to a non-Kali system can potentially cause system instability.

### Future Development

Refer to the `todo.md` file for planned features and improvements, including:
- Creating an install.sh script with various checks
- Updating the script to be compatible with more Linux distributions
- Fixing GPG key errors
