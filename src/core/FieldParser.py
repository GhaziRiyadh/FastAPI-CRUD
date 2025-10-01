import re
from typing import Dict, List, Optional, Union, Tuple
from enum import Enum


class FieldType(Enum):
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    DATETIME = "datetime"
    TEXT = "text"
    JSON = "json"
    LIST = "list"
    OPTIONAL = "optional"
    RELATIONSHIP = "relationship"


class FieldParser:
    """Parse model field definitions and detect relationships."""
    
    # Common type mappings
    TYPE_MAPPINGS = {
        'str': FieldType.STRING,
        'string': FieldType.STRING,
        'int': FieldType.INTEGER,
        'integer': FieldType.INTEGER,
        'float': FieldType.FLOAT,
        'bool': FieldType.BOOLEAN,
        'boolean': FieldType.BOOLEAN,
        'datetime': FieldType.DATETIME,
        'text': FieldType.TEXT,
        'json': FieldType.JSON,
        'dict': FieldType.JSON,
    }
    
    # Relationship patterns
    RELATIONSHIP_PATTERNS = [
        (r'.*_id$', 'ForeignKey'),  # post_id, user_id, etc.
        (r'^[A-Z][a-zA-Z]*$', 'ModelReference'),  # User, Post, Category
        (r'List\[[A-Z][a-zA-Z]*\]', 'OneToMany'),  # List[Post], List[Comment]
        (r'Optional\[[A-Z][a-zA-Z]*\]', 'ManyToOne'),  # Optional[User], Optional[Category]
    ]
    
    @classmethod
    def parse_field(cls, field_definition: str) -> Dict[str, any]:
        """
        Parse a field definition string and return structured information.
        
        Args:
            field_definition: Field definition in format "name:type" or "name:type=default"
            
        Returns:
            Dictionary with field information
        """
        # Clean the input
        field_definition = field_definition.strip()
        
        # Split field name and type/options
        if ':' not in field_definition:
            return cls._create_field_info(field_definition, 'str')
        
        name_part, type_part = field_definition.split(':', 1)
        field_name = name_part.strip()
        
        # Handle default values
        if '=' in type_part:
            type_def, default_val = type_part.split('=', 1)
            field_type = type_def.strip()
            default_value = default_val.strip()
        else:
            field_type = type_part.strip()
            default_value = None
        
        return cls._create_field_info(field_name, field_type, default_value)
    
    @classmethod
    def _create_field_info(cls, field_name: str, field_type: str, default_value: str = None) -> Dict[str, any]:
        """Create structured field information dictionary."""
        
        # Clean field type
        field_type = field_type.strip().lower()
        
        # Detect relationships
        relationship_info = cls._detect_relationship(field_name, field_type)
        
        # Get base type
        base_type = cls._get_base_type(field_type)
        
        # Determine if it's optional
        is_optional = cls._is_optional_type(field_type)
        
        # Determine if it's a list
        is_list = cls._is_list_type(field_type)
        
        # Get Python type hint
        python_type = cls._get_python_type(field_type)
        
        # Get SQLAlchemy/SQLModel type
        sql_type = cls._get_sql_type(field_type)
        
        return {
            'name': field_name,
            'original_type': field_type,
            'base_type': base_type.value if base_type else field_type,
            'python_type': python_type,
            'sql_type': sql_type,
            'is_optional': is_optional,
            'is_list': is_list,
            'is_relationship': relationship_info is not None,
            'relationship': relationship_info,
            'default_value': default_value,
            'field_definition': cls._generate_field_definition(field_name, field_type, default_value),
            'schema_definition': cls._generate_schema_definition(field_name, field_type, default_value),
        }
    
    @classmethod
    def _detect_relationship(cls, field_name: str, field_type: str) -> Optional[Dict[str, any]]:
        """Detect if field represents a relationship."""
        
        # Check for foreign key pattern (ends with _id)
        if field_name.endswith('_id') and field_type in ['int', 'integer']:
            related_model = field_name[:-3]  # Remove _id
            related_model = related_model.capitalize()
            return {
                'type': 'ForeignKey',
                'related_model': related_model,
                'relationship_type': 'ManyToOne',
                'description': f'Foreign key to {related_model}'
            }
        
        # Check for model reference (capitalized type)
        if field_type[0].isupper() and not field_type.startswith(('List[', 'Optional[')):
            return {
                'type': 'ModelReference',
                'related_model': field_type,
                'relationship_type': 'ManyToOne',
                'description': f'Relationship to {field_type}'
            }
        
        # Check for List[Model] pattern (OneToMany)
        list_match = re.match(r'list\[([a-zA-Z_][a-zA-Z0-9_]*)\]', field_type, re.IGNORECASE)
        if list_match:
            related_model = list_match.group(1)
            return {
                'type': 'OneToMany',
                'related_model': related_model,
                'relationship_type': 'OneToMany',
                'description': f'One-to-many relationship with {related_model}'
            }
        
        # Check for Optional[Model] pattern (ManyToOne)
        optional_match = re.match(r'optional\[([a-zA-Z_][a-zA-Z0-9_]*)\]', field_type, re.IGNORECASE)
        if optional_match:
            related_model = optional_match.group(1)
            return {
                'type': 'ManyToOne',
                'related_model': related_model,
                'relationship_type': 'ManyToOne',
                'description': f'Many-to-one relationship with {related_model}'
            }
        
        return None
    
    @classmethod
    def _get_base_type(cls, field_type: str) -> Optional[FieldType]:
        """Get the base field type."""
        # Remove List[] and Optional[] wrappers
        clean_type = re.sub(r'(List\[|Optional\[|\])', '', field_type)
        clean_type = clean_type.lower()
        
        return cls.TYPE_MAPPINGS.get(clean_type)
    
    @classmethod
    def _is_optional_type(cls, field_type: str) -> bool:
        """Check if field type is optional."""
        return field_type.lower().startswith('optional[')
    
    @classmethod
    def _is_list_type(cls, field_type: str) -> bool:
        """Check if field type is a list."""
        return field_type.lower().startswith('list[')
    
    @classmethod
    def _get_python_type(cls, field_type: str) -> str:
        """Get Python type hint string."""
        if cls._is_optional_type(field_type):
            inner_type = field_type[9:-1]  # Remove "Optional[" and "]"
            return f"Optional[{cls._get_python_type(inner_type)}]"
        elif cls._is_list_type(field