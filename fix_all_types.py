#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re

def fix_type_annotations(file_path):
    """Fix Python 3.10+ type annotations to be compatible with Python 3.9"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Add Optional import if not present and needed
    if ' | None' in content or '| None]' in content:
        if 'from typing import' in content and 'Optional' not in content:
            content = re.sub(
                r'(from typing import [^\n]+)',
                lambda m: m.group(1).rstrip() + ', Optional' if not m.group(1).endswith(',') else m.group(1) + ' Optional',
                content,
                count=1
            )
        elif 'from typing import' not in content and 'import typing' not in content:
            # Add import at the top after __future__ if present
            if 'from __future__' in content:
                content = re.sub(
                    r'(from __future__ import [^\n]+\n)',
                    r'\1\nfrom typing import Optional\n',
                    content,
                    count=1
                )
            else:
                content = 'from typing import Optional\n\n' + content

    # Replace X | None with Optional[X]
    content = re.sub(r':\s*([A-Za-z_][A-Za-z0-9_\[\]\.]*)\s*\|\s*None', r': Optional[\1]', content)
    content = re.sub(r'->\s*([A-Za-z_][A-Za-z0-9_\[\]\.]*)\s*\|\s*None', r'-> Optional[\1]', content)
    content = re.sub(r'Mapped\[([A-Za-z_][A-Za-z0-9_\[\]\.]*)\s*\|\s*None\]', r'Mapped[Optional[\1]]', content)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Fix all Python files in backend
fixed_count = 0
for root, dirs, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            if fix_type_annotations(file_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1

print(f"\nTotal files fixed: {fixed_count}")
