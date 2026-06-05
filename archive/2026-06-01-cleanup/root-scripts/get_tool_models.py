import sys
sys.path.insert(0, ".")
from src.services.models.free_model_rankings import load_free_model_rankings

rankings = load_free_model_rankings()
for r in rankings:
    if r.supports_tools:
        print(f"{r.model_id} (Tools: {r.supports_tools}, Score: {r.score})")
