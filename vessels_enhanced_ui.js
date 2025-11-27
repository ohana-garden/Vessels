// VESSELS ENHANCED UI - JavaScript
// Comprehensive UX improvements with error handling, loading states, and user feedback

// Configuration
const API_BASE = 'http://localhost:5000';
const SESSION_ID = 'session_' + Date.now();
const ONBOARDING_KEY = 'vessels_onboarding_completed';
const LANG_KEY = 'vessels_language';

// State Management
const state = {
    isListening: false,
    currentEmotion: 'neutral',
    speechRecognition: null,
    activeAgents: [],
    currentLanguage: localStorage.getItem(LANG_KEY) || 'en',
    sessionContext: [],
    agentPanelOpen: false,
    helpOpen: false,
    onboardingStep: 0,
    isProcessing: false
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeSpeechRecognition();
    initializeKeyboardShortcuts();
    initializeAccessibility();
    checkOnboarding();
    checkBackendConnection();

    // Event listeners
    document.getElementById('agentPanelToggle').addEventListener('click', toggleAgentPanel);
    document.getElementById('helpToggle').addEventListener('click', toggleHelp);
    document.getElementById('langToggle').addEventListener('click', toggleLanguage);

    // Close overlays on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllOverlays();
        }
    });

    console.log('Vessels Enhanced UI initialized');
});

// ============================================================================
// SPEECH RECOGNITION
// ============================================================================

function initializeSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        showNotification('Speech recognition not supported', 'error');
        return;
    }

    state.speechRecognition = new SpeechRecognition();
    state.speechRecognition.continuous = true;
    state.speechRecognition.interimResults = true;
    state.speechRecognition.lang = state.currentLanguage === 'haw' ? 'en-US' : 'en-US'; // Hawaiian TTS would need special handling

    state.speechRecognition.onstart = () => {
        state.isListening = true;
        updateVoiceUI('listening');
        setVoiceStatusText('Listening...');
    };

    state.speechRecognition.onend = () => {
        state.isListening = false;
        updateVoiceUI('idle');
        setVoiceStatusText('Click to speak');
    };

    state.speechRecognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        updateVoiceUI('error');

        if (event.error === 'no-speech') {
            setVoiceStatusText("Didn't catch that. Try again!");
        } else if (event.error === 'audio-capture') {
            showNotification('Microphone not accessible. Please check permissions.', 'error');
            setVoiceStatusText('Microphone error');
        } else if (event.error === 'not-allowed') {
            showNotification('Microphone permission denied. Please allow access.', 'error');
            setVoiceStatusText('Permission denied');
        } else {
            setVoiceStatusText('Error: ' + event.error);
        }

        // Reset after error
        setTimeout(() => {
            if (!state.isListening) {
                updateVoiceUI('idle');
                setVoiceStatusText('Click to speak');
            }
        }, 3000);
    };

    state.speechRecognition.onresult = (event) => {
        const last = event.results.length - 1;
        const transcript = event.results[last][0].transcript;
        const isFinal = event.results[last].isFinal;

        // Show interim results
        if (!isFinal) {
            showVoiceTranscript(transcript);
        } else {
            hideVoiceTranscript();
            processVoiceInput(transcript);
        }
    };
}

function toggleVoice() {
    if (state.isListening) {
        stopListening();
    } else {
        startListening();
    }
}

function startListening() {
    if (state.speechRecognition && !state.isListening) {
        try {
            state.speechRecognition.start();
        } catch (e) {
            console.log('Speech recognition already started');
        }
    }
}

function stopListening() {
    if (state.speechRecognition && state.isListening) {
        state.speechRecognition.stop();
    }
}

function updateVoiceUI(status) {
    const button = document.getElementById('voiceButton');
    button.className = 'voice-button ' + status;
}

function setVoiceStatusText(text) {
    document.getElementById('voiceStatusText').textContent = text;
}

function showVoiceTranscript(text) {
    const transcript = document.getElementById('voiceTranscript');
    transcript.textContent = text;
    transcript.classList.remove('hidden');
}

