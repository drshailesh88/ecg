/**
 * ============================================
 * ECG Guru - Production Frontend Application
 * ============================================
 *
 * A premium ECG analysis web application with:
 * - Smooth animations and micro-interactions
 * - Streaming AI responses
 * - Offline PWA support
 * - Comprehensive keyboard shortcuts
 * - Production-grade error handling
 *
 * @version 2.0.0
 * @author ECG Guru Team
 */

'use strict';

// ============================================
// Configuration & Constants
// ============================================

const CONFIG = {
    API_BASE_URL: window.location.origin,
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    DEBOUNCE_DELAY: 300,
    ANIMATION_DURATION: 300,
    TOAST_DURATION: 5000,
    TYPEWRITER_SPEED: 20, // ms per character
    IMAGE_QUALITY: 0.9,
    SUPPORTED_FORMATS: ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'],
};

const IS_PRODUCTION = !window.location.hostname.match(/localhost|127\.0\.0\.1/);

// ============================================
// State Management
// ============================================

/**
 * Centralized application state manager
 */
class ECGGuruApp {
    constructor() {
        this.state = {
            userLevel: 'student',
            teachingMode: true,
            darkMode: false,
            isLoading: false,
            isAnalyzing: false,
            currentAnalysis: null,
            analysisId: null,
            uploadedImage: null,
            chatHistory: [],
            suggestedQuestions: [],
            imageZoom: 1,
            offline: !navigator.onLine,
        };

        this.listeners = new Map();
        this.abortControllers = new Map();
    }

    /**
     * Update state and notify listeners
     * @param {Object} updates - State updates
     */
    setState(updates) {
        const oldState = { ...this.state };
        this.state = { ...this.state, ...updates };

        // Notify listeners of state changes
        Object.keys(updates).forEach(key => {
            if (this.listeners.has(key)) {
                this.listeners.get(key).forEach(callback => {
                    callback(this.state[key], oldState[key]);
                });
            }
        });
    }

    /**
     * Subscribe to state changes
     * @param {string} key - State key to watch
     * @param {Function} callback - Callback function
     */
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);

        // Return unsubscribe function
        return () => {
            this.listeners.get(key).delete(callback);
        };
    }

    /**
     * Reset application state
     */
    reset() {
        this.setState({
            currentAnalysis: null,
            analysisId: null,
            uploadedImage: null,
            chatHistory: [],
            suggestedQuestions: [],
            imageZoom: 1,
            isAnalyzing: false,
        });

        // Cancel all pending requests
        this.abortControllers.forEach(controller => controller.abort());
        this.abortControllers.clear();
    }

    /**
     * Get abort controller for a request
     * @param {string} key - Request identifier
     * @returns {AbortController}
     */
    getAbortController(key) {
        if (this.abortControllers.has(key)) {
            this.abortControllers.get(key).abort();
        }
        const controller = new AbortController();
        this.abortControllers.set(key, controller);
        return controller;
    }
}

// Initialize app
const app = new ECGGuruApp();

// ============================================
// API Service Layer
// ============================================

/**
 * API service for backend communication
 */
