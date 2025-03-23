# PydanticPrompt

A simple library to document [Pydantic](https://docs.pydantic.dev/) models for structured LLM outputs using standard Python docstrings.

## Installation

```bash
pip install pydantic-prompt
```

## Features

- Document Pydantic model fields using standard Python docstrings
- Format field documentation for LLM prompts with a single method call
- Automatic type inference and display
- Optional validation rule documentation
- Warnings for undocumented fields
- Seamlessly embeds documentation in your prompts

## Usage

### Basic Example

```python
from pydantic import BaseModel, Field
from typing import Optional
from pydantic_prompt import prompt_schema

@prompt_schema
class Person(BaseModel):
    name: str
    """The person's full name"""
    
    age: int = Field(ge=0)
    """Age in years"""
    
    email: Optional[str] = None
    """Contact email address if available"""

# Use in LLM prompt
prompt = f"""
Please extract a Person object from this text according to the schema below:

{Person.format_for_llm()}

Input: Jane Smith, 28, works at Acme Corp.
"""
```

### Output

The `format_for_llm()` method produces output like:

```
Person:
- name (str): The person's full name
- age (int): Age in years
- email (str, optional): Contact email address if available
```

### Working with Nested Models

```python
from pydantic import BaseModel
from pydantic_prompt import prompt_schema
from typing import list

@prompt_schema
class Address(BaseModel):
    street: str
    """Street name and number"""
    
    city: str
    """City name"""
    
    postal_code: str
    """Postal or ZIP code"""

@prompt_schema
class Contact(BaseModel):
    name: str
    """Full name of the contact"""
    
    addresses: list[Address] = []
    """List of addresses associated with this contact"""

# The format_for_llm method will nicely format nested structures too
print(Contact.format_for_llm())
```

### Including Validation Rules

You can include validation rules in the output:

```python
Person.format_for_llm(include_validation=True)
```

Output:

```
Person:
- name (str): The person's full name
- age (int): Age in years [Constraints: ge: 0]
- email (str, optional): Contact email address if available
```

### Warnings for Undocumented Fields

By default, PydanticPrompt warns you when fields don't have docstrings:

```python
@prompt_schema
class PartiallyDocumented(BaseModel):
    name: str
    """This field has a docstring"""
    
    age: int
    # Missing docstring will generate a warning
```

Output:
```
UserWarning: Field 'age' in PartiallyDocumented has no docstring. Add a docstring for better LLM prompts.
```

To disable these warnings:

```python
@prompt_schema(warn_undocumented=False)
class SilentModel(BaseModel):
    name: str
    # No warning for missing docstring
```

## Real-World Example

```python
from pydantic import BaseModel, Field
from pydantic_prompt import prompt_schema
from typing import list

@prompt_schema
class ProductReview(BaseModel):
    product_name: str
    """The exact name of the product being reviewed"""
    
    rating: int = Field(ge=1, le=5)
    """Rating from 1 to 5 stars, where 5 is best"""
    
    pros: list[str]
    """List of positive aspects mentioned about the product"""
    
    cons: list[str]
    """List of negative aspects mentioned about the product"""
    
    summary: str
    """A brief one-sentence summary of the overall review"""

# In your LLM prompt
prompt = f"""
Extract a structured product review from the following text.
Return the data according to this schema:

{ProductReview.format_for_llm(include_validation=True)}

Review text:
I recently purchased the UltraBook Pro X1 and I've been using it for about two weeks.
The screen is absolutely gorgeous and the battery lasts all day which is fantastic.
However, the keyboard feels a bit mushy and it runs hot when doing anything intensive.
Overall, a solid laptop with a few minor issues that don't detract from the experience.
"""
```

## How It Works

PydanticPrompt uses Python's introspection capabilities to:

1. Capture docstrings defined after field declarations
2. Extract type information from type hints
3. Identify optional fields
4. Format everything in a clear, LLM-friendly format

The library is designed to be lightweight and focused on a single task: making it easy to document your data models for LLMs in a way that both developers and AI can understand.

## Why Use PydanticPrompt?

- **Consistency**: Document your models once, use everywhere
- **DRY Principle**: No need to duplicate field descriptions between code and prompts
- **Developer-Friendly**: Uses standard Python docstrings
- **LLM-Friendly**: Produces clear, structured documentation that LLMs can easily understand
- **Maintainability**: When your models change, your prompt documentation automatically updates

## Development

### Setting up the development environment

Clone the repository:

```bash
git clone https://github.com/OpenAdaptAI/PydanticPrompt.git
cd PydanticPrompt
```

Create and activate a virtual environment with `uv`:

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

Install the package in development mode:

```bash
# Install the package
uv pip install -e .
```

Install development dependencies:

```bash
# Install dev dependencies
uv pip install -e ".[dev]"
```

### Note about hardlinking warning

If you see a warning about hardlinking when installing:

```
warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
```

This is normal when the cache and target directories are on different filesystems. You can suppress this warning with:

```bash
export UV_LINK_MODE=copy
```

### Running tests

Make sure your virtual environment is activated, then run:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage information
pytest --cov=pydantic_prompt
```

### Code formatting and linting

You can run all formatting and linting checks with:

```bash
# Run all linting and formatting 
./lint.sh
```

Or run individual commands:

```bash
# Format code
ruff format .

# Check code
ruff check .

# Auto-fix issues
ruff check --fix .

# Type check
mypy pydantic_prompt
```

## License

MIT
```

# Updated PR Description

```
# Initial Implementation of PydanticPrompt Library

This PR introduces PydanticPrompt, a lightweight Python library for documenting Pydantic models for LLM interactions using standard Python docstrings.

## Overview

PydanticPrompt allows developers to document their Pydantic models with standard Python docstrings and then easily format that documentation for inclusion in LLM prompts, providing a clean, consistent way to describe expected outputs for large language models.

## Key Features

- **Simple decorator interface** (`@prompt_schema`)
- **Uses standard Python docstrings** for field documentation
- **Automatic type inference** including generics and nested models
- **Optional validation rule display**
- **Warnings for undocumented fields**
- **Seamless integration** with existing Pydantic models

## Implementation Details

- Core functionality built around field inspection and docstring extraction
- Uses Pydantic's JSON schema for validation rule discovery
- Modern type annotations with mypy validation
- Automated CI setup with GitHub Actions
- Comprehensive linting with Ruff

## Example Usage

```python
from pydantic import BaseModel, Field
from pydantic_prompt import prompt_schema

@prompt_schema
class UserProfile(BaseModel):
    name: str
    """The full name of the user"""
    
    age: int = Field(ge=0)
    """User's age in years - must be a positive integer"""
    
    email: str = Field(pattern=r"[^@]+@[^@]+\.[^@]+")
    """Valid email address that will be used for communication"""

# In an LLM prompt
prompt = f"""
Extract a UserProfile from this text according to this schema:

{UserProfile.format_for_llm(include_validation=True)}

Text: John Doe is 32 years old, contact him at john.doe@example.com
"""
```

## Test Results

All tests are passing:

```
====================================================================== test session starts ======================================================================
platform linux -- Python 3.12.1, pytest-8.3.5, pluggy-1.5.0 -- /workspaces/PydanticPrompt/.venv/bin/python
cachedir: .pytest_cache
rootdir: /workspaces/PydanticPrompt
configfile: pyproject.toml
testpaths: tests
collected 4 items                                                                                                                                               

tests/test_pydantic_prompt.py::test_basic_docstring_extraction PASSED                                                                                     [ 25%]
tests/test_pydantic_prompt.py::test_optional_fields PASSED                                                                                                [ 50%]
tests/test_pydantic_prompt.py::test_validation_rules PASSED                                                                                               [ 75%]
tests/test_pydantic_prompt.py::test_nested_models PASSED                                                                                                  [100%]

======================================================================= 4 passed in 0.13s =======================================================================
```

## Changes Made

- Created core implementation with docstring extraction
- Added comprehensive type hints with mypy validation
- Set up CI with GitHub Actions for automated testing
- Added linting script for consistent code style
- Implemented warnings for undocumented fields
- Created detailed documentation and examples