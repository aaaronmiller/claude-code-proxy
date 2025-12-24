
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

try:
    print("Verifying Benchmarks...")
    from src.services.benchmarking.model_benchmarks import BENCHMARK_TESTS
    
    if len(BENCHMARK_TESTS) == 5:
        print("✅ Benchmarks loaded successfully from JSON (count=5)")
        print(f"First test: {BENCHMARK_TESTS[0].name}")
    else:
        print(f"❌ Benchmarks count mismatch. Expected 5, got {len(BENCHMARK_TESTS)}")
        sys.exit(1)

    print("\nVerifying Billing Integrations...")
    from src.services.billing.billing_integrations import billing_manager
    print("✅ Billing manager imported successfully")

except Exception as e:
    print(f"❌ Verification failed: {e}")
    sys.exit(1)
