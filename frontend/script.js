// Global Tab Switcher Function
window.switchTab = function (event, tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

    if (event) {
        event.currentTarget.classList.add('active');
    }
    document.getElementById('tab-' + tabId).classList.add('active');

    // Auto-fetch history when the tab is clicked
    if (tabId === 'history') {
        if (typeof window.fetchHistory === 'function') {
            window.fetchHistory();
        }
    }
};

function displayResult(data, file) {
    const resultSection = document.getElementById('result-section');
    resultSection.style.display = 'block';

    // Determine status colors and icons
    const isFake = data.verdict === 'FAKE';
    const color = isFake ? '#FF003C' : '#00FF41'; // Red for Fake, Green for Real
    const riskLevel = isFake ? 'CRITICAL - THREAT DETECTED' : 'LOW - AUTHENTIC';
    const icon = isFake ? '<i class="fas fa-biohazard"></i>' : '<i class="fas fa-shield-alt"></i>';

    // Extract Metadata Report
    const meta = data.checks.metadata.report || {};
    const hasGPS = meta.gps && meta.gps.includes("Present");

    // Helper for granular bars with detailed descriptions
    function createGranularBar(label, value, description) {
        if (value === "N/A" || value === null) return '';
        const numVal = parseFloat(value);
        let barColor = '#FF003C'; // Red
        if (numVal > 40) barColor = '#FFCC00'; // Yellow
        if (numVal > 75) barColor = '#00FF41'; // Green

        return `
            <div style="margin-bottom: 1.5rem; background: rgba(0,0,0,0.15); padding: 12px; border-radius: 8px; border-left: 3px solid ${barColor}88;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem; align-items: center;">
                    <span style="font-weight: 600; color: var(--text-main); font-size: 0.95rem;">${label}</span>
                    <span style="font-weight: 700; color: ${barColor}; letter-spacing: 1px;">${value}% REAL</span>
                </div>
                <div style="margin-bottom: 0.8rem; font-size: 0.8rem; color: var(--text-muted); line-height: 1.3;">${description}</div>
                <div class="dynamic-bar-bg" style="height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="width: ${numVal}%; background: ${barColor}; height: 100%; box-shadow: 0 0 10px ${barColor}55; border-radius: 4px;"></div>
                </div>
            </div>
        `;
    }

    // Helper to render detailed checks
    function renderDetailedChecks(title, report) {
        if (!report) return '';

        let html = `<div style="margin-top: 15px; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px; border-left: 3px solid rgba(255,255,255,0.2);">
            <strong style="color: var(--accent-cyan); display: block; margin-bottom: 10px; font-family: 'Space Grotesk', sans-serif;">${title} Findings:</strong>
            <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.95rem;">`;

        for (const [key, check] of Object.entries(report)) {
            if (key === 'error' || key === 'annotated_image' || key === 'waveform_graph') continue;
            // For boolean checks, true is good (Green), false is bad (Red) depending on logic.
            const icon = check.pass ? '<i class="fas fa-check-circle" style="color: #00FF41;"></i>' : '<i class="fas fa-times-circle" style="color: #FF003C;"></i>';
            const statusColor = check.pass ? '#00FF41' : '#FF003C';

            // Format key text (e.g. "noise_patterns" -> "Noise Patterns")
            const formattedKey = key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

            html += `<li style="margin-bottom: 8px; display: flex; align-items: flex-start; gap: 10px;">
                <span style="margin-top: 3px;">${icon}</span>
                <div>
                    <strong style="color: var(--text-muted);">${formattedKey}:</strong>
                    <span style="color: ${statusColor}; font-weight: 500;"> ${check.detail}</span>
                </div>
            </li>`;
        }

        html += `</ul></div>`;
        return html;
    }

    // Build the Forensic Report HTML
    const resultHTML = `
        <div class="dynamic-result-card" style="box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.05); padding: 30px; position: relative;">
            
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px;">
                <div>
                    <h3 style="color: ${color}; font-size: 2.2rem; margin: 0; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 20px ${color};">
                        <i class="fas ${icon}"></i> ${data.verdict}
                    </h3>
                    <p style="margin: 5px 0 0; color: var(--text-muted); font-size: 0.95rem;">File: <b>${file.name}</b></p>
                    <p style="margin: 5px 0 0; color: var(--accent-cyan); font-size: 0.90rem; font-family: 'Space Grotesk', monospace;">Scan ID: <b>${data.scan_id || 'N/A'}</b></p>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.9rem; color: var(--text-muted); background: rgba(0,0,0,0.3); padding: 5px 12px; border-radius: 20px; font-family: 'Outfit', sans-serif;">
                        <i class="fas fa-clock"></i> ${data.processing_time}
                    </span>
                    ${data.scan_id ? `<br><a href="/report/${data.scan_id}" target="_blank" style="display: inline-block; margin-top: 15px; padding: 10px 20px; background: rgba(10, 132, 255, 0.2); border: 1px solid var(--accent-blue); color: var(--accent-cyan); border-radius: 8px; text-decoration: none; font-size: 0.9rem; font-family: 'Space Grotesk', sans-serif; transition: all 0.3s;" onmouseover="this.style.background='rgba(10, 132, 255, 0.4)'" onmouseout="this.style.background='rgba(10, 132, 255, 0.2)'"><i class="fas fa-file-pdf"></i> Download PDF Report</a>` : ''}
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                
                <!-- LEFT COLUMN: COMPONENT ANALYSIS -->
                <div>
                    <h4 style="margin-top: 0; margin-bottom: 1.5rem; color: var(--text-main); border-bottom: 1px solid var(--border-color); padding-bottom: 10px; display:flex; align-items:center; gap:8px;">
                        <i class="fas fa-chart-pie" style="color: var(--accent-blue);"></i> Component Authenticity
                    </h4>
                    <div class="dynamic-panel">
                        ${createGranularBar('Face / Identity', data.components.face, 'Analyzes facial biometrics, blending boundaries, skin texture micro-patterns, and deep learning artifacts typical of GANs and face-swapping.')}
                        ${createGranularBar('Body / Movement', data.components.body, 'Evaluates skeletal motion, posture continuity, and unnatural joint kinematics over time to detect AI-generated video framing anomalies.')}
                        ${createGranularBar('Voice / Audio', data.components.voice, 'Scans for Text-to-Speech (TTS) acoustic signatures, unnatural frequency flatness, and voice cloning algorithms.')}
                        ${createGranularBar('Background / Environment', data.components.background, 'Detects pixel spatial frequency anomalies, warped environments, and copy-move forgery within the contextual background.')}
                        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 15px; font-style: italic; opacity: 0.8;">
                            * Scores represent the estimated probability of each component being authentic (unmanipulated).
                        </p>
                    </div>
                </div>

                <!-- RIGHT COLUMN: DEVICE FINGERPRINT -->
                <div>
                     <h4 style="margin-top: 0; margin-bottom: 1.5rem; color: var(--text-main); border-bottom: 1px solid var(--border-color); padding-bottom: 10px; display:flex; align-items:center; gap:8px;">
                        <i class="fas fa-fingerprint" style="color: var(--accent-cyan);"></i> Device & Metadata
                    </h4>
                    <div class="dynamic-panel" style="font-family: 'Space Grotesk', monospace; font-size: 0.95rem;">
                        <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">CRYPTOGRAPHIC CHECKSUM (SHA-256)</small>
                            <div style="color: #fff; font-family: 'Courier New', monospace; font-size: 0.85rem; word-wrap: break-word;">${data.file_hash_sha256 || "N/A"}</div>
                        </div>

                        <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">FILE SPECS & SIZE</small>
                            <div style="color: var(--accent-cyan); font-weight: bold;">${meta.format || "Unknown Format"} • ${meta.file_size || "N/A"}</div>
                        </div>

                        ${meta.resolution && meta.resolution !== 'Unknown' ? `
                        <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">MEDIA RESOLUTION</small>
                            <div style="color: #fff; font-weight: bold;">${meta.resolution}</div>
                        </div>` : ''}

                        ${meta.duration && meta.duration !== 'N/A' ? `
                        <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">MEDIA DURATION</small>
                            <div style="color: #fff; font-weight: bold;">${meta.duration}</div>
                        </div>` : ''}

                        <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">SOFTWARE / PLATFORM</small>
                            <div style="color: ${meta.software && meta.software.includes('EDITING') ? '#FF003C' : '#fff'}; font-weight: bold;">${meta.software || "Unknown Origin"}</div>
                        </div>
                        
                        <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">DEVICE SIGNATURE</small>
                            <div style="color: #fff; font-weight: bold;">${meta.device || "Unknown Device"}</div>
                        </div>

                        <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">CREATION TIMESTAMP</small>
                            <div style="color: #fff;">${meta.creation_date || "Metadata Stripped"}</div>
                        </div>
                        
                        <div>
                            <small style="color: var(--text-muted); display: block; margin-bottom: 4px;">GEOLOCATION DATA</small>
                            <div style="color: ${hasGPS ? '#FF003C' : '#00FF41'}; font-weight: bold;">
                                ${meta.gps || "No GPS Tags Found"}
                            </div>
                        </div>
                    </div>
                </div>

            </div>

            <!-- ANALYSIS BREAKDOWN (Below Columns) -->
            <div style="display: grid; grid-template-columns: 1fr; gap: 20px; text-align: left; margin-top: 30px;">
                
                <h4 style="margin-top: 10px; margin-bottom: 5px; color: var(--text-main); border-bottom: 1px solid var(--border-color); padding-bottom: 10px;">Detailed Forensic Findings</h4>

                <!-- 1. Metadata Risks -->
                <div style="padding: 20px; background: rgba(0,0,0,0.2); border: 1px solid var(--border-color); border-radius: 12px; border-left: 4px solid ${data.checks.metadata.pass ? '#00FF41' : '#FFCC00'};">
                    <strong style="font-size: 1.1rem; color: var(--text-main); display:flex; align-items:center; gap:8px;"><i class="fas fa-search" style="color: var(--accent-blue);"></i> Metadata Analysis</strong>
                    <p style="margin: 10px 0 0; font-size: 1rem; color: var(--text-muted);">${data.checks.metadata.detail}</p>
                </div>

                <!-- 2. Visual / Audio Analysis -->
                ${data.checks.visual ? `
                <div style="padding: 20px; background: rgba(0,0,0,0.2); border: 1px solid var(--border-color); border-radius: 12px; border-left: 4px solid ${data.checks.visual.pass ? '#00FF41' : '#FF003C'};">
                    <strong style="font-size: 1.1rem; color: var(--text-main); display:flex; align-items:center; gap:8px;"><i class="fas fa-eye" style="color: var(--accent-cyan);"></i> Visual Integrity Check</strong>
                    <p style="margin: 10px 0 0; font-size: 1rem; color: var(--text-muted);">${data.checks.visual.detail}</p>
                    
                    ${data.checks.visual.report && data.checks.visual.report.annotated_image ? `
                        <div style="margin-top: 20px; margin-bottom: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; background: rgba(0,0,0,0.3);">
                            <strong style="display: block; margin-bottom: 10px; color: var(--accent-cyan); font-size: 0.85rem; letter-spacing: 1px;">FACIAL ANALYSIS VISUALIZATION</strong>
                            <img src="${data.checks.visual.report.annotated_image}" style="max-width: 100%; border-radius: 6px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);" alt="Annotated Analysis Frame">
                        </div>
                    ` : ''}

                    ${data.checks.visual.report && data.checks.visual.report.lip_sync && data.checks.visual.report.lip_sync.graph ? `
                        <div style="margin-top: 20px; margin-bottom: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; background: rgba(0,0,0,0.3);">
                            <strong style="display: block; margin-bottom: 10px; color: var(--accent-blue); font-size: 0.85rem; letter-spacing: 1px;">LIP-SYNC CORRELATION GRAPH</strong>
                            <img src="${data.checks.visual.report.lip_sync.graph}" style="max-width: 100%; border-radius: 6px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);" alt="Lip Sync Graph">
                        </div>
                    ` : ''}

                    ${renderDetailedChecks('Visual', data.checks.visual.report)}
                </div>` : ''}

                ${data.checks.audio ? `
                <div style="padding: 20px; background: rgba(0,0,0,0.2); border: 1px solid var(--border-color); border-radius: 12px; border-left: 4px solid ${data.checks.audio.pass ? '#00FF41' : '#FF003C'};">
                    <strong style="font-size: 1.1rem; color: var(--text-main); display:flex; align-items:center; gap:8px;"><i class="fas fa-microphone-alt" style="color: var(--accent-yellow);"></i> Voice & Audio Analysis</strong>
                    <p style="margin: 10px 0 0; font-size: 1rem; color: var(--text-muted);">${data.checks.audio.detail}</p>
                    
                    ${data.checks.audio.report && data.checks.audio.report.waveform_graph ? `
                        <div style="margin-top: 20px; margin-bottom: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; background: rgba(0,0,0,0.3);">
                            <strong style="display: block; margin-bottom: 10px; color: var(--accent-yellow); font-size: 0.85rem; letter-spacing: 1px;">ACOUSTIC ENVELOPE ANALYSIS</strong>
                            <img src="${data.checks.audio.report.waveform_graph}" style="max-width: 100%; border-radius: 6px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);" alt="Waveform Generator Plot">
                        </div>
                    ` : ''}

                    ${renderDetailedChecks('Audio', data.checks.audio.report)}
                </div>` : ''}

                ${data.checks.steganography ? `
                <div style="padding: 20px; background: rgba(0,0,0,0.2); border: 1px solid var(--border-color); border-radius: 12px; border-left: 4px solid ${data.checks.steganography.pass ? '#00FF41' : '#FF003C'};">
                    <strong style="font-size: 1.1rem; color: var(--text-main); display:flex; align-items:center; gap:8px;"><i class="fas fa-user-secret" style="color: #9c27b0;"></i> Steganography Analysis</strong>
                    <p style="margin: 10px 0 0; font-size: 1rem; color: var(--text-muted);">${data.checks.steganography.detail}</p>
                    ${renderDetailedChecks('LSB Analytics', data.checks.steganography.report)}
                </div>` : ''}

            </div>

            <!-- 3. Final Verdict -->
            <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border-color);">
                <h4 style="font-size: 1.5rem; margin-bottom: 1.5rem;"><i class="fas fa-gavel" style="color: var(--accent-yellow);"></i> Final Verdict</h4>
                <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 2rem; text-align: center; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">
                    <p style="margin-bottom: 1.5rem; font-size: 1.3rem; color: var(--text-main);">
                        Overall Manipulation Probability: <strong style="color: ${color}; font-size: 1.8rem; display: block; margin-top: 5px; text-shadow: 0 0 15px ${color}66;">${(data.fake_probability * 100).toFixed(1)}%</strong>
                    </p>
                    <div class="dynamic-bar-bg" style="height: 15px; margin-bottom: 1.5rem; background: rgba(255,255,255,0.1);">
                        <div style="width: ${data.fake_probability * 100}%; background-color: ${color}; height: 100%; box-shadow: 0 0 15px ${color}99; transition: width 1s ease-in-out;"></div>
                    </div>
                    <p style="font-style: italic; color: var(--text-muted); font-size: 1.1rem; border-left: 3px solid ${color}88; padding-left: 20px; display: inline-block; max-width: 80%;">
                        "${data.explanation}"
                    </p>
                </div>
            </div>

        </div>
    `;

    resultSection.innerHTML = resultHTML;
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function simulateTerminal() {
    const terminalBody = document.getElementById('terminal-output');
    if (!terminalBody) return;

    terminalBody.innerHTML = '';
    const commands = [
        "Initializing PyTorch Deep Learning Tensors...",
        "Loading EfficientNet_B0 Neural Weights into VRAM... [OK]",
        "Calculated cryptographic hash (SHA-256)... [OK]",
        "Running ExifTool metadata extraction...",
        "Scanning LSB arrays for steganographic anomalies...",
        "Searching for editing software signatures...",
        "Processing visual artifacts (ELA/Noise)...",
        "Extracting acoustic envelope...",
        "Correlating audio-visual sync features...",
        "Compiling decision fusion matrix...",
        "Generating final forensic report..."
    ];

    let delay = 0;
    commands.forEach((cmd) => {
        setTimeout(() => {
            const line = document.createElement('div');
            line.className = 'terminal-line';
            line.innerHTML = `<span class="cmd-prompt">root@truthguard:~#</span> ${cmd}`;
            terminalBody.appendChild(line);
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }, delay);
        delay += Math.floor(Math.random() * 600) + 300;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // PERMANENT LOCALHOST CONNECTION
    // This absolutely guarantees that the frontend will always connect to your background TruthGuard server.
    const API_BASE = 'http://127.0.0.1:8000';
    const WS_BASE = 'ws://127.0.0.1:8000';
    const dropAreas = document.querySelectorAll('.drop-area');
    const fileInputs = document.querySelectorAll('.file-input');
    const resultSection = document.getElementById('result-section');
    const loading = document.getElementById('loading');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropAreas.forEach(area => area.addEventListener(eventName, preventDefaults, false));
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area
    ['dragenter', 'dragover'].forEach(eventName => {
        dropAreas.forEach(area => area.addEventListener(eventName, highlight, false));
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropAreas.forEach(area => area.addEventListener(eventName, unhighlight, false));
    });

    function highlight(e) {
        e.currentTarget.classList.add('highlight');
    }

    function unhighlight(e) {
        e.currentTarget.classList.remove('highlight');
    }

    // Handle dropped files
    dropAreas.forEach(area => area.addEventListener('drop', handleDrop, false));

    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;
        handleFiles(files, e.currentTarget);
    }

    // Handle file input
    fileInputs.forEach(input => {
        input.addEventListener('change', function () {
            const dropZone = this.closest('.drop-area');
            handleFiles(this.files, dropZone);
        });
    });

    function handleFiles(files, dropArea) {
        if (files.length > 0) {
            uploadFile(files[0], dropArea);
        }
    }

    // Handle URL input for Video Analysis
    const analyzeUrlBtn = document.getElementById('analyze-url-btn');
    const videoUrlInput = document.getElementById('video-url-input');

    if (analyzeUrlBtn && videoUrlInput) {
        analyzeUrlBtn.addEventListener('click', () => {
            const url = videoUrlInput.value.trim();
            if (!url) {
                alert("Please enter a valid video URL.");
                return;
            }

            const formData = new FormData();
            formData.append('url', url);

            loading.style.display = 'block';
            simulateTerminal();
            resultSection.style.display = 'none';
            resultSection.innerHTML = '';

            const btnOriginalHtml = analyzeUrlBtn.innerHTML;
            analyzeUrlBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
            analyzeUrlBtn.disabled = true;

            fetch(`${API_BASE}/analyze/`, {
                method: 'POST',
                body: formData
            })
                .then(async response => {
                    analyzeUrlBtn.innerHTML = btnOriginalHtml;
                    analyzeUrlBtn.disabled = false;
                    if (!response.ok) {
                        let errorMessage = `Server Error (${response.status})`;
                        try {
                            const textData = await response.text();
                            try {
                                const errData = JSON.parse(textData);
                                errorMessage = errData.detail || errData.error || errorMessage;
                            } catch (e) {
                                errorMessage = textData || errorMessage;
                            }
                        } catch (e) {
                            errorMessage = response.statusText || errorMessage;
                        }
                        throw new Error(errorMessage);
                    }
                    return response.json();
                })
                .then(data => {
                    loading.style.display = 'none';
                    /* Pass a mock file object so displayResult doesn't fail on file.name */
                    displayResult(data, { name: new URL(url).pathname.split('/').pop() || "Remote Video File" });
                })
                .catch(error => {
                    console.error('Error:', error);
                    loading.style.display = 'none';
                    analyzeUrlBtn.innerHTML = btnOriginalHtml;
                    analyzeUrlBtn.disabled = false;

                    if (error.message.includes("QUARANTINE_ALERT")) {
                        const parts = error.message.split("|");
                        const vtLink = parts[2] ? `<a href="${parts[2]}" target="_blank" style="color: #FF003C; text-decoration: underline; margin-top: 15px; display: inline-block;">View VirusTotal Report <i class="fas fa-external-link-alt"></i></a>` : '';
                        resultSection.innerHTML = `
                        <div class="dynamic-result-card" style="box-shadow: 0 0 40px rgba(255, 0, 60, 0.4); border: 2px solid #FF003C; padding: 40px; text-align: center;">
                            <i class="fas fa-biohazard" style="font-size: 5rem; color: #FF003C; margin-bottom: 20px; text-shadow: 0 0 20px #FF003C;"></i>
                            <h2 style="color: #FF003C; font-family: 'Space Grotesk', sans-serif; letter-spacing: 5px; text-transform: uppercase;">QUARANTINE ALERT</h2>
                            <p style="font-size: 1.2rem; color: var(--text-main); margin-top: 15px;">${parts[1]}</p>
                            ${vtLink}
                        </div>`;
                    } else {
                        resultSection.innerHTML = `
                        <div class="dynamic-result-card" style="border-left: 5px solid #FF003C; padding: 25px;">
                            <h3 style="color: #FF003C; margin-top: 0; display:flex; align-items:center; gap:10px;"><i class="fas fa-exclamation-triangle"></i> URL Analysis Failed</h3>
                            <p style="font-size: 1.1rem; color: var(--text-main); margin-bottom: 10px;">${error.message}</p>
                            <p style="color: var(--text-muted);">Please verify the URL is publicly accessible and points to a valid media file.</p>
                        </div>`;
                    }
                    resultSection.style.display = 'block';
                    resultSection.scrollIntoView({ behavior: 'smooth' });
                });
        });
    }

    function uploadFile(file, dropArea) {
        const formData = new FormData();
        formData.append('file', file);

        loading.style.display = 'block';
        simulateTerminal();
        resultSection.style.display = 'none';
        resultSection.innerHTML = '';
        dropArea.style.opacity = '0.5';

        fetch(`${API_BASE}/analyze/`, {
            method: 'POST',
            body: formData,
            mode: 'cors',
            cache: 'no-cache'
        })
            .then(async response => {
                dropArea.style.opacity = '1';
                if (!response.ok) {
                    let errorMessage = `Server Error (${response.status})`;
                    try {
                        const textData = await response.text();
                        try {
                            const errData = JSON.parse(textData);
                            errorMessage = errData.detail || errData.error || errorMessage;
                        } catch (e) {
                            errorMessage = textData || errorMessage;
                        }
                    } catch (e) {
                        errorMessage = response.statusText || errorMessage;
                    }
                    throw new Error(errorMessage);
                }
                return response.json();
            })
            .then(data => {
                loading.style.display = 'none';
                displayResult(data, file);
            })
            .catch(error => {
                console.error('Error:', error);
                loading.style.display = 'none';
                dropArea.style.opacity = '1';

                if (error.message.includes("QUARANTINE_ALERT")) {
                    const parts = error.message.split("|");
                    const vtLink = parts[2] ? `<a href="${parts[2]}" target="_blank" style="color: #FF003C; text-decoration: underline; margin-top: 15px; display: inline-block;">View VirusTotal Report <i class="fas fa-external-link-alt"></i></a>` : '';
                    resultSection.innerHTML = `
                    <div class="dynamic-result-card" style="box-shadow: 0 0 40px rgba(255, 0, 60, 0.4); border: 2px solid #FF003C; padding: 40px; text-align: center;">
                        <i class="fas fa-biohazard" style="font-size: 5rem; color: #FF003C; margin-bottom: 20px; text-shadow: 0 0 20px #FF003C;"></i>
                        <h2 style="color: #FF003C; font-family: 'Space Grotesk', sans-serif; letter-spacing: 5px; text-transform: uppercase;">QUARANTINE ALERT</h2>
                        <p style="font-size: 1.2rem; color: var(--text-main); margin-top: 15px;">${parts[1]}</p>
                        ${vtLink}
                    </div>`;
                } else {
                    resultSection.innerHTML = `
                    <div class="dynamic-result-card" style="border-left: 5px solid #FF003C; padding: 25px;">
                        <h3 style="color: #FF003C; margin-top: 0; display:flex; align-items:center; gap:10px;"><i class="fas fa-exclamation-triangle"></i> Analysis Failed</h3>
                        <p style="font-size: 1.1rem; color: var(--text-main); margin-bottom: 10px;">${error.message}</p>
                        <p style="color: var(--text-muted);">Please try uploading a different file or check your server connection.</p>
                    </div>`;
                }

                resultSection.style.display = 'block';
                resultSection.scrollIntoView({ behavior: 'smooth' });
            });
    }

    // ----------------------------------------------------------------------
    // REAL-TIME AUDIO WEBSOCKET STREAMING LOGIC
    // ----------------------------------------------------------------------
    const liveMicBtn = document.querySelector('.pulse-red'); // The Start Live Mic button
    let ws = null;
    let audioContext = null;
    let mediaStream = null;
    let isStreaming = false;
    let liveStatusEl = null;

    if (liveMicBtn) {
        // Create an element to display live results
        liveStatusEl = document.createElement('div');
        liveStatusEl.style.marginTop = '15px';
        liveStatusEl.style.padding = '10px';
        liveStatusEl.style.borderRadius = '8px';
        liveStatusEl.style.display = 'none';
        liveStatusEl.style.fontFamily = "'Space Grotesk', monospace";
        liveStatusEl.style.fontWeight = '700';
        liveStatusEl.style.transition = 'all 0.3s ease';
        liveStatusEl.innerHTML = 'Status: <span id="live-verdict">Waiting...</span> | Probability: <span id="live-prob">0%</span>';
        liveMicBtn.parentNode.appendChild(liveStatusEl);

        liveMicBtn.addEventListener('click', async () => {
            if (isStreaming) {
                stopLiveAudio();
                return;
            }
            startLiveAudio();
        });
    }

    async function startLiveAudio() {
        if (isStreaming) return;
        isStreaming = true;
        try {
            liveMicBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Stop Live Mic';
            liveMicBtn.style.borderColor = '#FF003C';
            liveMicBtn.style.backgroundColor = 'rgba(255, 59, 48, 0.2)';

            // 1. Establish WebSocket Connection
            ws = new WebSocket(`${WS_BASE}/ws/analyze_audio`);

            ws.onopen = () => {
                console.log("WebSocket connected. Starting stream...");
                liveStatusEl.style.display = 'block';
                liveStatusEl.style.backgroundColor = 'rgba(10, 132, 255, 0.2)';
                liveStatusEl.style.border = '1px solid #0A84FF';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.status === 'success') {
                    const verdictEl = document.getElementById('live-verdict');
                    const probEl = document.getElementById('live-prob');

                    const probPercent = Math.round(data.fake_probability * 100);
                    probEl.innerText = `${probPercent}% FAKE`;
                    verdictEl.innerText = data.verdict;

                    // Update visual UI based on live score
                    if (data.verdict === 'FAKE') {
                        liveStatusEl.style.backgroundColor = 'rgba(255, 59, 48, 0.2)';
                        liveStatusEl.style.border = '1px solid #FF003C';
                        verdictEl.style.color = '#FF003C';
                        probEl.style.color = '#FF003C';
                    } else {
                        liveStatusEl.style.backgroundColor = 'rgba(52, 199, 89, 0.2)';
                        liveStatusEl.style.border = '1px solid #00FF41';
                        verdictEl.style.color = '#00FF41';
                        probEl.style.color = '#00FF41';
                    }
                }
            };

            ws.onerror = (error) => {
                console.error("WebSocket Error:", error);
                stopLiveAudio();
            };

            ws.onclose = () => {
                stopLiveAudio();
            };

            // 2. Capture Microphone via Web Audio API 
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            audioContext = new (window.AudioContext || window.webkitAudioContext)();

            const source = audioContext.createMediaStreamSource(mediaStream);
            const processor = audioContext.createScriptProcessor(4096, 1, 1);

            source.connect(processor);
            processor.connect(audioContext.destination);

            processor.onaudioprocess = (e) => {
                if (!isStreaming || ws.readyState !== WebSocket.OPEN) return;

                // Get raw PCM audio float data (-1.0 to +1.0)
                const float32Array = e.inputBuffer.getChannelData(0);

                // Convert to 16-bit PCM buffer to send over WebSocket
                const buffer = new ArrayBuffer(float32Array.length * 2);
                const view = new DataView(buffer);

                for (let i = 0; i < float32Array.length; i++) {
                    let s = Math.max(-1, Math.min(1, float32Array[i]));
                    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                }

                // Send binary blob to the Python backend immediately
                ws.send(buffer);
            };

        } catch (error) {
            console.error("Microphone access denied or error:", error);
            alert("To use Real-Time Voice Detection, you must allow browser microphone access.");
            stopLiveAudio();
        }
    }

    function stopLiveAudio() {
        isStreaming = false;
        if (ws) {
            ws.close();
            ws = null;
        }
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        if (liveMicBtn) {
            liveMicBtn.innerHTML = '<i class="fas fa-microphone-lines"></i> Start Live Mic';
            liveMicBtn.style.borderColor = 'rgba(255, 59, 48, 0.5)';
            liveMicBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        }
        if (liveStatusEl) {
            liveStatusEl.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            liveStatusEl.style.border = '1px solid var(--border-color)';
            document.getElementById('live-verdict').innerText = 'Stopped';
            document.getElementById('live-verdict').style.color = 'var(--text-muted)';
            document.getElementById('live-prob').innerText = '--';
            document.getElementById('live-prob').style.color = 'var(--text-muted)';
        }
    }
    // ----------------------------------------------------------------------
    // REAL-TIME VIDEO WEBSOCKET STREAMING LOGIC
    // ----------------------------------------------------------------------
    const startWebcamBtn = document.getElementById('start-webcam-btn');
    const webcamPreview = document.getElementById('webcam-preview');
    const webcamCanvas = document.getElementById('webcam-canvas');
    let videoWs = null;
    let videoStream = null;
    let isVideoStreaming = false;
    let videoStatusEl = null;
    let frameInterval = null;

    if (startWebcamBtn) {
        // Create an element to display live video results
        videoStatusEl = document.createElement('div');
        videoStatusEl.style.marginTop = '15px';
        videoStatusEl.style.padding = '10px';
        videoStatusEl.style.borderRadius = '8px';
        videoStatusEl.style.display = 'none';
        videoStatusEl.style.fontFamily = "'Space Grotesk', monospace";
        videoStatusEl.style.fontWeight = '700';
        videoStatusEl.style.transition = 'all 0.3s ease';
        videoStatusEl.innerHTML = 'Status: <span id="video-verdict">Waiting...</span> | Probability: <span id="video-prob">0%</span>';
        const webcamContainer = document.getElementById('webcam-container') || webcamPreview;
        startWebcamBtn.parentNode.insertBefore(videoStatusEl, webcamContainer);

        startWebcamBtn.addEventListener('click', async () => {
            if (isVideoStreaming) {
                stopLiveVideo();
                return;
            }
            startLiveVideo();
        });
    }

    async function startLiveVideo() {
        if (isVideoStreaming) return;
        isVideoStreaming = true;
        try {
            startWebcamBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Stop Live Webcam';
            startWebcamBtn.style.borderColor = '#FF003C';
            startWebcamBtn.style.color = '#FF003C';
            startWebcamBtn.style.backgroundColor = 'rgba(255, 59, 48, 0.2)';
            startWebcamBtn.classList.remove('pulse-blue');
            startWebcamBtn.classList.add('pulse-red');

            // 1. Request Webcam Access
            videoStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
            webcamPreview.srcObject = videoStream;
            webcamPreview.style.display = 'block';
            const placeholder = document.getElementById('webcam-placeholder');
            if (placeholder) placeholder.style.display = 'none';

            // 2. Establish WebSocket Connection
            videoWs = new WebSocket(`${WS_BASE}/ws/analyze_video`);

            videoWs.onopen = () => {
                console.log("Video WebSocket connected. Starting frame streaming...");
                videoStatusEl.style.display = 'block';
                videoStatusEl.style.backgroundColor = 'rgba(10, 132, 255, 0.2)';
                videoStatusEl.style.border = '1px solid #0A84FF';

                // Send frames every 500ms
                frameInterval = setInterval(sendFrameToBackend, 500);
            };

            videoWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.status === 'success') {
                    const verdictEl = document.getElementById('video-verdict');
                    const probEl = document.getElementById('video-prob');

                    const probPercent = Math.round(data.fake_probability * 100);
                    probEl.innerText = `${probPercent}% FAKE`;
                    verdictEl.innerText = data.verdict;

                    // Update visual UI based on live score
                    if (data.verdict === 'FAKE') {
                        videoStatusEl.style.backgroundColor = 'rgba(255, 59, 48, 0.2)';
                        videoStatusEl.style.border = '1px solid #FF003C';
                        verdictEl.style.color = '#FF003C';
                        probEl.style.color = '#FF003C';
                    } else {
                        videoStatusEl.style.backgroundColor = 'rgba(52, 199, 89, 0.2)';
                        videoStatusEl.style.border = '1px solid #00FF41';
                        verdictEl.style.color = '#00FF41';
                        probEl.style.color = '#00FF41';
                    }
                }
            };

            videoWs.onerror = (error) => {
                console.error("Video WebSocket Error:", error);
                stopLiveVideo();
            };

            videoWs.onclose = () => {
                stopLiveVideo();
            };

        } catch (error) {
            console.error("Webcam access denied or error:", error);
            alert("To use Real-Time Webcam Analysis, you must allow browser camera access.");
            stopLiveVideo();
        }
    }

    function sendFrameToBackend() {
        if (!isVideoStreaming || videoWs.readyState !== WebSocket.OPEN) return;

        const context = webcamCanvas.getContext('2d');
        webcamCanvas.width = webcamPreview.videoWidth;
        webcamCanvas.height = webcamPreview.videoHeight;

        // Draw video frame to hidden canvas
        context.drawImage(webcamPreview, 0, 0, webcamCanvas.width, webcamCanvas.height);

        // Convert canvas image to Base64 (compressing slightly)
        const frameData = webcamCanvas.toDataURL('image/jpeg', 0.8);

        // Send Base64 payload over WebSocket
        videoWs.send(frameData);
    }

    function stopLiveVideo() {
        isVideoStreaming = false;
        if (frameInterval) {
            clearInterval(frameInterval);
            frameInterval = null;
        }

        if (videoWs) {
            videoWs.close();
            videoWs = null;
        }
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
            videoStream = null;
        }
        if (webcamPreview) {
            webcamPreview.style.display = 'none';
            // Explicitly clear the object stream to turn off hardware indicators
            webcamPreview.srcObject = null;
            const placeholder = document.getElementById('webcam-placeholder');
            if (placeholder) placeholder.style.display = 'flex';
        }

        if (startWebcamBtn) {
            startWebcamBtn.innerHTML = '<i class="fas fa-camera"></i> Start Live Webcam';
            startWebcamBtn.style.color = '';
            startWebcamBtn.style.borderColor = 'rgba(10, 132, 255, 0.5)';
            startWebcamBtn.style.backgroundColor = 'transparent';
            startWebcamBtn.classList.remove('pulse-red');
            startWebcamBtn.classList.add('pulse-blue');
        }
        if (videoStatusEl) {
            videoStatusEl.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            videoStatusEl.style.border = '1px solid var(--border-color)';
            document.getElementById('video-verdict').innerText = 'Stopped';
            document.getElementById('video-verdict').style.color = 'var(--text-muted)';
            document.getElementById('video-prob').innerText = '--';
            document.getElementById('video-prob').style.color = 'var(--text-muted)';
        }
    }
});

