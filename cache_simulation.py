import numpy as np
import collections

def generate_workload(num_requests, vocabulary_size, num_phases=4, alpha=0.9):
    """Generate a realistic workload with multiple trend shifts and continuous noise.
    
    alpha=0.9 creates a moderately skewed Zipfian distribution where 
    popularity is spread across more items (realistic for large-scale web traffic).
    """
    ranks = np.arange(1, vocabulary_size + 1)
    probabilities = 1.0 / (ranks ** alpha)
    probabilities /= np.sum(probabilities)
    
    phase_size = int(num_requests * 0.8 / num_phases)  # 80% popular traffic
    noise_size = int(num_requests * 0.2)                # 20% bot noise
    
    # Generate noise pool (unique random items outside the vocabulary)
    pollution = np.random.choice(
        np.arange(vocabulary_size + 1, vocabulary_size + 50001),
        size=noise_size, replace=True
    )
    noise_per_phase = noise_size // num_phases
    
    result = []
    for i in range(num_phases):
        # Each phase has a completely different set of popular items
        shift = (vocabulary_size // num_phases) * i
        shifted = (ranks + shift) % vocabulary_size + 1
        phase = np.random.choice(shifted, size=phase_size, p=probabilities)
        
        # Interleave noise into each phase
        noise_slice = pollution[i * noise_per_phase : (i + 1) * noise_per_phase]
        combined = np.concatenate((phase, noise_slice))
        np.random.shuffle(combined)
        result.append(combined)
    
    return np.concatenate(result)

class LRUCache:
    """Least Recently Used: evicts the item not accessed for the longest time."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = collections.OrderedDict()
        self.hits = 0

    def access(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
        else:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = True

class LFUCache:
    """Least Frequently Used: evicts the item with the lowest access count.
    Resets frequency to 1 when an evicted item re-enters (standard behavior)."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.freq = collections.defaultdict(int)
        self.hits = 0

    def access(self, key):
        if key in self.cache:
            self.freq[key] += 1
            self.hits += 1
        else:
            if len(self.cache) >= self.capacity:
                lfu_key = min(self.cache.keys(), key=lambda k: self.freq[k])
                del self.cache[lfu_key]
                del self.freq[lfu_key]
            self.cache[key] = True
            self.freq[key] = 1

class TDLFUCache:
    """Time-Decayed LFU with Periodic Halving, Global Frequency Memory,
    and Admission Filter.
    
    Three innovations over standard LFU:
    
    1. Periodic Halving: Every N requests, ALL frequency scores are halved
       simultaneously. This ensures old viral items gradually lose priority,
       unlike LFU where a historically popular item stays cached forever.
       
    2. Global Frequency Memory: Unlike LFU which resets an item's count to 1
       when re-admitted after eviction, TD-LFU remembers the global access
       history of ALL items (including non-cached ones). If a popular item
       is temporarily evicted, it returns with its accumulated (decayed)
       score, preventing unnecessary re-eviction.
       
    3. Admission Filter: A new item is only admitted to the cache if its
       observed global frequency is >= the eviction victim's frequency.
       This prevents cache pollution: one-time noise items (e.g., bot scans)
       cannot evict popular cached items because their frequency (1) is
       lower than any established cached item's frequency. Inspired by
       the TinyLFU admission policy used in production caches (Caffeine).
    """
    def __init__(self, capacity, halving_interval=5000):
        self.capacity = capacity
        self.cache = {}
        self.global_freq = {}  # Tracks frequency of ALL items, not just cached
        self.hits = 0
        self.time = 0
        self.halving_interval = halving_interval

    def access(self, key):
        self.time += 1
        
        # Periodic halving: decay ALL global frequencies simultaneously
        if self.time % self.halving_interval == 0:
            to_delete = []
            for k in self.global_freq:
                self.global_freq[k] *= 0.5
                # Clean up near-zero entries not in cache (memory optimization)
                if self.global_freq[k] < 0.01 and k not in self.cache:
                    to_delete.append(k)
            for k in to_delete:
                del self.global_freq[k]
        
        # Update global frequency BEFORE admission decision
        self.global_freq[key] = self.global_freq.get(key, 0) + 1.0
        
        if key in self.cache:
            self.hits += 1
        else:
            if len(self.cache) >= self.capacity:
                # Find the weakest cached item
                victim = min(self.cache.keys(), key=lambda k: self.global_freq.get(k, 0))
                
                # ADMISSION FILTER: only admit if new item's frequency
                # beats or equals the victim's frequency. This prevents
                # one-time noise items from evicting established items.
                if self.global_freq[key] >= self.global_freq.get(victim, 0):
                    del self.cache[victim]
                    self.cache[key] = True
                # else: REJECT admission. The new item's frequency is still
                # tracked globally, so if it's accessed again in the future,
                # its frequency will accumulate and it can earn admission.
            else:
                self.cache[key] = True

def run_simulation():
    print("=" * 70)
    print("  Cache Eviction Algorithm Benchmark: LRU vs LFU vs TD-LFU")
    print("  Workload: 100K requests | 4 Trend Shifts | 20% Cache Pollution")
    print("  TD-LFU: Periodic Halving + Global Memory + Admission Filter")
    print("=" * 70)
    
    reqs = generate_workload(100000, 10000, num_phases=4, alpha=0.9)
    caps = [50, 100, 200, 500, 1000, 2000, 3000, 5000]
    
    print(f"\n{'Capacity':<10} | {'LRU Hit%':<12} | {'LFU Hit%':<12} | {'TD-LFU Hit%':<12} | {'Improvement'}")
    print("-" * 72)
    
    for cap in caps:
        lru = LRUCache(cap)
        lfu = LFUCache(cap)
        tdlfu = TDLFUCache(cap, halving_interval=5000)
        
        for r in reqs:
            lru.access(r)
            lfu.access(r)
            tdlfu.access(r)
            
        lru_hit = (lru.hits / len(reqs)) * 100
        lfu_hit = (lfu.hits / len(reqs)) * 100
        tdlfu_hit = (tdlfu.hits / len(reqs)) * 100
        
        best_baseline = max(lru_hit, lfu_hit)
        improvement = tdlfu_hit - best_baseline
        sign = "+" if improvement >= 0 else ""
        
        print(f"{cap:<10} | {lru_hit:<12.2f} | {lfu_hit:<12.2f} | {tdlfu_hit:<12.2f} | {sign}{improvement:.2f}% vs best")

if __name__ == '__main__':
    run_simulation()
