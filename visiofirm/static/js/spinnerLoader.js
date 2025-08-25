// static/js/spinnerLoader.js

// Inject spinner styles into the document
const spinnerStyles = document.createElement('style');
spinnerStyles.textContent = `
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    transition: opacity 0.3s ease;
}

.loading-overlay.active {
    display: flex;
    opacity: 1;
}

.vf-loader {
    position: relative;
    width: 200px;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.vf-logo {
    position: relative;
    width: 120px;
    height: 120px;
}

.dot {
    position: absolute;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    top: 60px;
    left: 60px;
    opacity: 0;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
    z-index: 3; /* Ensure dots appear above lines */
}

/* Dot animations with staggered timing and blue-white pulse */
.dot-1 {
    animation: dotAppear 0.5s forwards, moveDot1 1s ease-out forwards 0.5s, pulseGlow 1.5s infinite 1.5s;
}
@keyframes moveDot1 {
    to { top: 10px; left: 10px; }
}
.dot-2 {
    animation: dotAppear 0.5s forwards 0.1s, moveDot2 1s ease-out forwards 0.6s, pulseGlow 1.5s infinite 1.6s;
}
@keyframes moveDot2 {
    to { top: 10px; left: 40px; }
}
.dot-3 {
    animation: dotAppear 0.5s forwards 0.2s, moveDot3 1s ease-out forwards 0.7s, pulseGlow 1.5s infinite 1.7s;
}
@keyframes moveDot3 {
    to { top: 10px; left: 70px; }
}
.dot-4 {
    animation: dotAppear 0.5s forwards 0.3s, moveDot4 1s ease-out forwards 0.8s, pulseGlow 1.5s infinite 1.8s;
}
@keyframes moveDot4 {
    to { top: 10px; left: 100px; }
}
.dot-5 {
    animation: dotAppear 0.5s forwards 0.4s, moveDot5 1s ease-out forwards 0.9s, pulseGlow 1.5s infinite 1.9s;
}
@keyframes moveDot5 {
    to { top: 50px; left: 70px; }
}
.dot-6 {
    animation: dotAppear 0.5s forwards 0.5s, moveDot6 1s ease-out forwards 1s, pulseGlow 1.5s infinite 2s;
}
@keyframes moveDot6 {
    to { top: 50px; left: 100px; }
}
.dot-7 {
    animation: dotAppear 0.5s forwards 0.6s, moveDot7 1s ease-out forwards 1.1s, pulseGlow 1.5s infinite 2.1s;
}
@keyframes moveDot7 {
    to { top: 90px; left: 25px; }
}
.dot-8 {
    animation: dotAppear 0.5s forwards 0.7s, moveDot8 1s ease-out forwards 1.2s, pulseGlow 1.5s infinite 2.2s;
}
@keyframes moveDot8 {
    to { top: 90px; left: 70px; }
}

@keyframes dotAppear {
    from { opacity: 0; transform: scale(0); }
    to { opacity: 1; transform: scale(1); }
}

@keyframes pulseGlow {
    0%, 100% { 
        transform: scale(1); 
        background: #ffffff;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
    }
    50% { 
        transform: scale(1.3); 
        background: #3498db;
        box-shadow: 0 0 20px rgba(52, 152, 219, 0.8);
    }
}

/* White SVG lines with glow effect */
.vf-lines {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 2; /* Lines behind dots */
}

.vf-lines path {
    fill: none;
    stroke: white;
    stroke-width: 2;
    stroke-dasharray: 100;
    stroke-dashoffset: 100;
    opacity: 0;
    filter: url(#glow);
}

/* All paths have the same white color and animation */
.vf-lines path {
    stroke: white;
    animation: drawLine 1s ease-in-out forwards, linePulse 2s infinite;
}

/* Staggered animations for each path */
.vf-lines path:nth-child(1) {
    animation-delay: 1.5s, 2.5s;
}
.vf-lines path:nth-child(2) {
    animation-delay: 1.6s, 2.6s;
}
.vf-lines path:nth-child(3) {
    animation-delay: 1.7s, 2.7s;
}
.vf-lines path:nth-child(4) {
    animation-delay: 1.8s, 2.8s;
}
.vf-lines path:nth-child(5) {
    animation-delay: 1.9s, 2.9s;
}

@keyframes drawLine {
    0% { stroke-dashoffset: 100; opacity: 0; }
    10% { opacity: 1; }
    100% { stroke-dashoffset: 0; opacity: 1; }
}

@keyframes linePulse {
    0%, 100% { 
        stroke-width: 2;
        opacity: 1;
    }
    50% { 
        stroke-width: 3;
        opacity: 0.8;
    }
}

/* Particle effects */
.particles {
    position: absolute;
    width: 100%;
    height: 100%;
    z-index: 1; /* Particles behind everything */
}

.particle {
    position: absolute;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.particle1 {
    top: 20px;
    left: 20px;
    animation: particleMove1 2s infinite;
}
@keyframes particleMove1 {
    0% { transform: translate(0, 0); opacity: 1; }
    100% { transform: translate(30px, 30px); opacity: 0; }
}
.particle2 {
    top: 100px;
    left: 100px;
    animation: particleMove2 2s infinite 0.5s;
}
@keyframes particleMove2 {
    0% { transform: translate(0, 0); opacity: 1; }
    100% { transform: translate(-20px, -20px); opacity: 0; }
}
.particle3 {
    top: 40px;
    left: 80px;
    animation: particleMove3 1.8s infinite 0.3s;
}
@keyframes particleMove3 {
    0% { transform: translate(0, 0); opacity: 1; }
    100% { transform: translate(20px, -30px); opacity: 0; }
}

/* Spinning rings */
.loading-ring {
    position: absolute;
    border-radius: 50%;
    opacity: 0;
    filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.7));
    z-index: 1; /* Rings behind dots */
}

.loading-ring1 {
    width: 160px;
    height: 160px;
    border: 4px solid transparent;
    border-top-color: white;
    border-right-color: white;
    animation: spin1 1.2s linear infinite, ringAppear 0.5s forwards 2.3s;
}
.loading-ring2 {
    width: 180px;
    height: 180px;
    border: 4px solid transparent;
    border-top-color: rgba(255, 255, 255, 0.7);
    border-right-color: rgba(255, 255, 255, 0.7);
    animation: spin2 1.5s linear infinite reverse, ringAppear 0.5s forwards 2.3s;
}
.loading-ring3 {
    width: 200px;
    height: 200px;
    border: 4px solid transparent;
    border-top-color: rgba(255, 255, 255, 0.4);
    border-right-color: rgba(255, 255, 255, 0.4);
    animation: spin3 2s linear infinite, ringAppear 0.5s forwards 2.3s;
}

@keyframes spin1 {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
@keyframes spin2 {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(-360deg); }
}
@keyframes spin3 {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
@keyframes ringAppear {
    to { opacity: 1; }
}
`;