// ----------------------------------------------------------------------
// THREAT HISTORY DATABASE (History Tab)
// ----------------------------------------------------------------------
window.fetchHistory = function () {
    const tableBody = document.getElementById('history-table-body');
    if (!tableBody) return;

    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Fetching records...</td></tr>`;

    fetch('http://127.0.0.1:8000/history/')
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch history");
            return response.json();
        })
        .then(json => {
            const data = json.data;
            if (!data || data.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px;">No historical scan data found.</td></tr>`;
                return;
            }

            let html = '';
            data.forEach(scan => {
                const dateObj = new Date(scan.timestamp);
                const isFake = scan.verdict === 'FAKE';
                const statusColor = isFake ? '#FF003C' : '#00FF41';
                const badge = isFake ? `<span style="background: rgba(255,0,60,0.2); color: #FF003C; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">FAKE (${scan.fake_probability}%)</span>` : `<span style="background: rgba(0,255,65,0.2); color: #00FF41; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">REAL (${scan.fake_probability}%)</span>`;

                html += `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.3s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 15px; font-family: monospace; color: var(--accent-blue);">${scan.scan_id.substring(0, 10)}...</td>
                        <td style="padding: 15px; font-size: 0.9rem; color: var(--text-muted);">${dateObj.toLocaleString()}</td>
                        <td style="padding: 15px; font-size: 0.9rem;">${scan.filename.substring(0, 25)}${scan.filename.length > 25 ? '...' : ''}</td>
                        <td style="padding: 15px;">${isFake ? '<i class="fas fa-times-circle" style="color:#FF003C;"></i>' : '<i class="fas fa-check-circle" style="color:#00FF41;"></i>'}</td>
                        <td style="padding: 15px;">${badge}</td>
                        <td style="padding: 15px;">
                            <a href="http://127.0.0.1:8000/report/${scan.scan_id}" target="_blank" style="color: var(--accent-cyan); text-decoration: none; font-size: 0.9rem; background: rgba(0, 229, 255, 0.1); padding: 5px 10px; border-radius: 4px; border: 1px solid rgba(0, 229, 255, 0.3); transition: all 0.3s; display: inline-block;">
                                <i class="fas fa-file-pdf"></i> Report
                            </a>
                        </td>
                    </tr>
                `;
            });
            tableBody.innerHTML = html;
        })
        .catch(error => {
            console.error(error);
            tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px; color: #FF003C;"><i class="fas fa-exclamation-triangle"></i> Error loading database logs.</td></tr>`;
        });
};
