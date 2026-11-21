/* ========================================
   POLITICORE — Three.js Scene Manager
   3D Environment, Particles, Post-Processing
   God Rays, Lens Flares, Volumetric Lighting
   ======================================== */

const POLITICORE = window.POLITICORE || {};
window.POLITICORE = POLITICORE;

(function() {
    'use strict';

    // ---- Scene Configuration ----
    const CONFIG = {
        particleCount: 800,
        orbCount: 14,
        bgColor: 0x05080f,
        bloomStrength: 1.4,
        bloomRadius: 0.7,
        bloomThreshold: 0.12,
        cameraFOV: 60,
        cameraNear: 0.1,
        cameraFar: 2000,
        cameraZ: 50,
        mouseInfluence: 0.0003,
        godRayCount: 3,
    };

    let scene, camera, renderer, composer;
    let particles, particleGeo, particleMat;
    let orbs = [];
    let godRays = [];
    let lensFlares = [];
    let clock, mouseX = 0, mouseY = 0;
    let targetCameraX = 0, targetCameraY = 0;
    let animationId;
    let gridHelper;

    // ---- Create Circular Particle Texture ----
    function createCircularTexture(size, color, softness) {
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        const half = size / 2;

        const gradient = ctx.createRadialGradient(half, half, 0, half, half, half);
        gradient.addColorStop(0, color || 'rgba(255,255,255,1)');
        gradient.addColorStop(softness || 0.3, color || 'rgba(255,255,255,0.6)');
        gradient.addColorStop(0.7, 'rgba(255,255,255,0.1)');
        gradient.addColorStop(1, 'rgba(255,255,255,0)');

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);

        const tex = new THREE.CanvasTexture(canvas);
        tex.needsUpdate = true;
        return tex;
    }

    // ---- Create Glow Sprite Texture ----
    function createGlowTexture(size) {
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        const half = size / 2;

        const gradient = ctx.createRadialGradient(half, half, 0, half, half, half);
        gradient.addColorStop(0, 'rgba(255,255,255,0.4)');
        gradient.addColorStop(0.15, 'rgba(255,255,255,0.2)');
        gradient.addColorStop(0.4, 'rgba(255,255,255,0.06)');
        gradient.addColorStop(0.7, 'rgba(255,255,255,0.01)');
        gradient.addColorStop(1, 'rgba(255,255,255,0)');

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);

        const tex = new THREE.CanvasTexture(canvas);
        tex.needsUpdate = true;
        return tex;
    }

    // ---- Create Lens Flare Texture ----
    function createFlareTexture(size, rings) {
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        const half = size / 2;

        // Central bright core
        const coreGrad = ctx.createRadialGradient(half, half, 0, half, half, half * 0.3);
        coreGrad.addColorStop(0, 'rgba(255,255,255,0.9)');
        coreGrad.addColorStop(0.5, 'rgba(200,230,255,0.3)');
        coreGrad.addColorStop(1, 'rgba(200,230,255,0)');
        ctx.fillStyle = coreGrad;
        ctx.fillRect(0, 0, size, size);

        // Horizontal streak
        const streakGrad = ctx.createLinearGradient(0, half, size, half);
        streakGrad.addColorStop(0, 'rgba(0,229,255,0)');
        streakGrad.addColorStop(0.3, 'rgba(0,229,255,0.05)');
        streakGrad.addColorStop(0.5, 'rgba(0,229,255,0.15)');
        streakGrad.addColorStop(0.7, 'rgba(0,229,255,0.05)');
        streakGrad.addColorStop(1, 'rgba(0,229,255,0)');
        ctx.fillStyle = streakGrad;
        ctx.fillRect(0, half - 2, size, 4);

        // Outer glow
        const outerGrad = ctx.createRadialGradient(half, half, half * 0.2, half, half, half);
        outerGrad.addColorStop(0, 'rgba(0,229,255,0.08)');
        outerGrad.addColorStop(0.5, 'rgba(224,64,251,0.04)');
        outerGrad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = outerGrad;
        ctx.fillRect(0, 0, size, size);

        if (rings) {
            ctx.strokeStyle = 'rgba(0,229,255,0.06)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(half, half, half * 0.6, 0, Math.PI * 2);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(half, half, half * 0.8, 0, Math.PI * 2);
            ctx.stroke();
        }

        const tex = new THREE.CanvasTexture(canvas);
        tex.needsUpdate = true;
        return tex;
    }

    // ---- God Ray Texture ----
    function createGodRayTexture(width, height) {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');

        const gradient = ctx.createLinearGradient(width / 2, 0, width / 2, height);
        gradient.addColorStop(0, 'rgba(0,229,255,0.06)');
        gradient.addColorStop(0.3, 'rgba(0,229,255,0.03)');
        gradient.addColorStop(0.7, 'rgba(224,64,251,0.02)');
        gradient.addColorStop(1, 'rgba(0,0,0,0)');

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.moveTo(width * 0.35, 0);
        ctx.lineTo(width * 0.65, 0);
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fill();

        const tex = new THREE.CanvasTexture(canvas);
        tex.needsUpdate = true;
        return tex;
    }

    // ---- Initialize Scene ----
    function init() {
        clock = new THREE.Clock();

        // Scene
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(CONFIG.bgColor, 0.007);

        // Camera
        camera = new THREE.PerspectiveCamera(
            CONFIG.cameraFOV,
            window.innerWidth / window.innerHeight,
            CONFIG.cameraNear,
            CONFIG.cameraFar
        );
        camera.position.set(0, 5, CONFIG.cameraZ);
        camera.lookAt(0, 0, 0);

        // Renderer
        const canvas = document.getElementById('three-canvas');
        renderer = new THREE.WebGLRenderer({
            canvas,
            antialias: true,
            alpha: false,
            powerPreference: 'high-performance'
        });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;

        // Post-processing (Bloom)
        setupPostProcessing();

        // Environment
        createAmbientParticles();
        createFloatingOrbs();
        createGridFloor();
        createAmbientLights();
        createGodRays();
        createLensFlares();

        // Events
        window.addEventListener('resize', onResize, false);
        window.addEventListener('mousemove', onMouseMove, false);

        // Expose globally
        POLITICORE.scene = scene;
        POLITICORE.camera = camera;
        POLITICORE.renderer = renderer;
        POLITICORE.config = CONFIG;

        // Start loop
        animate();

        // Loading sequence
        setTimeout(() => {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
                setTimeout(() => overlay.remove(), 800);
            }
        }, 2200);
    }

    // ---- Post-Processing ----
    function setupPostProcessing() {
        composer = new THREE.EffectComposer(renderer);
        const renderPass = new THREE.RenderPass(scene, camera);
        composer.addPass(renderPass);

        const bloomPass = new THREE.UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            CONFIG.bloomStrength,
            CONFIG.bloomRadius,
            CONFIG.bloomThreshold
        );
        composer.addPass(bloomPass);
        POLITICORE.bloomPass = bloomPass;
    }

    // ---- Ambient Particles ----
    function createAmbientParticles() {
        const count = CONFIG.particleCount;
        particleGeo = new THREE.BufferGeometry();
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const sizes = new Float32Array(count);
        const velocities = new Float32Array(count * 3);

        const cyanColor = new THREE.Color(0x00e5ff);
        const magentaColor = new THREE.Color(0xe040fb);
        const goldColor = new THREE.Color(0xffd740);
        const dimCyan = new THREE.Color(0x005577);

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            positions[i3] = (Math.random() - 0.5) * 200;
            positions[i3 + 1] = (Math.random() - 0.5) * 120;
            positions[i3 + 2] = (Math.random() - 0.5) * 200;

            // Random color distribution
            const r = Math.random();
            let color;
            if (r < 0.4) color = cyanColor;
            else if (r < 0.55) color = dimCyan;
            else if (r < 0.75) color = magentaColor;
            else if (r < 0.9) color = goldColor;
            else color = new THREE.Color(0xffffff);

            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;

            sizes[i] = Math.random() * 3.0 + 0.3;

            velocities[i3] = (Math.random() - 0.5) * 0.012;
            velocities[i3 + 1] = (Math.random() - 0.5) * 0.008;
            velocities[i3 + 2] = (Math.random() - 0.5) * 0.012;
        }

        particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        particleGeo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        particleGeo._velocities = velocities;

        // Use circular texture for particles
        const particleTexture = createCircularTexture(64);

        particleMat = new THREE.PointsMaterial({
            size: 1.5,
            map: particleTexture,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            sizeAttenuation: true,
        });

        particles = new THREE.Points(particleGeo, particleMat);
        scene.add(particles);
    }

    // ---- Floating Orbs ----
    function createFloatingOrbs() {
        const orbGeo = new THREE.SphereGeometry(0.5, 24, 24);
        const colors = [0x00e5ff, 0xe040fb, 0xffd740, 0x00e676, 0xff1744, 0x448aff, 0xb388ff];
        const glowTexture = createGlowTexture(128);

        for (let i = 0; i < CONFIG.orbCount; i++) {
            const color = colors[i % colors.length];
            const mat = new THREE.MeshBasicMaterial({
                color,
                transparent: true,
                opacity: 0.5,
            });
            const orb = new THREE.Mesh(orbGeo, mat);

            // Add soft glow sprite with circular texture
            const glowMat = new THREE.SpriteMaterial({
                map: glowTexture,
                color,
                transparent: true,
                opacity: 0.2,
                blending: THREE.AdditiveBlending,
            });
            const glow = new THREE.Sprite(glowMat);
            glow.scale.set(5, 5, 1);
            orb.add(glow);

            // Position in orbit
            const angle = (i / CONFIG.orbCount) * Math.PI * 2;
            const radius = 22 + Math.random() * 25;
            orb.position.set(
                Math.cos(angle) * radius,
                (Math.random() - 0.5) * 25,
                Math.sin(angle) * radius
            );

            orb.userData = {
                angle,
                radius,
                speed: 0.0002 + Math.random() * 0.0006,
                yOffset: (Math.random() - 0.5) * 20,
                ySpeed: 0.0005 + Math.random() * 0.001,
                baseY: orb.position.y,
            };

            orbs.push(orb);
            scene.add(orb);
        }
    }

    // ---- Grid Floor ----
    function createGridFloor() {
        const gridSize = 250;
        const gridDivisions = 50;
        gridHelper = new THREE.GridHelper(gridSize, gridDivisions, 0x061a30, 0x061a30);
        gridHelper.position.y = -30;
        gridHelper.material.transparent = true;
        gridHelper.material.opacity = 0.2;
        scene.add(gridHelper);

        // Ground glow plane
        const planeGeo = new THREE.PlaneGeometry(500, 500);
        const planeMat = new THREE.MeshBasicMaterial({
            color: 0x00e5ff,
            transparent: true,
            opacity: 0.012,
            side: THREE.DoubleSide,
        });
        const plane = new THREE.Mesh(planeGeo, planeMat);
        plane.rotation.x = -Math.PI / 2;
        plane.position.y = -30.1;
        scene.add(plane);
    }

    // ---- Ambient Lights ----
    function createAmbientLights() {
        const ambient = new THREE.AmbientLight(0x0a1e3c, 0.5);
        scene.add(ambient);

        // Key light (cyan tint)
        const keyLight = new THREE.PointLight(0x00e5ff, 1.5, 160);
        keyLight.position.set(30, 40, 30);
        scene.add(keyLight);

        // Fill light (magenta tint)
        const fillLight = new THREE.PointLight(0xe040fb, 0.6, 130);
        fillLight.position.set(-40, 20, -30);
        scene.add(fillLight);

        // Rim light (gold)
        const rimLight = new THREE.PointLight(0xffd740, 0.4, 110);
        rimLight.position.set(0, -25, -40);
        scene.add(rimLight);

        // Additional dim blue uplighting
        const upLight = new THREE.PointLight(0x0044aa, 0.3, 100);
        upLight.position.set(0, -30, 0);
        scene.add(upLight);
    }

    // ---- God Rays ----
    function createGodRays() {
        const godRayTexture = createGodRayTexture(128, 512);

        const rayConfigs = [
            { x: -20, y: 60, z: -30, rotZ: 0.15, scale: [25, 80, 1], opacity: 0.08, color: 0x00e5ff },
            { x: 25, y: 65, z: -25, rotZ: -0.12, scale: [20, 70, 1], opacity: 0.06, color: 0x6040fb },
            { x: 5, y: 70, z: -35, rotZ: 0.05, scale: [30, 90, 1], opacity: 0.05, color: 0x00a5c4 },
        ];

        rayConfigs.forEach(cfg => {
            const mat = new THREE.SpriteMaterial({
                map: godRayTexture,
                color: cfg.color,
                transparent: true,
                opacity: 0,
                blending: THREE.AdditiveBlending,
                depthWrite: false,
                rotation: cfg.rotZ,
            });
            const ray = new THREE.Sprite(mat);
            ray.position.set(cfg.x, cfg.y, cfg.z);
            ray.scale.set(cfg.scale[0], cfg.scale[1], cfg.scale[2]);
            ray.userData = { baseOpacity: cfg.opacity, phaseOffset: Math.random() * Math.PI * 2 };
            scene.add(ray);
            godRays.push(ray);

            // Fade in
            gsap.to(mat, { opacity: cfg.opacity, duration: 3, delay: 1 + Math.random() * 2 });
        });
    }

    // ---- Lens Flares ----
    function createLensFlares() {
        const flareTexture = createFlareTexture(128, true);
        const smallFlareTexture = createFlareTexture(64, false);

        const flareConfigs = [
            { x: 30, y: 30, z: -20, scale: 12, opacity: 0.12, color: 0x00e5ff },
            { x: -35, y: 20, z: -15, scale: 8, opacity: 0.08, color: 0xe040fb },
            { x: 15, y: -10, z: -25, scale: 6, opacity: 0.06, color: 0xffd740 },
            { x: -10, y: 40, z: -30, scale: 10, opacity: 0.1, color: 0x00ccff },
        ];

        flareConfigs.forEach((cfg, i) => {
            const tex = i < 2 ? flareTexture : smallFlareTexture;
            const mat = new THREE.SpriteMaterial({
                map: tex,
                color: cfg.color,
                transparent: true,
                opacity: 0,
                blending: THREE.AdditiveBlending,
                depthWrite: false,
            });
            const flare = new THREE.Sprite(mat);
            flare.position.set(cfg.x, cfg.y, cfg.z);
            flare.scale.set(cfg.scale, cfg.scale, 1);
            flare.userData = {
                baseOpacity: cfg.opacity,
                phaseOffset: Math.random() * Math.PI * 2,
                driftSpeed: 0.0002 + Math.random() * 0.0003,
                basePos: new THREE.Vector3(cfg.x, cfg.y, cfg.z),
            };
            scene.add(flare);
            lensFlares.push(flare);

            // Fade in
            gsap.to(mat, { opacity: cfg.opacity, duration: 2.5, delay: 2 + Math.random() * 2 });
        });
    }

    // ---- Animation Loop ----
    function animate() {
        animationId = requestAnimationFrame(animate);
        const delta = clock.getDelta();
        const elapsed = clock.getElapsedTime();

        // Smooth camera follow mouse
        targetCameraX += (mouseX * CONFIG.mouseInfluence - targetCameraX) * 0.02;
        targetCameraY += (mouseY * CONFIG.mouseInfluence - targetCameraY) * 0.02;
        camera.position.x += (targetCameraX * 15 - camera.position.x) * 0.01;
        camera.position.y += (5 + targetCameraY * 8 - camera.position.y) * 0.01;
        camera.lookAt(0, 0, 0);

        // Animate particles
        if (particles) {
            const pos = particleGeo.attributes.position.array;
            const vel = particleGeo._velocities;
            for (let i = 0; i < pos.length; i += 3) {
                pos[i] += vel[i];
                pos[i + 1] += vel[i + 1];
                pos[i + 2] += vel[i + 2];

                // Wrap around
                if (pos[i] > 100) pos[i] = -100;
                if (pos[i] < -100) pos[i] = 100;
                if (pos[i + 1] > 60) pos[i + 1] = -60;
                if (pos[i + 1] < -60) pos[i + 1] = 60;
                if (pos[i + 2] > 100) pos[i + 2] = -100;
                if (pos[i + 2] < -100) pos[i + 2] = 100;
            }
            particleGeo.attributes.position.needsUpdate = true;
            particles.rotation.y += 0.00008;
        }

        // Animate floating orbs
        for (const orb of orbs) {
            const d = orb.userData;
            d.angle += d.speed;
            orb.position.x = Math.cos(d.angle) * d.radius;
            orb.position.z = Math.sin(d.angle) * d.radius;
            orb.position.y = d.baseY + Math.sin(elapsed * d.ySpeed * 5) * 4;

            // Pulsing opacity
            orb.material.opacity = 0.3 + Math.sin(elapsed * 1.2 + d.angle) * 0.15;
        }

        // Grid subtle animation
        if (gridHelper) {
            gridHelper.material.opacity = 0.18 + Math.sin(elapsed * 0.3) * 0.04;
        }

        // Animate God Rays
        for (const ray of godRays) {
            const d = ray.userData;
            ray.material.opacity = d.baseOpacity + Math.sin(elapsed * 0.4 + d.phaseOffset) * d.baseOpacity * 0.4;
        }

        // Animate Lens Flares
        for (const flare of lensFlares) {
            const d = flare.userData;
            flare.material.opacity = d.baseOpacity + Math.sin(elapsed * 0.6 + d.phaseOffset) * d.baseOpacity * 0.5;
            // Subtle drift
            flare.position.x = d.basePos.x + Math.sin(elapsed * d.driftSpeed * 100 + d.phaseOffset) * 2;
            flare.position.y = d.basePos.y + Math.cos(elapsed * d.driftSpeed * 80 + d.phaseOffset) * 1.5;
        }

        // Render
        if (composer) {
            composer.render();
        } else {
            renderer.render(scene, camera);
        }
    }

    // ---- Events ----
    function onResize() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        if (composer) {
            composer.setSize(window.innerWidth, window.innerHeight);
        }
    }

    function onMouseMove(e) {
        mouseX = e.clientX - window.innerWidth / 2;
        mouseY = e.clientY - window.innerHeight / 2;
    }

    // ---- Particle Burst (for execute animation) ----
    POLITICORE.triggerParticleBurst = function() {
        if (!particleGeo) return;
        const vel = particleGeo._velocities;
        for (let i = 0; i < vel.length; i += 3) {
            vel[i] = (Math.random() - 0.5) * 0.25;
            vel[i + 1] = (Math.random() - 0.5) * 0.18;
            vel[i + 2] = (Math.random() - 0.5) * 0.25;
        }

        // Intensify god rays during burst
        godRays.forEach(ray => {
            gsap.to(ray.material, { opacity: ray.userData.baseOpacity * 3, duration: 0.5 });
        });

        // Intensify lens flares during burst
        lensFlares.forEach(flare => {
            gsap.to(flare.material, { opacity: flare.userData.baseOpacity * 4, duration: 0.4 });
        });

        // Slow them back down after a moment
        setTimeout(() => {
            for (let i = 0; i < vel.length; i += 3) {
                vel[i] = (Math.random() - 0.5) * 0.012;
                vel[i + 1] = (Math.random() - 0.5) * 0.008;
                vel[i + 2] = (Math.random() - 0.5) * 0.012;
            }

            // Restore god rays
            godRays.forEach(ray => {
                gsap.to(ray.material, { opacity: ray.userData.baseOpacity, duration: 1.5 });
            });

            // Restore lens flares
            lensFlares.forEach(flare => {
                gsap.to(flare.material, { opacity: flare.userData.baseOpacity, duration: 1.5 });
            });
        }, 2000);
    };

    // ---- Bloom Pulse ----
    POLITICORE.pulseBloom = function(strength, duration) {
        const bp = POLITICORE.bloomPass;
        if (!bp) return;
        const orig = bp.strength;
        bp.strength = strength || 2.5;
        setTimeout(() => {
            const fade = setInterval(() => {
                bp.strength -= 0.04;
                if (bp.strength <= orig) {
                    bp.strength = orig;
                    clearInterval(fade);
                }
            }, 25);
        }, duration || 600);
    };

    // ---- Init on DOM ready ----
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
