/**
 * Wizard Logic for AI SEO Blogger
 * Handles step navigation, mode selection, and terminal simulation.
 */

let currentStep = 1;
const totalSteps = 3;
let terminalInterval = null;

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Wizard
    updateProgress();

    // Initialize Tooltips if any
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});

// Navigation
function nextStep(step) {
    if (step === 2) {
        // Validation for Step 1
        const text = document.getElementById('text_input').value.trim();
        const url = document.getElementById('url_input').value.trim();
        if (!text && !url) {
            alert('주제나 URL을 입력해주세요.');
            return;
        }
    }

    showStep(step);
}

function prevStep(step) {
    showStep(step);
}

function showStep(step) {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(el => el.style.display = 'none');

    // Show target step
    document.getElementById(`step-${step}`).style.display = 'block';

    // Update state
    currentStep = step;
    updateProgress();

    // Update Review Data if entering Step 3
    if (step === 3) {
        updateReviewData();
    }
}

function updateProgress() {
    // Update Step Indicators
    document.querySelectorAll('.step').forEach(el => {
        const stepNum = parseInt(el.getAttribute('data-step'));
        el.classList.remove('active', 'completed');
        if (stepNum === currentStep) {
            el.classList.add('active');
        } else if (stepNum < currentStep) {
            el.classList.add('completed');
        }
    });

    // Update Progress Line
    const progressLine = document.querySelector('.progress-line-fill');
    const percentage = ((currentStep - 1) / (totalSteps - 1)) * 100;
    progressLine.style.width = `${percentage}%`;
}

// Mode Selection
function selectMode(mode) {
    // Visual Update
    document.querySelectorAll('.mode-card').forEach(el => el.classList.remove('selected'));
    document.querySelector(`.mode-card[data-mode="${mode}"]`).classList.add('selected');

    // Value Update
    document.getElementById('ai_mode').value = mode;

    // Smart Defaults Logic
    applySmartDefaults(mode);
}

function applySmartDefaults(mode) {
    const badgesContainer = document.getElementById('active-strategies-badges');
    badgesContainer.innerHTML = ''; // Clear existing

    let strategies = [];

    if (mode === 'enhanced') {
        // Auto-check advanced options
        document.getElementById('aeo').checked = true;
        document.getElementById('geo').checked = true;
        document.getElementById('aio').checked = true;
        document.getElementById('ai_seo').checked = true;
        document.getElementById('ai_search').checked = true;

        strategies = ['AEO', 'GEO', 'AIO', 'AI SEO', 'AI Search'];
    } else if (mode === 'news') {
        // Reset advanced options
        document.querySelectorAll('input[name="rules"]').forEach(cb => cb.checked = false);
        document.getElementById('ai_seo').checked = true; // Basic SEO for news

        strategies = ['AI SEO (Basic)'];
    } else {
        // Blog mode defaults
        document.querySelectorAll('input[name="rules"]').forEach(cb => cb.checked = false);
        document.getElementById('ai_seo').checked = true;
        document.getElementById('ai_search').checked = true;

        strategies = ['AI SEO', 'AI Search'];
    }

    // Render Badges
    strategies.forEach(strat => {
        const badge = document.createElement('span');
        badge.className = 'badge bg-secondary';
        badge.textContent = strat;
        badgesContainer.appendChild(badge);
    });
}

// UI Helpers
function toggleUrlInput() {
    const urlInput = document.getElementById('url_input');
    const textInput = document.getElementById('text_input');

    if (urlInput.classList.contains('d-none')) {
        urlInput.classList.remove('d-none');
        urlInput.focus();
        textInput.placeholder = "URL에 대한 추가 설명이나 지시사항을 입력하세요...";
    } else {
        urlInput.classList.add('d-none');
        textInput.placeholder = "예: '2025년 SEO 트렌드' 또는 분석할 URL 입력...";
    }
}

