#!/usr/bin/env python3
"""
Fractal Web Honeypot - Traps web crawlers in an infinite fractal structure
"""

from flask import Flask, request, render_template_string, abort, make_response
import hashlib
import time
import random
import json
import os
from datetime import datetime
from urllib.parse import quote

app = Flask(__name__)

# Configuration
CONFIG = {
    'N': 8,  # Number of links per page
    'branching_factor': 3,  # Controls how many levels to generate before repeating
    'max_depth': 100,  # Maximum depth to generate unique paths
    'delay_min': 0.1,  # Minimum delay in seconds
    'delay_max': 2.0,  # Maximum delay in seconds
    'log_file': 'honeypot.log',
    'blocked_user_agents': [
        'scrapy',
        'httrack',
        'webbandit',
        'sqlmap',
        'nikto',
        'nessus',
        'acunetix',
        'netsparker',
        'w3af'
    ],
    'fake_content': True,  # Generate fake content to look realistic
}

# In-memory store for tracking crawlers
crawler_tracker = {}

# HTML templates
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if depth > 0 %}Fractal Research - Level {{ depth }}{% else %}Fractal Mathematics Research Center{% endif %}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 20px;
        }
        h1 {
            color: #4a5568;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #718096;
            font-size: 1.1em;
        }
        .fractal-info {
            background: #f7fafc;
            border-left: 4px solid #4299e1;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .links-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        .fractal-link {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-decoration: none;
            color: #2d3748;
            border: 2px solid #cbd5e0;
            transition: all 0.3s ease;
            display: block;
        }
        .fractal-link:hover {
            border-color: #4299e1;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
        }
        .link-title {
            font-weight: bold;
            color: #2b6cb0;
            margin-bottom: 5px;
        }
        .link-desc {
            font-size: 0.9em;
            color: #718096;
        }
        .stats {
            background: #e6fffa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #81e6d9;
        }
        .warning {
            background: #fff5f5;
            border: 1px solid #fc8181;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            color: #c53030;
        }
        .loading {
            text-align: center;
            color: #4a5568;
            font-style: italic;
        }
    </style>
    <script>
        // Simulate loading delay for realism
        window.addEventListener('load', function() {
            setTimeout(function() {
                document.getElementById('content').style.opacity = '1';
            }, 300);
        });
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{% if depth > 0 %}Fractal Research - Level {{ depth }}{% else %}Fractal Mathematics Research Center{% endif %}</h1>
            <div class="subtitle">Exploring infinite complexity through Mandelbrot and Julia sets</div>
        </div>
        
        <div class="fractal-info">
            <strong>Current Coordinates:</strong> {{ path }}<br>
            <strong>Zoom Level:</strong> 1e-{{ depth * 15 }}<br>
            <strong>Iterations:</strong> {{ (depth + 1) * 1000 }}
        </div>
        
        {% if fake_content %}
        <p>This region of the Mandelbrot set exhibits {{ descriptors|random }} behavior. 
        The fractal dimension at this zoom level is approximately {{ (1.5 + depth * 0.1)|round(2) }}.</p>
        
        <div class="stats">
            <strong>Research Data:</strong><br>
            • Coordinates analyzed: {{ depth * 1000 }}<br>
            • Processing time: {{ (depth * 0.5)|round(2) }} ms<br>
            • Memory usage: {{ (50 + depth * 2) }} MB<br>
            • Similarity index: {{ (95 - depth * 0.5)|round(1) }}%
        </div>
        {% endif %}
        
        <div id="content" style="opacity: 0; transition: opacity 0.5s;">
            <h2>Continue Exploration</h2>
            <p>Select a region to explore further details of the fractal structure:</p>
            
            <div class="links-grid">
                {% for i in range(1, N+1) %}
                <a href="{{ links[i-1] }}" class="fractal-link">
                    <div class="link-title">Region {{ roman_numerals[i-1] }}</div>
                    <div class="link-desc">
                        Zoom factor: {{ 2**i }}x<br>
                        Complexity: {{ complexity_levels[i-1] }}<br>
                        Coordinates: {{ coordinates[i-1] }}
                    </div>
                </a>
                {% endfor %}
            </div>
            
            <div class="warning">
                <strong>⚠️ Warning:</strong> This research portal contains recursively generated content. 
                Bots and automated crawlers may experience infinite traversal.
            </div>
            
            {% if depth > 5 %}
            <div class="loading">
                <em>Computing next fractal iteration... This may take a moment.</em>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# Helper functions
