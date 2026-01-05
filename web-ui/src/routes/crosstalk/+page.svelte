<script lang="ts">
    import { onMount } from "svelte";
    import {
        Plus,
        Trash2,
        Play,
        Save,
        Settings,
        Terminal,
        MessageSquare,
        GitMerge,
        Network,
        Activity,
        Clock,
        Cpu,
        RefreshCw,
        AlertCircle,
        CheckCircle2,
        X,
        ArrowRight,
        ArrowLeft,
        Zap,
        Users,
        Filter
    } from "lucide-svelte";

    // State management
    let activeTab = $state("studio");
    let statusMessage = $state("");
    let isError = $state(false);
    let isLoading = $state(false);

    // Session configuration
    let session = $state({
        name: "",
        models: [
            { slot_id: 1, model_id: "big", system_prompt: "", jinja_template: "basic", temperature: 0.9, max_tokens: 4096 },
            { slot_id: 2, model_id: "small", system_prompt: "", jinja_template: "basic", temperature: 0.9, max_tokens: 4096 }
        ],
        topology: { type: "ring", order: [], center: 1, spokes: [] },
        paradigm: "relay",
        rounds: 5,
        infinite: false,
        stop_conditions: { max_time_seconds: 0, max_cost_dollars: 0, max_turns: 0, stop_keywords: [] },
        summarize_every: 0,
        initial_prompt: ""
    });

    // Visual data for flow visualization
    let flowNodes = $state<any[]>([]);
    let flowEdges = $state<any[]>([]);

    // Available options
    const paradigms = ["relay", "memory", "debate", "report"];
    const topologies = ["ring", "star", "mesh", "chain", "random", "tournament"];
    const templates = ["basic", "cli-explorer", "philosopher", "dreamer", "scientist", "storyteller"];
    const modelTiers = ["big", "middle", "small"];

    // Available models (would come from API)
    const availableModels = [
        "anthropic/claude-3-opus",
        "anthropic/claude-3-sonnet",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "google/gemini-pro",
        "google/gemini-flash",
        "openrouter/any"
    ];

    // Sessions and presets
    let presets = $state<any[]>([]);
    let sessions = $state<any[]>([]);

    // Execution state
    let currentSessionId = $state("");
    let executionLog = $state<string[]>([]);
    let isRunning = $state(false);

    // Visual update for flow diagram
    function updateFlowVisualization() {
        const nodes: any[] = [];
        const edges: any[] = [];

        const startX = 100;
        const startY = 100;
        const spacingX = 200;
        const spacingY = 120;

        if (session.topology.type === "ring") {
            // Circular layout
            const radius = 120;
            const centerX = 300;
            const centerY = 150;

            session.models.forEach((model, i) => {
                const angle = (2 * Math.PI * i / session.models.length) - (Math.PI / 2);
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);

                nodes.push({
                    id: `node-${i}`,
                    type: "model",
                    data: {
                        label: `AI${i+1}: ${model.model_id}`,
                        tier: model.model_id,
                        temp: model.temperature
                    },
                    position: { x, y }
                });

                // Add edges for ring flow
                if (session.models.length > 1) {
                    const next = (i + 1) % session.models.length;
                    edges.push({
                        id: `edge-${i}-${next}`,
                        source: `node-${i}`,
                        target: `node-${next}`,
                        animated: true,
                        label: `${i}→${next}`
                    });
                }
            });
        } else if (session.topology.type === "star") {
            // Star layout - center model with spokes
            const centerX = 300;
            const centerY = 150;
            const radius = 150;

            // Center model
            const centerIndex = session.topology.center - 1;
            if (centerIndex >= 0 && centerIndex < session.models.length) {
                nodes.push({
                    id: `node-center`,
                    type: "model",
                    data: {
                        label: `CENTER: ${session.models[centerIndex].model_id}`,
                        tier: session.models[centerIndex].model_id,
                        temp: session.models[centerIndex].temperature,
                        isCenter: true
                    },
                    position: { x: centerX, y: centerY }
                });

                // Spokes
                const spokes = session.topology.spokes.length > 0
                    ? session.topology.spokes
                    : session.models.map((_, i) => i + 1).filter(i => i !== session.topology.center);

                spokes.forEach((spoke, i) => {
                    const spokeIndex = spoke - 1;
                    if (spokeIndex >= 0 && spokeIndex < session.models.length && spokeIndex !== centerIndex) {
                        const angle = (2 * Math.PI * i / spokes.length);
                        const x = centerX + radius * Math.cos(angle);
                        const y = centerY + radius * Math.sin(angle);

                        nodes.push({
                            id: `node-${spokeIndex}`,
                            type: "model",
                            data: {
                                label: `AI${spoke}: ${session.models[spokeIndex].model_id}`,
                                tier: session.models[spokeIndex].model_id,
                                temp: session.models[spokeIndex].temperature
                            },
                            position: { x, y }
                        });

                        edges.push({
                            id: `edge-center-${spokeIndex}`,
                            source: `node-center`,
                            target: `node-${spokeIndex}`,
                            animated: true,
                            bidirectional: true
                        });
                    }
                });
            }
        } else if (session.topology.type === "mesh") {
            // Mesh layout - all to all
            session.models.forEach((model, i) => {
                const x = startX + (i % 3) * spacingX;
                const y = startY + Math.floor(i / 3) * spacingY;

                nodes.push({
                    id: `node-${i}`,
                    type: "model",
                    data: {
                        label: `AI${i+1}: ${model.model_id}`,
                        tier: model.model_id,
                        temp: model.temperature
                    },
                    position: { x, y }
                });

                // All-to-all connections
                session.models.forEach((_, j) => {
                    if (i !== j) {
                        edges.push({
                            id: `edge-${i}-${j}`,
                            source: `node-${i}`,
                            target: `node-${j}`,
                            animated: true,
                            style: "opacity: 0.3"
                        });
                    }
                });
            });
        } else {
            // Linear layout as fallback
            session.models.forEach((model, i) => {
                nodes.push({
                    id: `node-${i}`,
                    type: "model",
                    data: {
                        label: `AI${i+1}: ${model.model_id}`,
                        tier: model.model_id,
                        temp: model.temperature
                    },
                    position: { x: startX + i * spacingX, y: startY }
                });

                if (i < session.models.length - 1) {
                    edges.push({
                        id: `edge-${i}-${i+1}`,
                        source: `node-${i}`,
                        target: `node-${i+1}`,
                        animated: true
                    });
                }
            });
        }

        flowNodes = nodes;
        flowEdges = edges;
    }

    // Add model to session
    function addModel() {
        if (session.models.length >= 8) {
            showStatus("Maximum 8 models allowed", true);
            return;
        }

        const newSlot = {
            slot_id: session.models.length + 1,
            model_id: availableModels[0],
            system_prompt: "",
            jinja_template: "basic",
            temperature: 0.9,
            max_tokens: 4096
        };

        session.models.push(newSlot);
        updateFlowVisualization();
        showStatus(`Added Model ${newSlot.slot_id}`);
    }

    // Remove model from session
    function removeModel(index: number) {
        if (session.models.length <= 1) {
            showStatus("Must have at least 1 model", true);
            return;
        }

        session.models.splice(index, 1);
        // Renumber slots
        session.models.forEach((m, i) => m.slot_id = i + 1);
        updateFlowVisualization();
        showStatus("Model removed");
    }

    // Copy model
    function copyModel(index: number) {
        if (session.models.length >= 8) {
            showStatus("Maximum 8 models allowed", true);
            return;
        }

        const original = session.models[index];
        const copy = {
            ...original,
            slot_id: session.models.length + 1
        };

        session.models.push(copy);
        updateFlowVisualization();
        showStatus(`Copied to Model ${copy.slot_id}`);
    }

    // Update topology
    function updateTopology() {
        if (session.topology.type === "star") {
            // Set defaults for star if not set
            if (session.topology.center < 1 || session.topology.center > session.models.length) {
                session.topology.center = 1;
            }
            if (session.topology.spokes.length === 0) {
                session.topology.spokes = session.models
                    .map((_, i) => i + 1)
                    .filter(i => i !== session.topology.center);
            }
        }
        updateFlowVisualization();
    }

    // Show status message
    function showStatus(message: string, error: boolean = false) {
        statusMessage = message;
        isError = error;
        setTimeout(() => {
            statusMessage = "";
            isError = false;
        }, 3000);
    }

    // Load presets from API
    async function loadPresets() {
        isLoading = true;
        try {
            const res = await fetch("/api/crosstalk/presets");
            if (res.ok) {
                presets = await res.json();
            }
        } catch (e) {
            console.error("Failed to load presets:", e);
        }
        isLoading = false;
    }

    // Load sessions from API
    async function loadSessions() {
        isLoading = true;
        try {
            const res = await fetch("/api/crosstalk/sessions");
            if (res.ok) {
                sessions = await res.json();
            }
        } catch (e) {
            console.error("Failed to load sessions:", e);
        }
        isLoading = false;
    }

    // Save current session as preset
    async function savePreset() {
        if (!session.name) {
            showStatus("Please enter a session name", true);
            return;
        }

        isLoading = true;
        try {
            const res = await fetch("/api/crosstalk/presets", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: session.name,
                    models: session.models,
                    topology: session.topology,
                    paradigm: session.paradigm,
                    rounds: session.rounds,
                    infinite: session.infinite,
                    stop_conditions: session.stop_conditions,
                    summarize_every: session.summarize_every,
                    initial_prompt: session.initial_prompt
                })
            });

            if (res.ok) {
                showStatus("Preset saved successfully");
                loadPresets();
            } else {
                showStatus("Failed to save preset", true);
            }
        } catch (e) {
            showStatus(`Error: ${e}`, true);
        }
        isLoading = false;
    }

    // Load preset into session
    async function loadPreset(filename: string) {
        try {
            const res = await fetch(`/api/crosstalk/presets/${filename}`);
            if (res.ok) {
                const preset = await res.json();
                session = {
                    ...preset,
                    models: preset.models.map((m: any, i: number) => ({
                        ...m,
                        slot_id: i + 1
                    }))
                };
                updateFlowVisualization();
                showStatus(`Loaded preset: ${preset.name || filename}`);
                activeTab = "studio";
            }
        } catch (e) {
            showStatus(`Failed to load preset: ${e}`, true);
        }
    }

    // Run session
    async function runSession() {
        if (!session.initial_prompt) {
            showStatus("Initial prompt is required", true);
            return;
        }

        if (session.models.length < 2) {
            showStatus("At least 2 models required", true);
            return;
        }

        isLoading = true;
        isRunning = true;
        executionLog = [];
        currentSessionId = "";

        try {
            const res = await fetch("/api/crosstalk/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    models: session.models.map(m => m.model_id),
                    topology: session.topology,
                    paradigm: session.paradigm,
                    rounds: session.rounds,
                    infinite: session.infinite,
                    stop_conditions: session.stop_conditions,
                    initial_prompt: session.initial_prompt,
                    summarize_every: session.summarize_every
                })
            });

            if (res.ok) {
                const result = await res.json();
                currentSessionId = result.session_id;
                executionLog.push(`✅ Session created: ${currentSessionId}`);
                executionLog.push(`ℹ️  ${result.message}`);

                if (result.config) {
                    executionLog.push(`📋 Models: ${result.config.models.join(", ")}`);
                    executionLog.push(`🔁 Rounds: ${result.config.rounds}`);
                    executionLog.push(`🎯 Topology: ${result.config.topology.type}`);
                    executionLog.push(`🔮 Paradigm: ${result.config.paradigm}`);
                }

                showStatus("Session created! Use TUI for full execution");
                loadSessions();
            } else {
                const error = await res.json();
                showStatus(`Failed: ${error.detail || "Unknown error"}`, true);
                executionLog.push(`❌ Error: ${error.detail || "Unknown error"}`);
            }
        } catch (e) {
            showStatus(`Network error: ${e}`, true);
            executionLog.push(`❌ Network error: ${e}`);
        }

        isLoading = false;
        setTimeout(() => { isRunning = false; }, 1000);
    }

    // Load session transcript
    async function viewSession(filename: string) {
        try {
            const res = await fetch(`/api/crosstalk/sessions/${filename}`);
            if (res.ok) {
                const sessionData = await res.json();
                // Could show transcript in modal here
                alert(`Session transcript loaded:\n${JSON.stringify(sessionData, null, 2)}`);
            }
        } catch (e) {
            showStatus(`Failed to load session: ${e}`, true);
        }
    }

    // Update flow visualization when session changes
    $effect(() => {
        if (session.models && session.topology) {
            updateFlowVisualization();
        }
    });

    // Load initial data
    onMount(() => {
        updateFlowVisualization();
        loadPresets();
        loadSessions();
    });
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100 font-sans">
    <!-- Header -->
    <header class="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <span class="text-zinc-900 font-bold text-sm">CT</span>
                </div>
                <div>
                    <h1 class="font-bold text-lg tracking-tight">Crosstalk Studio</h1>
                    <p class="text-xs text-zinc-400">Multi-Model Conversation Orchestrator</p>
                </div>
            </div>
            <div class="flex gap-2">
                <button
                    onclick={() => { activeTab = 'studio'; }}
                    class="px-3 py-1.5 text-sm rounded-md border border-zinc-700 hover:bg-zinc-800 transition-colors {activeTab === 'studio' ? 'bg-zinc-800 border-purple-500' : ''}"
                >
                    Studio
                </button>
                <button
                    onclick={() => { activeTab = 'presets'; }}
                    class="px-3 py-1.5 text-sm rounded-md border border-zinc-700 hover:bg-zinc-800 transition-colors {activeTab === 'presets' ? 'bg-zinc-800 border-purple-500' : ''}"
                >
                    Presets
                </button>
                <button
                    onclick={() => { activeTab = 'sessions'; }}
                    class="px-3 py-1.5 text-sm rounded-md border border-zinc-700 hover:bg-zinc-800 transition-colors {activeTab === 'sessions' ? 'bg-zinc-800 border-purple-500' : ''}"
                >
                    Sessions
                </button>
                <button
                    onclick={() => { activeTab = 'help'; }}
                    class="px-3 py-1.5 text-sm rounded-md border border-zinc-700 hover:bg-zinc-800 transition-colors {activeTab === 'help' ? 'bg-zinc-800 border-purple-500' : ''}"
                >
                    Help
                </button>
            </div>
        </div>
    </header>

    <!-- Status Bar -->
    {#if statusMessage}
        <div class="max-w-7xl mx-auto px-6 py-2">
            <div class="p-3 rounded-lg border text-sm flex items-center gap-2 {isError ? 'border-red-500 bg-red-900/20 text-red-300' : 'border-green-500 bg-green-900/20 text-green-300'}">
                {#if isError}
                    <AlertCircle class="w-4 h-4" />
                {:else}
                    <CheckCircle2 class="w-4 h-4" />
                {/if}
                {statusMessage}
            </div>
        </div>
    {/if}

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 py-8">

        <!-- Studio Tab -->
        {#if activeTab === 'studio'}
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

                <!-- Left Panel: Configuration -->
                <div class="space-y-6">

                    <!-- Session Details -->
                    <section class="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                        <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
                            <Settings class="w-5 h-5 text-purple-400" />
                            Session Configuration
                        </h2>

                        <div class="space-y-4">
                            <div>
                                <label class="text-xs text-zinc-400 mb-1 block">Session Name</label>
                                <input
                                    type="text"
                                    bind:value={session.name}
                                    placeholder="my_crosstalk_session"
                                    class="w-full px-3 py-2 rounded bg-zinc-950 border border-zinc-700 focus:border-purple-500 focus:outline-none text-sm font-mono"
                                />
                            </div>

                            <div class="grid grid-cols-3 gap-2">
                                <div>
                                    <label class="text-xs text-zinc-400 mb-1 block">Paradigm</label>
                                    <select
                                        bind:value={session.paradigm}
                                        class="w-full px-2 py-2 rounded bg-zinc-950 border border-zinc-700 focus:border-purple-500 focus:outline-none text-sm"
                                    >
                                        {#each paradigms as p}
                                            <option value={p}>{p}</option>
                                        {/each}
                                    </select>
                                </div>

                                <div>
                                    <label class="text-xs text-zinc-400 mb-1 block">Topology</label>
                                    <select
                                        bind:value={session.topology.type}
                                        onchange={updateTopology}
                                        class="w-full px-2 py-2 rounded bg-zinc-950 border border-zinc-700 focus:border-purple-500 focus:outline-none text-sm"
                                    >
                                        {#each topologies as t}
                                            <option value={t}>{t}</option>
                                        {/each}
                                    </select>
                                </div>

                                <div>
                                    <label class="text-xs text-zinc-400 mb-1 block">Rounds</label>
                                    <input
                                        type="number"
                                        bind:value={session.rounds}
                                        min="1"
                                        max="100"
                                        class="w-full px-2 py-2 rounded bg-zinc-950 border border-zinc-700 focus:border-purple-500 focus:outline-none text-sm"
                                    />
                                </div>
                            </div>

                            <!-- Star Topology Specific -->
                            {#if session.topology.type === 'star'}
                                <div class="p-3 bg-zinc-950/50 rounded border border-zinc-800">
                                    <label class="text-xs text-purple-400 mb-1 block">Star Topology Settings</label>
                                    <div class="flex gap-2">
                                        <div class="flex-1">
                                            <span class="text-xs text-zinc-400">Center:</span>
                                            <input
                                                type="number"
                                                bind:value={session.topology.center}
                                                min="1"
                                                max={session.models.length}
                                                class="w-full px-2 py-1 rounded bg-zinc-950 border border-zinc-700 text-xs"
                                            />
                                        </div>
                                        <div class="flex-1">
                                            <span class="text-xs text-zinc-400">Spokes (comma sep):</span>
                                            <input
                                                type="text"
                                                bind:value={session.topology.spokes.join(',')}
                                                placeholder="2,3,4"
                                                onchange={(e) => {
                                                    session.topology.spokes = e.target.value.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n));
                                                    updateTopology();
                                                }}
                                                class="w-full px-2 py-1 rounded bg-zinc-950 border border-zinc-700 text-xs"
                                            />
                                        </div>
                                    </div>
                                </div>
                            {/if}

                            <div>
                                <label class="text-xs text-zinc-400 mb-1 block">Initial Prompt</label>
                                <textarea
                                    bind:value={session.initial_prompt}
                                    placeholder="Enter the conversation starter..."
                                    rows="3"
                                    class="w-full px-3 py-2 rounded bg-zinc-950 border border-zinc-700 focus:border-purple-500 focus:outline-none text-sm font-mono"
                                ></textarea>
                            </div>

                            <!-- Infinite Mode -->
                            <div class="flex items-center gap-3">
                                <label class="flex items-center gap-2 text-sm cursor-pointer">
                                    <input
                                        type="checkbox"
                                        bind:checked={session.infinite}
                                        class="rounded bg-zinc-950 border-zinc-700 text-purple-500 focus:ring-purple-500"
                                    />
                                    Infinite Mode
                                </label>

                                {#if session.infinite}
                                    <div class="flex gap-2 text-xs">
                                        <input
                                            type="number"
                                            placeholder="Max Time (s)"
                                            bind:value={session.stop_conditions.max_time_seconds}
                                            class="w-24 px-2 py-1 rounded bg-zinc-950 border border-zinc-700"
                                        />
                                        <input
                                            type="number"
                                            placeholder="Max Cost ($)"
                                            bind:value={session.stop_conditions.max_cost_dollars}
                                            class="w-24 px-2 py-1 rounded bg-zinc-950 border border-zinc-700"
                                        />
                                    </div>
                                {/if}
                            </div>
                        </div>
                    </section>

                    <!-- Models Configuration -->
                    <section class="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-lg font-bold flex items-center gap-2">
                                <Cpu class="w-5 h-5 text-cyan-400" />
                                Models ({session.models.length}/8)
                            </h2>
                            <div class="flex gap-2">
                                <button
                                    onclick={addModel}
                                    class="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-700 rounded text-sm font-medium flex items-center gap-1"
                                >
                                    <Plus class="w-3 h-3" /> Add
                                </button>
                            </div>
                        </div>

                        <div class="space-y-3">
                            {#each session.models as model, i}
                                <div class="p-4 bg-zinc-950 rounded-lg border border-zinc-800 hover:border-cyan-500/50 transition-colors">
                                    <div class="flex items-center justify-between mb-2">
                                        <div class="flex items-center gap-2">
                                            <span class="text-cyan-400 font-bold">AI{i+1}</span>
                                            <span class="text-xs text-zinc-500">Slot {model.slot_id}</span>
                                        </div>
                                        <div class="flex gap-1">
                                            <button
                                                onclick={() => copyModel(i)}
                                                class="px-2 py-1 bg-zinc-800 hover:bg-zinc-700 rounded text-xs"
                                                title="Copy"
                                            >
                                                Copy
                                            </button>
                                            <button
                                                onclick={() => removeModel(i)}
                                                class="px-2 py-1 bg-red-900/20 hover:bg-red-900/40 text-red-400 rounded text-xs"
                                                title="Remove"
                                            >
                                                Remove
                                            </button>
                                        </div>
                                    </div>

                                    <div class="grid grid-cols-2 gap-2 mb-2">
                                        <div>
                                            <label class="text-xs text-zinc-400">Model ID</label>
                                            <select
                                                bind:value={model.model_id}
                                                class="w-full px-2 py-1 rounded bg-zinc-900 border border-zinc-700 text-xs"
                                            >
                                                {#each availableModels as m}
                                                    <option value={m}>{m.split('/').pop()}</option>
                                                {/each}
                                            </select>
                                        </div>
                                        <div>
                                            <label class="text-xs text-zinc-400">Template</label>
                                            <select
                                                bind:value={model.jinja_template}
                                                class="w-full px-2 py-1 rounded bg-zinc-900 border border-zinc-700 text-xs"
                                            >
                                                {#each templates as t}
                                                    <option value={t}>{t}</option>
                                                {/each}
                                            </select>
                                        </div>
                                    </div>

                                    <div class="grid grid-cols-2 gap-2">
                                        <div>
                                            <label class="text-xs text-zinc-400">Temperature: {model.temperature}</label>
                                            <input
                                                type="range"
                                                bind:value={model.temperature}
                                                min="0.1"
                                                max="2.0"
                                                step="0.1"
                                                class="w-full"
                                            />
                                        </div>
                                        <div>
                                            <label class="text-xs text-zinc-400">Max Tokens</label>
                                            <input
                                                type="number"
                                                bind:value={model.max_tokens}
                                                class="w-full px-2 py-1 rounded bg-zinc-900 border border-zinc-700 text-xs"
                                            />
                                        </div>
                                    </div>

                                    <div class="mt-2">
                                        <label class="text-xs text-zinc-400">System Prompt (optional)</label>
                                        <input
                                            type="text"
                                            bind:value={model.system_prompt}
                                            placeholder="file:path or inline prompt"
                                            class="w-full px-2 py-1 rounded bg-zinc-900 border border-zinc-700 text-xs font-mono"
                                        />
                                    </div>
                                </div>
                            {/each}
                        </div>
                    </section>

                    <!-- Action Buttons -->
                    <section class="grid grid-cols-2 gap-3">
                        <button
                            onclick={savePreset}
                            disabled={isLoading}
                            class="px-4 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg font-medium border border-zinc-700 flex items-center justify-center gap-2"
                        >
                            <Save class="w-4 h-4" /> Save Preset
                        </button>
                        <button
                            onclick={runSession}
                            disabled={isLoading || !session.initial_prompt || session.models.length < 2}
                            class="px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium flex items-center justify-center gap-2"
                        >
                            <Play class="w-4 h-4" /> {isLoading ? 'Running...' : 'Run Session'}
                        </button>
                    </section>
                </div>

                <!-- Right Panel: Visualizer + Logs -->
                <div class="space-y-6">

                    <!-- Visual Flow Diagram -->
                    <section class="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                        <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
                            <Network class="w-5 h-5 text-pink-400" />
                            Visual Flow ({session.topology.type})
                        </h2>

                        <div class="bg-zinc-950 rounded-lg border border-zinc-800 overflow-hidden" style="height: 320px; position: relative;">
                            <!-- Simple SVG Visualization -->
                            <svg width="100%" height="100%" viewBox="0 0 600 320">
                                <!-- Edges -->
                                {#each flowEdges as edge}
                                    <defs>
                                        <marker id="arrowhead-{edge.id}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                                            <polygon points="0 0, 10 3, 0 6" fill="#d8b4fe" />
                                        </marker>
                                    </defs>
                                    <line
                                        x1={flowNodes.find(n => n.id === edge.source)?.position.x || 0}
                                        y1={flowNodes.find(n => n.id === edge.source)?.position.y || 0}
                                        x2={flowNodes.find(n => n.id === edge.target)?.position.x || 0}
                                        y2={flowNodes.find(n => n.id === edge.target)?.position.y || 0}
                                        stroke="#d8b4fe"
                                        stroke-width="2"
                                        stroke-dasharray="4"
                                        opacity="0.6"
                                        marker-end="url(#arrowhead-{edge.id})"
                                    />
                                {/each}

                                <!-- Nodes -->
                                {#each flowNodes as node}
                                    <g>
                                        <rect
                                            x={node.position.x - 60}
                                            y={node.position.y - 20}
                                            width="120"
                                            height="40"
                                            rx="8"
                                            fill={node.data.isCenter ? "#a855f7" : "#18181b"}
                                            stroke={node.data.isCenter ? "#d8b4fe" : "#3f3f46"}
                                            stroke-width="2"
                                        />
                                        <text
                                            x={node.position.x}
                                            y={node.position.y}
                                            text-anchor="middle"
                                            dominant-baseline="middle"
                                            fill="#e4e4e7"
                                            font-size="10"
                                            font-family="monospace"
                                        >
                                            {node.data.tier?.split('/').pop() || 'Model'}
                                        </text>
                                        <text
                                            x={node.position.x}
                                            y={node.position.y + 12}
                                            text-anchor="middle"
                                            dominant-baseline="middle"
                                            fill="#a1a1aa"
                                            font-size="8"
                                        >
                                            temp: {node.data.temp}
                                        </text>
                                    </g>
                                {/each}

                                <!-- No models message -->
                                {#if flowNodes.length === 0}
                                    <text x="300" y="160" text-anchor="middle" fill="#52525b" font-size="14">
                                        Add models to see visual flow
                                    </text>
                                {/if}
                            </svg>
                        </div>

                        <div class="mt-3 text-xs text-zinc-400 flex gap-4">
                            <span>🎯 Topology: <span class="text-zinc-200">{session.topology.type}</span></span>
                            <span>🔄 Paradigm: <span class="text-zinc-200">{session.paradigm}</span></span>
                            <span>👥 Models: <span class="text-zinc-200">{session.models.length}</span></span>
                        </div>
                    </section>

                    <!-- Execution Log -->
                    <section class="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-lg font-bold flex items-center gap-2">
                                <Terminal class="w-5 h-5 text-yellow-400" />
                                Execution Log
                            </h2>
                            <button
                                onclick={() => executionLog = []}
                                class="text-xs px-2 py-1 bg-zinc-800 hover:bg-zinc-700 rounded"
                            >
                                Clear
                            </button>
                        </div>

                        <div class="bg-black/40 rounded-lg border border-zinc-800 p-3 font-mono text-xs h-48 overflow-y-auto">
                            {#if executionLog.length === 0}
                                <div class="text-zinc-500 italic">No execution logs yet. Run a session to see output.</div>
                            {:else}
                                {#each executionLog as log}
                                    <div class="mb-1 text-zinc-300">{log}</div>
                                {/each}
                            {/if}
                        </div>

                        {#if currentSessionId}
                            <div class="mt-3 text-xs text-zinc-400">
                                Current Session: <span class="text-purple-400 font-mono">{currentSessionId}</span>
                                <button
                                    onclick={() => navigator.clipboard.writeText(currentSessionId)}
                                    class="ml-2 px-2 py-1 bg-zinc-800 hover:bg-zinc-700 rounded"
                                >
                                    Copy
                                </button>
                                <span class="ml-4 text-yellow-400">→ Use CLI for full streaming: <code class="bg-zinc-800 px-1 rounded">python start_proxy.py --crosstalk-studio</code></span>
                            </div>
                        {/if}
                    </section>
                </div>
            </div>

        <!-- Presets Tab -->
        {:else if activeTab === 'presets'}
            <div class="max-w-4xl mx-auto">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-xl font-bold">Saved Presets</h2>
                    <button onclick={loadPresets} class="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded flex items-center gap-2">
                        <RefreshCw class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" /> Refresh
                    </button>
                </div>

                {#if presets.length === 0}
                    <div class="bg-zinc-900 rounded-lg p-8 text-center border border-zinc-800">
                        <div class="text-zinc-400">No presets saved yet. Save your current session from the Studio tab.</div>
                    </div>
                {:else}
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {#each presets as preset}
                            <div class="bg-zinc-900 rounded-lg p-4 border border-zinc-800 hover:border-purple-500/50 transition-colors">
                                <h3 class="font-bold text-purple-400 mb-1">{preset.name}</h3>
                                <p class="text-xs text-zinc-400 mb-3">{preset.description || "No description"}</p>
                                <div class="text-xs text-zinc-300 space-y-1 font-mono">
                                    <div>Models: {preset.models}</div>
                                    <div>Topology: {preset.topology} | Paradigm: {preset.paradigm}</div>
                                    <div>Rounds: {preset.rounds}</div>
                                </div>
                                <div class="mt-3 flex gap-2">
                                    <button
                                        onclick={() => loadPreset(preset.filename)}
                                        class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded text-sm flex-1"
                                    >
                                        Load
                                    </button>
                                    <button
                                        onclick={() => window.open('/api/crosstalk/presets/' + preset.filename, '_blank')}
                                        class="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded text-sm"
                                    >
                                        JSON
                                    </button>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>

        <!-- Sessions Tab -->
        {:else if activeTab === 'sessions'}
            <div class="max-w-4xl mx-auto">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-xl font-bold">Recent Sessions</h2>
                    <button onclick={loadSessions} class="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded flex items-center gap-2">
                        <RefreshCw class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" /> Refresh
                    </button>
                </div>

                {#if sessions.length === 0}
                    <div class="bg-zinc-900 rounded-lg p-8 text-center border border-zinc-800">
                        <div class="text-zinc-400">No sessions yet. Run a session from the Studio tab to see it here.</div>
                    </div>
                {:else}
                    <div class="space-y-3">
                        {#each sessions as sessionItem}
                            <div class="bg-zinc-900 rounded-lg p-4 border border-zinc-800 hover:border-cyan-500/50 transition-colors">
                                <div class="flex justify-between items-start mb-2">
                                    <div>
                                        <h3 class="font-bold font-mono text-cyan-400">{sessionItem.filename}</h3>
                                        <p class="text-xs text-zinc-500">
                                            {sessionItem.started_at} → {sessionItem.ended_at || 'In Progress'}
                                        </p>
                                    </div>
                                    <span class="text-xs bg-zinc-800 px-2 py-1 rounded">{sessionItem.messages} messages</span>
                                </div>
                                <div class="text-sm text-zinc-300">
                                    <span class="text-purple-400">{sessionItem.paradigm}</span> conversation
                                </div>
                                <div class="mt-2">
                                    <button
                                        onclick={() => viewSession(sessionItem.filename)}
                                        class="text-xs px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded"
                                    >
                                        View Transcript
                                    </button>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>

        <!-- Help Tab -->
        {:else if activeTab === 'help'}
            <div class="max-w-4xl mx-auto space-y-6">
                <section class="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                    <h2 class="text-xl font-bold mb-4">Crosstalk Help & Reference</h2>

                    <div class="space-y-4 text-sm text-zinc-300">
                        <div>
                            <h3 class="font-bold text-purple-400 mb-2">Paradigms</h3>
                            <ul class="space-y-1 text-zinc-400">
                                <li><span class="text-zinc-200">Relay:</span> Sequential - each model only sees the previous response</li>
                                <li><span class="text-zinc-200">Memory:</span> All models see full conversation history</li>
                                <li><span class="text-zinc-200">Debate:</span> Models critique and challenge each other</li>
                                <li><span class="text-zinc-200">Report:</span> Models summarize before passing to next</li>
                            </ul>
                        </div>

                        <div>
                            <h3 class="font-bold text-cyan-400 mb-2">Topologies</h3>
                            <ul class="space-y-1 text-zinc-400">
                                <li><span class="text-zinc-200">Ring:</span> Circular flow 1→2→3→1 (default)</li>
                                <li><span class="text-zinc-200">Star:</span> Center model to all spokes and back</li>
                                <li><span class="text-zinc-200">Mesh:</span> All models communicate with all others</li>
                                <li><span class="text-zinc-200">Chain:</span> Linear, no return</li>
                                <li><span class="text-zinc-200">Random:</span> Random routing each turn</li>
                                <li><span class="text-zinc-200">Tournament:</span> Bracket elimination</li>
                            </ul>
                        </div>

                        <div>
                            <h3 class="font-bold text-pink-400 mb-2">Templates</h3>
                            <p class="text-zinc-400">Jinja templates format incoming messages:</p>
                            <ul class="space-y-1 mt-1 text-zinc-400">
                                <li><span class="text-zinc-200">basic:</span> Pass-through</li>
                                <li><span class="text-zinc-200">cli-explorer:</span> Terminal style (backrooms)</li>
                                <li><span class="text-zinc-200">philosopher:</span> Socratic dialogue</li>
                                <li><span class="text-zinc-200">dreamer:</span> Liminal consciousness</li>
                                <li><span class="text-zinc-200">scientist:</span> Hypothesis exchange</li>
                                <li><span class="text-zinc-200">storyteller:</span> Narrative continuation</li>
                            </ul>
                        </div>

                        <div>
                            <h3 class="font-bold text-yellow-400 mb-2">Infinite Mode</h3>
                            <p class="text-zinc-400">Run conversations indefinitely with stop conditions:</p>
                            <ul class="space-y-1 mt-1 text-zinc-400">
                                <li>Max time (seconds)</li>
                                <li>Max cost (dollars)</li>
                                <li>Max turns</li>
                                <li>Stop keywords</li>
                            </ul>
                        </div>

                        <div>
                            <h3 class="font-bold text-green-400 mb-2">Execution</h3>
                            <p class="text-zinc-400">This UI creates session configs. For full streaming execution:</p>
                            <div class="bg-black/40 p-3 rounded font-mono text-xs mt-2 text-green-400 border border-zinc-800">
                                python start_proxy.py --crosstalk-studio
                            </div>
                        </div>
                    </div>
                </section>

                <section class="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                    <h3 class="text-lg font-bold mb-3">Quick Examples</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div class="bg-zinc-950 p-3 rounded border border-zinc-800">
                            <div class="font-bold text-purple-400 mb-1">Philosophical Debate</div>
                            <div class="text-xs text-zinc-400 font-mono">
                                Models: 2<br>
                                Paradigm: debate<br>
                                Topology: ring<br>
                                Topic: "What is consciousness?"
                            </div>
                        </div>
                        <div class="bg-zinc-950 p-3 rounded border border-zinc-800">
                            <div class="font-bold text-cyan-400 mb-1">Creative Relay</div>
                            <div class="text-xs text-zinc-400 font-mono">
                                Models: 3+<br>
                                Paradigm: relay<br>
                                Topology: ring<br>
                                Template: storyteller
                            </div>
                        </div>
                        <div class="bg-zinc-950 p-3 rounded border border-zinc-800">
                            <div class="font-bold text-pink-400 mb-1">Backrooms Style</div>
                            <div class="text-xs text-zinc-400 font-mono">
                                Models: 2 (same)<br>
                                Paradigm: relay<br>
                                Topology: ring<br>
                                Template: cli-explorer<br>
                                Infinite mode: ON
                            </div>
                        </div>
                        <div class="bg-zinc-950 p-3 rounded border border-zinc-800">
                            <div class="font-bold text-yellow-400 mb-1">Expert Panel</div>
                            <div class="text-xs text-zinc-400 font-mono">
                                Models: 3+<br>
                                Paradigm: memory<br>
                                Topology: star<br>
                                Center: 1 (moderator)
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        {/if}
    </main>

    <!-- Footer -->
    <footer class="border-t border-zinc-800 py-6 mt-12">
        <div class="max-w-7xl mx-auto px-6 text-center text-zinc-500 text-sm">
            Crosstalk Studio v2.0 • AI Model-to-Model Conversation Orchestrator
            <div class="mt-2 text-xs">
                Inspired by <a href="https://dreams-of-an-electric-mind.webflow.io/" class="text-zinc-400 hover:text-purple-400">Dreams of an Electric Mind</a>
            </div>
        </div>
    </footer>
</div>

<style>
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #18181b;
    }
    ::-webkit-scrollbar-thumb {
        background: #3f3f46;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #52525b;
    }

    /* Font adjustments */
    .font-mono {
        font-feature-settings: "ss01" on, "ss02" on;
    }

    /* Glow effects */
    .hover-glow:hover {
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
    }
</style>