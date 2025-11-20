"""
Automated Model Benchmarking System

Tests models with standardized prompts to compare:
- Performance (latency, throughput)
- Quality (output correctness)
- Cost efficiency
- Reliability
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import time
import json
from pathlib import Path
import httpx

from src.core.logging import logger


class BenchmarkTest:
    """A single benchmark test case"""

    def __init__(
        self,
        name: str,
        prompt: str,
        expected_keywords: List[str] = None,
        category: str = "general"
    ):
        self.name = name
        self.prompt = prompt
        self.expected_keywords = expected_keywords or []
        self.category = category


# Standard benchmark test suite
BENCHMARK_TESTS = [
    BenchmarkTest(
        name="Simple Math",
        prompt="What is 123 + 456? Answer with just the number.",
        expected_keywords=["579"],
        category="reasoning"
    ),
    BenchmarkTest(
        name="Code Generation",
        prompt="Write a Python function to calculate fibonacci number. Include only the code, no explanation.",
        expected_keywords=["def", "fibonacci", "return"],
        category="coding"
    ),
    BenchmarkTest(
        name="Text Summarization",
        prompt="Summarize this in 10 words: Artificial intelligence is transforming how we work and live.",
        expected_keywords=["AI", "transform", "work", "live"],
        category="nlp"
    ),
    BenchmarkTest(
        name="Instruction Following",
        prompt="List exactly 3 colors. Format: 1. [color] 2. [color] 3. [color]",
        expected_keywords=["1.", "2.", "3."],
        category="instruction"
    ),
    BenchmarkTest(
        name="Creative Writing",
        prompt="Write a haiku about coding.",
        expected_keywords=[],
        category="creative"
    )
]


class ModelBenchmarker:
    """Runs benchmarks against models and records results"""

    def __init__(self, base_url: str = "http://localhost:8082", api_key: str = "test"):
        self.base_url = base_url
        self.api_key = api_key
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)

    async def benchmark_model(
        self,
        model_name: str,
        tests: List[BenchmarkTest] = None,
        iterations: int = 1
    ) -> Dict[str, Any]:
        """
        Benchmark a single model.

        Args:
            model_name: Name of the model to test
            tests: List of tests to run (defaults to BENCHMARK_TESTS)
            iterations: Number of times to run each test

        Returns:
            Dictionary with benchmark results
        """
        tests = tests or BENCHMARK_TESTS

        logger.info(f"Starting benchmark for {model_name} with {len(tests)} tests")

        results = {
            "model": model_name,
            "timestamp": datetime.utcnow().isoformat(),
            "iterations": iterations,
            "tests": [],
            "summary": {
                "total_tests": len(tests),
                "avg_latency_ms": 0,
                "min_latency_ms": 0,
                "max_latency_ms": 0,
                "total_tokens": 0,
                "avg_tokens_per_sec": 0,
                "total_cost": 0.0,
                "success_rate": 0.0
            }
        }

        latencies = []
        tokens_per_sec_list = []
        total_tokens = 0
        total_cost = 0.0
        successes = 0

        for test in tests:
            test_results = await self._run_test(model_name, test, iterations)
            results["tests"].append(test_results)

            if test_results["success"]:
                successes += 1

            latencies.extend(test_results["latencies"])
            if test_results.get("tokens_per_sec"):
                tokens_per_sec_list.append(test_results["tokens_per_sec"])
            total_tokens += test_results.get("total_tokens", 0)
            total_cost += test_results.get("total_cost", 0.0)

        # Calculate summary stats
        if latencies:
            results["summary"]["avg_latency_ms"] = sum(latencies) / len(latencies)
            results["summary"]["min_latency_ms"] = min(latencies)
            results["summary"]["max_latency_ms"] = max(latencies)

        if tokens_per_sec_list:
            results["summary"]["avg_tokens_per_sec"] = sum(tokens_per_sec_list) / len(tokens_per_sec_list)

        results["summary"]["total_tokens"] = total_tokens
        results["summary"]["total_cost"] = total_cost
        results["summary"]["success_rate"] = (successes / len(tests)) * 100 if tests else 0

        # Save results
        self._save_results(model_name, results)

        return results

    async def _run_test(
        self,
        model_name: str,
        test: BenchmarkTest,
        iterations: int
    ) -> Dict[str, Any]:
        """Run a single test multiple times"""
        test_results = {
            "name": test.name,
            "category": test.category,
            "iterations": iterations,
            "latencies": [],
            "success": False,
            "quality_score": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "tokens_per_sec": 0.0,
            "errors": []
        }

        for i in range(iterations):
            try:
                result = await self._call_model(model_name, test.prompt)

                test_results["latencies"].append(result["duration_ms"])
                test_results["total_tokens"] += result.get("tokens", 0)
                test_results["total_cost"] += result.get("cost", 0.0)

                # Check quality
                output = result.get("output", "").lower()
                keywords_found = sum(1 for kw in test.expected_keywords if kw.lower() in output)
                quality = (keywords_found / len(test.expected_keywords) * 100) if test.expected_keywords else 100

                test_results["quality_score"] = max(test_results["quality_score"], quality)
                test_results["success"] = True

                # Calculate tokens/sec
                if result["duration_ms"] > 0:
                    tps = result.get("tokens", 0) / (result["duration_ms"] / 1000)
                    test_results["tokens_per_sec"] = max(test_results["tokens_per_sec"], tps)

            except Exception as e:
                logger.error(f"Test {test.name} iteration {i+1} failed: {e}")
                test_results["errors"].append(str(e))

        return test_results

    async def _call_model(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Call the model via proxy API"""
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500
                },
                timeout=60.0
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}: {response.text}")

            data = response.json()
            content = data.get("content", [])
            output = content[0].get("text", "") if content else ""

            usage = data.get("usage", {})
            tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

            return {
                "duration_ms": duration_ms,
                "output": output,
                "tokens": tokens,
                "cost": 0.0  # Would need pricing data
            }

    def _save_results(self, model_name: str, results: Dict[str, Any]):
        """Save benchmark results to file"""
        safe_model_name = model_name.replace("/", "_").replace(":", "_")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{safe_model_name}_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved benchmark results to {filepath}")

    async def compare_models(
        self,
        model_names: List[str],
        tests: List[BenchmarkTest] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple models on the same test suite.

        Returns comparative analysis.
        """
        tests = tests or BENCHMARK_TESTS

        logger.info(f"Comparing {len(model_names)} models")

        results = []
        for model in model_names:
            result = await self.benchmark_model(model, tests)
            results.append(result)

        # Generate comparison
        comparison = {
            "timestamp": datetime.utcnow().isoformat(),
            "models": model_names,
            "results": results,
            "winner": {
                "fastest": min(results, key=lambda x: x["summary"]["avg_latency_ms"])["model"],
                "cheapest": min(results, key=lambda x: x["summary"]["total_cost"])["model"],
                "most_reliable": max(results, key=lambda x: x["summary"]["success_rate"])["model"]
            }
        }

        # Save comparison
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.results_dir / f"comparison_{timestamp}.json"
        with open(filepath, 'w') as f:
            json.dump(comparison, f, indent=2)

        return comparison


# Global benchmarker instance
model_benchmarker = ModelBenchmarker()