document.head.appendChild(spinnerStyles);

export function showLoadingOverlay(message = 'Loading Project...') {
    let loadingOverlay = document.getElementById('loading-overlay');
    
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.className = 'loading-overlay';
        
        const vfLoader = document.createElement('div');
        vfLoader.className = 'vf-loader';
        vfLoader.id = 'vf-loader';
        
        // Create particles
        const particles = document.createElement('div');
        particles.className = 'particles';
        particles.innerHTML = `
            <div class="particle particle1"></div>
            <div class="particle particle2"></div>
            <div class="particle particle3"></div>
        `;
        
        // Create VF logo with dots and connections
        const vfLogo = document.createElement('div');
        vfLogo.className = 'vf-logo';
        vfLogo.innerHTML = `
            <svg class="vf-lines" viewBox="0 0 120 120">
                <defs>
                    <filter id="glow">
                        <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur1"/>
                        <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur2"/>
                        <feMerge>
                            <feMergeNode in="blur1"/>
                            <feMergeNode in="blur2"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>
                <!-- V letter connections -->
                <path d="M29,94 L14,14" />
                <path d="M29,94 L44,14" />
            </svg>
            <div class="dot dot-1"></div>
            <div class="dot dot-2"></div>
            <div class="dot dot-3"></div>
            <div class="dot dot-4"></div>
            <div class="dot dot-5"></div>
            <div class="dot dot-6"></div>
            <div class="dot dot-7"></div>
            <div class="dot dot-8"></div>
        `;
        
        // Create loading rings
        const ring1 = document.createElement('div');
        ring1.className = 'loading-ring loading-ring1';
        const ring2 = document.createElement('div');
        ring2.className = 'loading-ring loading-ring2';
        const ring3 = document.createElement('div');
        ring3.className = 'loading-ring loading-ring3';
        
        vfLoader.appendChild(particles);
        vfLoader.appendChild(vfLogo);
        vfLoader.appendChild(ring1);
        vfLoader.appendChild(ring2);
        vfLoader.appendChild(ring3);
        
        const messageElement = document.createElement('p');
        messageElement.textContent = message;
        messageElement.style.color = 'white';
        messageElement.style.marginTop = '20px';
        messageElement.style.textAlign = 'center';
        messageElement.style.fontFamily = 'Arial, sans-serif';
        messageElement.style.fontSize = '1.1rem';
        messageElement.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
        
        loadingOverlay.appendChild(vfLoader);
        loadingOverlay.appendChild(messageElement);
        document.body.appendChild(loadingOverlay);
    }
    
    loadingOverlay.style.display = 'flex';
    setTimeout(() => {
        loadingOverlay.style.opacity = '1';
        const vfLoader = document.getElementById('vf-loader');
        if (vfLoader) {
            vfLoader.classList.add('active');
        }
    }, 10);
}

export function hideLoadingOverlay() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.opacity = '0';
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
            const vfLoader = document.getElementById('vf-loader');
            if (vfLoader) {
                vfLoader.classList.remove('active');
            }
        }, 300);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    hideLoadingOverlay();
});

window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
        hideLoadingOverlay();
    }
});