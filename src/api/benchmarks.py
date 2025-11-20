"""
Benchmarking API Endpoints

Provides endpoints to run model benchmarks and view results.
"""

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from typing import List
from pathlib import Path
import json

from src.benchmarking.model_benchmarks import model_benchmarker, BENCHMARK_TESTS
from src.core.logging import logger

router = APIRouter()


@router.post("/api/benchmarks/run")
async def run_benchmark(
    model_name: str = Query(..., description="Model to benchmark"),
    iterations: int = Query(1, ge=1, le=10, description="Number of iterations"),
    background_tasks: BackgroundTasks = None
):
    """
    Run a benchmark on a specific model.

    This runs in the background and saves results to disk.
    """
    try:
        # Run benchmark in background
        async def run_benchmark_task():
            try:
                await model_benchmarker.benchmark_model(model_name, iterations=iterations)
            except Exception as e:
                logger.error(f"Benchmark failed: {e}")

        if background_tasks:
            background_tasks.add_task(run_benchmark_task)

            return {
                "status": "started",
                "model": model_name,
                "iterations": iterations,
                "message": "Benchmark started in background. Check /api/benchmarks/results for results."
            }
        else:
            # Run synchronously if no background tasks available
            result = await model_benchmarker.benchmark_model(model_name, iterations=iterations)
            return {
                "status": "completed",
                "result": result
            }

    except Exception as e:
        logger.error(f"Failed to start benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/benchmarks/compare")
async def compare_models(
    models: List[str] = Query(..., description="List of models to compare"),
    background_tasks: BackgroundTasks = None
):
    """
    Compare multiple models on the same test suite.
    """
    if len(models) < 2:
        raise HTTPException(status_code=400, detail="At least 2 models required for comparison")

    try:
        async def run_comparison_task():
            try:
                await model_benchmarker.compare_models(models)
            except Exception as e:
                logger.error(f"Comparison failed: {e}")

        if background_tasks:
            background_tasks.add_task(run_comparison_task)

            return {
                "status": "started",
                "models": models,
                "message": "Comparison started in background. Check /api/benchmarks/results for results."
            }
        else:
            result = await model_benchmarker.compare_models(models)
            return {
                "status": "completed",
                "result": result
            }

    except Exception as e:
        logger.error(f"Failed to start comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/benchmarks/results")
async def get_benchmark_results(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Get recent benchmark results.

    Returns list of benchmark result files sorted by date.
    """
    try:
        results_dir = Path("benchmark_results")

        if not results_dir.exists():
            return {"results": []}

        # Get all JSON files
        result_files = sorted(
            results_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        results = []
        for filepath in result_files:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    results.append({
                        "filename": filepath.name,
                        "timestamp": data.get("timestamp"),
                        "model": data.get("model", data.get("models", [])),
                        "summary": data.get("summary", data.get("winner"))
                    })
            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")

        return {
            "count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Failed to get benchmark results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/benchmarks/results/{filename}")
async def get_benchmark_result(filename: str):
    """
    Get detailed results from a specific benchmark run.
    """
    try:
        filepath = Path("benchmark_results") / filename

        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Benchmark result not found")

        with open(filepath, 'r') as f:
            data = json.load(f)

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get benchmark result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/benchmarks/tests")
async def get_benchmark_tests():
    """
    Get list of available benchmark tests.
    """
    return {
        "count": len(BENCHMARK_TESTS),
        "tests": [
            {
                "name": test.name,
                "category": test.category,
                "prompt": test.prompt[:100] + "..." if len(test.prompt) > 100 else test.prompt
            }
            for test in BENCHMARK_TESTS
        ]
    }
