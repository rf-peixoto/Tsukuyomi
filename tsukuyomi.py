#!/usr/bin/env python3
"""
Tsukuyomi Fractal-Honey Pot
"""
from flask import Flask, request
import hashlib
import time

app = Flask(__name__)

def infinite_html(seed, depth=0):
    """Generate infinite recursive HTML"""
    N = 5  # Links per page
    links = []
    
    for i in range(N):
        # Generate next seed deterministically
        next_seed = hashlib.md5(f"{seed}_{i}".encode()).hexdigest()[:10]
        links.append(f'<a href="/{next_seed}">Branch {next_seed}</a><br>')
    
    return f'''
    <html><body style="font-family: monospace">
        <h1>Branch {seed}</h1>
        <p>Depth: {depth}</p>
        {' '.join(links)}
        <p>Generated: {time.time()}</p>
    </body></html>
    '''

@app.route('/')
@app.route('/<seed>')
def trap(seed=None):
    """Infinite recursive trap"""
    if seed is None:
        seed = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    
    # Estimate depth from seed
    depth = int(seed[:4], 16) % 10000 if len(seed) >= 4 else 0
    
    return infinite_html(seed, depth)

if __name__ == '__main__':
    print("Tsukuyomi running at http://localhost:5000/")
    app.run(host='0.0.0.0', port=5000, debug=False)