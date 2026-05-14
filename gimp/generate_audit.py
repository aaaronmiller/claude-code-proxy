import os
import ast
import sys

# Directories to ignore as per instructions ("not rtk, headrom or other full progams in subfolders")
IGNORE_DIRS = [
    'rtk', 'headroom', 'web-ui', 'node_modules', '.venv', '.git', 
    '__pycache__', '.pytest_cache', 'tests', '.claude', 'compression', 
    'benchmark_results', 'logs', 'audit-reports', '.ruff_cache', 
    '.build-artifacts', 'gimp'
]

def is_ignored(path):
    path_parts = path.split(os.sep)
    for d in IGNORE_DIRS:
        if d in path_parts:
            return True
    return False

def analyze_python(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception as e:
        return f"Error parsing {filepath}: {e}\n\n"

    lines = [f"# File Audit: {filepath}"]
    lines.append(f"**Path**: `{filepath}`\n")
    
    doc = ast.get_docstring(tree)
    if doc:
        lines.append(f"**Module Overview**: \n```text\n{doc}\n```\n")
    
    # Global assignments
    globals_list = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    val = "..."
                    try:
                        val = ast.unparse(node.value)
                    except:
                        pass
                    globals_list.append(f"- `{target.id}` = `{val}`")
    if globals_list:
        lines.append("## Global Presets & Variables")
        lines.extend(globals_list)
        lines.append("")

    # Imports
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for n in node.names:
                    imports.append(f"{node.module}.{n.name}")
    if imports:
        lines.append("## Dependencies & Imports")
        lines.append(", ".join(imports) + "\n")

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            lines.append(f"## Feature Class: `{node.name}`")
            cdoc = ast.get_docstring(node)
            if cdoc:
                lines.append(f"**Description:**\n```text\n{cdoc}\n```\n")
            
            for item in node.body:
                if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                    lines.append(f"### Method: `{item.name}`")
                    mdoc = ast.get_docstring(item)
                    if mdoc:
                        lines.append(f"**Logic & Purpose:**\n```text\n{mdoc}\n```\n")
                    
                    args = [a.arg for a in item.args.args]
                    lines.append(f"**Parameters:** `{', '.join(args)}`")
                    
                    vars_in_method = set()
                    for m_node in ast.walk(item):
                        if isinstance(m_node, ast.Assign):
                            for t in m_node.targets:
                                if isinstance(t, ast.Name):
                                    vars_in_method.add(t.id)
                    if vars_in_method:
                        lines.append(f"**Variables Used:** `{', '.join(vars_in_method)}`")
                    
                    try:
                        source = ast.unparse(item)
                        lines.append(f"**Implementation:**\n```python\n{source}\n```\n")
                    except:
                        pass
            lines.append("---\n")
            
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            lines.append(f"## Feature Function: `{node.name}`")
            fdoc = ast.get_docstring(node)
            if fdoc:
                lines.append(f"**Logic & Purpose:**\n```text\n{fdoc}\n```\n")
            
            args = [a.arg for a in node.args.args]
            lines.append(f"**Parameters:** `{', '.join(args)}`")
            
            vars_in_func = set()
            for m_node in ast.walk(node):
                if isinstance(m_node, ast.Assign):
                    for t in m_node.targets:
                        if isinstance(t, ast.Name):
                            vars_in_func.add(t.id)
            if vars_in_func:
                lines.append(f"**Variables Used:** `{', '.join(vars_in_func)}`")
                
            try:
                source = ast.unparse(node)
                lines.append(f"**Implementation:**\n```python\n{source}\n```\n")
            except:
                pass
            lines.append("---\n")

    return "\n".join(lines) + "\n\n"

def analyze_text(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading {filepath}: {e}\n\n"

    lines = [f"# Text/Config File Audit: {filepath}"]
    lines.append(f"**File Size:** {len(content)} bytes\n")
    
    if filepath.endswith('.md'):
        headers = [line.strip() for line in content.split('\n') if line.strip().startswith('#')]
        if headers:
            lines.append("## Features & Sections Declared:")
            lines.extend(headers)
            lines.append("\n")
    
    # Just append the whole content to ensure the specifics are captured
    lines.append("## Content / Data Structure:")
    lines.append("```text\n" + content + "\n```\n")
    lines.append("\n---\n")
    return "\n".join(lines) + "\n\n"

def main():
    root_dir = '/home/cheta/code/claude-code-proxy'
    out_dir = os.path.join(root_dir, 'gimp')
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    code_files = []
    text_files = []
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d))]
        for f in files:
            full_path = os.path.join(root, f)
            if f.endswith(('.py', '.js', '.ts', '.sh')):
                code_files.append(full_path)
            elif f.endswith(('.md', '.txt', '.json', '.yaml', '.yml', '.toml')):
                text_files.append(full_path)

    def write_chunks(file_list, generator_func, prefix, target_size=100000):
        chunk_idx = 1
        current_content = ""
        manifest = []
        
        for filepath in file_list:
            content = generator_func(filepath)
            current_content += content
            manifest.append(filepath)
            
            # 100000 chars is roughly 100KB
            if len(current_content) >= target_size:
                out_file = os.path.join(out_dir, f"{prefix}_{chunk_idx:02d}.md")
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(current_content)
                chunk_idx += 1
                current_content = ""
                
        if current_content:
            out_file = os.path.join(out_dir, f"{prefix}_{chunk_idx:02d}.md")
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(current_content)
                
        return manifest

    print("Auditing User Code Files...")
    code_manifest = write_chunks(code_files, analyze_python, "code_audit_scratch", 100000)
    
    print("Auditing Text and Config Files...")
    text_manifest = write_chunks(text_files, analyze_text, "text_audit_scratch", 100000)

    with open(os.path.join(out_dir, "audit_manifest.md"), "w", encoding="utf-8") as f:
        f.write("# Claude Code Proxy - Audit Manifest\n\n")
        f.write("## Audited Code Files\n")
        for mf in code_manifest:
            f.write(f"- {mf}\n")
        f.write("\n## Audited Text & Data Files\n")
        for mf in text_manifest:
            f.write(f"- {mf}\n")
            
    print(f"Audit Complete. Check the '{out_dir}' folder.")

if __name__ == "__main__":
    main()
