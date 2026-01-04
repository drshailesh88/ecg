# Case History & Analytics Integration Guide

## Overview

The ECG Guru Case History & Analytics module provides comprehensive case management, analytics dashboard, and comparison features. This guide explains how to integrate these features into your existing ECG Guru application.

## Files Included

1. **history.js** - Core functionality for case management and analytics
2. **history.css** - Styling for all history components
3. **history-demo.html** - Standalone demo showing all features

## Quick Start

### 1. Add Required Files to HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Existing head content -->
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="history.css">  <!-- Add this -->
</head>
<body>
    <!-- Your app content -->

    <script src="app.js"></script>
    <script src="history.js"></script>  <!-- Add this -->
</body>
</html>
```

### 2. Initialize History Module

The history module auto-initializes on DOM ready. Access it via the global `historyUI` object:

```javascript
// Wait for initialization
document.addEventListener('DOMContentLoaded', async () => {
    // historyUI is now available globally
    console.log('History module ready:', historyUI);
});
```

## Core Features

### Feature 1: Save Analysis to Case Library

After an ECG analysis is complete, save it to the case library:

```javascript
async function analyzeECG() {
    // Your existing analysis code
    const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        body: JSON.stringify({
            image_base64: state.uploadedImage,
            user_level: state.userLevel,
            include_teaching: state.teachingMode
        })
    });

    const analysisData = await response.json();

    // NEW: Save to case library
    try {
        const caseId = await historyUI.saveCurrentAnalysis(
            analysisData,              // Analysis results from backend
            state.uploadedImage,       // Base64 image data
            ''                         // Optional user notes
        );

        console.log('Case saved with ID:', caseId);
        showToast('Analysis saved to case library', 'success');
    } catch (error) {
        console.error('Failed to save case:', error);
        showToast('Failed to save case', 'error');
    }
}
```

### Feature 2: Display Case Library

Render the case library in any container:

```html
<!-- Add this container to your HTML -->
<div id="caseLibraryContainer"></div>
```

```javascript
// Render the case library
await historyUI.renderCaseLibrary('caseLibraryContainer');
```

This will display:
- All saved cases as cards
- Search functionality
- Filter by severity/timeframe
- Sort options
- View/Export/Delete actions

### Feature 3: Display Analytics Dashboard

Render analytics in any container:

```html
<!-- Add this container to your HTML -->
<div id="analyticsDashboard"></div>
```

```javascript
// Render the analytics dashboard
await historyUI.renderAnalyticsDashboard('analyticsDashboard');
```

This will display:
- Total cases analyzed
- Weekly/monthly stats
- Critical findings count
- Learning streak
- Diagnosis distribution pie chart
- Activity timeline
- Calendar heatmap (GitHub-style)

### Feature 4: Manual Case Operations

```javascript
// Get all cases
const allCases = await historyUI.db.getAllCases();

// Get a specific case
const caseData = await historyUI.db.getCase(caseId);

// Search cases
const searchResults = await historyUI.db.searchCases('STEMI');

// Delete a case
await historyUI.db.deleteCase(caseId);

// Export a case
await historyUI.caseLibrary.exportCase(caseId, 'pdf');  // or 'json'
```

### Feature 5: Get Analytics Stats

```javascript
// Get comprehensive stats
const stats = await historyUI.analytics.getStats();

console.log(stats);
// {
//   totalAnalyzed: 147,
//   thisWeek: 23,
//   thisMonth: 89,
//   criticalFound: 12,
//   abnormalFound: 34,
//   normalFound: 101,
//   byDiagnosis: { 'Normal': 101, 'STEMI': 12, ... },
//   activityByDay: { '2026-01-01': 5, '2026-01-02': 3, ... },
//   learningStreak: 7,
//   averagePerWeek: 23
// }
```

## Integration Patterns

### Pattern 1: Add "Save Case" Button

```html
<!-- In your results section -->
<button id="saveCaseBtn" class="btn btn-primary">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
    </svg>
    Save Case
