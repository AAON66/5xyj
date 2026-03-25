#!/usr/bin/env python3
import re
import os

def fix_mapped_optional(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix Optional[Mapped[X]] to Mapped[Optional[X]]
    content = re.sub(r'Optional\[Mapped\[([^\]]+)\]\]', r'Mapped[Optional[\1]]', content)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

fixed = 0
for root, dirs, files in os.walk('backend/app/models'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            if fix_mapped_optional(path):
                print(f"Fixed: {path}")
                fixed += 1

print(f"\nTotal: {fixed}")
