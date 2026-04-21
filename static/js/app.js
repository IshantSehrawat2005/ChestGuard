/**
 * ChestGuard NeuralScan — Main Application Controller
 * Handles state management, navigation, file upload, API calls, and UI orchestration.
 */

// ═══════════════════════════════════════════
// GLOBAL STATE
// ═══════════════════════════════════════════
const AppState = {
    selectedFile: null,
    analysisResult: null,
    isAnalyzing: false,
    activeTab: 'overview',
    chatOpen: false
};

// ═══════════════════════════════════════════
// DOM READY
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initNavigation();
    initFileUpload();
    initTabs();
    initAnalyzeButton();
    initActionButtons();
    animateCounters();
    initScrollAnimations();
});

// ═══════════════════════════════════════════
// PARTICLE BACKGROUND
// ═══════════════════════════════════════════
function initParticles() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    let animationId;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.5;
            this.speedY = (Math.random() - 0.5) * 0.5;
            this.opacity = Math.random() * 0.4 + 0.1;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }
        draw() {
            ctx.fillStyle = `rgba(99, 102, 241, ${this.opacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // Create particles
    const count = Math.min(80, Math.floor(window.innerWidth / 20));
    for (let i = 0; i < count; i++) {
        particles.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 150) {
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.06 * (1 - dist / 150)})`;
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }

        particles.forEach(p => {
            p.update();
            p.draw();
        });

        animationId = requestAnimationFrame(animate);
    }
    animate();
}

// ═══════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════
function initNavigation() {
    const navbar = document.getElementById('navbar');

    // Scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Nav links active state
    const sections = document.querySelectorAll('section[id]');
    window.addEventListener('scroll', () => {
        const scrollPos = window.scrollY + 100;
        sections.forEach(section => {
            const top = section.offsetTop;
            const height = section.offsetHeight;
            const id = section.getAttribute('id');
            const link = document.querySelector(`.nav-link[data-section="${id}"]`);
            if (link) {
                if (scrollPos >= top && scrollPos < top + height) {
                    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                    link.classList.add('active');
                }
            }
        });
    });

    // Smooth scroll for nav links
    document.querySelectorAll('.nav-link, a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });
}

// ═══════════════════════════════════════════
// FILE UPLOAD
// ═══════════════════════════════════════════
function initFileUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const removeBtn = document.getElementById('remove-image-btn');
    const analyzeBtn = document.getElementById('analyze-btn');

    // Browse button
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // Drop zone click
    dropZone.addEventListener('click', () => {
        if (!AppState.selectedFile) fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
    });

    // Remove image
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearFile();
    });
}

function handleFile(file) {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];
    if (!validTypes.includes(file.type)) {
        showToast('Please upload a valid image (JPG, PNG, BMP)', 'error');
        return;
    }

    if (file.size > 16 * 1024 * 1024) {
        showToast('File size must be under 16MB', 'error');
        return;
    }

    AppState.selectedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-image').src = e.target.result;
        document.getElementById('preview-filename').textContent = file.name;
        document.getElementById('drop-zone-content').style.display = 'none';
        document.getElementById('drop-zone-preview').style.display = 'block';
    };
    reader.readAsDataURL(file);

    // Enable analyze button
    document.getElementById('analyze-btn').disabled = false;
    document.getElementById('analyze-hint').textContent = 'Ready to analyze!';

    showToast('X-ray image loaded successfully', 'success');
}

function clearFile() {
    AppState.selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('drop-zone-content').style.display = 'flex';
    document.getElementById('drop-zone-preview').style.display = 'none';
    document.getElementById('analyze-btn').disabled = true;
    document.getElementById('analyze-hint').textContent = 'Upload an X-ray image to begin';
}

// ═══════════════════════════════════════════
// TABS
// ═══════════════════════════════════════════
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            setActiveTab(tab);
        });
    });
}

function setActiveTab(tab) {
    AppState.activeTab = tab;

    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tab}"]`).classList.add('active');

    // Update panes
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');

    // Trigger chart renders on tab switch
    if (tab === 'risk' && AppState.analysisResult) {
        setTimeout(() => renderRiskChart(AppState.analysisResult.neural_score), 100);
    }
    if (tab === 'timeline') {
        loadTimeline();
    }
}

// ═══════════════════════════════════════════
// ANALYZE
// ═══════════════════════════════════════════
function initAnalyzeButton() {
    document.getElementById('analyze-btn').addEventListener('click', runAnalysis);
}

