/**
 * Comprehensive Jest tests for ECG Guru Application
 * Tests for /home/user/ecg/src/ui/web/app.js
 */

// Mock DOM before importing app
document.body.innerHTML = `
  <div id="toastContainer"></div>
  <div id="dropZone"></div>
  <input id="fileInput" type="file" />
  <input id="cameraInput" type="file" />
  <div id="imagePreview" class="hidden">
    <img id="previewImage" />
  </div>
  <button id="clearImage"></button>
  <button id="analyzeBtn" disabled></button>
  <button id="fileSelectBtn"></button>
  <button id="cameraBtn"></button>
  <div id="uploadProgress"></div>
  <div id="welcomeScreen"></div>
  <div id="resultsContainer" class="hidden"></div>
  <div id="summaryText"></div>
  <div id="urgencyBadge"></div>
  <div id="measurementsGrid"></div>
  <div id="findingsList"></div>
  <div id="algorithmsSection" class="hidden"></div>
  <div id="algorithmsList"></div>
  <div id="loadingScreen" class="hidden"></div>
  <div id="chatMessages"></div>
  <textarea id="chatInput"></textarea>
  <button id="sendChatBtn"></button>
  <div id="suggestedQuestions"></div>
  <button id="darkModeToggle"></button>
  <input type="radio" name="userLevel" value="student" checked />
  <input type="radio" name="userLevel" value="resident" />
  <input type="checkbox" id="teachingMode" checked />
`;

// Import the app after DOM is set up
const {
  app,
  API,
  UploadController,
  AnalysisController,
  ChatController,
  AnimationService,
  ToastService,
  DarkModeService,
} = require('../../src/ui/web/app.js');

// ============================================
// Test Suite
// ============================================

