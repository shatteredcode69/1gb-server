from flask import Flask, jsonify, render_template
import psutil
import os
from datetime import datetime
import platform
import time

app = Flask(__name__)

metrics_history = []
start_time = time.time()

def get_system_metrics():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    cpu_percent = psutil.cpu_percent(interval=0.1)
    process = psutil.Process()
    process_memory = process.memory_info().rss / 1024 / 1024
    uptime = time.time() - start_time
    
    return {
        'memory': {
            'total': round(memory.total / 1024 / 1024, 2),
            'used': round(memory.used / 1024 / 1024, 2),
            'available': round(memory.available / 1024 / 1024, 2),
            'percent': memory.percent
        },
        'disk': {
            'total': round(disk.total / 1024 / 1024 / 1024, 2),
            'used': round(disk.used / 1024 / 1024 / 1024, 2),
            'free': round(disk.free / 1024 / 1024 / 1024, 2),
            'percent': disk.percent
        },
        'cpu': {
            'percent': cpu_percent,
            'cores': psutil.cpu_count()
        },
        'process': {
            'memory_mb': round(process_memory, 2),
            'threads': process.num_threads()
        },
        'system': {
            'platform': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'python_version': platform.python_version()
        },
        'uptime': uptime
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/api/v1/health')
def health():
    metrics = get_system_metrics()
    process = psutil.Process()
    
    status = 'healthy'
    if metrics['memory']['percent'] > 90:
        status = 'warning'
    
    return jsonify({
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'application_memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),  # NEW
        'memory_efficient': process.memory_info().rss < 1024 * 1024 * 512,  # Under 512MB
        'developer': 'Muhammad Abbas',
        'version': '1.0.0'
    })

@app.route('/api/v1/metrics')
def metrics():
    current_metrics = get_system_metrics()
    metrics_history.append({
        'timestamp': datetime.now().isoformat(),
        'memory': current_metrics['memory']['percent'],
        'cpu': current_metrics['cpu']['percent']
    })
    
    if len(metrics_history) > 60:
        metrics_history.pop(0)
    
    return jsonify({
        'current': current_metrics,
        'history': metrics_history
    })

@app.route('/api/v1/story')
def story():
    return jsonify({
        'title': 'The 1GB Server: A Developer\'s Journey',
        'author': 'Muhammad Abbas',
        'tagline': 'Building Excellence Under Constraint',
        'story': {
            'chapter_1': 'In a world obsessed with unlimited resources...',
            'chapter_2': 'One developer chose the path of optimization...',
            'chapter_3': 'And built something remarkable with just 1GB of RAM.',
            'moral': 'True engineering skill shines brightest under constraints.'
        },
        'stats': {
            'memory_budget': '1024 MB',
            'deployment_time': '<30 seconds',
            'uptime_target': '99.9%'
        }
    })

@app.route('/api/v1/Server')
def challenge():
    return jsonify({
        'name': '1GB Server',
        'objective': 'Build a production-grade system with only 1GB RAM',
        'components': [
            'Flask Web Application',
            'Real-time Monitoring Dashboard',
            'CI/CD Pipeline',
            'Zero-downtime Deployment',
            'Automatic Rollback',
            'Health Monitoring',
            'Performance Optimization'
        ],
        'skills_learned': [
            'Resource Optimization',
            'DevOps Best Practices',
            'System Monitoring',
            'Production Deployment',
            'Performance Tuning'
        ],
        'developer': {
            'name': 'Muhammad Abbas',
            'role': 'Aspiring Cloud Enthusiast'
        }
    })

@app.route('/api/v1/system')
def system():
    return jsonify(get_system_metrics())

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 1GB SERVER")
    print("="*60)
    print(f"👨‍💻 Developer: Muhammad Abbas")
    print(f"🎯 Mission: Production System on 1GB RAM")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
