// VESSELS GIST ARTIFACTS - Beautiful Visual Content Generation
// Crystallizes meaningful conversation moments into visual artifacts

// ============================================================================
// GIST TYPES & VISUAL DEFINITIONS
// ============================================================================

const GIST_TYPES = {
    insight: {
        name: 'Insight',
        icon: '💡',
        gradient: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 50%, #c4b5fd 100%)',
        glow: 'rgba(139, 92, 246, 0.4)',
        border: 'rgba(167, 139, 250, 0.6)',
        description: 'A new understanding emerged'
    },
    decision: {
        name: 'Decision',
        icon: '✓',
        gradient: 'linear-gradient(135deg, #10b981 0%, #34d399 50%, #6ee7b7 100%)',
        glow: 'rgba(16, 185, 129, 0.4)',
        border: 'rgba(52, 211, 153, 0.6)',
        description: 'A choice was made'
    },
    action: {
        name: 'Action',
        icon: '→',
        gradient: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 50%, #93c5fd 100%)',
        glow: 'rgba(59, 130, 246, 0.4)',
        border: 'rgba(96, 165, 250, 0.6)',
        description: 'Something to be done'
    },
    resource: {
        name: 'Resource',
        icon: '💎',
        gradient: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 50%, #fcd34d 100%)',
        glow: 'rgba(245, 158, 11, 0.4)',
        border: 'rgba(251, 191, 36, 0.6)',
        description: 'A valuable asset found'
    },
    connection: {
        name: 'Connection',
        icon: '🔗',
        gradient: 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 50%, #5eead4 100%)',
        glow: 'rgba(20, 184, 166, 0.4)',
        border: 'rgba(45, 212, 191, 0.6)',
        description: 'A relationship discovered'
    },
    milestone: {
        name: 'Milestone',
        icon: '⭐',
        gradient: 'linear-gradient(135deg, #f43f5e 0%, #fb7185 50%, #fda4af 100%)',
        glow: 'rgba(244, 63, 94, 0.4)',
        border: 'rgba(251, 113, 133, 0.6)',
        description: 'A significant moment'
    }
};

// ============================================================================
// ARTIFACT STATE MANAGEMENT
// ============================================================================

const artifactState = {
    artifacts: [],
    galleryOpen: false,
    currentFilter: 'all'
};

// Load from localStorage on init
function initArtifacts() {
    const saved = localStorage.getItem('vessels_artifacts');
    if (saved) {
        try {
            artifactState.artifacts = JSON.parse(saved);
        } catch (e) {
            console.warn('Failed to load saved artifacts:', e);
        }
    }
    renderArtifactGallery();
    updateArtifactCount();
}

// Save to localStorage
function saveArtifacts() {
    localStorage.setItem('vessels_artifacts', JSON.stringify(artifactState.artifacts));
}

// ============================================================================
// GIST DETECTION
// ============================================================================

