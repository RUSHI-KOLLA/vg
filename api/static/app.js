import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// --- DOM ELEMENTS ---
const heroState = document.getElementById('hero-state');
const commandState = document.getElementById('command-state');
const btnInit = document.getElementById('btn-init');
const form = document.getElementById('query-form');
const input = document.getElementById('question-input');
const enhancedMode = document.getElementById('enhanced-mode');
const processingView = document.getElementById('processing-view');
const resultsView = document.getElementById('results-view');
const btnReset = document.getElementById('btn-reset');

// Result Elements
const confVal = document.getElementById('conf-val');
const confFill = document.getElementById('conf-fill');
const verdictPrimary = document.getElementById('verdict-primary');
const resPattern = document.getElementById('res-pattern');
const resPrecedent = document.getElementById('res-precedent');
const resReasoning = document.getElementById('res-reasoning');

// --- THREE.JS SETUP ---
let scene, camera, renderer, composer, bloomPass;
let singularityParticles, singularityGeo;
let ringMesh, coreGlow;
let mouse = new THREE.Vector2();
let targetMouse = new THREE.Vector2();
let clock = new THREE.Clock();

// App State
let isWarping = false;
let currentPhase = 'hero'; // 'hero', 'idle', 'processing', 'results'
let baseRotationSpeed = 0.001;
let targetCameraZ = 100;
let particleCount = 15000;

function initThreeJS() {
    const container = document.getElementById('canvas-container');
    
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.008);

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 180; // Start far away

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    container.appendChild(renderer.domElement);

    // Post-processing
    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    
    bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 2.0, 0.5, 0.1);
    composer.addPass(bloomPass);

    buildSingularity();

    window.addEventListener('resize', onResize);
    window.addEventListener('mousemove', onMouseMove);

    animate();
}

function createCircleTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 32;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
    gradient.addColorStop(0, 'rgba(255,255,255,1)');
    gradient.addColorStop(0.2, 'rgba(255,255,255,0.8)');
    gradient.addColorStop(0.5, 'rgba(255,255,255,0.2)');
    gradient.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 32, 32);
    return new THREE.CanvasTexture(canvas);
}

function buildSingularity() {
    // 1. The Particle Swarm
    singularityGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    
    // Physics properties
    const velocities = new Float32Array(particleCount * 3);
    const originAngles = new Float32Array(particleCount * 2); // theta, phi

    const colorCyan = new THREE.Color(0x00ffff);
    const colorMagenta = new THREE.Color(0xff00ff);
    const colorWhite = new THREE.Color(0xffffff);

    for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        const i2 = i * 2;
        
        // Spherical distribution with higher density in center
        const radius = Math.pow(Math.random(), 3) * 80 + 5;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos((Math.random() * 2) - 1);
        
        originAngles[i2] = theta;
        originAngles[i2 + 1] = phi;

        positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i3 + 2] = radius * Math.cos(phi);

        // Color based on distance from center
        const mixRatio = radius / 85;
        let c = colorCyan.clone().lerp(colorMagenta, mixRatio);
        if (Math.random() > 0.95) c = colorWhite;
        
        colors[i3] = c.r;
        colors[i3 + 1] = c.g;
        colors[i3 + 2] = c.b;

        sizes[i] = Math.random() * 1.5 + 0.5;

        // Orbital velocity
        velocities[i3] = (Math.random() - 0.5) * 0.5;
        velocities[i3 + 1] = (Math.random() - 0.5) * 0.5;
        velocities[i3 + 2] = (Math.random() - 0.5) * 0.5;
    }

    singularityGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    singularityGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    singularityGeo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    singularityGeo.userData = { velocities, originAngles };

    const material = new THREE.PointsMaterial({
        size: 1.0,
        map: createCircleTexture(),
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        sizeAttenuation: true
    });

    singularityParticles = new THREE.Points(singularityGeo, material);
    scene.add(singularityParticles);

    // 2. The Core Glow
    const glowGeo = new THREE.SphereGeometry(15, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({
        color: 0x00ffff,
        transparent: true,
        opacity: 0.15,
        blending: THREE.AdditiveBlending,
        wireframe: true
    });
    coreGlow = new THREE.Mesh(glowGeo, glowMat);
    scene.add(coreGlow);

    // 3. Orbital Rings
    const ringGeo = new THREE.TorusGeometry(45, 0.2, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0.2, blending: THREE.AdditiveBlending });
    ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 2.5;
    scene.add(ringMesh);
}