</button>
```

```javascript
document.getElementById('saveCaseBtn').addEventListener('click', async () => {
    if (!state.currentAnalysis || !state.uploadedImage) {
        showToast('No analysis to save', 'error');
        return;
    }

    const notes = prompt('Add notes to this case (optional):');

    try {
        await historyUI.saveCurrentAnalysis(
            state.currentAnalysis,
            state.uploadedImage,
            notes || ''
        );
        showToast('Case saved successfully!', 'success');
    } catch (error) {
        showToast('Failed to save case', 'error');
    }
});
```

### Pattern 2: Add Navigation Tabs

```html
<div class="nav-tabs">
    <button class="tab-btn active" data-view="analyze">
        <svg>...</svg> Analyze
    </button>
    <button class="tab-btn" data-view="history">
        <svg>...</svg> History
    </button>
    <button class="tab-btn" data-view="analytics">
        <svg>...</svg> Analytics
    </button>
</div>

<div id="analyzeView" class="view-container">
    <!-- Your existing analysis UI -->
</div>

<div id="historyView" class="view-container hidden">
    <!-- Will be populated by history.js -->
</div>

<div id="analyticsView" class="view-container hidden">
    <!-- Will be populated by history.js -->
</div>
```

```javascript
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        const view = e.currentTarget.dataset.view;

        // Hide all views
        document.querySelectorAll('.view-container').forEach(v => {
            v.classList.add('hidden');
        });

        // Update active tab
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.remove('active');
        });
        e.currentTarget.classList.add('active');

        // Show selected view
        if (view === 'analyze') {
            document.getElementById('analyzeView').classList.remove('hidden');
        } else if (view === 'history') {
            document.getElementById('historyView').classList.remove('hidden');
            await historyUI.renderCaseLibrary('historyView');
        } else if (view === 'analytics') {
            document.getElementById('analyticsView').classList.remove('hidden');
            await historyUI.renderAnalyticsDashboard('analyticsView');
        }
    });
});
```

### Pattern 3: Auto-Save Every Analysis

```javascript
// In your existing analyzeECG function
async function analyzeECG() {
    // ... existing analysis code ...

    const data = await response.json();
    state.currentAnalysis = data;
    state.analysisId = data.analysis_id || generateUUID();

    displayAnalysisResults(data);

    // AUTO-SAVE: Save every analysis automatically
    try {
        await historyUI.saveCurrentAnalysis(
            data,
            state.uploadedImage,
            `Auto-saved analysis`
        );
        console.log('Analysis auto-saved to history');
    } catch (error) {
        console.error('Failed to auto-save:', error);
        // Don't show error to user for auto-save failures
    }

    hideLoadingState();
    showToast('Analysis complete', 'success');
}
```

## Data Structure

### Case Object Structure

```javascript
{
    id: 123,                          // Auto-generated
    timestamp: 1704398400000,         // Unix timestamp
    diagnosis: 'Anterior STEMI',      // Primary diagnosis
    summary: 'ST elevation in V2-V4...', // Summary text
    severity: 'critical',             // 'normal', 'abnormal', 'critical'
    measurements: {                   // ECG measurements
        heart_rate: 82,
        pr_interval_ms: 160,
        qrs_duration_ms: 95,
        // ... other measurements
    },
    findings: [                       // Array of findings
        {
            category: 'ST Segment',
            finding: 'ST Elevation',
            explanation: '...',
            severity: 'critical'
        }
    ],
    algorithmResults: [],             // Algorithm outputs
    imageThumbnail: 'data:image/...', // Compressed thumbnail
    imageData: 'data:image/...',      // Full image (base64)
    conversationHistory: [],          // Chat messages
    tags: ['Critical', 'STEMI', 'LAD'], // Auto-generated tags
    notes: 'User notes here',         // User-entered notes
    userLevel: 'student'              // User experience level
}
```

## Advanced Features

### Custom Case Views

```javascript
// Get cases with custom filtering
const criticalCases = await historyUI.caseLibrary.getCases('critical', 'recent');
const thisWeekCases = await historyUI.caseLibrary.getCases('week', 'recent');

// Render custom case list
criticalCases.forEach(caseItem => {
    console.log(`${caseItem.diagnosis} - ${new Date(caseItem.timestamp).toLocaleDateString()}`);
});
```

### Export Functionality

```javascript
// Export as JSON
await historyUI.caseLibrary.exportCase(caseId, 'json');

