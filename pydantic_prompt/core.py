import inspect
from typing import Type, TypeVar, Any, get_origin, get_args, Optional, Union
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def llm_documented(cls: Type[T]) -> Type[T]:
    """Decorator to add LLM documentation methods to a Pydantic model."""
    
    @classmethod
    def format_for_llm(cls, include_validation: bool = False) -> str:
        """Format this model's fields and docstrings for LLM prompts."""
        lines = [f"{cls.__name__}:"]
        
        # Get JSON schema to extract validation info if needed
        json_schema = cls.model_json_schema() if include_validation else {}
        properties = json_schema.get("properties", {})
        
        # Iterate through each field
        for name, field_info in cls.model_fields.items():
            # Get the field's type
            field_type = _get_field_type_name(field_info)
            
            # Get docstring for the field
            docstring = _extract_field_docstring(cls, name)
            
            # Determine if field is optional
            is_optional = not field_info.is_required()
            optional_str = ", optional" if is_optional else ""
            
            # Format the field line
            field_line = f"- {name} ({field_type}{optional_str}): {docstring}"
            
            # Add validation info if requested
            if include_validation and name in properties:
                field_schema = properties[name]
                
                constraints = []
                # Common validation keywords
                for key in ["minLength", "maxLength", "minimum", "maximum", "pattern"]:
                    if key in field_schema:
                        # Convert camelCase to snake_case for display
                        display_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
                        # Special case mappings
                        if display_key == "minimum":
                            display_key = "ge" if field_schema.get("exclusiveMinimum") else "ge"
                        elif display_key == "maximum":
                            display_key = "le" if field_schema.get("exclusiveMaximum") else "le"
                        elif display_key == "min_length":
                            display_key = "min_length" 
                        elif display_key == "max_length":
                            display_key = "max_length"
                        
                        constraints.append(f"{display_key}: {field_schema[key]}")
                
                if constraints:
                    field_line += f" [Constraints: {', '.join(constraints)}]"
            
            lines.append(field_line)
        
        return "\n".join(lines)
    
    # Add the format_for_llm method to the class
    cls.format_for_llm = format_for_llm
    
    return cls


def _extract_field_docstring(cls, field_name):
    """Extract docstring for a field from class source code."""
    try:
        source = inspect.getsource(cls)
        
        # Look for field definition
        patterns = [
            f"{field_name}:", 
            f"{field_name} :",
            f"{field_name} ="
        ]
        
        field_pos = -1
        for pattern in patterns:
            pos = source.find(pattern)
            if pos != -1:
                field_pos = pos
                break
                
        if field_pos == -1:
            return ""
            
        # Look for triple-quoted docstring
        for quote in ['"""', "'''"]:
            doc_start = source.find(quote, field_pos)
            if doc_start != -1:
                doc_end = source.find(quote, doc_start + 3)
                if doc_end != -1:
                    return source[doc_start + 3:doc_end].strip()
                
    except Exception:
        pass
        
    return ""


def _get_field_type_name(field_info):
    """Get a user-friendly type name from a field."""
    annotation = field_info.annotation
    
    # Handle Optional types
    if get_origin(annotation) is Union and type(None) in get_args(annotation):
        args = get_args(annotation)
        for arg in args:
            if arg is not type(None):
                # Remove Optional wrapper, we handle optionality separately
                annotation = arg
                break
    
    # Handle basic types
    if isinstance(annotation, type):
        return annotation.__name__
    
    # Handle parameterized generics
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        
        # Handle list types
        if origin is list or str(origin).endswith("list"):
            arg_type = args[0]
            # Get simple name for the argument type
            if hasattr(arg_type, "__name__"):
                arg_name = arg_type.__name__
            else:
                arg_name = str(arg_type).replace("typing.", "")
            return f"list[{arg_name}]"
        
        # Handle dict types
        elif origin is dict or str(origin).endswith("dict"):
            key_type = args[0]
            val_type = args[1]
            key_name = key_type.__name__ if hasattr(key_type, "__name__") else str(key_type)
            val_name = val_type.__name__ if hasattr(val_type, "__name__") else str(val_type)
            return f"dict[{key_name}, {val_name}]"
        
        # Handle other generic types
        else:
            origin_name = origin.__name__ if hasattr(origin, "__name__") else str(origin)
            origin_name = origin_name.lower()  # Convert List to list, etc.
            arg_strs = []
            for arg in args:
                if hasattr(arg, "__name__"):
                    arg_strs.append(arg.__name__)
                else:
                    arg_strs.append(str(arg).replace("typing.", ""))
            return f"{origin_name}[{', '.join(arg_strs)}]"
    
    # For any other types
    return str(annotation).replace("typing.", "")