async function runAnalysis() {
    if (!AppState.selectedFile || AppState.isAnalyzing) return;

    AppState.isAnalyzing = true;
    showLoader();

    // Gather patient info
    const symptoms = [];
    document.querySelectorAll('.chip input:checked').forEach(cb => {
        symptoms.push(cb.value);
    });
    const otherSymptoms = document.getElementById('other-symptoms').value.trim();
    if (otherSymptoms) symptoms.push(otherSymptoms);

    const formData = new FormData();
    formData.append('xray', AppState.selectedFile);
    formData.append('name', document.getElementById('patient-name').value.trim());
    formData.append('age', document.getElementById('patient-age').value);
    formData.append('gender', document.getElementById('patient-gender').value);
    formData.append('symptoms', symptoms.length > 0 ? symptoms.join(', ') : 'None reported');
    formData.append('smoking', document.getElementById('smoking-history').value);
    formData.append('conditions', document.getElementById('conditions').value || 'None reported');

    try {
        // Animate loader steps
        animateLoaderStep(1);
        await sleep(800);
        animateLoaderStep(2);
        await sleep(600);
        animateLoaderStep(3);

        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        animateLoaderStep(4);
        await sleep(400);
        animateLoaderStep(5);

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Analysis failed');
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Analysis failed');
        }

        AppState.analysisResult = result;

        // Complete all steps
        completeAllLoaderSteps();
        await sleep(600);

        hideLoader();
        displayResults(result);
        showToast('Analysis complete!', 'success');

        // Enable chat
        document.getElementById('chat-input').disabled = false;
        document.getElementById('chat-send-btn').disabled = false;

    } catch (error) {
        hideLoader();
        showToast(error.message, 'error');
        console.error('Analysis error:', error);
    } finally {
        AppState.isAnalyzing = false;
    }
}

