from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from enum import Enum

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