/* ============================================
   IRIS v7.0 SECURE - The Conscious AI Workspace
   FULLY FIXED & ENHANCED VERSION
   - Voice profile selection
   - Retry last message
   - Emoji picker for reactions
   - Command palette with fuzzy search
   - Document preview, import, export
   - Memory graph visualization
   - Syntax highlighting
   - System commands (screenshot/lock/volume/brightness)
   - Creator admin panel with user management
   - Password authentication (optional)
   - Scheduled tasks (email reminders)
   - Speaking indicator and hologram
   ============================================ */

'use strict';

function fuzzySearch(query, items, keys) {
    if (!query) return items;
    const lowerQuery = query.toLowerCase();
    return items.filter(item => {
        return keys.some(key => {
            const val = item[key];
            if (typeof val !== 'string') return false;
            return val.toLowerCase().includes(lowerQuery);
        });
    });
}

class IRISApp {
    constructor() {
        // Core state
        this.currentUser = null;
        this.currentChat = null;
        this.chats = [];
        this.messages = [];
        this.abortControllers = new Map();

        // Configuration
        this.personalities = {};
        this.themes = {};
        this.voices = {};
        this.models = {};
        this.reasoningModes = {};
        this.commands = {};

        // UI State
        this.isRecording = false;
        this.sidebarVisible = true;
        this.rightPanelVisible = true;
        this.commandPaletteOpen = false;
        this.focusMode = false;
        this.isTyping = false;
        this.currentPanelTab = 'context';
        this.replyingTo = null;
        this.isSpeaking = false;
        this.currentAudio = null;
        this.hologram = null;
        this.liveMode = false;
        this.currentChatPersonality = null;

        // Command palette navigation
        this.commandSelectedIndex = 0;
        this.filteredCommands = [];

        // Emoji picker
        this.emojiPickerVisible = false;
        this.currentReactionMessageId = null;

        // Features
        this.voiceWaveformInterval = null;
        this.offline = !navigator.onLine;
        this.csrfToken = null;

        // Admin / creator
        this.userList = [];
        this.selectedUserId = null;
        this.facts = [];
        this.pendingFacts = [];
        this.allTags = [];

        // Initialize
        this.init();
    }

    async init() {
        try {
            this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            const loggedIn = await this.checkLogin();
            if (!loggedIn) return;
            await this.loadConfig();
            this.applyTheme(this.currentUser?.theme || 'midnight');
            this.setupEventListeners();
            this.setupCommandPalette();
            this.setupDragAndDrop();
            this.setupOfflineDetection();
            this.setupKeyboardShortcuts();
            this.renderLogo();
            this.loadReportList();
            await this.loadChats();
            this.initHologram();
            if (this.currentUser?.focus_mode) this.toggleFocusMode(true);
            console.log('🚀 IRIS v7.0 Secure Enhanced Initialized');
        } catch (error) {
            console.error('Initialization error:', error);
            this.showToast('Failed to initialize application', 'error');
        }
    }

async loadReportList() {
    try {
        const data = await this.secureFetch('/api/reports/list');
        if (data?.success) {
            this.availableReports = data.reports;
        }
    } catch (e) {
        console.error('Failed to load report list:', e);
        // Fallback list
        this.availableReports = [
            'system_health', 'error_logs', 'performance_metrics', 'trading_activity',
            'portfolio_snapshot', 'security_log', 'database_backup', 'api_usage',
            'model_usage', 'system_update', 'weekly_intelligence', 'file_changes',
            'autonomous_actions'
        ];
    }
}

    // Offline Models
    async refreshModels() {
        try {
            const models = await this.secureFetch('/api/models');
            this.renderModelList(models);
        } catch (e) {
            console.error('Failed to load models:', e);
            this.showToast('Error loading models', 'error');
        }
    }

    renderModelList(models) {
        const container = document.getElementById('offlineModelList');
        if (!container) return;
        if (!models || models.length === 0) {
            container.innerHTML = '<div class="context-item">No models available.</div>';
            return;
        }
        container.innerHTML = models.map(model => `
            <div class="context-item" style="flex-wrap: wrap;">
                <div class="context-item-icon">🤖</div>
                <div style="flex: 1;">
                    <div><strong>${this.escapeHtml(model.name)}</strong> (${model.size})</div>
                    <div style="font-size: 0.75rem; color: var(--iris-text-muted);">${model.description}</div>
                    <div style="font-size: 0.75rem;">Status: ${model.status}</div>
                </div>
                <div class="message-actions" style="opacity:1; margin-left:auto;">
                    ${model.status === 'available' ? 
                        `<button class="message-action-btn" onclick="app.downloadModel('${model.repo_id}')" title="Download">⬇️</button>` : 
                        `<button class="message-action-btn" onclick="app.switchModel('${model.repo_id}')" title="Activate">✅</button>
                         <button class="message-action-btn" onclick="app.deleteModel('${model.repo_id}')" title="Delete">🗑️</button>`}
                </div>
            </div>
        `).join('');
    }

    async downloadModel(repoId) {
        try {
            const data = await this.secureFetch('/api/models/download', {
                method: 'POST',
                body: { repo_id: repoId }
            });
            this.showToast('Download started. Check back later.', 'info');
            this.refreshModels();
        } catch (e) {
            this.showToast('Download failed', 'error');
        }
    }

    async switchModel(repoId) {
        try {
            const data = await this.secureFetch('/api/models/switch', {
                method: 'POST',
                body: { repo_id: repoId }
            });
            this.showToast('Model activated', 'success');
            this.refreshModels();
        } catch (e) {
            this.showToast('Switch failed: ' + (e.message || 'Unknown error'), 'error');
        }
    }

    async deleteModel(repoId) {
        if (!confirm('Delete this model?')) return;
        try {
            const data = await this.secureFetch(`/api/models/${encodeURIComponent(repoId)}`, {
                method: 'DELETE'
            });
            this.showToast('Model deleted', 'success');
            this.refreshModels();
        } catch (e) {
            this.showToast('Delete failed', 'error');
        }
    }

    // ==========================================
    // CREATOR ADMIN
    // ==========================================

    async loadUserList() {
        try {
            const data = await this.secureFetch('/api/admin/users');
            if (data?.success) {
                this.userList = data.users;
                this.renderUserList();
            }
        } catch (e) {
            console.error('Load user list error:', e);
        }
    }

    renderUserList() {
        const container = document.getElementById('userList');
        if (!container) return;
        if (!this.userList || this.userList.length === 0) {
            container.innerHTML = '<div class="context-item">No users found.</div>';
            return;
        }
        container.innerHTML = this.userList.map(u => `
            <div class="context-item" onclick="app.selectUser('${u.id}')" style="cursor: pointer;">
                <div class="context-item-icon">${u.role === 'creator' ? '👑' : '👤'}</div>
                <div>
                    <div style="font-weight: 500;">${this.escapeHtml(u.username)}</div>
                    <div style="font-size: 0.75rem; color: var(--iris-text-muted);">
                        Role: ${u.role} · Created: ${new Date(u.created_at).toLocaleDateString()}
                    </div>
                </div>
            </div>
        `).join('');
    }

    selectUser(userId) {
        this.selectedUserId = userId;
        const user = this.userList.find(u => u.id === userId);
        if (!user) return;
        document.getElementById('selectedUserSection').style.display = 'block';
        document.getElementById('selectedUserTitle').innerText = `User: ${user.username}`;
        document.getElementById('selectedUserInfo').innerHTML = `
            <div class="context-item">
                <div><strong>ID:</strong> ${user.id}</div>
                <div><strong>Email:</strong> ${user.email || 'none'}</div>
                <div><strong>Role:</strong> ${user.role}</div>
                <div><strong>Last Login:</strong> ${user.last_login ? new Date(user.last_login).toLocaleString() : 'never'}</div>
            </div>
        `;
        document.getElementById('userDataDisplay').innerHTML = '';
    }

    async viewUserFacts() {
        if (!this.selectedUserId) return;
        try {
            const data = await this.secureFetch(`/api/memory/facts?user_id=${this.selectedUserId}&include_shared=false`);
            if (data?.success) {
                let html = '<div class="context-section-title">Facts</div>';
                if (data.facts.length === 0) {
                    html += '<div class="context-item">No facts.</div>';
                } else {
                    data.facts.forEach(f => {
                        html += `<div class="context-item">${this.escapeHtml(f.fact)} <span style="font-size:0.75rem;">(conf: ${f.confidence})</span></div>`;
                    });
                }
                document.getElementById('userDataDisplay').innerHTML = html;
            }
        } catch (e) {
            this.showToast('Error loading facts', 'error');
        }
    }

    async viewUserDocs() {
        if (!this.selectedUserId) return;
        try {
            const data = await this.secureFetch(`/api/documents?user_id=${this.selectedUserId}`);
            if (data?.success) {
                let html = '<div class="context-section-title">Documents</div>';
                if (data.documents.length === 0) {
                    html += '<div class="context-item">No documents.</div>';
                } else {
                    data.documents.forEach(d => {
                        html += `<div class="context-item" onclick="app.viewDocument('${d.id}')">📄 ${this.escapeHtml(d.filename)}</div>`;
                    });
                }
                document.getElementById('userDataDisplay').innerHTML = html;
            }
        } catch (e) {
            this.showToast('Error loading documents', 'error');
        }
    }

    async impersonateUser() {
        if (!this.selectedUserId) return;
        if (confirm(`Impersonate user ${this.selectedUserId}?`)) {
            try {
                const data = await this.secureFetch('/api/admin/impersonate', {
                    method: 'POST',
                    body: { user_id: this.selectedUserId }
                });
                if (data?.success) {
                    this.showToast('Now impersonating user', 'success');
                    await this.loadUser();
                    await this.loadChats();
                }
            } catch (e) {
                this.showToast('Impersonation failed', 'error');
            }
        }
    }

    async revertImpersonation() {
        try {
            const data = await this.secureFetch('/api/admin/revert', { method: 'POST' });
            if (data?.success) {
                this.showToast('Reverted to original user', 'success');
                await this.loadUser();
                await this.loadChats();
            }
        } catch (e) {
            this.showToast('Revert failed', 'error');
        }
    }

