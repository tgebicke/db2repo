# DB2Repo CLI Application Specification

## Project Overview

**Purpose:** A command-line interface (CLI) tool for tracking database DDL (Data Definition Language) in a git repository. The tool will be platform-agnostic with adapters for different database systems, starting with Snowflake.

**Target Users:** Database developers and administrators who need to version control their database schema changes.

**Application Type:** CLI application written in Python, packaged for easy installation and distribution.

## Core Functionality

### Primary Features
1. **Database Connection Management** - Connect to database instances using various authentication methods
2. **DDL Extraction** - Retrieve DDL statements for database objects
3. **Repository Management** - Organize and store DDL files in a structured git repository
4. **Change Tracking** - Detect and track changes between database and repository
5. **Git Integration** - Automatically commit changes to git repository

### Supported Database Objects (MVP)
- Tables
- Views
- Materialized Views
- Stages
- Snow Pipes
- Stored Procedures

### Future Scope
- All database objects (extensible architecture)
- Additional database platforms (PostgreSQL, MySQL, SQL Server, Oracle, etc.)

## Technical Architecture

### Technology Stack
- **Language:** Python 3.8+
- **CLI Framework:** Click or Typer for command-line interface
- **Configuration:** TOML parsing with `toml` library
- **Database Connections:** Platform-specific drivers (snowflake-connector-python for Snowflake)
- **Git Integration:** GitPython or subprocess calls to git commands
- **Dependency Management:** Poetry for Python package management
- **Project Configuration:** mise for tool version management and project settings
- **Packaging:** Poetry for building and publishing packages

### Adapter Pattern
The application will use an adapter pattern to support multiple database platforms:
- **Core Interface** - Abstract base class that all database adapters must implement
- **Snowflake Adapter** - First implementation for Snowflake database
- **Extensible Design** - Easy addition of new database platform adapters

### Configuration Management
- **Format:** TOML configuration file
- **Location:** User home directory (`~/.db2repo.toml`)
- **Scope:** Global profiles (project-specific profiles in future roadmap)

### Python Project Structure
```
db2repo/
├── pyproject.toml              # Poetry configuration and dependencies
├── .mise.toml                 # mise tool configuration
├── README.md                   # Project documentation
├── db2repo/
│   ├── __init__.py
│   ├── cli.py                  # Main CLI entry point
│   ├── config.py               # Configuration management
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract base adapter class
│   │   └── snowflake.py        # Snowflake adapter implementation
│   ├── git/
│   │   ├── __init__.py
│   │   └── manager.py          # Git operations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── ddl_formatter.py    # DDL formatting utilities
│   │   └── validators.py       # Input validation
│   └── exceptions.py           # Custom exceptions
└── tests/
    ├── __init__.py
    ├── test_cli.py
    ├── test_config.py
    ├── test_snowflake_adapter.py
    └── test_git_manager.py
```

### Profile System (AWS-style)
```toml
active_profile = "dev"

[default]
platform = "snowflake"
account = "your-account.snowflakecomputing.com"
username = "your-username"
password = "your-password"
warehouse = "your-warehouse"
database = "your-database"
schema = "your-schema"
role = "your-role"
auth_method = "username_password"
git_repo_path = "/path/to/your/ddl-repository"
git_remote_url = "https://github.com/your-org/ddl-repository.git"
git_branch = "main"
git_author_name = "Your Name"
git_author_email = "your.email@company.com"

[dev]
platform = "snowflake"
account = "dev-account.snowflakecomputing.com"
username = "dev-user"
password = "dev-password"
warehouse = "dev-warehouse"
database = "dev-database"
schema = "dev-schema"
role = "dev-role"
auth_method = "username_password"
git_repo_path = "/path/to/dev-ddl-repo"
git_remote_url = "https://github.com/your-org/dev-ddl-repo.git"
git_branch = "develop"
git_author_name = "Dev User"
git_author_email = "dev@company.com"

[prod]
platform = "snowflake"
account = "prod-account.snowflakecomputing.com"
username = "prod-user"
private_key_path = "~/.ssh/snowflake_key"
warehouse = "prod-warehouse"
database = "prod-database"
schema = "prod-schema"
role = "prod-role"
auth_method = "ssh_key"
git_repo_path = "/path/to/prod-ddl-repo"
git_remote_url = "https://github.com/your-org/prod-ddl-repo.git"
git_branch = "main"
git_author_name = "Prod User"
git_author_email = "prod@company.com"
```

### Authentication Methods (MVP)
1. **Username/Password** - Basic authentication
2. **SSH Key** - Private key authentication
3. **External Browser** - Browser-based authentication
4. **OAuth** - Future roadmap item

### Setup Process
The `db2repo setup` command will guide users through an interactive process to configure:

1. **Profile Information**
   - Profile name (default, dev, prod, etc.)
   - Platform selection (snowflake, postgresql, etc.)

2. **Database Connection**
   - Account/connection details
   - Authentication method and credentials
   - Database, schema, warehouse, and role settings