function onMouseMove(event) {
    // Normalized mouse coordinates (-1 to +1)
    targetMouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    targetMouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
}

function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
}

// --- PHYSICS & ANIMATION LOOP ---
function updatePhysics() {
    if (!singularityGeo) return;

    const positions = singularityGeo.attributes.position.array;
    const velocities = singularityGeo.userData.velocities;
    
    // Smooth mouse follow
    mouse.lerp(targetMouse, 0.05);
    
    // Mouse world position approximation
    const mouseWorldX = mouse.x * 50;
    const mouseWorldY = mouse.y * 30;

    // Physics parameters based on state
    const repulsionStrength = isWarping ? 0 : 2.5;
    const attractionStrength = isWarping ? 0.001 : 0.02;
    const maxSpeed = isWarping ? 15 : 2;

    for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        let px = positions[i3];
        let py = positions[i3 + 1];
        let pz = positions[i3 + 2];

        // 1. Core Attraction (Gravity)
        const distToCenter = Math.sqrt(px*px + py*py + pz*pz);
        const dirX = -px / distToCenter;
        const dirY = -py / distToCenter;
        const dirZ = -pz / distToCenter;

        if (!isWarping) {
            velocities[i3] += dirX * attractionStrength;
            velocities[i3 + 1] += dirY * attractionStrength;
            velocities[i3 + 2] += dirZ * attractionStrength;
        }

        // 2. Mouse Repulsion
        if (!isWarping && distToCenter > 10) {
            const dx = px - mouseWorldX;
            const dy = py - mouseWorldY;
            const distToMouse = Math.sqrt(dx*dx + dy*dy + pz*pz);
            
            if (distToMouse < 30) {
                const force = (30 - distToMouse) / 30 * repulsionStrength;
                velocities[i3] += (dx / distToMouse) * force;
                velocities[i3 + 1] += (dy / distToMouse) * force;
            }
        }

        // 3. Orbital Swirl (Cross product with Up vector)
        if (!isWarping) {
            velocities[i3] += dirZ * 0.05;
            velocities[i3 + 2] -= dirX * 0.05;
        }

        // 4. Warp Speed (Push particles towards camera rapidly)
        if (isWarping) {
            velocities[i3 + 2] += 2.0; // Shoot towards +Z
            velocities[i3] *= 1.05; // Expand outwards X
            velocities[i3 + 1] *= 1.05; // Expand outwards Y
        } else {
             // Friction
            velocities[i3] *= 0.95;
            velocities[i3 + 1] *= 0.95;
            velocities[i3 + 2] *= 0.95;
        }

        // Limit speed
        const speed = Math.sqrt(velocities[i3]**2 + velocities[i3+1]**2 + velocities[i3+2]**2);
        if (speed > maxSpeed) {
            velocities[i3] = (velocities[i3] / speed) * maxSpeed;
            velocities[i3 + 1] = (velocities[i3 + 1] / speed) * maxSpeed;
            velocities[i3 + 2] = (velocities[i3 + 2] / speed) * maxSpeed;
        }

        // Apply velocity
        positions[i3] += velocities[i3];
        positions[i3 + 1] += velocities[i3 + 1];
        positions[i3 + 2] += velocities[i3 + 2];

        // Reset if too far during warp
        if (isWarping && positions[i3 + 2] > camera.position.z + 50) {
            positions[i3] = (Math.random() - 0.5) * 40;
            positions[i3 + 1] = (Math.random() - 0.5) * 40;
            positions[i3 + 2] = -200 - Math.random() * 100;
            velocities[i3+2] = 5 + Math.random() * 5;
        }
    }

    singularityGeo.attributes.position.needsUpdate = true;
}

function animate() {
    requestAnimationFrame(animate);
    const dt = clock.getDelta();
    const elapsed = clock.getElapsedTime();

    // Camera follow mouse slightly
    camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.x * 15, 0.05);
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.y * 15, 0.05);
    camera.position.z = THREE.MathUtils.lerp(camera.position.z, targetCameraZ, 0.05);
    camera.lookAt(0, 0, 0);

    // Rotate meshes
    if (singularityParticles) singularityParticles.rotation.y += baseRotationSpeed;
    if (coreGlow) {
        coreGlow.rotation.y -= baseRotationSpeed * 2;
        coreGlow.scale.setScalar(1 + Math.sin(elapsed * 2) * 0.05);
    }
    if (ringMesh) {
        ringMesh.rotation.z += 0.005;
        ringMesh.material.opacity = 0.2 + Math.sin(elapsed) * 0.1;
    }

    updatePhysics();
    composer.render();
}