function hideVoiceTranscript() {
    const transcript = document.getElementById('voiceTranscript');
    transcript.classList.add('hidden');
}

// ============================================================================
// VOICE INPUT PROCESSING
// ============================================================================

async function processVoiceInput(text) {
    // Clear transcript
    hideVoiceTranscript();

    // Show user subtitle
    addSubtitle(text, 'user', 'You');

    // Add to session context
    state.sessionContext.push({ type: 'user', text: text, timestamp: Date.now() });

    // Detect emotion
    const emotion = detectEmotion(text);
    state.currentEmotion = emotion;

    // Show loading
    showLoading('Processing your request...');

    try {
        // Send to backend
        const response = await fetch(`${API_BASE}/api/voice/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                session_id: SESSION_ID,
                emotion: emotion,
                language: state.currentLanguage
            })
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Hide loading
        hideLoading();

        // Update active agents
        if (data.agents) {
            updateAgentPanel(data.agents);
        }

        // Render content
        if (data.content_type && data.content_data) {
            renderContent(data.content_type, data.content_data);
        }

        // Show subtitles with delays
        if (data.subtitles) {
            data.subtitles.forEach(subtitle => {
                setTimeout(() => {
                    addSubtitle(subtitle.text, subtitle.type, subtitle.speaker);
                }, subtitle.delay || 0);
            });
        }

        // Handle gist artifact creation
        if (data.gist && window.VesselsArtifacts) {
            setTimeout(() => {
                window.VesselsArtifacts.create({
                    type: data.gist.type,
                    content: data.gist.content,
                    context: data.gist.context,
                    source: 'server'
                });
            }, 800); // Slight delay for dramatic effect
        } else if (window.VesselsArtifacts) {
            // Client-side gist detection as fallback
            const responseText = JSON.stringify(data.content_data || {});
            window.VesselsArtifacts.processForGists(responseText, 'assistant');
        }

        // Add to session context
        state.sessionContext.push({
            type: 'assistant',
            content_type: data.content_type,
            timestamp: Date.now()
        });

        // Show success notification
        showNotification('Request processed successfully', 'success');

    } catch (error) {
        console.error('Backend communication error:', error);
        hideLoading();

        // Show error to user
        showNotification(
            `I couldn't connect to the server. ${error.message}. Trying local processing...`,
            'error'
        );

        // Fallback to local processing
        processLocally(text);
    }
}

function detectEmotion(text) {
    const lower = text.toLowerCase();

    if (lower.includes('confused') || lower.includes("don't understand")) {
        return 'uncertain';
    } else if (lower.includes('frustrated') || lower.includes('nothing works')) {
        return 'frustrated';
    } else if (lower.includes('great') || lower.includes('awesome') || lower.includes('mahalo')) {
        return 'excited';
    } else if (lower.includes('help') || lower.includes('please')) {
        return 'seeking_help';
    } else {
        return 'neutral';
    }
}

// ============================================================================
// LOADING STATES
// ============================================================================

function showLoading(message, agents = []) {
    const overlay = document.getElementById('loadingOverlay');
    const text = document.getElementById('loadingText');
    const agentsContainer = document.getElementById('loadingAgents');

    text.textContent = message;

    // Show agents that are working
    if (agents.length > 0) {
        agentsContainer.innerHTML = agents.map(agent => `
            <div class="loading-agent-item">
                <div class="loading-agent-icon"></div>
                <span>${agent.name} is ${agent.activity || 'working'}...</span>
            </div>
        `).join('');
    } else {
        agentsContainer.innerHTML = '';
    }

    overlay.classList.add('active');
    state.isProcessing = true;
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('active');
    state.isProcessing = false;
}

function updateLoadingMessage(message) {
    document.getElementById('loadingText').textContent = message;
}

// ============================================================================
// AGENT PANEL
// ============================================================================

