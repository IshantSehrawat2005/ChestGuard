/**
 * ChestGuard NeuralScan — Patient History
 * Loads and displays patient records and scan history from local database.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-history-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadHistory);
    }

    // Close scan detail
    const closeBtn = document.getElementById('close-scan-detail');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('scan-detail-panel').style.display = 'none';
        });
    }

    // Auto-load history when section becomes visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                loadHistory();
            }
        });
    }, { threshold: 0.1 });

    const historySection = document.getElementById('history-section');
    if (historySection) {
        observer.observe(historySection);
    }
});


async function loadHistory() {
    try {
        // Load stats
        const statsResp = await fetch('/api/stats');
        const stats = await statsResp.json();
        renderHistoryStats(stats);

        // Load patients
        const patientsResp = await fetch('/api/patients');
        const data = await patientsResp.json();
        renderPatientsTable(data.patients);

    } catch (error) {
        console.error('History load error:', error);
    }
}

function renderHistoryStats(stats) {
    const patientsEl = document.getElementById('hist-total-patients');
    const scansEl = document.getElementById('hist-total-scans');
    const avgEl = document.getElementById('hist-avg-score');

    if (patientsEl) patientsEl.textContent = stats.total_patients || 0;
    if (scansEl) scansEl.textContent = stats.total_scans || 0;
    if (avgEl) avgEl.textContent = stats.avg_neural_score || 0;
}

function renderPatientsTable(patients) {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    if (!patients || patients.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-text">
                    <div style="padding:32px 0;">
                        <i class="fas fa-folder-open" style="font-size:2rem; color:var(--accent-primary); opacity:0.4; display:block; margin-bottom:12px;"></i>
                        No patient records yet. Analyze an X-ray to create your first record.
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = '';
    patients.forEach((patient, idx) => {
        const row = document.createElement('tr');
        row.style.animationDelay = `${idx * 0.05}s`;

        const name = patient.name || 'Unnamed';
        const symptoms = patient.symptoms || 'None';
        const truncSymptoms = symptoms.length > 30 ? symptoms.substring(0, 30) + '...' : symptoms;
        const lastScan = patient.last_scan_date
            ? new Date(patient.last_scan_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : 'Never';

        row.innerHTML = `
            <td><span class="table-id">#${patient.id}</span></td>
            <td><strong>${escapeHtml(name)}</strong></td>
            <td>${patient.age || '--'}</td>
            <td>${patient.gender || '--'}</td>
            <td title="${escapeHtml(symptoms)}">${escapeHtml(truncSymptoms)}</td>
            <td><span class="scan-count-badge">${patient.scan_count || 0}</span></td>
            <td><span class="table-date">${lastScan}</span></td>
            <td>
                <div class="table-actions">
                    <button class="btn-icon" title="View Scans" onclick="viewPatientScans(${patient.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-icon btn-icon-danger" title="Delete" onclick="deletePatientRecord(${patient.id})">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function viewPatientScans(patientId) {
    try {
        const resp = await fetch(`/api/patients/${patientId}`);
        const data = await resp.json();

        const panel = document.getElementById('scan-detail-panel');
        const content = document.getElementById('scan-detail-content');
        panel.style.display = 'block';

        if (!data.scans || data.scans.length === 0) {
            content.innerHTML = '<p class="empty-text">No scans found for this patient.</p>';
            panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            return;
        }

        const patient = data.patient;
        let html = `
            <div style="margin-bottom:20px; padding:16px; border-radius:var(--radius-md); background:rgba(99,102,241,0.05); border:1px solid rgba(99,102,241,0.2);">
                <strong style="font-size:1.1rem;">${escapeHtml(patient.name || 'Unnamed Patient')}</strong>
                <span style="color:var(--text-secondary); margin-left:12px;">Age: ${patient.age} • ${patient.gender} • Smoking: ${patient.smoking_history || 'N/A'}</span>
                <br><span style="font-size:0.82rem; color:var(--text-muted);">Conditions: ${escapeHtml(patient.pre_existing_conditions || 'None')}</span>
            </div>
        `;

        html += '<div class="scan-cards-grid">';
        data.scans.forEach(scan => {
            const date = new Date(scan.created_at).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
            });

            const topFindings = scan.top_findings || {};
            let findingsHtml = '';
            Object.entries(topFindings).slice(0, 3).forEach(([name, prob]) => {
                const color = prob >= 60 ? '#ef4444' : prob >= 35 ? '#f59e0b' : '#10b981';
                findingsHtml += `<span style="display:inline-block;margin-right:8px;font-size:0.78rem;">${name}: <strong style="color:${color}">${prob}%</strong></span>`;
            });

            html += `
                <div class="scan-history-card">
                    <div class="scan-history-header">
                        <span class="scan-history-id">Scan #${scan.id}</span>
                        <span class="scan-history-date">${date}</span>
                    </div>
                    <div class="scan-history-body">
                        <div class="scan-history-score">
                            <div class="mini-score" style="color:${getScoreColor(scan.neural_score)}">
                                ${scan.neural_score?.toFixed(0) || '--'}
                            </div>
                            <div class="mini-score-label">NeuralScore™</div>
                        </div>
                        <div class="scan-history-findings">
                            <div class="scan-history-tier" style="color:${getTierColor(scan.risk_tier)}">${scan.risk_tier || '--'}</div>
                            <div style="margin-top:6px;">${findingsHtml || 'No significant findings'}</div>
                        </div>
                    </div>
                    <div class="scan-history-footer">
                        <span style="font-size:0.75rem; color:var(--text-muted);">${scan.xray_original_name || 'X-ray'}</span>
                        <button class="btn btn-outline btn-sm" onclick="deleteScanRecord(${scan.id})">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        content.innerHTML = html;
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (error) {
        console.error('View scans error:', error);
        showToast('Failed to load scan details', 'error');
    }
}

async function deletePatientRecord(patientId) {
    if (!confirm('Delete this patient and ALL their scans? This cannot be undone.')) return;

    try {
        await fetch(`/api/patients/${patientId}`, { method: 'DELETE' });
        showToast('Patient record deleted', 'success');
        loadHistory();
        document.getElementById('scan-detail-panel').style.display = 'none';
    } catch (error) {
        showToast('Failed to delete patient', 'error');
    }
}

async function deleteScanRecord(scanId) {
    if (!confirm('Delete this scan record?')) return;

    try {
        await fetch(`/api/scans/${scanId}`, { method: 'DELETE' });
        showToast('Scan deleted', 'success');
        document.getElementById('scan-detail-panel').style.display = 'none';
        loadHistory();
    } catch (error) {
        showToast('Failed to delete scan', 'error');
    }
}

function getScoreColor(score) {
    if (!score) return 'var(--text-muted)';
    if (score >= 60) return '#ef4444';
    if (score >= 35) return '#f59e0b';
    return '#10b981';
}

function getTierColor(tier) {
    if (!tier) return 'var(--text-muted)';
    const t = tier.toLowerCase();
    if (t.includes('critical') || t.includes('high')) return '#ef4444';
    if (t.includes('moderate') || t.includes('elevated')) return '#f59e0b';
    return '#10b981';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
