from typing import Dict, Any

class DividerScript:
    """Special script type for visual dividers in the GUI."""
    
    def __init__(self, label: str = None, style: str = "default"):
        self.label = label
        self.style = style
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'type': 'divider',
            'label': self.label,
            'style': self.style
        }
    
    @staticmethod
    def is_divider_script(item) -> bool:
        """Check if an object is a DividerScript."""
        return isinstance(item, DividerScript)