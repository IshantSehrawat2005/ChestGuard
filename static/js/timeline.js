/**
 * ChestGuard NeuralScan — Timeline
 * Temporal progression tracking UI.
 */

async function loadTimeline() {
    try {
        const response = await fetch('/api/temporal/progression');
        const data = await response.json();
        
        if (!data.has_data) {
            // Show empty state (already in HTML)
            return;
        }
        
        if (data.scan_count < 2) {
            const container = document.getElementById('timeline-content');
            container.innerHTML = `
                <div class="timeline-empty">
                    <i class="fas fa-clock-rotate-left"></i>
                    <p>You have <strong>1 scan</strong> recorded.</p>
                    <p class="hint">Upload and analyze another X-ray to see progression tracking.</p>
                    <a href="#upload-section" class="btn btn-outline btn-sm">
                        <i class="fas fa-plus"></i> Add Another Scan
                    </a>
                </div>
            `;
            return;
        }
        
        // Render timeline chart
        if (data.timeline_chart) {
            renderTimelineChart(data.timeline_chart);
        }
        
        // Render alerts
        renderTimelineAlerts(data.alerts);
        
        // Update scan count stat
        const statEl = document.getElementById('stat-scans-value');
        if (statEl) statEl.textContent = data.scan_count;
        
    } catch (error) {
        console.error('Timeline load error:', error);
    }
}

function renderTimelineAlerts(alerts) {
    const container = document.getElementById('timeline-alerts');
    if (!container) return;
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="empty-text">No significant changes detected between scans.</p>';
        return;
    }
    
    container.innerHTML = '';
    
    alerts.forEach(alert => {
        const alertEl = document.createElement('div');
        alertEl.className = `timeline-alert ${alert.type}`;
        
        const icon = alert.type === 'warning' 
            ? 'fa-arrow-trend-up' 
            : 'fa-arrow-trend-down';
        const color = alert.type === 'warning' ? 'var(--warning)' : 'var(--success)';
        
        alertEl.innerHTML = `
            <i class="fas ${icon}" style="color:${color};margin-top:2px;"></i>
            <span>${alert.message}</span>
        `;
        
        container.appendChild(alertEl);
    });
}

// Scan comparison cards
function renderScanComparison(scans) {
    if (!scans || scans.length < 2) return;
    
    const latest = scans[scans.length - 1];
    const previous = scans[scans.length - 2];
    
    const scoreChange = latest.neural_score - previous.neural_score;
    const direction = scoreChange > 0 ? 'increased' : 'decreased';
    const color = scoreChange > 0 ? 'var(--danger)' : 'var(--success)';
    
    return `
        <div class="scan-comparison" style="padding:16px;border-radius:12px;background:var(--bg-card);border:1px solid var(--border);margin-top:16px;">
            <h4 style="margin-bottom:12px;font-size:0.95rem;">
                <i class="fas fa-code-compare" style="color:var(--accent-primary)"></i>
                Latest vs Previous
            </h4>
            <p style="font-size:0.85rem;color:var(--text-secondary);">
                NeuralScore™ <strong style="color:${color}">${direction}</strong> by 
                <strong style="color:${color}">${Math.abs(scoreChange).toFixed(1)}</strong> points
                (${previous.neural_score.toFixed(1)} → ${latest.neural_score.toFixed(1)})
            </p>
        </div>
    `;
}