function updateAgentPanel(agents) {
    state.activeAgents = agents || [];

    const agentList = document.getElementById('agentList');
    const collabFlow = document.getElementById('collabFlow');

    if (agents.length === 0) {
        agentList.innerHTML = '<p style="opacity: 0.6; font-size: 14px;">No agents currently active</p>';
        collabFlow.innerHTML = '<p style="opacity: 0.6; font-size: 12px;">Agents will coordinate here</p>';
        return;
    }

    // Update agent list
    agentList.innerHTML = agents.map(agent => `
        <div class="agent-item">
            <div class="agent-name">${agent.name}</div>
            <div class="agent-status">Type: ${agent.type || 'specialist'}</div>
            <div class="agent-activity">🟢 Active</div>
        </div>
    `).join('');

    // Update collaboration flow
    collabFlow.innerHTML = `
        <div class="collab-step">
            <span>You</span>
            <span class="collab-arrow">→</span>
            <span>${agents[0].name}</span>
        </div>
        ${agents.length > 1 ? `
            <div class="collab-step">
                <span>${agents[0].name}</span>
                <span class="collab-arrow">↓</span>
                <span>${agents[1].name}</span>
            </div>
        ` : ''}
        ${agents.length > 2 ? `
            <div class="collab-step">
                <span>Team collaboration</span>
                <span class="collab-arrow">→</span>
                <span>Results</span>
            </div>
        ` : ''}
    `;

    // Auto-open agent panel on first agents
    if (!state.agentPanelOpen && agents.length > 0) {
        setTimeout(() => {
            showNotification('Agents are now working on your request!', 'info');
        }, 500);
    }
}