const API = {
    /**
     * Analyze ECG image
     * @param {string} imageData - Base64 encoded image
     * @param {string} userLevel - User expertise level
     * @param {boolean} includeTeaching - Include teaching points
     * @returns {Promise<Object>}
     */
    async analyzeECG(imageData, userLevel, includeTeaching) {
        const controller = app.getAbortController('analyze');

        const response = await fetch(`${CONFIG.API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_base64: imageData,
                user_level: userLevel,
                include_teaching: includeTeaching,
            }),
            signal: controller.signal,
        });

        if (!response.ok) {
            throw new APIError(`Analysis failed: ${response.statusText}`, response.status);
        }

        return response.json();
    },

    /**
     * Send chat message
     * @param {string} message - User message
     * @param {string} analysisId - Analysis ID
     * @param {Array} history - Conversation history
     * @returns {Promise<Object>}
     */
    async chat(message, analysisId, history) {
        const controller = app.getAbortController('chat');

        const response = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                analysis_id: analysisId,
                user_level: app.state.userLevel,
                conversation_history: history,
            }),
            signal: controller.signal,
        });

        if (!response.ok) {
            throw new APIError(`Chat failed: ${response.statusText}`, response.status);
        }

        return response.json();
    },

    /**
     * Stream chat response (for future streaming support)
     * @param {string} message - User message
     * @param {string} analysisId - Analysis ID
     * @returns {AsyncGenerator<string>}
     */
    async *streamChat(message, analysisId) {
        // Placeholder for streaming implementation
        // When backend supports SSE or WebSocket, implement here
        const response = await this.chat(message, analysisId, app.state.chatHistory);
        yield response.response;
    },
};

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }
}

// ============================================
// UI Controllers
// ============================================

/**
 * Upload Controller
 */
const UploadController = {
    dropZone: null,
    fileInput: null,
    cameraInput: null,
    previewContainer: null,
    previewImage: null,

    init() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.cameraInput = document.getElementById('cameraInput');
        this.previewContainer = document.getElementById('imagePreview');
        this.previewImage = document.getElementById('previewImage');

        this.attachEvents();
    },

    attachEvents() {
        // Drag and drop events
        this.dropZone.addEventListener('click', (e) => {
            if (e.target === this.dropZone || e.target.closest('.drop-zone-text, .drop-zone-subtext, .upload-icon')) {
                this.fileInput.click();
            }
        });

        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('drag-over');
            this.addGlowEffect();
        });

        this.dropZone.addEventListener('dragleave', (e) => {
            if (e.target === this.dropZone) {
                this.dropZone.classList.remove('drag-over');
                this.removeGlowEffect();
            }
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('drag-over');
            this.removeGlowEffect();

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });

        // File input events
        document.getElementById('fileSelectBtn')?.addEventListener('click', () => {
            this.fileInput.click();
        });

        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });

        // Camera input events
        document.getElementById('cameraBtn')?.addEventListener('click', () => {
            this.cameraInput.click();
        });

        this.cameraInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });

        // Clear image button
        document.getElementById('clearImage')?.addEventListener('click', () => {
            this.clearImage();
        });

        // Image zoom controls
        this.previewImage.addEventListener('click', () => {
            this.toggleZoom();
        });
    },

    /**
     * Add glow effect on drag over
     */
    addGlowEffect() {
        this.dropZone.style.boxShadow = '0 0 30px rgba(52, 152, 219, 0.5)';
    },

    /**
     * Remove glow effect
     */
    removeGlowEffect() {
        this.dropZone.style.boxShadow = '';
    },

    /**
     * Handle file upload
     * @param {File} file - Uploaded file
     */
    async handleFile(file) {
        // Validate file type
        if (!CONFIG.SUPPORTED_FORMATS.includes(file.type)) {
            ToastService.error('Please upload a valid image file (JPEG, PNG, WebP)');
            return;
        }

        // Validate file size
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            ToastService.error('File size must be less than 10MB');
            return;
        }

        // Show upload progress
        this.showUploadProgress();

        try {
            const imageData = await this.readFileAsDataURL(file);
            app.setState({ uploadedImage: imageData });
            await this.displayPreview(imageData);
            this.enableAnalyzeButton();
            ToastService.success('Image uploaded successfully');
        } catch (error) {
            this.logError('File upload error', error);
            ToastService.error('Failed to upload image. Please try again.');
        } finally {
            this.hideUploadProgress();
        }
    },

    /**
     * Read file as data URL
     * @param {File} file - File to read
     * @returns {Promise<string>}
     */
    readFileAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsDataURL(file);
        });
    },

    /**
     * Display image preview
     * @param {string} imageSrc - Image source
     */
    async displayPreview(imageSrc) {
        this.previewImage.src = imageSrc;

        await AnimationService.fadeOut(this.dropZone);
        this.dropZone.classList.add('hidden');

        this.previewContainer.classList.remove('hidden');
        await AnimationService.fadeIn(this.previewContainer);
    },

    /**
     * Clear uploaded image
     */
    async clearImage() {
        app.reset();

        await AnimationService.fadeOut(this.previewContainer);
        this.previewContainer.classList.add('hidden');

        this.dropZone.classList.remove('hidden');
        await AnimationService.fadeIn(this.dropZone);

        this.fileInput.value = '';
        this.cameraInput.value = '';
        this.previewImage.src = '';

        document.getElementById('analyzeBtn').disabled = true;

        // Show welcome screen
        document.getElementById('resultsContainer')?.classList.add('hidden');
        document.getElementById('welcomeScreen')?.classList.remove('hidden');
    },

    /**
     * Toggle image zoom
     */
    toggleZoom() {
        const currentZoom = app.state.imageZoom;
        const newZoom = currentZoom === 1 ? 2 : 1;

        app.setState({ imageZoom: newZoom });
        this.previewImage.style.transform = `scale(${newZoom})`;
        this.previewImage.style.cursor = newZoom === 1 ? 'zoom-in' : 'zoom-out';
        this.previewImage.style.transition = 'transform 0.3s ease';
    },

    /**
     * Enable analyze button
     */
    enableAnalyzeButton() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = false;
        analyzeBtn.classList.add('pulse');
        setTimeout(() => analyzeBtn.classList.remove('pulse'), 1000);
    },

    /**
     * Show upload progress
     */
    showUploadProgress() {
        const progressBar = document.getElementById('uploadProgress');
        if (progressBar) {
            progressBar.style.display = 'block';
            progressBar.style.width = '0%';

            // Simulate progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                progressBar.style.width = `${progress}%`;
                if (progress >= 90) {
                    clearInterval(interval);
                }
            }, 50);
        }
    },

    /**
     * Hide upload progress
     */
    hideUploadProgress() {
        const progressBar = document.getElementById('uploadProgress');
        if (progressBar) {
            progressBar.style.width = '100%';
            setTimeout(() => {
                progressBar.style.display = 'none';
            }, 300);
        }
    },

    /**
     * Log error (only in development)
     * @param {string} context - Error context
     * @param {Error} error - Error object
     */
    logError(context, error) {
        if (!IS_PRODUCTION) {
            console.error(`[${context}]`, error);
        }
    },
};

/**
 * Analysis Controller
 */
const AnalysisController = {
    init() {
        document.getElementById('analyzeBtn')?.addEventListener('click', () => {
            this.analyze();
        });
    },

    /**
     * Analyze ECG
     */
    async analyze() {
        if (!app.state.uploadedImage) {
            ToastService.error('Please upload an ECG image first');
            return;
        }

        app.setState({ isAnalyzing: true });
        this.showLoadingSkeleton();

        try {
            const data = await API.analyzeECG(
                app.state.uploadedImage,
                app.state.userLevel,
                app.state.teachingMode
            );

            app.setState({
                currentAnalysis: data,
                analysisId: data.analysis_id || this.generateUUID(),
            });

            await this.displayResults(data);
            ToastService.success('Analysis complete');
        } catch (error) {
            if (error.name === 'AbortError') return;

            this.logError('Analysis error', error);
            ToastService.error(
                error instanceof APIError
                    ? 'Analysis service unavailable. Please try again.'
                    : 'Failed to analyze ECG. Please check your connection.'
            );
        } finally {
            app.setState({ isAnalyzing: false });
            this.hideLoadingSkeleton();
        }
    },

    /**
     * Display analysis results with animations
     * @param {Object} data - Analysis data
     */
    async displayResults(data) {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const resultsContainer = document.getElementById('resultsContainer');

        // Hide welcome screen
        if (welcomeScreen && !welcomeScreen.classList.contains('hidden')) {
            await AnimationService.fadeOut(welcomeScreen);
            welcomeScreen.classList.add('hidden');
        }

        // Show results container
        resultsContainer.classList.remove('hidden');
        await AnimationService.fadeIn(resultsContainer);

        // Display components with staggered animation
        await this.displaySummary(data);
        await this.delay(100);
        await this.displayMeasurements(data.measurements);
        await this.delay(100);
        await this.displayFindings(data.findings);
        await this.delay(100);

        if (data.algorithm_results?.length > 0) {
            await this.displayAlgorithms(data.algorithm_results);
        }

        // Initialize chat with suggested questions
        ChatController.initialize(data.suggested_questions || []);
    },

    /**
     * Display summary section
     * @param {Object} data - Analysis data
     */
    async displaySummary(data) {
        const summaryText = document.getElementById('summaryText');
        const urgencyBadge = document.getElementById('urgencyBadge');

        if (summaryText) {
            await AnimationService.typewriter(summaryText, data.summary || 'Analysis complete');
        }

        if (urgencyBadge) {
            const isUrgent = data.is_urgent || false;
            urgencyBadge.textContent = isUrgent ? 'Urgent' : 'Normal';
            urgencyBadge.className = `badge ${isUrgent ? 'critical' : 'normal'}`;
            AnimationService.pulse(urgencyBadge);
        }
    },

    /**
     * Display measurements grid
     * @param {Object} measurements - Measurement data
     */
    async displayMeasurements(measurements) {
        const grid = document.getElementById('measurementsGrid');
        if (!grid) return;

        grid.innerHTML = '';

        if (!measurements) {
            grid.innerHTML = '<p class="text-secondary">No measurements available</p>';
            return;
        }

        const measurementMap = [
            { key: 'heart_rate', label: 'Heart Rate', unit: 'bpm' },
            { key: 'pr_interval_ms', label: 'PR Interval', unit: 'ms' },
            { key: 'qrs_duration_ms', label: 'QRS Duration', unit: 'ms' },
            { key: 'qt_interval_ms', label: 'QT Interval', unit: 'ms' },
            { key: 'qtc_ms', label: 'QTc', unit: 'ms' },
            { key: 'axis_degrees', label: 'Axis', unit: '°' },
            { key: 'rhythm', label: 'Rhythm', unit: '' },
        ];

        measurementMap.forEach(({ key, label, unit }, index) => {
            const value = measurements[key];
            if (value !== null && value !== undefined) {
                const item = this.createMeasurementItem(label, value, unit);
                grid.appendChild(item);

                // Stagger animation
                setTimeout(() => {
                    AnimationService.slideIn(item);
                }, index * 50);
            }
        });
    },

    /**
     * Create measurement item
     * @param {string} label - Measurement label
     * @param {*} value - Measurement value
     * @param {string} unit - Unit
     * @returns {HTMLElement}
     */
    createMeasurementItem(label, value, unit) {
        const item = document.createElement('div');
        item.className = 'measurement-item';
        item.style.opacity = '0';

        const labelDiv = document.createElement('div');
        labelDiv.className = 'measurement-label';
        labelDiv.textContent = label;

        const valueDiv = document.createElement('div');
        valueDiv.className = 'measurement-value normal';
        valueDiv.innerHTML = `${value}<span class="measurement-unit">${unit}</span>`;

        item.appendChild(labelDiv);
        item.appendChild(valueDiv);

        return item;
    },

    /**
     * Display findings list
     * @param {Array} findings - Findings array
     */
    async displayFindings(findings) {
        const list = document.getElementById('findingsList');
        if (!list) return;

        list.innerHTML = '';

        if (!findings || findings.length === 0) {
            list.innerHTML = '<p class="text-secondary">No findings to report</p>';
            return;
        }

        findings.forEach((finding, index) => {
            const item = this.createFindingItem(finding);
            list.appendChild(item);

            // Stagger animation with color-coded entrance
            setTimeout(() => {
                AnimationService.slideIn(item);
                this.highlightBySeverity(item, finding.severity);
            }, index * 100);
        });
    },

    /**
     * Create finding item
     * @param {Object} finding - Finding data
     * @returns {HTMLElement}
     */
    createFindingItem(finding) {
        const item = document.createElement('div');
        item.className = `finding-item ${finding.severity || 'normal'}`;
        item.style.opacity = '0';

        const icon = document.createElement('div');
        icon.className = 'finding-icon';
        icon.innerHTML = this.getSeverityIcon(finding.severity);

        const content = document.createElement('div');
        content.className = 'finding-content';

        const title = document.createElement('div');
        title.className = 'finding-title';
        title.textContent = `${finding.category || 'Finding'}: ${finding.finding}`;

        const description = document.createElement('div');
        description.className = 'finding-description';
        description.textContent = finding.explanation;

        content.appendChild(title);
        content.appendChild(description);

        if (app.state.teachingMode && finding.teaching_point) {
            const teaching = document.createElement('div');
            teaching.className = 'finding-teaching';
            teaching.innerHTML = `💡 ${finding.teaching_point}`;
            content.appendChild(teaching);
        }

        item.appendChild(icon);
        item.appendChild(content);

        return item;
    },

    /**
     * Display algorithm results
     * @param {Array} algorithms - Algorithm results
     */
    async displayAlgorithms(algorithms) {
        const section = document.getElementById('algorithmsSection');
        const list = document.getElementById('algorithmsList');

        if (!section || !list) return;

        section.classList.remove('hidden');
        list.innerHTML = '';

        algorithms.forEach((algo, index) => {
            const item = this.createAlgorithmItem(algo);
            list.appendChild(item);

            setTimeout(() => {
                AnimationService.slideIn(item);
            }, index * 100);
        });
    },

    /**
     * Create algorithm item
     * @param {Object} algo - Algorithm data
     * @returns {HTMLElement}
     */
    createAlgorithmItem(algo) {
        const item = document.createElement('div');
        item.className = 'algorithm-item';
        item.style.opacity = '0';

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

        if (algo.steps?.length > 0) {
            algo.steps.forEach((step, index) => {
                const stepDiv = this.createStepItem(step, index + 1);
                steps.appendChild(stepDiv);
            });

            // Add click to expand
            header.addEventListener('click', () => {
                item.classList.toggle('expanded');
                AnimationService.pulse(header);
            });
            header.style.cursor = 'pointer';
        }

        item.appendChild(header);
        item.appendChild(steps);

        return item;
    },

    /**
     * Create algorithm step item
     * @param {string|Object} step - Step data
     * @param {number} number - Step number
     * @returns {HTMLElement}
     */
    createStepItem(step, number) {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'algorithm-step';

        const stepNumber = document.createElement('div');
        stepNumber.className = 'step-number';
        stepNumber.textContent = number;

        const stepContent = document.createElement('div');
        stepContent.className = 'step-content';
        stepContent.textContent = typeof step === 'string' ? step : JSON.stringify(step);

        stepDiv.appendChild(stepNumber);
        stepDiv.appendChild(stepContent);

        return stepDiv;
    },

    /**
     * Highlight element by severity
     * @param {HTMLElement} element - Element to highlight
     * @param {string} severity - Severity level
     */
    highlightBySeverity(element, severity) {
        const colors = {
            normal: 'var(--color-success)',
            abnormal: 'var(--color-warning)',
            critical: 'var(--color-danger)',
        };

        const color = colors[severity] || colors.normal;
        element.style.borderLeft = `4px solid ${color}`;
    },

    /**
     * Get severity icon SVG
     * @param {string} severity - Severity level
     * @returns {string}
     */
    getSeverityIcon(severity) {
        const icons = {
            normal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-success);"><polyline points="20 6 9 17 4 12"/></svg>',
            abnormal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-warning);"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            critical: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-danger);"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
        };
        return icons[severity] || icons.normal;
    },

    /**
     * Show loading skeleton
     */
    showLoadingSkeleton() {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.classList.remove('hidden');
            AnimationService.fadeIn(loadingScreen);
        }
    },

    /**
     * Hide loading skeleton
     */
    hideLoadingSkeleton() {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            AnimationService.fadeOut(loadingScreen).then(() => {
                loadingScreen.classList.add('hidden');
            });
        }
    },

    /**
     * Delay helper
     * @param {number} ms - Milliseconds
     * @returns {Promise}
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * Generate UUID
     * @returns {string}
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    },

    /**
     * Log error (only in development)
     * @param {string} context - Error context
     * @param {Error} error - Error object
     */
    logError(context, error) {
        if (!IS_PRODUCTION) {
            console.error(`[${context}]`, error);
        }
    },
};

/**
 * Chat Controller
 */
const ChatController = {
    chatInput: null,
    chatMessages: null,
    sendBtn: null,
    suggestedQuestionsContainer: null,

    init() {
        this.chatInput = document.getElementById('chatInput');
        this.chatMessages = document.getElementById('chatMessages');
        this.sendBtn = document.getElementById('sendChatBtn');
        this.suggestedQuestionsContainer = document.getElementById('suggestedQuestions');

        this.attachEvents();
    },

    attachEvents() {
        // Send message on Enter (Cmd/Ctrl + Enter for multi-line)
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button click
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // Auto-resize textarea
        this.chatInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
    },

    /**
     * Initialize chat interface
     * @param {Array} suggestedQuestions - Suggested questions
     */
    initialize(suggestedQuestions = []) {
        this.chatMessages.innerHTML = '';
        this.displaySuggestedQuestions(suggestedQuestions);
    },

    /**
     * Display suggested questions as clickable pills
     * @param {Array} questions - Questions array
     */
    displaySuggestedQuestions(questions) {
        this.suggestedQuestionsContainer.innerHTML = '';

        if (!questions || questions.length === 0) return;

        questions.forEach((question, index) => {
            const pill = document.createElement('button');
            pill.className = 'suggested-question';
            pill.textContent = question;
            pill.style.opacity = '0';

            pill.addEventListener('click', () => {
                this.chatInput.value = question;
                this.sendMessage();
                AnimationService.pulse(pill);
            });

            this.suggestedQuestionsContainer.appendChild(pill);

            // Stagger animation
            setTimeout(() => {
                AnimationService.slideIn(pill);
            }, index * 50);
        });
    },

    /**
     * Send chat message
     */
    async sendMessage() {
        const message = this.chatInput.value.trim();

        if (!message) return;

        if (!app.state.analysisId) {
            ToastService.error('Please analyze an ECG first');
            return;
        }

        // Add user message
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        this.autoResizeTextarea();

        // Update state
        const history = [...app.state.chatHistory, { role: 'user', content: message }];
        app.setState({ chatHistory: history });

        // Disable send button
        this.sendBtn.disabled = true;
        this.sendBtn.classList.add('loading');

        // Show typing indicator
        const typingIndicator = this.addTypingIndicator();

        try {
            const response = await API.chat(
                message,
                app.state.analysisId,
                history
            );

            // Remove typing indicator
            typingIndicator.remove();

            // Add assistant message with typewriter effect
            await this.addMessage(response.response, 'assistant', true);

            // Update state
            app.setState({
                chatHistory: [...history, { role: 'assistant', content: response.response }],
            });

            // Update suggested questions
            if (response.suggested_questions) {
                this.displaySuggestedQuestions(response.suggested_questions);
            }

        } catch (error) {
            if (error.name === 'AbortError') return;

            typingIndicator.remove();
            this.logError('Chat error', error);
            this.addMessage(
                'Sorry, I encountered an error. Please try again.',
                'assistant'
            );
        } finally {
            this.sendBtn.disabled = false;
            this.sendBtn.classList.remove('loading');
        }
    },

    /**
     * Add message to chat
     * @param {string} message - Message text
     * @param {string} sender - 'user' or 'assistant'
     * @param {boolean} animate - Whether to animate (typewriter effect)
     */
    async addMessage(message, sender, animate = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.style.opacity = '0';

        const avatar = document.createElement('div');
        avatar.className = `chat-avatar ${sender}`;
        avatar.textContent = sender === 'user' ? 'U' : 'AI';

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';

        // Add copy button for assistant messages
        if (sender === 'assistant') {
            const copyBtn = this.createCopyButton(message);
            bubble.appendChild(copyBtn);
        }

        const content = document.createElement('div');
        content.className = 'chat-content';

        bubble.appendChild(content);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);

        // Animate entrance
        await AnimationService.slideIn(messageDiv);

        // Render message (with markdown for assistant)
        if (animate && sender === 'assistant') {
            await AnimationService.typewriter(content, message, CONFIG.TYPEWRITER_SPEED);
        } else {
            if (sender === 'assistant') {
                content.innerHTML = this.renderMarkdown(message);
            } else {
                content.textContent = message;
            }
        }

        // Scroll to bottom smoothly
        this.scrollToBottom();
    },

    /**
     * Create copy button for message
     * @param {string} text - Text to copy
     * @returns {HTMLElement}
     */
    createCopyButton(text) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
        copyBtn.title = 'Copy response';

        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(text);
                copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
                ToastService.success('Copied to clipboard');

                setTimeout(() => {
                    copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
                }, 2000);
            } catch (error) {
                ToastService.error('Failed to copy');
            }
        });

        return copyBtn;
    },

    /**
     * Add typing indicator
     * @returns {HTMLElement}
     */
    addTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message assistant typing-indicator';

        const avatar = document.createElement('div');
        avatar.className = 'chat-avatar assistant';
        avatar.textContent = 'AI';

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);

        this.scrollToBottom();

        return messageDiv;
    },

    /**
     * Render markdown (simple implementation)
     * @param {string} text - Markdown text
     * @returns {string}
     */
    renderMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    },

    /**
     * Auto-resize textarea
     */
    autoResizeTextarea() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 150) + 'px';
    },

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        this.chatMessages.scrollTo({
            top: this.chatMessages.scrollHeight,
            behavior: 'smooth',
        });
    },

    /**
     * Log error (only in development)
     * @param {string} context - Error context
     * @param {Error} error - Error object
     */
    logError(context, error) {
        if (!IS_PRODUCTION) {
            console.error(`[${context}]`, error);
        }
    },
};

// ============================================
// Services
// ============================================

/**
 * Animation Service
 */
const AnimationService = {
    /**
     * Fade in element
     * @param {HTMLElement} element - Element to animate
     * @returns {Promise}
     */
    fadeIn(element) {
        return new Promise((resolve) => {
            element.style.opacity = '0';
            element.style.transition = `opacity ${CONFIG.ANIMATION_DURATION}ms ease`;

            requestAnimationFrame(() => {
                element.style.opacity = '1';
                setTimeout(resolve, CONFIG.ANIMATION_DURATION);
            });
        });
    },

    /**
     * Fade out element
     * @param {HTMLElement} element - Element to animate
     * @returns {Promise}
     */
    fadeOut(element) {
        return new Promise((resolve) => {
            element.style.opacity = '1';
            element.style.transition = `opacity ${CONFIG.ANIMATION_DURATION}ms ease`;

            requestAnimationFrame(() => {
                element.style.opacity = '0';
                setTimeout(resolve, CONFIG.ANIMATION_DURATION);
            });
        });
    },

    /**
     * Slide in element
     * @param {HTMLElement} element - Element to animate
     */
    slideIn(element) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = `opacity ${CONFIG.ANIMATION_DURATION}ms ease, transform ${CONFIG.ANIMATION_DURATION}ms ease`;

        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        });
    },

    /**
     * Pulse animation
     * @param {HTMLElement} element - Element to animate
     */
    pulse(element) {
        element.classList.add('pulse');
        setTimeout(() => {
            element.classList.remove('pulse');
        }, 600);
    },

    /**
     * Typewriter effect
     * @param {HTMLElement} element - Element to type into
     * @param {string} text - Text to type
     * @param {number} speed - Speed in ms per character
     * @returns {Promise}
     */
    typewriter(element, text, speed = CONFIG.TYPEWRITER_SPEED) {
        return new Promise((resolve) => {
            let index = 0;
            element.textContent = '';

            const type = () => {
                if (index < text.length) {
                    element.textContent += text.charAt(index);
                    index++;
                    setTimeout(type, speed);
                } else {
                    resolve();
                }
            };

            type();
        });
    },
};

/**
 * Toast Service
 */
const ToastService = {
    container: null,

    init() {
        this.container = document.getElementById('toastContainer');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toastContainer';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, info)
     */
    show(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = document.createElement('div');
        icon.className = 'toast-icon';
        icon.innerHTML = this.getIcon(type);

        const messageDiv = document.createElement('div');
        messageDiv.className = 'toast-message';
        messageDiv.textContent = message;

        toast.appendChild(icon);
        toast.appendChild(messageDiv);
        this.container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), CONFIG.ANIMATION_DURATION);
        }, CONFIG.TOAST_DURATION);
    },

    success(message) {
        this.show(message, 'success');
    },

    error(message) {
        this.show(message, 'error');
    },

    info(message) {
        this.show(message, 'info');
    },

    /**
     * Get icon SVG for toast type
     * @param {string} type - Toast type
     * @returns {string}
     */
    getIcon(type) {
        const icons = {
            success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
            error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        };
        return icons[type] || icons.info;
    },
};

/**
 * Dark Mode Service
 */
const DarkModeService = {
    init() {
        // Load saved preference
        const savedMode = localStorage.getItem('darkMode');
        if (savedMode === 'true') {
            this.enable();
        }

        // Listen for system preference changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (localStorage.getItem('darkMode') === null) {
                    e.matches ? this.enable() : this.disable();
                }
            });
        }

        // Toggle button
        document.getElementById('darkModeToggle')?.addEventListener('click', () => {
            this.toggle();
        });
    },

    enable() {
        document.body.classList.add('dark-mode');
        app.setState({ darkMode: true });
        localStorage.setItem('darkMode', 'true');
    },

    disable() {
        document.body.classList.remove('dark-mode');
        app.setState({ darkMode: false });
        localStorage.setItem('darkMode', 'false');
    },

    toggle() {
        if (app.state.darkMode) {
            this.disable();
        } else {
            this.enable();
        }
    },
};

/**
 * Keyboard Shortcuts Service
 */
const KeyboardService = {
    init() {
        document.addEventListener('keydown', (e) => {
            // Cmd/Ctrl + U: Focus upload
            if ((e.metaKey || e.ctrlKey) && e.key === 'u') {
                e.preventDefault();
                document.getElementById('fileInput')?.click();
            }

            // Cmd/Ctrl + Enter: Send chat (handled in ChatController)
            // Already implemented

            // Escape: Close modals, clear focus
            if (e.key === 'Escape') {
                this.handleEscape();
            }

            // Cmd/Ctrl + K: Focus chat input
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('chatInput')?.focus();
            }

            // Cmd/Ctrl + D: Toggle dark mode
            if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
                e.preventDefault();
                DarkModeService.toggle();
            }
        });
    },

    handleEscape() {
        // Blur active element
        if (document.activeElement) {
            document.activeElement.blur();
        }

        // Close expanded algorithm items
        document.querySelectorAll('.algorithm-item.expanded').forEach(item => {
            item.classList.remove('expanded');
        });
    },
};

/**
 * PWA Service Worker
 */
const PWAService = {
    init() {
        if ('serviceWorker' in navigator) {
            this.registerServiceWorker();
        }

        // Listen for online/offline events
        window.addEventListener('online', () => {
            app.setState({ offline: false });
            ToastService.success('Back online');
        });

        window.addEventListener('offline', () => {
            app.setState({ offline: true });
            ToastService.error('You are offline');
        });

        // Show offline indicator
        this.updateOfflineIndicator();
        app.subscribe('offline', () => {
            this.updateOfflineIndicator();
        });
    },

    async registerServiceWorker() {
        try {
            const registration = await navigator.serviceWorker.register('/sw.js');
            if (!IS_PRODUCTION) {
                console.log('Service Worker registered:', registration);
            }
        } catch (error) {
            if (!IS_PRODUCTION) {
                console.error('Service Worker registration failed:', error);
            }
        }
    },

    updateOfflineIndicator() {
        let indicator = document.getElementById('offlineIndicator');

        if (app.state.offline) {
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'offlineIndicator';
                indicator.className = 'offline-indicator';
                indicator.innerHTML = '<span>Offline</span>';
                document.body.appendChild(indicator);
            }
            AnimationService.slideIn(indicator);
        } else {
            if (indicator) {
                AnimationService.fadeOut(indicator).then(() => {
                    indicator.remove();
                });
            }
        }
    },
};

/**
 * Settings Controller
 */
const SettingsController = {
    init() {
        // User level selection
        document.querySelectorAll('input[name="userLevel"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                app.setState({ userLevel: e.target.value });
                ToastService.info(`Level changed to: ${e.target.value}`);
            });
        });

        // Teaching mode toggle
        document.getElementById('teachingMode')?.addEventListener('change', (e) => {
            app.setState({ teachingMode: e.target.checked });
        });
    },
};

// ============================================
// Utility Functions
// ============================================

/**
 * Debounce function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function}
 */
function debounce(func, wait = CONFIG.DEBOUNCE_DELAY) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 * @param {Function} func - Function to throttle
 * @param {number} limit - Limit in ms
 * @returns {Function}
 */
function throttle(func, limit = CONFIG.DEBOUNCE_DELAY) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ============================================
// Initialization
// ============================================

/**
 * Initialize application
 */
function initializeApp() {
    // Initialize all controllers and services
    ToastService.init();
    DarkModeService.init();
    KeyboardService.init();
    PWAService.init();
    SettingsController.init();
    UploadController.init();
    AnalysisController.init();
    ChatController.init();

    // Show welcome message
    if (!IS_PRODUCTION) {
        console.log('%cECG Guru v2.0', 'color: #3498db; font-size: 24px; font-weight: bold;');
        console.log('%cProduction-grade ECG analysis platform', 'color: #95a5a6; font-size: 14px;');
    }
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

// ============================================
// Export for testing (if needed)
// ============================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        app,
        API,
        UploadController,
        AnalysisController,
        ChatController,
        AnimationService,
        ToastService,
        DarkModeService,
    };
}