def generate_path_hash(path, salt=None):
    """Generate a unique hash for a path"""
    if salt is None:
        salt = str(time.time())
    return hashlib.sha256(f"{path}:{salt}".encode()).hexdigest()[:16]

def should_block_request(user_agent):
    """Check if request should be blocked based on user agent"""
    if not user_agent:
        return False
    user_agent = user_agent.lower()
    for blocked in CONFIG['blocked_user_agents']:
        if blocked in user_agent:
            return True
    return False

def log_request(path, ip, user_agent, depth):
    """Log request to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | IP: {ip} | Depth: {depth} | Path: {path} | UA: {user_agent[:100]}\n"
    
    # Write to log file
    with open(CONFIG['log_file'], 'a') as f:
        f.write(log_entry)
    
    # Print to console
    print(log_entry.strip())
    
    # Track crawler
    crawler_key = f"{ip}:{user_agent}"
    if crawler_key not in crawler_tracker:
        crawler_tracker[crawler_key] = {
            'first_seen': timestamp,
            'last_seen': timestamp,
            'max_depth': depth,
            'visit_count': 1,
            'paths': [path]
        }
    else:
        crawler_tracker[crawler_key]['last_seen'] = timestamp
        crawler_tracker[crawler_key]['max_depth'] = max(
            crawler_tracker[crawler_key]['max_depth'], depth
        )
        crawler_tracker[crawler_key]['visit_count'] += 1
        crawler_tracker[crawler_key]['paths'].append(path)

def generate_fractal_links(path, depth):
    """Generate N links for the current page"""
    links = []
    roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'][:CONFIG['N']]
    complexity_levels = ['Low', 'Medium', 'High', 'Very High', 'Extreme', 'Chaotic', 'Infinite'][:CONFIG['N']]
    descriptors = ['quasi-self-similar', 'self-similar', 'scale-invariant', 'recursive', 
                   'chaotic', 'complex', 'detailed', 'intricate', 'beautiful']
    coordinates = []
    
    for i in range(1, CONFIG['N'] + 1):
        # Create new path by appending segment
        if depth < CONFIG['max_depth']:
            new_path = f"{path}/{generate_path_hash(path, i)}" if path else generate_path_hash('root', i)
        else:
            # After max depth, start recycling paths to create cycles
            cycle_index = (depth * CONFIG['N'] + i) % (CONFIG['max_depth'] * CONFIG['N'])
            new_path = f"cycle/{cycle_index}"
        
        links.append(f"/explore/{new_path}")
        
        # Generate fake coordinates
        coord_x = round(-0.743643 + (random.random() - 0.5) * (0.1 / (depth + 1)), 10)
        coord_y = round(0.131825 + (random.random() - 0.5) * (0.1 / (depth + 1)), 10)
        coordinates.append(f"{coord_x:.6f}, {coord_y:.6f}")
    
    return links, roman_numerals, complexity_levels, descriptors, coordinates

def add_delay(depth):
    """Add realistic delay based on depth"""
    if depth > 3:
        delay = random.uniform(CONFIG['delay_min'], CONFIG['delay_max'])
        time.sleep(delay)

@app.route('/')
def index():
    """Main entry point"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    if should_block_request(user_agent):
        abort(403)
    
    log_request('/', ip, user_agent, 0)
    
    links, roman_numerals, complexity_levels, descriptors, coordinates = generate_fractal_links('', 0)
    
    return render_template_string(
        MAIN_TEMPLATE,
        N=CONFIG['N'],
        depth=0,
        path='root',
        links=links,
        roman_numerals=roman_numerals,
        complexity_levels=complexity_levels,
        descriptors=descriptors,
        coordinates=coordinates,
        fake_content=CONFIG['fake_content']
    )