// ═══════════════════════════════════════════
// DISPLAY RESULTS
// ═══════════════════════════════════════════
function displayResults(result) {
    const section = document.getElementById('results-section');
    section.style.display = 'block';

    // Scroll to results
    setTimeout(() => {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 200);

    // Quick stats
    renderQuickStats(result);

    // Overview tab
    renderFindings(result.top_findings, result.predictions);
    renderAllConditions(result.predictions);
    renderNeuralGauge(result.neural_score);
    renderXrayPreview(result.original_image);

    // Heatmaps tab
    renderHeatmaps(result.heatmaps, result.original_image, result.top_findings);

    // Regions tab
    renderRegions(result.regions, result.region_overlay, result.original_image);

    // Agents tab
    renderAgentPipeline(result.pipeline);

    // Risk tab
    renderRiskFactors(result.neural_score);

    // Set active tab
    setActiveTab('overview');
}

function renderQuickStats(result) {
    const score = result.neural_score.score;
    const tier = result.neural_score.tier;

    // NeuralScore
    animateCounter('stat-score-value', score, '/100');

    // Risk tier
    const tierEl = document.getElementById('stat-severity-value');
    tierEl.textContent = tier.level;
    tierEl.style.color = tier.color;

    // Conditions found (above 30%)
    const significantCount = Object.values(result.predictions)
        .filter(v => v > 30).length;
    animateCounter('stat-conditions-value', significantCount);

    // Scan count
    document.getElementById('stat-scans-value').textContent = result.scan_entry?.id || 1;
}

function renderFindings(topFindings, allPredictions) {
    const container = document.getElementById('findings-bars');
    container.innerHTML = '';

    Object.entries(topFindings).forEach(([condition, prob], i) => {
        const color = getBarColor(prob);
        const bar = document.createElement('div');
        bar.className = 'finding-bar';
        bar.innerHTML = `
            <div class="finding-bar-header">
                <span class="finding-name">${condition}</span>
                <span class="finding-prob" style="color:${color}">${prob}%</span>
            </div>
            <div class="finding-bar-track">
                <div class="finding-bar-fill" style="background:${color}"></div>
            </div>
        `;
        container.appendChild(bar);

        // Animate bar fill
        setTimeout(() => {
            bar.querySelector('.finding-bar-fill').style.width = `${Math.min(prob, 100)}%`;
        }, 100 + i * 150);
    });
}

function renderAllConditions(predictions) {
    const grid = document.getElementById('all-conditions-grid');
    grid.innerHTML = '';

    Object.entries(predictions).forEach(([condition, prob]) => {
        const color = getBarColor(prob);
        const pill = document.createElement('div');
        pill.className = 'condition-pill';
        pill.innerHTML = `
            <span class="condition-pill-name">${condition}</span>
            <span class="condition-pill-value" style="color:${color}">${prob}%</span>
        `;
        grid.appendChild(pill);
    });
}

function renderXrayPreview(imageB64) {
    const img = document.getElementById('result-xray-preview');
    img.src = `data:image/png;base64,${imageB64}`;
}

// ═══════════════════════════════════════════
// HEATMAPS
// ═══════════════════════════════════════════
function renderHeatmaps(heatmaps, originalImage, topFindings) {
    const baseImg = document.getElementById('heatmap-base-image');
    const overlayImg = document.getElementById('heatmap-overlay-image');
    const buttonsContainer = document.getElementById('heatmap-buttons');

    baseImg.src = `data:image/png;base64,${originalImage}`;
    overlayImg.style.display = 'none';

    buttonsContainer.innerHTML = '';

    if (!heatmaps || Object.keys(heatmaps).length === 0) {
        buttonsContainer.innerHTML = '<p class="empty-text">Heatmaps not available for this analysis.</p>';
        return;
    }

    Object.entries(heatmaps).forEach(([condition, heatmapB64]) => {
        const prob = topFindings[condition] || 0;
        const btn = document.createElement('button');
        btn.className = 'heatmap-btn';
        btn.innerHTML = `
            <span>${condition}</span>
            <span class="heatmap-btn-prob">${prob}%</span>
        `;
        btn.addEventListener('click', () => {
            // Toggle active
            document.querySelectorAll('.heatmap-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Show heatmap overlay
            overlayImg.src = `data:image/png;base64,${heatmapB64}`;
            overlayImg.style.display = 'block';
        });
        buttonsContainer.appendChild(btn);
    });

    // Opacity slider
    const opacitySlider = document.getElementById('heatmap-opacity');
    const opacityValue = document.getElementById('opacity-value');
    opacitySlider.addEventListener('input', (e) => {
        const val = e.target.value;
        overlayImg.style.opacity = val / 100;
        opacityValue.textContent = `${val}%`;
    });
}

// ═══════════════════════════════════════════
// REGIONS
// ═══════════════════════════════════════════
function renderRegions(regions, regionOverlay, originalImage) {
    const xrayImg = document.getElementById('region-xray-image');
    xrayImg.src = `data:image/png;base64,${originalImage}`;

    const svg = document.getElementById('region-overlay-svg');
    const cardsContainer = document.getElementById('region-cards');

    svg.innerHTML = '';
    cardsContainer.innerHTML = '';

    if (!regions || Object.keys(regions).length === 0) return;

    // Render region overlay rectangles on SVG
    Object.entries(regionOverlay).forEach(([name, data]) => {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', `${data.x * 100}%`);
        rect.setAttribute('y', `${data.y * 100}%`);
        rect.setAttribute('width', `${data.width * 100}%`);
        rect.setAttribute('height', `${data.height * 100}%`);
        rect.setAttribute('stroke', data.color);
        rect.setAttribute('rx', '4');

        rect.addEventListener('mouseenter', () => {
            rect.style.fill = `${data.color}33`;
            const card = document.querySelector(`.region-card[data-region="${name}"]`);
            if (card) card.style.borderColor = data.color;
        });
        rect.addEventListener('mouseleave', () => {
            rect.style.fill = 'transparent';
            const card = document.querySelector(`.region-card[data-region="${name}"]`);
            if (card) card.style.borderColor = '';
        });

        svg.appendChild(rect);
    });

    // Render region cards
    Object.entries(regions).forEach(([name, info]) => {
        const statusColor = getStatusColor(info.status);
        const card = document.createElement('div');
        card.className = 'region-card';
        card.dataset.region = name;

        let findingsHtml = '';
        Object.entries(info.findings).forEach(([condition, prob]) => {
            findingsHtml += `
                <div class="region-finding-item">
                    <span>${condition}</span>
                    <span style="color:${getBarColor(prob)};font-family:var(--font-mono);font-weight:600">${prob}%</span>
                </div>
            `;
        });

        card.innerHTML = `
            <div class="region-card-header">
                <span class="region-card-name">
                    <span class="region-color-dot" style="background:${info.color}"></span>
                    ${name}
                </span>
                <span class="region-health-badge" style="background:${statusColor}22;color:${statusColor}">
                    ${info.health_score}% Health
                </span>
            </div>
            <div class="region-card-findings">${findingsHtml}</div>
        `;

        // Hover effect — highlight SVG region
        card.addEventListener('mouseenter', () => {
            const rects = svg.querySelectorAll('rect');
            const overlay = regionOverlay[name];
            rects.forEach(r => {
                if (r.getAttribute('stroke') === overlay?.color) {
                    r.style.fill = `${overlay.color}33`;
                    r.setAttribute('stroke-width', '3');
                }
            });
        });
        card.addEventListener('mouseleave', () => {
            svg.querySelectorAll('rect').forEach(r => {
                r.style.fill = 'transparent';
                r.setAttribute('stroke-width', '2');
            });
        });

        cardsContainer.appendChild(card);
    });
}

// ═══════════════════════════════════════════
// AGENT PIPELINE
// ═══════════════════════════════════════════
function renderAgentPipeline(pipeline) {
    const container = document.getElementById('agents-chain');
    container.innerHTML = '';

    if (!pipeline || !pipeline.agents) return;

    pipeline.agents.forEach((agent, i) => {
        const card = document.createElement('div');
        card.className = 'agent-card';
        card.style.animationDelay = `${i * 0.15}s`;

        // Format output with markdown-like rendering
        const formattedOutput = formatAgentOutput(agent.output);

        card.innerHTML = `
            <div class="agent-step-dot"></div>
            <div class="agent-card-header">
                <span class="agent-icon">${agent.icon}</span>
                <span class="agent-name">${agent.agent}</span>
                <span class="agent-status ${agent.status}">${agent.status}</span>
            </div>
            <button class="agent-toggle" onclick="toggleAgent(this)">
                <i class="fas fa-chevron-down"></i>
                <span>View Analysis</span>
            </button>
            <div class="agent-output">${formattedOutput}</div>
        `;

        container.appendChild(card);
    });

    // Auto-expand the last agent (recommendations)
    const lastCard = container.querySelector('.agent-card:last-child');
    if (lastCard) {
        setTimeout(() => toggleAgent(lastCard.querySelector('.agent-toggle')), 500);
    }
}

function toggleAgent(btn) {
    const card = btn.closest('.agent-card');
    card.classList.toggle('expanded');
    const span = btn.querySelector('span');
    span.textContent = card.classList.contains('expanded') ? 'Hide Analysis' : 'View Analysis';
}

function formatAgentOutput(text) {
    if (!text) return '<p>No output available.</p>';

    // Convert markdown-like formatting to HTML
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.*$)/gm, '<h4 style="margin:12px 0 6px;color:var(--text-primary)">$1</h4>')
        .replace(/^## (.*$)/gm, '<h3 style="margin:14px 0 8px;color:var(--text-primary)">$1</h3>')
        .replace(/^- (.*$)/gm, '<li style="margin:2px 0;list-style:none;padding-left:12px;">• $1</li>')
        .replace(/\n\n/g, '</p><p style="margin:8px 0;">')
        .replace(/\n/g, '<br>');

    return `<div style="padding-top:8px;">${html}</div>`;
}

// ═══════════════════════════════════════════
// RISK FACTORS
// ═══════════════════════════════════════════
function renderRiskFactors(neuralScore) {
    const container = document.getElementById('risk-factors-list');
    container.innerHTML = '';

    if (!neuralScore || !neuralScore.breakdown) return;

    Object.entries(neuralScore.breakdown).forEach(([key, data]) => {
        const color = getBarColor(data.score);
        const item = document.createElement('div');
        item.className = 'risk-factor-item';
        item.innerHTML = `
            <div class="risk-factor-header">
                <span class="risk-factor-name">${data.label}</span>
                <span class="risk-factor-score" style="color:${color}">${data.score}/100</span>
            </div>
            <div class="risk-factor-bar">
                <div class="risk-factor-bar-fill" style="background:${color};width:0%"></div>
            </div>
        `;
        container.appendChild(item);

        // Animate
        setTimeout(() => {
            item.querySelector('.risk-factor-bar-fill').style.width = `${data.score}%`;
        }, 200);
    });

    // Render radar chart
    setTimeout(() => renderRiskChart(neuralScore), 300);
}

// ═══════════════════════════════════════════
// ACTION BUTTONS
// ═══════════════════════════════════════════
function initActionButtons() {
    // PDF Download
    document.getElementById('download-pdf-btn').addEventListener('click', downloadPDF);

    // New Scan
    document.getElementById('new-scan-btn').addEventListener('click', () => {
        clearFile();
        document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' });
    });

    // Add to Timeline
    document.getElementById('add-to-timeline-btn').addEventListener('click', () => {
        setActiveTab('timeline');
        loadTimeline();
    });

    // Chat toggle (nav)
    document.getElementById('chat-toggle-btn').addEventListener('click', toggleChat);
}

async function downloadPDF() {
    if (!AppState.analysisResult) {
        showToast('No analysis results to export', 'warning');
        return;
    }

    showToast('Generating PDF report...', 'info');

    try {
        const response = await fetch('/api/report/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(AppState.analysisResult)
        });

        if (!response.ok) throw new Error('Failed to generate PDF');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ChestGuard_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
        a.click();
        URL.revokeObjectURL(url);

        showToast('PDF report downloaded!', 'success');
    } catch (error) {
        showToast('Failed to generate PDF: ' + error.message, 'error');
    }
}

