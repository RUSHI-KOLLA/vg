/* ========================================
   POLITICORE — UI Controller
   Interactions, Animations, Execute Flow
   ======================================== */

(function() {
    'use strict';

    const P = window.POLITICORE;

    // ---- Insight Data (simulated AI results) ----
    const INSIGHT_DATA = [
        {
            type: 'alliance',
            title: 'Shadow Coalition Forming',
            body: 'Sen. Wheeler and Rep. Harding show 73% coordination in voting patterns despite opposing parties. PAC Nexus Corp financial trails suggest coordinated funding channels established Q2 2025.',
            confidence: 94,
            nodes: ['Sen. Wheeler', 'Rep. Harding', 'PAC Nexus Corp'],
        },
        {
            type: 'prediction',
            title: 'Election Shift Probability: 78%',
            body: 'Predictive model indicates Unity Coalition will pivot alliance toward Green Alliance before election. Historical pattern match: 89% similar to 2018 realignment cycle.',
            confidence: 78,
            nodes: ['Unity Coalition', 'Green Alliance', 'Election 2026'],
        },
        {
            type: 'scandal',
            title: 'Financial Trail Anomaly Detected',
            body: 'Campaign finance irregularities traced through 3 shell entities. Connection strength between scandal and PAC Nexus Corp exceeds 90th percentile of known corruption networks.',
            confidence: 91,
            nodes: ['Campaign Finance Scandal', 'PAC Nexus Corp'],
        },
        {
            type: 'trend',
            title: 'Voter Bloc Realignment Signal',
            body: 'Suburban voter sentiment shifted +12.4% toward Green Alliance policies. Social media signal analysis suggests organic grassroots movement rather than astroturfing.',
            confidence: 85,
            nodes: ['Voter Bloc Shift', 'Green Alliance'],
        },
        {
            type: 'policy',
            title: 'Legislative Package Convergence',
            body: 'Trade Reform Act and Healthcare Bill share 67% overlap in sponsor networks. Hidden dependency: Tax Code Overhaul is a prerequisite for both, creating a legislative bottleneck.',
            confidence: 88,
            nodes: ['Trade Reform Act', 'Healthcare Bill', 'Tax Code Overhaul'],
        },
    ];

    // ---- DOM Elements ----
    let executeBtn, queryInput, insightsContainer, confidenceValue, confidenceFill;
    let statusText, statusDot;
    let isAnalyzing = false;

    // ---- Init ----
    function init() {
        executeBtn = document.getElementById('execute-btn');
        queryInput = document.getElementById('query-input');
        insightsContainer = document.getElementById('insights-container');
        confidenceValue = document.getElementById('confidence-value');
        confidenceFill = document.getElementById('confidence-fill');
        statusText = document.getElementById('status-text');
        statusDot = document.getElementById('status-dot');

        // Execute button click
        executeBtn.addEventListener('click', onExecute);

        // Preset queries
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                queryInput.value = btn.dataset.query;
                queryInput.focus();
                gsap.fromTo(queryInput, { borderColor: 'rgba(0, 229, 255, 0.5)' },
                    { borderColor: 'rgba(0, 229, 255, 0.12)', duration: 1 });
            });
        });

        // Mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Voice button (visual feedback only)
        document.getElementById('voice-btn').addEventListener('click', () => {
            const voiceBtn = document.getElementById('voice-btn');
            voiceBtn.style.boxShadow = '0 0 30px rgba(224, 64, 251, 0.5)';
            setTimeout(() => {
                voiceBtn.style.boxShadow = '';
                queryInput.value = 'What hidden alliances are forming around the upcoming election?';
            }, 1200);
        });

        // Timeline scrubber drag
        initTimelineScrubber();

        // Node click handler
        P.onNodeClick = onNodeClick;

        // Right panel toggle
        document.getElementById('right-toggle').addEventListener('click', () => {
            const panel = document.getElementById('right-panel');
            panel.style.transform = panel.style.transform === 'translateX(calc(100% + 16px))'
                ? 'translateX(0)' : 'translateX(calc(100% + 16px))';
        });
    }

    // ---- Execute Analysis ----
    function onExecute() {
        if (isAnalyzing) return;

        const query = queryInput.value.trim();
        if (!query) {
            gsap.fromTo(queryInput,
                { borderColor: 'rgba(255, 23, 68, 0.6)' },
                { borderColor: 'rgba(0, 229, 255, 0.12)', duration: 1.5 }
            );
            return;
        }

        isAnalyzing = true;
        document.body.classList.add('analysis-active');
        executeBtn.classList.add('executing');

        // Phase 1: Screen pulse
        screenPulse();
        updateStatus('ANALYZING — NEURAL PATTERN SCAN IN PROGRESS', true);

        // Phase 2: Particle burst
        setTimeout(() => {
            P.triggerParticleBurst();
            P.pulseBloom(3.0, 800);
        }, 200);

        // Phase 3: Build graph
        setTimeout(() => {
            updateStatus('BUILDING KNOWLEDGE GRAPH — MAPPING CONNECTIONS');
            P.buildAnalysisGraph(() => {
                // Phase 4: Show insights
                setTimeout(() => {
                    showInsights();
                    updateConfidence(89);
                    updateStatus('ANALYSIS COMPLETE — 18 NODES, 26 PATTERNS IDENTIFIED', false);

                    isAnalyzing = false;
                    document.body.classList.remove('analysis-active');
                    executeBtn.classList.remove('executing');

                    // Final bloom pulse
                    P.pulseBloom(2.0, 400);
                }, 600);
            });
        }, 800);
    }

    // ---- Screen Pulse ----
    function screenPulse() {
        const pulse = document.createElement('div');
        pulse.className = 'screen-pulse';
        document.body.appendChild(pulse);
        setTimeout(() => pulse.remove(), 1000);
    }

    // ---- Update Status ----
    function updateStatus(text, isActive) {
        if (statusText) {
            gsap.to(statusText, {
                opacity: 0, duration: 0.2, onComplete: () => {
                    statusText.textContent = text;
                    gsap.to(statusText, { opacity: 1, duration: 0.3 });
                }
            });
        }
    }

    // ---- Update Confidence ----
    function updateConfidence(value) {
        if (confidenceValue) {
            let current = 0;
            const interval = setInterval(() => {
                current += 1;
                confidenceValue.textContent = current + '%';
                if (current >= value) clearInterval(interval);
            }, 20);
        }
        if (confidenceFill) {
            confidenceFill.style.width = value + '%';
        }
    }

    // ---- Show Insights ----
    function showInsights() {
        insightsContainer.innerHTML = '';

        INSIGHT_DATA.forEach((insight, i) => {
            setTimeout(() => {
                const card = createInsightCard(insight);
                insightsContainer.appendChild(card);

                // Animate in
                gsap.from(card, {
                    opacity: 0,
                    y: 20,
                    scale: 0.95,
                    duration: 0.5,
                    ease: 'back.out(1.4)',
                });
            }, i * 200);
        });
    }

    // ---- Create Insight Card ----
    function createInsightCard(insight) {
        const card = document.createElement('div');
        card.className = `insight-card type-${insight.type}`;

        const confidenceColor = insight.confidence >= 90 ? 'var(--green)' :
                               insight.confidence >= 70 ? 'var(--gold)' : 'var(--red)';

        card.innerHTML = `
            <div class="insight-card-header">
                <span class="insight-type">${insight.type.toUpperCase()}</span>
                <span class="insight-confidence" style="color: ${confidenceColor}">${insight.confidence}%</span>
            </div>
            <div class="insight-title">${insight.title}</div>
            <div class="insight-body">${insight.body}</div>
            <div class="insight-nodes">
                ${insight.nodes.map(n => `<span class="insight-node-tag">${n}</span>`).join('')}
            </div>
        `;

        // Hover: highlight related nodes in graph
        card.addEventListener('mouseenter', () => {
            highlightNodes(insight.nodes, true);
        });
        card.addEventListener('mouseleave', () => {
            highlightNodes(insight.nodes, false);
        });

        return card;
    }

    // ---- Highlight Graph Nodes from Insight ----
    function highlightNodes(nodeLabels, highlight) {
        if (!P.graphNodes) return;
        P.graphNodes.forEach(node => {
            if (nodeLabels.includes(node.userData.label)) {
                if (highlight) {
                    gsap.to(node.scale, { x: 1.6, y: 1.6, z: 1.6, duration: 0.4 });
                    gsap.to(node.material, { emissiveIntensity: 1.0, duration: 0.4 });
                } else {
                    gsap.to(node.scale, { x: 1, y: 1, z: 1, duration: 0.4 });
                    gsap.to(node.material, { emissiveIntensity: 0.3, duration: 0.4 });
                }
            }
        });
    }

    // ---- Node Click Handler ----
    function onNodeClick(nodeData) {
        if (!nodeData.label) return;

        // Flash the node info briefly
        const info = document.createElement('div');
        info.className = 'floating-insight';
        info.style.left = '50%';
        info.style.top = '40%';
        info.style.transform = 'translate(-50%, -50%)';
        info.style.zIndex = '50';

        const typeConfig = nodeData.typeConfig;
        const colorStr = '#' + typeConfig.color.toString(16).padStart(6, '0');

        info.innerHTML = `
            <div class="insight-card type-${nodeData.type}" style="border-color: ${colorStr}44;">
                <div class="insight-card-header">
                    <span class="insight-type">${nodeData.type.toUpperCase()}</span>
                </div>
                <div class="insight-title">${nodeData.label}</div>
                <div class="insight-body" style="color: var(--text-dim);">
                    Node ID: ${nodeData.id} · Type: ${typeConfig.label} · Click edges to explore connections
                </div>
            </div>
        `;

        document.getElementById('insight-cards-container').appendChild(info);
        setTimeout(() => {
            gsap.to(info, { opacity: 0, y: -20, duration: 0.5, onComplete: () => info.remove() });
        }, 2500);
    }

    // ---- Timeline Scrubber ----
    function initTimelineScrubber() {
        const track = document.querySelector('.timeline-track');
        const progress = document.getElementById('timeline-progress');
        const scrubber = document.getElementById('timeline-scrubber');
        if (!track) return;

        let isDragging = false;

        const updateScrubber = (e) => {
            const rect = track.getBoundingClientRect();
            let pct = ((e.clientX - rect.left) / rect.width) * 100;
            pct = Math.max(0, Math.min(100, pct));
            progress.style.width = pct + '%';
            scrubber.style.left = pct + '%';
        };

        track.addEventListener('mousedown', (e) => {
            isDragging = true;
            updateScrubber(e);
        });

        window.addEventListener('mousemove', (e) => {
            if (isDragging) updateScrubber(e);
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
        });

        // Play button auto-animates timeline
        document.getElementById('tl-play').addEventListener('click', () => {
            let pct = 0;
            const interval = setInterval(() => {
                pct += 0.3;
                progress.style.width = pct + '%';
                scrubber.style.left = pct + '%';
                if (pct >= 100) clearInterval(interval);
            }, 30);
        });
    }

    // ---- Keyboard shortcut ----
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            onExecute();
        }
    });

    // ---- Init ----
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 200);
    }

})();
