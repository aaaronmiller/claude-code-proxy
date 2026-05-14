
import sys

with open('src/services/conversion/response_converter.py', 'r') as f:
    lines = f.readlines()

i = 0
while i < len(lines):
    line = lines[i]
    # Check if this line is the problematic yield line
    if 'yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}}' in line and "'text': '\\n\\n'" in line:
        # Get the indentation
        indent = len(line) - len(line.lstrip())
        space_indent = " " * indent
        
        # Replace this line with two lines: the var definition and the fixed yield line
        lines[i] = space_indent + "newline = '\\n\\n'\n"
        # The fixed yield line: we replace the hardcoded string with the variable
        # We have to be careful about the quotes in the yield line.
        # We know the line has: 'text': '\\n\\n'
        # We want to change it to: 'text': newline
        fixed_line = line.replace("'text': '\\n\\n'", "'text': newline")
        lines.insert(i+1, fixed_line)
        # We have added a line, so we skip the original line (which is now at i) and the new line (at i+1)
        # by incrementing i by 2
        i += 2
    else:
        i += 1

with open('src/services/conversion/response_converter.py', 'w') as f:
    f.writelines(lines)
