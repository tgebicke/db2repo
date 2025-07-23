# DB2Repo

Database DDL to Git Repository Tool

A command-line interface tool for tracking database DDL (Data Definition Language) in a git repository. Supports multiple database platforms with an extensible adapter pattern, starting with Snowflake.

## Features

- **Multi-Platform Support**: Extensible adapter pattern for different database platforms
- **Profile Management**: AWS-style profile system for multiple database connections
- **Git Integration**: Seamless version control for database schema changes
- **DDL Extraction**: Extract and format DDL for various database objects
- **Modern CLI**: Beautiful terminal interface with rich output

## Installation

### Prerequisites

- Python 3.8 or higher
- Poetry (for development)
- mise (for tool version management)

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd db2repo
```

2. Install tools with mise:
```bash
mise install
```

3. Install dependencies with Poetry:
```bash
poetry install
```

4. Activate the virtual environment:
```bash
poetry shell
```

## Usage

```bash
# Show help
db2repo --help

# Show version
db2repo version
```

## Development

### Project Structure

```
db2repo/
├── pyproject.toml              # Poetry configuration
├── .mise.toml                 # mise tool configuration
├── README.md                  # This file
├── db2repo/                   # Main package
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point
│   ├── config.py              # Configuration management
│   ├── adapters/              # Database adapters
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract base adapter
│   │   └── snowflake.py       # Snowflake adapter
│   ├── git/                   # Git operations
│   │   ├── __init__.py
│   │   └── manager.py         # Git management
│   ├── utils/                 # Utilities
│   │   ├── __init__.py
│   │   ├── ddl_formatter.py   # DDL formatting
│   │   └── validators.py      # Input validation
│   └── exceptions.py          # Custom exceptions
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_cli.py
    ├── test_config.py
    ├── test_snowflake_adapter.py
    └── test_git_manager.py
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=db2repo

# Run specific test file
poetry run pytest tests/test_cli.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run flake8

# Type checking
poetry run mypy db2repo/
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## Roadmap

- [ ] Snowflake database adapter
- [ ] PostgreSQL database adapter
- [ ] MySQL database adapter
- [ ] Advanced git integration
- [ ] Web interface
- [ ] CI/CD pipeline integration 