    async exportUserData() {
        if (!this.selectedUserId) return;
        try {
            const response = await fetch(`/api/admin/users/${this.selectedUserId}/export`, {
                headers: { 'X-CSRFToken': this.csrfToken }
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `user_${this.selectedUserId}_export.json`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            this.showToast('Export failed', 'error');
        }
    }

    async deleteUser() {
        if (!this.selectedUserId) return;
        if (!confirm(`Permanently delete user ${this.selectedUserId}?`)) return;
        try {
            const data = await this.secureFetch(`/api/admin/users/${this.selectedUserId}`, {
                method: 'DELETE'
            });
            if (data?.success) {
                this.showToast('User deleted', 'success');
                this.loadUserList();
                document.getElementById('selectedUserSection').style.display = 'none';
            }
        } catch (e) {
            this.showToast('Delete failed', 'error');
        }
    }

    refreshUserList() {
        this.loadUserList();
    }

    // ==========================================
    // SELF DESTRUCT (CREATOR ONLY)
    // ==========================================

    showSelfDestructDialog() {
        if (this.currentUser?.role !== 'creator') {
            this.showToast('Access denied', 'error');
            return;
        }
        // For demo, we'll simulate voice/face with confirm prompts
        // In production, replace with real biometric checks
        const voiceOk = confirm('Say "I confirm self‑destruct" into the microphone. (Simulated)');
        if (!voiceOk) {
            this.showToast('Self‑destruct cancelled', 'info');
            return;
        }
        const faceOk = confirm('Look at the camera for face verification. (Simulated)');
        if (!faceOk) {
            this.showToast('Self‑destruct cancelled', 'info');
            return;
        }
        const password = prompt('Enter your admin password:');
        if (!password) return;
        this.selfDestruct(password);
    }

    async selfDestruct(password) {
        try {
            const data = await this.secureFetch('/api/self_destruct', {
                method: 'POST',
                body: {
                    voice: 'dummy_voice_match',   // Replace with actual voice print later
                    face: 'dummy_face_match',     // Replace with actual face print later
                    password: password
                }
            });
            if (data?.success) {
                this.showToast('Self‑destruct initiated. Backup sent to email.', 'warning');
                await this.logout();
            } else {
                this.showToast('Self‑destruct failed: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (e) {
            this.showToast('Self‑destruct error', 'error');
        }
    }

    // ==========================================
    // USER AUTHENTICATION (with password)
    // ==========================================

async checkLogin() {
    try {
        // Try to fetch current user
        const data = await this.secureFetch('/api/current_user');
        if (data?.success) {
            this.currentUser = data.user;
            this.updateUIForUser();
            document.getElementById('loginOverlay').style.display = 'none';
            await this.loadChats();
            return true;
        } else {
            this.showLogin();
            return false;
        }
    } catch (e) {
        console.warn('Check login error:', e);
        // If offline, check for stored local user or create guest
        const localUser = localStorage.getItem('localUser');
        if (localUser) {
            this.currentUser = JSON.parse(localUser);
            this.currentUser.local_only = true; // mark as local-only
            this.updateUIForUser();
            document.getElementById('loginOverlay').style.display = 'none';
            this.showToast('Offline mode – using local user', 'info');
            await this.loadChats(); // load chats from IndexedDB? Not yet implemented.
            return true;
        } else {
            // Show login but with offline notice
            this.showLogin();
            document.querySelector('.login-modal p').innerHTML = 
                'You are offline. Enter a name to continue in local-only mode.';
            return false;
        }
    }
}

    showLogin() {
        document.getElementById('loginOverlay').style.display = 'flex';
        document.getElementById('loginName').focus();
        // Also show password field (if not already present, we add it dynamically)
        const loginModal = document.querySelector('.login-modal');
        if (loginModal && !document.getElementById('loginPassword')) {
            const passwordInput = document.createElement('input');
            passwordInput.type = 'password';
            passwordInput.id = 'loginPassword';
            passwordInput.className = 'search-input';
            passwordInput.placeholder = 'Password (optional)';
            passwordInput.style.marginTop = '0.5rem';
            const nameInput = document.getElementById('loginName');
            nameInput.insertAdjacentElement('afterend', passwordInput);
        }
    }

async login() {
    const nameInput = document.getElementById('loginName');
    const passwordInput = document.getElementById('loginPassword');
    const username = nameInput.value.trim();
    const password = passwordInput ? passwordInput.value : '';
    if (!username) return;

    try {
        const data = await this.secureFetch('/api/login', {
            method: 'POST',
            body: { username, password }
        });
        if (data?.success) {
            this.currentUser = data.user;
            this.updateUIForUser();
            document.getElementById('loginOverlay').style.display = 'none';
            // Save user locally for offline use
            localStorage.setItem('localUser', JSON.stringify(this.currentUser));
            // ... rest of success handling
        } else {
            this.showToast('Login failed: ' + (data.error || 'Invalid credentials'), 'error');
        }
    } catch (e) {
        console.warn('Login error – offline?', e);
        // If offline, create a local user
        const localUser = {
            id: 'local-' + Date.now(),
            username: username,
            role: 'family',
            local_only: true,
            theme: 'midnight',
            personality: 'default',
            voice_enabled: false,
            model: 'local'
        };
        localStorage.setItem('localUser', JSON.stringify(localUser));
        this.currentUser = localUser;
        this.updateUIForUser();
        document.getElementById('loginOverlay').style.display = 'none';
        this.showToast('Logged in locally (offline mode)', 'info');
        await this.loadChats(); // eventually load from local storage
    }
}
    async logout() {
        try {
            await this.secureFetch('/api/logout', { method: 'POST' });
            this.currentUser = null;
            this.chats = [];
            this.messages = [];
            this.renderChatList();
            this.showWelcomeState();
            this.showLogin();
        } catch (e) {
            console.error('Logout error:', e);
        }
    }

    toggleUserMenu() {
        const menu = document.getElementById('userMenu');
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }

    async switchUser(username) {
        this.toggleUserMenu();
        await this.logout();
        document.getElementById('loginName').value = username;
        document.getElementById('loginPassword').value = '';
        this.login();
    }

    addNewUser() {
        this.toggleUserMenu();
        this.showLogin();
        document.getElementById('loginName').value = '';
        if (document.getElementById('loginPassword')) document.getElementById('loginPassword').value = '';
        document.getElementById('loginName').focus();
    }

    // ==========================================
    // SECURE API HELPERS
    // ==========================================

    async secureFetch(url, options = {}) {
        const controller = new AbortController();
        const requestId = Date.now().toString();
        this.abortControllers.set(requestId, controller);

        const defaultOptions = {
            signal: controller.signal,
            credentials: 'include',   // <-- ADD THIS LINE
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken || '',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        if (options.body && typeof options.body === 'object') {
            finalOptions.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, finalOptions);

            if (response.status === 429) {
                const data = await response.json();
                this.showToast(data.error || 'Rate limit exceeded. Please slow down.', 'warning');
                throw new Error('Rate limit exceeded');
            }

            if (response.status === 400) {
                const data = await response.json();
                if (data.error && data.error.includes('CSRF')) {
                    this.showToast('Security token expired. Refreshing...', 'warning');
                    window.location.reload();
                    throw new Error('CSRF token expired');
                }
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Request cancelled:', url);
                return null;
            }

            if (error.message === 'Failed to fetch') {
                this.showToast('Network error. Check your connection.', 'error');
            }

            throw error;
        } finally {
            this.abortControllers.delete(requestId);
        }
    }

    cancelRequest(requestId) {
        const controller = this.abortControllers.get(requestId);
        if (controller) {
            controller.abort();
            this.abortControllers.delete(requestId);
        }
    }

    // ==========================================
    // DATA LOADING
    // ==========================================

    async loadUser() {
        try {
            const data = await this.secureFetch('/api/user');
            if (data?.success) {
                this.currentUser = data.user;
            } else {
                throw new Error('Failed to load user');
            }
        } catch (e) {
            console.error('Load user error:', e);
            this.currentUser = {
                username: 'User',
                theme: 'midnight',
                personality: 'default',
                voice_enabled: false,
                voice_profile: 'jarvis',
                status: 'online',
                model: 'balanced',
                reasoning_mode: 'normal',
                role: 'family'
            };
        }
        this.updateUIForUser();
    }

    async loadConfig() {
        try {
            const data = await this.secureFetch('/api/config');
            if (data?.success) {
                this.personalities = data.personalities;
                this.themes = data.themes;
                this.models = data.models;
                this.reasoningModes = data.reasoning_modes;
                this.voices = data.voice_profiles;
                this.commands = data.commands;
            }
        } catch (e) {
            console.error('Load config error:', e);
            this.setDefaultConfig();
        }
        this.populateSettings();
    }

    setDefaultConfig() {
        this.personalities = {
            default: { name: 'Balanced', icon: '⚖️', desc: 'General-purpose assistance' },
            creative: { name: 'Creative', icon: '🎨', desc: 'Imaginative & artistic' },
            precise: { name: 'Precise', icon: '🎯', desc: 'Technical & accurate' }
        };

        this.themes = {
            midnight: { name: 'Midnight', bg: '#0a0a0f', type: 'dark' },
            light: { name: 'Clean Light', bg: '#ffffff', type: 'light' },
            sunset: { name: 'Sunset', bg: '#2d1b2e', type: 'dark' },
            forest: { name: 'Forest', bg: '#1a2e1a', type: 'dark' },
            ocean: { name: 'Ocean', bg: '#0a1f2e', type: 'dark' }
        };

        this.models = {
            fast: 'Fast',
            balanced: 'Balanced',
            powerful: 'Powerful'
        };

        this.reasoningModes = {
            normal: { name: 'Normal', icon: '⚡', desc: 'Standard responses' },
            deep: { name: 'Deep Analysis', icon: '🔬', desc: 'Thorough reasoning' },
            fast: { name: 'Fast Response', icon: '💨', desc: 'Quick answers' }
        };

        this.voices = {
            jarvis: { name: 'Jarvis', voice: 'en-GB-RyanNeural' },
            friday: { name: 'F.R.I.D.A.Y.', voice: 'en-US-JennyNeural' },
            tony: { name: 'Tony', voice: 'en-US-GuyNeural' },
            sarah: { name: 'Sarah', voice: 'en-US-SaraNeural' }
        };
    }

    async loadChats() {
        try {
            const data = await this.secureFetch('/api/chats');
            if (data?.success) {
                this.chats = data.chats;
                this.renderChatList();
                if (this.chats.length > 0 && !this.currentChat) {
                    await this.switchToChat(this.chats[0].id);
                }
            }
        } catch (e) {
            console.error('Load chats error:', e);
            this.chats = [];
            this.renderChatList();
        }
    }

    // ==========================================
    // SPEAKING INDICATOR & CONTROL
    // ==========================================

    speakText(text) {
        if (!this.currentUser?.voice_enabled) return;
        this.isSpeaking = true;
        this.updateHologramForSpeech(true);
        this.showSpeakingIndicator();

        fetch('/api/voice/speak', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                text: text.substring(0, 500),
                profile: this.currentUser.voice_profile,
                mood: 'neutral'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const duration = Math.max(2000, text.length * 60);
                setTimeout(() => {
                    this.isSpeaking = false;
                    this.updateHologramForSpeech(false);
                    this.hideSpeakingIndicator();
                }, duration);
            } else {
                this.isSpeaking = false;
                this.updateHologramForSpeech(false);
                this.hideSpeakingIndicator();
            }
        })
        .catch(() => {
            this.isSpeaking = false;
            this.updateHologramForSpeech(false);
            this.hideSpeakingIndicator();
        });
    }

    stopSpeaking() {
        fetch('/api/voice/stop', {
            method: 'POST',
            headers: { 'X-CSRFToken': this.csrfToken }
        })
        .then(() => {
            this.isSpeaking = false;
            this.hideSpeakingIndicator();
            this.updateHologramForSpeech(false);
        })
        .catch(err => console.error('Stop speaking error:', err));
    }

    showSpeakingIndicator() {
        const indicator = document.getElementById('speakingIndicator');
        if (indicator) indicator.style.display = 'flex';
    }

    hideSpeakingIndicator() {
        const indicator = document.getElementById('speakingIndicator');
        if (indicator) indicator.style.display = 'none';
    }

    // ==========================================
    // HOLOGRAM ANIMATION
    // ==========================================

    initHologram() {
        const canvas = document.getElementById('hologramCanvas');
        if (!canvas) return;
        canvas.style.display = 'none';
        this.hologram = new Hologram(canvas);
        this.hologram.start();
    }

    updateHologramForSpeech(isSpeaking) {
        if (this.hologram) {
            this.hologram.setSpeaking(isSpeaking);
        }
    }

    updateHologramForLive(isLive) {
        if (this.hologram) {
            this.hologram.setLive(isLive);
            const canvas = document.getElementById('hologramCanvas');
            if (canvas) {
                canvas.style.display = isLive ? 'block' : 'none';
                if (isLive) {
                    this.hologram.resize();
                }
            }
        }
    }

    // ==========================================
    // XSS-SAFE RENDERING
    // ==========================================

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    sanitizeHtml(html) {
        if (typeof DOMPurify !== 'undefined') {
            return DOMPurify.sanitize(html, {
                ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                              'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'a', 'span'],
                ALLOWED_ATTR: ['href', 'title', 'class']
            });
        }
        return this.escapeHtml(html);
    }

    renderLogo() {
        const containers = document.querySelectorAll('.iris-logo-container');
        const svg = `<svg class="iris-logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="infinityGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
                    <stop offset="50%" style="stop-color:#8b5cf6;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ec4899;stop-opacity:1" />
                </linearGradient>
                <radialGradient id="irisGradient" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.9" />
                    <stop offset="40%" style="stop-color:#60a5fa;stop-opacity:0.6" />
                    <stop offset="100%" style="stop-color:#6366f1;stop-opacity:0.2" />
                </radialGradient>
                <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>
            <g class="circuit-pattern" opacity="0.3">
                <path d="M15,50 L35,50 L45,40 M55,60 L65,50 L85,50" stroke="currentColor" stroke-width="1" fill="none"/>
                <path d="M50,15 L50,35 L40,45 M60,55 L50,65 L50,85" stroke="currentColor" stroke-width="1" fill="none"/>
                <circle cx="35" cy="50" r="3" fill="currentColor"/>
                <circle cx="65" cy="50" r="3" fill="currentColor"/>
            </g>
            <path class="infinity-loop" d="M30,50 C30,32 45,32 50,50 C55,68 70,68 70,50 C70,32 55,32 50,50 C45,68 30,68 30,50 Z"
                fill="none" stroke="url(#infinityGradient)" stroke-width="3" stroke-linecap="round" filter="url(#glow)"/>
            <circle class="iris-eye" cx="50" cy="50" r="10" fill="url(#irisGradient)" filter="url(#glow)"/>
            <circle cx="50" cy="50" r="4" fill="white" opacity="0.9"/>
            <circle class="data-pulse" r="3" fill="#06b6d4" filter="url(#glow)">
                <animateMotion dur="4s" repeatCount="indefinite" path="M30,50 C30,32 45,32 50,50 C55,68 70,68 70,50 C70,32 55,32 50,50 C45,68 30,68 30,50 Z"/>
            </circle>
        </svg>`;

        containers.forEach(container => {
            if (container) container.innerHTML = svg;
        });
    }

    renderChatList() {
        const container = document.getElementById('chatList');
        if (!container) return;

        const searchValue = (document.getElementById('searchChats')?.value || '').toLowerCase();
        const filtered = this.chats.filter(c =>
            c.title.toLowerCase().includes(searchValue) ||
            (c.tags || []).some(t => t.toLowerCase().includes(searchValue))
        );

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">💬</div>
                    <p>No conversations yet</p>
                    <p style="font-size: 0.875rem; margin-top: 0.5rem;">Start a new chat to begin</p>
                </div>`;
            return;
        }

        const pinned = filtered.filter(c => c.is_pinned);
        const today = filtered.filter(c => !c.is_pinned && this.isToday(c.updated_at));
        const yesterday = filtered.filter(c => !c.is_pinned && this.isYesterday(c.updated_at));
        const older = filtered.filter(c => !c.is_pinned && !this.isToday(c.updated_at) && !this.isYesterday(c.updated_at));

        let html = '';
        if (pinned.length) html += this.renderChatSection('📌 Pinned', pinned);
        if (today.length) html += this.renderChatSection('Today', today);
        if (yesterday.length) html += this.renderChatSection('Yesterday', yesterday);
        if (older.length) html += this.renderChatSection('Previous', older);

        container.innerHTML = html;
    }

    renderChatSection(title, chats) {
        return `<div class="chat-section">
            <div class="chat-section-title">${this.escapeHtml(title)}</div>
            ${chats.map(chat => this.renderChatItem(chat)).join('')}
        </div>`;
    }

    renderChatItem(chat) {
        const personalityKey = this.currentChatPersonality || this.currentUser?.personality || 'default';
        const personality = (this.personalities && this.personalities[personalityKey]) ||
                    { icon: '🤖', name: 'Assistant' };
        const isActive = chat.id === this.currentChat;

        return `<div class="chat-item ${isActive ? 'active' : ''} ${chat.is_pinned ? 'pinned' : ''}"
            data-chat-id="${chat.id}"
            onclick="app.switchToChat('${chat.id}')"
            oncontextmenu="app.showChatContextMenu(event, '${chat.id}')">
            <div class="chat-item-avatar">${personality.icon}</div>
            <div class="chat-item-content">
                <div class="chat-item-title">${this.escapeHtml(chat.title)}</div>
                <div class="chat-item-meta">
                    ${new Date(chat.updated_at).toLocaleDateString()} • ${chat.message_count || 0} messages
                    ${chat.is_temporary ? ' • ⏱️ Temporary' : ''}
                </div>
            </div>
        </div>`;
    }

    renderMessage(message) {
        const isUser = message.sender === 'user';
        const isSystem = message.sender === 'system';
        const personalityKey = this.currentChatPersonality || this.currentUser?.personality || 'default';
        const personality = (this.personalities && this.personalities[personalityKey]) ||
                            { icon: '🤖', name: 'Assistant' };

        let content = this.sanitizeHtml(message.content);

        if (typeof marked !== 'undefined' && !isSystem) {
            const parsed = marked.parse(message.content);
            content = this.sanitizeHtml(parsed);
        }

        const timestamp = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        let reactionsHtml = '';
        if (message.reactions && Object.keys(message.reactions).length > 0) {
            reactionsHtml = `<div class="message-reactions">
                ${Object.entries(message.reactions).map(([emoji, users]) => `
                    <span class="reaction ${users.includes(this.currentUser?.id) ? 'active' : ''}"
                          onclick="app.toggleReaction('${message.id}', '${emoji}')">
                        ${this.escapeHtml(emoji)} ${users.length}
                    </span>
                `).join('')}
            </div>`;
        }

        let replyHtml = '';
        if (message.reply_to) {
            const replyMsg = this.messages.find(m => m.id === message.reply_to);
            if (replyMsg) {
                replyHtml = `<div class="message-reply-preview" onclick="app.scrollToMessage('${message.reply_to}')">
                    ↩️ ${this.escapeHtml(replyMsg.content.substring(0, 50))}...
                </div>`;
            }
        }

        return `<div class="message ${message.sender}" id="msg-${message.id}" data-message-id="${message.id}">
            <div class="message-avatar">
                ${isUser ? (this.escapeHtml(this.currentUser?.username?.charAt(0).toUpperCase()) || 'U') :
                  isSystem ? '⚙️' : personality.icon}
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">${isUser ? 'You' : isSystem ? 'System' : personality.name}</span>
                    <span class="message-time">${timestamp}</span>
                    ${message.confidence_score ? `<span title="Confidence: ${Math.round(message.confidence_score * 100)}%">🎯</span>` : ''}
                </div>
                ${replyHtml}
                <div class="message-bubble">${content}</div>
                ${reactionsHtml}
                <div class="message-actions">
                    <button class="message-action-btn" onclick="app.addReaction('${message.id}', event)" title="Add reaction">😊</button>
                    <button class="message-action-btn" onclick="app.copyMessage('${message.id}')" title="Copy">📋</button>
                    ${isUser ? `<button class="message-action-btn" onclick="app.editMessage('${message.id}')" title="Edit">✏️</button>` : ''}
                    <button class="message-action-btn" onclick="app.replyToMessage('${message.id}')" title="Reply">↩️</button>
                    <button class="message-action-btn" onclick="app.retryMessage('${message.id}')" title="Retry response">🔄</button>
                </div>
            </div>
        </div>`;
    }

    // ==========================================
    // CHAT OPERATIONS
    // ==========================================

    async switchToChat(chatId) {
        if (!chatId) return;

        this.abortControllers.forEach(controller => controller.abort());
        this.abortControllers.clear();

        this.currentChat = chatId;
        this.replyingTo = null;
        this.hideReplyPreview();

        try {
            const data = await this.secureFetch(`/api/chats/${chatId}/messages`);

            const container = document.getElementById('messages');

            if (data?.success && data.messages?.length > 0) {
                this.messages = data.messages;
                container.innerHTML = data.messages.map(m => this.renderMessage(m)).join('');
                this.scrollToBottom();
                if (typeof hljs !== 'undefined') {
                    hljs.highlightAll();
                this.addCopyButtonsToCodeBlocks();   // <-- ADD THIS 
                }
            } else {
                this.showWelcomeState();
            }

            const chat = this.chats.find(c => c.id === chatId);
            if (chat) {
                this.currentChatPersonality = chat.personality;
                const titleEl = document.getElementById('chatTitle');
                if (titleEl) titleEl.textContent = chat.title;
            }

            this.updateContextPanel();
            this.renderChatList();
        } catch (e) {
            console.error('Switch chat error:', e);
            this.showWelcomeState();
        }
    }

    showWelcomeState() {
        const container = document.getElementById('messages');
        if (!container) return;

        const prompts = [
            { icon: '📊', title: 'Analyze Data', desc: 'Upload CSV/Excel for insights', prompt: 'Analyze this dataset and create visualizations' },
            { icon: '📝', title: 'Write Content', desc: 'Documents, emails, proposals', prompt: 'Help me write a professional project proposal' },
            { icon: '💻', title: 'Code Assistant', desc: 'Review, debug, optimize', prompt: 'Debug this code and explain the issues' },
            { icon: '🔍', title: 'Research', desc: 'Deep analysis & summaries', prompt: 'Research the latest trends and summarize findings' }
        ];

        container.innerHTML = `<div class="welcome-state">
            <div class="welcome-logo">
                <div class="iris-logo-container iris-logo-xl"></div>
            </div>
            <div class="welcome-text">
                <h1 class="welcome-title">How can I help you today?</h1>
                <p class="welcome-subtitle">
                    I'm IRIS, your AI assistant with advanced document understanding,
                    voice interaction, and persistent memory.
                </p>
            </div>
            <div class="quick-actions">
                ${prompts.map(p => `
                    <div class="quick-action-card" onclick="app.sendQuickMessage('${this.escapeHtml(p.prompt)}')">
                        <div class="quick-action-icon">${p.icon}</div>
                        <div class="quick-action-title">${this.escapeHtml(p.title)}</div>
                        <div class="quick-action-desc">${this.escapeHtml(p.desc)}</div>
                    </div>
                `).join('')}
            </div>
        </div>`;

        this.renderLogo();

        const titleEl = document.getElementById('chatTitle');
        if (titleEl) titleEl.textContent = 'New Chat';
    }

    async createNewChat(options = {}) {
        try {
            const data = await this.secureFetch('/api/chats', {
                method: 'POST',
                body: {
                    personality: this.currentUser?.personality || 'default',
                    title: options.title || 'New Chat',
                    is_temporary: options.temporary || false,
                    project_id: options.project_id
                }
            });

            if (data?.success) {
                await this.loadChats();
                await this.switchToChat(data.chat.id);
                this.showToast('New conversation started', 'success');
            }
        } catch (e) {
            console.error('Create chat error:', e);
            this.showToast('Failed to create chat', 'error');
        }
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        if (!input || !this.currentChat) return;

        const text = input.value.trim();
        if (!text || this.isTyping) return;

        // Handle slash commands
        if (text.startsWith('/')) {
            const handled = await this.handleSlashCommand(text);
            if (handled) {
                input.value = '';
                input.style.height = 'auto';
                return;
            }
        }

        input.value = '';
        input.style.height = 'auto';
        this.isTyping = true;

        const container = document.getElementById('messages');
        const welcomeState = container.querySelector('.welcome-state');
        if (welcomeState) welcomeState.remove();

        const userMsg = {
            id: 'msg-' + Date.now(),
            content: text,
            sender: 'user',
            timestamp: new Date().toISOString(),
            reply_to: this.replyingTo
        };

        container.insertAdjacentHTML('beforeend', this.renderMessage(userMsg));
        this.messages.push(userMsg);
        this.scrollToBottom();

        this.replyingTo = null;
        this.hideReplyPreview();
        this.showTypingIndicator();

        try {
            const data = await this.secureFetch(`/api/chats/${this.currentChat}/messages`, {
                method: 'POST',
                body: {
                    content: text,
                    reply_to: userMsg.reply_to
                }
            });

            this.hideTypingIndicator();

            if (data?.success && data.ai_response) {
                const aiMsg = {
                    id: 'ai-' + Date.now(),
                    content: data.ai_response.response,
                    sender: 'iris',
                    timestamp: new Date().toISOString(),
                    model: data.ai_response.model,
                    confidence_score: data.ai_response.confidence
                };

                container.insertAdjacentHTML('beforeend', this.renderMessage(aiMsg));
                this.messages.push(aiMsg);

                if (typeof hljs !== 'undefined') {
                    hljs.highlightAll();
                    this.addCopyButtonsToCodeBlocks();   // <-- ADD THIS LINE
                }

                if (data.ai_response.new_facts && data.ai_response.new_facts.length > 0) {
                    data.ai_response.new_facts.forEach(fact => {
                        this.showToast(`New fact learned: ${fact.fact}`, 'info');
                    });
                }

                if (this.currentUser?.voice_enabled && data.ai_response.response) {
                    this.speakText(data.ai_response.response);
                }

                this.scrollToBottom();
                await this.loadChats();
                this.updateContextPanel();
            }
        } catch (e) {
            this.hideTypingIndicator();
            if (e.message.includes('503')) {
                this.showToast('Voice not available. Install edge-tts and pyaudio.', 'warning');
            } else {
                this.showToast('Failed to send message', 'error');
            }
            console.error('Send message error:', e);
        } finally {
            this.isTyping = false;
        }
    }

    // ==========================================
    // CODE BLOCK COPY BUTTON
    // ==========================================
    addCopyButtonsToCodeBlocks() {
        document.querySelectorAll('pre code').forEach((codeBlock) => {
            // Avoid duplicates
            if (codeBlock.parentNode.querySelector('.copy-code-button')) return;

            const button = document.createElement('button');
            button.className = 'copy-code-button';
            button.innerHTML = '📋';
            button.title = 'Copy code';
            button.onclick = (e) => {
                e.stopPropagation();
                const code = codeBlock.innerText;
                navigator.clipboard.writeText(code).then(() => {
                    this.showToast('Code copied!', 'success');
                }).catch(() => {
                    this.showToast('Failed to copy', 'error');
                });
            };
            codeBlock.parentNode.style.position = 'relative';
            codeBlock.parentNode.appendChild(button);
        });
    }

    // New slash command handler
    async handleSlashCommand(text) {
        const parts = text.split(' ');
        const command = parts[0].toLowerCase();
        const args = parts.slice(1);

        // Email command (creator only)
if (command === '/email') {
    if (args.length === 0) {
        this.showToast('Usage: /email <report_type> [schedule] [format] or /email <custom message>', 'warning');
        // Optionally show available reports
        if (this.availableReports) {
            this.showToast('Available reports: ' + this.availableReports.join(', '), 'info');
        }
        return true;
    }

    // Define available reports (could be fetched from server)
    const reportTypes = this.availableReports || [
        'system_health', 'error_logs', 'performance_metrics', 'trading_activity',
        'portfolio_snapshot', 'security_log', 'database_backup', 'api_usage',
        'model_usage', 'system_update', 'weekly_intelligence', 'file_changes',
        'autonomous_actions'
    ];

    const firstArg = args[0].toLowerCase();
    let reportType = null;
    let schedule = 'now';
    let format = 'txt';
    let customMessage = '';

    // Check if it's a known report type
    if (reportTypes.includes(firstArg)) {
        reportType = firstArg;
        // Parse remaining arguments for schedule and format
        let i = 1;
        while (i < args.length) {
            if (args[i] === 'in' || args[i] === 'at') {
                // Schedule phrase: "in 10 minutes" or "at 14:30"
                schedule = args.slice(i).join(' ');
                break;
            } else if (args[i] === 'format' && i+1 < args.length) {
                format = args[i+1].toLowerCase();
                i += 2;
            } else {
                // If we encounter something else, treat as part of custom message? No, we'll stop.
                break;
            }
        }
    } else {
        // No report type, treat whole thing as custom message
        customMessage = args.join(' ');
    }

    // If it's a custom message, use the old email endpoint
    if (!reportType) {
        this.secureFetch('/api/creator/send_email', {
            method: 'POST',
            body: { subject: 'User message', body: customMessage }
        }).then(() => {
            this.showToast('Email sent!', 'success');
        }).catch(e => {
            this.showToast('Email failed: ' + (e.message || 'Unknown error'), 'error');
        });
        return true;
    }

    // Send report request
    this.secureFetch('/api/user/send_report', {
        method: 'POST',
        body: { report_type: reportType, schedule: schedule, format: format }
    }).then(data => {
        if (data.success) {
            let msg = data.message;
            if (data.download_url) {
                msg += ` Download: ${data.download_url}`;
            }
            this.showToast(msg, 'success');
        } else {
            this.showToast('Report failed: ' + (data.error || 'Unknown error'), 'error');
        }
    }).catch(e => {
        this.showToast('Report request failed: ' + e.message, 'error');
    });
    return true;
}

        // Remind command (creator only)
        if (command === '/remind' && this.currentUser?.role === 'creator') {
            // Format: /remind in 10 minutes "message"
            // For simplicity, we'll just parse as "in X minutes"
            if (args[0] !== 'in' || args.length < 3) {
                this.showToast('Usage: /remind in <minutes> <message>', 'warning');
                return true;
            }
            const minutes = parseInt(args[1]);
            if (isNaN(minutes)) {
                this.showToast('Invalid time', 'error');
                return true;
            }
            const message = args.slice(3).join(' ') || 'Reminder';
            const executeAt = new Date(Date.now() + minutes * 60000).toISOString();
            try {
                await this.secureFetch('/api/creator/schedule_task', {
                    method: 'POST',
                    body: {
                        task_type: 'email',
                        execute_at: executeAt,
                        data: { body: message }
                    }
                });
                this.showToast(`Reminder set for ${minutes} minutes from now`, 'success');
                return true;
            } catch (e) {
                this.showToast('Failed to set reminder', 'error');
                return true;
            }
        }

        return false; // let normal processing handle
    }

    // ==========================================
    // MESSAGE FEATURES
    // ==========================================

    async toggleReaction(messageId, emoji) {
        try {
            const data = await this.secureFetch(`/api/messages/${messageId}/reactions`, {
                method: 'POST',
                body: { emoji }
            });

            if (data?.success) {
                const msg = this.messages.find(m => m.id === messageId);
                if (msg) {
                    msg.reactions = data.reactions;
                    this.refreshMessage(messageId);
                }
            }
        } catch (e) {
            console.error('Reaction error:', e);
        }
    }

    addReaction(messageId, event) {
        this.currentReactionMessageId = messageId;
        this.showEmojiPicker(event);
    }

    showEmojiPicker(event) {
        const emojis = ['👍', '❤️', '😂', '😮', '🎉', '👏', '🔥', '💯', '✅', '❌', '⭐', '🤔'];
        const picker = document.createElement('div');
        picker.className = 'emoji-picker';
        picker.innerHTML = emojis.map(e => `<span onclick="app.toggleReaction('${this.currentReactionMessageId}', '${e}')">${e}</span>`).join('');
        const btn = event.target;
        btn.parentElement.appendChild(picker);
        setTimeout(() => picker.remove(), 3000);
    }

    replyToMessage(messageId) {
        this.replyingTo = messageId;
        const msg = this.messages.find(m => m.id === messageId);
        if (msg) {
            this.showReplyPreview(msg);
            document.getElementById('messageInput')?.focus();
        }
    }

    showReplyPreview(message) {
        let preview = document.getElementById('replyPreview');
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'replyPreview';
            preview.className = 'message-reply-preview';
            const inputContainer = document.querySelector('.input-container');
            if (inputContainer) {
                inputContainer.insertBefore(preview, inputContainer.firstChild);
            }
        }

        preview.innerHTML = `
            ↩️ Replying to: ${this.escapeHtml(message.content.substring(0, 50))}...
            <button onclick="app.cancelReply()" style="margin-left: auto; background: none; border: none; cursor: pointer;">✕</button>
        `;
        preview.style.display = 'flex';
    }

    hideReplyPreview() {
        const preview = document.getElementById('replyPreview');
        if (preview) preview.style.display = 'none';
    }

    cancelReply() {
        this.replyingTo = null;
        this.hideReplyPreview();
    }

    async copyMessage(messageId) {
        const msg = this.messages.find(m => m.id === messageId);
        if (msg && navigator.clipboard) {
            try {
                await navigator.clipboard.writeText(msg.content);
                this.showToast('Copied to clipboard', 'success');
            } catch (e) {
                this.showToast('Failed to copy', 'error');
            }
        }
    }

    async editMessage(messageId) {
        const msg = this.messages.find(m => m.id === messageId);
        if (!msg || msg.sender !== 'user') return;

        const newContent = prompt('Edit message:', msg.content);
        if (newContent && newContent !== msg.content) {
            try {
                const data = await this.secureFetch(`/api/messages/${messageId}`, {
                    method: 'PUT',
                    body: { content: newContent }
                });

                if (data?.success) {
                    msg.content = newContent;
                    msg.is_edited = true;
                    this.refreshMessage(messageId);
                }
            } catch (e) {
                this.showToast('Failed to edit message', 'error');
            }
        }
    }

    async retryMessage(messageId) {
        const msg = this.messages.find(m => m.id === messageId);
        if (!msg) return;

        let userMsgId = messageId;
        if (msg.sender === 'iris') {
            const index = this.messages.findIndex(m => m.id === messageId);
            for (let i = index - 1; i >= 0; i--) {
                if (this.messages[i].sender === 'user') {
                    userMsgId = this.messages[i].id;
                    break;
                }
            }
        }
        const userMsg = this.messages.find(m => m.id === userMsgId);
        if (!userMsg || userMsg.sender !== 'user') return;

        const input = document.getElementById('messageInput');
        input.value = userMsg.content;
        this.autoResize(input);
        this.sendMessage();
    }

    refreshMessage(messageId) {
        const el = document.getElementById(`msg-${messageId}`);
        const msg = this.messages.find(m => m.id === messageId);
        if (el && msg) {
            el.outerHTML = this.renderMessage(msg);
        }
    }

    scrollToMessage(messageId) {
        const el = document.getElementById(`msg-${messageId}`);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            el.style.animation = 'pulse 1s';
            setTimeout(() => el.style.animation = '', 1000);
        }
    }

    // ==========================================
    // VOICE FEATURES
    // ==========================================

    async toggleMic() {
        const btn = document.getElementById('micBtn');
        const waveform = document.getElementById('voiceWaveform');

        if (this.isRecording) {
            this.stopRecording();
            return;
        }

        this.isRecording = true;
        btn?.classList.add('recording');

        if (waveform) {
            waveform.style.display = 'flex';
            this.startWaveformAnimation(waveform);
        }

        try {
            const data = await this.secureFetch('/api/voice/listen', { method: 'POST' });

            if (data?.success && data.text) {
                const input = document.getElementById('messageInput');
                if (input) {
                    input.value = data.text;
                    this.autoResize(input);
                }

                if (data.detected_tone) {
                    this.showToast(`Detected tone: ${data.detected_tone}`, 'info');
                }

                setTimeout(() => this.sendMessage(), 500);
            }
        } catch (e) {
            if (e.message.includes('503')) {
                this.showToast('Voice not available. Install edge-tts and pyaudio.', 'warning');
            } else {
                this.showToast('Voice input unavailable', 'warning');
            }
        } finally {
            this.stopRecording();
        }
    }

    stopRecording() {
        this.isRecording = false;
        const btn = document.getElementById('micBtn');
        const waveform = document.getElementById('voiceWaveform');

        if (btn) btn.classList.remove('recording');
        if (waveform) {
            waveform.style.display = 'none';
            this.stopWaveformAnimation();
        }
    }

    startWaveformAnimation(container) {
        container.innerHTML = Array(10).fill(0).map(() =>
            `<div class="waveform-bar" style="height: ${Math.random() * 20 + 4}px"></div>`
        ).join('');

        this.voiceWaveformInterval = setInterval(() => {
            const bars = container.querySelectorAll('.waveform-bar');
            bars.forEach(bar => {
                bar.style.height = `${Math.random() * 20 + 4}px`;
            });
        }, 100);
    }

    stopWaveformAnimation() {
        if (this.voiceWaveformInterval) {
            clearInterval(this.voiceWaveformInterval);
            this.voiceWaveformInterval = null;
        }
    }

    async speakText(text) {
        if (!this.currentUser?.voice_enabled) return;

        try {
            await this.secureFetch('/api/voice/speak', {
                method: 'POST',
                body: {
                    text: text.substring(0, 500),
                    profile: this.currentUser.voice_profile,
                    mood: 'neutral'
                }
            });
        } catch (e) {
            console.error('Speech failed:', e);
        }
    }

    // ==========================================
    // LIVE MODE
    // ==========================================

    toggleLive() {
        const liveBtn = document.getElementById('liveBtn');
        if (this.liveMode) {
            this.liveMode = false;
            liveBtn.classList.remove('active');
            document.body.classList.remove('live-mode');
            this.updateHologramForLive(false);
            if (this.isRecording) this.stopRecording();
            this.showToast('Live mode ended', 'info');
        } else {
            this.liveMode = true;
            liveBtn.classList.add('active');
            document.body.classList.add('live-mode');
            this.updateHologramForLive(true);
            setTimeout(() => {
                if (this.liveMode) this.toggleMic();
            }, 500);
            this.showToast('Live mode activated', 'success');
        }
    }

    // ==========================================
    // COMMAND PALETTE
    // ==========================================

    setupCommandPalette() {
        this.commandPalette = document.getElementById('commandPalette');
        this.commandInput = document.getElementById('commandInput');
        this.commandList = document.getElementById('commandList');
        this.commandOverlay = document.getElementById('commandPaletteOverlay');

        this.loadCommands();
    }

    async loadCommands() {
        try {
            const data = await this.secureFetch('/api/commands');
            if (data?.success) {
                this.allCommands = data.commands.map(cmd => ({
                    id: cmd.command.replace('/', ''),
                    title: cmd.command,
                    desc: cmd.description,
                    icon: this.getCommandIcon(cmd.category),
                    category: cmd.category,
                    action: () => this.executeCommand(cmd.command)
                }));
            } else {
                throw new Error('No commands');
            }
        } catch (e) {
            this.allCommands = [
                { id: 'new-chat', title: '/new', desc: 'Start new conversation', icon: '💬', action: () => this.createNewChat() },
                { id: 'focus-mode', title: '/focus', desc: 'Toggle focus mode', icon: '🎯', action: () => this.toggleFocusMode() },
                { id: 'settings', title: 'Settings', desc: 'Open settings panel', icon: '⚙️', action: () => toggleSettingsPanel() },
                { id: 'clear', title: '/clear', desc: 'Clear conversation', icon: '🧹', action: () => this.clearCurrentChat() },
                { id: 'export', title: '/export', desc: 'Export conversation', icon: '📤', action: () => this.exportCurrentChat() },
                { id: 'import', title: '/import', desc: 'Import conversation', icon: '📥', action: () => document.getElementById('importFile').click() },
                { id: 'theme', title: '/theme', desc: 'Change theme', icon: '🎨', action: () => this.openThemeSelector() },
                { id: 'model', title: '/model', desc: 'Change AI model', icon: '🤖', action: () => this.openModelSelector() },
                { id: 'persona', title: '/persona', desc: 'Change personality', icon: '🧑', action: () => this.openPersonalitySelector() },
                { id: 'system', title: '/system', desc: 'Show system info', icon: '💻', action: () => this.openSystemPanel() },
                { id: 'maflex', title: '/maflex', desc: 'Enter Maflex mode', icon: '⚡', action: () => enterMaflex() },
                { id: 'email', title: '/email', desc: 'Send email (creator)', icon: '📧', action: () => this.executeCommand('/email ') },
                { id: 'remind', title: '/remind', desc: 'Set reminder (creator)', icon: '⏰', action: () => this.executeCommand('/remind in ') }
            ];
        }
        this.filteredCommands = this.allCommands;
    }

    getCommandIcon(category) {
        const icons = {
            'General': '⚙️',
            'System': '🔧',
            'UI': '🎨',
            'Data': '📊',
            'Memory': '🧠',
            'AI': '🤖',
            'Voice': '🎙️',
            'Privacy': '🔒'
        };
        return icons[category] || '⚡';
    }

    openCommandPalette() {
        this.commandPaletteOpen = true;
        this.commandPalette?.classList.add('open');
        this.commandOverlay?.classList.add('open');
        if (this.commandInput) {
            this.commandInput.value = '';
            this.commandInput.focus();
        }
        this.filteredCommands = this.allCommands;
        this.commandSelectedIndex = 0;
        this.renderCommands(this.filteredCommands);
    }

    closeCommandPalette() {
        this.commandPaletteOpen = false;
        this.commandPalette?.classList.remove('open');
        this.commandOverlay?.classList.remove('open');
    }

    filterCommands(query) {
        this.filteredCommands = fuzzySearch(query, this.allCommands, ['title', 'desc']);
        this.commandSelectedIndex = 0;
        this.renderCommands(this.filteredCommands);
    }

    renderCommands(commands) {
        if (!this.commandList) return;

        this.commandList.innerHTML = commands.map((cmd, index) => `
            <div class="command-item ${index === this.commandSelectedIndex ? 'selected' : ''}" 
                 onclick="app.executeCommandById('${cmd.id}')"
                 data-index="${index}">
                <div class="command-item-icon">${cmd.icon}</div>
                <div class="command-item-content">
                    <div class="command-item-title">${this.escapeHtml(cmd.title)}</div>
                    <div class="command-item-desc">${this.escapeHtml(cmd.desc)}</div>
                </div>
            </div>
        `).join('');
    }

    navigateCommandList(direction) {
        if (this.filteredCommands.length === 0) return;
        this.commandSelectedIndex = (this.commandSelectedIndex + direction + this.filteredCommands.length) % this.filteredCommands.length;
        this.renderCommands(this.filteredCommands);
        const selected = this.commandList.querySelector(`[data-index="${this.commandSelectedIndex}"]`);
        if (selected) selected.scrollIntoView({ block: 'nearest' });
    }

    executeSelectedCommand() {
        if (this.filteredCommands.length > 0 && this.commandSelectedIndex >= 0) {
            const cmd = this.filteredCommands[this.commandSelectedIndex];
            cmd.action();
            this.closeCommandPalette();
        }
    }

    executeCommandById(commandId) {
        const cmd = this.allCommands.find(c => c.id === commandId);
        if (cmd) {
            cmd.action();
            this.closeCommandPalette();
        }
    }

    executeCommand(command) {
        const input = document.getElementById('messageInput');
        if (input) {
            input.value = command;
            this.sendMessage();
        }
        this.closeCommandPalette();
    }

    openThemeSelector() {
        this.closeCommandPalette();
        toggleSettingsPanel();
        setTimeout(() => document.querySelector('.theme-grid')?.scrollIntoView({ behavior: 'smooth' }), 300);
    }

    openModelSelector() {
        this.closeCommandPalette();
        toggleSettingsPanel();
        setTimeout(() => document.getElementById('modelSelect')?.scrollIntoView({ behavior: 'smooth' }), 300);
    }

    openPersonalitySelector() {
        this.closeCommandPalette();
        toggleSettingsPanel();
        setTimeout(() => document.getElementById('personalityGrid')?.scrollIntoView({ behavior: 'smooth' }), 300);
    }

    openSystemPanel() {
        this.closeCommandPalette();
        toggleSystemPanel();
    }

    // ==========================================
    // SETTINGS & CONFIGURATION
    // ==========================================

    populateSettings() {
        const themeGrid = document.getElementById('themeGrid');
        if (themeGrid) {
            themeGrid.innerHTML = Object.entries(this.themes).map(([key, theme]) => `
                <div class="theme-card ${this.currentUser?.theme === key ? 'active' : ''}" onclick="app.setTheme('${key}')">
                    <div class="theme-preview" style="background: ${theme.bg}; ${theme.type === 'light' ? 'border-color: #e2e8f0;' : ''}"></div>
                    <div class="theme-name">${this.escapeHtml(theme.name)}</div>
                </div>
            `).join('');
        }

        // Show/hide admin tab based on role
        const adminTab = document.querySelector('[data-tab="admin"]');
        if (adminTab) {
            adminTab.style.display = this.currentUser?.role === 'creator' ? 'flex' : 'none';
        }

        const persGrid = document.getElementById('personalityGrid');
        if (persGrid) {
            persGrid.innerHTML = Object.entries(this.personalities).map(([key, p]) => `
                <div class="personality-card ${this.currentUser?.personality === key ? 'active' : ''}" onclick="app.setPersonality('${key}')">
                    <div class="personality-icon">${p.icon}</div>
                    <div class="personality-info">
                        <div class="personality-name">${this.escapeHtml(p.name)}</div>
                        <div class="personality-desc">${this.escapeHtml(p.desc)}</div>
                    </div>
                </div>
            `).join('');
        }

        const voiceToggle = document.getElementById('voiceToggle');
        if (voiceToggle) {
            voiceToggle.checked = this.currentUser?.voice_enabled || false;
        }

        const voiceProfileSelect = document.getElementById('voiceProfile');
        if (voiceProfileSelect) {
            voiceProfileSelect.innerHTML = Object.entries(this.voices).map(([key, v]) => `
                <option value="${key}" ${this.currentUser?.voice_profile === key ? 'selected' : ''}>${v.name}</option>
            `).join('');
            voiceProfileSelect.onchange = (e) => this.setVoiceProfile(e.target.value);
        }

        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect) {
            modelSelect.innerHTML = Object.entries(this.models).map(([key, desc]) => `
                <option value="${key}" ${this.currentUser?.model === key ? 'selected' : ''}>${desc}</option>
            `).join('');
            modelSelect.onchange = (e) => this.setModel(e.target.value);
        }

        const reasoningSelect = document.getElementById('reasoningSelect');
        if (reasoningSelect && this.reasoningModes) {
            reasoningSelect.innerHTML = Object.entries(this.reasoningModes).map(([key, mode]) => `
                <option value="${key}" ${this.currentUser?.reasoning_mode === key ? 'selected' : ''}>${mode.name}</option>
            `).join('');
            reasoningSelect.onchange = (e) => this.setReasoningMode(e.target.value);
        }

        const usernameInput = document.getElementById('usernameInput');
        if (usernameInput) {
            usernameInput.value = this.currentUser?.username || '';
            usernameInput.onchange = (e) => this.setUsername(e.target.value);
        }

        const avatarPreview = document.getElementById('avatarPreview');
        if (avatarPreview && this.currentUser?.avatar_url) {
            avatarPreview.src = this.currentUser.avatar_url;
        }
    }

    async setTheme(themeKey) {
        try {
            this.currentUser.theme = themeKey;
            this.applyTheme(themeKey);

            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { theme: themeKey }
            });

            this.populateSettings();
            this.showToast(`Theme: ${this.themes[themeKey]?.name}`, 'success');
        } catch (e) {
            console.error('Set theme error:', e);
        }
    }

    applyTheme(themeKey) {
        document.documentElement.setAttribute('data-theme', themeKey);

        if (themeKey === 'auto') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'midnight' : 'light');
        }
    }

    async setPersonality(key) {
        try {
            this.currentUser.personality = key;

            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { personality: key }
            });

            this.populateSettings();
            this.showToast(`Mode: ${this.personalities[key]?.name}`, 'success');
        } catch (e) {
            console.error('Set personality error:', e);
        }
    }

    async setModel(modelKey) {
        try {
            this.currentUser.model = modelKey;
            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { model: modelKey }
            });
            this.showToast(`Model: ${this.models[modelKey]}`, 'success');
            this.updateContextPanel();
        } catch (e) {
            console.error('Set model error:', e);
        }
    }

    async setReasoningMode(modeKey) {
        try {
            this.currentUser.reasoning_mode = modeKey;
            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { reasoning_mode: modeKey }
            });
            this.showToast(`Reasoning mode: ${this.reasoningModes[modeKey]?.name}`, 'success');
        } catch (e) {
            console.error('Set reasoning mode error:', e);
        }
    }

    async setVoiceProfile(profile) {
        try {
            this.currentUser.voice_profile = profile;
            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { voice_profile: profile }
            });
            this.showToast(`Voice profile: ${this.voices[profile]?.name}`, 'success');
        } catch (e) {
            console.error('Set voice profile error:', e);
        }
    }

    async toggleVoiceSetting() {
        try {
            const enabled = !this.currentUser?.voice_enabled;
            this.currentUser.voice_enabled = enabled;

            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { voice_enabled: enabled }
            });

            this.populateSettings();
            this.showToast(enabled ? 'Voice enabled' : 'Voice disabled', 'success');
        } catch (e) {
            console.error('Toggle voice error:', e);
        }
    }

    async setUsername(username) {
        if (!username.trim()) return;
        try {
            this.currentUser.username = username;
            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { username: username }
            });
            this.updateUIForUser();
            this.showToast('Username updated', 'success');
        } catch (e) {
            console.error('Set username error:', e);
        }
    }

    async uploadAvatar(file) {
        if (!file) return;
        const formData = new FormData();
        formData.append('avatar', file);

        try {
            const response = await fetch('/api/user/avatar', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken || ''
                },
                body: formData
            });
            const data = await response.json();
            if (data.success) {
                this.currentUser.avatar_url = data.avatar_url;
                this.updateUIForUser();
                this.populateSettings();
                this.showToast('Avatar updated', 'success');
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (e) {
            console.error('Avatar upload error:', e);
            this.showToast('Avatar upload failed', 'error');
        }
    }

    async toggleFocusMode(force = null) {
        this.focusMode = force !== null ? force : !this.focusMode;
        document.body.classList.toggle('focus-mode', this.focusMode);

        try {
            await this.secureFetch('/api/user/settings', {
                method: 'PUT',
                body: { focus_mode: this.focusMode }
            });

            if (this.focusMode) this.showToast('Focus mode enabled', 'success');
        } catch (e) {
            console.error('Toggle focus mode error:', e);
        }
    }

    // ==========================================
    // RIGHT PANEL
    // ==========================================

    switchPanelTab(tab) {
        this.currentPanelTab = tab;

        document.querySelectorAll('.panel-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });

        document.querySelectorAll('.panel-content-section').forEach(s => {
            s.classList.toggle('hidden', s.dataset.section !== tab);
        });

        if (tab === 'memory') {
            this.loadMemoryPanel();
        } else if (tab === 'system') {
            this.loadSystemPanel();
        } else if (tab === 'context') {
            this.loadContextPanel();
        } else if (tab === 'games') {
            console.log('Games tab activated');
        } else if (tab === 'admin') {
            if (this.currentUser?.role === 'creator') {
                this.loadUserList();
            } else {
                document.querySelector('[data-tab="admin"]').style.display = 'none';
            }
        }
    }

    async updateContextPanel() {
        if (this.currentPanelTab !== 'context') return;

        const chat = this.chats.find(c => c.id === this.currentChat);
        if (chat) {
            const titleEl = document.getElementById('contextChatTitle');
            const countEl = document.getElementById('contextMessageCount');
            if (titleEl) titleEl.textContent = chat.title;
            if (countEl) countEl.textContent = this.messages.length;
        }

        const modelNameEl = document.getElementById('activeModelName');
        const modelDescEl = document.getElementById('activeModelDesc');
        if (modelNameEl && this.currentUser?.model) {
            const modelKey = this.currentUser.model;
            const modelDesc = this.models[modelKey] || modelKey;
            modelNameEl.textContent = modelDesc;
        }
        if (modelDescEl) {
            modelDescEl.textContent = `${this.currentUser?.reasoning_mode || 'normal'} mode`;
        }
    }

    async loadContextPanel() {
        try {
            const data = await this.secureFetch('/api/documents');
            if (data?.success) {
                const recentFiles = data.documents.slice(0, 5);
                const container = document.getElementById('recentFiles');
                if (container) {
                    if (recentFiles.length === 0) {
                        container.innerHTML = '<div class="context-item-icon">📄</div><div style="font-size: 0.875rem; color: var(--iris-text-muted);">No files in this conversation</div>';
                    } else {
                        container.innerHTML = recentFiles.map(doc => `
                            <div class="context-item" onclick="app.viewDocument('${doc.id}')">
                                <div class="context-item-icon">📄</div>
                                <div>
                                    <div style="font-weight: 500;">${this.escapeHtml(doc.filename)}</div>
                                    <div style="font-size: 0.75rem; color: var(--iris-text-muted);">${doc.summary?.substring(0, 50)}...</div>
                                </div>
                            </div>
                        `).join('');
                    }
                }
            }
        } catch (e) {
            console.error('Load recent files error:', e);
        }
        this.updateContextPanel();
    }

    async loadMemoryPanel() {
        try {
            const statsData = await this.secureFetch('/api/memory');
            const graphData = await this.secureFetch('/api/memory/graph');
            await this.loadFacts();
            await this.loadPendingFacts();
            await this.loadTags();

            const summaryEl = document.getElementById('memorySummary');
            const statsEl = document.getElementById('memoryStats');

            if (statsData?.success) {
                if (summaryEl) summaryEl.textContent = statsData.summary || 'No memories yet';
                if (statsEl) {
                    statsEl.innerHTML = `
                        <div class="system-stats-grid">
                            <div class="stat-card"><div class="stat-value">${statsData.stats?.memories || 0}</div><div class="stat-label">Memories</div></div>
                            <div class="stat-card"><div class="stat-value">${statsData.stats?.facts || 0}</div><div class="stat-label">Facts</div></div>
                            <div class="stat-card"><div class="stat-value">${statsData.stats?.concept_links || 0}</div><div class="stat-label">Links</div></div>
                        </div>
                    `;
                }
            }

            const graphContainer = document.querySelector('.memory-graph-preview');
            if (graphContainer) {
                if (graphData?.success && graphData.graph && graphData.graph.nodes?.length > 0) {
                    graphContainer.innerHTML = '';
                    const nodes = new vis.DataSet(graphData.graph.nodes.map(n => ({ id: n.id, label: n.id, group: n.group })));
                    const edges = new vis.DataSet(graphData.graph.links.map(l => ({ from: l.source, to: l.target, value: l.value })));

                    const network = new vis.Network(graphContainer, { nodes, edges }, {
                        nodes: { shape: 'dot', size: 20, font: { size: 12, color: 'var(--iris-text)' } },
                        edges: { color: { color: 'var(--iris-primary)', highlight: 'var(--iris-accent)' }, arrows: 'to' },
                        physics: { enabled: true, solver: 'forceAtlas2Based' }
                    });
                } else {
                    graphContainer.innerHTML = '<div class="memory-graph-placeholder"><i class="fas fa-project-diagram" style="font-size: 2rem;"></i><span>No graph data available</span></div>';
                }
            }
        } catch (e) {
            console.error('Load memory panel error:', e);
        }
    }

    // ==========================================
    // MEMORY FACTS MANAGEMENT
    // ==========================================

    async loadFacts() {
        try {
            const data = await this.secureFetch('/api/memory/facts');
            if (data?.success) {
                this.facts = data.facts;
                this.renderFacts();
            }
        } catch (e) {
            console.error('Load facts error:', e);
        }
    }

    renderFacts() {
        const container = document.getElementById('memoryFactsList');
        if (!container) return;

        if (!this.facts || this.facts.length === 0) {
            container.innerHTML = '<div class="context-item"><div class="context-item-icon">📌</div><div>No facts yet. IRIS will learn automatically or you can add manually.</div></div>';
            return;
        }

        container.innerHTML = this.facts.map(fact => `
            <div class="context-item fact-item" data-fact-id="${fact.id}" style="flex-wrap: wrap;">
                <div class="context-item-icon">${fact.is_auto ? '🤖' : '📌'}</div>
                <div style="flex: 1; min-width: 0;">
                    <div class="fact-content" data-fact-id="${fact.id}">
                        <span class="fact-text">${this.escapeHtml(fact.fact)}</span>
                        <span class="fact-category badge">${fact.category}</span>
                        ${fact.tags.map(t => `<span class="badge tag-badge">${t}</span>`).join('')}
                        ${fact.shared ? '<span title="Shared with family">🌐</span>' : ''}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--iris-text-muted);">
                        confidence: ${fact.confidence} · ${fact.is_auto ? 'auto' : 'manual'} · ${fact.persistent ? 'permanent' : 'temporary'}
                    </div>
                    <div class="fact-edit-form" data-fact-id="${fact.id}" style="display: none; margin-top: 0.5rem;">
                        <input type="text" class="search-input fact-edit-input" value="${this.escapeHtml(fact.fact)}" style="width: 100%; margin-bottom: 0.25rem;">
                        <div style="display: flex; gap: 0.25rem;">
                            <input type="text" class="search-input fact-category-input" placeholder="Category" value="${fact.category}" style="flex: 1;">
                            <input type="text" class="search-input fact-tags-input" placeholder="Tags (comma-separated)" value="${fact.tags.join(', ')}" style="flex: 2;">
                        </div>
                        <div style="display: flex; gap: 0.25rem; margin-top: 0.25rem;">
                            <input type="number" class="search-input fact-confidence-input" step="0.1" min="0" max="1" value="${fact.confidence}" style="width: 80px;">
                            <label><input type="checkbox" class="fact-persistent-checkbox" ${fact.persistent ? 'checked' : ''}> Permanent</label>
                            <button class="btn btn-secondary save-fact-btn" data-id="${fact.id}">Save</button>
                            <button class="btn btn-ghost cancel-edit-btn" data-id="${fact.id}">Cancel</button>
                        </div>
                    </div>
                </div>
                <div class="message-actions" style="opacity: 1; margin-left: auto;">
                    <button class="message-action-btn edit-fact-btn" data-id="${fact.id}" title="Edit">✏️</button>
                    <button class="message-action-btn delete-fact-btn" data-id="${fact.id}" title="Delete">🗑️</button>
                </div>
            </div>
        `).join('');

        document.querySelectorAll('.edit-fact-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const factId = e.target.dataset.id;
                this.showFactEditForm(factId);
            });
        });
        document.querySelectorAll('.delete-fact-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const factId = e.target.dataset.id;
                this.deleteFact(factId);
            });
        });
        document.querySelectorAll('.save-fact-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const factId = e.target.dataset.id;
                this.saveFactEdit(factId);
            });
        });
        document.querySelectorAll('.cancel-edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const factId = e.target.dataset.id;
                this.hideFactEditForm(factId);
            });
        });
    }

    showFactEditForm(factId) {
        document.querySelectorAll('.fact-edit-form').forEach(f => f.style.display = 'none');
        const form = document.querySelector(`.fact-edit-form[data-fact-id="${factId}"]`);
        if (form) form.style.display = 'block';
    }

    hideFactEditForm(factId) {
        const form = document.querySelector(`.fact-edit-form[data-fact-id="${factId}"]`);
        if (form) form.style.display = 'none';
    }

    async saveFactEdit(factId) {
        const form = document.querySelector(`.fact-edit-form[data-fact-id="${factId}"]`);
        if (!form) return;
        const factInput = form.querySelector('.fact-edit-input');
        const categoryInput = form.querySelector('.fact-category-input');
        const tagsInput = form.querySelector('.fact-tags-input');
        const confidenceInput = form.querySelector('.fact-confidence-input');
        const persistentCheck = form.querySelector('.fact-persistent-checkbox');

        const newFact = factInput.value.trim();
        const newCategory = categoryInput.value.trim();
        const tags = tagsInput.value.split(',').map(t => t.trim()).filter(t => t);
        const newConfidence = parseFloat(confidenceInput.value);
        const persistent = persistentCheck.checked;

        if (!newFact) {
            this.showToast('Fact cannot be empty', 'error');
            return;
        }

        try {
            const data = await this.secureFetch(`/api/memory/facts/${factId}`, {
                method: 'PUT',
                body: { fact: newFact, confidence: newConfidence, category: newCategory, tags }
            });
            if (data?.success) {
                this.showToast('Fact updated', 'success');
                this.hideFactEditForm(factId);
                this.loadFacts();
            } else {
                throw new Error('Failed to update fact');
            }
        } catch (e) {
            this.showToast('Error updating fact', 'error');
            console.error(e);
        }
    }

    async addFact() {
        const subject = prompt('Subject (e.g., user, project, general):', 'user');
        if (!subject) return;
        const fact = prompt('Enter fact:');
        if (!fact) return;
        const category = prompt('Category (e.g., identity, like, dislike, project):', 'general');
        if (!category) return;
        const confidence = parseFloat(prompt('Confidence (0.0 to 1.0):', '1.0'));
        if (isNaN(confidence)) return;
        const persistent = confirm('Make this fact permanent? (OK = permanent, Cancel = temporary)');
        const tagsInput = prompt('Tags (comma-separated, optional):');
        const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(t => t) : [];

        try {
            const data = await this.secureFetch('/api/memory/facts', {
                method: 'POST',
                body: { subject, fact, category, confidence, persistent, tags }
            });
            if (data?.success) {
                this.showToast('Fact added', 'success');
                this.loadFacts();
                this.loadTags();
            } else {
                throw new Error('Failed to add fact');
            }
        } catch (e) {
            this.showToast('Error adding fact', 'error');
            console.error(e);
        }
    }

    async deleteFact(factId) {
        if (!confirm('Delete this fact?')) return;
        try {
            const data = await this.secureFetch(`/api/memory/facts/${factId}`, {
                method: 'DELETE'
            });
            if (data?.success) {
                this.showToast('Fact deleted', 'success');
                this.loadFacts();
            } else {
                throw new Error('Failed to delete fact');
            }
        } catch (e) {
            this.showToast('Error deleting fact', 'error');
            console.error(e);
        }
    }

    async loadTags() {
        try {
            const data = await this.secureFetch('/api/memory/facts/tags');
            if (data?.success) {
                this.allTags = data.tags;
                this.populateTagFilter();
            }
        } catch (e) {
            console.error('Load tags error:', e);
        }
    }

    populateTagFilter() {
        const select = document.getElementById('tagFilter');
        if (!select) return;
        select.innerHTML = '<option value="">All tags</option>' +
            this.allTags.map(t => `<option value="${t}">${t}</option>`).join('');
    }

    async filterFacts() {
        const searchInput = document.getElementById('factSearch');
        const categorySelect = document.getElementById('categoryFilter');
        const tagSelect = document.getElementById('tagFilter');
        const query = searchInput?.value || '';
        const category = categorySelect?.value || null;
        const tag = tagSelect?.value || null;

        try {
            const data = await this.secureFetch('/api/memory/facts/search', {
                method: 'POST',
                body: { query, category, tag }
            });
            if (data?.success) {
                this.facts = data.facts;
                this.renderFacts();
            }
        } catch (e) {
            console.error('Filter facts error:', e);
        }
    }

    async loadPendingFacts() {
        try {
            const data = await this.secureFetch('/api/memory/facts/pending');
            if (data?.success) {
                this.pendingFacts = data.facts;
                this.renderPendingFacts();
            }
        } catch (e) {
            console.error('Load pending facts error:', e);
        }
    }

    renderPendingFacts() {
        const container = document.getElementById('pendingFactsList');
        if (!container) return;

        if (!this.pendingFacts || this.pendingFacts.length === 0) {
            container.innerHTML = '<div class="context-item"><div class="context-item-icon">⏳</div><div>No pending confirmations.</div></div>';
            return;
        }

        container.innerHTML = this.pendingFacts.map(fact => `
            <div class="context-item" data-fact-id="${fact.id}" style="flex-wrap: wrap;">
                <div class="context-item-icon">🤖</div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 500;">${this.escapeHtml(fact.fact)}</div>
                    <div style="font-size: 0.75rem; color: var(--iris-text-muted);">
                        ${fact.category} · confidence: ${fact.confidence}
                    </div>
                </div>
                <div class="message-actions" style="opacity: 1; margin-left: auto;">
                    <button class="message-action-btn" onclick="app.confirmFact('${fact.id}')" title="Accept">✅</button>
                    <button class="message-action-btn" onclick="app.editFact('${fact.id}')" title="Edit">✏️</button>
                    <button class="message-action-btn" onclick="app.deleteFact('${fact.id}')" title="Reject">🗑️</button>
                </div>
            </div>
        `).join('');
    }

    async confirmFact(factId) {
        try {
            const data = await this.secureFetch(`/api/memory/facts/${factId}/confirm`, {
                method: 'POST'
            });
            if (data?.success) {
                this.showToast('Fact confirmed', 'success');
                this.loadFacts();
                this.loadPendingFacts();
            } else {
                throw new Error('Failed to confirm fact');
            }
        } catch (e) {
            this.showToast('Error confirming fact', 'error');
            console.error(e);
        }
    }

    async confirmAllPending() {
        if (!confirm('Confirm all pending facts?')) return;
        try {
            const data = await this.secureFetch('/api/memory/facts/confirm-all', {
                method: 'POST'
            });
            if (data?.success) {
                this.showToast(`${data.count} facts confirmed`, 'success');
                this.loadFacts();
                this.loadPendingFacts();
            } else {
                throw new Error('Failed to confirm all');
            }
        } catch (e) {
            this.showToast('Error confirming facts', 'error');
            console.error(e);
        }
    }

    async exportFacts() {
        try {
            const response = await fetch('/api/memory/facts/export', {
                headers: { 'X-CSRFToken': this.csrfToken || '' }
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'iris_facts.json';
            a.click();
            window.URL.revokeObjectURL(url);
            this.showToast('Facts exported', 'success');
        } catch (e) {
            console.error('Export error:', e);
            this.showToast('Export failed', 'error');
        }
    }

    async importFacts(input) {
        if (!input.files || input.files.length === 0) return;
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/api/memory/facts/import', {
                method: 'POST',
                headers: { 'X-CSRFToken': this.csrfToken || '' },
                body: formData
            });
            const data = await response.json();
            if (data.success) {
                this.showToast(`${data.count} facts imported`, 'success');
                this.loadFacts();
                this.loadPendingFacts();
            } else {
                throw new Error(data.error || 'Import failed');
            }
        } catch (e) {
            console.error('Import error:', e);
            this.showToast('Import failed', 'error');
        }
        input.value = '';
    }

    // ==========================================
    // SYSTEM PANEL
    // ==========================================

    async loadSystemPanel() {
        try {
            const data = await this.secureFetch('/api/system/status');

            if (data?.success && data.stats) {
                const stats = data.stats;
                const container = document.getElementById('systemStats');

                if (container) {
                    container.innerHTML = `
                        <div class="system-stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${stats.cpu !== undefined ? Math.round(stats.cpu) : '--'}%</div>
                                <div class="stat-label">CPU</div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${stats.cpu || 0}%"></div>
                                </div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${stats.ram !== undefined ? Math.round(stats.ram) : '--'}%</div>
                                <div class="stat-label">RAM</div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${stats.ram || 0}%"></div>
                                </div>
                            </div>
                        </div>
                        <div class="system-controls" style="margin-top: var(--space-lg);">
                            <h4 class="settings-section-title">Volume</h4>
                            <div style="display: flex; gap: var(--space-sm); align-items: center;">
                                <button class="btn btn-secondary" onclick="app.systemCommand('volume', 0)">🔇</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('volume', 25)">25%</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('volume', 50)">50%</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('volume', 75)">75%</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('volume', 100)">100%</button>
                            </div>
                            <h4 class="settings-section-title" style="margin-top: var(--space-md);">Brightness</h4>
                            <div style="display: flex; gap: var(--space-sm); align-items: center;">
                                <button class="btn btn-secondary" onclick="app.systemCommand('brightness', 0)">🌑</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('brightness', 25)">25%</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('brightness', 50)">50%</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('brightness', 75)">75%</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('brightness', 100)">100%</button>
                            </div>
                            <h4 class="settings-section-title" style="margin-top: var(--space-md);">Power</h4>
                            <div style="display: flex; gap: var(--space-sm);">
                                <button class="btn btn-secondary" onclick="app.systemCommand('restart')">🔄 Restart</button>
                                <button class="btn btn-secondary" onclick="app.systemCommand('shutdown')">⏻ Shutdown</button>
                            </div>
                        </div>
                    `;
                }
            }
        } catch (e) {
            console.error('Load system panel error:', e);
        }
    }

    // ==========================================
    // FILE UPLOAD
    // ==========================================

    setupDragAndDrop() {
        const wrapper = document.querySelector('.input-wrapper');
        const messages = document.getElementById('messages');

        if (!wrapper) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(e => {
            wrapper.addEventListener(e, (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
            });
            messages?.addEventListener(e, (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(e => {
            wrapper.addEventListener(e, () => wrapper.classList.add('drag-active'));
        });

        ['dragleave', 'drop'].forEach(e => {
            wrapper.addEventListener(e, () => wrapper.classList.remove('drag-active'));
        });

        wrapper.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length) this.handleFileUpload(files[0]);
        });

        document.addEventListener('paste', (e) => {
            const items = e.clipboardData.items;
            for (let item of items) {
                if (item.kind === 'file') {
                    this.handleFileUpload(item.getAsFile());
                    break;
                }
            }
        });
    }

    async handleFileUpload(file) {
        if (!this.currentChat) {
            this.showToast('Please select a conversation first', 'warning');
            return;
        }

        if (file.size > 50 * 1024 * 1024) {
            this.showToast('File too large (max 50MB)', 'error');
            return;
        }

        const ext = file.name.split('.').pop().toLowerCase();
        const allowedTypes = ['txt', 'md', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'py', 'js', 'html', 'css',
                           'json', 'csv', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'];

        if (!allowedTypes.includes(ext)) {
            this.showToast('File type not allowed', 'error');
            return;
        }

        this.showToast(`Uploading: ${this.escapeHtml(file.name)}...`, 'info');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('chat_id', this.currentChat);

        try {
            const response = await fetch('/api/documents',{
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken || ''
                },
                body: formData,
                credentials: 'include',   // <-- ADD THIS LINE
                signal: this.abortControllers.get('upload')?.signal
            });

            if (response.status === 429) {
                this.showToast('Rate limit exceeded. Please slow down.', 'warning');
                return;
            }

            const data = await response.json();

            if (data.success) {
    this.showToast(`Uploaded: ${data.document?.filename || file.name}`, 'success');
    if (data.chat_formatted) {
        // Add a system message to the chat
        const systemMsg = {
            id: 'sys-' + Date.now(),
            content: data.chat_formatted,
            sender: 'system',
            timestamp: new Date().toISOString()
        };
        document.getElementById('messages').insertAdjacentHTML('beforeend', this.renderMessage(systemMsg));
        this.messages.push(systemMsg);
        this.scrollToBottom();
    }
    await this.switchToChat(this.currentChat); // reloads messages
    this.loadContextPanel();
} else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (e) {
            if (e.name !== 'AbortError') {
                this.showToast('Upload failed', 'error');
                console.error('Upload error:', e);
            }
        }
    }

    // ==========================================
    // KEYBOARD SHORTCUTS
    // ==========================================

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                this.openCommandPalette();
            }

            if (e.key === 'Escape') {
                this.closeCommandPalette();
                closeAllPanels();
            }

            if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
                e.preventDefault();
                this.createNewChat();
            }

            if ((e.metaKey || e.ctrlKey) && e.key === ',') {
                e.preventDefault();
                toggleSettingsPanel();
            }

            if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'F') {
                e.preventDefault();
                this.toggleFocusMode();
            }

            if (this.commandPaletteOpen) {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.navigateCommandList(1);
                }
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.navigateCommandList(-1);
                }
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.executeSelectedCommand();
                }
            }
        });
    }

    // ==========================================
    // OFFLINE DETECTION
    // ==========================================

    setupOfflineDetection() {
        const updateOnlineStatus = () => {
            this.offline = !navigator.onLine;
            const banner = document.getElementById('offlineBanner');
            if (banner) {
                banner.classList.toggle('show', this.offline);
            }

            if (this.offline) {
                this.showToast('You are offline', 'warning');
            } else {
                this.showToast('Back online', 'success');
            }
        };

        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        updateOnlineStatus();
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================

setupEventListeners() {
    this.eventListeners = [];

    const input = document.getElementById('messageInput');
    if (input) {
        const handler = () => this.autoResize(input);
        input.addEventListener('input', handler);
        this.eventListeners.push({ element: input, type: 'input', handler });

        // Paste listener for long text
        input.addEventListener('paste', (e) => {
            setTimeout(async () => {
                const text = input.value;
                const PASTE_THRESHOLD = 2000;
                if (text.length > PASTE_THRESHOLD && this.currentChat) {
                    const shouldConvert = confirm(`You've pasted ${text.length} characters. Convert to a text document?`);
                    if (shouldConvert) {
                        const blob = new Blob([text], { type: 'text/plain' });
                        const file = new File([blob], 'pasted_text.txt', { type: 'text/plain' });
                        input.value = '';
                        this.autoResize(input);
                        await this.handleFileUpload(file);
                    }
                }
            }, 10);
        });
    }



    const resizeHandler = () => this.handleResize();
    window.addEventListener('resize', resizeHandler);
    this.eventListeners.push({ element: window, type: 'resize', handler: resizeHandler });

    window.addEventListener('beforeunload', () => this.cleanup());
}

    cleanup() {
        this.abortControllers.forEach(controller => controller.abort());
        this.abortControllers.clear();

        this.eventListeners?.forEach(({ element, type, handler }) => {
            element.removeEventListener(type, handler);
        });

        this.stopWaveformAnimation();
    }

    handleResize() {
        if (window.innerWidth < 768) {
            document.getElementById('sidebar')?.classList.add('collapsed');
        }
    }

    // ==========================================
    // UTILITY METHODS
    // ==========================================

    autoResize(textarea) {
        if (!textarea) return;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }

    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.innerHTML = `
            <span style="font-size: 1.25rem;">${icons[type]}</span>
            <span>${this.escapeHtml(message)}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    scrollToBottom() {
        const container = document.getElementById('messages');
        if (container) {
            container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
        }
    }

    isToday(date) {
        const d = new Date(date);
        return d.toDateString() === new Date().toDateString();
    }

    isYesterday(date) {
        const d = new Date(date);
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        return d.toDateString() === yesterday.toDateString();
    }

    updateUIForUser() {
        const userNameEl = document.getElementById('userName');
        const userAvatarEl = document.getElementById('userAvatar');
        const dangerZone = document.getElementById('dangerZoneSection');
        if (dangerZone) {
            dangerZone.style.display = this.currentUser?.role === 'creator' ? 'block' : 'none';
        }

        if (userNameEl) userNameEl.textContent = this.currentUser?.username || 'User';
        if (userAvatarEl) {
            if (this.currentUser?.avatar_url) {
                userAvatarEl.innerHTML = `<img src="${this.escapeHtml(this.currentUser.avatar_url)}" alt="Avatar">`;
            } else {
                userAvatarEl.textContent = (this.currentUser?.username || 'U').charAt(0).toUpperCase();
            }
            if (this.currentUser?.role === 'creator') {
                userAvatarEl.classList.add('creator-avatar');
                userAvatarEl.classList.add('creator-welcome');
            } else {
                userAvatarEl.classList.remove('creator-avatar', 'creator-welcome');
            }
        }
    }

    showTypingIndicator() {
        const container = document.getElementById('messages');
        if (!container) return;

        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'message iris';
        indicator.innerHTML = `
            <div class="message-avatar" style="background: var(--gradient-primary); color: white;">
                <div style="width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(indicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        document.getElementById('typing-indicator')?.remove();
    }

    sendQuickMessage(text) {
        const input = document.getElementById('messageInput');
        if (input) {
            input.value = text;
            input.focus();
            this.autoResize(input);
            setTimeout(() => this.sendMessage(), 100);
        }
    }

    // ==========================================
    // ADDITIONAL CHAT OPERATIONS
    // ==========================================

    async deleteChat(chatId) {
        if (!chatId) return;
        if (!confirm('Are you sure you want to delete this chat?')) return;

        try {
            const data = await this.secureFetch(`/api/chats/${chatId}`, {
                method: 'DELETE'
            });

            if (data?.success) {
                this.showToast('Chat deleted', 'success');
                await this.loadChats();
                if (this.chats.length > 0) {
                    await this.switchToChat(this.chats[0].id);
                } else {
                    this.currentChat = null;
                    this.showWelcomeState();
                }
            }
        } catch (e) {
            console.error('Delete chat error:', e);
            this.showToast('Failed to delete chat', 'error');
        }
    }

    async exportCurrentChat() {
        if (!this.currentChat) return;
        try {
            const response = await fetch(`/api/chats/${this.currentChat}/export?format=json`, {
                headers: {
                    'X-CSRFToken': this.csrfToken || ''
                }
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chat-${this.currentChat}.json`;
            a.click();
            window.URL.revokeObjectURL(url);
            this.showToast('Chat exported', 'success');
        } catch (e) {
            console.error('Export error:', e);
            this.showToast('Export failed', 'error');
        }
    }

    async clearCurrentChat() {
        if (!this.currentChat) return;
        const input = document.getElementById('messageInput');
        input.value = '/clear';
        await this.sendMessage();
    }

    async systemCommand(cmd, value = null) {
        try {
            if (cmd === 'screenshot') {
                const data = await this.secureFetch('/api/system/screenshot', { method: 'POST' });
                if (data?.success) this.showToast('Screenshot taken', 'success');
            } else if (cmd === 'lock') {
                await this.secureFetch('/api/system/lock', { method: 'POST' });
                this.showToast('System locked', 'success');
            } else if (cmd === 'volume') {
                await this.secureFetch('/api/system/volume', { method: 'POST', body: { level: value } });
                this.showToast(`Volume set to ${value}%`, 'success');
            } else if (cmd === 'brightness') {
                await this.secureFetch('/api/system/brightness', { method: 'POST', body: { level: value } });
                this.showToast(`Brightness set to ${value}%`, 'success');
            } else if (cmd === 'restart') {
                this.showToast('Restart not implemented (placeholder)', 'warning');
            } else if (cmd === 'shutdown') {
                this.showToast('Shutdown not implemented (placeholder)', 'warning');
            }
        } catch (e) {
            console.error('System command error:', e);
            this.showToast('Command failed', 'error');
        }
    }

    async viewDocument(docId) {
        this.openDocumentModal(docId);
    }

    openDocumentModal(docId) {
        this.currentDocId = docId;
        const overlay = document.getElementById('docModalOverlay');
        const titleEl = document.getElementById('docModalTitle');
        const contentEl = document.getElementById('docModalContent');
        const downloadBtn = document.getElementById('docModalDownload');

        contentEl.innerHTML = 'Loading...';
        overlay.classList.add('open');

        this.secureFetch(`/api/documents/${docId}`).then(data => {
            if (data?.success) {
                const doc = data.document;
                titleEl.textContent = doc.filename;
                contentEl.innerHTML = `<pre style="white-space: pre-wrap; word-wrap: break-word;">${this.escapeHtml(doc.content)}</pre>`;
                downloadBtn.onclick = () => this.downloadDocument(doc);
            } else {
                contentEl.innerHTML = '<p style="color: var(--iris-error);">Failed to load document.</p>';
            }
        }).catch(err => {
            contentEl.innerHTML = '<p style="color: var(--iris-error);">Error loading document.</p>';
            console.error(err);
        });
    }

    closeDocumentModal() {
        document.getElementById('docModalOverlay').classList.remove('open');
    }

    downloadDocument(doc) {
        const blob = new Blob([doc.content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = doc.filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    async importChat(input) {
        if (!input.files || input.files.length === 0) return;
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/chats/import', {
                method: 'POST',
                headers: { 'X-CSRFToken': this.csrfToken || '' },
                body: formData
            });
            const data = await response.json();
            if (data.success) {
                this.showToast('Chat imported successfully', 'success');
                await this.loadChats();
                await this.switchToChat(data.chat_id);
            } else {
                throw new Error(data.error || 'Import failed');
            }
        } catch (e) {
            console.error('Import error:', e);
            this.showToast('Import failed: ' + e.message, 'error');
        }
        input.value = '';
    }

    showChatContextMenu(event, chatId) {
        event.preventDefault();
        const action = confirm('Pin chat?');
        if (action) {
            this.showToast('Pin feature not yet implemented', 'info');
        }
    }

    // ==========================================
    // GAMES
    // ==========================================

    async startGame() {
        try {
            const data = await this.secureFetch('/api/games/start/medieval_rpg', { method: 'POST' });
            if (data.success) {
                document.getElementById('gameStatus').innerText = `Game started: ${data.state}`;
                document.getElementById('gameControls').style.display = 'block';
                document.getElementById('gameOutput').innerText = data.full_state;
                this.switchPanelTab('games');
            } else {
                this.showToast('Failed to start game: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (e) {
            console.error('Start game error:', e);
            this.showToast('Error starting game: ' + e.message, 'error');
        }
    }

    async sendGameCommand() {
        const input = document.getElementById('gameCommand');
        const cmd = input.value.trim();
        if (!cmd) return;
        input.value = '';
        const parts = cmd.split(' ');
        const action = parts[0];
        const args = parts.slice(1);
        try {
            const data = await this.secureFetch('/api/games/action', {
                method: 'POST',
                body: { action, args }
            });
            if (data.success) {
                document.getElementById('gameOutput').innerText = data.result + '\n\n' + data.state;
            } else {
                this.showToast('Command failed', 'error');
            }
        } catch (e) {
            console.error('Game command error:', e);
        }
    }

    async useGamePower(power) {
        const argsInput = prompt(`Enter arguments for ${power} (optional):`);
        const args = argsInput ? argsInput.split(' ') : [];
        try {
            const data = await this.secureFetch('/api/games/power', {
                method: 'POST',
                body: { power, args }
            });
            if (data.success) {
                document.getElementById('gameOutput').innerText = data.result + '\n\nEnergy: ' + data.energy;
            } else {
                this.showToast('Power failed', 'error');
            }
        } catch (e) {
            console.error('Use power error:', e);
        }
    }
}

// ============================================
// Hologram class
// ============================================
class Hologram {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.speaking = false;
        this.phase = 0;
        this.lastTimestamp = 0;
        this.live = false;
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }

    start() {
        this.animate();
    }

    setSpeaking(speaking) {
        this.speaking = speaking;
    }

    setLive(live) {
        this.live = live;
    }

    animate(timestamp) {
        if (this.canvas.width === 0 || this.canvas.height === 0) {
            requestAnimationFrame((t) => this.animate(t));
            return;
        }

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const baseRadius = Math.min(this.canvas.width, this.canvas.height) * 0.3;
        const time = performance.now() / 1000;
        const pulse = this.speaking ? 1.0 : 0.3;
        const radius = baseRadius + Math.sin(time * 5) * 15 * pulse;

        const gradient = this.ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius * 1.5);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.8)');
        gradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.4)');
        gradient.addColorStop(1, 'rgba(0, 212, 255, 0)');

        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        this.ctx.fillStyle = gradient;
        this.ctx.fill();

        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius * 0.7, 0, Math.PI * 2);
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        if (this.speaking) {
            for (let i = 0; i < 10; i++) {
                const angle = (i / 10) * Math.PI * 2 + time * 2;
                const x = centerX + Math.cos(angle) * radius * 1.2;
                const y = centerY + Math.sin(angle) * radius * 1.2;
                this.ctx.beginPath();
                this.ctx.arc(x, y, 3, 0, Math.PI * 2);
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                this.ctx.fill();
            }
        }

        if (this.live) {
            this.ctx.save();
            this.ctx.translate(centerX, centerY);
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(-radius * 0.3, 0, radius * 0.25, 0, Math.PI * 2);
            this.ctx.arc(radius * 0.3, 0, radius * 0.25, 0, Math.PI * 2);
            this.ctx.stroke();
            this.ctx.restore();
        }

        requestAnimationFrame((t) => this.animate(t));
    }
}

// ============================================
// Global initialization
// ============================================
const app = new IRISApp();

// Global Functions for HTML onclick handlers
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const slideToggle = document.querySelector('.slide-toggle');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        app.sidebarVisible = !sidebar.classList.contains('collapsed');
    }
    if (slideToggle) {
        slideToggle.classList.toggle('visible', !app.sidebarVisible);
    }
}

function toggleRightPanel() {
    const panel = document.getElementById('rightPanel');
    if (panel) {
        panel.classList.toggle('collapsed');
        app.rightPanelVisible = !panel.classList.contains('collapsed');
    }
}

function toggleSettingsPanel() {
    const panel = document.getElementById('settingsPanel');
    const isOpen = panel?.classList.toggle('open');
    panel?.setAttribute('aria-hidden', !isOpen);
        app.refreshModels();   // <-- ADD THIS

}

function enterMaflex() {
    window.location.href = '/maflex';
}

function toggleSystemPanel() {
    const panel = document.getElementById('systemPanel');
    const isOpen = panel?.classList.toggle('open');
    panel?.setAttribute('aria-hidden', !isOpen);
}

function closeAllPanels() {
    document.getElementById('settingsPanel')?.classList.remove('open');
    document.getElementById('systemPanel')?.classList.remove('open');
    document.querySelectorAll('.panel').forEach(p => p.setAttribute('aria-hidden', 'true'));
}

function closeDocModal() {
    app.closeDocumentModal();
}

function createNewChat() {
    app.createNewChat();
}

function sendMessage() {
    app.sendMessage();
}

function toggleMic() {
    app.toggleMic();
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        app.sendMessage();
    }
}

function autoResize(textarea) {
    app.autoResize(textarea);
}

function handleFileUpload(input) {
    if (input.files?.[0]) {
        app.handleFileUpload(input.files[0]);
    }
}

function searchChats() {
    app.renderChatList();
}

function switchPanelTab(tab) {
    app.switchPanelTab(tab);
}
