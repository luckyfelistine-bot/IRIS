// IRIS v8 Dashboard JavaScript
class IRISApp {
    constructor() {
        this.sessionId = localStorage.getItem('iris_session') || null;
        this.currentSection = 'chat';
        this.isListening = false;
        this.isStreaming = false;
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupChat();
        this.setupVoice();
        this.setupVision();
        this.setupPhone();
        this.setupCalendar();
        this.setupNotes();
        this.setupMath();
        this.setupProjects();
        this.setupSettings();
        this.loadStatus();
        this.startStatusPolling();
    }

    // Navigation
    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            });
        });
    }

    switchSection(section) {
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(`${section}-section`).classList.add('active');
        this.currentSection = section;

        const titles = {
            chat: 'Chat with IRIS',
            calendar: 'Aevibron Calendar',
            notes: 'Aevibron Notes',
            projects: 'Project Generator',
            phone: 'Phone Control',
            vision: 'Vision Stream',
            math: 'Aevibron Math',
            settings: 'Settings'
        };
        document.getElementById('page-title').textContent = titles[section] || 'IRIS';

        // Load section data
        if (section === 'calendar') this.loadCalendar();
        if (section === 'notes') this.loadNotes();
        if (section === 'projects') this.loadProjects();
        if (section === 'phone') this.loadPhoneData();
        if (section === 'settings') this.loadSettings();
    }

    // Chat
    setupChat() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendBtn.addEventListener('click', () => this.sendMessage());

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 150) + 'px';
        });
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;

        input.value = '';
        input.style.height = 'auto';

        this.addMessage('user', message);
        this.showTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: this.sessionId })
            });
            const data = await response.json();

            this.hideTyping();

            if (data.success) {
                this.sessionId = data.session_id;
                localStorage.setItem('iris_session', this.sessionId);
                this.addMessage('assistant', data.response);
                this.updateEmotion(data.emotion);
            } else {
                this.addMessage('assistant', `Error: ${data.error}`);
            }
        } catch (e) {
            this.hideTyping();
            this.addMessage('assistant', `Connection error: ${e.message}`);
        }
    }

    addMessage(role, content) {
        const messages = document.getElementById('messages');
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = `
            <div class="message-avatar">${role === 'assistant' ? 'I' : 'U'}</div>
            <div class="message-content">
                <p>${this.escapeHtml(content).replace(/\n/g, '<br>')}</p>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
        `;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    showTyping() {
        const messages = document.getElementById('messages');
        const div = document.createElement('div');
        div.className = 'message assistant typing-indicator';
        div.id = 'typing-indicator';
        div.innerHTML = `
            <div class="message-avatar">I</div>
            <div class="message-content">
                <p>Thinking<span class="dots">...</span></p>
            </div>
        `;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    hideTyping() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Voice
    setupVoice() {
        document.getElementById('voice-btn').addEventListener('click', () => {
            document.getElementById('voice-overlay').classList.add('active');
            this.startVoiceListening();
        });

        document.getElementById('wake-word-btn').addEventListener('click', async () => {
            const response = await fetch('/api/voice/wake-word/start', { method: 'POST' });
            const data = await response.json();
            alert(data.message);
        });
    }

    async startVoiceListening() {
        try {
            const response = await fetch('/api/voice/listen', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                document.getElementById('voice-text').textContent = `You said: "${data.text}"`;
                // Send to chat
                document.getElementById('chat-input').value = data.text;
                await this.sendMessage();
                setTimeout(() => {
                    document.getElementById('voice-overlay').classList.remove('active');
                }, 2000);
            } else {
                document.getElementById('voice-text').textContent = data.error;
            }
        } catch (e) {
            document.getElementById('voice-text').textContent = 'Voice recognition not available';
        }
    }

    // Vision
    setupVision() {
        document.getElementById('start-vision-btn').addEventListener('click', async () => {
            await fetch('/api/vision/stream/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: 'screen', interval: 2.0 })
            });
            this.isStreaming = true;
            this.startVisionFeed();
        });

        document.getElementById('stop-vision-btn').addEventListener('click', async () => {
            await fetch('/api/vision/stream/stop', { method: 'POST' });
            this.isStreaming = false;
        });

        document.getElementById('analyze-vision-btn').addEventListener('click', async () => {
            const response = await fetch('/api/vision/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: 'What do you see?' })
            });
            const data = await response.json();
            document.getElementById('vision-analysis').textContent = data.analysis || data.error;
        });
    }

    startVisionFeed() {
        if (!this.isStreaming) return;
        // In production: WebSocket or polling for frames
        setTimeout(() => this.startVisionFeed(), 2000);
    }

    // Phone
    setupPhone() {
        document.getElementById('torch-btn').addEventListener('click', () => this.phoneAction('torch', { state: 'toggle' }));
        document.getElementById('wifi-btn').addEventListener('click', () => this.phoneAction('wifi', { state: 'toggle' }));
        document.getElementById('bluetooth-btn').addEventListener('click', () => this.phoneAction('bluetooth', { state: 'toggle' }));
        document.getElementById('camera-btn-phone').addEventListener('click', () => this.phoneAction('camera', { action: 'open' }));
    }

    async phoneAction(endpoint, body) {
        try {
            const response = await fetch(`/api/phone/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await response.json();
            console.log(data);
        } catch (e) {
            console.error(e);
        }
    }

    async loadPhoneData() {
        try {
            const battery = await fetch('/api/phone/battery').then(r => r.json());
            document.getElementById('battery-info').textContent = battery.level ? `${battery.level}% — ${battery.status}` : 'Not connected';

            const contacts = await fetch('/api/phone/contacts').then(r => r.json());
            if (contacts.success) {
                document.getElementById('contacts-list').innerHTML = contacts.contacts.slice(0, 10).map(c =>
                    `<div class="contact-item">${c.name} — ${c.number}</div>`
                ).join('');
            }

            const messages = await fetch('/api/phone/messages?limit=5').then(r => r.json());
            if (messages.success) {
                document.getElementById('phone-messages-list').innerHTML = messages.messages.slice(0, 5).map(m =>
                    `<div class="message-item">${m.address}: ${m.body?.substring(0, 50)}...</div>`
                ).join('');
            }
        } catch (e) {
            console.error('Phone data load failed:', e);
        }
    }

    // Calendar
    setupCalendar() {
        document.getElementById('add-event-btn').addEventListener('click', () => {
            const title = prompt('Event title:');
            if (!title) return;
            const date = prompt('Date (YYYY-MM-DD HH:MM):');
            if (!date) return;
            this.addEvent(title, date);
        });
    }

    async loadCalendar() {
        try {
            const response = await fetch('/api/calendar/today');
            const data = await response.json();
            if (data.success) {
                document.getElementById('events-list').innerHTML = data.events.map(e => `
                    <div class="event-item">
                        <strong>${e.title}</strong>
                        <span>${e.start_time}</span>
                        <p>${e.description || ''}</p>
                    </div>
                `).join('') || '<p>No events today</p>';
            }
        } catch (e) {
            console.error(e);
        }
    }

    async addEvent(title, startTime) {
        try {
            await fetch('/api/calendar/events', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, start_time: startTime })
            });
            this.loadCalendar();
        } catch (e) {
            console.error(e);
        }
    }

    // Notes
    setupNotes() {
        document.getElementById('add-note-btn').addEventListener('click', () => {
            const title = prompt('Note title:');
            if (!title) return;
            const content = prompt('Note content:');
            this.createNote(title, content);
        });
    }

    async loadNotes() {
        try {
            const response = await fetch('/api/notes');
            const data = await response.json();
            if (data.success) {
                document.getElementById('notes-grid').innerHTML = data.notes.map(n => `
                    <div class="note-card">
                        <h4>${n.title}</h4>
                        <p>${n.content?.substring(0, 100)}...</p>
                        <small>${n.category}</small>
                    </div>
                `).join('') || '<p>No notes yet</p>';
            }
        } catch (e) {
            console.error(e);
        }
    }

    async createNote(title, content) {
        try {
            await fetch('/api/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content })
            });
            this.loadNotes();
        } catch (e) {
            console.error(e);
        }
    }

    // Math
    setupMath() {
        document.querySelectorAll('.math-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const op = btn.dataset.op;
                const expression = document.getElementById('math-expression').value;
                this.doMath(op, expression);
            });
        });
    }

    async doMath(operation, expression) {
        try {
            const endpoints = {
                solve: '/api/math/solve',
                simplify: '/api/math/simplify',
                differentiate: '/api/math/differentiate',
                integrate: '/api/math/integrate',
                evaluate: '/api/math/evaluate'
            };

            const response = await fetch(endpoints[operation], {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ expression })
            });
            const data = await response.json();

            const resultDiv = document.getElementById('math-result');
            if (data.success) {
                resultDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            } else {
                resultDiv.innerHTML = `<span style="color: var(--danger)">Error: ${data.error}</span>`;
            }
        } catch (e) {
            document.getElementById('math-result').textContent = `Error: ${e.message}`;
        }
    }

    // Projects
    setupProjects() {
        document.getElementById('generate-project-btn').addEventListener('click', async () => {
            const name = document.getElementById('project-name').value;
            const template = document.getElementById('project-template').value;
            const description = document.getElementById('project-desc').value;
            if (!name) return alert('Project name required');

            const response = await fetch('/api/projects/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, template, description })
            });
            const data = await response.json();
            alert(data.success ? `Project ${name} generated!` : `Error: ${data.error}`);
            this.loadProjects();
        });
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();
            if (data.success) {
                document.getElementById('projects-list').innerHTML = data.projects.map(p => `
                    <div class="project-card">
                        <h4>${p.name}</h4>
                        <p>${p.path}</p>
                        <small>${p.created}</small>
                    </div>
                `).join('') || '<p>No projects yet</p>';
            }
        } catch (e) {
            console.error(e);
        }
    }

    // Settings
    setupSettings() {
        document.getElementById('analyze-self-btn').addEventListener('click', async () => {
            const response = await fetch('/api/self/analyze');
            const data = await response.json();
            document.getElementById('self-analysis-result').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        });

        document.getElementById('reflect-btn').addEventListener('click', async () => {
            const response = await fetch('/api/consciousness/reflect');
            const data = await response.json();
            document.getElementById('reflection-result').innerHTML = `<pre>${data.reflection}</pre>`;
        });
    }

    async loadSettings() {
        try {
            const status = await fetch('/api/status').then(r => r.json());
            document.getElementById('setting-uptime').textContent = status.iris.uptime;
            document.getElementById('setting-emotion').textContent = status.iris.emotion.dominant;
            document.getElementById('setting-awareness').textContent = `${(status.iris.awareness * 100).toFixed(1)}%`;
            document.getElementById('autonomous-status').textContent = status.autonomous.running ? 'Running' : 'Stopped';
            document.getElementById('queue-size').textContent = status.autonomous.queue_size;
        } catch (e) {
            console.error(e);
        }
    }

    // Status & Polling
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            this.updateEmotion(data.iris.emotion.dominant);
        } catch (e) {
            console.error('Status load failed:', e);
        }
    }

    startStatusPolling() {
        setInterval(() => this.loadStatus(), 30000); // Every 30s
    }

    updateEmotion(emotion) {
        document.getElementById('emotion-display').textContent = emotion || 'neutral';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.irisApp = new IRISApp();
});
