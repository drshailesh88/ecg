// ============================================
// ECG Guru - Frontend Application Logic
// ============================================

// API Configuration
const API_BASE_URL = window.location.origin; // Assumes server running on same origin

// State Management
const state = {
    uploadedImage: null,
    analysisId: null,
    userLevel: 'student',
    teachingMode: true,
    currentAnalysis: null,
    conversationHistory: []
};

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeDarkMode();
});

// ============================================
// Event Listeners
// ============================================
function initializeEventListeners() {
    // File Upload Events
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileSelectBtn = document.getElementById('fileSelectBtn');
    const cameraBtn = document.getElementById('cameraBtn');
    const cameraInput = document.getElementById('cameraInput');
    const clearImageBtn = document.getElementById('clearImage');

    // Drag and Drop
    dropZone.addEventListener('click', (e) => {
        if (e.target === dropZone || e.target.closest('.drop-zone-text, .drop-zone-subtext, .upload-icon')) {
            fileInput.click();
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    // File Input
    fileSelectBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Camera Input
    cameraBtn.addEventListener('click', () => cameraInput.click());
    cameraInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Clear Image
    clearImageBtn.addEventListener('click', clearUploadedImage);

    // User Level Selection
    document.querySelectorAll('input[name="userLevel"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            state.userLevel = e.target.value;
        });
    });

    // Teaching Mode Toggle
    document.getElementById('teachingMode').addEventListener('change', (e) => {
        state.teachingMode = e.target.checked;
    });

    // Analyze Button
    document.getElementById('analyzeBtn').addEventListener('click', analyzeECG);

    // Chat Interface
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    sendChatBtn.addEventListener('click', sendChatMessage);

    // Dark Mode Toggle
    document.getElementById('darkModeToggle').addEventListener('click', toggleDarkMode);
}

// ============================================
// File Upload Handling
// ============================================
function handleFileUpload(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showToast('Please upload an image file', 'error');
        return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
        showToast('File size must be less than 10MB', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        state.uploadedImage = e.target.result;
        displayImagePreview(e.target.result);
        enableAnalyzeButton();
    };
    reader.onerror = () => {
        showToast('Error reading file', 'error');
    };
    reader.readAsDataURL(file);
}

function displayImagePreview(imageSrc) {
    const dropZone = document.getElementById('dropZone');
    const imagePreview = document.getElementById('imagePreview');
    const previewImage = document.getElementById('previewImage');

    previewImage.src = imageSrc;
    dropZone.classList.add('hidden');
    imagePreview.classList.remove('hidden');
}

function clearUploadedImage() {
    state.uploadedImage = null;
    state.analysisId = null;
    state.currentAnalysis = null;
    state.conversationHistory = [];

    const dropZone = document.getElementById('dropZone');
    const imagePreview = document.getElementById('imagePreview');

    dropZone.classList.remove('hidden');
    imagePreview.classList.add('hidden');

    document.getElementById('fileInput').value = '';
    document.getElementById('cameraInput').value = '';
    document.getElementById('analyzeBtn').disabled = true;

    // Hide results and show welcome screen
    document.getElementById('resultsContainer').classList.add('hidden');
    document.getElementById('welcomeScreen').classList.remove('hidden');
}

function enableAnalyzeButton() {
    document.getElementById('analyzeBtn').disabled = false;
}

// ============================================
// ECG Analysis
// ============================================
async function analyzeECG() {
    if (!state.uploadedImage) {
        showToast('Please upload an ECG image first', 'error');
        return;
    }

    // Show loading state
    showLoadingState('Analyzing ECG...');

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_base64: state.uploadedImage,
                user_level: state.userLevel,
                include_teaching: state.teachingMode
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        state.currentAnalysis = data;
        state.analysisId = data.analysis_id || generateUUID();

        displayAnalysisResults(data);
        hideLoadingState();
        showToast('Analysis complete', 'success');

    } catch (error) {
        console.error('Analysis error:', error);
        hideLoadingState();
        showToast('Failed to analyze ECG. Please try again.', 'error');
    }
}

