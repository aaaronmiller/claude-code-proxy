import os
import re

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return

    # Regex to find 'except Exception as _e:' followed by 'pass'
    pattern = re.compile(r'^([ \t]*)except Exception as _e:\s+pass', re.MULTILINE)
    
    def replacement(match):
        indent = match.group(1)
        inner_indent = indent + "    "
        # We use a simple print if logger isn't strictly guaranteed, 
        # but in our codebase we use logger heavily. Let's use a safe fallback mechanism just in case,
        # actually no, we'll import logging.getLogger if we need to.
        return f"{indent}except Exception as _e:\n{inner_indent}import logging\n{inner_indent}logging.getLogger(__name__).debug(f\"Ghost exception handled: {{_e}}\")"

    new_content, count = pattern.subn(replacement, content)
    
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {count} instances in {filepath}")

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))