3. **Git Repository Configuration**
   - Local repository path
   - Remote repository URL
   - Default branch name
   - Git author name and email
   - Option to initialize git repository if it doesn't exist

4. **Validation**
   - Test database connection
   - Verify git repository access
   - Confirm configuration settings

## Command Structure

### Profile Management Commands
```bash
db2repo profiles                    # List all configured profiles
db2repo setup                      # Interactive setup for a profile
db2repo setup --profile dev        # Setup specific profile
db2repo use-profile dev            # Set active profile
```

### Main Operation Commands
```bash
db2repo sync                       # Sync using active profile
db2repo sync --profile dev         # Sync using specific profile
db2repo sync --commit              # Sync and auto-commit changes
db2repo sync --dry-run             # Preview changes without applying
db2repo status                     # Show what would be updated
db2repo diff                       # Show differences between repo and database
```

### Git Repository Management
```bash
db2repo init-repo                  # Initialize git repository for current profile
db2repo init-repo --profile dev    # Initialize git repository for specific profile
db2repo push                       # Push changes to remote repository
db2repo pull                       # Pull latest changes from remote repository
```

### Global Flags
- `--profile <name>` - Specify profile to use
- `--commit` or `-c` - Auto-commit changes to git
- `--dry-run` - Preview changes without applying
- `--verbose` or `-v` - Detailed output
- `--quiet` or `-q` - Minimal output

## File Organization Structure

### Repository Structure
```
database_name/
├── schema_name/
│   ├── tables/
│   │   ├── table1.sql
│   │   └── table2.sql
│   ├── views/
│   │   ├── view1.sql
│   │   └── view2.sql
│   ├── materialized_views/
│   │   └── mview1.sql
│   ├── stages/
│   │   └── stage1.sql
│   ├── snowpipes/
│   │   └── pipe1.sql
│   └── stored_procedures/
│       └── proc1.sql
```

### DDL File Format
- **File Extension:** `.sql`
- **Content:** Full DDL statements with all object properties
- **Format:** Standardized formatting for consistency
- **Comments:** Include object comments and metadata where available

## Snowflake-Specific Implementation

### Connection Parameters
- Account URL
- Username
- Password/Private Key
- Warehouse
- Database
- Schema
- Role
- Authentication Method

### DDL Extraction Strategy
- Use Snowflake's `SHOW CREATE` commands for each object type
- Handle Snowflake-specific features (clustering, time travel, etc.)
- Preserve original DDL formatting where possible
- Include grants and permissions where accessible
- Special handling for stored procedures to de-stringify content

### Stored Procedure Implementation Details
**Problem:** Snowflake's `SHOW CREATE PROCEDURE` returns stringified content:
```sql
CREATE OR REPLACE PROCEDURE test_proc()
RETURNS STRING
LANGUAGE SQL
AS 'BEGIN\n  RETURN ''Hello World'';\nEND;'
```

**Solution:** Reconstruct readable DDL by:
1. **Get Procedure Metadata:**
   ```sql
   SELECT PROCEDURE_NAME, PROCEDURE_SCHEMA, PROCEDURE_CATALOG, 
          ARGUMENT_SIGNATURE, RESULT_TYPE, PROCEDURE_DEFINITION
   FROM INFORMATION_SCHEMA.PROCEDURES 
   WHERE PROCEDURE_SCHEMA = 'SCHEMA_NAME' 
   AND PROCEDURE_NAME = 'PROCEDURE_NAME';
   ```

2. **Get Procedure Signature:**
   ```sql
   DESC PROCEDURE schema_name.procedure_name;
   ```

3. **Reconstruct DDL:** Combine signature information with un-stringified body from `INFORMATION_SCHEMA.PROCEDURES`

**Alternative:** Use existing de-stringification stored procedure if available in the target database.

### Object Type Handling
1. **Tables** - `SHOW CREATE TABLE`
2. **Views** - `SHOW CREATE VIEW`
3. **Materialized Views** - `SHOW CREATE MATERIALIZED VIEW`
4. **Stages** - `SHOW CREATE STAGE`
5. **Snow Pipes** - `SHOW CREATE PIPE`
6. **Stored Procedures** - Special handling required for de-stringification

### Stored Procedure DDL Extraction
Snowflake stores stored procedures with stringified content (single quotes around the procedure body), making them unreadable. The tool will implement a de-stringification process:

1. **Extract Procedure Header** - Use `SHOW CREATE PROCEDURE` or `DESC PROCEDURE` to get the procedure signature
2. **Extract Procedure Body** - Query `INFORMATION_SCHEMA.PROCEDURES` to get the un-stringified procedure body
3. **Reconstruct DDL** - Combine header and body to create readable DDL
4. **Format Output** - Apply consistent formatting for readability

**Implementation Options:**
- Use existing stored procedure for de-stringification (if available)
- Implement custom SQL query to reconstruct procedure DDL
- Combine multiple Snowflake commands to build complete procedure definition

**Expected Output Format:**
```sql
CREATE OR REPLACE PROCEDURE schema_name.procedure_name(
    param1 STRING,
    param2 NUMBER
)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Procedure body without stringification
    RETURN 'Hello World';
END;
$$;
```