function displayAnalysisResults(data) {
    // Hide welcome screen and show results
    document.getElementById('welcomeScreen').classList.add('hidden');
    document.getElementById('resultsContainer').classList.remove('hidden');

    // Display Summary
    const urgency = data.is_urgent ? 'critical' : 'normal';
    displaySummary(data.summary, urgency);

    // Display Measurements
    displayMeasurements(data.measurements);

    // Display Findings
    displayFindings(data.findings);

    // Display Algorithm Results (if available)
    if (data.algorithm_results && data.algorithm_results.length > 0) {
        displayAlgorithmResults(data.algorithm_results);
    }

    // Initialize Chat (backend doesn't return suggested_questions in analysis, only in chat)
    initializeChat([]);
}

function displaySummary(summary, urgency) {
    document.getElementById('summaryText').textContent = summary;

    const urgencyBadge = document.getElementById('urgencyBadge');
    if (urgency === 'critical') {
        urgencyBadge.textContent = 'Urgent';
        urgencyBadge.className = 'badge critical';
    } else {
        urgencyBadge.textContent = 'Normal';
        urgencyBadge.className = 'badge normal';
    }
}

function displayMeasurements(measurements) {
    const grid = document.getElementById('measurementsGrid');
    grid.innerHTML = '';

    if (!measurements) {
        grid.innerHTML = '<p style="color: var(--text-secondary);">No measurements available</p>';
        return;
    }

    // Map backend fields to display format
    const measurementMap = [
        { key: 'heart_rate', label: 'Heart Rate', unit: 'bpm' },
        { key: 'pr_interval_ms', label: 'PR Interval', unit: 'ms' },
        { key: 'qrs_duration_ms', label: 'QRS Duration', unit: 'ms' },
        { key: 'qt_interval_ms', label: 'QT Interval', unit: 'ms' },
        { key: 'qtc_ms', label: 'QTc', unit: 'ms' },
        { key: 'axis_degrees', label: 'Axis', unit: '°' },
        { key: 'rhythm', label: 'Rhythm', unit: '' }
    ];

    measurementMap.forEach(({ key, label, unit }) => {
        const value = measurements[key];
        if (value !== null && value !== undefined) {
            const item = document.createElement('div');
            item.className = 'measurement-item';

            const labelDiv = document.createElement('div');
            labelDiv.className = 'measurement-label';
            labelDiv.textContent = label;

            const valueDiv = document.createElement('div');
            valueDiv.className = 'measurement-value normal';
            valueDiv.innerHTML = `${value}<span class="measurement-unit">${unit}</span>`;

            item.appendChild(labelDiv);
            item.appendChild(valueDiv);
            grid.appendChild(item);
        }
    });
}

function displayFindings(findings) {
    const list = document.getElementById('findingsList');
    list.innerHTML = '';

    if (!findings || findings.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary);">No findings to report</p>';
        return;
    }

    findings.forEach(finding => {
        const item = document.createElement('div');
        item.className = `finding-item ${finding.severity || 'normal'}`;

        const icon = document.createElement('div');
        icon.className = 'finding-icon';
        icon.innerHTML = getSeverityIcon(finding.severity);

        const content = document.createElement('div');
        content.className = 'finding-content';

        const title = document.createElement('div');
        title.className = 'finding-title';
        title.textContent = `${finding.category}: ${finding.finding}`;

        const description = document.createElement('div');
        description.className = 'finding-description';
        description.textContent = finding.explanation;

        content.appendChild(title);
        content.appendChild(description);

        if (state.teachingMode && finding.teaching_point) {
            const teaching = document.createElement('div');
            teaching.className = 'finding-teaching';
            teaching.innerHTML = `💡 ${finding.teaching_point}`;
            content.appendChild(teaching);
        }

        item.appendChild(icon);
        item.appendChild(content);
        list.appendChild(item);
    });
}

