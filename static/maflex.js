
# Create the JavaScript file for Maflex

maflex_js = '''/*
 * MAFLEX - The Infinite Gaming Universe
 * Core JavaScript Controller
 */

class MaflexUniverse {
    constructor() {
        this.energy = 100;
        this.maxEnergy = 100;
        this.currentGame = null;
        this.activePowers = new Set();
        this.games = [
            {
                id: 'medieval-rpg',
                name: 'Medieval RPG',
                description: 'Embark on a legendary quest through mystical realms. Battle foes, discover treasures, and forge your destiny.',
                icon: '⚔️',
                color: '#ffaa00',
                stats: { players: '1', difficulty: 'Medium', time: '∞' }
            },
            {
                id: 'cyber-arena',
                name: 'Cyber Arena',
                description: 'Neon-drenched combat in a digital dystopia. Hack systems, upgrade your avatar, dominate the grid.',
                icon: '🌆',
                color: '#00d4ff',
                stats: { players: '1-4', difficulty: 'Hard', time: '15-30m' }
            },
            {
                id: 'void-chess',
                name: 'Void Chess',
                description: 'Strategic warfare across dimensions. Pieces have powers, the board shifts, nothing is certain.',
                icon: '♟️',
                color: '#ff00ff',
                stats: { players: '2', difficulty: 'Expert', time: '30-60m' }
            },
            {
                id: 'nebula-miner',
                name: 'Nebula Miner',
                description: 'Extract rare resources from dying stars. Manage your crew, upgrade your ship, survive the void.',
                icon: '🚀',
                color: '#00ff88',
                stats: { players: '1', difficulty: 'Medium', time: '∞' }
            },
            {
                id: 'chronos-puzzle',
                name: 'Chronos Puzzle',
                description: 'Manipulate time to solve paradoxes. Every choice echoes across timelines.',
                icon: '⏳',
                color: '#ff0044',
                stats: { players: '1', difficulty: 'Hard', time: '20-40m' }
            }
        ];
        
        this.powerCosts = {
            insight: 15,
            sight: 10,
            manifest: 25,
            avatar: 50,
            adjust: 30
        };
        
        this.init();
    }

    init() {
        this.setupMatrixRain();
        this.setupParticles();
        this.setupOrbs();
        
        // Start entrance sequence
        setTimeout(() => this.completeEntrance(), 5500);
    }

    /* ============================================
       ENTRANCE SEQUENCE
       ============================================ */
    
    setupMatrixRain() {
        const canvas = document.getElementById('matrix-canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*';
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops = [];
        
        for (let i = 0; i < columns; i++) {
            drops[i] = Math.random() * -100;
        }
        
        const draw = () => {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.fillStyle = '#00d4ff';
            ctx.font = fontSize + 'px monospace';
            
            for (let i = 0; i < drops.length; i++) {
                const text = chars[Math.floor(Math.random() * chars.length)];
                const x = i * fontSize;
                const y = drops[i] * fontSize;
                
                // Gradient color based on position
                const hue = 180 + (Math.random() * 60);
                ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
                ctx.fillText(text, x, y);
                
                if (y > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
        };
        
        setInterval(draw, 35);
        
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    }

    setupParticles() {
        const container = document.getElementById('infinity-particles');
        
        for (let i = 0; i < 20; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 2 + 's';
                container.appendChild(particle);
            }, i * 100);
        }
    }

    setupOrbs() {
        const container = document.getElementById('universe-orbs');
        const colors = ['#00d4ff', '#ff00ff', '#00ff88', '#ffaa00'];
        
        for (let i = 0; i < 8; i++) {
            const orb = document.createElement('div');
            orb.className = 'orb';
            orb.style.width = (20 + Math.random() * 60) + 'px';
            orb.style.height = orb.style.width;
            orb.style.left = Math.random() * 100 + '%';
            orb.style.top = Math.random() * 100 + '%';
            orb.style.background = colors[Math.floor(Math.random() * colors.length)];
            orb.style.opacity = 0.1 + Math.random() * 0.2;
            orb.style.animationDuration = (10 + Math.random() * 10) + 's';
            orb.style.animationDelay = Math.random() * 5 + 's';
            container.appendChild(orb);
        }
    }

    completeEntrance() {
        const overlay = document.getElementById('entrance-overlay');
        const universe = document.getElementById('maflex-universe');
        
        overlay.classList.add('hidden');
        universe.classList.add('active');
        
        this.renderGames();
        this.startEnergyRegen();
        
        // Welcome message from IRIS after entrance
        setTimeout(() => {
            this.addIrisMessage('The universe awaits. I have loaded 5 dimensions for you. Each contains unique challenges and mysteries. Your powers are ready.', 'iris');
        }, 1000);
    }

    /* ============================================
       GAMES MANAGEMENT
       ============================================ */
    
    renderGames() {
        const container = document.getElementById('games-list');
        container.innerHTML = this.games.map(game => `
            <div class="game-card ${this.currentGame === game.id ? 'active' : ''}" 
                 onclick="maflex.selectGame('${game.id}')"
                 style="--game-color: ${game.color}">
                <div class="game-icon" style="background: linear-gradient(135deg, ${game.color}, transparent);">
                    ${game.icon}
                </div>
                <div class="game-title" style="color: ${game.color}">${game.name}</div>
                <div class="game-desc">${game.description}</div>
                <div class="game-stats">
                    <span><i class="fas fa-users"></i> ${game.stats.players}</span>
                    <span><i class="fas fa-chart-line"></i> ${game.stats.difficulty}</span>
                    <span><i class="fas fa-clock"></i> ${game.stats.time}</span>
                </div>
            </div>
        `).join('');
    }

    selectGame(gameId) {
        this.currentGame = gameId;
        this.renderGames();
        
        const game = this.games.find(g => g.id === gameId);
        
        // Hide placeholder, show canvas
        document.getElementById('viewport-placeholder').style.display = 'none';
        document.getElementById('game-canvas').classList.add('active');
        
        // Initialize game
        this.initializeGame(game);
        
        // Notify IRIS
        this.addIrisMessage(`Entering ${game.name}... ${game.description}`, 'system');
        
        // Send to actual game system
        this.loadActualGame(gameId);
    }

    initializeGame(game) {
        const canvas = document.getElementById('game-canvas');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        
        // Clear and draw initial state
        ctx.fillStyle = '#050508';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw game-specific content
        ctx.fillStyle = game.color;
        ctx.font = 'bold 30px Orbitron';
        ctx.textAlign = 'center';
        ctx.fillText(`${game.icon} ${game.name}`, canvas.width/2, canvas.height/2 - 50);
        
        ctx.font = '16px Rajdhani';
        ctx.fillStyle = '#fff';
        ctx.fillText('Initializing game environment...', canvas.width/2, canvas.height/2 + 20);
        
        // Draw loading bar
        let progress = 0;
        const loadInterval = setInterval(() => {
            progress += 2;
            
            ctx.fillStyle = '#050508';
            ctx.fillRect(canvas.width/2 - 150, canvas.height/2 + 50, 300, 20);
            
            ctx.strokeStyle = game.color;
            ctx.strokeRect(canvas.width/2 - 150, canvas.height/2 + 50, 300, 20);
            
            ctx.fillStyle = game.color;
            ctx.fillRect(canvas.width/2 - 148, canvas.height/2 + 52, (296 * progress) / 100, 16);
            
            if (progress >= 100) {
                clearInterval(loadInterval);
                ctx.fillText('Press any key or click to begin', canvas.width/2, canvas.height/2 + 100);
            }
        }, 30);
    }

    loadActualGame(gameId) {
        // Connect to your existing games.py backend
        fetch(`/api/games/start/${gameId}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.gameState = data.state;
                    this.addIrisMessage(`Game started! State: ${data.state}`, 'iris');
                } else {
                    this.addIrisMessage(`Could not start game: ${data.error}`, 'system');
                }
            })
            .catch(err => {
                console.log('Backend not connected - running in demo mode');
                this.addIrisMessage('Demo mode: Backend not detected. Game visuals only.', 'system');
            });
    }

    /* ============================================
       POWERS SYSTEM
       ============================================ */
    
    activatePower(powerName) {
        const cost = this.powerCosts[powerName];
        
        if (this.energy < cost) {
            this.addIrisMessage(`Insufficient energy! Need ${cost} energy, have ${this.energy}.`, 'system');
            this.shakeElement(document.getElementById(`power-${powerName}`));
            return;
        }
        
        // Deduct energy
        this.energy -= cost;
        this.updateEnergyDisplay();
        
        // Visual activation
        this.showPowerActivation();
        
        // Activate power effect
        document.getElementById(`power-${powerName}`).classList.add('active');
        this.activePowers.add(powerName);
        
        // Power-specific effects
        this.executePowerEffect(powerName);
        
        // Auto-deactivate after duration
        setTimeout(() => {
            document.getElementById(`power-${powerName}`).classList.remove('active');
            this.activePowers.delete(powerName);
        }, 10000);
    }

    executePowerEffect(powerName) {
        const effects = {
            insight: () => {
                this.addIrisMessage('🔮 Temporal Insight activated! I can see possible futures... Choose wisely.', 'iris');
                if (this.currentGame) {
                    this.addIrisMessage(`Prediction: Success rate for current objective is ${Math.floor(Math.random() * 30 + 60)}%`, 'iris');
                }
            },
            sight: () => {
                this.addIrisMessage('👁️ Data Sight activated! Hidden information revealed.', 'iris');
                if (this.currentGame) {
                    this.addIrisMessage(`Hidden stat: Enemy weakness detected - ${['Fire', 'Ice', 'Lightning', 'Shadow'][Math.floor(Math.random() * 4)]} damage +50%`, 'iris');
                }
            },
            manifest: () => {
                this.addIrisMessage('✨ Controlled Manifestation! Creating useful item...', 'iris');
                const items = ['Health Potion', 'Energy Crystal', 'Mystery Box', 'Power Booster'];
                const item = items[Math.floor(Math.random() * items.length)];
                this.addIrisMessage(`Manifested: ${item}!`, 'system');
            },
            avatar: () => {
                this.addIrisMessage('🧑 Avatar Mode engaged! You are now physically present in the game world.', 'iris');
                document.body.style.transform = 'scale(1.02)';
                setTimeout(() => document.body.style.transform = '', 500);
            },
            adjust: () => {
                this.addIrisMessage('🌍 World-State Adjustment! Reality is malleable...', 'iris');
                this.showWorldAdjustDialog();
            }
        };
        
        if (effects[powerName]) {
            effects[powerName]();
        }
    }

    showPowerActivation() {
        const activation = document.getElementById('power-activation');
        activation.classList.add('active');
        setTimeout(() => activation.classList.remove('active'), 1000);
    }

    showWorldAdjustDialog() {
        const adjustments = [
            'Increase game speed',
            'Decrease difficulty',
            'Add random event',
            'Change weather/time',
            'Spawn secret merchant'
        ];
        
        const options = adjustments.map((adj, i) => `${i + 1}. ${adj}`).join('\\n');
        this.addIrisMessage(`Select adjustment:\\n${options}\\n(Type the number)`, 'iris');
    }

    /* ============================================
       IRIS CHAT SYSTEM
       ============================================ */
    
    addIrisMessage(text, sender = 'iris') {
        const container = document.getElementById('iris-messages');
        const message = document.createElement('div');
        message.className = `message ${sender}`;
        message.textContent = text;
        container.appendChild(message);
        container.scrollTop = container.scrollHeight;
    }

    sendIrisMessage() {
        const input = document.getElementById('iris-input');
        const text = input.value.trim();
        
        if (!text) return;
        
        this.addIrisMessage(text, 'user');
        input.value = '';
        
        // Process command or query
        this.processIrisQuery(text);
    }

    processIrisQuery(text) {
        const lower = text.toLowerCase();
        
        // Game selection commands
        if (lower.includes('start') || lower.includes('play') || lower.includes('open')) {
            const gameNames = {
                'medieval': 'medieval-rpg',
                'rpg': 'medieval-rpg',
                'cyber': 'cyber-arena',
                'chess': 'void-chess',
                'nebula': 'nebula-miner',
                'miner': 'nebula-miner',
                'chronos': 'chronos-puzzle',
                'puzzle': 'chronos-puzzle'
            };
            
            for (const [key, id] of Object.entries(gameNames)) {
                if (lower.includes(key)) {
                    setTimeout(() => this.selectGame(id), 500);
                    this.addIrisMessage(`I'll open ${this.games.find(g => g.id === id).name} for you.`, 'iris');
                    return;
                }
            }
        }
        
        // Power explanations
        if (lower.includes('power') || lower.includes('ability') || lower.includes('how do i use')) {
            this.addIrisMessage(`Your powers:\\n🔮 Temporal Insight - Predict outcomes (15 energy)\\n👁️ Data Sight - See hidden stats (10 energy)\\n✨ Manifestation - Create items (25 energy)\\n🧑 Avatar Mode - Enter game world (50 energy)\\n🌍 World Adjust - Change reality (30 energy)`, 'iris');
            return;
        }
        
        // Game tricks/tips
        if (lower.includes('trick') || lower.includes('tip') || lower.includes('hint') || lower.includes('help')) {
            const tricks = [
                'Always check your corners in Cyber Arena - hidden loot is everywhere.',
                'In Medieval RPG, talk to every NPC twice. Some have secret second dialogues.',
                'Void Chess: Sacrificing a pawn can trigger dimensional shifts.',
                'Nebula Miner: Mine during solar flares for rare minerals.',
                'Chronos Puzzle: The solution often requires thinking backwards in time.'
            ];
            this.addIrisMessage(`💡 Pro tip: ${tricks[Math.floor(Math.random() * tricks.length)]}`, 'iris');
            return;
        }
        
        // Energy queries
        if (lower.includes('energy') || lower.includes('power level')) {
            this.addIrisMessage(`Your current energy: ${this.energy}/${this.maxEnergy}. Energy regenerates over time, or you can use Manifestation to create energy crystals.`, 'iris');
            return;
        }
        
        // World state adjustment responses
        if (/^[1-5]$/.test(text)) {
            const adjustments = [
                'Game speed increased! Time flows 50% faster.',
                'Difficulty decreased. Enemies are now less aggressive.',
                'Random event triggered! Something unexpected approaches...',
                'Atmosphere shifted. The world feels different now.',
                'Secret merchant appeared! Check your map.'
            ];
            this.addIrisMessage(adjustments[parseInt(text) - 1], 'system');
            return;
        }
        
        // Default response
        const responses = [
            'I understand. How can I assist you further in Maflex?',
            'Interesting. Would you like me to activate a power or open a game?',
            'I\'m here to help. Try asking me to start a game or explain your powers.',
            'The universe is vast. What would you like to explore?',
            'I can play games with you, give you tips, or control the world. Just ask!'
        ];
        
        setTimeout(() => {
            this.addIrisMessage(responses[Math.floor(Math.random() * responses.length)], 'iris');
        }, 800);
    }

    /* ============================================
       UTILITY FUNCTIONS
       ============================================ */
    
    updateEnergyDisplay() {
        document.getElementById('energy-value').textContent = this.energy;
        
        // Update power button states
        for (const [power, cost] of Object.entries(this.powerCosts)) {
            const btn = document.getElementById(`power-${power}`);
            if (this.energy < cost) {
                btn.disabled = true;
                btn.style.opacity = '0.3';
            } else {
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        }
    }

    startEnergyRegen() {
        setInterval(() => {
            if (this.energy < this.maxEnergy) {
                this.energy = Math.min(this.maxEnergy, this.energy + 1);
                this.updateEnergyDisplay();
            }
        }, 3000); // +1 energy every 3 seconds
    }

    shakeElement(element) {
        element.style.animation = 'shake 0.5s ease';
        setTimeout(() => element.style.animation = '', 500);
    }

    exitMaflex() {
        if (confirm('Exit Maflex and return to IRIS?')) {
            window.location.href = '/'; // Return to main IRIS
        }
    }
}

// Global functions for HTML onclick handlers
function activatePower(power) {
    maflex.activatePower(power);
}

function sendQuickMessage(text) {
    document.getElementById('iris-input').value = text;
    maflex.sendIrisMessage();
}

function handleIrisInput(event) {
    if (event.key === 'Enter') {
        maflex.sendIrisMessage();
    }
}

function exitMaflex() {
    maflex.exitMaflex();
}

// Initialize
const maflex = new MaflexUniverse();

// Add shake animation to styles
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
`;
document.head.appendChild(style);
'''

print("JavaScript file created successfully!")
print(f"Length: {len(maflex_js)} characters")
