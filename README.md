# Fractal Web Honeypot Collection

Two Python-based honeypots that trap web crawlers in infinite fractal recursion structures, inspired by mathematical chaos theory.

## Scripts

### 1. **schemata.py** - Feature-Rich Trapping System
A sophisticated honeypot with monitoring, logging, and realistic fractal simulation. Named after "schemata" (plural of schema) representing the underlying patterns that guide the infinite structure.

### 2. **tsukuyomi.py** - Minimal Infinite Trap
An ultra-efficient honeypot named after the Japanese moon god Tsukuyomi, representing endless cycles and illusions. Uses virtually no server resources while creating infinite recursion.

## Mathematical Foundation

### Mandelbrot Set
Both honeypots simulate exploration of the **Mandelbrot Set**, a famous fractal defined by the simple recursive equation: _zₙ₊₁ = zₙ² + c_ where `z` and `c` are complex numbers. The set consists of all `c` values for which the orbit of `z` (starting at 0) remains bounded.

**Key Properties Exploited:**
- **Infinite Complexity**: No matter how much you zoom, new patterns emerge
- **Self-Similarity**: Similar structures appear at different scales
- **Boundary Complexity**: The edge of the set is infinitely intricate
- **Uncomputable Regions**: Some areas require infinite computation to determine membership

### Julia Sets
Closely related to the Mandelbrot set, **Julia Sets** are created by fixing `c` and varying the starting point `z₀`. Each point in the Mandelbrot set corresponds to a different Julia set: _J(c) = {z₀ ∈ ℂ : zₙ remains bounded under zₙ₊₁ = zₙ² + c}_


## Technical Implementation

### schemata.py Architecture
```
┌─────────────────────────────────────────────────┐
│ Request Handler                                 │
├─────────────────────────────────────────────────┤
│ Path Generation Engine                          │
│ • SHA-256 based unique path creation            │
│ • Depth-limited branching (N=8)                 │
│ • Cycle detection and infinite loop creation    │
├─────────────────────────────────────────────────┤
│ Crawler Tracking System                         │
│ • IP/UA logging                                 │
│ • Depth monitoring                              │
│ • Visit pattern analysis                        │
├─────────────────────────────────────────────────┤
│ Realistic Content Generator                     │
│ • Fractal coordinate generation                 │
│ • Mathematical description generation           │
│ • Progressively increasing "zoom" levels        │
└─────────────────────────────────────────────────┘
```

**Key Features:**
- **Path Hashing**: `sha256(path:salt:depth)` creates unique, non-guessable URLs
- **Exponential Growth**: Each page generates N links, creating N^depth total paths
- **Cycle Creation**: After reaching `max_depth`, paths recycle into infinite loops
- **Resource Monitoring**: Tracks crawler behavior without significant memory overhead
- **Realistic Delays**: Simulates computational load with configurable timeouts

### tsukuyomi.py
```
┌─────────────────────────────────────────────────┐
│ Deterministic Generator                         │
│ • Seed-based path generation                    │
│ • Hash chaining for infinite recursion          │
│ • O(1) memory usage                             │
├─────────────────────────────────────────────────┤
│ Illusion Engine                                 │
│ • Mathematical coordinate generation            │
│ • Zoom factor progression                       │
│ • Infinite sitemap generation                   │
└─────────────────────────────────────────────────┘
```


**Efficiency Innovations:**
- **Stateless Design**: No tracking of crawler paths or history
- **Deterministic Paths**: `next_seed = sha256(current_seed + i + depth)`
- **Mathematical Coordinates**: Generated on-the-fly using hash functions
- **Minimal HTML**: <5KB responses with inline CSS
- **Log Rotation**: Single-file append-only logging

## Fractal Coordinate Systems

Both scripts use coordinates from the **Seahorse Valley** region of the Mandelbrot set: Base Coordinates: (-0.743643, 0.131825)

This region exhibits:
- **Deep Zoom Capability**: Can be magnified infinitely
- **Complex Structures**: Spirals, seahorses, and mini-Mandelbrots
- **Mathematical Significance**: Located near the boundary of the main cardioid

### Zoom Progression Algorithm
```python
def generate_coordinates(seed, depth, i):
    base_x, base_y = -0.743643, 0.131825
    zoom_factor = 2 ** (depth // 10)
    
    # Add pseudorandom offsets based on hash
    offset_x = (hash(seed + "x") % 1000 - 500) / (1000 * zoom_factor)
    offset_y = (hash(seed + "y") % 1000 - 500) / (1000 * zoom_factor)
    
    return (base_x + offset_x, base_y + offset_y)
```

### Trapping Mechanisms

1. Infinite Sitemap Generation
```
sitemap-index.xml → sitemap-1.xml → sitemap-2.xml → ...
                  ↘ page-1.html   ↘ page-2.html   ↘ ...
```
2. Recursive Link Structure
```
Level 0: 1 page with N links
Level 1: N pages, each with N links (N² total)
Level 2: N² pages, each with N links (N³ total)
...
Level d: N^d pages (exponential growth)
```
3. Hash-Based Cycle Creation (After reaching maximum configured depth, paths begin to cycle. This creates infinite traversal without infinite unique pages.)
```
Path A → Path B → Path C → Path D → Path A (cycle)
```

[WORK IN PROGRESS]
