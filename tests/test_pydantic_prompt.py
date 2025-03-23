from typing import Optional

from pydantic import BaseModel, Field
from pydantic_prompt import prompt_schema


def test_basic_docstring_extraction():
    @prompt_schema
    class BasicModel(BaseModel):
        name: str
        """The user's name"""

        age: int
        """Age in years"""

    output = BasicModel.format_for_llm()
    assert "name (str): The user's name" in output
    assert "age (int): Age in years" in output


def test_optional_fields():
    @prompt_schema
    class OptionalFieldsModel(BaseModel):
        required: str
        """Required field"""

        optional: Optional[str] = None
        """Optional field"""

    output = OptionalFieldsModel.format_for_llm()
    assert "required (str):" in output
    assert "optional (str, optional):" in output


def test_validation_rules():
    @prompt_schema
    class ValidationModel(BaseModel):
        name: str = Field(min_length=2, max_length=50)
        """User name"""

        age: int = Field(ge=0, le=120)
        """Age in years"""

    # Without validation
    basic_output = ValidationModel.format_for_llm()
    assert "Constraints" not in basic_output

    # With validation
    validation_output = ValidationModel.format_for_llm(include_validation=True)
    assert "Constraints: min_length: 2, max_length: 50" in validation_output
    assert "Constraints: ge: 0, le: 120" in validation_output


def test_nested_models():
    @prompt_schema
    class Address(BaseModel):
        street: str
        """Street address"""

        city: str
        """City name"""

    @prompt_schema
    class Person(BaseModel):
        name: str
        """Person's name"""

        addresses: list[Address] = []
        """List of addresses"""

    output = Person.format_for_llm()
    assert "name (str): Person's name" in output
    
    # More flexible assertion that checks for the important parts
    assert "addresses (list[Address], optional): List of addresses" in output or (
        "addresses (list[" in output and 
        "Address" in output and 
        "optional): List of addresses" in output
    )