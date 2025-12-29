let metricsChart;
let memoryPieChart;

const chartData = {
    labels: [],
    memory: [],
    cpu: []
};

// UI log buffer (what gets downloaded)
let logEntries = [];
let backendLogPollTimer = null;

function initCharts() {
    const ctx = document.getElementById('metricsChart').getContext('2d');
    metricsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Memory %',
                    data: chartData.memory,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2
                },
                {
                    label: 'CPU %',
                    data: chartData.cpu,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#f1f5f9' } } },
            scales: {
                y: { beginAtZero: true, max: 100, ticks: { color: '#64748b' }, grid: { color: 'rgba(59, 130, 246, 0.1)' } },
                x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(59, 130, 246, 0.1)' } }
            }
        }
    });

    const ctx2 = document.getElementById('memoryPieChart').getContext('2d');
    memoryPieChart = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: ['Used', 'Available'],
            datasets: [{
                data: [0, 100],
                backgroundColor: ['#3b82f6', 'rgba(59, 130, 246, 0.1)'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });
}

function addLogEntry(type, message) {
    const timestamp = new Date().toLocaleTimeString();
    const logClass = type.toLowerCase();
    const entry = `[${timestamp}] [${type}] ${message}`;

    const terminal = document.getElementById('logs-terminal');
    if (terminal) {
        terminal.innerHTML += `<div class="log-entry ${logClass}">${entry}</div>`;
        terminal.scrollTop = terminal.scrollHeight;
    }

    logEntries.push(entry);
    if (logEntries.length > 300) logEntries.shift();
}

function downloadLogs() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `1gb-server-logs-${timestamp}.txt`;

    const logContent = [
        '='.repeat(70),
        '1GB SERVER - SYSTEM LOGS',
        '='.repeat(70),
        `Generated: ${new Date().toLocaleString()}`,
        `Developer: Muhammad Abbas`,
        '='.repeat(70),
        '',
        ...logEntries,
        '',
        '='.repeat(70),
        'End of Logs'
    ].join('\n');

    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    addLogEntry('INFO', 'Logs downloaded successfully');
}

function formatUptime(seconds) {
    const s = Math.max(0, Math.floor(seconds || 0));
    const hours = Math.floor(s / 3600);
    const minutes = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    return `${hours}h ${minutes}m ${secs}s`;
}

function updateAppProof(current) {
    const appMb = Number(current?.process?.memory_mb ?? 0);

    // App footprint card
    const appValue = document.getElementById('appmem-value');
    const appBar = document.getElementById('appmem-bar');
    const appInfo = document.getElementById('appmem-info');

    if (appValue) appValue.textContent = `${appMb.toFixed(2)} MB`;

    const pct = Math.min((appMb / 1024) * 100, 100);
    if (appBar) appBar.style.width = `${pct}%`;

    const headroom = Math.max(0, 1024 - appMb);
    if (appInfo) appInfo.textContent = `Using ${pct.toFixed(1)}% of 1GB • Headroom ${headroom.toFixed(0)} MB`;

    // Proof bar section
    const fill = document.getElementById('app-budget-fill');
    const text = document.getElementById('app-budget-text');
    const head = document.getElementById('app-headroom-text');
    const pill = document.getElementById('proof-pill');

    if (fill) fill.style.width = `${pct}%`;
    if (text) text.textContent = `${appMb.toFixed(0)} MB / 1024 MB`;
    if (head) head.textContent = `Headroom: ${headroom.toFixed(0)} MB`;

    if (pill) {
        if (appMb <= 1024) {
            pill.textContent = '1GB READY';
            pill.className = 'proof-pill ok';
        } else {
            pill.textContent = 'OVER 1GB';
            pill.className = 'proof-pill bad';
        }
    }

    if (fill) {
        if (pct < 50) fill.style.background = 'linear-gradient(90deg, #10b981, #059669)';
        else if (pct < 75) fill.style.background = 'linear-gradient(90deg, #3b82f6, #2563eb)';
        else if (pct < 90) fill.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
        else fill.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
    }
}

