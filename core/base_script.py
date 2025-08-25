from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List
from enum import Enum
from dataclasses import dataclass

class ArgumentType(Enum):
    """Types of arguments that scripts can accept"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CHOICE = "choice"  # Select from predefined options

@dataclass
class ArgumentSpec:
    """Specification for a script argument"""
    name: str
    arg_type: ArgumentType
    description: str
    required: bool = True
    default_value: Any = None
    choices: Optional[List[str]] = None  # For CHOICE type
    min_value: Optional[float] = None   # For numeric types
    max_value: Optional[float] = None   # For numeric types

    def __post_init__(self):
        if self.arg_type == ArgumentType.CHOICE and not self.choices:
            raise ValueError(f"CHOICE argument '{self.name}' must specify choices")

@dataclass 
class ScriptArgumentsSpec:
    """Complete argument specification for a script"""
    supports_arguments: bool = False
    arguments: List[ArgumentSpec] = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []

class UtilityScript(ABC):
    
    def __init__(self):
        self._validate_metadata()
    
    def _validate_metadata(self):
        metadata = self.get_metadata()
        required_fields = ['name', 'description', 'button_type']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Script metadata missing required field: {field}")
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_status(self) -> Any:
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        pass
    
    def get_status_display(self) -> str:
        try:
            status = self.get_status()
            if status is None:
                return "Unknown"
            return str(status)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def is_available(self) -> bool:
        try:
            return self.validate()
        except Exception:
            return False
    
    def get_arguments_spec(self) -> ScriptArgumentsSpec:
        """
        Override this method to specify argument requirements for your script.
        Returns ScriptArgumentsSpec with supports_arguments=False by default.
        """
        return ScriptArgumentsSpec(supports_arguments=False)
    
    def supports_arguments(self) -> bool:
        """Check if this script supports configurable arguments"""
        try:
            spec = self.get_arguments_spec()
            return spec.supports_arguments and len(spec.arguments) > 0
        except Exception:
            return False
    
    def validate_arguments(self, args: List[Any]) -> bool:
        """Validate provided arguments against the script's argument specification"""
        try:
            spec = self.get_arguments_spec()
            if not spec.supports_arguments:
                return len(args) == 0
            
            required_count = sum(1 for arg_spec in spec.arguments if arg_spec.required)
            if len(args) < required_count:
                return False
            
            # Validate each argument type and constraints
            for i, arg_value in enumerate(args):
                if i >= len(spec.arguments):
                    break  # Extra args are ignored
                
                arg_spec = spec.arguments[i]
                if not self._validate_single_argument(arg_value, arg_spec):
                    return False
            
            return True
        except Exception:
            return False
    
    def _validate_single_argument(self, value: Any, spec: ArgumentSpec) -> bool:
        """Validate a single argument value against its specification"""
        if value is None:
            return not spec.required
        
        try:
            if spec.arg_type == ArgumentType.STRING:
                return isinstance(value, str)
            elif spec.arg_type == ArgumentType.INTEGER:
                if not isinstance(value, int):
                    return False
                if spec.min_value is not None and value < spec.min_value:
                    return False
                if spec.max_value is not None and value > spec.max_value:
                    return False
                return True
            elif spec.arg_type == ArgumentType.FLOAT:
                if not isinstance(value, (int, float)):
                    return False
                if spec.min_value is not None and value < spec.min_value:
                    return False
                if spec.max_value is not None and value > spec.max_value:
                    return False
                return True
            elif spec.arg_type == ArgumentType.BOOLEAN:
                return isinstance(value, bool)
            elif spec.arg_type == ArgumentType.CHOICE:
                return str(value) in spec.choices
            
            return False
        except Exception:
            return False