// Export as PDF (opens print dialog)
await historyUI.caseLibrary.exportCase(caseId, 'pdf');
```

### Comparison Feature (Future)

```javascript
// Load two cases for comparison
const comparison = new ECGComparison();
await comparison.loadComparison(caseId1, caseId2, historyUI.db);

// Find differences
const differences = comparison.findDifferences();
console.log(differences);
```

## Styling & Theming

The history module uses CSS variables for theming. Customize by overriding:

```css
:root {
    --color-primary: #2563eb;
    --color-success: #059669;
    --color-warning: #f59e0b;
    --color-danger: #dc2626;
    --bg-primary: #ffffff;
    --bg-secondary: #f9fafb;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
}
```

Dark mode is automatically supported if your app has a `dark-mode` class on `<body>`.

## Browser Compatibility

- **IndexedDB**: All modern browsers (Chrome 24+, Firefox 16+, Safari 10+, Edge 12+)
- **ES6+ Features**: Requires modern browser or transpilation
- **Canvas API**: For thumbnail generation

For older browser support, consider adding polyfills.

## Performance Considerations

### Image Storage

- Thumbnails are compressed to ~30% quality at 300px width
- Full images are stored as-is (base64)
- Consider implementing cleanup for old cases:

```javascript
// Delete cases older than 90 days
const ninetyDaysAgo = Date.now() - (90 * 24 * 60 * 60 * 1000);
const allCases = await historyUI.db.getAllCases();
const oldCases = allCases.filter(c => c.timestamp < ninetyDaysAgo);

for (const oldCase of oldCases) {
    await historyUI.db.deleteCase(oldCase.id);
}
```

### IndexedDB Limits

- Quota varies by browser (typically 50% of available disk space)
- Minimum ~10MB guaranteed
- Monitor usage and implement cleanup as needed

## Troubleshooting

### Issue: Cases not saving

```javascript
// Check if IndexedDB is available
if (!window.indexedDB) {
    console.error('IndexedDB not supported');
    // Fallback to localStorage or show warning
}

// Check initialization
if (!historyUI || !historyUI.db) {
    console.error('History module not initialized');
    await historyUI.init();
}
```

### Issue: Render not showing

```javascript
// Ensure container exists
const container = document.getElementById('caseLibraryContainer');
if (!container) {
    console.error('Container not found');
    return;
}

// Check for cases
const cases = await historyUI.db.getAllCases();
console.log(`Found ${cases.length} cases`);
```

## API Reference

### ECGDatabase

- `init()` - Initialize database
- `saveCase(caseData)` - Save a case
- `updateCase(id, caseData)` - Update existing case
- `getAllCases()` - Get all cases
- `getCase(id)` - Get specific case
- `deleteCase(id)` - Delete a case
- `searchCases(query)` - Search cases

### CaseLibrary

- `saveCurrentAnalysis(analysis, imageData, notes)` - Save analysis as case
- `getCases(filter, sort)` - Get filtered/sorted cases
- `exportCase(caseId, format)` - Export case

### AnalyticsDashboard

- `getStats()` - Get comprehensive statistics
- `getRecentActivity(days)` - Get recent cases
- `getDiagnosisTrends()` - Get trends by diagnosis

### HistoryUI

- `init()` - Initialize UI module
- `renderCaseLibrary(containerId)` - Render case library
- `renderAnalyticsDashboard(containerId)` - Render analytics
- `viewCase(caseId)` - View case details
- `exportCase(caseId)` - Export case
- `deleteCase(caseId)` - Delete case

## Testing

See `history-demo.html` for a complete working example with demo data generation.

## Future Enhancements

- [ ] Cloud sync for cases
- [ ] Multi-case comparison view
- [ ] Export to FHIR format
- [ ] Quiz mode using saved cases
- [ ] Case sharing with privacy controls
- [ ] Advanced analytics (diagnosis accuracy tracking)
- [ ] Integration with EMR system

## Support

For issues or questions, refer to the ECG Guru documentation or check `history-demo.html` for working examples.
