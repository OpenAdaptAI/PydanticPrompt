import inspect
import warnings
from typing import TypeVar, Union, get_args, get_origin, Callable, Any, Optional, cast

from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def prompt_schema(cls: type[T], *, warn_undocumented: bool = True) -> type[T]:
    """
    Decorator to add LLM documentation methods to a Pydantic model.
    
    Args:
        cls: The Pydantic model class to decorate
        warn_undocumented: Whether to emit warnings for fields without docstrings
    
    Returns:
        The decorated class with format_for_llm method
    """
    
    def format_for_llm_impl(cls_param: type[T], include_validation: bool = False) -> str:
        """Format this model's fields and docstrings for LLM prompts."""
        lines = [f"{cls_param.__name__}:"]
        
        # Get JSON schema to extract validation info if needed
        json_schema = cls_param.model_json_schema() if include_validation else {}
        properties = json_schema.get("properties", {})
        
        # Iterate through each field
        for name, field_info in cls_param.model_fields.items():
            # Get the field's type
            field_type = _get_field_type_name(field_info)
            
            # Get docstring for the field
            docstring = _extract_field_docstring(cls_param, name)
            
            # Warn if field is not documented
            if warn_undocumented and not docstring:
                warnings.warn(
                    f"Field '{name}' in {cls_param.__name__} has no docstring. "
                    "Add a docstring for better LLM prompts.",
                    UserWarning,
                    stacklevel=2
                )
            
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
                        display_key = "".join(
                            ["_" + c.lower() if c.isupper() else c for c in key]
                        ).lstrip("_")
                        # Special case mappings
                        if display_key == "minimum":
                            display_key = "ge"
                        elif display_key == "maximum":
                            display_key = "le"
                        elif display_key == "min_length":
                            display_key = "min_length" 
                        elif display_key == "max_length":
                            display_key = "max_length"
                        
                        constraints.append(f"{display_key}: {field_schema[key]}")
                
                if constraints:
                    field_line += f" [Constraints: {', '.join(constraints)}]"
            
            lines.append(field_line)
        
        return "\n".join(lines)
    
    # Add the format_for_llm method to the class using the classmethod decorator
    setattr(cls, "format_for_llm", classmethod(format_for_llm_impl))  # type: ignore
    
    return cls


def _extract_field_docstring(cls: type, field_name: str) -> str:
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


def _get_field_type_name(field_info: Any) -> str:
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
            inner_type = ""
            
            # Get the name of the inner type more reliably
            if isinstance(arg_type, type):
                inner_type = arg_type.__name__
            elif hasattr(arg_type, "_name") and arg_type._name:
                inner_type = arg_type._name
            else:
                # Fall back to string representation with cleanup
                inner_type = str(arg_type).replace("typing.", "").strip("'<>")
                
                # Extract class name from ForwardRef if needed
                if "ForwardRef" in inner_type:
                    import re
                    match = re.search(r"ForwardRef\('([^']+)'\)", inner_type)
                    if match:
                        inner_type = match.group(1)
            
            return f"list[{inner_type}]"
        
        # Handle dict types
        if origin is dict or str(origin).endswith("dict"):
            key_type = args[0]
            val_type = args[1]
            
            # Get key type name
            if isinstance(key_type, type):
                key_name = key_type.__name__
            else:
                key_name = str(key_type).replace("typing.", "")
                
            # Get value type name
            if isinstance(val_type, type):
                val_name = val_type.__name__
            else:
                val_name = str(val_type).replace("typing.", "")
                
            return f"dict[{key_name}, {val_name}]"
        
        # Handle other generic types
        origin_name = origin.__name__ if hasattr(origin, "__name__") else str(origin)
        origin_name = origin_name.lower()  # Convert List to list, etc.
        
        arg_strs = []
        for arg in args:
            if isinstance(arg, type):
                arg_strs.append(arg.__name__)
            else:
                arg_str = str(arg).replace("typing.", "")
                if "ForwardRef" in arg_str:
                    import re
                    match = re.search(r"ForwardRef\('([^']+)'\)", arg_str)
                    if match:
                        arg_str = match.group(1)
                arg_strs.append(arg_str)
                
        return f"{origin_name}[{', '.join(arg_strs)}]"
    
    # For any other types
    type_str = str(annotation).replace("typing.", "")
    
    # Clean up ForwardRef representation
    if "ForwardRef" in type_str:
        import re
        match = re.search(r"ForwardRef\('([^']+)'\)", type_str)
        if match:
            return match.group(1)
    
    return type_str