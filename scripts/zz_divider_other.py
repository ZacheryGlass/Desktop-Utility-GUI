"""
Divider for additional utilities section.
Note: File starts with 'zz' to sort it at the end.
"""

import sys
sys.path.append('..')

from core.divider_script import DividerScript

class OtherDivider(DividerScript):
    def __init__(self):
        super().__init__(label="Other Utilities", style="section")