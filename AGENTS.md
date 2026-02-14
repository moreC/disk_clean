# AGENTS.md - Coding Guidelines for Disk Cleaner Project

## Build / Lint / Test Commands

Since this project doesn't have formal test/lint tooling configured yet, use these standard Python commands:

```bash
# Run a Python script
python disk_checker.py

# Run with arguments
python disk_cleaner.py --min-size 50

# Run a single test (when tests exist)
python -m pytest tests/test_disk_cleaner.py::TestClass::test_method -v

# Run all tests (when tests exist)
python -m pytest tests/ -v

# Check code style
python -m flake8 *.py
python -m pylint *.py

# Format code
python -m black *.py

# Type check
python -m mypy *.py
```

## Code Style Guidelines

### File Structure
- Always include shebang: `#!/usr/bin/env python3`
- Always include encoding: `# -*- coding: utf-8 -*-`
- Imports: standard library first, no wildcard imports

### Naming Conventions
- **Classes**: PascalCase (e.g., `DiskCleanerTree`, `CleanupPlanner`)
- **Methods/Functions**: snake_case (e.g., `get_dir_size`, `should_exclude`)
- **Variables**: snake_case (e.g., `total_size`, `exclude_dirs`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_DEPTH`, `DEFAULT_SIZE`)
- **Private methods**: prefix with underscore (e.g., `_helper_method`)

### Formatting
- Indentation: 4 spaces (no tabs)
- Line length: 100 characters max
- Use f-strings for formatting: `f"Size: {size:.2f} MB"`
- Docstrings: Use triple quotes in Chinese for user-facing tools

### Error Handling
- Use specific exceptions, avoid bare `except:`
- Always log or print error messages
- Handle Windows permission errors gracefully

```python
try:
    result = subprocess.run(command, capture_output=True, text=True)
except subprocess.SubprocessError as e:
    print(f"Command failed: {e}")
    return False
```

### Type Hints (Recommended)
Add type hints for new code:

```python
def get_dir_size(self, path: str) -> int:
    """计算目录大小"""
    total: int = 0
    ...
```

### Project Patterns
- Classes encapsulate functionality (e.g., `DiskCleaner`, `DiskChecker`)
- Use `os.path.join()` and `os.path.expanduser()` for paths
- Store data in `data/` directory, logs in `logs/` directory
- Use `os.makedirs(path, exist_ok=True)` for directory creation

## Windows-Specific Notes
- Paths use Windows format: `'C:\\Windows'`
- Use `schtasks` for scheduled tasks
- Handle permission errors on system directories gracefully
- Test on Windows environment

## Adding New Features
1. Create a new class or add methods to existing classes
2. Update README定时任务.md with usage instructions
3. Add command-line interface using `argparse`
4. Follow existing code patterns and Chinese comments style

## Dependencies
This project uses only Python standard library:
- os, sys, json, time, argparse, subprocess
- datetime, shutil, zipfile
- No external packages required
