# ECG Guru - Case History & Analytics Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ECG Guru Web Application                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Analysis   │  │   History    │  │  Analytics   │         │
│  │     View     │  │     View     │  │     View     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                  │                  │
│         └─────────────────┼──────────────────┘                  │
│                           │                                      │
│                    ┌──────▼──────┐                              │
│                    │  HistoryUI  │ (Rendering Layer)            │
│                    │  Controller │                              │
│                    └──────┬──────┘                              │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                   │
│         │                 │                 │                   │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌─────▼─────┐            │
│  │ CaseLibrary  │  │  Analytics   │  │   ECG     │            │
│  │  Management  │  │  Dashboard   │  │Comparison │            │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘            │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                      │
│                    ┌──────▼──────┐                              │
│                    │ ECGDatabase │ (Data Layer)                 │
│                    │  Abstraction│                              │
│                    └──────┬──────┘                              │
│                           │                                      │
│                    ┌──────▼──────┐                              │
│                    │  IndexedDB  │ (Browser Storage)            │
│                    │             │                              │
│                    │ ┌─────────┐ │                              │
│                    │ │  Cases  │ │                              │
│                    │ │  Store  │ │                              │
│                    │ └─────────┘ │                              │
│                    │             │                              │
│                    │ ┌─────────┐ │                              │
│                    │ │Analytics│ │                              │
│                    │ │  Store  │ │                              │
│                    │ └─────────┘ │                              │
│                    └─────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Case Saving Flow
```
User Analyzes ECG
       │
       ▼
Backend Analysis
       │
       ▼
Analysis Results + Image
       │
       ▼
CaseLibrary.saveCurrentAnalysis()
       │
       ├──► Create Thumbnail (compress image)
       │
       ├──► Extract Primary Diagnosis
       │
       ├──► Determine Severity (critical/abnormal/normal)
       │
       ├──► Generate Tags (STEMI, VT, WPW, etc.)
       │
       ▼
Build Case Object
       │
       ▼
ECGDatabase.saveCase()
       │
       ▼
IndexedDB Write
       │
       ▼
Update Daily Analytics
       │
       ▼
Return Case ID
```

### 2. Case Library Rendering Flow
```
User Opens History View
       │
       ▼
HistoryUI.renderCaseLibrary(containerId)
       │
       ▼
CaseLibrary.getCases(filter, sort)
       │
       ├──► ECGDatabase.getAllCases()
       │         │
       │         ▼
       │    IndexedDB Query
       │         │
       │         ▼
       │    Raw Cases Array
       │
       ├──► Apply Filter (all/week/month/critical/abnormal/normal)
       │
       ├──► Apply Search (if query exists)
       │
       ├──► Apply Sort (recent/oldest/severity)
       │
       ▼
Filtered & Sorted Cases
       │
       ▼
renderCaseCards(cases)
       │
       ├──► For each case:
       │    ├──► Create card HTML
       │    ├──► Attach thumbnail
       │    ├──► Add severity badge
       │    ├──► Add tags
       │    └──► Attach event listeners
       │
       ▼
Inject into DOM
       │
       ▼
Attach Global Event Listeners (search, filter, sort)
```

### 3. Analytics Dashboard Flow
```
User Opens Analytics View
       │
       ▼
HistoryUI.renderAnalyticsDashboard(containerId)
       │
       ▼
AnalyticsDashboard.getStats()
       │
       ├──► ECGDatabase.getAllCases()
       │         │
       │         ▼
       │    All Cases Array
       │
       ├──► Calculate Totals (all-time, week, month)
       │
       ├──► Count by Severity (critical, abnormal, normal)
       │
       ├──► Group by Diagnosis
       │
       ├──► Build Activity by Day (last 30 days)
       │
       ├──► Calculate Learning Streak
       │
       ▼
Stats Object
       │
       ▼
Render Stats Cards
       │
       ▼
Render Charts
       │
       ├──► renderPieChart(byDiagnosis)
       │    └──► CSS conic-gradient pie chart
       │
       ├──► renderLineChart(activityByDay)
       │    └──► Flexbox bar chart
       │
       ├──► renderCalendarHeatmap(activityByDay)
       │    └──► Grid-based heatmap
       │
       ▼
Inject into DOM
```

## Class Hierarchy

### ECGDatabase
**Responsibility**: Low-level IndexedDB operations
**Methods**:
- `init()` - Open/create database
- `saveCase(caseData)` - Insert new case
- `updateCase(id, caseData)` - Update existing case
- `getAllCases()` - Retrieve all cases
- `getCase(id)` - Retrieve specific case
- `deleteCase(id)` - Remove case
- `searchCases(query)` - Text search across cases
- `updateAnalytics(date, stats)` - Store daily analytics
- `getAnalyticsByDateRange(start, end)` - Retrieve analytics

**Dependencies**: Browser IndexedDB API

### CaseLibrary
**Responsibility**: Business logic for case management
**Methods**:
- `saveCurrentAnalysis(analysis, imageData, notes)` - Convert analysis to case
- `createThumbnail(imageData, maxWidth)` - Compress image
- `extractPrimaryDiagnosis(analysis)` - Find main diagnosis
- `determineSeverity(analysis)` - Calculate severity level
- `generateTags(analysis)` - Auto-tag based on findings
- `getCases(filter, sort)` - Retrieve filtered/sorted cases
- `updateDailyAnalytics()` - Update today's analytics
- `exportCase(caseId, format)` - Export as PDF or JSON
- `exportAsJSON(caseData)` - JSON download
- `exportAsPDF(caseData)` - Print dialog with formatted HTML
- `generatePrintableHTML(caseData)` - Create print-ready report

**Dependencies**: ECGDatabase, Canvas API (for thumbnails)

### AnalyticsDashboard
**Responsibility**: Statistics calculation and aggregation
**Methods**:
- `getStats()` - Calculate comprehensive statistics
- `getRecentActivity(days)` - Get recent cases
- `getDiagnosisTrends()` - Monthly diagnosis trends

**Dependencies**: ECGDatabase

### ECGComparison
**Responsibility**: Side-by-side case comparison
**Methods**:
- `loadComparison(caseIdA, caseIdB, db)` - Load two cases
- `findDifferences()` - Compare and highlight differences
- `compareMeasurements()` - Compare ECG measurements
- `compareFindings()` - Compare clinical findings

**Dependencies**: ECGDatabase
**Status**: Ready for expansion (UI not yet built)

### HistoryUI
**Responsibility**: Orchestration and rendering
**Properties**:
- `db` - ECGDatabase instance
- `caseLibrary` - CaseLibrary instance
- `analytics` - AnalyticsDashboard instance
- `comparison` - ECGComparison instance
- `currentView` - Active view ('library', 'analytics', 'comparison')

**Methods**:
- `init()` - Initialize all subsystems
- `renderCaseLibrary(containerId)` - Render case library UI
- `renderAnalyticsDashboard(containerId)` - Render analytics UI
- `renderCaseCards(cases)` - Generate case card HTML
- `renderPieChart(data)` - Generate pie chart HTML/CSS
- `renderLineChart(data)` - Generate line chart HTML/CSS
- `renderCalendarHeatmap(data)` - Generate heatmap HTML/CSS
- `formatDate(timestamp)` - Human-readable date formatting
- `attachCaseLibraryEvents()` - Wire up search/filter/sort
- `attachAnalyticsEvents()` - Wire up date range selector
- `viewCase(caseId)` - Show case details
- `exportCase(caseId)` - Trigger export
- `deleteCase(caseId)` - Delete with confirmation
- `saveCurrentAnalysis(data, image, notes)` - Wrapper for CaseLibrary

**Dependencies**: All other classes

## Database Schema

### Cases Object Store
```javascript
{
  keyPath: 'id',
  autoIncrement: true,
  indexes: [
    { name: 'timestamp', unique: false },
    { name: 'diagnosis', unique: false },
    { name: 'severity', unique: false },
    { name: 'tags', unique: false, multiEntry: true }
  ]
}
```

**Sample Record**:
```javascript
{
  id: 1,
  timestamp: 1704398400000,
  diagnosis: 'Anterior STEMI',
  summary: 'ST elevation in leads V2-V4...',
  severity: 'critical',
  measurements: { heart_rate: 82, ... },
  findings: [ { category: '...', ... } ],
  algorithmResults: [ { name: '...', ... } ],
  imageThumbnail: 'data:image/jpeg;base64,...',
  imageData: 'data:image/jpeg;base64,...',
  conversationHistory: [ { role: 'user', content: '...' } ],
  tags: ['Critical', 'STEMI', 'LAD'],
  notes: 'User notes',
  userLevel: 'student'
}
```

### Analytics Object Store
```javascript
{
  keyPath: 'date'
}
```

**Sample Record**:
```javascript
{
  date: '2026-01-04',
  count: 5,
  critical: 1,
  abnormal: 2,
  normal: 2
}
```

## CSS Architecture

### Component Hierarchy
```
history.css
├── History Header & Controls
│   ├── .history-header
│   ├── .history-controls
│   ├── .search-input
│   ├── .filter-select
│   └── .sort-select
│
├── Case Grid & Cards
│   ├── .case-grid
│   ├── .case-card
│   ├── .case-thumbnail
│   ├── .case-content
│   ├── .case-header
│   ├── .case-severity (critical/abnormal/normal)
│   ├── .case-tags
│   └── .case-actions
│
├── Analytics Dashboard
│   ├── .analytics-header
│   ├── .stats-grid
│   ├── .stat-card (primary/critical/success)
│   └── .charts-grid
│
├── Charts
│   ├── Pie Chart
│   │   ├── .pie-chart-wrapper
│   │   ├── .pie-chart (conic-gradient)
│   │   └── .pie-legend
│   │
│   ├── Line Chart
│   │   ├── .line-chart
│   │   └── .line-bar
│   │
│   └── Calendar Heatmap
│       ├── .heatmap-grid
│       ├── .heatmap-week
│       ├── .heatmap-day
│       └── .heatmap-legend
│
├── Responsive Breakpoints
│   ├── @media (max-width: 1024px)
│   ├── @media (max-width: 768px)
│   └── @media (max-width: 480px)
│
├── Dark Mode
│   └── body.dark-mode overrides
│
└── Print Styles
    └── @media print
```

### CSS Variables Used
```css
--color-primary: #2563eb
--color-success: #059669
--color-warning: #f59e0b
--color-danger: #dc2626
--bg-primary: #ffffff
--bg-secondary: #f9fafb
--text-primary: #1f2937
--text-secondary: #6b7280
--border-color: #e5e7eb
```

## Performance Optimization Strategies

### 1. Image Compression
- Thumbnails created at 300px width
- JPEG quality set to 70%
- ~70% storage reduction per case
- Lazy loading ready (structure in place)

### 2. IndexedDB Optimization
- Indexes on frequently queried fields (timestamp, diagnosis, severity)
- Multi-entry index on tags for fast tag searches
- Batch operations for analytics updates

### 3. Rendering Optimization
- Staggered animations prevent jank (0.05s delay per card)
- CSS transforms for hover effects (GPU-accelerated)
- Flexbox/Grid for layouts (no float/positioning hacks)
- Minimal DOM manipulation (build HTML strings, single inject)

### 4. Search & Filter
- In-memory filtering after single DB query
- Debounced search input (can add if needed)
- Efficient array methods (filter, map, reduce)

## Security Considerations

### 1. Data Privacy
- All data stored locally (IndexedDB)
- No automatic cloud sync
- User controls all data

### 2. XSS Prevention
- No innerHTML with user-generated content
- Template literals properly escaped
- SVG icons embedded (no external sources)

### 3. Input Validation
- File type validation on upload
- File size limits (10MB)
- Search query sanitization

## Browser Compatibility Matrix

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| IndexedDB | 24+ | 16+ | 10+ | 12+ |
| CSS Grid | 57+ | 52+ | 10.1+ | 16+ |
| CSS Flexbox | 29+ | 28+ | 9+ | 12+ |
| Conic Gradient | 69+ | 83+ | 12.1+ | 79+ |
| Canvas API | 4+ | 3.6+ | 3.1+ | 12+ |
| ES6 Classes | 49+ | 45+ | 10+ | 13+ |
| Async/Await | 55+ | 52+ | 11+ | 15+ |

