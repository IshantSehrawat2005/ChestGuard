/**
 * ChestGuard NeuralScan — Charts
 * Chart.js visualizations for NeuralScore gauge, risk radar, and progression.
 */

// ═══════════════════════════════════════════
// NEURAL SCORE GAUGE
// ═══════════════════════════════════════════
function renderNeuralGauge(neuralScore) {
    const canvas = document.getElementById('neural-gauge');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const score = neuralScore.score;
    const tier = neuralScore.tier;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height - 20;
    const radius = 110;
    const lineWidth = 18;
    
    // Draw background arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI, false);
    ctx.lineWidth = lineWidth;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineCap = 'round';
    ctx.stroke();
    
    // Animate the score arc
    const targetAngle = Math.PI + (score / 100) * Math.PI;
    let currentAngle = Math.PI;
    const startTime = performance.now();
    const duration = 1500;
    
    function animateGauge(timestamp) {
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        
        currentAngle = Math.PI + eased * (score / 100) * Math.PI;
        
        // Clear and redraw background
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI, false);
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.lineCap = 'round';
        ctx.stroke();
        
        // Draw gradient arc
        const gradient = ctx.createLinearGradient(centerX - radius, centerY, centerX + radius, centerY);
        gradient.addColorStop(0, '#10b981');
        gradient.addColorStop(0.35, '#f59e0b');
        gradient.addColorStop(0.65, '#f97316');
        gradient.addColorStop(1, '#ef4444');
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, Math.PI, currentAngle, false);
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = gradient;
        ctx.lineCap = 'round';
        ctx.stroke();
        
        // Draw tick marks
        for (let i = 0; i <= 10; i++) {
            const angle = Math.PI + (i / 10) * Math.PI;
            const innerR = radius - lineWidth / 2 - 6;
            const outerR = radius - lineWidth / 2 - 2;
            
            ctx.beginPath();
            ctx.moveTo(
                centerX + Math.cos(angle) * innerR,
                centerY + Math.sin(angle) * innerR
            );
            ctx.lineTo(
                centerX + Math.cos(angle) * outerR,
                centerY + Math.sin(angle) * outerR
            );
            ctx.lineWidth = i % 5 === 0 ? 2 : 1;
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.stroke();
        }
        
        // Update score display
        const currentScore = Math.round(eased * score);
        document.getElementById('gauge-score').textContent = currentScore;
        document.getElementById('gauge-score').style.color = tier.color;
        
        if (progress < 1) {
            requestAnimationFrame(animateGauge);
        } else {
            document.getElementById('gauge-label').textContent = `${tier.level} Risk`;
            document.getElementById('gauge-label').style.color = tier.color;
            document.getElementById('gauge-action').textContent = neuralScore.action || '';
        }
    }
    
    requestAnimationFrame(animateGauge);
}

// ═══════════════════════════════════════════
// RISK RADAR CHART
// ═══════════════════════════════════════════
let riskChartInstance = null;

function renderRiskChart(neuralScore) {
    const canvas = document.getElementById('risk-radar-chart');
    if (!canvas) return;
    
    if (riskChartInstance) {
        riskChartInstance.destroy();
    }
    
    const breakdown = neuralScore.breakdown;
    if (!breakdown) return;
    
    const labels = Object.values(breakdown).map(d => d.label);
    const scores = Object.values(breakdown).map(d => d.score);
    
    riskChartInstance = new Chart(canvas, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Score',
                data: scores,
                fill: true,
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                borderColor: 'rgba(99, 102, 241, 0.8)',
                pointBackgroundColor: 'rgba(99, 102, 241, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 25,
                        color: 'rgba(148, 163, 184, 0.6)',
                        backdropColor: 'transparent',
                        font: { size: 10, family: "'JetBrains Mono'" }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.06)'
                    },
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.06)'
                    },
                    pointLabels: {
                        color: 'rgba(241, 245, 249, 0.8)',
                        font: { size: 11, family: "'Inter'", weight: '600' }
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(10, 16, 41, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(99, 102, 241, 0.3)',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { family: "'Inter'", weight: '700' },
                    bodyFont: { family: "'JetBrains Mono'" },
                    callbacks: {
                        label: (ctx) => `Score: ${ctx.raw}/100`
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

// ═══════════════════════════════════════════
// TIMELINE PROGRESSION CHART
// ═══════════════════════════════════════════
let timelineChartInstance = null;

function renderTimelineChart(timelineData) {
    const container = document.getElementById('timeline-content');
    if (!container) return;
    
    // Create canvas if not exists
    let canvas = container.querySelector('canvas');
    if (!canvas) {
        container.innerHTML = '<div class="timeline-chart-container"><canvas id="timeline-chart"></canvas></div>';
        canvas = document.getElementById('timeline-chart');
    }
    
    if (timelineChartInstance) {
        timelineChartInstance.destroy();
    }
    
    const colors = [
        { bg: 'rgba(99, 102, 241, 0.2)', border: 'rgba(99, 102, 241, 0.8)' },
        { bg: 'rgba(6, 182, 212, 0.2)', border: 'rgba(6, 182, 212, 0.8)' },
        { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgba(245, 158, 11, 0.8)' },
        { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgba(239, 68, 68, 0.8)' },
        { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgba(16, 185, 129, 0.8)' }
    ];
    
    const datasets = [];
    let i = 0;
    
    // Add condition datasets
    for (const [condition, values] of Object.entries(timelineData.condition_datasets)) {
        const colorSet = colors[i % colors.length];
        datasets.push({
            label: condition,
            data: values,
            fill: false,
            borderColor: colorSet.border,
            backgroundColor: colorSet.bg,
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7
        });
        i++;
    }
    
    // Add NeuralScore line
    datasets.push({
        label: 'NeuralScore™',
        data: timelineData.neural_scores,
        fill: false,
        borderColor: 'rgba(255, 255, 255, 0.6)',
        borderWidth: 3,
        borderDash: [8, 4],
        tension: 0.3,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: 'rectRounded'
    });
    
    timelineChartInstance = new Chart(canvas, {
        type: 'line',
        data: {
            labels: timelineData.labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: { color: 'rgba(148, 163, 184, 0.8)', font: { family: "'Inter'" } },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: 'rgba(148, 163, 184, 0.8)',
                        font: { family: "'JetBrains Mono'", size: 10 },
                        callback: (v) => v + '%'
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#f1f5f9',
                        font: { family: "'Inter'", size: 11 },
                        padding: 16,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 16, 41, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(99, 102, 241, 0.3)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toFixed(1)}%`
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}