function toggleAgentPanel() {
    state.agentPanelOpen = !state.agentPanelOpen;
    const panel = document.getElementById('agentPanel');

    if (state.agentPanelOpen) {
        panel.classList.add('open');
    } else {
        panel.classList.remove('open');
    }
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notifications');

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-header">
            <span class="notification-title">${getNotificationTitle(type)}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="notification-body">${message}</div>
    `;

    container.appendChild(notification);

    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    // Announce to screen readers
    announceToScreenReader(message);
}

function getNotificationTitle(type) {
    const titles = {
        'success': '✓ Success',
        'error': '⚠ Error',
        'warning': '⚠ Warning',
        'info': 'ℹ Info'
    };
    return titles[type] || 'Notification';
}

// ============================================================================
// CONTENT RENDERING
// ============================================================================

function renderContent(type, data) {
    const contentArea = document.getElementById('contentArea');

    switch(type) {
        case 'grant_cards':
            renderGrantCards(contentArea, data);
            break;
        case 'care_protocol':
            renderCareProtocol(contentArea, data);
            break;
        case 'dashboard':
            renderDashboard(contentArea, data);
            break;
        default:
            console.log('Unknown content type:', type);
            break;
    }
}

function renderGrantCards(container, data) {
    const grants = data.grants || [];
    container.innerHTML = `
        <div class="grant-cards">
            ${grants.map((grant, i) => `
                <div class="grant-card">
                    <div class="grant-title">${escapeHtml(grant.title)}</div>
                    <div class="grant-amount">${escapeHtml(grant.amount)}</div>
                    <div class="grant-description">${escapeHtml(grant.description)}</div>

                    ${grant.match_score ? `
                        <div class="grant-match-score">
                            <span style="font-size: 12px;">Match:</span>
                            <div class="match-bar">
                                <div class="match-fill" style="width: ${grant.match_score}%"></div>
                            </div>
                            <span style="font-size: 12px; font-weight: 600;">${grant.match_score}%</span>
                        </div>
                    ` : ''}

                    <div class="grant-actions">
                        <button class="action-button primary" onclick="applyToGrant(${i})">
                            Apply Now
                        </button>
                        <button class="action-button" onclick="learnMore(${i})">
                            Learn More
                        </button>
                    </div>

                    <div class="feedback-bar">
                        <button class="feedback-button" onclick="giveFeedback(${i}, 'helpful')" title="Helpful">
                            👍 Helpful
                        </button>
                        <button class="feedback-button" onclick="giveFeedback(${i}, 'not_relevant')" title="Not relevant">
                            👎 Not relevant
                        </button>
                        <button class="feedback-button" onclick="giveFeedback(${i}, 'missing_info')" title="Missing info">
                            💡 Missing info
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderCareProtocol(container, data) {
    container.innerHTML = `
        <div class="care-protocol">
            <div class="protocol-title">${escapeHtml(data.title)}</div>
            ${data.steps.map((step, i) => `
                <div class="protocol-step">
                    <strong>${escapeHtml(step.title)}:</strong> ${escapeHtml(step.description)}
                </div>
            `).join('')}

            <div class="feedback-bar" style="margin-top: var(--spacing-xl);">
                <button class="feedback-button" onclick="giveFeedback('protocol', 'helpful')">
                    👍 Helpful
                </button>
                <button class="feedback-button" onclick="giveFeedback('protocol', 'unclear')">
                    ❓ Unclear
                </button>
                <button class="feedback-button" onclick="giveFeedback('protocol', 'suggest_changes')">
                    💡 Suggest changes
                </button>
            </div>
        </div>
    `;
}

function renderDashboard(container, data) {
    container.innerHTML = `
        <div class="impact-dashboard">
            <h2 class="dashboard-title">Community Impact This Week</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">🕐</div>
                    <div class="stat-value">${data.kala || 450}</div>
                    <div class="stat-label">Kala earned</div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">🍱</div>
                    <div class="stat-value">${data.meals || 32}</div>
                    <div class="stat-label">Meals coordinated</div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">💰</div>
                    <div class="stat-value">$${(data.grants_found || 125000).toLocaleString()}</div>
                    <div class="stat-label">Grants found</div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">👥</div>
                    <div class="stat-value">${data.elders || 18}</div>
                    <div class="stat-label">Elders supported</div>
                </div>
            </div>
        </div>
    `;
}

// ============================================================================
// SUBTITLES
// ============================================================================

function addSubtitle(text, type, speaker) {
    const subtitles = document.getElementById('subtitles');

    // Clear old subtitles (keep last 2)
    while (subtitles.children.length > 2) {
        subtitles.removeChild(subtitles.firstChild);
    }

    const subtitle = document.createElement('div');
    subtitle.className = `subtitle ${type}`;

    if (speaker) {
        subtitle.innerHTML = `
            <div class="speaker-label">${escapeHtml(speaker)}</div>
            ${escapeHtml(text)}
        `;
    } else {
        subtitle.textContent = text;
    }

    subtitles.appendChild(subtitle);

    // Auto-remove after 10 seconds
    setTimeout(() => {
        subtitle.style.opacity = '0';
        setTimeout(() => subtitle.remove(), 300);
    }, 10000);
}

// ============================================================================
// ONBOARDING
// ============================================================================

function checkOnboarding() {
    const completed = localStorage.getItem(ONBOARDING_KEY);

    if (!completed) {
        setTimeout(() => {
            showOnboarding();
        }, 1000);
    }
}

function showOnboarding() {
    document.getElementById('onboardingOverlay').classList.add('active');
    state.onboardingStep = 1;
}

function nextOnboardingStep() {
    const currentStep = document.getElementById(`step${state.onboardingStep}`);
    currentStep.classList.remove('active');

    state.onboardingStep++;

    const nextStep = document.getElementById(`step${state.onboardingStep}`);
    if (nextStep) {
        nextStep.classList.add('active');
    }
}

function prevOnboardingStep() {
    const currentStep = document.getElementById(`step${state.onboardingStep}`);
    currentStep.classList.remove('active');

    state.onboardingStep--;

    const prevStep = document.getElementById(`step${state.onboardingStep}`);
    if (prevStep) {
        prevStep.classList.add('active');
    }
}

function skipOnboarding() {
    finishOnboarding();
}

function finishOnboarding() {
    document.getElementById('onboardingOverlay').classList.remove('active');
    localStorage.setItem(ONBOARDING_KEY, 'true');
    showNotification('Welcome to Vessels! Click the microphone to get started.', 'success');
}

// ============================================================================
// HELP SYSTEM
// ============================================================================

function toggleHelp() {
    state.helpOpen = !state.helpOpen;
    const help = document.getElementById('helpOverlay');

    if (state.helpOpen) {
        help.classList.add('open');
    } else {
        help.classList.remove('open');
    }
}

// ============================================================================
// LANGUAGE TOGGLE
// ============================================================================

function toggleLanguage() {
    state.currentLanguage = state.currentLanguage === 'en' ? 'haw' : 'en';
    localStorage.setItem(LANG_KEY, state.currentLanguage);

    const toggle = document.getElementById('langToggle');
    toggle.textContent = state.currentLanguage === 'haw' ? 'English' : 'ʻŌlelo Hawaiʻi';

    showNotification(
        state.currentLanguage === 'haw'
            ? 'Aloha! E ʻoluʻolu e ʻōlelo Hawaiʻi'
            : 'Switched to English',
        'info'
    );
}

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================

function initializeKeyboardShortcuts() {
    document.addEventListener('keypress', (e) => {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        const shortcuts = {
            '1': "Find grants for elder care",
            '2': "Show me the elder care protocol",
            '3': "What food is available?",
            '4': "Show delivery routes",
            '5': "When can volunteers help?",
            'h': () => toggleHelp(),
            'a': () => toggleAgentPanel(),
            'd': () => showDashboard(),
            'g': () => window.toggleArtifactGallery && toggleArtifactGallery()
        };

        const action = shortcuts[e.key];
        if (typeof action === 'string') {
            processVoiceInput(action);
        } else if (typeof action === 'function') {
            action();
        }
    });
}

// ============================================================================
// ACCESSIBILITY
// ============================================================================

function initializeAccessibility() {
    // Focus management for modals
    const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

    // Trap focus in onboarding
    const onboarding = document.getElementById('onboardingOverlay');
    onboarding.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' && onboarding.classList.contains('active')) {
            const focusable = onboarding.querySelectorAll(focusableElements);
            const firstFocusable = focusable[0];
            const lastFocusable = focusable[focusable.length - 1];

            if (e.shiftKey && document.activeElement === firstFocusable) {
                lastFocusable.focus();
                e.preventDefault();
            } else if (!e.shiftKey && document.activeElement === lastFocusable) {
                firstFocusable.focus();
                e.preventDefault();
            }
        }
    });
}

function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

// ============================================================================
// FEEDBACK SYSTEM
// ============================================================================

function giveFeedback(itemId, feedbackType) {
    console.log('Feedback:', itemId, feedbackType);

    // Send to backend
    fetch(`${API_BASE}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            item_id: itemId,
            feedback_type: feedbackType,
            session_id: SESSION_ID,
            timestamp: Date.now()
        })
    }).catch(err => console.log('Feedback submission failed:', err));

    // Visual feedback
    event.target.classList.add('selected');
    showNotification('Thank you for your feedback!', 'success', 2000);
}

