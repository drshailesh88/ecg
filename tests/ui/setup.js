/**
 * Jest Test Setup for ECG Guru Frontend
 *
 * This file sets up the testing environment with:
 * - DOM mocks (fetch, localStorage, navigator)
 * - IndexedDB mock (fake-indexeddb)
 * - Custom matchers
 * - Global test utilities
 */

// Import fake IndexedDB for history.js tests
require('fake-indexeddb/auto');

// Polyfill for structuredClone (required by fake-indexeddb)
if (typeof global.structuredClone === 'undefined') {
    global.structuredClone = (obj) => {
        return JSON.parse(JSON.stringify(obj));
    };
}

// Mock fetch API
global.fetch = jest.fn(() =>
    Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
        text: () => Promise.resolve(''),
        blob: () => Promise.resolve(new Blob()),
    })
);

// Mock localStorage
const localStorageMock = {
    store: {},
    getItem: jest.fn((key) => localStorageMock.store[key] || null),
    setItem: jest.fn((key, value) => {
        localStorageMock.store[key] = String(value);
    }),
    removeItem: jest.fn((key) => {
        delete localStorageMock.store[key];
    }),
    clear: jest.fn(() => {
        localStorageMock.store = {};
    }),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock sessionStorage
const sessionStorageMock = {
    store: {},
    getItem: jest.fn((key) => sessionStorageMock.store[key] || null),
    setItem: jest.fn((key, value) => {
        sessionStorageMock.store[key] = String(value);
    }),
    removeItem: jest.fn((key) => {
        delete sessionStorageMock.store[key];
    }),
    clear: jest.fn(() => {
        sessionStorageMock.store = {};
    }),
};
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
    value: true,
    writable: true,
});

// Mock navigator.serviceWorker
Object.defineProperty(navigator, 'serviceWorker', {
    value: {
        register: jest.fn(() => Promise.resolve({ scope: '/' })),
        ready: Promise.resolve({
            active: { postMessage: jest.fn() },
        }),
    },
});

// Mock window.matchMedia (for dark mode)
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
    constructor(callback) {
        this.callback = callback;
    }
    observe() {}
    unobserve() {}
    disconnect() {}
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
    constructor(callback) {
        this.callback = callback;
    }
    observe() {}
    unobserve() {}
    disconnect() {}
};

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = jest.fn();

// Mock FileReader
global.FileReader = class FileReader {
    constructor() {
        this.result = null;
        this.onload = null;
        this.onerror = null;
    }
    readAsDataURL(blob) {
        setTimeout(() => {
            this.result = 'data:image/png;base64,mockbase64data';
            if (this.onload) this.onload({ target: this });
        }, 0);
    }
    readAsText(blob) {
        setTimeout(() => {
            this.result = 'mock text content';
            if (this.onload) this.onload({ target: this });
        }, 0);
    }
};

// Mock Image
global.Image = class Image {
    constructor() {
        this.onload = null;
        this.onerror = null;
        this.src = '';
        setTimeout(() => {
            this.width = 800;
            this.height = 600;
            if (this.onload) this.onload();
        }, 0);
    }
};

// Mock canvas
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
    drawImage: jest.fn(),
    getImageData: jest.fn(() => ({ data: new Uint8ClampedArray(4) })),
    putImageData: jest.fn(),
    fillRect: jest.fn(),
    clearRect: jest.fn(),
    beginPath: jest.fn(),
    moveTo: jest.fn(),
    lineTo: jest.fn(),
    stroke: jest.fn(),
    arc: jest.fn(),
    fill: jest.fn(),
    measureText: jest.fn(() => ({ width: 100 })),
    fillText: jest.fn(),
}));
HTMLCanvasElement.prototype.toDataURL = jest.fn(() => 'data:image/png;base64,mock');
HTMLCanvasElement.prototype.toBlob = jest.fn((callback) => {
    callback(new Blob(['mock'], { type: 'image/png' }));
});

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((callback) => setTimeout(callback, 16));
global.cancelAnimationFrame = jest.fn((id) => clearTimeout(id));

// Mock performance.now
if (!global.performance) {
    global.performance = {};
}
global.performance.now = jest.fn(() => Date.now());

