"""
Simple visual separator between groups.
Note: File starts with 'm' to place it in the middle of the list.
"""

import sys
sys.path.append('..')

from core.divider_script import DividerScript

class SimpleSeparator(DividerScript):
    def __init__(self):
        # No label, just a line
        super().__init__(label=None, style="subtle")