// ═══════════════════════════════════════════
// LOADER
// ═══════════════════════════════════════════
function showLoader() {
    const loader = document.getElementById('analysis-loader');
    loader.style.display = 'flex';

    // Reset all steps
    document.querySelectorAll('.loader-step').forEach(step => {
        step.classList.remove('active', 'complete');
        step.querySelector('.step-indicator').innerHTML = '<i class="fas fa-circle"></i>';
    });
    document.getElementById('loader-progress-bar').style.width = '0%';
}

function hideLoader() {
    document.getElementById('analysis-loader').style.display = 'none';
}

function animateLoaderStep(stepNum) {
    const totalSteps = 5;
    const steps = document.querySelectorAll('.loader-step');

    // Complete previous steps
    steps.forEach((step, i) => {
        if (i + 1 < stepNum) {
            step.classList.remove('active');
            step.classList.add('complete');
            step.querySelector('.step-indicator').innerHTML = '<i class="fas fa-circle-check"></i>';
        }
    });

    // Set current step as active
    const currentStep = document.getElementById(`step-${['model', 'gradcam', 'regions', 'risk', 'agents'][stepNum - 1]}`);
    if (currentStep) {
        currentStep.classList.add('active');
        currentStep.querySelector('.step-indicator').innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    }

    // Update titles
    const titles = [
        'Analyzing X-ray with DenseNet-121...',
        'Generating explainability heatmaps...',
        'Mapping anatomical regions...',
        'Computing NeuralScore™...',
        'Running AI diagnostic agents...'
    ];
    document.getElementById('loader-title').textContent = titles[stepNum - 1] || 'Processing...';

    // Update progress bar
    const progress = (stepNum / totalSteps) * 100;
    document.getElementById('loader-progress-bar').style.width = `${progress}%`;
}

