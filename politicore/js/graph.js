/* ========================================
   POLITICORE — 3D Knowledge Graph Engine
   Force-directed graph with nodes & edges
   ======================================== */

(function() {
    'use strict';

    const P = window.POLITICORE;

    // ---- Shared textures ----
    let glowSpriteTexture = null;

    function getGlowTexture() {
        if (glowSpriteTexture) return glowSpriteTexture;
        const size = 128;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        const half = size / 2;
        const gradient = ctx.createRadialGradient(half, half, 0, half, half, half);
        gradient.addColorStop(0, 'rgba(255,255,255,0.5)');
        gradient.addColorStop(0.2, 'rgba(255,255,255,0.2)');
        gradient.addColorStop(0.5, 'rgba(255,255,255,0.05)');
        gradient.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);
        glowSpriteTexture = new THREE.CanvasTexture(canvas);
        glowSpriteTexture.needsUpdate = true;
        return glowSpriteTexture;
    }

    // ---- Graph Data ----
    const NODE_TYPES = {
        politician: { color: 0x00e5ff, size: 1.8, label: 'POLITICIAN' },
        party:      { color: 0xe040fb, size: 2.2, label: 'PARTY' },
        event:      { color: 0xffd740, size: 1.5, label: 'EVENT' },
        policy:     { color: 0x00e676, size: 1.6, label: 'POLICY' },
        scandal:    { color: 0xff1744, size: 1.4, label: 'SCANDAL' },
        trend:      { color: 0xff9100, size: 1.3, label: 'TREND' },
        media:      { color: 0x448aff, size: 1.2, label: 'MEDIA' },
        lobby:      { color: 0xb388ff, size: 1.5, label: 'LOBBY' },
    };

    // Simulated analysis data sets
    const GRAPH_DATASETS = {
        alliances: {
            nodes: [
                { id: 'n1', label: 'Sen. Wheeler', type: 'politician' },
                { id: 'n2', label: 'Rep. Harding', type: 'politician' },
                { id: 'n3', label: 'Gov. Chen', type: 'politician' },
                { id: 'n4', label: 'Liberty Party', type: 'party' },
                { id: 'n5', label: 'Unity Coalition', type: 'party' },
                { id: 'n6', label: 'Green Alliance', type: 'party' },
                { id: 'n7', label: 'Trade Reform Act', type: 'policy' },
                { id: 'n8', label: 'Campaign Finance Scandal', type: 'scandal' },
                { id: 'n9', label: 'Election 2026', type: 'event' },
                { id: 'n10', label: 'PAC Nexus Corp', type: 'lobby' },
                { id: 'n11', label: 'Voter Bloc Shift', type: 'trend' },
                { id: 'n12', label: 'Sen. Morales', type: 'politician' },
                { id: 'n13', label: 'Healthcare Bill', type: 'policy' },
                { id: 'n14', label: 'Media Spin Cycle', type: 'media' },
                { id: 'n15', label: 'Rep. Davis', type: 'politician' },
                { id: 'n16', label: 'Tax Code Overhaul', type: 'policy' },
                { id: 'n17', label: 'Patriot Front', type: 'party' },
                { id: 'n18', label: 'Data Leak Incident', type: 'scandal' },
            ],
            edges: [
                { from: 'n1', to: 'n4', strength: 0.9 },
                { from: 'n2', to: 'n5', strength: 0.7 },
                { from: 'n3', to: 'n6', strength: 0.85 },
                { from: 'n1', to: 'n2', strength: 0.6 },
                { from: 'n4', to: 'n5', strength: 0.5 },
                { from: 'n7', to: 'n1', strength: 0.75 },
                { from: 'n7', to: 'n3', strength: 0.65 },
                { from: 'n8', to: 'n2', strength: 0.8 },
                { from: 'n8', to: 'n10', strength: 0.9 },
                { from: 'n9', to: 'n4', strength: 0.7 },
                { from: 'n9', to: 'n5', strength: 0.6 },
                { from: 'n10', to: 'n1', strength: 0.55 },
                { from: 'n11', to: 'n9', strength: 0.85 },
                { from: 'n11', to: 'n6', strength: 0.4 },
                { from: 'n12', to: 'n5', strength: 0.7 },
                { from: 'n12', to: 'n13', strength: 0.9 },
                { from: 'n13', to: 'n3', strength: 0.6 },
                { from: 'n14', to: 'n8', strength: 0.75 },
                { from: 'n14', to: 'n9', strength: 0.5 },
                { from: 'n15', to: 'n17', strength: 0.8 },
                { from: 'n15', to: 'n16', strength: 0.7 },
                { from: 'n16', to: 'n10', strength: 0.65 },
                { from: 'n17', to: 'n4', strength: 0.3 },
                { from: 'n18', to: 'n15', strength: 0.85 },
                { from: 'n18', to: 'n14', strength: 0.6 },
                { from: 'n12', to: 'n1', strength: 0.45 },
            ],
        },
    };

    // Graph state
    let graphGroup = null;
    let graphNodes = [];
    let graphEdges = [];
    let nodeObjects = {};
    let hoveredNode = null;
    let raycaster, mouseVec;
    let isBuilt = false;

    // ---- Initialize Graph System ----
    function init() {
        graphGroup = new THREE.Group();
        P.scene.add(graphGroup);

        raycaster = new THREE.Raycaster();
        mouseVec = new THREE.Vector2();

        // Always show idle graph
        buildIdleGraph();

        // Mouse interaction
        window.addEventListener('mousemove', onGraphMouseMove, false);
        window.addEventListener('click', onGraphClick, false);

        P.graphGroup = graphGroup;
        P.buildAnalysisGraph = buildAnalysisGraph;
        P.clearGraph = clearGraph;
        P.graphNodes = graphNodes;
    }

    // ---- Idle Graph (subtle ambient) ----
    function buildIdleGraph() {
        const idleCount = 8;
        for (let i = 0; i < idleCount; i++) {
            const angle = (i / idleCount) * Math.PI * 2;
            const r = 12 + Math.random() * 5;
            const pos = new THREE.Vector3(
                Math.cos(angle) * r,
                (Math.random() - 0.5) * 8,
                Math.sin(angle) * r
            );
            const types = Object.keys(NODE_TYPES);
            const type = types[i % types.length];
            createNode('idle_' + i, '', type, pos, 0.5);
        }

        // Subtle idle edges
        for (let i = 0; i < idleCount; i++) {
            const j = (i + 1) % idleCount;
            if (graphNodes[i] && graphNodes[j]) {
                createEdge(graphNodes[i], graphNodes[j], 0.2, true);
            }
        }
    }

    // ---- Create Node ----
    function createNode(id, label, type, position, opacity) {
        const typeConfig = NODE_TYPES[type] || NODE_TYPES.event;
        const baseOpacity = opacity !== undefined ? opacity : 1;

        // Core sphere
        const geo = new THREE.SphereGeometry(typeConfig.size, 24, 24);
        const mat = new THREE.MeshPhongMaterial({
            color: typeConfig.color,
            transparent: true,
            opacity: 0,
            emissive: typeConfig.color,
            emissiveIntensity: 0.3,
            shininess: 80,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.copy(position);

        // Outer glow ring
        const ringGeo = new THREE.RingGeometry(typeConfig.size + 0.6, typeConfig.size + 0.9, 32);
        const ringMat = new THREE.MeshBasicMaterial({
            color: typeConfig.color,
            transparent: true,
            opacity: 0,
            side: THREE.DoubleSide,
            blending: THREE.AdditiveBlending,
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.lookAt(P.camera.position);
        mesh.add(ring);

        // Glow sprite (with circular texture)
        const spriteMat = new THREE.SpriteMaterial({
            map: getGlowTexture(),
            color: typeConfig.color,
            transparent: true,
            opacity: 0,
            blending: THREE.AdditiveBlending,
        });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.scale.set(typeConfig.size * 4.5, typeConfig.size * 4.5, 1);
        mesh.add(sprite);

        mesh.userData = {
            id,
            label,
            type,
            typeConfig,
            ring,
            sprite,
            ringMat,
            spriteMat,
            targetOpacity: baseOpacity,
            basePosition: position.clone(),
            velocity: new THREE.Vector3(),
            isIdle: opacity < 1,
        };

        graphGroup.add(mesh);
        graphNodes.push(mesh);
        nodeObjects[id] = mesh;

        // Animate in
        gsap.to(mat, { opacity: baseOpacity, duration: 0.8, delay: Math.random() * 0.5 });
        gsap.to(ringMat, { opacity: baseOpacity * 0.3, duration: 0.8, delay: Math.random() * 0.5 });
        gsap.to(spriteMat, { opacity: baseOpacity * 0.12, duration: 0.8, delay: Math.random() * 0.5 });

        return mesh;
    }

    // ---- Create Edge ----
    function createEdge(nodeA, nodeB, strength, isIdle) {
        const points = [nodeA.position, nodeB.position];
        const geo = new THREE.BufferGeometry().setFromPoints(points);

        // Color based on strength
        const color = new THREE.Color().lerpColors(
            new THREE.Color(0x0a2540),
            new THREE.Color(0x00e5ff),
            strength
        );

        const mat = new THREE.LineBasicMaterial({
            color,
            transparent: true,
            opacity: 0,
            blending: THREE.AdditiveBlending,
            linewidth: 1,
        });
        const line = new THREE.Line(geo, mat);

        line.userData = {
            nodeA,
            nodeB,
            strength,
            isIdle: !!isIdle,
            pulseOffset: Math.random() * Math.PI * 2,
        };

        graphGroup.add(line);
        graphEdges.push(line);

        const targetOpacity = isIdle ? 0.1 : Math.max(0.15, strength * 0.5);
        gsap.to(mat, { opacity: targetOpacity, duration: 1.0, delay: Math.random() * 0.8 });

        return line;
    }

    // ---- Build Analysis Graph (called on Execute) ----
    function buildAnalysisGraph(callback) {
        clearGraph();
        isBuilt = false;

        const data = GRAPH_DATASETS.alliances;
        const totalNodes = data.nodes.length;
        let builtNodes = 0;

        // Build nodes one by one with delay
        data.nodes.forEach((nodeData, i) => {
            setTimeout(() => {
                // Position using 3D layout
                const phi = Math.acos(-1 + (2 * i) / totalNodes);
                const theta = Math.sqrt(totalNodes * Math.PI) * phi;
                const radius = 15 + Math.random() * 8;

                const pos = new THREE.Vector3(
                    radius * Math.cos(theta) * Math.sin(phi),
                    radius * Math.cos(phi) * 0.6,
                    radius * Math.sin(theta) * Math.sin(phi)
                );

                createNode(nodeData.id, nodeData.label, nodeData.type, pos, 1.0);
                builtNodes++;

                // Update UI counter
                const counter = document.getElementById('node-count');
                if (counter) counter.textContent = builtNodes;

                // After all nodes, build edges
                if (builtNodes === totalNodes) {
                    setTimeout(() => buildEdges(data.edges, callback), 300);
                }
            }, i * 120);
        });
    }

    function buildEdges(edgesData, callback) {
        let builtEdges = 0;
        edgesData.forEach((edgeData, i) => {
            setTimeout(() => {
                const nA = nodeObjects[edgeData.from];
                const nB = nodeObjects[edgeData.to];
                if (nA && nB) {
                    createEdge(nA, nB, edgeData.strength, false);
                }
                builtEdges++;

                const counter = document.getElementById('pattern-count');
                if (counter) counter.textContent = builtEdges;

                if (builtEdges === edgesData.length) {
                    isBuilt = true;
                    if (callback) callback();
                }
            }, i * 80);
        });
    }

    // ---- Clear Graph ----
    function clearGraph() {
        graphNodes.forEach(n => {
            graphGroup.remove(n);
            n.geometry.dispose();
            n.material.dispose();
        });
        graphEdges.forEach(e => {
            graphGroup.remove(e);
            e.geometry.dispose();
            e.material.dispose();
        });
        graphNodes = [];
        graphEdges = [];
        nodeObjects = {};
        P.graphNodes = graphNodes;
    }

    // ---- Force Simulation Update (called from animLoop) ----
    function updateForceSimulation(elapsed) {
        if (!isBuilt) return;

        // Gentle rotation of graph group
        graphGroup.rotation.y += 0.0008;

        // Node bobbing
        graphNodes.forEach((node, i) => {
            if (!node.userData.isIdle) {
                node.position.y = node.userData.basePosition.y +
                    Math.sin(elapsed * 0.8 + i * 0.5) * 0.4;
            }

            // Ring always faces camera
            if (node.userData.ring) {
                node.userData.ring.lookAt(P.camera.position);
            }
        });

        // Edge updates (keep connected)
        graphEdges.forEach(edge => {
            const { nodeA, nodeB, pulseOffset } = edge.userData;
            if (nodeA && nodeB) {
                const positions = edge.geometry.attributes.position;
                positions.setXYZ(0, nodeA.position.x, nodeA.position.y, nodeA.position.z);
                positions.setXYZ(1, nodeB.position.x, nodeB.position.y, nodeB.position.z);
                positions.needsUpdate = true;

                // Pulse opacity
                if (!edge.userData.isIdle) {
                    const pulse = Math.sin(elapsed * 2 + pulseOffset) * 0.1;
                    edge.material.opacity = Math.max(0.1, edge.userData.strength * 0.4 + pulse);
                }
            }
        });
    }

    // ---- Hover Detection ----
    function onGraphMouseMove(e) {
        mouseVec.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouseVec.y = -(e.clientY / window.innerHeight) * 2 + 1;

        raycaster.setFromCamera(mouseVec, P.camera);
        const intersects = raycaster.intersectObjects(graphNodes, false);

        // Reset previous
        if (hoveredNode) {
            const d = hoveredNode.userData;
            gsap.to(hoveredNode.scale, { x: 1, y: 1, z: 1, duration: 0.3 });
            gsap.to(d.ringMat, { opacity: d.targetOpacity * 0.3, duration: 0.3 });
            gsap.to(hoveredNode.material, { emissiveIntensity: 0.3, duration: 0.3 });
            hoveredNode = null;
            document.body.style.cursor = 'default';
        }

        if (intersects.length > 0) {
            const node = intersects[0].object;
            if (node.userData.id) {
                hoveredNode = node;
                gsap.to(node.scale, { x: 1.4, y: 1.4, z: 1.4, duration: 0.3 });
                gsap.to(node.userData.ringMat, { opacity: 0.6, duration: 0.3 });
                gsap.to(node.material, { emissiveIntensity: 0.8, duration: 0.3 });
                document.body.style.cursor = 'pointer';
            }
        }
    }

    function onGraphClick(e) {
        if (!hoveredNode || !hoveredNode.userData.label) return;
        const data = hoveredNode.userData;

        // Highlight connected edges
        graphEdges.forEach(edge => {
            const { nodeA, nodeB } = edge.userData;
            if (nodeA === hoveredNode || nodeB === hoveredNode) {
                gsap.to(edge.material, { opacity: 0.9, duration: 0.3 });
                gsap.to(edge.material.color, { r: 1, g: 0.85, b: 0.2, duration: 0.3 });
                setTimeout(() => {
                    gsap.to(edge.material, { opacity: edge.userData.strength * 0.4, duration: 0.8 });
                    const color = new THREE.Color().lerpColors(
                        new THREE.Color(0x0a2540),
                        new THREE.Color(0x00e5ff),
                        edge.userData.strength
                    );
                    gsap.to(edge.material.color, { r: color.r, g: color.g, b: color.b, duration: 0.8 });
                }, 1500);
            }
        });

        // Show tooltip / info (dispatched to UI)
        if (P.onNodeClick) P.onNodeClick(data);
    }

    // ---- Expose update for animation loop ----
    // Hook into existing animation loop
    const origAnimate = window.requestAnimationFrame;
    let graphClock = new THREE.Clock();

    function graphLoop() {
        requestAnimationFrame(graphLoop);
        const elapsed = graphClock.getElapsedTime();

        // Idle graph gentle rotation
        if (!isBuilt && graphGroup) {
            graphGroup.rotation.y += 0.001;
            graphNodes.forEach((node, i) => {
                node.position.y += Math.sin(elapsed * 0.5 + i) * 0.003;
                if (node.userData.ring) {
                    node.userData.ring.lookAt(P.camera.position);
                }
            });

            // Update idle edges
            graphEdges.forEach(edge => {
                const { nodeA, nodeB } = edge.userData;
                if (nodeA && nodeB) {
                    const positions = edge.geometry.attributes.position;
                    positions.setXYZ(0, nodeA.position.x, nodeA.position.y, nodeA.position.z);
                    positions.setXYZ(1, nodeB.position.x, nodeB.position.y, nodeB.position.z);
                    positions.needsUpdate = true;
                }
            });
        }

        updateForceSimulation(elapsed);
    }

    // Start graph loop
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { init(); graphLoop(); });
    } else {
        setTimeout(() => { init(); graphLoop(); }, 100);
    }

})();
