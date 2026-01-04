// ============================================
// ECG Guru - Case History & Analytics Module
// ============================================

// IndexedDB Configuration
const DB_NAME = 'ecg_guru_db';
const DB_VERSION = 1;
const STORE_CASES = 'cases';
const STORE_ANALYTICS = 'analytics';

// ============================================
// Database Management
// ============================================
class ECGDatabase {
    constructor() {
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Cases Store
                if (!db.objectStoreNames.contains(STORE_CASES)) {
                    const casesStore = db.createObjectStore(STORE_CASES, { keyPath: 'id', autoIncrement: true });
                    casesStore.createIndex('timestamp', 'timestamp', { unique: false });
                    casesStore.createIndex('diagnosis', 'diagnosis', { unique: false });
                    casesStore.createIndex('severity', 'severity', { unique: false });
                    casesStore.createIndex('tags', 'tags', { unique: false, multiEntry: true });
                }

                // Analytics Store
                if (!db.objectStoreNames.contains(STORE_ANALYTICS)) {
                    const analyticsStore = db.createObjectStore(STORE_ANALYTICS, { keyPath: 'date' });
                }
            };
        });
    }

    async saveCase(caseData) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_CASES], 'readwrite');
            const store = transaction.objectStore(STORE_CASES);
            const request = store.add(caseData);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateCase(id, caseData) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_CASES], 'readwrite');
            const store = transaction.objectStore(STORE_CASES);
            const request = store.put({ ...caseData, id });

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAllCases() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_CASES], 'readonly');
            const store = transaction.objectStore(STORE_CASES);
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getCase(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_CASES], 'readonly');
            const store = transaction.objectStore(STORE_CASES);
            const request = store.get(id);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async deleteCase(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_CASES], 'readwrite');
            const store = transaction.objectStore(STORE_CASES);
            const request = store.delete(id);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async searchCases(query) {
        const allCases = await this.getAllCases();
        const lowerQuery = query.toLowerCase();

        return allCases.filter(caseItem => {
            return (
                caseItem.diagnosis?.toLowerCase().includes(lowerQuery) ||
                caseItem.notes?.toLowerCase().includes(lowerQuery) ||
                caseItem.tags?.some(tag => tag.toLowerCase().includes(lowerQuery)) ||
                caseItem.summary?.toLowerCase().includes(lowerQuery)
            );
        });
    }

    async updateAnalytics(date, stats) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_ANALYTICS], 'readwrite');
            const store = transaction.objectStore(STORE_ANALYTICS);
            const request = store.put({ date, ...stats });

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAnalyticsByDateRange(startDate, endDate) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([STORE_ANALYTICS], 'readonly');
            const store = transaction.objectStore(STORE_ANALYTICS);
            const request = store.getAll();

            request.onsuccess = () => {
                const results = request.result.filter(item => {
                    const itemDate = new Date(item.date);
                    return itemDate >= startDate && itemDate <= endDate;
                });
                resolve(results);
            };
            request.onerror = () => reject(request.error);
        });
    }
}

// ============================================
// Case Library Management
// ============================================
class CaseLibrary {
    constructor(db) {
        this.db = db;
        this.currentFilter = 'all';
        this.currentSort = 'recent';
        this.searchQuery = '';
    }

    async saveCurrentAnalysis(analysis, imageData, userNotes = '') {
        // Compress image for thumbnail
        const thumbnail = await this.createThumbnail(imageData);

        const caseData = {
            timestamp: Date.now(),
            diagnosis: this.extractPrimaryDiagnosis(analysis),
            summary: analysis.summary,
            severity: analysis.is_urgent ? 'critical' : this.determineSeverity(analysis),
            measurements: analysis.measurements,
            findings: analysis.findings,
            algorithmResults: analysis.algorithm_results,
            imageThumbnail: thumbnail,
            imageData: imageData, // Store full image (base64)
            conversationHistory: analysis.conversationHistory || [],
            tags: this.generateTags(analysis),
            notes: userNotes,
            userLevel: analysis.userLevel || 'student'
        };

        const id = await this.db.saveCase(caseData);
        await this.updateDailyAnalytics();
        return id;
    }

