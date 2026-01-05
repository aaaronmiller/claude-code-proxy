"""
Documentation API Routes

Serves markdown documentation files for the web UI.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List, Dict, Any

router = APIRouter(prefix="/api/docs", tags=["documentation"])

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"


@router.get("/")
async def list_docs() -> Dict[str, Any]:
    """List all available documentation files."""
    docs = []
    
    if not DOCS_DIR.exists():
        return {"docs": [], "error": "Documentation directory not found"}
    
    # Walk through docs directory
    for path in DOCS_DIR.rglob("*.md"):
        relative = path.relative_to(DOCS_DIR)
        docs.append({
            "path": str(relative),
            "name": path.stem.replace("-", " ").replace("_", " ").title(),
            "category": relative.parent.name if relative.parent.name != "." else "root",
            "size": path.stat().st_size
        })
    
    # Sort: root docs first, then by category
    docs.sort(key=lambda x: (0 if x["category"] == "root" else 1, x["category"], x["name"]))
    
    return {
        "docs": docs,
        "categories": list(set(d["category"] for d in docs))
    }


@router.get("/{path:path}")
async def get_doc(path: str) -> Dict[str, Any]:
    """Get a specific documentation file's content."""
    # Sanitize path
    if ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    doc_path = DOCS_DIR / path
    
    # Add .md extension if not present
    if not doc_path.suffix:
        doc_path = doc_path.with_suffix(".md")
    
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail=f"Document not found: {path}")
    
    if not doc_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    try:
        content = doc_path.read_text()
        
        # Extract title from first H1
        title = path
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        return {
            "path": str(doc_path.relative_to(DOCS_DIR)),
            "title": title,
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading document: {str(e)}")


@router.get("/search/{query}")
async def search_docs(query: str) -> Dict[str, Any]:
    """Search documentation content."""
    results = []
    query_lower = query.lower()
    
    if not DOCS_DIR.exists():
        return {"results": [], "query": query}
    
    for path in DOCS_DIR.rglob("*.md"):
        try:
            content = path.read_text()
            if query_lower in content.lower():
                # Find matching lines
                matches = []
                for i, line in enumerate(content.split("\n")):
                    if query_lower in line.lower():
                        matches.append({
                            "line": i + 1,
                            "text": line[:200]  # Truncate long lines
                        })
                
                results.append({
                    "path": str(path.relative_to(DOCS_DIR)),
                    "name": path.stem.replace("-", " ").replace("_", " ").title(),
                    "matches": matches[:5]  # Limit matches per file
                })
        except Exception:
            continue
    
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }
