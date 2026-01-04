// ============================================
// ECG Guru - Teaching Mode Module
// ============================================
// Interactive teaching system that makes ECG learning habit-forming
// Features: Walkthrough, Progress Tracking, Quiz Mode, Badges, Streaks

// ============================================
// Constants & Configuration
// ============================================

const BADGES = {
    'first_analysis': {
        name: 'First Steps',
        icon: '🎯',
        description: 'Completed your first ECG analysis',
        requirement: 1
    },
    'stemi_spotted': {
        name: 'Life Saver',
        icon: '❤️',
        description: 'Correctly identified a STEMI',
        requirement: 1
    },
    'week_streak': {
        name: 'Dedicated Learner',
        icon: '🔥',
        description: 'Maintained a 7-day learning streak',
        requirement: 7
    },
    'vt_master': {
        name: 'Rhythm Expert',
        icon: '⚡',
        description: 'Mastered VT vs SVT differentiation',
        requirement: 10
    },
    'hundred_ecgs': {
        name: 'ECG Guru',
        icon: '🏆',
        description: 'Analyzed 100 ECGs',
        requirement: 100
    },
    'perfect_quiz': {
        name: 'Perfect Score',
        icon: '⭐',
        description: 'Achieved 100% on a quiz',
        requirement: 1
    },
    'pathway_expert': {
        name: 'EP Fellow',
        icon: '🎓',
        description: 'Mastered accessory pathway localization',
        requirement: 15
    },
    'teaching_advocate': {
        name: 'Professor',
        icon: '👨‍🏫',
        description: 'Completed all teaching modules',
        requirement: 1
    }
};

const TEACHING_TOPICS = {
    'rhythm': {
        name: 'Rhythm Analysis',
        lessons: [
            'Normal Sinus Rhythm',
            'Sinus Tachycardia & Bradycardia',
            'Atrial Fibrillation',
            'Atrial Flutter',
            'AV Blocks'
        ]
    },
    'intervals': {
        name: 'Intervals & Measurements',
        lessons: [
            'PR Interval',
            'QRS Duration',
            'QT/QTc Interval',
            'Axis Determination'
        ]
    },
    'stemi': {
        name: 'STEMI Recognition',
        lessons: [
            'ST Segment Basics',
            'Anterior STEMI (LAD)',
            'Inferior STEMI (RCA)',
            'Lateral STEMI (LCx)',
            'Posterior STEMI',
            'RCA vs LCx Differentiation'
        ]
    },
    'vt_svt': {
        name: 'VT vs SVT',
        lessons: [
            'Wide Complex Tachycardia Basics',
            'Brugada Algorithm',
            'Vereckei Algorithm',
            'Basel Algorithm'
        ]
    },
    'wpw': {
        name: 'WPW & Accessory Pathways',
        lessons: [
            'Pre-excitation Patterns',
            'SMART-WPW Algorithm',
            'Pathway Localization'
        ]
    }
};

const ECG_COMPONENTS = [
    {
        id: 'p_wave',
        name: 'P Wave',
        description: 'Represents atrial depolarization',
        normal: 'Upright in leads I, II, aVF; duration <120ms',
        highlight_color: '#4CAF50'
    },
    {
        id: 'pr_interval',
        name: 'PR Interval',
        description: 'Time from start of atrial to ventricular depolarization',
        normal: '120-200ms (3-5 small squares)',
        highlight_color: '#2196F3'
    },
    {
        id: 'qrs_complex',
        name: 'QRS Complex',
        description: 'Represents ventricular depolarization',
        normal: '<120ms (narrow); Q wave <1mm, R wave progression V1-V6',
        highlight_color: '#9C27B0'
    },
    {
        id: 'st_segment',
        name: 'ST Segment',
        description: 'Period between ventricular depolarization and repolarization',
        normal: 'Isoelectric (at baseline); elevation/depression <1mm',
        highlight_color: '#FF9800'
    },
    {
        id: 't_wave',
        name: 'T Wave',
        description: 'Represents ventricular repolarization',
        normal: 'Upright in leads with tall R waves; asymmetric shape',
        highlight_color: '#F44336'
    },
    {
        id: 'qt_interval',
        name: 'QT Interval',
        description: 'Total ventricular depolarization and repolarization time',
        normal: 'QTc <440ms (men), <460ms (women)',
        highlight_color: '#00BCD4'
    }
];

// ============================================
// ECG Walkthrough - Interactive Step-by-Step Guide
// ============================================

class ECGWalkthrough {
    constructor() {
        this.currentStep = 0;
        this.userLevel = 'student';
        this.isActive = false;
        this.ecgImage = null;
    }

    start(ecgImage, userLevel = 'student') {
        this.ecgImage = ecgImage;
        this.userLevel = userLevel;
        this.currentStep = 0;
        this.isActive = true;
        this.render();
        this.showStep(0);
    }

    render() {
        const container = document.createElement('div');
        container.id = 'ecgWalkthroughModal';
        container.className = 'teaching-modal';

        container.innerHTML = `
            <div class="teaching-modal-overlay" onclick="ecgWalkthrough.close()"></div>
            <div class="teaching-modal-content walkthrough-modal">
                <button class="teaching-modal-close" onclick="ecgWalkthrough.close()">×</button>

                <div class="walkthrough-header">
                    <h2>Interactive ECG Walkthrough</h2>
                    <div class="walkthrough-progress">
                        <div class="walkthrough-progress-bar" id="walkthroughProgressBar"></div>
                    </div>
                    <p class="walkthrough-step-indicator" id="walkthroughStepIndicator">
                        Step <span id="currentStepNum">1</span> of ${ECG_COMPONENTS.length}
                    </p>
                </div>

                <div class="walkthrough-body">
                    <div class="walkthrough-image-container">
                        <img id="walkthroughEcgImage" src="${this.ecgImage}" alt="ECG">
                        <canvas id="walkthroughCanvas" class="walkthrough-highlight-canvas"></canvas>
                    </div>

                    <div class="walkthrough-content">
                        <div class="component-indicator" id="componentIndicator"></div>
                        <h3 id="componentTitle"></h3>
                        <p class="component-description" id="componentDescription"></p>
                        <div class="component-normal" id="componentNormal">
                            <strong>Normal Values:</strong>
                            <p id="componentNormalText"></p>
                        </div>

                        <div class="teaching-point-box" id="teachingPointBox">
                            <div class="teaching-point-icon">💡</div>
                            <div id="teachingPointContent"></div>
                        </div>
                    </div>
                </div>

                <div class="walkthrough-footer">
                    <button class="btn btn-secondary" id="prevStepBtn" onclick="ecgWalkthrough.prevStep()">
                        ← Previous
                    </button>
                    <button class="btn btn-primary" id="nextStepBtn" onclick="ecgWalkthrough.nextStep()">
                        Next →
                    </button>
                    <button class="btn btn-success hidden" id="finishWalkthroughBtn" onclick="ecgWalkthrough.finish()">
                        Finish ✓
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(container);
    }

    showStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= ECG_COMPONENTS.length) return;

        this.currentStep = stepIndex;
        const component = ECG_COMPONENTS[stepIndex];

        // Update progress
        const progress = ((stepIndex + 1) / ECG_COMPONENTS.length) * 100;
        document.getElementById('walkthroughProgressBar').style.width = `${progress}%`;
        document.getElementById('currentStepNum').textContent = stepIndex + 1;

        // Update component info
        const indicator = document.getElementById('componentIndicator');
        indicator.style.backgroundColor = component.highlight_color;

        document.getElementById('componentTitle').textContent = component.name;
        document.getElementById('componentDescription').textContent = component.description;
        document.getElementById('componentNormalText').textContent = component.normal;

        // Add level-appropriate teaching point
        this.showTeachingPoint(component);

        // Update navigation buttons
        document.getElementById('prevStepBtn').disabled = stepIndex === 0;

        const nextBtn = document.getElementById('nextStepBtn');
        const finishBtn = document.getElementById('finishWalkthroughBtn');

        if (stepIndex === ECG_COMPONENTS.length - 1) {
            nextBtn.classList.add('hidden');
            finishBtn.classList.remove('hidden');
        } else {
            nextBtn.classList.remove('hidden');
            finishBtn.classList.add('hidden');
        }

        // Highlight component on ECG (simulated - would need actual lead detection)
        this.highlightComponent(component);
    }

    highlightComponent(component) {
        // In production, this would use actual ECG lead detection
        // For now, we'll show a visual indicator
        const canvas = document.getElementById('walkthroughCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const img = document.getElementById('walkthroughEcgImage');

        canvas.width = img.offsetWidth;
        canvas.height = img.offsetHeight;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw a pulsing highlight box (placeholder for actual detection)
        ctx.strokeStyle = component.highlight_color;
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);

        // Simulate component location (would be from actual detection)
        const x = canvas.width * 0.2;
        const y = canvas.height * 0.4;
        const width = canvas.width * 0.3;
        const height = canvas.height * 0.2;

        ctx.strokeRect(x, y, width, height);
    }

    showTeachingPoint(component) {
        const teachingPoints = {
            'p_wave': {
                'rmp': 'Look for a small bump before each heartbeat. If missing or irregular, the rhythm may be abnormal.',
                'student': 'The P wave shows the atria contracting. Check for: presence, regularity, and morphology across leads.',
                'resident': 'Analyze P wave axis, morphology in V1 (biphasic = normal), and relationship to QRS. Consider left atrial enlargement if P wave duration >120ms.',
                'cardiologist': 'Advanced: Retrograde P waves in junctional rhythms, P wave morphology for atrial tachycardia origin, flutter waves vs P waves in differential diagnosis.'
            },
            'pr_interval': {
                'rmp': 'This is the time from atrial to ventricular contraction. If too long, there may be a heart block.',
                'student': 'Count small squares: 3-5 = normal (120-200ms). >5 = first-degree AV block. Progressive lengthening = Mobitz I.',
                'resident': 'Short PR (<120ms) suggests pre-excitation (WPW, LGL). Variable PR indicates AV dissociation or Mobitz II. Consider RP relationship in tachycardias.',
                'cardiologist': 'Differential: Short PR with delta wave (WPW) vs without (LGL, enhanced AV conduction). RP-PR relationship critical for SVT mechanism.'
            },
            'qrs_complex': {
                'rmp': 'This represents the main heartbeat. If very wide or unusual shape, refer to cardiologist.',
                'student': 'Normal QRS <120ms (3 small squares). Wide QRS suggests bundle branch block or ventricular origin. Check R wave progression V1→V6.',
                'resident': 'Bundle branch block criteria: RBBB (RSR\' in V1), LBBB (broad R in V5-V6). Pathological Q waves indicate prior MI. Check for fragmentation.',
                'cardiologist': 'Advanced: QRS morphology for VT vs SVT (Brugada, Vereckei criteria). His-Purkinje disease patterns. Epsilon waves in ARVC. Pre-excitation localization.'
            },
            'st_segment': {
                'rmp': 'If this is elevated >2mm in consecutive leads, suspect STEMI - URGENT referral needed!',
                'student': 'Measure from J point. Elevation ≥1mm (≥2mm in V2-V3) = STEMI. Depression suggests ischemia or reciprocal changes. Check for PR depression (pericarditis).',
                'resident': 'Localize STEMI: Anterior (V1-V4) = LAD, Inferior (II, III, aVF) = RCA/LCx, Lateral (I, aVL, V5-V6) = LCx. Apply RCA vs LCx algorithm. Consider Wellens syndrome.',
                'cardiologist': 'Subtle patterns: DeWinter T waves, hyperacute T waves, posterior STEMI (R>S in V1-V2). Benign early repolarization vs pericarditis vs Brugada. STEMI mimics.'
            },
            't_wave': {
                'rmp': 'T waves should point the same direction as the main heartbeat spike. Inverted T waves may indicate heart problems.',
                'student': 'T waves normally concordant with QRS. Inversion in V1-V3 normal in young/African descent. Pathological if deep, symmetric, or associated with symptoms.',
                'resident': 'Wellens syndrome: Deep T inversion V2-V4 after chest pain (critical LAD stenosis). Consider electrolyte abnormalities (hyperkalemia = peaked T, hypokalemia = flat/U waves).',
                'cardiologist': 'Cerebral T waves (SAH), juvenile T pattern, memory T waves post-pacing. Bidirectional T waves in catecholaminergic VT. T wave alternans (electrical instability).'
            },
            'qt_interval': {
                'rmp': 'If unusually long, patient at risk for dangerous heart rhythms. Check medications.',
                'student': 'Measure from Q start to T end. Use Bazett formula: QTc = QT / √RR. Normal <440ms (men), <460ms (women). Long QT increases torsades risk.',
                'resident': 'Causes of long QT: Congenital (LQTS1-3), medications (list!), electrolytes (hypoCa, hypoK, hypoMg). Short QT syndrome rare but high risk. R-on-T phenomenon.',
                'cardiologist': 'LQTS subtypes: LQT1 (exercise), LQT2 (arousal/auditory), LQT3 (rest/sleep). Acquired causes, Brugada overlap. Schwartz score for diagnosis. ICD indications.'
            }
        };

        const point = teachingPoints[component.id]?.[this.userLevel] || teachingPoints[component.id]?.['student'];
        document.getElementById('teachingPointContent').innerHTML = `<p>${point}</p>`;
    }

    nextStep() {
        if (this.currentStep < ECG_COMPONENTS.length - 1) {
            this.showStep(this.currentStep + 1);
        }
    }

    prevStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }

    finish() {
        // Award badge for completing walkthrough
        learningProgress.incrementStat('walkthroughs_completed');
        this.close();
        showToast('Walkthrough completed! Keep learning!', 'success');
    }

    close() {
        const modal = document.getElementById('ecgWalkthroughModal');
        if (modal) {
            modal.remove();
        }
        this.isActive = false;
    }
}

// ============================================
// Learning Progress - Track Progress & Achievements
// ============================================

class LearningProgress {
    constructor() {
        this.data = this.load();
        this.initializeUI();
    }

    load() {
        const saved = localStorage.getItem('ecg_learning_progress');
        if (saved) {
            return JSON.parse(saved);
        }

        return {
            topics: {
                'rhythm': { completed: [], total: TEACHING_TOPICS.rhythm.lessons.length },
                'intervals': { completed: [], total: TEACHING_TOPICS.intervals.lessons.length },
                'stemi': { completed: [], total: TEACHING_TOPICS.stemi.lessons.length },
                'vt_svt': { completed: [], total: TEACHING_TOPICS.vt_svt.lessons.length },
                'wpw': { completed: [], total: TEACHING_TOPICS.wpw.lessons.length }
            },
            stats: {
                ecgs_analyzed: 0,
                stemis_identified: 0,
                vt_svt_analyzed: 0,
                wpw_analyzed: 0,
                walkthroughs_completed: 0,
                quizzes_completed: 0,
                perfect_quizzes: 0
            },
            badges: [],
            streak: {
                current: 0,
                longest: 0,
                last_activity: null
            },
            quiz_history: []
        };
    }

    save() {
        localStorage.setItem('ecg_learning_progress', JSON.stringify(this.data));
    }

    initializeUI() {
        // Create teaching mode dashboard button in header
        const header = document.querySelector('.header-controls');
        if (header && !document.getElementById('teachingDashboardBtn')) {
            const btn = document.createElement('button');
            btn.id = 'teachingDashboardBtn';
            btn.className = 'icon-button';
            btn.title = 'Teaching Dashboard';
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                    <path d="M6 12v5c0 1 2 3 6 3s6-2 6-3v-5"/>
                </svg>
            `;
            btn.addEventListener('click', () => this.showDashboard());
            header.insertBefore(btn, header.firstChild);
        }
    }

    showDashboard() {
        const modal = document.createElement('div');
        modal.id = 'teachingDashboard';
        modal.className = 'teaching-modal';

        modal.innerHTML = `
            <div class="teaching-modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="teaching-modal-content dashboard-modal">
                <button class="teaching-modal-close" onclick="this.closest('.teaching-modal').remove()">×</button>

                <div class="dashboard-header">
                    <h2>Your Learning Journey</h2>
                    <div class="dashboard-stats">
                        <div class="stat-card">
                            <div class="stat-number">${this.data.stats.ecgs_analyzed}</div>
                            <div class="stat-label">ECGs Analyzed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${this.data.streak.current} 🔥</div>
                            <div class="stat-label">Day Streak</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${this.data.badges.length}</div>
                            <div class="stat-label">Badges Earned</div>
                        </div>
                    </div>
                </div>

                <div class="dashboard-body">
                    <div class="dashboard-section">
                        <h3>Learning Topics</h3>
                        <div class="topics-grid" id="topicsGrid"></div>
                    </div>

                    <div class="dashboard-section">
                        <h3>Achievements</h3>
                        <div class="badges-grid" id="badgesGrid"></div>
                    </div>

                    <div class="dashboard-section">
                        <h3>Recent Activity</h3>
                        <div class="activity-list" id="activityList"></div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.renderTopics();
        this.renderBadges();
        this.renderActivity();
    }

    renderTopics() {
        const container = document.getElementById('topicsGrid');
        if (!container) return;

        container.innerHTML = '';

        Object.entries(TEACHING_TOPICS).forEach(([key, topic]) => {
            const progress = this.data.topics[key];
            const completedCount = progress.completed.length;
            const percentage = (completedCount / progress.total) * 100;

            const card = document.createElement('div');
            card.className = 'topic-card';
            card.innerHTML = `
                <div class="topic-header">
                    <h4>${topic.name}</h4>
                    <span class="topic-progress-text">${completedCount}/${progress.total}</span>
                </div>
                <div class="progress-ring-container">
                    <svg class="progress-ring" width="80" height="80">
                        <circle class="progress-ring-bg" cx="40" cy="40" r="35" />
                        <circle class="progress-ring-fill" cx="40" cy="40" r="35"
                                style="stroke-dasharray: ${2 * Math.PI * 35}; stroke-dashoffset: ${2 * Math.PI * 35 * (1 - percentage / 100)};" />
                    </svg>
                    <div class="progress-ring-text">${Math.round(percentage)}%</div>
                </div>
                <div class="topic-lessons">
                    ${topic.lessons.map((lesson, idx) => `
                        <div class="lesson-item ${progress.completed.includes(idx) ? 'completed' : ''}">
                            <span class="lesson-check">${progress.completed.includes(idx) ? '✓' : '○'}</span>
                            <span class="lesson-name">${lesson}</span>
                        </div>
                    `).join('')}
                </div>
            `;

            container.appendChild(card);
        });
    }

    renderBadges() {
        const container = document.getElementById('badgesGrid');
        if (!container) return;

        container.innerHTML = '';

        Object.entries(BADGES).forEach(([key, badge]) => {
            const earned = this.data.badges.includes(key);
            const card = document.createElement('div');
            card.className = `badge-card ${earned ? 'earned' : 'locked'}`;

            card.innerHTML = `
                <div class="badge-icon ${earned ? 'pulse' : ''}">${badge.icon}</div>
                <div class="badge-name">${badge.name}</div>
                <div class="badge-description">${badge.description}</div>
                ${!earned ? `<div class="badge-requirement">Required: ${badge.requirement}</div>` : ''}
            `;

            if (earned) {
                card.addEventListener('click', () => this.celebrateBadge(badge));
            }

            container.appendChild(card);
        });
    }

    renderActivity() {
        const container = document.getElementById('activityList');
        if (!container) return;

        const recentActivities = [
            { text: `Analyzed ${this.data.stats.ecgs_analyzed} ECGs`, icon: '📊' },
            { text: `Completed ${this.data.stats.walkthroughs_completed} walkthroughs`, icon: '🎓' },
            { text: `Took ${this.data.stats.quizzes_completed} quizzes`, icon: '📝' },
            { text: `${this.data.streak.longest} day longest streak`, icon: '🏆' }
        ];

        container.innerHTML = recentActivities.map(activity => `
            <div class="activity-item">
                <span class="activity-icon">${activity.icon}</span>
                <span class="activity-text">${activity.text}</span>
            </div>
        `).join('');
    }

    incrementStat(stat, amount = 1) {
        this.data.stats[stat] = (this.data.stats[stat] || 0) + amount;
        this.updateStreak();
        this.checkBadges();
        this.save();
    }

    completeLesson(topic, lessonIndex) {
        if (!this.data.topics[topic].completed.includes(lessonIndex)) {
            this.data.topics[topic].completed.push(lessonIndex);
            this.checkBadges();
            this.save();
        }
    }

    updateStreak() {
        const today = new Date().toDateString();
        const lastActivity = this.data.streak.last_activity;

        if (lastActivity !== today) {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);

            if (lastActivity === yesterday.toDateString()) {
                this.data.streak.current++;
            } else if (lastActivity !== today) {
                this.data.streak.current = 1;
            }

            this.data.streak.last_activity = today;
            this.data.streak.longest = Math.max(this.data.streak.current, this.data.streak.longest);

            this.save();
        }
    }

    checkBadges() {
        const newBadges = [];

        // Check each badge requirement
        if (this.data.stats.ecgs_analyzed >= 1 && !this.data.badges.includes('first_analysis')) {
            newBadges.push('first_analysis');
        }

        if (this.data.stats.stemis_identified >= 1 && !this.data.badges.includes('stemi_spotted')) {
            newBadges.push('stemi_spotted');
        }

        if (this.data.streak.current >= 7 && !this.data.badges.includes('week_streak')) {
            newBadges.push('week_streak');
        }

        if (this.data.stats.vt_svt_analyzed >= 10 && !this.data.badges.includes('vt_master')) {
            newBadges.push('vt_master');
        }

        if (this.data.stats.ecgs_analyzed >= 100 && !this.data.badges.includes('hundred_ecgs')) {
            newBadges.push('hundred_ecgs');
        }

        if (this.data.stats.perfect_quizzes >= 1 && !this.data.badges.includes('perfect_quiz')) {
            newBadges.push('perfect_quiz');
        }

        if (this.data.stats.wpw_analyzed >= 15 && !this.data.badges.includes('pathway_expert')) {
            newBadges.push('pathway_expert');
        }

        // Check if all topics completed
        const allCompleted = Object.values(this.data.topics).every(
            topic => topic.completed.length === topic.total
        );
        if (allCompleted && !this.data.badges.includes('teaching_advocate')) {
            newBadges.push('teaching_advocate');
        }

        // Award new badges with celebration
        newBadges.forEach(badgeKey => {
            this.data.badges.push(badgeKey);
            this.celebrateBadge(BADGES[badgeKey]);
        });

        if (newBadges.length > 0) {
            this.save();
        }
    }

    celebrateBadge(badge) {
        // Create confetti effect
        createConfetti();

        // Show badge modal
        const modal = document.createElement('div');
        modal.className = 'badge-celebration-modal';
        modal.innerHTML = `
            <div class="badge-celebration-content">
                <div class="badge-celebration-icon">${badge.icon}</div>
                <h2 class="badge-celebration-title">Badge Unlocked!</h2>
                <h3 class="badge-celebration-name">${badge.name}</h3>
                <p class="badge-celebration-description">${badge.description}</p>
                <button class="btn btn-primary" onclick="this.closest('.badge-celebration-modal').remove()">
                    Awesome! ✓
                </button>
            </div>
        `;
        document.body.appendChild(modal);

        setTimeout(() => modal.remove(), 5000);
    }
}

// ============================================
// ECG Quiz - Interactive Quiz Mode with Spaced Repetition
// ============================================

class ECGQuiz {
    constructor() {
        this.questions = [];
        this.currentQuestion = 0;
        this.score = 0;
        this.answers = [];
    }

    start(difficulty = 'beginner') {
        this.questions = this.generateQuestions(difficulty);
        this.currentQuestion = 0;
        this.score = 0;
        this.answers = [];
        this.render();
        this.showQuestion(0);
    }

    generateQuestions(difficulty) {
        // In production, these would come from a database
        const questionBank = {
            'beginner': [
                {
                    ecg_image: '/path/to/ecg1.jpg',
                    question: 'What is the heart rate in this ECG?',
                    options: ['60 bpm', '75 bpm', '90 bpm', '105 bpm'],
                    correct: 1,
                    explanation: 'Count the number of large squares between R waves and use the 300 rule.',
                    topic: 'rhythm'
                },
                {
                    ecg_image: '/path/to/ecg2.jpg',
                    question: 'What is the rhythm shown?',
                    options: ['Normal Sinus Rhythm', 'Atrial Fibrillation', 'Atrial Flutter', 'Ventricular Tachycardia'],
                    correct: 0,
                    explanation: 'Regular rhythm with P waves before each QRS indicates normal sinus rhythm.',
                    topic: 'rhythm'
                }
            ],
            'intermediate': [
                {
                    ecg_image: '/path/to/ecg3.jpg',
                    question: 'Which leads show ST elevation?',
                    options: ['V1-V4', 'II, III, aVF', 'I, aVL, V5-V6', 'No ST elevation'],
                    correct: 0,
                    explanation: 'ST elevation in V1-V4 indicates anterior STEMI from LAD occlusion.',
                    topic: 'stemi'
                }
            ],
            'advanced': [
                {
                    ecg_image: '/path/to/ecg4.jpg',
                    question: 'Using the Brugada algorithm, is this VT or SVT?',
                    options: ['VT', 'SVT with aberrancy', 'Cannot determine', 'AVRT with pre-excitation'],
                    correct: 0,
                    explanation: 'Absence of RS complex in all precordial leads suggests VT.',
                    topic: 'vt_svt'
                }
            ]
        };

        return questionBank[difficulty] || questionBank['beginner'];
    }

    render() {
        const container = document.createElement('div');
        container.id = 'ecgQuizModal';
        container.className = 'teaching-modal';

        container.innerHTML = `
            <div class="teaching-modal-overlay"></div>
            <div class="teaching-modal-content quiz-modal">
                <button class="teaching-modal-close" onclick="ecgQuiz.close()">×</button>

                <div class="quiz-header">
                    <h2>ECG Quiz</h2>
                    <div class="quiz-progress">
                        <span id="quizProgressText">Question 1 of ${this.questions.length}</span>
                        <div class="quiz-progress-bar">
                            <div class="quiz-progress-fill" id="quizProgressFill"></div>
                        </div>
                    </div>
                    <div class="quiz-score" id="quizScore">Score: 0/${this.questions.length}</div>
                </div>

                <div class="quiz-body">
                    <div class="quiz-image-container" id="quizImageContainer">
                        <img id="quizEcgImage" alt="ECG for quiz">
                    </div>

                    <div class="quiz-question">
                        <h3 id="quizQuestionText"></h3>
                        <div class="quiz-options" id="quizOptions"></div>
                    </div>

                    <div class="quiz-explanation hidden" id="quizExplanation">
                        <div class="explanation-header">
                            <span class="explanation-icon" id="explanationIcon"></span>
                            <span class="explanation-title" id="explanationTitle"></span>
                        </div>
                        <p id="explanationText"></p>
                    </div>
                </div>

                <div class="quiz-footer">
                    <button class="btn btn-secondary" id="quizSkipBtn" onclick="ecgQuiz.skip()">
                        Skip
                    </button>
                    <button class="btn btn-primary hidden" id="quizNextBtn" onclick="ecgQuiz.next()">
                        Next Question →
                    </button>
                    <button class="btn btn-success hidden" id="quizFinishBtn" onclick="ecgQuiz.finish()">
                        See Results
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(container);
    }

    showQuestion(index) {
        if (index >= this.questions.length) {
            this.showResults();
            return;
        }

        const question = this.questions[index];
        this.currentQuestion = index;

        // Update progress
        const progress = ((index + 1) / this.questions.length) * 100;
        document.getElementById('quizProgressFill').style.width = `${progress}%`;
        document.getElementById('quizProgressText').textContent = `Question ${index + 1} of ${this.questions.length}`;

        // Show question
        document.getElementById('quizEcgImage').src = question.ecg_image;
        document.getElementById('quizQuestionText').textContent = question.question;

        // Render options
        const optionsContainer = document.getElementById('quizOptions');
        optionsContainer.innerHTML = '';

        question.options.forEach((option, idx) => {
            const optionBtn = document.createElement('button');
            optionBtn.className = 'quiz-option';
            optionBtn.textContent = option;
            optionBtn.onclick = () => this.selectAnswer(idx);
            optionsContainer.appendChild(optionBtn);
        });

        // Reset explanation
        document.getElementById('quizExplanation').classList.add('hidden');
        document.getElementById('quizNextBtn').classList.add('hidden');
        document.getElementById('quizFinishBtn').classList.add('hidden');
        document.getElementById('quizSkipBtn').classList.remove('hidden');
    }

    selectAnswer(answerIndex) {
        const question = this.questions[this.currentQuestion];
        const isCorrect = answerIndex === question.correct;

        // Record answer
        this.answers.push({
            question: this.currentQuestion,
            selected: answerIndex,
            correct: question.correct,
            isCorrect: isCorrect
        });

        if (isCorrect) {
            this.score++;
            document.getElementById('quizScore').textContent = `Score: ${this.score}/${this.questions.length}`;
        }

        // Show feedback
        this.showFeedback(isCorrect, question);

        // Update UI
        const options = document.querySelectorAll('.quiz-option');
        options.forEach((opt, idx) => {
            opt.disabled = true;
            if (idx === question.correct) {
                opt.classList.add('correct');
            } else if (idx === answerIndex && !isCorrect) {
                opt.classList.add('incorrect');
            }
        });

        // Show next/finish button
        document.getElementById('quizSkipBtn').classList.add('hidden');
        if (this.currentQuestion < this.questions.length - 1) {
            document.getElementById('quizNextBtn').classList.remove('hidden');
        } else {
            document.getElementById('quizFinishBtn').classList.remove('hidden');
        }
    }

    showFeedback(isCorrect, question) {
        const explanation = document.getElementById('quizExplanation');
        const icon = document.getElementById('explanationIcon');
        const title = document.getElementById('explanationTitle');
        const text = document.getElementById('explanationText');

        if (isCorrect) {
            icon.textContent = '✓';
            icon.className = 'explanation-icon correct';
            title.textContent = 'Correct!';
        } else {
            icon.textContent = '✗';
            icon.className = 'explanation-icon incorrect';
            title.textContent = 'Not quite right';
        }

        text.textContent = question.explanation;
        explanation.classList.remove('hidden');

        // Mark topic for spaced repetition if incorrect
        if (!isCorrect) {
            // In production, this would update spaced repetition algorithm
            console.log(`Mark ${question.topic} for review`);
        }
    }

    skip() {
        this.next();
    }

    next() {
        this.showQuestion(this.currentQuestion + 1);
    }

    finish() {
        this.showResults();
    }

    showResults() {
        const percentage = (this.score / this.questions.length) * 100;
        const isPerfect = percentage === 100;

        // Update learning progress
        learningProgress.incrementStat('quizzes_completed');
        if (isPerfect) {
            learningProgress.incrementStat('perfect_quizzes');
        }

        const modal = document.getElementById('ecgQuizModal');
        modal.querySelector('.teaching-modal-content').innerHTML = `
            <button class="teaching-modal-close" onclick="ecgQuiz.close()">×</button>

            <div class="quiz-results">
                <div class="results-icon ${isPerfect ? 'perfect' : ''}">${isPerfect ? '🏆' : '📊'}</div>
                <h2>${isPerfect ? 'Perfect Score!' : 'Quiz Complete'}</h2>

                <div class="results-score">
                    <div class="results-score-circle">
                        <svg class="results-progress-ring" width="200" height="200">
                            <circle class="progress-ring-bg" cx="100" cy="100" r="90" />
                            <circle class="progress-ring-fill" cx="100" cy="100" r="90"
                                    style="stroke-dasharray: ${2 * Math.PI * 90}; stroke-dashoffset: ${2 * Math.PI * 90 * (1 - percentage / 100)};" />
                        </svg>
                        <div class="results-score-text">
                            <div class="results-percentage">${Math.round(percentage)}%</div>
                            <div class="results-fraction">${this.score}/${this.questions.length}</div>
                        </div>
                    </div>
                </div>

                <div class="results-breakdown">
                    <h3>Your Answers</h3>
                    ${this.answers.map((answer, idx) => `
                        <div class="result-item ${answer.isCorrect ? 'correct' : 'incorrect'}">
                            <span class="result-number">${idx + 1}</span>
                            <span class="result-status">${answer.isCorrect ? '✓' : '✗'}</span>
                            <span class="result-question">${this.questions[idx].question}</span>
                        </div>
                    `).join('')}
                </div>

                <div class="results-actions">
                    <button class="btn btn-secondary" onclick="ecgQuiz.close()">Close</button>
                    <button class="btn btn-primary" onclick="ecgQuiz.retake()">Retake Quiz</button>
                </div>
            </div>
        `;

        if (isPerfect) {
            createConfetti();
        }
    }

    retake() {
        this.start();
    }

    close() {
        const modal = document.getElementById('ecgQuizModal');
        if (modal) {
            modal.remove();
        }
    }
}

// ============================================
// Teaching Points System
// ============================================

class TeachingPoints {
    static show(analysis, userLevel) {
        const points = this.generate(analysis, userLevel);

        if (!points || points.length === 0) return;

        // Add teaching points to the analysis results
        const findingsCard = document.querySelector('.findings-card');
        if (!findingsCard) return;

        const teachingSection = document.createElement('div');
        teachingSection.className = 'teaching-points-section';
        teachingSection.innerHTML = `
            <h3>💡 Teaching Points</h3>
            <div class="teaching-points-list">
                ${points.map(point => `
                    <div class="teaching-point-card ${point.type}">
                        <div class="teaching-point-icon">${this.getIcon(point.type)}</div>
                        <div class="teaching-point-content">
                            <strong>${point.title}</strong>
                            <p>${point.content}</p>
                            ${point.learn_more ? `<a href="#" class="learn-more-link" onclick="teachingPoints.showLearnMore('${point.topic}')">Learn more →</a>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        findingsCard.insertAdjacentElement('afterend', teachingSection);
    }

    static generate(analysis, userLevel) {
        const points = [];

        // Did you notice?
        if (analysis.findings && analysis.findings.length > 0) {
            const criticalFindings = analysis.findings.filter(f => f.severity === 'critical');
            if (criticalFindings.length > 0) {
                points.push({
                    type: 'notice',
                    title: 'Did you notice?',
                    content: `This ECG shows ${criticalFindings.length} critical finding(s) that require immediate attention. Always check for STEMI and life-threatening arrhythmias first.`,
                    topic: 'critical_interpretation'
                });
            }
        }

        // Pro tip
        if (analysis.algorithm_results && analysis.algorithm_results.length > 0) {
            points.push({
                type: 'tip',
                title: 'Pro Tip',
                content: 'When analyzing wide complex tachycardia, always run multiple algorithms (Brugada, Vereckei, Basel) for highest accuracy. Concordance between algorithms increases diagnostic confidence.',
                topic: 'vt_svt',
                learn_more: true
            });
        }

        // Common mistake
        if (analysis.measurements && analysis.measurements.qtc_ms > 440) {
            points.push({
                type: 'mistake',
                title: 'Common Mistake',
                content: 'Don\'t forget to check the QTc, not just the QT interval. Long QT can be missed if you only look at the uncorrected value, especially in bradycardia.',
                topic: 'intervals'
            });
        }

        // Learn more
        if (analysis.is_urgent) {
            points.push({
                type: 'learn',
                title: 'Learn More',
                content: 'STEMI localization is crucial for predicting complications and choosing the right intervention. Understanding coronary anatomy helps you become a better clinician.',
                topic: 'stemi',
                learn_more: true
            });
        }

        return points;
    }

    static getIcon(type) {
        const icons = {
            'notice': '👀',
            'tip': '💡',
            'mistake': '⚠️',
            'learn': '📚'
        };
        return icons[type] || '💡';
    }

    static showLearnMore(topic) {
        // In production, this would load detailed content
        alert(`Opening ${topic} learning module...`);
    }
}

// ============================================
// Confetti Effect for Celebrations
// ============================================

function createConfetti() {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'];
    const confettiCount = 50;

    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = Math.random() * 3 + 's';
        confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';

        document.body.appendChild(confetti);

        setTimeout(() => confetti.remove(), 5000);
    }
}

// ============================================
// Initialize Teaching Module
// ============================================

// Global instances
let ecgWalkthrough = null;
let learningProgress = null;
let ecgQuiz = null;
const teachingPoints = TeachingPoints;

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTeachingMode);
} else {
    initializeTeachingMode();
}

function initializeTeachingMode() {
    ecgWalkthrough = new ECGWalkthrough();
    learningProgress = new LearningProgress();
    ecgQuiz = new ECGQuiz();

    // Add quiz button to header
    addQuizButton();

    // Hook into analysis completion to show teaching points
    const originalDisplayAnalysis = window.displayAnalysisResults;
    if (originalDisplayAnalysis) {
        window.displayAnalysisResults = function(data) {
            originalDisplayAnalysis.call(this, data);

            // Update learning stats
            learningProgress.incrementStat('ecgs_analyzed');

            // Check for STEMI
            if (data.is_urgent || (data.findings && data.findings.some(f => f.finding.toLowerCase().includes('stemi')))) {
                learningProgress.incrementStat('stemis_identified');
            }

            // Check for VT/SVT
            if (data.algorithm_results && data.algorithm_results.some(a => a.name.includes('VT') || a.name.includes('SVT'))) {
                learningProgress.incrementStat('vt_svt_analyzed');
            }

            // Check for WPW
            if (data.findings && data.findings.some(f => f.finding.toLowerCase().includes('wpw') || f.finding.toLowerCase().includes('pre-excitation'))) {
                learningProgress.incrementStat('wpw_analyzed');
            }

            // Show teaching points if teaching mode enabled
            if (state.teachingMode) {
                teachingPoints.show(data, state.userLevel);
            }

            // Add walkthrough button
            addWalkthroughButton();
        };
    }
}

function addQuizButton() {
    const header = document.querySelector('.header-controls');
    if (header && !document.getElementById('quizModeBtn')) {
        const btn = document.createElement('button');
        btn.id = 'quizModeBtn';
        btn.className = 'icon-button';
        btn.title = 'Take a Quiz';
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11l3 3L22 4"/>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
            </svg>
        `;
        btn.addEventListener('click', () => {
            const difficulty = state.userLevel === 'rmp' ? 'beginner' :
                             state.userLevel === 'student' ? 'beginner' :
                             state.userLevel === 'resident' ? 'intermediate' : 'advanced';
            ecgQuiz.start(difficulty);
        });
        header.insertBefore(btn, document.getElementById('teachingDashboardBtn'));
    }
}

function addWalkthroughButton() {
    const summaryCard = document.querySelector('.summary-card');
    if (summaryCard && !document.getElementById('startWalkthroughBtn') && state.uploadedImage) {
        const btn = document.createElement('button');
        btn.id = 'startWalkthroughBtn';
        btn.className = 'btn btn-secondary';
        btn.style.marginTop = '1rem';
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px; margin-right: 8px;">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
            </svg>
            Start Interactive Walkthrough
        `;
        btn.addEventListener('click', () => {
            ecgWalkthrough.start(state.uploadedImage, state.userLevel);
        });
        summaryCard.appendChild(btn);
    }
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ECGWalkthrough,
        LearningProgress,
        ECGQuiz,
        TeachingPoints
    };
}