// Pattern-based gist detection (client-side fallback)
const GIST_PATTERNS = {
    insight: [
        /I (?:now )?understand/i,
        /(?:key|important) (?:insight|realization|finding)/i,
        /this means/i,
        /the (?:real|core|key) (?:issue|point|thing)/i,
        /we've (?:discovered|learned|realized)/i,
        /aha moment/i,
        /breakthrough/i
    ],
    decision: [
        /we(?:'ve| have)? decided/i,
        /let's go with/i,
        /the decision is/i,
        /we(?:'ll| will) (?:proceed|move forward) with/i,
        /agreed(?:!|\.)/i,
        /our choice is/i,
        /confirmed:/i
    ],
    action: [
        /next step(?:s)?:/i,
        /action item(?:s)?:/i,
        /todo:/i,
        /we need to/i,
        /(?:please|can you) (?:do|complete|finish)/i,
        /follow(?:-| )up:/i,
        /task:/i
    ],
    resource: [
        /grant(?:s)? (?:found|identified|available)/i,
        /funding opportunity/i,
        /resource(?:s)? available/i,
        /contact:/i,
        /found \$[\d,]+/i,
        /budget:/i,
        /opportunity:/i
    ],
    connection: [
        /(?:connected|linked) with/i,
        /relationship with/i,
        /partnership/i,
        /collaboration with/i,
        /network(?:ed|ing)/i,
        /introduced to/i,
        /ally:/i
    ],
    milestone: [
        /milestone(?:!|:)/i,
        /achievement(?:!|:)/i,
        /completed(?:!)/i,
        /success(?:!|:)/i,
        /accomplished/i,
        /reached our goal/i,
        /celebration/i
    ]
};

// Detect gist type from text
function detectGistType(text) {
    for (const [type, patterns] of Object.entries(GIST_PATTERNS)) {
        for (const pattern of patterns) {
            if (pattern.test(text)) {
                return type;
            }
        }
    }
    return null;
}

// Extract gist content (simplified - enhance with LLM on backend)
function extractGistContent(text, type) {
    // Find the most relevant sentence
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 10);

    // Score sentences based on gist type keywords
    const patterns = GIST_PATTERNS[type] || [];
    let bestSentence = sentences[0] || text;
    let bestScore = 0;

    for (const sentence of sentences) {
        let score = 0;
        for (const pattern of patterns) {
            if (pattern.test(sentence)) score += 2;
        }
        // Bonus for shorter, punchier sentences
        if (sentence.length < 100) score += 1;

        if (score > bestScore) {
            bestScore = score;
            bestSentence = sentence;
        }
    }

    return bestSentence.trim();
}

// ============================================================================
// ARTIFACT CREATION
// ============================================================================

function createArtifact(options) {
    const {
        type = 'insight',
        title,
        content,
        context = null,
        source = 'conversation'
    } = options;

    const typeInfo = GIST_TYPES[type] || GIST_TYPES.insight;

    const artifact = {
        id: `artifact_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type,
        title: title || typeInfo.name,
        content,
        context,
        source,
        timestamp: Date.now(),
        saved: false
    };

    // Add to state
    artifactState.artifacts.unshift(artifact);
    saveArtifacts();
    updateArtifactCount();

    // Render the artifact with emergence animation
    renderArtifactEmergence(artifact);

    return artifact;
}

// Process response to check for gists
function processForGists(responseText, responseType = 'assistant') {
    const detectedType = detectGistType(responseText);

    if (detectedType) {
        const content = extractGistContent(responseText, detectedType);

        // Only create artifact if content is meaningful
        if (content && content.length > 20) {
            createArtifact({
                type: detectedType,
                content: content,
                context: responseText.substring(0, 200),
                source: responseType
            });
        }
    }
}

// ============================================================================
// ARTIFACT RENDERING - EMERGENCE ANIMATION
// ============================================================================

function renderArtifactEmergence(artifact) {
    const typeInfo = GIST_TYPES[artifact.type] || GIST_TYPES.insight;

    // Create container if it doesn't exist
    let container = document.getElementById('artifactEmergence');
    if (!container) {
        container = document.createElement('div');
        container.id = 'artifactEmergence';
        container.className = 'artifact-emergence-container';
        document.body.appendChild(container);
    }

    // Create the artifact card
    const card = document.createElement('div');
    card.className = 'artifact-card emerging';
    card.dataset.artifactId = artifact.id;
    card.innerHTML = `
        <div class="artifact-glow" style="background: ${typeInfo.glow}"></div>
        <div class="artifact-border" style="border-color: ${typeInfo.border}"></div>
        <div class="artifact-inner">
            <div class="artifact-header">
                <div class="artifact-icon" style="background: ${typeInfo.gradient}">
                    ${typeInfo.icon}
                </div>
                <div class="artifact-meta">
                    <span class="artifact-type">${typeInfo.name}</span>
                    <span class="artifact-time">${formatRelativeTime(artifact.timestamp)}</span>
                </div>
            </div>
            <div class="artifact-content">
                ${escapeHtml(artifact.content)}
            </div>
            <div class="artifact-actions">
                <button class="artifact-action-btn" onclick="saveArtifact('${artifact.id}')" title="Save">
                    <span class="action-icon">📌</span>
                </button>
                <button class="artifact-action-btn" onclick="expandArtifact('${artifact.id}')" title="Expand">
                    <span class="action-icon">↗</span>
                </button>
                <button class="artifact-action-btn" onclick="shareArtifact('${artifact.id}')" title="Share">
                    <span class="action-icon">↪</span>
                </button>
                <button class="artifact-action-btn dismiss" onclick="dismissArtifact('${artifact.id}')" title="Dismiss">
                    <span class="action-icon">×</span>
                </button>
            </div>
        </div>
        <div class="artifact-shimmer"></div>
    `;

    container.appendChild(card);

    // Trigger emergence animation
    requestAnimationFrame(() => {
        card.classList.add('emerged');
    });

    // Play subtle sound (if enabled)
    playArtifactSound(artifact.type);

    // Auto-dismiss after 12 seconds if not interacted with
    setTimeout(() => {
        if (card.parentNode && !card.classList.contains('saved')) {
            dismissArtifact(artifact.id);
        }
    }, 12000);
}

// ============================================================================
// ARTIFACT GALLERY
// ============================================================================

function toggleArtifactGallery() {
    artifactState.galleryOpen = !artifactState.galleryOpen;
    const gallery = document.getElementById('artifactGallery');

    if (artifactState.galleryOpen) {
        renderArtifactGallery();
        gallery.classList.add('open');
    } else {
        gallery.classList.remove('open');
    }
}

function renderArtifactGallery() {
    const gallery = document.getElementById('artifactGalleryContent');
    if (!gallery) return;

    const filtered = artifactState.currentFilter === 'all'
        ? artifactState.artifacts
        : artifactState.artifacts.filter(a => a.type === artifactState.currentFilter);

    if (filtered.length === 0) {
        gallery.innerHTML = `
            <div class="gallery-empty">
                <div class="empty-icon">✨</div>
                <p>No artifacts yet</p>
                <p class="empty-hint">Meaningful moments will appear here as you converse</p>
            </div>
        `;
        return;
    }

    gallery.innerHTML = filtered.map(artifact => {
        const typeInfo = GIST_TYPES[artifact.type] || GIST_TYPES.insight;
        return `
            <div class="gallery-artifact" onclick="expandArtifact('${artifact.id}')">
                <div class="gallery-artifact-icon" style="background: ${typeInfo.gradient}">
                    ${typeInfo.icon}
                </div>
                <div class="gallery-artifact-content">
                    <div class="gallery-artifact-type">${typeInfo.name}</div>
                    <div class="gallery-artifact-text">${escapeHtml(truncate(artifact.content, 80))}</div>
                    <div class="gallery-artifact-time">${formatRelativeTime(artifact.timestamp)}</div>
                </div>
                ${artifact.saved ? '<span class="saved-badge">📌</span>' : ''}
            </div>
        `;
    }).join('');
}

function filterArtifacts(type) {
    artifactState.currentFilter = type;

    // Update filter buttons
    document.querySelectorAll('.gallery-filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === type);
    });

    renderArtifactGallery();
}

function updateArtifactCount() {
    const badge = document.getElementById('artifactCount');
    if (badge) {
        const count = artifactState.artifacts.length;
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

// ============================================================================
// ARTIFACT ACTIONS
// ============================================================================

function saveArtifact(id) {
    const artifact = artifactState.artifacts.find(a => a.id === id);
    if (artifact) {
        artifact.saved = true;
        saveArtifacts();

        // Visual feedback
        const card = document.querySelector(`[data-artifact-id="${id}"]`);
        if (card) {
            card.classList.add('saved');
        }

        showNotification('Artifact saved to your collection', 'success', 2000);
    }
}

function dismissArtifact(id) {
    const card = document.querySelector(`[data-artifact-id="${id}"]`);
    if (card) {
        card.classList.add('dismissing');
        setTimeout(() => {
            card.remove();
        }, 400);
    }
}

function expandArtifact(id) {
    const artifact = artifactState.artifacts.find(a => a.id === id);
    if (!artifact) return;

    const typeInfo = GIST_TYPES[artifact.type] || GIST_TYPES.insight;

    // Create expanded view overlay
    const overlay = document.createElement('div');
    overlay.className = 'artifact-expand-overlay';
    overlay.innerHTML = `
        <div class="artifact-expand-card">
            <button class="expand-close" onclick="this.closest('.artifact-expand-overlay').remove()">×</button>

            <div class="expand-header" style="background: ${typeInfo.gradient}">
                <span class="expand-icon">${typeInfo.icon}</span>
                <span class="expand-type">${typeInfo.name}</span>
            </div>

            <div class="expand-body">
                <div class="expand-content">${escapeHtml(artifact.content)}</div>

                ${artifact.context ? `
                    <div class="expand-context">
                        <div class="context-label">Context</div>
                        <div class="context-text">${escapeHtml(artifact.context)}</div>
                    </div>
                ` : ''}

                <div class="expand-meta">
                    <span>Created ${formatFullTime(artifact.timestamp)}</span>
                    <span>Source: ${artifact.source}</span>
                </div>
            </div>

            <div class="expand-actions">
                <button class="expand-action-btn" onclick="copyArtifact('${artifact.id}')">
                    📋 Copy
                </button>
                <button class="expand-action-btn" onclick="exportArtifact('${artifact.id}')">
                    📤 Export
                </button>
                <button class="expand-action-btn danger" onclick="deleteArtifact('${artifact.id}')">
                    🗑 Delete
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // Close on background click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
    });

    // Close on Escape
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            overlay.remove();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

function shareArtifact(id) {
    const artifact = artifactState.artifacts.find(a => a.id === id);
    if (!artifact) return;

    const typeInfo = GIST_TYPES[artifact.type] || GIST_TYPES.insight;
    const shareText = `${typeInfo.icon} ${typeInfo.name}: ${artifact.content}`;

    if (navigator.share) {
        navigator.share({
            title: `Vessels ${typeInfo.name}`,
            text: shareText
        }).catch(() => {
            copyToClipboard(shareText);
        });
    } else {
        copyToClipboard(shareText);
    }
}

function copyArtifact(id) {
    const artifact = artifactState.artifacts.find(a => a.id === id);
    if (artifact) {
        copyToClipboard(artifact.content);
        showNotification('Copied to clipboard', 'success', 2000);
    }
}

function exportArtifact(id) {
    const artifact = artifactState.artifacts.find(a => a.id === id);
    if (!artifact) return;

    const typeInfo = GIST_TYPES[artifact.type] || GIST_TYPES.insight;
    const exportData = {
        type: artifact.type,
        typeName: typeInfo.name,
        content: artifact.content,
        context: artifact.context,
        timestamp: new Date(artifact.timestamp).toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vessels-${artifact.type}-${artifact.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function deleteArtifact(id) {
    if (confirm('Delete this artifact?')) {
        artifactState.artifacts = artifactState.artifacts.filter(a => a.id !== id);
        saveArtifacts();
        updateArtifactCount();
        renderArtifactGallery();

        // Close overlay
        document.querySelector('.artifact-expand-overlay')?.remove();

        showNotification('Artifact deleted', 'info', 2000);
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatRelativeTime(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function formatFullTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function truncate(text, length) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard', 'success', 2000);
    }).catch(() => {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('Copied to clipboard', 'success', 2000);
    });
}

function playArtifactSound(type) {
    // Optional: subtle audio feedback
    // Using Web Audio API for a soft chime
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        // Different tones for different types
        const frequencies = {
            insight: 523.25,    // C5
            decision: 659.25,   // E5
            action: 392,        // G4
            resource: 783.99,   // G5
            connection: 587.33, // D5
            milestone: 880      // A5
        };

        oscillator.frequency.value = frequencies[type] || 523.25;
        oscillator.type = 'sine';

        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.5);
    } catch (e) {
        // Audio not supported, silent fail
    }
}

// ============================================================================
// MANUAL ARTIFACT CREATION (for testing/demo)
// ============================================================================

function createManualArtifact(type, content) {
    return createArtifact({
        type: type || 'insight',
        content: content || 'This is a test artifact',
        source: 'manual'
    });
}

// Demo function to show all artifact types
function demoArtifacts() {
    const demos = [
        { type: 'insight', content: 'The community garden project could serve as a central hub for both food distribution and social gathering.' },
        { type: 'decision', content: 'We will proceed with the grant application for the Older Americans Act funding.' },
        { type: 'action', content: 'Schedule meeting with County Elder Services to discuss partnership opportunities.' },
        { type: 'resource', content: 'Found $50,000 Hawaii Community Foundation grant matching our elder care criteria.' },
        { type: 'connection', content: 'Connected with Aunty Leilani who coordinates meals for 12 kupuna in Waimea.' },
        { type: 'milestone', content: 'First successful week of volunteer-coordinated meal deliveries - 45 meals served!' }
    ];

    demos.forEach((demo, i) => {
        setTimeout(() => {
            createArtifact({
                type: demo.type,
                content: demo.content,
                source: 'demo'
            });
        }, i * 2000);
    });
}

// ============================================================================
// INITIALIZATION
// ============================================================================

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initArtifacts);
} else {
    initArtifacts();
}

// Export for global access
window.VesselsArtifacts = {
    create: createArtifact,
    processForGists,
    toggle: toggleArtifactGallery,
    demo: demoArtifacts,
    state: artifactState,
    types: GIST_TYPES
};

console.log('Vessels Gist Artifacts loaded ✨');