function applyToGrant(grantIndex) {
    showNotification('Starting grant application...', 'info');
    processVoiceInput(`Apply to grant number ${grantIndex + 1}`);
}

function learnMore(grantIndex) {
    showNotification('Loading grant details...', 'info');
    processVoiceInput(`Tell me more about grant number ${grantIndex + 1}`);
}

// ============================================================================
// MOBILE NAVIGATION
// ============================================================================

function showHome() {
    const contentArea = document.getElementById('contentArea');
    contentArea.innerHTML = `
        <div class="welcome">
            <h1>Aloha 🌺</h1>
            <p>What can I help you with today?</p>
        </div>
    `;
    updateMobileNav('home');
}

function showDashboard() {
    renderDashboard(document.getElementById('contentArea'), {});
    updateMobileNav('dashboard');
}

function updateMobileNav(active) {
    const buttons = document.querySelectorAll('.mobile-nav-button');
    buttons.forEach(btn => btn.classList.remove('active'));
    // This would need more sophisticated tracking in production
}

// ============================================================================
// UTILITIES
// ============================================================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function closeAllOverlays() {
    document.getElementById('onboardingOverlay').classList.remove('active');
    document.getElementById('helpOverlay').classList.remove('open');
    document.getElementById('agentPanel').classList.remove('open');
    document.getElementById('artifactGallery')?.classList.remove('open');
    state.agentPanelOpen = false;
    state.helpOpen = false;
    if (window.VesselsArtifacts) {
        window.VesselsArtifacts.state.galleryOpen = false;
    }
}