    async createThumbnail(imageData, maxWidth = 300) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const scaleFactor = maxWidth / img.width;
                canvas.width = maxWidth;
                canvas.height = img.height * scaleFactor;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                resolve(canvas.toDataURL('image/jpeg', 0.7));
            };
            img.src = imageData;
        });
    }

    extractPrimaryDiagnosis(analysis) {
        if (!analysis.findings || analysis.findings.length === 0) {
            return 'Normal ECG';
        }

        // Find most severe/critical finding
        const critical = analysis.findings.find(f => f.severity === 'critical');
        if (critical) {
            return critical.finding || critical.category;
        }

        const abnormal = analysis.findings.find(f => f.severity === 'abnormal');
        if (abnormal) {
            return abnormal.finding || abnormal.category;
        }

        return analysis.findings[0].finding || analysis.findings[0].category || 'See Findings';
    }

    determineSeverity(analysis) {
        if (analysis.is_urgent) return 'critical';

        const hasCritical = analysis.findings?.some(f => f.severity === 'critical');
        if (hasCritical) return 'critical';

        const hasAbnormal = analysis.findings?.some(f => f.severity === 'abnormal');
        if (hasAbnormal) return 'abnormal';

        return 'normal';
    }

    generateTags(analysis) {
        const tags = [];

        // Add severity tag
        if (analysis.is_urgent) {
            tags.push('Critical');
        }

        // Extract tags from findings
        if (analysis.findings) {
            analysis.findings.forEach(finding => {
                if (finding.category) {
                    tags.push(finding.category);
                }

                // Extract key medical terms
                const finding_text = finding.finding || '';
                if (finding_text.includes('STEMI')) tags.push('STEMI');
                if (finding_text.includes('VT') || finding_text.includes('Ventricular Tachycardia')) tags.push('VT');
                if (finding_text.includes('WPW') || finding_text.includes('Pre-excitation')) tags.push('WPW');
                if (finding_text.includes('LAD')) tags.push('LAD');
                if (finding_text.includes('RCA')) tags.push('RCA');
                if (finding_text.includes('LCx')) tags.push('LCx');
                if (finding_text.includes('RBBB')) tags.push('RBBB');
                if (finding_text.includes('LBBB')) tags.push('LBBB');
                if (finding_text.includes('Atrial Fibrillation') || finding_text.includes('AFib')) tags.push('AFib');
            });
        }

        // Extract from algorithm results
        if (analysis.algorithm_results) {
            analysis.algorithm_results.forEach(algo => {
                if (algo.name.includes('Brugada')) tags.push('Brugada');
                if (algo.name.includes('SMART-WPW')) tags.push('Pathway');
            });
        }

        // Remove duplicates
        return [...new Set(tags)];
    }

    async getCases(filter = 'all', sort = 'recent') {
        let cases = await this.db.getAllCases();

        // Apply filter
        if (filter === 'critical') {
            cases = cases.filter(c => c.severity === 'critical');
        } else if (filter === 'abnormal') {
            cases = cases.filter(c => c.severity === 'abnormal');
        } else if (filter === 'normal') {
            cases = cases.filter(c => c.severity === 'normal');
        } else if (filter === 'week') {
            const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
            cases = cases.filter(c => c.timestamp >= weekAgo);
        } else if (filter === 'month') {
            const monthAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
            cases = cases.filter(c => c.timestamp >= monthAgo);
        }

        // Apply search
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            cases = cases.filter(c =>
                c.diagnosis?.toLowerCase().includes(query) ||
                c.notes?.toLowerCase().includes(query) ||
                c.tags?.some(tag => tag.toLowerCase().includes(query))
            );
        }

        // Apply sort
        if (sort === 'recent') {
            cases.sort((a, b) => b.timestamp - a.timestamp);
        } else if (sort === 'oldest') {
            cases.sort((a, b) => a.timestamp - b.timestamp);
        } else if (sort === 'severity') {
            const severityOrder = { critical: 0, abnormal: 1, normal: 2 };
            cases.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
        }

        return cases;
    }

    async updateDailyAnalytics() {
        const today = new Date().toISOString().split('T')[0];
        const cases = await this.db.getAllCases();
        const todayCases = cases.filter(c => {
            const caseDate = new Date(c.timestamp).toISOString().split('T')[0];
            return caseDate === today;
        });

        await this.db.updateAnalytics(today, {
            count: todayCases.length,
            critical: todayCases.filter(c => c.severity === 'critical').length,
            abnormal: todayCases.filter(c => c.severity === 'abnormal').length,
            normal: todayCases.filter(c => c.severity === 'normal').length
        });
    }

    async exportCase(caseId, format = 'json') {
        const caseData = await this.db.getCase(caseId);

        if (format === 'json') {
            return this.exportAsJSON(caseData);
        } else if (format === 'pdf') {
            return this.exportAsPDF(caseData);
        }
    }

    exportAsJSON(caseData) {
        const blob = new Blob([JSON.stringify(caseData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ecg_case_${caseData.id}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    exportAsPDF(caseData) {
        // Create a printable HTML version
        const printWindow = window.open('', '_blank');
        const html = this.generatePrintableHTML(caseData);

        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.print();
    }

    generatePrintableHTML(caseData) {
        return `
<!DOCTYPE html>
<html>
<head>
    <title>ECG Case Report - ${caseData.diagnosis}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }
        .meta { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 20px 0; }
        .meta-item { background: #f3f4f6; padding: 10px; border-radius: 4px; }
        .meta-label { font-weight: bold; color: #6b7280; }
        .section { margin: 20px 0; }
        .section-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #1f2937; }
        .finding { background: #f9fafb; padding: 10px; margin: 5px 0; border-left: 3px solid #2563eb; }
        .measurement-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .measurement { background: #eff6ff; padding: 10px; border-radius: 4px; text-align: center; }
        .measurement-value { font-size: 24px; font-weight: bold; color: #2563eb; }
        .measurement-label { font-size: 12px; color: #6b7280; }
        .critical { border-left-color: #dc2626; }
        .abnormal { border-left-color: #f59e0b; }
        img { max-width: 100%; height: auto; margin: 20px 0; }
        @media print { body { margin: 0; padding: 10px; } }
    </style>
</head>
<body>
    <h1>ECG Case Report</h1>

    <div class="meta">
        <div class="meta-item">
            <div class="meta-label">Diagnosis</div>
            <div>${caseData.diagnosis}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Date</div>
            <div>${new Date(caseData.timestamp).toLocaleString()}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Severity</div>
            <div>${caseData.severity.toUpperCase()}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">User Level</div>
            <div>${caseData.userLevel}</div>
        </div>
    </div>

    ${caseData.imageData ? `<img src="${caseData.imageData}" alt="ECG Image" />` : ''}

    <div class="section">
        <div class="section-title">Summary</div>
        <p>${caseData.summary}</p>
    </div>

    <div class="section">
        <div class="section-title">Measurements</div>
        <div class="measurement-grid">
            ${Object.entries(caseData.measurements || {}).map(([key, value]) => `
                <div class="measurement">
                    <div class="measurement-value">${value}</div>
                    <div class="measurement-label">${key.replace(/_/g, ' ')}</div>
                </div>
            `).join('')}
        </div>
    </div>

    <div class="section">
        <div class="section-title">Findings</div>
        ${(caseData.findings || []).map(finding => `
            <div class="finding ${finding.severity}">
                <strong>${finding.category}: ${finding.finding}</strong>
                <p>${finding.explanation}</p>
            </div>
        `).join('')}
    </div>

    ${caseData.notes ? `
        <div class="section">
            <div class="section-title">Notes</div>
            <p>${caseData.notes}</p>
        </div>
    ` : ''}

    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 12px;">
        Generated by ECG Guru - AI-Powered ECG Analysis Platform
    </div>
</body>
</html>
        `;
    }
}

// ============================================
// Analytics Dashboard
// ============================================
class AnalyticsDashboard {
    constructor(db) {
        this.db = db;
    }

    async getStats() {
        const cases = await this.db.getAllCases();
        const now = Date.now();
        const weekAgo = now - (7 * 24 * 60 * 60 * 1000);
        const monthAgo = now - (30 * 24 * 60 * 60 * 1000);

        // Count by diagnosis
        const byDiagnosis = {};
        cases.forEach(c => {
            const diagnosis = c.diagnosis || 'Unknown';
            byDiagnosis[diagnosis] = (byDiagnosis[diagnosis] || 0) + 1;
        });

        // Activity over time (last 30 days)
        const activityByDay = {};
        for (let i = 0; i < 30; i++) {
            const date = new Date(now - (i * 24 * 60 * 60 * 1000));
            const dateKey = date.toISOString().split('T')[0];
            activityByDay[dateKey] = 0;
        }

        cases.forEach(c => {
            const dateKey = new Date(c.timestamp).toISOString().split('T')[0];
            if (activityByDay.hasOwnProperty(dateKey)) {
                activityByDay[dateKey]++;
            }
        });

        // Learning streak (consecutive days with at least 1 analysis)
        let streak = 0;
        const sortedDays = Object.keys(activityByDay).sort().reverse();
        for (const day of sortedDays) {
            if (activityByDay[day] > 0) {
                streak++;
            } else {
                break;
            }
        }

        return {
            totalAnalyzed: cases.length,
            thisWeek: cases.filter(c => c.timestamp >= weekAgo).length,
            thisMonth: cases.filter(c => c.timestamp >= monthAgo).length,
            criticalFound: cases.filter(c => c.severity === 'critical').length,
            abnormalFound: cases.filter(c => c.severity === 'abnormal').length,
            normalFound: cases.filter(c => c.severity === 'normal').length,
            byDiagnosis,
            activityByDay,
            learningStreak: streak,
            averagePerWeek: cases.length > 0 ? Math.round(cases.filter(c => c.timestamp >= monthAgo).length / 4) : 0
        };
    }

    async getRecentActivity(days = 30) {
        const cases = await this.db.getAllCases();
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);

        return cases
            .filter(c => c.timestamp >= cutoff)
            .sort((a, b) => b.timestamp - a.timestamp);
    }

    async getDiagnosisTrends() {
        const cases = await this.db.getAllCases();

        // Group by month and diagnosis
        const trends = {};
        cases.forEach(c => {
            const date = new Date(c.timestamp);
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

            if (!trends[monthKey]) {
                trends[monthKey] = {};
            }

            const diagnosis = c.diagnosis || 'Unknown';
            trends[monthKey][diagnosis] = (trends[monthKey][diagnosis] || 0) + 1;
        });

        return trends;
    }
}

// ============================================
// ECG Comparison
// ============================================
class ECGComparison {
    constructor() {
        this.caseA = null;
        this.caseB = null;
    }

    async loadComparison(caseIdA, caseIdB, db) {
        this.caseA = await db.getCase(caseIdA);
        this.caseB = await db.getCase(caseIdB);
        return { caseA: this.caseA, caseB: this.caseB };
    }

    findDifferences() {
        if (!this.caseA || !this.caseB) {
            return null;
        }

        const differences = {
            measurements: this.compareMeasurements(),
            findings: this.compareFindings(),
            severity: this.caseA.severity !== this.caseB.severity
        };

        return differences;
    }

    compareMeasurements() {
        const diffs = [];
        const measA = this.caseA.measurements || {};
        const measB = this.caseB.measurements || {};

        const allKeys = new Set([...Object.keys(measA), ...Object.keys(measB)]);

        allKeys.forEach(key => {
            const valueA = measA[key];
            const valueB = measB[key];

            if (valueA !== valueB) {
                diffs.push({
                    measurement: key,
                    caseA: valueA,
                    caseB: valueB,
                    difference: typeof valueA === 'number' && typeof valueB === 'number'
                        ? valueB - valueA
                        : 'N/A'
                });
            }
        });

        return diffs;
    }

    compareFindings() {
        const findingsA = this.caseA.findings || [];
        const findingsB = this.caseB.findings || [];

        const uniqueToA = findingsA.filter(fA =>
            !findingsB.some(fB => fB.finding === fA.finding)
        );

        const uniqueToB = findingsB.filter(fB =>
            !findingsA.some(fA => fA.finding === fB.finding)
        );

        return { uniqueToA, uniqueToB };
    }
}

// ============================================
// UI Controller
// ============================================
class HistoryUI {
    constructor() {
        this.db = new ECGDatabase();
        this.caseLibrary = null;
        this.analytics = null;
        this.comparison = new ECGComparison();
        this.currentView = 'library'; // 'library', 'analytics', 'comparison'
    }

    async init() {
        await this.db.init();
        this.caseLibrary = new CaseLibrary(this.db);
        this.analytics = new AnalyticsDashboard(this.db);
    }

    async renderCaseLibrary(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const cases = await this.caseLibrary.getCases();

        container.innerHTML = `
            <div class="history-header">
                <h2>Case Library</h2>
                <div class="history-controls">
                    <input type="text" id="caseSearch" class="search-input" placeholder="Search cases..." />
                    <select id="caseFilter" class="filter-select">
                        <option value="all">All Cases</option>
                        <option value="week">This Week</option>
                        <option value="month">This Month</option>
                        <option value="critical">Critical Only</option>
                        <option value="abnormal">Abnormal Only</option>
                        <option value="normal">Normal Only</option>
                    </select>
                    <select id="caseSort" class="sort-select">
                        <option value="recent">Most Recent</option>
                        <option value="oldest">Oldest First</option>
                        <option value="severity">By Severity</option>
                    </select>
                </div>
            </div>
            <div id="caseGrid" class="case-grid">
                ${this.renderCaseCards(cases)}
            </div>
        `;

        this.attachCaseLibraryEvents();
    }

    renderCaseCards(cases) {
        if (cases.length === 0) {
            return `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 11l3 3L22 4"></path>
                        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path>
                    </svg>
                    <h3>No cases found</h3>
                    <p>Analyze your first ECG to start building your case library</p>
                </div>
            `;
        }

        return cases.map(caseItem => `
            <div class="case-card" data-case-id="${caseItem.id}">
                <img src="${caseItem.imageThumbnail}" alt="ECG Thumbnail" class="case-thumbnail" />
                <div class="case-content">
                    <div class="case-header">
                        <span class="case-diagnosis">${caseItem.diagnosis}</span>
                        <span class="case-severity ${caseItem.severity}">${caseItem.severity}</span>
                    </div>
                    <div class="case-meta">
                        <span class="case-date">${this.formatDate(caseItem.timestamp)}</span>
                    </div>
                    ${caseItem.tags && caseItem.tags.length > 0 ? `
                        <div class="case-tags">
                            ${caseItem.tags.slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('')}
                            ${caseItem.tags.length > 3 ? `<span class="tag-more">+${caseItem.tags.length - 3}</span>` : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="case-actions">
                    <button class="case-btn view-btn" onclick="historyUI.viewCase(${caseItem.id})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                    </button>
                    <button class="case-btn export-btn" onclick="historyUI.exportCase(${caseItem.id})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                    </button>
                    <button class="case-btn delete-btn" onclick="historyUI.deleteCase(${caseItem.id})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');
    }

    async renderAnalyticsDashboard(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const stats = await this.analytics.getStats();

        container.innerHTML = `
            <div class="analytics-header">
                <h2>Analytics Dashboard</h2>
                <div class="date-range-selector">
                    <button class="range-btn active" data-range="30">30 Days</button>
                    <button class="range-btn" data-range="90">90 Days</button>
                    <button class="range-btn" data-range="all">All Time</button>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${stats.totalAnalyzed}</div>
                        <div class="stat-label">Total ECGs Analyzed</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${stats.thisWeek}</div>
                        <div class="stat-label">This Week</div>
                    </div>
                </div>

                <div class="stat-card critical">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${stats.criticalFound}</div>
                        <div class="stat-label">Critical Findings</div>
                    </div>
                </div>

                <div class="stat-card success">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${stats.learningStreak}</div>
                        <div class="stat-label">Day Streak</div>
                    </div>
                </div>
            </div>

            <div class="charts-grid">
                <div class="chart-card">
                    <h3>Diagnosis Distribution</h3>
                    <div id="diagnosisChart" class="chart-container">
                        ${this.renderPieChart(stats.byDiagnosis)}
                    </div>
                </div>

                <div class="chart-card">
                    <h3>Activity Over Time</h3>
                    <div id="activityChart" class="chart-container">
                        ${this.renderLineChart(stats.activityByDay)}
                    </div>
                </div>

                <div class="chart-card full-width">
                    <h3>Activity Calendar</h3>
                    <div id="calendarHeatmap" class="calendar-heatmap">
                        ${this.renderCalendarHeatmap(stats.activityByDay)}
                    </div>
                </div>
            </div>
        `;

        this.attachAnalyticsEvents();
    }

    renderPieChart(data) {
        const total = Object.values(data).reduce((sum, val) => sum + val, 0);
        if (total === 0) {
            return '<div class="chart-empty">No data available</div>';
        }

        const colors = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#ca8a04', '#65a30d', '#0891b2'];
        const entries = Object.entries(data).slice(0, 7); // Top 7

        let currentAngle = 0;
        const segments = entries.map(([label, value], index) => {
            const percentage = (value / total) * 100;
            const angle = (value / total) * 360;
            const startAngle = currentAngle;
            currentAngle += angle;

            return `
                <div class="pie-legend-item">
                    <span class="pie-color" style="background: ${colors[index]}"></span>
                    <span class="pie-label">${label}</span>
                    <span class="pie-value">${value} (${percentage.toFixed(1)}%)</span>
                </div>
            `;
        }).join('');

        return `
            <div class="pie-chart-wrapper">
                <div class="pie-chart" style="background: conic-gradient(
                    ${entries.map(([_, value], index) => {
                        const prevTotal = entries.slice(0, index).reduce((sum, [_, v]) => sum + v, 0);
                        const startPct = (prevTotal / total) * 100;
                        const endPct = ((prevTotal + value) / total) * 100;
                        return `${colors[index]} ${startPct}% ${endPct}%`;
                    }).join(', ')}
                )"></div>
                <div class="pie-legend">
                    ${segments}
                </div>
            </div>
        `;
    }

    renderLineChart(activityData) {
        const entries = Object.entries(activityData).sort(([a], [b]) => a.localeCompare(b));
        if (entries.length === 0) {
            return '<div class="chart-empty">No data available</div>';
        }

        const maxValue = Math.max(...entries.map(([_, value]) => value), 1);
        const width = 100 / entries.length;

        const bars = entries.map(([date, value], index) => {
            const height = (value / maxValue) * 100;
            const label = new Date(date).getDate();

            return `
                <div class="line-bar" style="width: ${width}%; height: ${height}%" title="${date}: ${value}">
                    <span class="line-label">${label}</span>
                </div>
            `;
        }).join('');

        return `
            <div class="line-chart">
                ${bars}
            </div>
        `;
    }

    renderCalendarHeatmap(activityData) {
        const entries = Object.entries(activityData).sort(([a], [b]) => a.localeCompare(b));
        if (entries.length === 0) {
            return '<div class="chart-empty">No data available</div>';
        }

        const maxValue = Math.max(...entries.map(([_, value]) => value), 1);

        // Group by week
        const weeks = [];
        let currentWeek = [];

        entries.forEach(([date, value]) => {
            const dayOfWeek = new Date(date).getDay();

            if (dayOfWeek === 0 && currentWeek.length > 0) {
                weeks.push(currentWeek);
                currentWeek = [];
            }

            currentWeek.push([date, value]);
        });

        if (currentWeek.length > 0) {
            weeks.push(currentWeek);
        }

        return `
            <div class="heatmap-grid">
                ${weeks.map(week => `
                    <div class="heatmap-week">
                        ${week.map(([date, value]) => {
                            const intensity = maxValue > 0 ? Math.ceil((value / maxValue) * 4) : 0;
                            const day = new Date(date).toLocaleDateString('en-US', { weekday: 'short' });
                            return `
                                <div class="heatmap-day intensity-${intensity}"
                                     title="${date}: ${value} ECG${value !== 1 ? 's' : ''}">
                                    <span class="day-label">${day}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `).join('')}
            </div>
            <div class="heatmap-legend">
                <span>Less</span>
                <div class="legend-scale">
                    <div class="legend-box intensity-0"></div>
                    <div class="legend-box intensity-1"></div>
                    <div class="legend-box intensity-2"></div>
                    <div class="legend-box intensity-3"></div>
                    <div class="legend-box intensity-4"></div>
                </div>
                <span>More</span>
            </div>
        `;
    }

    formatDate(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;

        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    attachCaseLibraryEvents() {
        const searchInput = document.getElementById('caseSearch');
        const filterSelect = document.getElementById('caseFilter');
        const sortSelect = document.getElementById('caseSort');

        if (searchInput) {
            searchInput.addEventListener('input', async (e) => {
                this.caseLibrary.searchQuery = e.target.value;
                const cases = await this.caseLibrary.getCases(this.caseLibrary.currentFilter, this.caseLibrary.currentSort);
                document.getElementById('caseGrid').innerHTML = this.renderCaseCards(cases);
            });
        }

        if (filterSelect) {
            filterSelect.addEventListener('change', async (e) => {
                this.caseLibrary.currentFilter = e.target.value;
                const cases = await this.caseLibrary.getCases(e.target.value, this.caseLibrary.currentSort);
                document.getElementById('caseGrid').innerHTML = this.renderCaseCards(cases);
            });
        }

        if (sortSelect) {
            sortSelect.addEventListener('change', async (e) => {
                this.caseLibrary.currentSort = e.target.value;
                const cases = await this.caseLibrary.getCases(this.caseLibrary.currentFilter, e.target.value);
                document.getElementById('caseGrid').innerHTML = this.renderCaseCards(cases);
            });
        }
    }

    attachAnalyticsEvents() {
        const rangeButtons = document.querySelectorAll('.range-btn');
        rangeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                rangeButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                // TODO: Implement date range filtering
            });
        });
    }

    async viewCase(caseId) {
        const caseData = await this.db.getCase(caseId);
        // TODO: Open modal or navigate to case detail view
        console.log('Viewing case:', caseData);

        // For now, show in a modal-like alert
        alert(`Case: ${caseData.diagnosis}\n\nSummary: ${caseData.summary}\n\nClick Export to save this case.`);
    }

    async exportCase(caseId) {
        const choice = confirm('Export as PDF (OK) or JSON (Cancel)?');
        const format = choice ? 'pdf' : 'json';
        await this.caseLibrary.exportCase(caseId, format);
    }

    async deleteCase(caseId) {
        if (confirm('Are you sure you want to delete this case? This action cannot be undone.')) {
            await this.db.deleteCase(caseId);
            // Refresh the view
            const cases = await this.caseLibrary.getCases(this.caseLibrary.currentFilter, this.caseLibrary.currentSort);
            document.getElementById('caseGrid').innerHTML = this.renderCaseCards(cases);
        }
    }

    async saveCurrentAnalysis(analysisData, imageData, notes = '') {
        return await this.caseLibrary.saveCurrentAnalysis(analysisData, imageData, notes);
    }
}

// ============================================
// Global Instance
// ============================================
let historyUI = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    historyUI = new HistoryUI();
    await historyUI.init();

    // Auto-save after analysis if needed
    // This would be called from app.js after successful analysis
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ECGDatabase, CaseLibrary, AnalyticsDashboard, ECGComparison, HistoryUI };
}
