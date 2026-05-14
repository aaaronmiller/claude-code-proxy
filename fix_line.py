
import sys

with open("src/services/conversion/response_converter.py", "r") as f:
    lines = f.readlines()

# Line numbers are 1-indexed, so line 821 is index 820
line_index = 820  # 0-indexed
if line_index < len(lines):
    line = lines[line_index]
    # Get the indentation
    indent = len(line) - len(line.lstrip())
    space_indent = " " * indent
    
    # Replace the line with two lines
    lines[line_index] = space_indent + "newline = '\\n\\n'\n"
    lines.insert(line_index + 1, space_indent + 'yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': newline}}, ensure_ascii=False)}\n\n"\n')
    
    with open("src/services/conversion/response_converter.py", "w") as f:
        f.writelines(lines)
    
    print("Fixed line 821")
else:
    print(f"Line {line_index + 1} not found!")