async function checkBackendConnection() {
    try {
        const response = await fetch(`${API_BASE}/api/status`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000)
        });

        if (response.ok) {
            const data = await response.json();
            showNotification('Connected to Vessels platform', 'success', 3000);
            console.log('Backend status:', data);
        } else {
            throw new Error('Backend returned error status');
        }
    } catch (error) {
        console.warn('Backend not available:', error);
        showNotification(
            'Running in offline mode. Some features may be limited.',
            'warning',
            5000
        );
    }
}

// ============================================================================
// LOCAL FALLBACK PROCESSING
// ============================================================================

function processLocally(text) {
    const lower = text.toLowerCase();

    if (lower.includes('grant') || lower.includes('funding')) {
        showLocalGrantInterface();
    } else if (lower.includes('elder') || lower.includes('kupuna')) {
        showLocalElderCare();
    } else if (lower.includes('dashboard') || lower.includes('impact')) {
        showDashboard();
    } else if (lower.includes('help')) {
        toggleHelp();
    } else {
        addSubtitle(
            "I'm working in offline mode. Try asking about grants, elder care, or say 'help'.",
            'agent-care',
            'System'
        );
    }
}

function showLocalGrantInterface() {
    renderGrantCards(document.getElementById('contentArea'), {
        grants: [
            {
                title: 'Older Americans Act',
                amount: '$50K - $500K',
                description: 'Federal funding for elder care services in rural communities.',
                match_score: 92
            },
            {
                title: 'Hawaii Community Foundation',
                amount: '$10K - $50K',
                description: 'Local funding for community-driven initiatives.',
                match_score: 85
            },
            {
                title: 'AARP Foundation Grants',
                amount: '$5K - $25K',
                description: 'Support for elder care programs and services.',
                match_score: 78
            }
        ]
    });

    setTimeout(() => {
        addSubtitle("I found 3 matching grants for your community needs", 'agent-grant', 'Grant Finder');
    }, 500);
}

function showLocalElderCare() {
    renderCareProtocol(document.getElementById('contentArea'), {
        title: 'Kupuna Care Protocol',
        steps: [
            { title: 'Morning Check', description: 'Call or visit by 9am. Verify medications taken, breakfast eaten.' },
            { title: 'Midday Support', description: 'Lunch delivery if needed. Social interaction, talk story time.' },
            { title: 'Afternoon Tasks', description: 'Doctor appointments, shopping. Coordinate with ʻohana.' },
            { title: 'Evening Safety', description: 'Dinner check, secure home. Emergency contacts confirmed.' }
        ]
    });

    setTimeout(() => {
        addSubtitle("Here's a culturally-adapted care protocol for kupuna", 'agent-care', 'Elder Care Specialist');
    }, 500);
}

// ============================================================================
// SESSION SUMMARY
// ============================================================================

function getSessionSummary() {
    const summary = {
        session_id: SESSION_ID,
        duration: Date.now() - parseInt(SESSION_ID.split('_')[1]),
        interactions: state.sessionContext.length,
        agents_deployed: state.activeAgents.length,
        languages_used: [state.currentLanguage]
    };

    return summary;
}

// Export for debugging
window.VesselsState = state;
window.getSessionSummary = getSessionSummary;

console.log('Vessels Enhanced UI loaded successfully ✓');