function displayAlgorithmResults(algorithms) {
    const section = document.getElementById('algorithmsSection');
    const list = document.getElementById('algorithmsList');

    section.classList.remove('hidden');
    list.innerHTML = '';

    algorithms.forEach(algo => {
        const item = document.createElement('div');
        item.className = 'algorithm-item';

        const header = document.createElement('div');
        header.className = 'algorithm-header';

        const name = document.createElement('div');
        name.className = 'algorithm-name';
        name.textContent = algo.name;

        const result = document.createElement('div');
        result.className = 'algorithm-result';
        result.textContent = algo.conclusion;

        header.appendChild(name);
        header.appendChild(result);

        const steps = document.createElement('div');
        steps.className = 'algorithm-steps';

        if (algo.steps && algo.steps.length > 0) {
            algo.steps.forEach((step, index) => {
                const stepDiv = document.createElement('div');
                stepDiv.className = 'algorithm-step';

                const stepNumber = document.createElement('div');
                stepNumber.className = 'step-number';
                stepNumber.textContent = index + 1;

                const stepContent = document.createElement('div');
                stepContent.className = 'step-content';
                // Step can be a dict or string, handle both
                if (typeof step === 'string') {
                    stepContent.textContent = step;
                } else {
                    stepContent.textContent = JSON.stringify(step);
                }

                stepDiv.appendChild(stepNumber);
                stepDiv.appendChild(stepContent);
                steps.appendChild(stepDiv);
            });

            header.addEventListener('click', () => {
                item.classList.toggle('expanded');
            });
        }

        item.appendChild(header);
        item.appendChild(steps);
        list.appendChild(item);
    });
}

// ============================================
// Chat Interface
// ============================================
function initializeChat(suggestedQuestions) {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';

    // Display suggested questions
    displaySuggestedQuestions(suggestedQuestions);
}

function displaySuggestedQuestions(questions) {
    const container = document.getElementById('suggestedQuestions');
    container.innerHTML = '';

    if (!questions || questions.length === 0) {
        return;
    }

    questions.forEach(question => {
        const button = document.createElement('button');
        button.className = 'suggested-question';
        button.textContent = question;
        button.addEventListener('click', () => {
            document.getElementById('chatInput').value = question;
            sendChatMessage();
        });
        container.appendChild(button);
    });
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) {
        return;
    }

    if (!state.analysisId) {
        showToast('Please analyze an ECG first', 'error');
        return;
    }

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    // Update conversation history
    state.conversationHistory.push({ role: 'user', content: message });

    // Disable send button
    const sendBtn = document.getElementById('sendChatBtn');
    sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                analysis_id: state.analysisId,
                user_level: state.userLevel,
                conversation_history: state.conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Add assistant response to chat
        addChatMessage(data.response, 'assistant');

        // Update conversation history
        state.conversationHistory.push({ role: 'assistant', content: data.response });

        // Update suggested questions
        if (data.suggested_questions) {
            displaySuggestedQuestions(data.suggested_questions);
        }

    } catch (error) {
        console.error('Chat error:', error);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        sendBtn.disabled = false;
    }
}

function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = `chat-avatar ${sender}`;
    avatar.textContent = sender === 'user' ? 'U' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.textContent = message;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============================================
// Dark Mode
// ============================================
function initializeDarkMode() {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode === 'true') {
        document.body.classList.add('dark-mode');
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
}

// ============================================
// UI Helper Functions
// ============================================
function showLoadingState(message = 'Loading...') {
    document.getElementById('loadingText').textContent = message;
    document.getElementById('welcomeScreen').classList.add('hidden');
    document.getElementById('resultsContainer').classList.add('hidden');
    document.getElementById('loadingScreen').classList.remove('hidden');
}

