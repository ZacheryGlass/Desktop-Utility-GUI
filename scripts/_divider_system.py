"""
Divider to separate system utilities from other scripts.
Note: File starts with underscore to sort it appropriately.
"""

import sys
sys.path.append('..')

from core.divider_script import DividerScript

class SystemDivider(DividerScript):
    def __init__(self):
        super().__init__(label="System Utilities", style="section")