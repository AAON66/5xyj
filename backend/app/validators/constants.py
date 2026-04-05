from __future__ import annotations

import re

ID_NUMBER_PATTERN = re.compile(r'^\d{15}$|^\d{17}[\dX]$')
NON_MAINLAND_ID_NUMBER_PATTERN = re.compile(r'^[A-Z]{1,2}\d{6,10}[A-Z0-9]?$')