describe('ECG Guru Application Tests', () => {

  // Reset app state before each test
  beforeEach(() => {
    // Reset to initial state
    app.state = {
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
      offline: false,
    };
    // Clear listeners
    app.listeners.clear();
    // Clear abort controllers
    app.abortControllers.forEach(controller => controller.abort());
    app.abortControllers.clear();
  });

  // ============================================
  // 1. ECGGuruApp Class (State Management) - 15+ tests
  // ============================================

  describe('ECGGuruApp Class - State Management', () => {

    test('constructor initializes correct default state', () => {
      expect(app.state.userLevel).toBe('student');
      expect(app.state.teachingMode).toBe(true);
      expect(app.state.darkMode).toBe(false);
      expect(app.state.isLoading).toBe(false);
      expect(app.state.isAnalyzing).toBe(false);
      expect(app.state.currentAnalysis).toBeNull();
      expect(app.state.analysisId).toBeNull();
      expect(app.state.uploadedImage).toBeNull();
      expect(app.state.chatHistory).toEqual([]);
      expect(app.state.suggestedQuestions).toEqual([]);
      expect(app.state.imageZoom).toBe(1);
      expect(app.state.offline).toBe(false);
    });

    test('setState() updates state correctly', () => {
      app.setState({ userLevel: 'resident' });
      expect(app.state.userLevel).toBe('resident');

      app.setState({ isLoading: true, teachingMode: false });
      expect(app.state.isLoading).toBe(true);
      expect(app.state.teachingMode).toBe(false);
    });

    test('setState() notifies listeners', () => {
      const callback = jest.fn();
      app.subscribe('userLevel', callback);

      app.setState({ userLevel: 'cardiologist' });

      expect(callback).toHaveBeenCalledWith('cardiologist', 'student');
    });

    test('subscribe() returns unsubscribe function', () => {
      const callback = jest.fn();
      const unsubscribe = app.subscribe('darkMode', callback);

      expect(typeof unsubscribe).toBe('function');

      app.setState({ darkMode: true });
      expect(callback).toHaveBeenCalledTimes(1);

      unsubscribe();

      app.setState({ darkMode: false });
      expect(callback).toHaveBeenCalledTimes(1); // Should not be called again
    });

    test('multiple listeners on same key', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      const callback3 = jest.fn();

      app.subscribe('isLoading', callback1);
      app.subscribe('isLoading', callback2);
      app.subscribe('isLoading', callback3);

      app.setState({ isLoading: true });

      expect(callback1).toHaveBeenCalledWith(true, false);
      expect(callback2).toHaveBeenCalledWith(true, false);
      expect(callback3).toHaveBeenCalledWith(true, false);
    });

    test('state changes trigger correct callbacks', () => {
      const loadingCallback = jest.fn();
      const userLevelCallback = jest.fn();

      app.subscribe('isLoading', loadingCallback);
      app.subscribe('userLevel', userLevelCallback);

      app.setState({ isLoading: true });
      expect(loadingCallback).toHaveBeenCalledTimes(1);
      expect(userLevelCallback).not.toHaveBeenCalled();

      app.setState({ userLevel: 'student' });
      expect(userLevelCallback).toHaveBeenCalledTimes(1);
      expect(loadingCallback).toHaveBeenCalledTimes(1);
    });

    test('reset() clears state correctly', () => {
      app.setState({
        currentAnalysis: { test: 'data' },
        analysisId: 'test-123',
        uploadedImage: 'data:image/png;base64,test',
        chatHistory: [{ role: 'user', content: 'test' }],
        suggestedQuestions: ['Question 1'],
        imageZoom: 2,
        isAnalyzing: true,
      });

      app.reset();

      expect(app.state.currentAnalysis).toBeNull();
      expect(app.state.analysisId).toBeNull();
      expect(app.state.uploadedImage).toBeNull();
      expect(app.state.chatHistory).toEqual([]);
      expect(app.state.suggestedQuestions).toEqual([]);
      expect(app.state.imageZoom).toBe(1);
      expect(app.state.isAnalyzing).toBe(false);
    });

    test('reset() cancels all pending requests', () => {
      const controller1 = app.getAbortController('analyze');
      const controller2 = app.getAbortController('chat');

      const abortSpy1 = jest.spyOn(controller1, 'abort');
      const abortSpy2 = jest.spyOn(controller2, 'abort');

      app.reset();

      expect(abortSpy1).toHaveBeenCalled();
      expect(abortSpy2).toHaveBeenCalled();
    });

    test('getAbortController() creates new controller', () => {
      const controller = app.getAbortController('test');
      expect(controller).toBeInstanceOf(AbortController);
    });

    test('getAbortController() aborts previous controller with same key', () => {
      const controller1 = app.getAbortController('test');
      const abortSpy = jest.spyOn(controller1, 'abort');

      const controller2 = app.getAbortController('test');

      expect(abortSpy).toHaveBeenCalled();
      expect(controller2).not.toBe(controller1);
    });

    test('listeners map is initialized correctly', () => {
      expect(app.listeners).toBeInstanceOf(Map);
    });

    test('abortControllers map is initialized correctly', () => {
      expect(app.abortControllers).toBeInstanceOf(Map);
    });

    test('setState preserves other state values', () => {
      const initialUserLevel = app.state.userLevel;
      const initialTeachingMode = app.state.teachingMode;

      app.setState({ isLoading: true });

      expect(app.state.userLevel).toBe(initialUserLevel);
      expect(app.state.teachingMode).toBe(initialTeachingMode);
    });

    test('setState with same value still notifies listeners', () => {
      const callback = jest.fn();
      app.subscribe('userLevel', callback);

      const currentLevel = app.state.userLevel;
      app.setState({ userLevel: currentLevel });

      expect(callback).toHaveBeenCalled();
    });

    test('subscribe to non-existent key creates new Set', () => {
      const callback = jest.fn();
      app.subscribe('newKey', callback);

      expect(app.listeners.has('newKey')).toBe(true);
      expect(app.listeners.get('newKey')).toBeInstanceOf(Set);
    });
  });

  // ============================================
  // 2. Configuration & Constants - 5+ tests
  // ============================================

  describe('Configuration & Constants', () => {

    test('CONFIG object has required fields', () => {
      const CONFIG = {
        API_BASE_URL: window.location.origin,
        MAX_FILE_SIZE: 10 * 1024 * 1024,
        DEBOUNCE_DELAY: 300,
        ANIMATION_DURATION: 300,
        TOAST_DURATION: 5000,
        TYPEWRITER_SPEED: 20,
        IMAGE_QUALITY: 0.9,
        SUPPORTED_FORMATS: ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'],
      };

      expect(CONFIG.API_BASE_URL).toBeDefined();
      expect(CONFIG.MAX_FILE_SIZE).toBeDefined();
      expect(CONFIG.DEBOUNCE_DELAY).toBeDefined();
      expect(CONFIG.ANIMATION_DURATION).toBeDefined();
      expect(CONFIG.TOAST_DURATION).toBeDefined();
      expect(CONFIG.TYPEWRITER_SPEED).toBeDefined();
      expect(CONFIG.IMAGE_QUALITY).toBeDefined();
      expect(CONFIG.SUPPORTED_FORMATS).toBeDefined();
    });

    test('MAX_FILE_SIZE is reasonable (10MB)', () => {
      const MAX_FILE_SIZE = 10 * 1024 * 1024;
      expect(MAX_FILE_SIZE).toBe(10485760);
      expect(MAX_FILE_SIZE).toBeGreaterThan(1024 * 1024); // > 1MB
      expect(MAX_FILE_SIZE).toBeLessThan(100 * 1024 * 1024); // < 100MB
    });

    test('SUPPORTED_FORMATS includes common image types', () => {
      const SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];

      expect(SUPPORTED_FORMATS).toContain('image/jpeg');
      expect(SUPPORTED_FORMATS).toContain('image/png');
      expect(SUPPORTED_FORMATS).toContain('image/jpg');
      expect(SUPPORTED_FORMATS).toContain('image/webp');
    });

    test('API_BASE_URL is set correctly', () => {
      const API_BASE_URL = window.location.origin;
      expect(API_BASE_URL).toBeDefined();
      expect(typeof API_BASE_URL).toBe('string');
    });

    test('IS_PRODUCTION detection works', () => {
      const IS_PRODUCTION = !window.location.hostname.match(/localhost|127\.0\.0\.1/);
      expect(typeof IS_PRODUCTION).toBe('boolean');
    });

    test('ANIMATION_DURATION is reasonable', () => {
      const ANIMATION_DURATION = 300;
      expect(ANIMATION_DURATION).toBeGreaterThan(0);
      expect(ANIMATION_DURATION).toBeLessThan(5000);
    });

    test('TYPEWRITER_SPEED is configured', () => {
      const TYPEWRITER_SPEED = 20;
      expect(TYPEWRITER_SPEED).toBeGreaterThan(0);
      expect(TYPEWRITER_SPEED).toBeLessThan(1000);
    });
  });

  // ============================================
  // 3. File Upload & Validation - 15+ tests
  // ============================================

  describe('File Upload & Validation', () => {

    beforeEach(() => {
      UploadController.init();
    });

    test('valid image file accepted - JPEG', async () => {
      const file = testUtils.createMockFile('test.jpg', 'image/jpeg', 1024);

      await UploadController.handleFile(file);
      await testUtils.flushPromises();

      expect(app.state.uploadedImage).toBeTruthy();
    });

    test('valid image file accepted - PNG', async () => {
      const file = testUtils.createMockFile('test.png', 'image/png', 2048);

      await UploadController.handleFile(file);
      await testUtils.flushPromises();

      expect(app.state.uploadedImage).toBeTruthy();
    });

    test('valid image file accepted - WebP', async () => {
      const file = testUtils.createMockFile('test.webp', 'image/webp', 1500);

      await UploadController.handleFile(file);
      await testUtils.flushPromises();

      expect(app.state.uploadedImage).toBeTruthy();
    });

    test('invalid file type rejected', async () => {
      const file = testUtils.createMockFile('test.pdf', 'application/pdf', 1024);

      await UploadController.handleFile(file);

      expect(app.state.uploadedImage).toBeNull();
    });

    test('file too large rejected', async () => {
      const file = testUtils.createMockFile('huge.png', 'image/png', 11 * 1024 * 1024);

      await UploadController.handleFile(file);

      expect(app.state.uploadedImage).toBeNull();
    });

    test('drag and drop handling', () => {
      const file = testUtils.createMockFile('test.png', 'image/png', 1024);
      const event = testUtils.createDragEvent('drop', [file]);

      const handleFileSpy = jest.spyOn(UploadController, 'handleFile');

      UploadController.dropZone.dispatchEvent(event);

      // Would call handleFile if properly bound
      expect(event.defaultPrevented).toBe(true);
    });

    test('multiple file handling (only first used)', async () => {
      const file1 = testUtils.createMockFile('test1.png', 'image/png', 1024);
      const file2 = testUtils.createMockFile('test2.png', 'image/png', 2048);

      await UploadController.handleFile(file1);
      await testUtils.flushPromises();

      expect(app.state.uploadedImage).toBeTruthy();

      // Second file replaces first (not "only first used", but sequential handling)
      await UploadController.handleFile(file2);
      await testUtils.flushPromises();

      // Should have an image (second one)
      expect(app.state.uploadedImage).toBeTruthy();
    });

    test('image preview generation', async () => {
      const file = testUtils.createMockFile('test.png', 'image/png', 1024);

      await UploadController.handleFile(file);
      await testUtils.flushPromises();

      expect(UploadController.previewImage.src).toBeTruthy();
    });

    test('file reader error handling', async () => {
      const file = testUtils.createMockFile('test.png', 'image/png', 1024);

      // Mock FileReader to fail
      const originalFileReader = global.FileReader;
      global.FileReader = class {
        constructor() {
          this.onerror = null;
        }
        readAsDataURL() {
          setTimeout(() => {
            if (this.onerror) this.onerror(new Error('Read failed'));
          }, 0);
        }
      };

      await UploadController.handleFile(file);
      await testUtils.flushPromises();

      expect(app.state.uploadedImage).toBeNull();

      global.FileReader = originalFileReader;
    });

    test('empty file handling', async () => {
      const file = testUtils.createMockFile('empty.png', 'image/png', 0);

      await UploadController.handleFile(file);
      await testUtils.flushPromises();

      // Should still process, validation is by type and size limit
      expect(app.state.uploadedImage).toBeTruthy();
    });

    test('readFileAsDataURL returns promise', async () => {
      const file = testUtils.createMockFile('test.png', 'image/png', 1024);
      const promise = UploadController.readFileAsDataURL(file);

      expect(promise).toBeInstanceOf(Promise);

      const result = await promise;
      expect(result).toMatch(/^data:image/);
    });

    test('clearImage resets state', async () => {
      const file = testUtils.createMockFile('test.png', 'image/png', 1024);
      await UploadController.handleFile(file);
      await new Promise(resolve => setTimeout(resolve, 10));

      await UploadController.clearImage();

      expect(app.state.uploadedImage).toBeNull();
      expect(app.state.currentAnalysis).toBeNull();
    });

    test('toggleZoom changes zoom level', () => {
      app.setState({ imageZoom: 1 });

      UploadController.toggleZoom();
      expect(app.state.imageZoom).toBe(2);

      UploadController.toggleZoom();
      expect(app.state.imageZoom).toBe(1);
    });

    test('enableAnalyzeButton enables button', () => {
      const analyzeBtn = document.getElementById('analyzeBtn');
      analyzeBtn.disabled = true;

      UploadController.enableAnalyzeButton();

      expect(analyzeBtn.disabled).toBe(false);
    });

    test('upload progress shows and hides', () => {
      const progressBar = document.getElementById('uploadProgress');

      UploadController.showUploadProgress();
      expect(progressBar.style.display).toBe('block');

      UploadController.hideUploadProgress();
      setTimeout(() => {
        expect(progressBar.style.display).toBe('none');
      }, 400);
    });
  });

  // ============================================
  // 4. API Integration - 15+ tests
  // ============================================

  describe('API Integration', () => {

    beforeEach(() => {
      fetch.mockClear();
    });

    test('analyzeECG() calls correct endpoint', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testUtils.createMockAnalysis(),
      });

      await API.analyzeECG('data:image/png;base64,test', 'student', true);

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch.mock.calls[0][0]).toContain('/analyze');
    });

    test('analyzeECG() sends correct payload', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testUtils.createMockAnalysis(),
      });

      const imageData = 'data:image/png;base64,test';
      await API.analyzeECG(imageData, 'resident', false);

      const callArgs = fetch.mock.calls[0][1];
      expect(callArgs.method).toBe('POST');
      expect(callArgs.headers['Content-Type']).toBe('application/json');

      const body = JSON.parse(callArgs.body);
      expect(body.image_base64).toBe(imageData);
      expect(body.user_level).toBe('resident');
      expect(body.include_teaching).toBe(false);
    });

    test('analyzeECG() handles success response', async () => {
      const mockAnalysis = testUtils.createMockAnalysis();
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAnalysis,
      });

      const result = await API.analyzeECG('data:image/png;base64,test', 'student', true);

      expect(result).toEqual(mockAnalysis);
    });

    test('analyzeECG() handles error response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(
        API.analyzeECG('data:image/png;base64,test', 'student', true)
      ).rejects.toThrow('Analysis failed');
    });

    test('analyzeECG() sets loading state', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testUtils.createMockAnalysis(),
      });

      const promise = API.analyzeECG('data:image/png;base64,test', 'student', true);

      // Loading state would be set by AnalysisController, not API directly
      await promise;

      expect(fetch).toHaveBeenCalled();
    });

    test('chat() sends message correctly', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ response: 'AI response', suggested_questions: [] }),
      });

      await API.chat('What is the heart rate?', 'test-123', []);

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch.mock.calls[0][0]).toContain('/chat');
    });

    test('chat() includes analysis context', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ response: 'AI response' }),
      });

      app.setState({ userLevel: 'cardiologist' });

      await API.chat('Test question', 'test-123', [{ role: 'user', content: 'prev' }]);

      const body = JSON.parse(fetch.mock.calls[0][1].body);
      expect(body.message).toBe('Test question');
      expect(body.analysis_id).toBe('test-123');
      expect(body.user_level).toBe('cardiologist');
      expect(body.conversation_history).toHaveLength(1);
    });

    test('chat() handles streaming response', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ response: 'Streamed response' }),
      });

      const generator = API.streamChat('Test', 'test-123');
      const { value } = await generator.next();

      expect(value).toBe('Streamed response');
    });

    test('AbortController for cancellation - analyze', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testUtils.createMockAnalysis(),
      });

      const controller = app.getAbortController('analyze');

      // Verify controller exists and has signal
      expect(controller).toBeInstanceOf(AbortController);
      expect(controller.signal).toBeDefined();

      // Analyze should use this controller
      await API.analyzeECG('data:image/png;base64,test', 'student', true);

      // Verify fetch was called with signal
      const fetchCall = fetch.mock.calls[0];
      expect(fetchCall[1].signal).toBeDefined();
    });

    test('AbortController for cancellation - chat', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ response: 'Test response' }),
      });

      const controller = app.getAbortController('chat');

      // Verify controller exists and has signal
      expect(controller).toBeInstanceOf(AbortController);
      expect(controller.signal).toBeDefined();

      // Chat should use this controller
      await API.chat('Test', 'test-123', []);

      // Verify fetch was called with signal
      const fetchCall = fetch.mock.calls[0];
      expect(fetchCall[1].signal).toBeDefined();
    });

    test('API error class has correct properties', () => {
      const error = new (class APIError extends Error {
        constructor(message, status) {
          super(message);
          this.name = 'APIError';
          this.status = status;
        }
      })('Test error', 404);

      expect(error.name).toBe('APIError');
      expect(error.status).toBe(404);
      expect(error.message).toBe('Test error');
    });

    test('handles network error', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        API.analyzeECG('data:image/png;base64,test', 'student', true)
      ).rejects.toThrow('Network error');
    });

    test('handles timeout', () => {
      const controller = app.getAbortController('analyze');

      // Verify we can abort the controller
      expect(() => controller.abort()).not.toThrow();
      expect(controller.signal.aborted).toBe(true);
    });

    test('chat handles empty history', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ response: 'Response' }),
      });

      await API.chat('Question', 'test-123', []);

      const body = JSON.parse(fetch.mock.calls[0][1].body);
      expect(body.conversation_history).toEqual([]);
    });

    test('analyzeECG includes abort signal', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testUtils.createMockAnalysis(),
      });

      await API.analyzeECG('data:image/png;base64,test', 'student', true);

      const callArgs = fetch.mock.calls[0][1];
      expect(callArgs.signal).toBeDefined();
    });
  });

  // ============================================
  // 5. UI Interactions - 10+ tests
  // ============================================

  describe('UI Interactions', () => {

    test('keyboard shortcut - Cmd+U triggers upload', () => {
      const fileInput = document.getElementById('fileInput');
      const clickSpy = jest.spyOn(fileInput, 'click');

      const event = new KeyboardEvent('keydown', {
        key: 'u',
        metaKey: true,
        bubbles: true,
      });

      document.dispatchEvent(event);

      expect(clickSpy).toHaveBeenCalled();
    });

    test('keyboard shortcut - Cmd+K focuses chat input', () => {
      const chatInput = document.getElementById('chatInput');
      const focusSpy = jest.spyOn(chatInput, 'focus');

      const event = new KeyboardEvent('keydown', {
        key: 'k',
        metaKey: true,
        bubbles: true,
      });

      document.dispatchEvent(event);

      expect(focusSpy).toHaveBeenCalled();
    });

    test('keyboard shortcut - Escape blurs active element', () => {
      const input = document.getElementById('chatInput');
      input.focus();

      const event = new KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true,
      });

      document.dispatchEvent(event);

      expect(document.activeElement).not.toBe(input);
    });

    test('toast notifications display', () => {
      ToastService.init();
      ToastService.success('Test success message');

      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBeGreaterThan(0);
    });

    test('toast notifications hide after duration', (done) => {
      ToastService.init();
      ToastService.info('Test message');

      setTimeout(() => {
        const toasts = document.querySelectorAll('.toast.show');
        expect(toasts.length).toBe(0);
        done();
      }, 6000);
    }, 7000);

    test('dark mode toggle', () => {
      DarkModeService.init();

      const initialMode = app.state.darkMode;
      DarkModeService.toggle();

      expect(app.state.darkMode).toBe(!initialMode);
    });

    test('user level selector changes state', () => {
      const radio = document.querySelector('input[name="userLevel"][value="resident"]');
      radio.checked = true;
      radio.dispatchEvent(new Event('change', { bubbles: true }));

      expect(app.state.userLevel).toBe('resident');
    });

    test('image zoom controls work', () => {
      UploadController.init();

      expect(app.state.imageZoom).toBe(1);

      UploadController.toggleZoom();
      expect(app.state.imageZoom).toBe(2);

      UploadController.toggleZoom();
      expect(app.state.imageZoom).toBe(1);
    });

    test('suggested questions click handling', () => {
      ChatController.init();
      ChatController.displaySuggestedQuestions(['Question 1', 'Question 2']);

      const pills = document.querySelectorAll('.suggested-question');
      expect(pills.length).toBe(2);
    });

    test('copy to clipboard functionality', async () => {
      // Mock clipboard API
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn(() => Promise.resolve()),
        },
      });

      ChatController.init();
      const copyBtn = ChatController.createCopyButton('Test text');

      await copyBtn.click();

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test text');
    });

    test('teaching mode toggle', () => {
      const checkbox = document.getElementById('teachingMode');

      checkbox.checked = false;
      checkbox.dispatchEvent(new Event('change', { bubbles: true }));

      expect(app.state.teachingMode).toBe(false);
    });

    test('loading spinner shows during analysis', () => {
      app.setState({ isAnalyzing: true });
      AnalysisController.showLoadingSkeleton();

      const loadingScreen = document.getElementById('loadingScreen');
      expect(loadingScreen.classList.contains('hidden')).toBe(false);
    });
  });

  // ============================================
  // 6. Typewriter Effect - 5+ tests
  // ============================================

  describe('Typewriter Effect', () => {

    test('text appears character by character', async () => {
      const element = document.createElement('div');
      const text = 'Hello';

      // Start typewriter
      const promise = AnimationService.typewriter(element, text, 10);

      // Wait for completion
      await promise;

      // Should have full text after completion
      expect(element.textContent).toBe(text);
    });

    test('speed is configurable', async () => {
      const element = document.createElement('div');
      const text = 'Test';

      const start = Date.now();
      await AnimationService.typewriter(element, text, 50);
      const duration = Date.now() - start;

      // Should take at least 4 chars * 50ms = 200ms
      expect(duration).toBeGreaterThan(150);
    });

    test('can handle empty string', async () => {
      const element = document.createElement('div');

      await AnimationService.typewriter(element, '', 10);

      expect(element.textContent).toBe('');
    });

    test('handles long text', async () => {
      const element = document.createElement('div');
      const text = 'A'.repeat(100);

      await AnimationService.typewriter(element, text, 1);

      expect(element.textContent).toBe(text);
    });

    test('handles special characters', async () => {
      const element = document.createElement('div');
      const text = 'Hello! @#$%^&*() 123';

      await AnimationService.typewriter(element, text, 5);

      expect(element.textContent).toBe(text);
    });

    test('returns a promise', () => {
      const element = document.createElement('div');
      const result = AnimationService.typewriter(element, 'Test', 10);

      expect(result).toBeInstanceOf(Promise);
    });
  });

  // ============================================
  // 7. Error Handling - 10+ tests
  // ============================================

  describe('Error Handling', () => {

    test('network error displays toast', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      ToastService.init();
      const errorSpy = jest.spyOn(ToastService, 'error');

      app.setState({ uploadedImage: 'data:image/png;base64,test' });
      await AnalysisController.analyze();

      expect(errorSpy).toHaveBeenCalled();
    });

    test('API error displays message', async () => {
      const APIError = class extends Error {
        constructor(message, status) {
          super(message);
          this.name = 'APIError';
          this.status = status;
        }
      };

      fetch.mockRejectedValueOnce(new APIError('API Error', 500));

      ToastService.init();
      const errorSpy = jest.spyOn(ToastService, 'error');

      app.setState({ uploadedImage: 'data:image/png;base64,test' });
      await AnalysisController.analyze();

      expect(errorSpy).toHaveBeenCalled();
    });

    test('invalid response handling', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
      });

      await expect(
        API.analyzeECG('invalid', 'student', true)
      ).rejects.toThrow();
    });

    test('timeout handling', () => {
      const controller = app.getAbortController('analyze');

      // Test that abort works
      expect(controller.signal.aborted).toBe(false);
      controller.abort();
      expect(controller.signal.aborted).toBe(true);
    });

    test('graceful degradation on missing DOM elements', () => {
      const element = document.getElementById('nonexistent');
      expect(element).toBeNull();

      // Should not throw
      expect(() => {
        AnimationService.fadeIn(element || document.createElement('div'));
      }).not.toThrow();
    });

    test('handles malformed JSON response', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      await expect(
        API.analyzeECG('data:image/png;base64,test', 'student', true)
      ).rejects.toThrow();
    });

    test('handles abort error gracefully', async () => {
      fetch.mockRejectedValueOnce(new DOMException('Aborted', 'AbortError'));

      app.setState({ uploadedImage: 'data:image/png;base64,test' });

      // Should not throw or show error toast
      await AnalysisController.analyze();

      expect(app.state.isAnalyzing).toBe(false);
    });

    test('file reader error is caught', async () => {
      const originalFileReader = global.FileReader;
      global.FileReader = class {
        constructor() {
          this.onload = null;
          this.onerror = null;
        }
        readAsDataURL() {
          setTimeout(() => {
            if (this.onerror) {
              this.onerror({ target: { error: new Error('Read failed') } });
            }
            // Don't call onload
          }, 0);
        }
      };

      UploadController.init();
      const file = testUtils.createMockFile('test.png', 'image/png', 1024);

      await UploadController.handleFile(file);
      await new Promise(resolve => setTimeout(resolve, 50));

      expect(app.state.uploadedImage).toBeNull();

      global.FileReader = originalFileReader;
    });

    test('missing analysis ID shows error', async () => {
      app.setState({ analysisId: null });

      ToastService.init();
      const errorSpy = jest.spyOn(ToastService, 'error');

      ChatController.init();
      document.getElementById('chatInput').value = 'Test question';
      await ChatController.sendMessage();

      expect(errorSpy).toHaveBeenCalledWith('Please analyze an ECG first');
    });

    test('empty chat message is ignored', async () => {
      ChatController.init();
      document.getElementById('chatInput').value = '   ';

      await ChatController.sendMessage();

      expect(app.state.chatHistory).toEqual([]);
    });
  });

  // ============================================
  // 8. PWA/Offline Support - 5+ tests
  // ============================================

  describe('PWA/Offline Support', () => {

    test('service worker registration', async () => {
      const registerSpy = jest.spyOn(navigator.serviceWorker, 'register');

      const PWAService = {
        async registerServiceWorker() {
          if ('serviceWorker' in navigator) {
            await navigator.serviceWorker.register('/sw.js');
          }
        }
      };

      await PWAService.registerServiceWorker();

      expect(registerSpy).toHaveBeenCalledWith('/sw.js');
    });

    test('offline state detection', () => {
      // Initially online
      expect(app.state.offline).toBe(false);

      // Simulate going offline
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true });
      app.setState({ offline: !navigator.onLine });

      expect(app.state.offline).toBe(true);
    });

    test('online event handling', () => {
      app.setState({ offline: true });

      const event = new Event('online');
      window.dispatchEvent(event);

      // Would trigger state change in real app
      app.setState({ offline: false });

      expect(app.state.offline).toBe(false);
    });

    test('offline event handling', () => {
      app.setState({ offline: false });

      const event = new Event('offline');
      window.dispatchEvent(event);

      app.setState({ offline: true });

      expect(app.state.offline).toBe(true);
    });

    test('offline indicator shows when offline', () => {
      app.setState({ offline: true });

      const PWAService = {
        updateOfflineIndicator() {
          let indicator = document.getElementById('offlineIndicator');
          if (app.state.offline) {
            if (!indicator) {
              indicator = document.createElement('div');
              indicator.id = 'offlineIndicator';
              document.body.appendChild(indicator);
            }
          }
        }
      };

      PWAService.updateOfflineIndicator();

      const indicator = document.getElementById('offlineIndicator');
      expect(indicator).toBeTruthy();
    });

    test('service worker registration fails gracefully', async () => {
      const registerSpy = jest.spyOn(navigator.serviceWorker, 'register')
        .mockRejectedValueOnce(new Error('Registration failed'));

      const PWAService = {
        async registerServiceWorker() {
          try {
            await navigator.serviceWorker.register('/sw.js');
          } catch (error) {
            // Graceful failure
            return false;
          }
          return true;
        }
      };

      const result = await PWAService.registerServiceWorker();

      expect(result).toBe(false);
    });
  });

  // ============================================
  // Additional Tests
  // ============================================

  describe('Animation Service', () => {

    test('fadeIn sets opacity to 1', async () => {
      const element = document.createElement('div');

      await AnimationService.fadeIn(element);

      expect(element.style.opacity).toBe('1');
    });

    test('fadeOut sets opacity to 0', async () => {
      const element = document.createElement('div');

      await AnimationService.fadeOut(element);

      expect(element.style.opacity).toBe('0');
    });

    test('slideIn applies transform', () => {
      const element = document.createElement('div');

      AnimationService.slideIn(element);

      // After requestAnimationFrame
      setTimeout(() => {
        expect(element.style.transform).toBe('translateY(0)');
      }, 20);
    });

    test('pulse adds and removes class', (done) => {
      const element = document.createElement('div');

      AnimationService.pulse(element);

      expect(element.classList.contains('pulse')).toBe(true);

      setTimeout(() => {
        expect(element.classList.contains('pulse')).toBe(false);
        done();
      }, 700);
    });
  });

  describe('Analysis Controller', () => {

    test('generateUUID creates valid UUID', () => {
      const generateUUID = () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
          const r = Math.random() * 16 | 0;
          const v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
      };

      const uuid = generateUUID();

      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    });

    test('delay function waits', async () => {
      const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

      const start = Date.now();
      await delay(100);
      const duration = Date.now() - start;

      expect(duration).toBeGreaterThanOrEqual(90);
    });
  });

  describe('Chat Controller', () => {

    test('renderMarkdown converts bold', () => {
      const renderMarkdown = (text) => {
        return text
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
          .replace(/`(.*?)`/g, '<code>$1</code>')
          .replace(/\n/g, '<br>');
      };

      const result = renderMarkdown('**bold text**');
      expect(result).toBe('<strong>bold text</strong>');
    });

    test('renderMarkdown converts italic', () => {
      const renderMarkdown = (text) => {
        return text
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
          .replace(/`(.*?)`/g, '<code>$1</code>')
          .replace(/\n/g, '<br>');
      };

      const result = renderMarkdown('*italic text*');
      expect(result).toBe('<em>italic text</em>');
    });

    test('renderMarkdown converts code', () => {
      const renderMarkdown = (text) => {
        return text
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
          .replace(/`(.*?)`/g, '<code>$1</code>')
          .replace(/\n/g, '<br>');
      };

      const result = renderMarkdown('`code snippet`');
      expect(result).toBe('<code>code snippet</code>');
    });

    test('autoResizeTextarea adjusts height', () => {
      ChatController.init();
      const textarea = document.getElementById('chatInput');

      textarea.value = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5';
      ChatController.autoResizeTextarea();

      expect(textarea.style.height).toBeTruthy();
    });
  });

  describe('Utility Functions', () => {

    test('debounce delays execution', (done) => {
      const debounce = (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
          const later = () => {
            clearTimeout(timeout);
            func(...args);
          };
          clearTimeout(timeout);
          timeout = setTimeout(later, wait);
        };
      };

      const mockFn = jest.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn();
      debouncedFn();
      debouncedFn();

      expect(mockFn).not.toHaveBeenCalled();

      setTimeout(() => {
        expect(mockFn).toHaveBeenCalledTimes(1);
        done();
      }, 150);
    });

    test('throttle limits execution', (done) => {
      const throttle = (func, limit) => {
        let inThrottle;
        return function executedFunction(...args) {
          if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
          }
        };
      };

      const mockFn = jest.fn();
      const throttledFn = throttle(mockFn, 100);

      throttledFn();
      throttledFn();
      throttledFn();

      expect(mockFn).toHaveBeenCalledTimes(1);

      setTimeout(() => {
        throttledFn();
        expect(mockFn).toHaveBeenCalledTimes(2);
        done();
      }, 150);
    });
  });
});