function toggleAdvancedSettings() {
    const settings = document.getElementById('advanced-settings');
    const view = document.getElementById('smart-defaults-view');
    const toggle = document.getElementById('advanced-toggle');

    if (toggle.checked) {
        settings.style.display = 'block';
        view.style.display = 'none';
    } else {
        settings.style.display = 'none';
        view.style.display = 'block';
    }
}

function updateReviewData() {
    const text = document.getElementById('text_input').value;
    const url = document.getElementById('url_input').value;
    const mode = document.getElementById('ai_mode').value;
    const length = document.getElementById('content_length').options[document.getElementById('content_length').selectedIndex].text;

    // Topic
    const topic = url ? `URL: ${url}` : (text.length > 50 ? text.substring(0, 50) + '...' : text);
    document.getElementById('review-topic').textContent = topic;

    // Mode
    const modeBadge = document.getElementById('review-mode');
    modeBadge.textContent = mode.toUpperCase();
    modeBadge.className = `badge ${mode === 'enhanced' ? 'bg-primary' : 'bg-dark'}`;

    // Length
    document.getElementById('review-length').textContent = length;

    // Strategies
    const checkedRules = Array.from(document.querySelectorAll('input[name="rules"]:checked')).map(cb => cb.nextElementSibling.textContent);
    document.getElementById('review-strategies').textContent = checkedRules.length > 0 ? checkedRules.join(', ') : '기본 설정';
}

// Terminal Simulation
function addTerminalLog(message, type = 'info') {
    const logs = document.getElementById('terminal-logs');
    const line = document.createElement('div');
    line.className = 'log-line';

    let icon = '➜';
    let colorClass = 'text-success';

    if (type === 'process') { icon = '⚙️'; colorClass = 'text-warning'; }
    if (type === 'success') { icon = '✅'; colorClass = 'text-success'; }
    if (type === 'error') { icon = '❌'; colorClass = 'text-danger'; }

    line.innerHTML = `<span class="${colorClass}">${icon}</span> ${message}`;
    logs.appendChild(line);
    logs.scrollTop = logs.scrollHeight;
}

// Generation Wrapper
async function startGeneration() {
    // UI Update
    document.getElementById('action-buttons').style.display = 'none';
    document.getElementById('live-terminal').style.display = 'block';
    document.getElementById('cancel-area').style.display = 'block';

    // Start Terminal Logs
    addTerminalLog('Initializing AI Agent...', 'process');

    // Simulate initial checks
    setTimeout(() => addTerminalLog('Validating inputs...', 'process'), 500);
    setTimeout(() => addTerminalLog('Connecting to Gemini 2.0 Flash...', 'process'), 1000);

    // Call original generate function (from index.html)
    // We need to make sure generateContent is accessible or we wrap it here
    try {
        await generateContent(); // This calls the function in index.html

        // Success handling is done in generateContent, but we can add final logs here if needed
        addTerminalLog('Content generation completed successfully!', 'success');

        // Hide terminal and show result (handled in index.html, but we can smooth it)
        setTimeout(() => {
            document.getElementById('wizard-container').style.display = 'none';
            document.getElementById('result-wrapper').style.display = 'block';
        }, 1500);

    } catch (error) {
        addTerminalLog(`Error: ${error.message}`, 'error');
        document.getElementById('action-buttons').style.display = 'flex';
        document.getElementById('cancel-area').style.display = 'none';
    }
}

function resetWizard() {
    document.getElementById('result-wrapper').style.display = 'none';
    document.getElementById('wizard-container').style.display = 'block';
    showStep(1);

    // Reset inputs
    document.getElementById('text_input').value = '';
    document.getElementById('url_input').value = '';
    document.getElementById('terminal-logs').innerHTML = '<div class="log-line"><span class="text-success">➜</span> System initialized...</div>';
    document.getElementById('action-buttons').style.display = 'flex';
    document.getElementById('live-terminal').style.display = 'none';
    document.getElementById('cancel-area').style.display = 'none';
}
