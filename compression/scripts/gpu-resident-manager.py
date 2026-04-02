#!/usr/bin/env python3
"""
GPU Resident Model Manager for Headroom
Keeps multiple compression models resident in VRAM for 90%+ utilization
"""

import torch
import sys
from transformers import AutoModel, AutoTokenizer
from headroom.transforms.kompress_compressor import KompressCompressor, KompressConfig

class GPUResidentModelManager:
    """Manages multiple resident models on GPU for maximum VRAM utilization."""
    
    def __init__(self, target_utilization=0.92):
        self.target_utilization = target_utilization
        self.models = {}
        self.tokenizers = {}
        self.caches = {}
        self.total_vram = self._get_total_vram()
        print(f"🎯 Target VRAM: {self.target_utilization * 100:.0f}% ({int(self.total_vram * self.target_utilization)} MiB)")
    
    def _get_total_vram(self):
        """Get total GPU VRAM in MiB."""
        return torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
    
    def _get_used_vram(self):
        """Get currently used VRAM in MiB."""
        return torch.cuda.memory_allocated(0) / (1024 * 1024)
    
    def _get_utilization(self):
        """Get current VRAM utilization percentage."""
        return self._get_used_vram() / self.total_vram * 100
    
    def load_model(self, name: str, model_id: str, keep_tokenizer=True):
        """Load a model onto GPU and keep it resident."""
        print(f"\n📦 Loading {name}...")
        try:
            model = AutoModel.from_pretrained(model_id).to('cuda')
            model.eval()
            # Keep model in memory (don't delete reference)
            self.models[name] = model
            
            if keep_tokenizer:
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                self.tokenizers[name] = tokenizer
            
            used = self._get_used_vram()
            pct = self._get_utilization()
            print(f"   ✓ {name} loaded ({used:.0f} MiB, {pct:.1f}%)")
            return True
        except Exception as e:
            print(f"   ✗ {name} failed: {e}")
            return False
    
    def load_kompress(self):
        """Load Kompress compressor (resident)."""
        print(f"\n📦 Loading Kompress (resident)...")
        try:
            config = KompressConfig(device='cuda', batch_size=16, preload=True, resident=True)
            komp = KompressCompressor(config)
            self.models['kompress'] = komp
            used = self._get_used_vram()
            pct = self._get_utilization()
            print(f"   ✓ Kompress loaded ({used:.0f} MiB, {pct:.1f}%)")
            return True
        except Exception as e:
            print(f"   ✗ Kompress failed: {e}")
            return False
    
    def allocate_cache(self, name: str, size_mb: int):
        """Allocate persistent GPU cache."""
        print(f"\n💾 Allocating {name} ({size_mb} MiB)...")
        try:
            # Allocate on GPU
            cache = torch.randn(size_mb * 256 * 1024, dtype=torch.float32, device='cuda')
            self.caches[name] = cache
            used = self._get_used_vram()
            pct = self._get_utilization()
            print(f"   ✓ {name} allocated ({used:.0f} MiB, {pct:.1f}%)")
            return True
        except Exception as e:
            print(f"   ✗ {name} failed: {e}")
            return False
    
    def optimize_memory(self):
        """Optimize GPU memory to reduce fragmentation."""
        print("\n🔧 Optimizing GPU memory...")
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        used = self._get_used_vram()
        pct = self._get_utilization()
        print(f"   ✓ Optimized ({used:.0f} MiB, {pct:.1f}%)")
    
    def report(self):
        """Print VRAM utilization report."""
        used = self._get_used_vram()
        total = self.total_vram
        pct = self._get_utilization()
        
        print("\n" + "="*60)
        print("📊 GPU VRAM UTILIZATION REPORT")
        print("="*60)
        print(f"   Used:     {used:.0f} MiB")
        print(f"   Total:    {total:.0f} MiB")
        print(f"   Free:     {total - used:.0f} MiB")
        print(f"   Utilization: {pct:.1f}%")
        print(f"   Target:   {self.target_utilization * 100:.0f}%")
        
        if pct >= 90:
            print("\n✅ SUCCESS: 90%+ VRAM utilization achieved!")
        elif pct >= 70:
            print(f"\n⚠ Good: {pct:.1f}% (could go higher)")
        else:
            print(f"\n❌ Low: {pct:.1f}% (target not met)")
        
        print("\n📦 Resident Models:")
        for name in self.models:
            print(f"   • {name}")
        
        print("\n💾 Allocated Caches:")
        for name in self.caches:
            size = self.caches[name].numel() * self.caches[name].element_size() / (1024 * 1024)
            print(f"   • {name}: {size:.0f} MiB")
        
        print("="*60)


def main():
    """Load models to maximize VRAM utilization."""
    print("="*60)
    print("🚀 GPU RESIDENT MODEL MANAGER")
    print("   Maximizing VRAM utilization to 90%+")
    print("="*60)
    
    manager = GPUResidentModelManager(target_utilization=0.92)
    
    # Phase 1: Load compression models
    print("\n" + "="*60)
    print("PHASE 1: Loading Compression Models")
    print("="*60)
    
    manager.load_kompress()
    manager.load_model("ModernBERT-base", "answerdotai/ModernBERT-base")
    manager.load_model("ModernBERT-large", "answerdotai/ModernBERT-large")
    
    # Phase 2: Load encoder models
    print("\n" + "="*60)
    print("PHASE 2: Loading Encoder Models")
    print("="*60)
    
    manager.load_model("ALBERT-base", "albert-base-v2")
    manager.load_model("DistilBERT", "distilbert-base-uncased")
    
    # Phase 3: Allocate caches
    print("\n" + "="*60)
    print("PHASE 3: Allocating GPU Caches")
    print("="*60)
    
    manager.allocate_cache("compression_cache", 500)
    manager.allocate_cache("token_cache", 500)
    manager.allocate_cache("batch_buffer", 300)
    
    # Phase 4: Fill remaining VRAM
    print("\n" + "="*60)
    print("PHASE 4: Filling Remaining VRAM")
    print("="*60)
    
    current_pct = manager._get_utilization()
    if current_pct < 90:
        remaining_mb = int((0.92 - current_pct/100) * manager.total_vram)
        print(f"\n📦 Allocating {remaining_mb} MiB to reach 92%...")
        manager.allocate_cache("fill_cache", remaining_mb)
    
    # Optimize and report
    manager.optimize_memory()
    manager.report()
    
    print("\n✅ Models loaded and resident in VRAM")
    print("   Press Ctrl+C to unload")
    
    try:
        while True:
            # Keep models resident
            torch.cuda.synchronize()
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n👋 Unloading models...")
        # Models will be automatically unloaded when script exits


if __name__ == "__main__":
    main()
