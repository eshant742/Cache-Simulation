# Cache Eviction Algorithm Benchmark: TD-LFU

A research simulation comparing **LRU**, **LFU**, and a proposed **Time-Decayed LFU (TD-LFU)** cache eviction algorithm under realistic web traffic conditions with trend shifts and cache pollution.

## Author
- **Eshant Gupta** (LCB2023016) — IIIT Lucknow
- **Faculty Supervisor:** Dr. Sushil Kumar Tiwari — IIIT Lucknow

## Overview

Traditional cache eviction algorithms have known weaknesses:
- **LRU (Least Recently Used):** Suffers from *cache pollution* — a burst of one-time bot requests flushes popular data from memory.
- **LFU (Least Frequently Used):** Suffers from *cache bloat* — historically popular items stay cached forever, even after they stop being relevant.

**TD-LFU** introduces three innovations to solve both problems simultaneously:

1. **Periodic Halving:** Every 5,000 requests, all frequency scores are halved. Old viral items gradually lose their advantage, allowing new trends to take over.
2. **Global Frequency Memory:** Unlike standard LFU which resets an item's count on re-admission, TD-LFU remembers the access history of all items globally. Temporarily evicted popular items return with their accumulated score.
3. **Admission Filter:** A new item is only admitted if its frequency beats the eviction victim's frequency. One-time bot requests (frequency = 1) cannot evict established popular items.

## Results

Workload: 100,000 requests | 4 Trend Shifts | 20% Cache Pollution (Bot Noise)

| Capacity | LRU Hit% | LFU Hit% | TD-LFU Hit% | Improvement |
|----------|----------|----------|-------------|-------------|
| 50       | 13.53    | 7.23     | **24.99**   | +11.46%     |
| 100      | 18.76    | 10.17    | **29.78**   | +11.01%     |
| 500      | 32.96    | 22.25    | **41.49**   | +8.52%      |
| 1000     | 39.93    | 30.17    | **46.18**   | +6.25%      |
| 2000     | 47.53    | 39.00    | **50.67**   | +3.14%      |

TD-LFU outperforms both baselines at every tested capacity, with the largest gains under tight memory constraints where eviction policy matters most.

## How to Run

### Prerequisites
- Python 3.7+
- NumPy (`pip install numpy`)

### Run the Simulation
```bash
python cache_simulation.py
```

## Files
- `cache_simulation.py` — Python simulation benchmarking LRU, LFU, and TD-LFU
- `research_paper.tex` — IEEE-format research paper (compile with LaTeX/Overleaf)

## License
This project is part of the Research Internship course (6th Semester) at IIIT Lucknow.