async function updateMetrics() {
    try {
        const response = await fetch('/api/v1/metrics', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        const { current, history } = data;

        // Status badge (host memory-based)
        const statusEl = document.getElementById('status');
        const status = current.memory.percent > 90 ? 'critical' :
                       current.memory.percent > 80 ? 'warning' : 'healthy';
        if (statusEl) {
            statusEl.innerHTML = `<span class="pulse"></span> ${status.toUpperCase()}`;
            statusEl.className = `status-badge status-${status}`;
        }

        // Host Memory card
        const memVal = document.getElementById('memory-value');
        const memBar = document.getElementById('memory-bar');
        const memInfo = document.getElementById('memory-info');
        if (memVal) memVal.textContent = `${current.memory.used.toFixed(0)} MB`;
        if (memBar) memBar.style.width = `${current.memory.percent}%`;
        if (memInfo) memInfo.textContent = `${current.memory.available.toFixed(0)} MB available of ${current.memory.total.toFixed(0)} MB`;

        // CPU card
        const cpuVal = document.getElementById('cpu-value');
        const cpuBar = document.getElementById('cpu-bar');
        const cpuInfo = document.getElementById('cpu-info');
        if (cpuVal) cpuVal.textContent = `${current.cpu.percent.toFixed(1)}%`;
        if (cpuBar) cpuBar.style.width = `${current.cpu.percent}%`;
        if (cpuInfo) cpuInfo.textContent = `${current.cpu.cores} cores available`;

        // Disk card (safe if disk metrics unavailable)
        const diskVal = document.getElementById('disk-value');
        const diskBar = document.getElementById('disk-bar');
        const diskInfo = document.getElementById('disk-info');

        if (current.disk && current.disk.used != null && current.disk.percent != null) {
            if (diskVal) diskVal.textContent = `${current.disk.used.toFixed(1)} GB`;
            if (diskBar) diskBar.style.width = `${current.disk.percent}%`;
            if (diskInfo) diskInfo.textContent = `${current.disk.free.toFixed(1)} GB free of ${current.disk.total.toFixed(1)} GB`;
        } else {
            if (diskVal) diskVal.textContent = `-- GB`;
            if (diskBar) diskBar.style.width = `0%`;
            const err = current?.disk?.error ? ` (${current.disk.error})` : '';
            if (diskInfo) diskInfo.textContent = `Disk metrics unavailable${err}`;
        }

        // Uptime
        const upVal = document.getElementById('uptime-value');
        if (upVal) upVal.textContent = formatUptime(current.uptime);

        // App proof
        updateAppProof(current);

        // System info (must stay real-time at the bottom)
        const systemDetails = document.getElementById('system-details');
        if (systemDetails) {
            systemDetails.innerHTML = `
                <div class="info-item">
                    <div class="info-label">Platform</div>
                    <div class="info-value">${current.system.platform}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Release</div>
                    <div class="info-value">${current.system.release}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Machine</div>
                    <div class="info-value">${current.system.machine}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Python</div>
                    <div class="info-value">${current.system.python_version}</div>
                </div>
                <div class="info-item gold-ticket">
                    <div class="info-label">Process Memory (RSS) <span class="gold-pill">APP</span></div>
                    <div class="info-value gold-value">${current.process.memory_mb.toFixed(2)} MB</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Threads</div>
                    <div class="info-value">${current.process.threads}</div>
                </div>
            `;
        }

        // Charts (history is 60 points max)
        if (history && history.length > 0) {
            chartData.labels = history.map((_, i) => `-${history.length - i}s`);
            chartData.memory = history.map(h => h.memory);
            chartData.cpu = history.map(h => h.cpu);

            metricsChart.data.labels = chartData.labels;
            metricsChart.data.datasets[0].data = chartData.memory;
            metricsChart.data.datasets[1].data = chartData.cpu;
            metricsChart.update('none');
        }

        // Pie
        memoryPieChart.data.datasets[0].data = [current.memory.used, current.memory.available];
        memoryPieChart.update('none');

    } catch (error) {
        console.error('Error updating metrics:', error);
        addLogEntry('ERROR', `Failed to fetch metrics: ${error.message}`);
    }
}

function formatBackendLogLine(l) {
    const ts = l?.ts ? new Date(l.ts).toLocaleTimeString() : new Date().toLocaleTimeString();
    const level = (l?.level || 'INFO').toUpperCase();
    const msg = l?.message || '';
    const path = l?.path ? ` ${l.path}` : '';
    const status = (typeof l?.status_code === "number") ? ` status=${l.status_code}` : '';
    const dur = (typeof l?.duration_ms === "number") ? ` ${l.duration_ms.toFixed(2)}ms` : '';
    const rid = l?.request_id ? ` rid=${String(l.request_id).slice(0, 8)}` : '';
    return `[${ts}] [${level}] ${`${msg}${path}${status}${dur}${rid}`.trim()}`;
}

async function pollBackendLogs() {
    try {
        const res = await fetch('/api/v1/logs?limit=80', { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const logs = data?.logs || [];

        const terminal = document.getElementById('logs-terminal');
        if (terminal && terminal.dataset.cleared !== "true") {
            terminal.innerHTML = '';
            terminal.dataset.cleared = "true";
        }

        // Append only new lines to keep client lightweight for a 1GB server
        const existing = new Set(logEntries.slice(-200));
        for (const l of logs) {
            const line = formatBackendLogLine(l);
            if (!existing.has(line)) {
                const levelClass = (l?.level || 'INFO').toLowerCase();
                if (terminal) {
                    terminal.innerHTML += `<div class="log-entry ${levelClass}">${line}</div>`;
                    terminal.scrollTop = terminal.scrollHeight;
                }
                logEntries.push(line);
                if (logEntries.length > 300) logEntries.shift();
                existing.add(line);
            }
        }
    } catch (e) {
        addLogEntry('WARNING', `Backend logs unavailable: ${e.message}`);
    }
}

function startBackendLogs() {
    if (backendLogPollTimer) clearInterval(backendLogPollTimer);
    pollBackendLogs();
    backendLogPollTimer = setInterval(pollBackendLogs, 2000);
}

let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        if (metricsChart) metricsChart.resize();
        if (memoryPieChart) memoryPieChart.resize();
    }, 250);
});

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    updateMetrics();
    setInterval(updateMetrics, 1000); // real-time
    startBackendLogs();

    addLogEntry('INFO', 'Dashboard initialized (1s metrics + real backend logs)');
});
