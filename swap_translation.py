#!/usr/bin/env python3
"""Script to swap source and translation in a .ts file"""

import re

def swap_source_and_translation(ts_file_path):
    with open(ts_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content into parts to handle multiline content properly
    # Find all <source>...</source><translation>...</translation> pairs
    # This regex handles multiline content inside the tags
    pattern = r'(<source>)(.*?)(</source>\s*<translation>)(.*?)(</translation>)'
    
    def replace_match(match):
        opening_source = match.group(1)  # <source>
        source_content = match.group(2)  # content inside source
        middle_part = match.group(3)     # </source><translation>
        translation_content = match.group(4)  # content inside translation
        closing_part = match.group(5)    # </translation>
        
        # Swap the content: source becomes translation, translation becomes source
        new_content = f'{opening_source}{translation_content}{middle_part}{source_content}{closing_part}'
        return new_content
    
    # Replace all matches
    swapped_content = re.sub(pattern, replace_match, content, flags=re.DOTALL)
    
    with open(ts_file_path, 'w', encoding='utf-8') as f:
        f.write(swapped_content)

if __name__ == "__main__":
    swap_source_and_translation('/root/filmeto/i18n/filmeto_zh_CN.ts')