**Recommended Minimum**: Chrome 69+, Firefox 83+, Safari 12.1+, Edge 79+

## Testing Strategy

### Unit Tests (Future)
```javascript
// Example test structure
describe('CaseLibrary', () => {
  test('extractPrimaryDiagnosis returns critical first', () => {
    // ...
  });

  test('generateTags extracts medical terms', () => {
    // ...
  });
});

describe('AnalyticsDashboard', () => {
  test('calculates learning streak correctly', () => {
    // ...
  });
});
```

### Integration Tests (Manual)
1. Save case → verify in IndexedDB
2. Search cases → verify results
3. Export PDF → verify print dialog
4. Dark mode toggle → verify all colors
5. Mobile responsive → verify layout

### Load Tests
- 100 cases → verify performance
- 500 cases → verify scroll performance
- 1000 cases → verify memory usage

## Deployment Checklist

- [ ] Minify JavaScript (optional, ~40KB → ~20KB)
- [ ] Minify CSS (optional, ~19KB → ~10KB)
- [ ] Enable gzip compression on server
- [ ] Add Content-Security-Policy headers
- [ ] Test on target browsers
- [ ] Test on target devices (mobile/tablet)
- [ ] Verify IndexedDB quota on iOS Safari
- [ ] Add error tracking (Sentry, etc.)
- [ ] Add usage analytics (optional)
- [ ] Document backup/restore strategy

## Maintenance Guide

### Adding New Filters
1. Update `getCases()` in CaseLibrary
2. Add option to filter select in renderCaseLibrary()
3. Test with edge cases

### Adding New Charts
1. Add render method to HistoryUI
2. Call from renderAnalyticsDashboard()
3. Add CSS to history.css

### Adding New Indexes
1. Increment DB_VERSION in history.js
2. Add index in onupgradeneeded handler
3. Test migration with existing data

### Performance Monitoring
```javascript
// Add performance markers
performance.mark('case-save-start');
await historyUI.saveCurrentAnalysis(...);
performance.mark('case-save-end');
performance.measure('case-save', 'case-save-start', 'case-save-end');
console.log(performance.getEntriesByName('case-save'));
```

## Extension Points

### 1. Custom Algorithms
Add new analysis to saved cases:
```javascript
// In saveCurrentAnalysis
caseData.customAlgorithms = runCustomAnalysis(analysis);
```

### 2. External Integration
Export to external systems:
```javascript
async exportToEMR(caseId) {
  const caseData = await this.db.getCase(caseId);
  const fhirData = convertToFHIR(caseData);
  await sendToEMR(fhirData);
}
```

### 3. Cloud Sync
Add sync capability:
```javascript
async syncToCloud() {
  const cases = await this.db.getAllCases();
  const unsyncedCases = cases.filter(c => !c.synced);
  await uploadToCloud(unsyncedCases);
}
```

## Troubleshooting Guide

### Issue: IndexedDB quota exceeded
**Solution**: Implement cleanup strategy
```javascript
const MB_90_DAYS_AGO = Date.now() - (90 * 24 * 60 * 60 * 1000);
const oldCases = cases.filter(c => c.timestamp < MB_90_DAYS_AGO);
for (const c of oldCases) await db.deleteCase(c.id);
```

### Issue: Slow rendering with many cases
**Solution**: Add pagination or virtual scrolling
```javascript
const CASES_PER_PAGE = 20;
const paginatedCases = cases.slice(0, CASES_PER_PAGE);
```

### Issue: Large images causing storage issues
**Solution**: Reduce thumbnail size or quality
```javascript
// In createThumbnail, change:
canvas.toDataURL('image/jpeg', 0.5);  // 50% quality instead of 70%
```

---

**Architecture Version**: 1.0.0
**Last Updated**: 2026-01-04
**Maintainer**: ECG Guru Development Team