## Error Handling & Validation

### Connection Errors
- Invalid credentials
- Network connectivity issues
- Insufficient permissions
- Account/warehouse not found

### DDL Extraction Errors
- Object not found
- Permission denied
- Invalid object state
- Dependency issues
- Stored procedure de-stringification failures
- Information schema access issues

### Repository Errors
- Git not initialized
- Uncommitted changes
- Merge conflicts
- File permission issues
- Invalid repository path
- Remote repository access issues
- Branch not found
- Git authentication failures

### User Experience
- Clear error messages with actionable guidance
- Graceful degradation when possible
- Detailed logging in verbose mode
- Progress indicators for long operations

## Security Considerations

### Credential Storage
- Plain text storage in config file (AWS-style)
- Config file permissions should be restricted (600)
- Consider encrypted storage in future versions

### Authentication
- Support for multiple authentication methods
- Secure handling of credentials in memory
- No credential logging in any mode

### Network Security
- TLS/SSL for all database connections
- Certificate validation
- Connection timeout handling

## Performance Requirements

### Scalability
- Handle large numbers of database objects efficiently
- Support for databases with thousands of objects
- Memory-efficient processing for large DDL statements

### Speed
- Fast connection establishment
- Efficient DDL extraction
- Quick change detection
- Minimal overhead for git operations

## Future Roadmap

### Phase 2 Features
- OAuth authentication support
- Project-specific configuration files
- Additional database platform adapters
- Webhook integration for automated syncing
- Change notification system

### Phase 3 Features
- Schema migration generation
- Rollback capabilities
- Team collaboration features
- Integration with CI/CD pipelines
- Advanced reporting and analytics

## Development Guidelines

### Code Quality
- Comprehensive test coverage
- Clear documentation
- Consistent error handling
- Logging for debugging

### Python Packaging & Distribution with Poetry & mise

**Poetry Configuration (`pyproject.toml`):**
```toml
[tool.poetry]
name = "db2repo"
version = "0.1.0"
description = "Database DDL to Git Repository Tool"
authors = ["Your Name <your.email@company.com>"]
readme = "README.md"
packages = [{include = "db2repo"}]

[tool.poetry.dependencies]
python = "^3.8"
click = "^8.0.0"
toml = "^0.10.0"
snowflake-connector-python = "^3.0.0"
gitpython = "^3.1.0"
rich = "^12.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
black = "^22.0.0"
flake8 = "^4.0.0"
mypy = "^0.950"
pre-commit = "^2.20.0"
pytest-cov = "^4.0.0"

[tool.poetry.scripts]
db2repo = "db2repo.cli:cli"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**mise Configuration (`.mise.toml`):**
```toml
[tools]
python = "3.11"
poetry = "1.7.0"

[env]
PYTHONPATH = "{root}/db2repo"
```

**Installation Methods:**
```bash
# Install from PyPI (when published)
pip install db2repo

# Install from local development with Poetry
poetry install

# Install from git repository
pip install git+https://github.com/your-org/db2repo.git

# Development setup with mise
mise install
mise run poetry install
```

**Development Workflow:**
```bash
# Activate virtual environment
poetry shell

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run flake8

# Type checking
poetry run mypy db2repo/

# Build package
poetry build

# Publish to PyPI
poetry publish
```

### User Experience
- Intuitive command structure
- Helpful error messages
- Progress indicators
- Clear documentation

### Extensibility
- Clean separation of concerns
- Well-defined interfaces
- Easy addition of new database adapters
- Plugin architecture for future features

### Python Implementation Details
**Adapter Base Class:**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DatabaseAdapter(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[Dict[str, Any]]:
        """Retrieve table DDL"""
        pass
    
    @abstractmethod
    def get_views(self) -> List[Dict[str, Any]]:
        """Retrieve view DDL"""
        pass
    
    @abstractmethod
    def get_stored_procedures(self) -> List[Dict[str, Any]]:
        """Retrieve stored procedure DDL"""
        pass
```

**CLI Structure with Click:**
```python
import click

@click.group()
def cli():
    """DB2Repo - Database DDL to Git Repository Tool"""
    pass

@cli.command()
@click.option('--profile', help='Profile name to setup')
def setup(profile):
    """Interactive setup for database profile"""
    pass

@cli.command()
@click.option('--profile', help='Profile to use')
@click.option('--commit', is_flag=True, help='Auto-commit changes')
def sync(profile, commit):
    """Sync database DDL to repository"""
    pass
```

## Success Criteria

### MVP Success Metrics
- Successfully connect to Snowflake databases
- Extract DDL for all specified object types
- Organize files in specified directory structure
- Integrate with git for version control
- Support multiple profiles and authentication methods
- Handle errors gracefully with clear messaging

### User Acceptance Criteria
- Database developers can easily set up and use the tool
- DDL changes are accurately tracked in git
- Tool works reliably across different Snowflake environments
- Configuration is intuitive and follows familiar patterns
- Error messages are clear and actionable