// --- UI LOGIC & TRANSITIONS ---

function transitionToCommand() {
    // Hide Hero
    gsap.to(heroState, { opacity: 0, scale: 1.1, duration: 1, onComplete: () => {
        heroState.classList.add('hidden');
        commandState.classList.remove('hidden');
        
        // Show Command HUD
        gsap.fromTo(commandState, 
            { opacity: 0 }, 
            { opacity: 1, duration: 1 }
        );
        gsap.fromTo(".console-box", 
            { y: 50, opacity: 0 }, 
            { y: 0, opacity: 1, duration: 1, delay: 0.5, ease: "power3.out" }
        );
    }});

    // Camera Zoom into singularity
    targetCameraZ = 100;
    gsap.to(bloomPass, { strength: 3.0, duration: 1, yoyo: true, repeat: 1 });
}

function triggerWarpAnimation() {
    isWarping = true;
    baseRotationSpeed = 0.01;
    
    // Hide Form
    gsap.to(form, { opacity: 0, y: -20, duration: 0.5, onComplete: () => form.classList.add('hidden') });
    
    // Show Processing
    processingView.classList.remove('hidden');
    gsap.fromTo(processingView, { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.5, delay: 0.5 });

    // Intense Bloom and Color Shift
    gsap.to(bloomPass, { strength: 4.0, duration: 0.5 });
    
    // Change particle colors to Red/Alert
    const colors = singularityGeo.attributes.color.array;
    for(let i=0; i<colors.length; i+=3) {
        colors[i] = 1.0;   // R
        colors[i+1] = 0.2; // G
        colors[i+2] = 0.2; // B
    }
    singularityGeo.attributes.color.needsUpdate = true;
}

function stopWarpAnimation() {
    isWarping = false;
    baseRotationSpeed = 0.001;
    
    // Restore Bloom
    gsap.to(bloomPass, { strength: 2.0, duration: 1.5 });

    // Restore particle colors
    const colors = singularityGeo.attributes.color.array;
    for(let i=0; i<colors.length; i+=3) {
        colors[i] = 0.0;   // R
        colors[i+1] = 1.0; // G
        colors[i+2] = 1.0; // B
    }
    singularityGeo.attributes.color.needsUpdate = true;

    // Transition UI
    gsap.to(processingView, { opacity: 0, scale: 1.2, duration: 0.5, onComplete: () => processingView.classList.add('hidden') });
    
    resultsView.classList.remove('hidden');
    gsap.fromTo(resultsView, 
        { opacity: 0, y: 30 }, 
        { opacity: 1, y: 0, duration: 1, delay: 0.5, ease: "power2.out" }
    );
}

function resetUI() {
    gsap.to(resultsView, { opacity: 0, y: -30, duration: 0.5, onComplete: () => {
        resultsView.classList.add('hidden');
        form.classList.remove('hidden');
        input.value = '';
        gsap.fromTo(form, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5 });
    }});
}

// --- EVENT LISTENERS ---

btnInit.addEventListener('click', transitionToCommand);

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if(!query) return;

    triggerWarpAnimation();

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: query, enhanced: enhancedMode.checked }),
        });

        const data = await response.json();
        
        // Wait a minimum time for the warp effect to look cool
        setTimeout(() => {
            if (!response.ok) {
                verdictPrimary.textContent = "SYSTEM ERROR: " + (data.error || "Unknown");
                verdictPrimary.style.color = "var(--accent-alert)";
            } else {
                populateResults(data.result);
            }
            stopWarpAnimation();
        }, 3000);

    } catch (error) {
        setTimeout(() => {
            verdictPrimary.textContent = "UPLINK SEVERED";
            verdictPrimary.style.color = "var(--accent-alert)";
            stopWarpAnimation();
        }, 2000);
    }
});

btnReset.addEventListener('click', resetUI);

function populateResults(result) {
    const v = result.verdict || {};
    
    verdictPrimary.textContent = v.majority_verdict || "INCONCLUSIVE";
    verdictPrimary.style.color = "var(--text-main)";
    
    resPattern.textContent = v.key_pattern || "None detected.";
    resPrecedent.textContent = v.historical_precedent || "No historical match.";
    resReasoning.textContent = v.reasoning || "Data insufficient for full reasoning construct.";

    const conf = Number(v.confidence || 0);
    confVal.textContent = conf + "%";
    
    // Animate confidence bar
    setTimeout(() => {
        confFill.style.width = conf + "%";
    }, 500);
}

// Start ThreeJS
initThreeJS();