// Mock console methods to reduce noise in tests (optional)
// global.console = {
//     ...console,
//     log: jest.fn(),
//     debug: jest.fn(),
//     info: jest.fn(),
//     warn: jest.fn(),
// };

// Reset mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.store = {};
    sessionStorageMock.store = {};
    fetch.mockClear();
});

// Clean up after all tests
afterAll(() => {
    jest.restoreAllMocks();
});

// Custom matchers
expect.extend({
    toBeValidECGAnalysis(received) {
        const hasRequiredFields =
            received &&
            typeof received.analysis_id === 'string' &&
            typeof received.summary === 'string' &&
            Array.isArray(received.findings);

        return {
            pass: hasRequiredFields,
            message: () => hasRequiredFields
                ? `Expected ${JSON.stringify(received)} not to be a valid ECG analysis`
                : `Expected ${JSON.stringify(received)} to be a valid ECG analysis with analysis_id, summary, and findings`,
        };
    },
    toHaveBeenCalledWithAPIEndpoint(received, endpoint) {
        const calls = received.mock.calls;
        const matchingCall = calls.find(call => call[0].includes(endpoint));

        return {
            pass: !!matchingCall,
            message: () => matchingCall
                ? `Expected fetch not to have been called with endpoint containing "${endpoint}"`
                : `Expected fetch to have been called with endpoint containing "${endpoint}". Actual calls: ${JSON.stringify(calls.map(c => c[0]))}`,
        };
    },
});

// Polyfill setImmediate for Node.js test environment
if (typeof setImmediate === 'undefined') {
    global.setImmediate = (callback, ...args) => setTimeout(callback, 0, ...args);
}

// Global test utilities
global.testUtils = {
    // Create a mock ECG analysis response
    createMockAnalysis: (overrides = {}) => ({
        analysis_id: 'test-123',
        timestamp: new Date().toISOString(),
        processing_time_ms: 1500,
        summary: 'Normal sinus rhythm',
        measurements: {
            heart_rate: 75,
            pr_interval_ms: 160,
            qrs_duration_ms: 90,
            qt_interval_ms: 400,
            qtc_ms: 420,
            axis_degrees: 45,
        },
        findings: [
            { category: 'rhythm', finding: 'Normal sinus rhythm', severity: 'normal', confidence: 0.95 },
        ],
        primary_diagnosis: 'Normal ECG',
        confidence: 0.92,
        is_urgent: false,
        recommended_actions: ['Continue routine monitoring'],
        ...overrides,
    }),

    // Create a mock STEMI analysis
    createMockSTEMI: () => ({
        analysis_id: 'stemi-456',
        timestamp: new Date().toISOString(),
        processing_time_ms: 800,
        summary: 'ACUTE STEMI - Inferior territory',
        findings: [
            {
                category: 'ischemia',
                finding: 'ACUTE STEMI',
                severity: 'critical',
                confidence: 0.98,
            },
        ],
        algorithm_results: {
            stemi: {
                is_stemi: true,
                territories: ['Inferior'],
                culprit_vessel: 'RCA',
                culprit_confidence: 0.85,
            },
        },
        primary_diagnosis: 'STEMI - Inferior',
        is_urgent: true,
        urgency_reason: 'Critical finding: ACUTE STEMI',
        recommended_actions: [
            'Activate cath lab immediately',
            'Administer aspirin 325mg',
            'Start heparin protocol',
        ],
    }),

    // Wait for promises to resolve
    flushPromises: () => new Promise(resolve => setImmediate(resolve)),

    // Simulate user typing
    simulateTyping: async (element, text) => {
        for (const char of text) {
            element.value += char;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise(resolve => setTimeout(resolve, 10));
        }
    },

    // Create mock file
    createMockFile: (name = 'test.png', type = 'image/png', size = 1024) => {
        const content = new Array(size).fill('a').join('');
        return new File([content], name, { type });
    },

    // Create mock drag event
    createDragEvent: (type, files = []) => {
        const event = new Event(type, { bubbles: true, cancelable: true });
        event.dataTransfer = {
            files,
            items: files.map(f => ({ kind: 'file', type: f.type, getAsFile: () => f })),
            types: ['Files'],
        };
        return event;
    },
};