function completeAllLoaderSteps() {
    document.querySelectorAll('.loader-step').forEach(step => {
        step.classList.remove('active');
        step.classList.add('complete');
        step.querySelector('.step-indicator').innerHTML = '<i class="fas fa-circle-check"></i>';
    });
    document.getElementById('loader-progress-bar').style.width = '100%';
    document.getElementById('loader-title').textContent = 'Analysis Complete!';
}

// ═══════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getBarColor(prob) {
    if (prob >= 60) return '#ef4444';
    if (prob >= 35) return '#f59e0b';
    return '#10b981';
}

function getStatusColor(status) {
    switch (status) {
        case 'normal': return '#10b981';
        case 'mild': return '#22c55e';
        case 'moderate': return '#f59e0b';
        case 'concerning': return '#ef4444';
        default: return '#94a3b8';
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: 'fa-circle-check',
        error: 'fa-circle-xmark',
        warning: 'fa-triangle-exclamation',
        info: 'fa-circle-info'
    };

    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

function animateCounter(elementId, target, suffix = '') {
    const el = document.getElementById(elementId);
    if (!el) return;

    const duration = 1500;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);

        el.textContent = current + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function animateCounters() {
    // Hero stat counters
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.dataset.count);
                if (!el.dataset.animated) {
                    el.dataset.animated = 'true';
                    const duration = 1200;
                    const startTime = performance.now();

                    function animate(currentTime) {
                        const elapsed = currentTime - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = 1 - Math.pow(1 - progress, 3);
                        el.textContent = Math.round(target * eased);
                        if (progress < 1) requestAnimationFrame(animate);
                    }
                    requestAnimationFrame(animate);
                }
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.hero-stat-number[data-count]').forEach(el => {
        observer.observe(el);
    });
}

function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.pipeline-step, .glass-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

function toggleChat() {
    const panel = document.getElementById('chat-panel');
    const fab = document.getElementById('chat-fab');
    AppState.chatOpen = !AppState.chatOpen;
    panel.classList.toggle('open', AppState.chatOpen);

    if (AppState.chatOpen && AppState.analysisResult) {
        document.getElementById('chat-input').focus();
    }
}