@app.route('/explore/')
@app.route('/explore/<path:fractal_path>')
def explore(fractal_path=''):
    """Fractal exploration pages - infinite recursion"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    if should_block_request(user_agent):
        abort(403)
    
    # Calculate depth from path
    depth = fractal_path.count('/') + 1 if fractal_path else 1
    
    # Log the request
    log_request(fractal_path, ip, user_agent, depth)
    
    # Add realistic delay for deeper levels
    add_delay(depth)
    
    # Generate links for next level
    links, roman_numerals, complexity_levels, descriptors, coordinates = generate_fractal_links(
        fractal_path, depth
    )
    
    return render_template_string(
        MAIN_TEMPLATE,
        N=CONFIG['N'],
        depth=depth,
        path=fractal_path or 'root',
        links=links,
        roman_numerals=roman_numerals,
        complexity_levels=complexity_levels,
        descriptors=descriptors,
        coordinates=coordinates,
        fake_content=CONFIG['fake_content']
    )

@app.route('/robots.txt')
def robots():
    """Misleading robots.txt to attract crawlers"""
    response = make_response("""User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /explore/
Allow: /research/
Sitemap: /sitemap.xml
""")
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/sitemap.xml')
def sitemap():
    """Dynamic sitemap that references infinite paths"""
    urls = ['/']
    for i in range(100):  # Generate many URLs to look legitimate
        path = generate_path_hash(f"sitemap_{i}")
        urls.append(f"/explore/{path}")
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        sitemap_xml += f'  <url>\n    <loc>http://localhost:5000{url}</loc>\n    <priority>0.8</priority>\n  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/stats')
def stats():
    """Display statistics about trapped crawlers (for monitoring)"""
    stats_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Honeypot Statistics</title>
    <style>
        body { font-family: monospace; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
    </head>
    <body>
        <h1>Fractal Honeypot Statistics</h1>
        <p>Total unique crawlers: {count}</p>
        <table>
            <tr>
                <th>IP</th>
                <th>User Agent</th>
                <th>First Seen</th>
                <th>Last Seen</th>
                <th>Max Depth</th>
                <th>Visit Count</th>
            </tr>
    """
    
    for key, data in crawler_tracker.items():
        ip, ua = key.split(':', 1)
        stats_html += f"""
            <tr>
                <td>{ip}</td>
                <td>{ua[:50]}</td>
                <td>{data['first_seen']}</td>
                <td>{data['last_seen']}</td>
                <td>{data['max_depth']}</td>
                <td>{data['visit_count']}</td>
            </tr>
        """
    
    stats_html += """
        </table>
        <br>
        <a href="/">Back to honeypot</a>
    </body>
    </html>
    """
    
    return stats_html.format(count=len(crawler_tracker))

@app.errorhandler(403)
def forbidden(e):
    """Custom 403 page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Access Denied</title></head>
    <body>
        <h1>403 - Access Denied</h1>
        <p>Automated crawling of this research site is not permitted.</p>
        <p>Please contact the administrator for access credentials.</p>
    </body>
    </html>
    ''', 403

@app.errorhandler(404)
def not_found(e):
    """Redirect 404 to a new fractal path"""
    new_path = generate_path_hash('404_' + str(time.time()))
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/explore/{new_path}" />
    </head>
    <body>
        <p>Redirecting to research page...</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    # Create log file if it doesn't exist
    if not os.path.exists(CONFIG['log_file']):
        with open(CONFIG['log_file'], 'w') as f:
            f.write("Fractal Honeypot Access Log\n")
            f.write("=" * 50 + "\n")
    
    print("=" * 60)
    print("Fractal Web Honeypot Starting...")
    print(f"• Access at: http://localhost:5000/")
    print(f"• Statistics: http://localhost:5000/stats")
    print(f"• Log file: {CONFIG['log_file']}")
    print(f"• Links per page: {CONFIG['N']}")
    print(f"• Max unique depth: {CONFIG['max_depth']}")
    print("=" * 60)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )