# Fractal Web Honeypot Collection

Two Python-based honeypots that trap web crawlers in infinite fractal recursion structures, inspired by mathematical chaos theory.

---

## Overview

This project contains two web honeypots designed to exploit crawler traversal behavior using mathematically inspired infinite structures derived from fractal geometry.

- schemata.py — Research panel
- tsukuyomi.py — Minimalist and stateless

Both systems create the illusion of infinite exploration while remaining computationally bounded.

---
## Mathematical Foundation

### Mandelbrot Set

Both honeypots simulate exploration of the Mandelbrot Set, defined by the recursive equation:

    z_{n+1} = z_n^2 + c

Where z and c are complex numbers. The Mandelbrot set consists of all values of c for which the orbit of z (starting at 0) remains bounded.

Key properties exploited:
- Infinite complexity
- Self-similarity
- Boundary complexity
- Uncomputable regions

### Julia Sets

Julia sets are closely related to the Mandelbrot set. Each point c in the Mandelbrot set corresponds to a unique Julia set:

    J(c) = { z0 in C : zn remains bounded under zn+1 = zn^2 + c }

---

## Technical Implementation

### schemata.py Architecture

Request Handler
- Path generation using SHA-256
- Depth-limited branching
- Cycle detection

Crawler Tracking
- IP and User-Agent logging
- Depth monitoring
- Traversal pattern analysis

Realistic Content Generator
- Fractal coordinate synthesis
- Mathematical narrative generation
- Progressive zoom illusion

Key features:
- Non-guessable URLs via hashing
- Exponential traversal growth
- Infinite cycling without infinite storage
- Configurable artificial delays

### tsukuyomi.py Architecture

Deterministic Generator
- Seed-based path creation
- Hash chaining
- Constant memory usage

Illusion Engine
- Mathematical coordinate generation
- Zoom progression
- Infinite sitemap illusion

Efficiency features:
- Fully stateless
- Minimal HTML responses
- Append-only logging

---

## Fractal Coordinate System

Both scripts operate around the Seahorse Valley region of the Mandelbrot set. Base coordinates: (-0.743643, 0.131825)

This region supports infinite zoom, complex structures, and lies near the boundary of the main cardioid.

---

## Trapping Mechanisms

1. Infinite sitemap chains
2. Exponential recursive link structures
3. Hash-based traversal cycles

---

## Performance Characteristics

schemata.py:
- Memory: O(k)
- CPU: Medium
- Throughput: ~100–500 req/s

tsukuyomi.py:
- Memory: O(1)
- CPU: Low
- Throughput: ~1000–5000 req/s

---
## Configuration

schemata.py:
- N: links per page
- max_depth: depth before cycling
- delay_min / delay_max
- log_file
- fake_content toggle

tsukuyomi.py:
- N
- delay_min / delay_max
- log_file

---

## Detection Capabilities

Detects:
- Blind crawlers
- Recursive scanners
- Sitemap-driven bots
- Persistent traversal agents

---

## References

- Mandelbrot, B. B. — The Fractal Geometry of Nature
- Douady & Hubbard — Complex Polynomial Dynamics
- Peitgen & Richter — The Beauty of Fractals
- Devaney — Chaotic Dynamical Systems

