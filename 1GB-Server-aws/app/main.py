from flask import Flask, jsonify, render_template
import psutil
import os
import platform
import time
from datetime import datetime

app = Flask(__name__)

metrics_history = []
start_time = time.time()

def get_disk_path():
    """Get appropriate disk path based on OS"""
    if platform.system() == 'Windows':
        return 'C:\\'
    else:
        return '/'  # Linux root partition

def get_network_io():
    """Get network I/O statistics"""
    net_io = psutil.net_io_counters()
    return {
        'bytes_sent': round(net_io.bytes_sent / 1024 / 1024, 2),  # MB
        'bytes_recv': round(net_io.bytes_recv / 1024 / 1024, 2),  # MB
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv
    }

def get_system_metrics():
    """Collect all system metrics"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(get_disk_path())
    cpu_percent = psutil.cpu_percent(interval=0.1)
    process = psutil.Process()
    process_memory = process.memory_info().rss / 1024 / 1024  # MB
    uptime = time.time() - start_time
    network = get_network_io()
    
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
        'network': network,
        'process': {
            'memory_mb': round(process_memory, 2),
            'threads': process.num_threads()
        },
        'system': {
            'platform': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'python_version': platform.python_version(),
            'hostname': platform.node()
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
    """Health check endpoint with 1GB RAM verification"""
    metrics = get_system_metrics()
    process = psutil.Process()
    app_memory_mb = round(process.memory_info().rss / 1024 / 1024, 2)
    
    # Determine health status
    status = 'healthy'
    if metrics['memory']['percent'] > 90:
        status = 'critical'
    elif metrics['memory']['percent'] > 80:
        status = 'warning'
    
    # 1GB RAM proof
    is_1gb_ready = app_memory_mb < 1024
    
    return jsonify({
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'application_memory_mb': app_memory_mb,
        'memory_budget_mb': 1024,
        'is_1gb_ready': is_1gb_ready,
        'headroom_mb': round(1024 - app_memory_mb, 2),
        'developer': 'Muhammad Abbas',
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'production')
    })

@app.route('/api/v1/metrics')
def metrics():
    """Real-time metrics with history"""
    current_metrics = get_system_metrics()
    
    # Store in history
    metrics_history.append({
        'timestamp': datetime.now().isoformat(),
        'memory': current_metrics['memory']['percent'],
        'cpu': current_metrics['cpu']['percent']
    })
    
    # Keep only last 60 entries (1 minute at 1s refresh)
    if len(metrics_history) > 60:
        metrics_history.pop(0)
    
    return jsonify({
        'current': current_metrics,
        'history': metrics_history
    })

@app.route('/api/v1/system')
def system():
    """Detailed system information"""
    return jsonify(get_system_metrics())

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 1GB SERVER - DEVELOPMENT MODE")
    print("="*60)
    print(f"👨‍💻 Developer: Muhammad Abbas")
    print(f"🎯 Mission: Production System on 1GB RAM")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