function hideLoadingState() {
    document.getElementById('loadingScreen').classList.add('hidden');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = document.createElement('div');
    icon.className = 'toast-icon';
    icon.innerHTML = getToastIcon(type);

    const messageDiv = document.createElement('div');
    messageDiv.className = 'toast-message';
    messageDiv.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(messageDiv);
    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function getToastIcon(type) {
    const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-success);"><polyline points="20 6 9 17 4 12"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-danger);"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-info);"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };
    return icons[type] || icons.info;
}

function getSeverityIcon(severity) {
    const icons = {
        normal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-success);"><polyline points="20 6 9 17 4 12"/></svg>',
        abnormal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-warning);"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        critical: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-danger);"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
    };
    return icons[severity] || icons.normal;
}

function formatMeasurementLabel(key) {
    const labels = {
        heart_rate: 'Heart Rate',
        pr_interval: 'PR Interval',
        qrs_duration: 'QRS Duration',
        qt_interval: 'QT Interval',
        qtc: 'QTc',
        axis: 'Axis',
        rhythm: 'Rhythm'
    };
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// ============================================
// Mock Data for Testing (Remove in Production)
// ============================================
// Uncomment the following to test the UI without a backend

/*
function analyzeECG() {
    showLoadingState('Analyzing ECG...');

    setTimeout(() => {
        const mockData = {
            analysis_id: generateUUID(),
            summary: 'Sinus rhythm with normal heart rate. ST segment elevation in leads V2-V4 suggestive of anterior STEMI. Immediate cardiology consultation recommended.',
            urgency: 'critical',
            measurements: {
                heart_rate: { value: 78, unit: 'bpm', status: 'normal' },
                pr_interval: { value: 160, unit: 'ms', status: 'normal' },
                qrs_duration: { value: 92, unit: 'ms', status: 'normal' },
                qt_interval: { value: 380, unit: 'ms', status: 'normal' },
                qtc: { value: 420, unit: 'ms', status: 'normal' },
                axis: { value: 45, unit: '°', status: 'normal' }
            },
            findings: [
                {
                    title: 'ST Segment Elevation',
                    description: 'Significant ST elevation (>2mm) in V2-V4',
                    severity: 'critical',
                    teaching_point: 'ST elevation in consecutive leads suggests acute myocardial infarction. The pattern in V2-V4 indicates LAD territory involvement.'
                },
                {
                    title: 'Normal Sinus Rhythm',
                    description: 'Regular rhythm with P waves before each QRS complex',
                    severity: 'normal',
                    teaching_point: 'Normal sinus rhythm originates from the SA node with a rate between 60-100 bpm.'
                },
                {
                    title: 'Q Waves',
                    description: 'Pathological Q waves present in V2-V3',
                    severity: 'abnormal',
                    teaching_point: 'Pathological Q waves may indicate prior myocardial infarction or acute transmural ischemia.'
                }
            ],
            algorithm_results: [
                {
                    name: 'Brugada Algorithm (VT vs SVT)',
                    result: 'Not Applicable - Regular Rhythm',
                    steps: []
                },
                {
                    name: 'STEMI Localization',
                    result: 'Anterior STEMI (LAD Territory)',
                    steps: [
                        'ST elevation present: Yes (V2-V4)',
                        'Lead distribution: Anterior leads',
                        'Reciprocal changes: None detected',
                        'Culprit vessel: LAD (Left Anterior Descending)'
                    ]
                }
            ],
            suggested_questions: [
                'What is the significance of ST elevation?',
                'Should this patient receive thrombolysis?',
                'What are the next steps in management?',
                'Explain the pathophysiology of STEMI'
            ]
        };

        state.currentAnalysis = mockData;
        state.analysisId = mockData.analysis_id;
        displayAnalysisResults(mockData);
        hideLoadingState();
        showToast('Analysis complete', 'success');
    }, 2000);
}
*/
