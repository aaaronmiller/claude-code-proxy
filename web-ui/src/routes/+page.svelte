<script lang="ts">
    import {
        Activity,
        Settings,
        Zap,
        Server,
        Terminal,
        FileText,
        RefreshCw,
        MessageSquare,
        Radio,
        Shield,
        Play,
        Plus,
        Trash2,
        ChevronDown,
    } from "lucide-svelte";

    let activeTab = $state("dashboard");
    let config = $state<Record<string, any>>({
        // ═══════════════════════════════════════════════════════════════════════════════
        // MODEL SETTINGS
        // ═══════════════════════════════════════════════════════════════════════════════
        big_model: "",
        middle_model: "",
        small_model: "",
        model_cascade: false,
        big_cascade: "",
        middle_cascade: "",
        small_cascade: "",

        // ═══════════════════════════════════════════════════════════════════════════════
        // PROVIDER & AUTH
        // ═══════════════════════════════════════════════════════════════════════════════
        provider_base_url: "",
        default_provider: "openrouter",
        azure_api_version: "",
        enable_openrouter_selection: "true",

        // ═══════════════════════════════════════════════════════════════════════════════
        // HYBRID ROUTING
        // ═══════════════════════════════════════════════════════════════════════════════
        enable_big_endpoint: false,
        big_endpoint: "",
        big_api_key: "",
        enable_middle_endpoint: false,
        middle_endpoint: "",
        middle_api_key: "",
        enable_small_endpoint: false,
        small_endpoint: "",
        small_api_key: "",

        // ═══════════════════════════════════════════════════════════════════════════════
        // REASONING CONFIGURATION
        // ═══════════════════════════════════════════════════════════════════════════════
        reasoning_effort: "",
        reasoning_max_tokens: "",
        reasoning_exclude: "false",
        verbosity: "",
        big_model_reasoning: "",
        middle_model_reasoning: "",
        small_model_reasoning: "",

        // ═══════════════════════════════════════════════════════════════════════════════
        // CUSTOM SYSTEM PROMPTS
        // ═══════════════════════════════════════════════════════════════════════════════
        enable_custom_big_prompt: "false",
        big_system_prompt: "",
        big_system_prompt_file: "",
        enable_custom_middle_prompt: "false",
        middle_system_prompt: "",
        middle_system_prompt_file: "",
        enable_custom_small_prompt: "false",
        small_system_prompt: "",
        small_system_prompt_file: "",

        // ═══════════════════════════════════════════════════════════════════════════════
        // TERMINAL DISPLAY
        // ═══════════════════════════════════════════════════════════════════════════════
        terminal_display_mode: "detailed",
        terminal_color_scheme: "auto",
        terminal_show_workspace: "true",
        terminal_show_context_pct: "true",
        terminal_show_task_type: "true",
        terminal_show_speed: "true",
        terminal_show_cost: "true",
        terminal_show_duration_colors: "true",
        terminal_session_colors: "true",

        // ═══════════════════════════════════════════════════════════════════════════════
        // LOGGING SETTINGS
        // ═══════════════════════════════════════════════════════════════════════════════
        log_style: "rich",
        compact_logger: "false",
        show_token_counts: "true",
        show_performance: "true",
        color_scheme: "auto",

        // ═══════════════════════════════════════════════════════════════════════════════
        // USAGE & ANALYTICS
        // ═══════════════════════════════════════════════════════════════════════════════
        track_usage: "false",
        usage_db_path: "usage_tracking.db",

        // ═══════════════════════════════════════════════════════════════════════════════
        // DASHBOARD SETTINGS
        // ═══════════════════════════════════════════════════════════════════════════════
        enable_dashboard: "false",
        dashboard_layout: "default",
        dashboard_refresh: "0.5",
        dashboard_waterfall_size: "20",

        // ═══════════════════════════════════════════════════════════════════════════════
        // PERFORMANCE SETTINGS
        // ═══════════════════════════════════════════════════════════════════════════════
        max_tokens_limit: "65536",
        min_tokens_limit: "4096",
        request_timeout: "120",
        max_retries: "2",

        // ═══════════════════════════════════════════════════════════════════════════════
        // SERVER CONFIGURATION (read-only)
        // ═══════════════════════════════════════════════════════════════════════════════
        host: "0.0.0.0",
        port: "8082",
        log_level: "INFO",
    });
    let status = $state({ connected: false, provider: "", requests: 0 });
    let loading = $state(false);
    let error = $state("");
    let saveMessage = $state("");
    let showWizard = $state(false);
    let presets = $state<any[]>([]);
    let sessions = $state<any[]>([]);
    let stats = $state({
        requests_today: 0,
        total_tokens: 0,
        est_cost: 0,
        avg_latency: 0,
    });

    // WebSocket logs state
    let ws: WebSocket | null = $state(null);
    let wsConnected = $state(false);
    let logs = $state<any[]>([]);
    let logFilter = $state("all");

    // Playground state
    let playground = $state({
        tier: "big",
        systemPrompt: "",
        userMessage: "",
        temperature: 0.7,
        maxTokens: 1024,
        response: "",
        loading: false,
        error: "",
        tokens: { input: 0, output: 0 },
        latency: 0,
    });

    // Crosstalk session state - FULL FEATURE PARITY
    let crosstalkSession = $state({
        models: [
            {
                slot_id: 1,
                model_id: "",
                system_prompt: "",
                jinja_template: "basic", // NEW
                temperature: 0.7,
                max_tokens: 2048,
                append: "", // NEW: Added to messages this model receives
                prepend: "", // NEW: Added before messages this model sends
                endpoint: "", // NEW: Custom API endpoint
                api_key_env: "", // NEW: Environment variable for API key
            },
            {
                slot_id: 2,
                model_id: "",
                system_prompt: "",
                jinja_template: "basic",
                temperature: 0.7,
                max_tokens: 2048,
                append: "",
                prepend: "",
                endpoint: "",
                api_key_env: "",
            },
        ],
        topology: {
            type: "ring",
            order: [],
            center: 1,
            spokes: [],
            pattern: [],
        },
        paradigm: "relay",
        rounds: 5,
        infinite: false,
        stop_conditions: {
            max_time_seconds: 0,
            max_cost_dollars: 0,
            stop_keywords: [],
            repetition_threshold: 0.85, // NEW
        },
        initial_prompt: "",
        // NEW: Advanced session options
        summarize_every: 0, // 0 = disabled, N = summarize every N rounds
        checkpoint_every: 10, // Checkpoint every N rounds for infinite mode
        final_round_vote: {
            enabled: false,
            question: "What is your final verdict?",
            options: ["yes", "no", "undecided"],
            tally_method: "majority",
        },
    });

    // Available Jinja templates
    const jinjaTemplates = [
        "basic",
        "debate",
        "analyst",
        "creative",
        "concise",
    ];

    const tabs = [
        { id: "dashboard", label: "Dashboard", icon: Activity },
        { id: "models", label: "Models", icon: Zap },
        { id: "cascade", label: "Cascade", icon: RefreshCw },
        { id: "routing", label: "Routing", icon: Server },
        { id: "crosstalk", label: "Crosstalk", icon: MessageSquare },
        { id: "terminal", label: "Terminal", icon: Terminal },
        { id: "playground", label: "Playground", icon: Play },
        { id: "logs", label: "Logs", icon: FileText },
    ];

    const topologies = [
        "ring",
        "star",
        "mesh",
        "chain",
        "random",
        "custom",
        "tournament",
    ];
    const paradigms = ["relay", "memory", "report", "debate"];

    async function loadConfig() {
        loading = true;
        try {
            const res = await fetch("/api/config");
            if (res.ok) {
                const data = await res.json();
                config = { ...config, ...data };
                status.connected = true;
                status.provider = data.default_provider || "unknown";

                // Check if provider is configured - show wizard if not
                const healthRes = await fetch("/api/health");
                if (healthRes.ok) {
                    const health = await healthRes.json();
                    if (!health.provider_configured) {
                        showWizard = true;
                    }
                }
            }
        } catch (e) {
            status.connected = false;
            // Show wizard on connection error (server might be fresh install)
            showWizard = true;
        }
        loading = false;
    }

    async function loadPresets() {
        try {
            const res = await fetch("/api/crosstalk/presets");
            if (res.ok) presets = await res.json();
        } catch (e) {
            console.error(e);
        }
    }

    async function loadSessions() {
        try {
            const res = await fetch("/api/crosstalk/sessions");
            if (res.ok) sessions = await res.json();
        } catch (e) {
            console.error(e);
        }
    }

    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            if (res.ok) stats = await res.json();
        } catch (e) {
            console.error(e);
        }
    }

    async function saveConfig() {
        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config),
            });
            if (res.ok) {
                saveMessage = "✅ Configuration saved";
                setTimeout(() => (saveMessage = ""), 3000);
            } else {
                saveMessage = "❌ Failed to save";
                setTimeout(() => (saveMessage = ""), 3000);
            }
        } catch (e) {
            saveMessage = "❌ Connection error";
            setTimeout(() => (saveMessage = ""), 3000);
        }
    }

    async function loadPreset(filename: string) {
        try {
            const res = await fetch(`/api/crosstalk/presets/${filename}`);
            if (res.ok) {
                const data = await res.json();
                crosstalkSession = { ...crosstalkSession, ...data };
            }
        } catch (e) {
            console.error(e);
        }
    }

    function connectWebSocket() {
        if (ws) {
            ws.close();
        }
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/api/ws/logs`;
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            wsConnected = true;
            logs = [
                ...logs,
                {
                    level: "info",
                    message: "Connected to log stream",
                    timestamp: new Date().toISOString(),
                },
            ];
        };

        ws.onmessage = (event) => {
            try {
                const log = JSON.parse(event.data);
                logs = [...logs.slice(-199), log]; // Keep last 200 logs
            } catch (e) {
                console.error("Failed to parse log:", e);
            }
        };

        ws.onclose = () => {
            wsConnected = false;
            logs = [
                ...logs,
                {
                    level: "warning",
                    message: "Disconnected from log stream",
                    timestamp: new Date().toISOString(),
                },
            ];
            // Auto-reconnect after 3 seconds
            setTimeout(() => {
                if (activeTab === "logs") connectWebSocket();
            }, 3000);
        };

        ws.onerror = () => {
            wsConnected = false;
        };
    }

    function clearLogs() {
        logs = [];
    }

    function addModelSlot() {
        const nextId =
            Math.max(...crosstalkSession.models.map((m) => m.slot_id)) + 1;
        crosstalkSession.models = [
            ...crosstalkSession.models,
            {
                slot_id: nextId,
                model_id: "",
                system_prompt: "",
                jinja_template: "basic",
                temperature: 0.7,
                max_tokens: 2048,
                append: "",
                prepend: "",
                endpoint: "",
                api_key_env: "",
            },
        ];
    }

    function removeModelSlot(slotId: number) {
        if (crosstalkSession.models.length > 2) {
            crosstalkSession.models = crosstalkSession.models.filter(
                (m) => m.slot_id !== slotId,
            );
        }
    }

    $effect(() => {
        loadConfig();
        loadPresets();
        loadSessions();
        loadStats();
    });
</script>

<div class="flex flex-col h-screen">
    <!-- Header -->
    <header class="border-b border-cyber-border bg-cyber-surface px-6 py-4">
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
                <h1 class="font-mono text-2xl font-bold text-glow">
                    <span class="text-cyber-cyan">CCP</span>
                    <span class="text-cyber-muted">//</span>
                    <span class="text-cyber-text">PROXY</span>
                </h1>
                <div
                    class="flex items-center gap-2 px-3 py-1 rounded-full bg-cyber-bg border border-cyber-border"
                >
                    <div
                        class={`w-2 h-2 rounded-full ${status.connected ? "bg-cyber-green status-online" : "bg-cyber-red"}`}
                    ></div>
                    <span class="text-xs font-mono text-cyber-muted">
                        {status.connected
                            ? status.provider.toUpperCase()
                            : "OFFLINE"}
                    </span>
                </div>
            </div>

            <div class="flex items-center gap-4">
                <button
                    onclick={() => {
                        loadConfig();
                        loadStats();
                    }}
                    class="p-2 rounded-lg hover:bg-cyber-elevated transition-colors"
                    title="Refresh"
                >
                    <RefreshCw
                        class={`w-5 h-5 text-cyber-muted ${loading ? "animate-spin" : ""}`}
                    />
                </button>
                <button
                    class="p-2 rounded-lg hover:bg-cyber-elevated transition-colors"
                    title="Settings"
                >
                    <Settings class="w-5 h-5 text-cyber-muted" />
                </button>
            </div>
        </div>

        <!-- Tabs -->
        <nav class="flex gap-1 mt-4 -mb-4 overflow-x-auto">
            {#each tabs as tab}
                <button
                    onclick={() => (activeTab = tab.id)}
                    class={`cyber-tab flex items-center gap-2 font-mono text-sm whitespace-nowrap ${activeTab === tab.id ? "active" : ""}`}
                >
                    <tab.icon class="w-4 h-4" />
                    {tab.label.toUpperCase()}
                </button>
            {/each}
        </nav>
    </header>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto p-6">
        {#if activeTab === "dashboard"}
            <!-- Dashboard -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="cyber-card p-4">
                    <p class="text-cyber-muted text-xs font-mono">
                        REQUESTS TODAY
                    </p>
                    <p class="text-2xl font-mono text-cyber-cyan">
                        {stats.requests_today}
                    </p>
                </div>
                <div class="cyber-card p-4">
                    <p class="text-cyber-muted text-xs font-mono">
                        TOTAL TOKENS
                    </p>
                    <p class="text-2xl font-mono text-cyber-magenta">
                        {stats.total_tokens.toLocaleString()}
                    </p>
                </div>
                <div class="cyber-card p-4">
                    <p class="text-cyber-muted text-xs font-mono">EST. COST</p>
                    <p class="text-2xl font-mono text-cyber-green">
                        ${stats.est_cost.toFixed(4)}
                    </p>
                </div>
                <div class="cyber-card p-4">
                    <p class="text-cyber-muted text-xs font-mono">
                        AVG LATENCY
                    </p>
                    <p class="text-2xl font-mono text-cyber-amber">
                        {stats.avg_latency}ms
                    </p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="cyber-card p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 rounded-lg bg-cyber-cyan/10">
                            <Zap class="w-5 h-5 text-cyber-cyan" />
                        </div>
                        <span class="text-cyber-muted font-mono text-sm"
                            >BIG MODEL</span
                        >
                    </div>
                    <p class="font-mono text-lg text-cyber-text truncate">
                        {config.big_model || "Not set"}
                    </p>
                </div>
                <div class="cyber-card p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 rounded-lg bg-cyber-magenta/10">
                            <Zap class="w-5 h-5 text-cyber-magenta" />
                        </div>
                        <span class="text-cyber-muted font-mono text-sm"
                            >MIDDLE MODEL</span
                        >
                    </div>
                    <p class="font-mono text-lg text-cyber-text truncate">
                        {config.middle_model || "Not set"}
                    </p>
                </div>
                <div class="cyber-card p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 rounded-lg bg-cyber-green/10">
                            <Zap class="w-5 h-5 text-cyber-green" />
                        </div>
                        <span class="text-cyber-muted font-mono text-sm"
                            >SMALL MODEL</span
                        >
                    </div>
                    <p class="font-mono text-lg text-cyber-text truncate">
                        {config.small_model || "Not set"}
                    </p>
                </div>
            </div>
        {:else if activeTab === "models"}
            <div class="max-w-3xl space-y-6">
                <h2 class="font-mono text-xl text-cyber-cyan mb-6">
                    // MODEL CONFIGURATION
                </h2>

                <!-- Model Selection -->
                <div class="cyber-card p-4 space-y-4">
                    <h3 class="font-mono text-cyber-text mb-4">
                        Model Selection
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label
                                for="big_model"
                                class="block text-xs font-mono text-cyber-muted mb-1"
                                >BIG_MODEL (Opus)</label
                            >
                            <input
                                id="big_model"
                                type="text"
                                bind:value={config.big_model}
                                class="cyber-input w-full text-sm"
                                placeholder="anthropic/claude-3-opus"
                            />
                        </div>
                        <div>
                            <label
                                for="middle_model"
                                class="block text-xs font-mono text-cyber-muted mb-1"
                                >MIDDLE_MODEL (Sonnet)</label
                            >
                            <input
                                id="middle_model"
                                type="text"
                                bind:value={config.middle_model}
                                class="cyber-input w-full text-sm"
                                placeholder="anthropic/claude-3-sonnet"
                            />
                        </div>
                        <div>
                            <label
                                for="small_model"
                                class="block text-xs font-mono text-cyber-muted mb-1"
                                >SMALL_MODEL (Haiku)</label
                            >
                            <input
                                id="small_model"
                                type="text"
                                bind:value={config.small_model}
                                class="cyber-input w-full text-sm"
                                placeholder="anthropic/claude-3-haiku"
                            />
                        </div>
                    </div>
                </div>

                <!-- Reasoning Configuration -->
                <details class="cyber-card p-4">
                    <summary
                        class="font-mono text-cyber-text cursor-pointer select-none flex items-center gap-2"
                    >
                        <ChevronDown class="w-4 h-4 transition-transform" />
                        Reasoning Configuration
                    </summary>
                    <div class="mt-4 space-y-4">
                        <p class="text-xs text-cyber-dim">
                            Configure thinking/reasoning for o-series and Claude
                            models
                        </p>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Global Effort</label
                                >
                                <select
                                    bind:value={config.reasoning_effort}
                                    class="cyber-input w-full text-sm"
                                >
                                    <option value="">Disabled</option>
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Max Tokens</label
                                >
                                <input
                                    type="number"
                                    bind:value={config.reasoning_max_tokens}
                                    class="cyber-input w-full text-sm"
                                    placeholder="128000"
                                />
                            </div>
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Verbosity</label
                                >
                                <select
                                    bind:value={config.verbosity}
                                    class="cyber-input w-full text-sm"
                                >
                                    <option value="">Default</option>
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div class="flex items-center gap-2 pt-5">
                                <input
                                    type="checkbox"
                                    id="reasoning_exclude"
                                    checked={config.reasoning_exclude ===
                                        "true"}
                                    onchange={(e) =>
                                        (config.reasoning_exclude = e.target
                                            .checked
                                            ? "true"
                                            : "false")}
                                    class="accent-cyber-cyan"
                                />
                                <label
                                    for="reasoning_exclude"
                                    class="text-xs text-cyber-muted"
                                    >Exclude from response</label
                                >
                            </div>
                        </div>
                        <div
                            class="grid grid-cols-3 gap-4 pt-2 border-t border-cyber-border/20"
                        >
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >BIG Override</label
                                >
                                <select
                                    bind:value={config.big_model_reasoning}
                                    class="cyber-input w-full text-sm"
                                >
                                    <option value="">Use Global</option>
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >MIDDLE Override</label
                                >
                                <select
                                    bind:value={config.middle_model_reasoning}
                                    class="cyber-input w-full text-sm"
                                >
                                    <option value="">Use Global</option>
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >SMALL Override</label
                                >
                                <select
                                    bind:value={config.small_model_reasoning}
                                    class="cyber-input w-full text-sm"
                                >
                                    <option value="">Use Global</option>
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </details>

                <!-- Custom System Prompts -->
                <details class="cyber-card p-4">
                    <summary
                        class="font-mono text-cyber-text cursor-pointer select-none flex items-center gap-2"
                    >
                        <ChevronDown class="w-4 h-4 transition-transform" />
                        Custom System Prompts
                    </summary>
                    <div class="mt-4 space-y-4">
                        <p class="text-xs text-cyber-dim">
                            Override system prompts per model tier. File path
                            takes precedence if both set.
                        </p>

                        <!-- BIG Prompt -->
                        <div
                            class="p-3 bg-cyber-bg rounded border border-cyber-border/20"
                        >
                            <div class="flex items-center gap-3 mb-2">
                                <input
                                    type="checkbox"
                                    checked={config.enable_custom_big_prompt ===
                                        "true"}
                                    onchange={(e) =>
                                        (config.enable_custom_big_prompt = e
                                            .target.checked
                                            ? "true"
                                            : "false")}
                                    class="accent-cyber-cyan"
                                />
                                <span class="text-sm font-mono text-cyber-cyan"
                                    >BIG Tier</span
                                >
                            </div>
                            {#if config.enable_custom_big_prompt === "true"}
                                <div class="space-y-2 pl-6">
                                    <input
                                        type="text"
                                        bind:value={
                                            config.big_system_prompt_file
                                        }
                                        class="cyber-input w-full text-sm"
                                        placeholder="File path (optional)"
                                    />
                                    <textarea
                                        bind:value={config.big_system_prompt}
                                        class="cyber-input w-full text-sm h-16"
                                        placeholder="Inline prompt..."
                                    ></textarea>
                                </div>
                            {/if}
                        </div>

                        <!-- MIDDLE Prompt -->
                        <div
                            class="p-3 bg-cyber-bg rounded border border-cyber-border/20"
                        >
                            <div class="flex items-center gap-3 mb-2">
                                <input
                                    type="checkbox"
                                    checked={config.enable_custom_middle_prompt ===
                                        "true"}
                                    onchange={(e) =>
                                        (config.enable_custom_middle_prompt = e
                                            .target.checked
                                            ? "true"
                                            : "false")}
                                    class="accent-cyber-cyan"
                                />
                                <span class="text-sm font-mono text-cyber-cyan"
                                    >MIDDLE Tier</span
                                >
                            </div>
                            {#if config.enable_custom_middle_prompt === "true"}
                                <div class="space-y-2 pl-6">
                                    <input
                                        type="text"
                                        bind:value={
                                            config.middle_system_prompt_file
                                        }
                                        class="cyber-input w-full text-sm"
                                        placeholder="File path (optional)"
                                    />
                                    <textarea
                                        bind:value={config.middle_system_prompt}
                                        class="cyber-input w-full text-sm h-16"
                                        placeholder="Inline prompt..."
                                    ></textarea>
                                </div>
                            {/if}
                        </div>

                        <!-- SMALL Prompt -->
                        <div
                            class="p-3 bg-cyber-bg rounded border border-cyber-border/20"
                        >
                            <div class="flex items-center gap-3 mb-2">
                                <input
                                    type="checkbox"
                                    checked={config.enable_custom_small_prompt ===
                                        "true"}
                                    onchange={(e) =>
                                        (config.enable_custom_small_prompt = e
                                            .target.checked
                                            ? "true"
                                            : "false")}
                                    class="accent-cyber-cyan"
                                />
                                <span class="text-sm font-mono text-cyber-cyan"
                                    >SMALL Tier</span
                                >
                            </div>
                            {#if config.enable_custom_small_prompt === "true"}
                                <div class="space-y-2 pl-6">
                                    <input
                                        type="text"
                                        bind:value={
                                            config.small_system_prompt_file
                                        }
                                        class="cyber-input w-full text-sm"
                                        placeholder="File path (optional)"
                                    />
                                    <textarea
                                        bind:value={config.small_system_prompt}
                                        class="cyber-input w-full text-sm h-16"
                                        placeholder="Inline prompt..."
                                    ></textarea>
                                </div>
                            {/if}
                        </div>
                    </div>
                </details>

                <button onclick={saveConfig} class="cyber-btn mt-6"
                    >SAVE CONFIGURATION</button
                >
            </div>
        {:else if activeTab === "cascade"}
            <div class="max-w-2xl space-y-6">
                <h2 class="font-mono text-xl text-cyber-cyan mb-6">
                    // CASCADE FALLBACK
                </h2>
                <div class="cyber-card p-4 flex items-center justify-between">
                    <div>
                        <p class="font-mono text-cyber-text">
                            Enable Model Cascade
                        </p>
                        <p class="text-sm text-cyber-muted">
                            Auto-switch to fallback models on errors
                        </p>
                    </div>
                    <button
                        onclick={() =>
                            (config.model_cascade = !config.model_cascade)}
                        class={`w-12 h-6 rounded-full transition-colors ${config.model_cascade ? "bg-cyber-cyan" : "bg-cyber-border"}`}
                        aria-label="Toggle cascade"
                    >
                        <div
                            class={`w-5 h-5 rounded-full bg-white transform transition-transform ${config.model_cascade ? "translate-x-6" : "translate-x-0.5"}`}
                        ></div>
                    </button>
                </div>
                {#if config.model_cascade}
                    <div class="space-y-4 mt-6">
                        <div>
                            <label
                                for="big_cascade"
                                class="block text-sm font-mono text-cyber-muted mb-2"
                                >BIG_CASCADE</label
                            >
                            <input
                                id="big_cascade"
                                type="text"
                                bind:value={config.big_cascade}
                                class="cyber-input w-full"
                                placeholder="openai/gpt-4o,google/gemini-pro"
                            />
                        </div>
                        <div>
                            <label
                                for="middle_cascade"
                                class="block text-sm font-mono text-cyber-muted mb-2"
                                >MIDDLE_CASCADE</label
                            >
                            <input
                                id="middle_cascade"
                                type="text"
                                bind:value={config.middle_cascade}
                                class="cyber-input w-full"
                                placeholder="openai/gpt-4o-mini"
                            />
                        </div>
                        <div>
                            <label
                                for="small_cascade"
                                class="block text-sm font-mono text-cyber-muted mb-2"
                                >SMALL_CASCADE</label
                            >
                            <input
                                id="small_cascade"
                                type="text"
                                bind:value={config.small_cascade}
                                class="cyber-input w-full"
                                placeholder="google/gemini-flash"
                            />
                        </div>
                    </div>
                    <div
                        class="cyber-card p-4 mt-6 border-l-4 border-cyber-amber"
                    >
                        <p class="font-mono text-sm text-cyber-amber">
                            ⚡ CASCADE BEHAVIOR
                        </p>
                        <ul class="text-sm text-cyber-muted mt-2 space-y-1">
                            <li>• SSL/Cert errors → Switch immediately</li>
                            <li>• 400/401 errors → Switch immediately</li>
                            <li>
                                • Connection/Timeout/Rate limit → 5 retries
                                before switch
                            </li>
                        </ul>
                    </div>
                {/if}
                <button onclick={saveConfig} class="cyber-btn mt-6"
                    >SAVE CASCADE CONFIG</button
                >
            </div>
        {:else if activeTab === "routing"}
            <div class="max-w-2xl space-y-6">
                <h2 class="font-mono text-xl text-cyber-cyan mb-6">
                    // HYBRID ROUTING
                </h2>
                <p class="text-cyber-muted mb-4">
                    Route different model tiers to different API endpoints.
                </p>

                {#each [{ tier: "BIG", enable: "enable_big_endpoint", endpoint: "big_endpoint", apiKey: "big_api_key" }, { tier: "MIDDLE", enable: "enable_middle_endpoint", endpoint: "middle_endpoint", apiKey: "middle_api_key" }, { tier: "SMALL", enable: "enable_small_endpoint", endpoint: "small_endpoint", apiKey: "small_api_key" }] as route}
                    <div class="cyber-card p-4">
                        <div class="flex items-center justify-between mb-4">
                            <span class="font-mono text-cyber-text"
                                >{route.tier} Endpoint</span
                            >
                            <button
                                onclick={() =>
                                    (config[route.enable] =
                                        !config[route.enable])}
                                class={`w-12 h-6 rounded-full transition-colors ${config[route.enable] ? "bg-cyber-cyan" : "bg-cyber-border"}`}
                                aria-label="Toggle endpoint"
                            >
                                <div
                                    class={`w-5 h-5 rounded-full bg-white transform transition-transform ${config[route.enable] ? "translate-x-6" : "translate-x-0.5"}`}
                                ></div>
                            </button>
                        </div>
                        {#if config[route.enable]}
                            <div class="space-y-3">
                                <div>
                                    <label
                                        class="block text-xs text-cyber-muted mb-1"
                                        >Endpoint URL</label
                                    >
                                    <input
                                        type="text"
                                        bind:value={config[route.endpoint]}
                                        class="cyber-input w-full"
                                        placeholder="https://api.openai.com/v1"
                                    />
                                </div>
                                <div>
                                    <label
                                        class="block text-xs text-cyber-muted mb-1"
                                        >API Key</label
                                    >
                                    <input
                                        type="password"
                                        bind:value={config[route.apiKey]}
                                        class="cyber-input w-full"
                                        placeholder="sk-..."
                                    />
                                </div>
                            </div>
                        {/if}
                    </div>
                {/each}
                <button onclick={saveConfig} class="cyber-btn mt-6"
                    >SAVE ROUTING</button
                >
            </div>
        {:else if activeTab === "crosstalk"}
            <div class="space-y-6">
                <div class="flex items-center justify-between">
                    <h2 class="font-mono text-xl text-cyber-cyan">
                        // CROSSTALK ORCHESTRATION
                    </h2>
                    <div class="flex gap-2">
                        <select
                            onchange={(e) =>
                                loadPreset(
                                    (e.target as HTMLSelectElement).value,
                                )}
                            class="cyber-input text-sm"
                        >
                            <option value="">Load Preset...</option>
                            {#each presets as preset}
                                <option value={preset.filename}
                                    >{preset.name}</option
                                >
                            {/each}
                        </select>
                    </div>
                </div>

                <!-- Model Slots -->
                <div class="cyber-card p-4">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="font-mono text-cyber-text">Model Slots</h3>
                        <button
                            onclick={addModelSlot}
                            class="flex items-center gap-1 text-cyber-cyan text-sm"
                        >
                            <Plus class="w-4 h-4" /> Add Slot
                        </button>
                    </div>
                    <div class="space-y-4">
                        {#each crosstalkSession.models as model, i}
                            <div
                                class="p-4 bg-cyber-bg rounded-lg border border-cyber-border/30"
                            >
                                <div
                                    class="flex items-center justify-between mb-3"
                                >
                                    <span
                                        class="text-cyber-cyan font-mono text-sm"
                                        >Slot #{model.slot_id}</span
                                    >
                                    {#if crosstalkSession.models.length > 2}
                                        <button
                                            onclick={() =>
                                                removeModelSlot(model.slot_id)}
                                            class="text-cyber-red p-1 hover:bg-cyber-red/10 rounded"
                                        >
                                            <Trash2 class="w-4 h-4" />
                                        </button>
                                    {/if}
                                </div>

                                <!-- Model ID & Template -->
                                <div class="grid grid-cols-2 gap-3 mb-3">
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >Model ID</label
                                        >
                                        <input
                                            type="text"
                                            bind:value={model.model_id}
                                            class="cyber-input w-full text-sm"
                                            placeholder="openai/gpt-4o-mini"
                                        />
                                    </div>
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >Jinja Template</label
                                        >
                                        <select
                                            bind:value={model.jinja_template}
                                            class="cyber-input w-full text-sm"
                                        >
                                            {#each jinjaTemplates as tpl}
                                                <option value={tpl}
                                                    >{tpl}</option
                                                >
                                            {/each}
                                        </select>
                                    </div>
                                </div>

                                <!-- System Prompt -->
                                <div class="mb-3">
                                    <label
                                        class="text-xs text-cyber-muted block mb-1"
                                        >System Prompt</label
                                    >
                                    <textarea
                                        bind:value={model.system_prompt}
                                        class="cyber-input w-full text-sm h-16"
                                        placeholder="You are a helpful assistant..."
                                    ></textarea>
                                </div>

                                <!-- Temp & Max Tokens -->
                                <div class="grid grid-cols-4 gap-3 mb-3">
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >Temp</label
                                        >
                                        <input
                                            type="number"
                                            step="0.1"
                                            min="0"
                                            max="2"
                                            bind:value={model.temperature}
                                            class="cyber-input w-full text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >Max Tokens</label
                                        >
                                        <input
                                            type="number"
                                            bind:value={model.max_tokens}
                                            class="cyber-input w-full text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >Endpoint</label
                                        >
                                        <input
                                            type="text"
                                            bind:value={model.endpoint}
                                            class="cyber-input w-full text-sm"
                                            placeholder="Custom API URL"
                                        />
                                    </div>
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >API Key Env</label
                                        >
                                        <input
                                            type="text"
                                            bind:value={model.api_key_env}
                                            class="cyber-input w-full text-sm"
                                            placeholder="OPENAI_API_KEY"
                                        />
                                    </div>
                                </div>

                                <!-- Context Modifiers -->
                                <div class="grid grid-cols-2 gap-3">
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >Prepend (to outgoing)</label
                                        >
                                        <input
                                            type="text"
                                            bind:value={model.prepend}
                                            class="cyber-input w-full text-sm"
                                            placeholder="Added before responses..."
                                        />
                                    </div>
                                    <div>
                                        <label
                                            class="text-xs text-cyber-muted block mb-1"
                                            >Append (to incoming)</label
                                        >
                                        <input
                                            type="text"
                                            bind:value={model.append}
                                            class="cyber-input w-full text-sm"
                                            placeholder="Added to messages received..."
                                        />
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>

                <!-- Session Settings -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="cyber-card p-4">
                        <h3 class="font-mono text-cyber-text mb-4">Topology</h3>
                        <select
                            bind:value={crosstalkSession.topology.type}
                            class="cyber-input w-full"
                        >
                            {#each topologies as t}<option value={t}
                                    >{t.toUpperCase()}</option
                                >{/each}
                        </select>
                    </div>
                    <div class="cyber-card p-4">
                        <h3 class="font-mono text-cyber-text mb-4">Paradigm</h3>
                        <select
                            bind:value={crosstalkSession.paradigm}
                            class="cyber-input w-full"
                        >
                            {#each paradigms as p}<option value={p}
                                    >{p.toUpperCase()}</option
                                >{/each}
                        </select>
                    </div>
                    <div class="cyber-card p-4">
                        <h3 class="font-mono text-cyber-text mb-4">Rounds</h3>
                        <div class="flex items-center gap-4">
                            <input
                                type="number"
                                bind:value={crosstalkSession.rounds}
                                class="cyber-input w-20"
                                disabled={crosstalkSession.infinite}
                            />
                            <label
                                class="flex items-center gap-2 text-sm text-cyber-muted"
                            >
                                <input
                                    type="checkbox"
                                    bind:checked={crosstalkSession.infinite}
                                    class="accent-cyber-cyan"
                                />
                                Infinite
                            </label>
                        </div>
                    </div>
                    <div class="cyber-card p-4">
                        <h3 class="font-mono text-cyber-text mb-4">
                            Stop Conditions
                        </h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex items-center gap-2">
                                <label class="text-cyber-muted w-24"
                                    >Max Time:</label
                                >
                                <input
                                    type="number"
                                    bind:value={
                                        crosstalkSession.stop_conditions
                                            .max_time_seconds
                                    }
                                    class="cyber-input w-20"
                                />
                                <span class="text-cyber-muted">sec</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <label class="text-cyber-muted w-24"
                                    >Max Cost:</label
                                >
                                <input
                                    type="number"
                                    step="0.01"
                                    bind:value={
                                        crosstalkSession.stop_conditions
                                            .max_cost_dollars
                                    }
                                    class="cyber-input w-20"
                                />
                                <span class="text-cyber-muted">$</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <label class="text-cyber-muted w-24"
                                    >Repetition:</label
                                >
                                <input
                                    type="number"
                                    step="0.05"
                                    min="0"
                                    max="1"
                                    bind:value={
                                        crosstalkSession.stop_conditions
                                            .repetition_threshold
                                    }
                                    class="cyber-input w-20"
                                />
                                <span class="text-cyber-muted text-xs"
                                    >similarity threshold</span
                                >
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Advanced Options -->
                <div class="cyber-card p-4 mt-4">
                    <h3 class="font-mono text-cyber-text mb-4">
                        Advanced Options
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <label class="text-xs text-cyber-muted block mb-1"
                                >Summarize Every</label
                            >
                            <div class="flex items-center gap-2">
                                <input
                                    type="number"
                                    min="0"
                                    bind:value={
                                        crosstalkSession.summarize_every
                                    }
                                    class="cyber-input w-16 text-sm"
                                />
                                <span class="text-cyber-muted text-xs"
                                    >rounds</span
                                >
                            </div>
                            <p class="text-cyber-dim text-xs mt-1">
                                0 = disabled
                            </p>
                        </div>
                        <div>
                            <label class="text-xs text-cyber-muted block mb-1"
                                >Checkpoint Every</label
                            >
                            <div class="flex items-center gap-2">
                                <input
                                    type="number"
                                    min="0"
                                    bind:value={
                                        crosstalkSession.checkpoint_every
                                    }
                                    class="cyber-input w-16 text-sm"
                                />
                                <span class="text-cyber-muted text-xs"
                                    >rounds</span
                                >
                            </div>
                            <p class="text-cyber-dim text-xs mt-1">
                                For infinite mode
                            </p>
                        </div>
                        <div class="col-span-2">
                            <label
                                class="flex items-center gap-2 text-sm text-cyber-muted"
                            >
                                <input
                                    type="checkbox"
                                    bind:checked={
                                        crosstalkSession.final_round_vote
                                            .enabled
                                    }
                                    class="accent-cyber-cyan"
                                />
                                Enable Final Round Voting
                            </label>
                            {#if crosstalkSession.final_round_vote.enabled}
                                <input
                                    type="text"
                                    bind:value={
                                        crosstalkSession.final_round_vote
                                            .question
                                    }
                                    class="cyber-input w-full text-sm mt-2"
                                    placeholder="Vote question..."
                                />
                            {/if}
                        </div>
                    </div>
                </div>

                <!-- Initial Prompt -->
                <div class="cyber-card p-4">
                    <h3 class="font-mono text-cyber-text mb-4">
                        Initial Prompt
                    </h3>
                    <textarea
                        bind:value={crosstalkSession.initial_prompt}
                        class="cyber-input w-full h-32"
                        placeholder="Enter the starting prompt for the conversation..."
                    ></textarea>
                </div>

                <div class="flex gap-4">
                    <button class="cyber-btn flex items-center gap-2">
                        <Play class="w-4 h-4" /> RUN SESSION
                    </button>
                    <button
                        class="px-4 py-2 border border-cyber-border rounded-lg text-cyber-muted hover:text-cyber-text transition-colors"
                    >
                        SAVE AS PRESET
                    </button>
                </div>

                <!-- Recent Sessions -->
                {#if sessions.length > 0}
                    <div class="cyber-card p-4 mt-6">
                        <h3 class="font-mono text-cyber-text mb-4">
                            Recent Sessions
                        </h3>
                        <div class="space-y-2">
                            {#each sessions.slice(0, 5) as session}
                                <div
                                    class="flex items-center justify-between p-2 bg-cyber-bg rounded"
                                >
                                    <span
                                        class="font-mono text-sm text-cyber-muted"
                                        >{session.filename}</span
                                    >
                                    <span class="text-xs text-cyber-dim"
                                        >{session.messages} messages</span
                                    >
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
        {:else if activeTab === "terminal"}
            <div class="max-w-3xl space-y-6">
                <h2 class="font-mono text-xl text-cyber-cyan mb-6">
                    // TERMINAL OUTPUT
                </h2>

                <!-- Display Settings -->
                <div class="cyber-card p-4 space-y-4">
                    <h3 class="font-mono text-cyber-text mb-4">
                        Display Settings
                    </h3>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs text-cyber-muted mb-1"
                                >Display Mode</label
                            >
                            <select
                                bind:value={config.terminal_display_mode}
                                class="cyber-input w-full text-sm"
                            >
                                <option value="minimal">Minimal</option>
                                <option value="normal">Normal</option>
                                <option value="detailed">Detailed</option>
                                <option value="debug">Debug</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs text-cyber-muted mb-1"
                                >Color Scheme</label
                            >
                            <select
                                bind:value={config.terminal_color_scheme}
                                class="cyber-input w-full text-sm"
                            >
                                <option value="auto">Auto</option>
                                <option value="vibrant">Vibrant</option>
                                <option value="subtle">Subtle</option>
                                <option value="mono">Mono</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Metrics Toggles -->
                <details class="cyber-card p-4" open>
                    <summary
                        class="font-mono text-cyber-text cursor-pointer select-none flex items-center gap-2"
                    >
                        <ChevronDown class="w-4 h-4" /> Metrics Display
                    </summary>
                    <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                        <label
                            class="flex items-center gap-2 text-sm text-cyber-muted"
                        >
                            <input
                                type="checkbox"
                                checked={config.terminal_show_workspace ===
                                    "true"}
                                onchange={(e) =>
                                    (config.terminal_show_workspace = e.target
                                        .checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            Workspace
                        </label>
                        <label
                            class="flex items-center gap-2 text-sm text-cyber-muted"
                        >
                            <input
                                type="checkbox"
                                checked={config.terminal_show_context_pct ===
                                    "true"}
                                onchange={(e) =>
                                    (config.terminal_show_context_pct = e.target
                                        .checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            Context %
                        </label>
                        <label
                            class="flex items-center gap-2 text-sm text-cyber-muted"
                        >
                            <input
                                type="checkbox"
                                checked={config.terminal_show_task_type ===
                                    "true"}
                                onchange={(e) =>
                                    (config.terminal_show_task_type = e.target
                                        .checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            Task Type 🧠
                        </label>
                        <label
                            class="flex items-center gap-2 text-sm text-cyber-muted"
                        >
                            <input
                                type="checkbox"
                                checked={config.terminal_show_speed === "true"}
                                onchange={(e) =>
                                    (config.terminal_show_speed = e.target
                                        .checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            Speed (tok/s)
                        </label>
                        <label
                            class="flex items-center gap-2 text-sm text-cyber-muted"
                        >
                            <input
                                type="checkbox"
                                checked={config.terminal_show_cost === "true"}
                                onchange={(e) =>
                                    (config.terminal_show_cost = e.target
                                        .checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            Cost
                        </label>
                        <label
                            class="flex items-center gap-2 text-sm text-cyber-muted"
                        >
                            <input
                                type="checkbox"
                                checked={config.terminal_show_duration_colors ===
                                    "true"}
                                onchange={(e) =>
                                    (config.terminal_show_duration_colors = e
                                        .target.checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            Duration Colors
                        </label>
                        <label
                            class="flex items-center gap-2 text-sm text-cyber-muted"
                        >
                            <input
                                type="checkbox"
                                checked={config.terminal_session_colors ===
                                    "true"}
                                onchange={(e) =>
                                    (config.terminal_session_colors = e.target
                                        .checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            Session Colors
                        </label>
                    </div>
                </details>

                <!-- Logging Settings -->
                <details class="cyber-card p-4">
                    <summary
                        class="font-mono text-cyber-text cursor-pointer select-none flex items-center gap-2"
                    >
                        <ChevronDown class="w-4 h-4" /> Logging
                    </summary>
                    <div class="mt-4 space-y-4">
                        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Log Style</label
                                >
                                <select
                                    bind:value={config.log_style}
                                    class="cyber-input w-full text-sm"
                                >
                                    <option value="rich">Rich (colored)</option>
                                    <option value="plain">Plain</option>
                                    <option value="compact">Compact</option>
                                </select>
                            </div>
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Color Scheme</label
                                >
                                <select
                                    bind:value={config.color_scheme}
                                    class="cyber-input w-full text-sm"
                                >
                                    <option value="auto">Auto</option>
                                    <option value="dark">Dark</option>
                                    <option value="light">Light</option>
                                    <option value="none">None</option>
                                </select>
                            </div>
                            <label
                                class="flex items-center gap-2 text-sm text-cyber-muted pt-5"
                            >
                                <input
                                    type="checkbox"
                                    checked={config.compact_logger === "true"}
                                    onchange={(e) =>
                                        (config.compact_logger = e.target
                                            .checked
                                            ? "true"
                                            : "false")}
                                    class="accent-cyber-cyan"
                                />
                                Compact Logger
                            </label>
                        </div>
                        <div class="flex gap-6">
                            <label
                                class="flex items-center gap-2 text-sm text-cyber-muted"
                            >
                                <input
                                    type="checkbox"
                                    checked={config.show_token_counts ===
                                        "true"}
                                    onchange={(e) =>
                                        (config.show_token_counts = e.target
                                            .checked
                                            ? "true"
                                            : "false")}
                                    class="accent-cyber-cyan"
                                />
                                Show Token Counts
                            </label>
                            <label
                                class="flex items-center gap-2 text-sm text-cyber-muted"
                            >
                                <input
                                    type="checkbox"
                                    checked={config.show_performance === "true"}
                                    onchange={(e) =>
                                        (config.show_performance = e.target
                                            .checked
                                            ? "true"
                                            : "false")}
                                    class="accent-cyber-cyan"
                                />
                                Show Performance
                            </label>
                        </div>
                    </div>
                </details>

                <!-- Dashboard Settings -->
                <details class="cyber-card p-4">
                    <summary
                        class="font-mono text-cyber-text cursor-pointer select-none flex items-center gap-2"
                    >
                        <ChevronDown class="w-4 h-4" /> Terminal Dashboard
                    </summary>
                    <div class="mt-4 space-y-4">
                        <label class="flex items-center gap-3">
                            <input
                                type="checkbox"
                                checked={config.enable_dashboard === "true"}
                                onchange={(e) =>
                                    (config.enable_dashboard = e.target.checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            <span class="text-sm text-cyber-muted"
                                >Enable Live Dashboard</span
                            >
                        </label>
                        {#if config.enable_dashboard === "true"}
                            <div class="grid grid-cols-3 gap-4 pl-6">
                                <div>
                                    <label
                                        class="block text-xs text-cyber-muted mb-1"
                                        >Layout</label
                                    >
                                    <select
                                        bind:value={config.dashboard_layout}
                                        class="cyber-input w-full text-sm"
                                    >
                                        <option value="default">Default</option>
                                        <option value="compact">Compact</option>
                                        <option value="detailed"
                                            >Detailed</option
                                        >
                                    </select>
                                </div>
                                <div>
                                    <label
                                        class="block text-xs text-cyber-muted mb-1"
                                        >Refresh Rate</label
                                    >
                                    <input
                                        type="number"
                                        step="0.1"
                                        bind:value={config.dashboard_refresh}
                                        class="cyber-input w-full text-sm"
                                    />
                                </div>
                                <div>
                                    <label
                                        class="block text-xs text-cyber-muted mb-1"
                                        >Waterfall Size</label
                                    >
                                    <input
                                        type="number"
                                        bind:value={
                                            config.dashboard_waterfall_size
                                        }
                                        class="cyber-input w-full text-sm"
                                    />
                                </div>
                            </div>
                        {/if}
                    </div>
                </details>

                <!-- Analytics -->
                <details class="cyber-card p-4">
                    <summary
                        class="font-mono text-cyber-text cursor-pointer select-none flex items-center gap-2"
                    >
                        <ChevronDown class="w-4 h-4" /> Usage Analytics
                    </summary>
                    <div class="mt-4 space-y-4">
                        <label class="flex items-center gap-3">
                            <input
                                type="checkbox"
                                checked={config.track_usage === "true"}
                                onchange={(e) =>
                                    (config.track_usage = e.target.checked
                                        ? "true"
                                        : "false")}
                                class="accent-cyber-cyan"
                            />
                            <span class="text-sm text-cyber-muted"
                                >Track API Usage (SQLite)</span
                            >
                        </label>
                        {#if config.track_usage === "true"}
                            <div class="pl-6">
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Database Path</label
                                >
                                <input
                                    type="text"
                                    bind:value={config.usage_db_path}
                                    class="cyber-input w-full text-sm"
                                />
                            </div>
                        {/if}
                    </div>
                </details>

                <!-- Performance -->
                <details class="cyber-card p-4">
                    <summary
                        class="font-mono text-cyber-text cursor-pointer select-none flex items-center gap-2"
                    >
                        <ChevronDown class="w-4 h-4" /> Performance
                    </summary>
                    <div class="mt-4 grid grid-cols-4 gap-4">
                        <div>
                            <label class="block text-xs text-cyber-muted mb-1"
                                >Max Tokens</label
                            >
                            <input
                                type="number"
                                bind:value={config.max_tokens_limit}
                                class="cyber-input w-full text-sm"
                            />
                        </div>
                        <div>
                            <label class="block text-xs text-cyber-muted mb-1"
                                >Min Tokens</label
                            >
                            <input
                                type="number"
                                bind:value={config.min_tokens_limit}
                                class="cyber-input w-full text-sm"
                            />
                        </div>
                        <div>
                            <label class="block text-xs text-cyber-muted mb-1"
                                >Timeout (sec)</label
                            >
                            <input
                                type="number"
                                bind:value={config.request_timeout}
                                class="cyber-input w-full text-sm"
                            />
                        </div>
                        <div>
                            <label class="block text-xs text-cyber-muted mb-1"
                                >Max Retries</label
                            >
                            <input
                                type="number"
                                bind:value={config.max_retries}
                                class="cyber-input w-full text-sm"
                            />
                        </div>
                    </div>
                </details>

                <!-- Server Info (read-only) -->
                <div class="cyber-card p-4">
                    <h3 class="font-mono text-cyber-text mb-4">
                        Server Info <span class="text-xs text-cyber-dim"
                            >(restart required)</span
                        >
                    </h3>
                    <div class="grid grid-cols-3 gap-4 text-sm">
                        <div>
                            <span class="text-cyber-muted">Host:</span>
                            <span class="text-cyber-text ml-2 font-mono"
                                >{config.host}</span
                            >
                        </div>
                        <div>
                            <span class="text-cyber-muted">Port:</span>
                            <span class="text-cyber-text ml-2 font-mono"
                                >{config.port}</span
                            >
                        </div>
                        <div>
                            <span class="text-cyber-muted">Log Level:</span>
                            <span class="text-cyber-text ml-2 font-mono"
                                >{config.log_level}</span
                            >
                        </div>
                    </div>
                </div>

                <button onclick={saveConfig} class="cyber-btn mt-6"
                    >SAVE SETTINGS</button
                >
            </div>
        {:else if activeTab === "playground"}
            <div class="max-w-4xl space-y-6">
                <h2 class="font-mono text-xl text-cyber-cyan mb-6">
                    // MODEL PLAYGROUND
                </h2>
                <p class="text-cyber-muted">
                    Test prompts against configured models.
                </p>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="space-y-4">
                        <div>
                            <label
                                class="block text-sm font-mono text-cyber-muted mb-2"
                                >Model</label
                            >
                            <select
                                bind:value={playground.tier}
                                class="cyber-input w-full"
                            >
                                <option value="big"
                                    >BIG: {config.big_model ||
                                        "Not configured"}</option
                                >
                                <option value="middle"
                                    >MIDDLE: {config.middle_model ||
                                        "Not configured"}</option
                                >
                                <option value="small"
                                    >SMALL: {config.small_model ||
                                        "Not configured"}</option
                                >
                            </select>
                        </div>

                        <div>
                            <label
                                class="block text-sm font-mono text-cyber-muted mb-2"
                                >System Prompt</label
                            >
                            <textarea
                                bind:value={playground.systemPrompt}
                                class="cyber-input w-full h-20"
                                placeholder="You are a helpful assistant..."
                            ></textarea>
                        </div>

                        <div>
                            <label
                                class="block text-sm font-mono text-cyber-muted mb-2"
                                >User Message</label
                            >
                            <textarea
                                bind:value={playground.userMessage}
                                class="cyber-input w-full h-32"
                                placeholder="Enter your prompt here..."
                            ></textarea>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Temperature: {playground.temperature}</label
                                >
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    bind:value={playground.temperature}
                                    class="w-full accent-cyber-cyan"
                                />
                            </div>
                            <div>
                                <label
                                    class="block text-xs text-cyber-muted mb-1"
                                    >Max Tokens</label
                                >
                                <input
                                    type="number"
                                    bind:value={playground.maxTokens}
                                    class="cyber-input w-full"
                                />
                            </div>
                        </div>

                        <button
                            onclick={async () => {
                                playground.loading = true;
                                playground.error = "";
                                try {
                                    const res = await fetch(
                                        "/api/playground/run",
                                        {
                                            method: "POST",
                                            headers: {
                                                "Content-Type":
                                                    "application/json",
                                            },
                                            body: JSON.stringify({
                                                model_tier: playground.tier,
                                                system_prompt:
                                                    playground.systemPrompt,
                                                user_message:
                                                    playground.userMessage,
                                                temperature:
                                                    playground.temperature,
                                                max_tokens:
                                                    playground.maxTokens,
                                            }),
                                        },
                                    );
                                    const data = await res.json();
                                    if (data.success) {
                                        playground.response = data.content;
                                        playground.tokens = {
                                            input: data.input_tokens,
                                            output: data.output_tokens,
                                        };
                                        playground.latency = data.latency_ms;
                                    } else {
                                        playground.error =
                                            data.error || "Request failed";
                                    }
                                } catch (e) {
                                    playground.error = "Connection error";
                                }
                                playground.loading = false;
                            }}
                            disabled={playground.loading ||
                                !playground.userMessage}
                            class="cyber-btn w-full flex items-center justify-center gap-2"
                        >
                            {#if playground.loading}
                                <span class="animate-spin">⟳</span> Running...
                            {:else}
                                <Play class="w-4 h-4" /> RUN PROMPT
                            {/if}
                        </button>
                    </div>

                    <div>
                        <label
                            class="block text-sm font-mono text-cyber-muted mb-2"
                            >Response</label
                        >
                        <div
                            class="cyber-card h-96 p-4 font-mono text-sm overflow-auto bg-cyber-bg"
                        >
                            {#if playground.error}
                                <p class="text-cyber-red">
                                    {playground.error}
                                </p>
                            {:else if playground.response}
                                <p class="text-cyber-text whitespace-pre-wrap">
                                    {playground.response}
                                </p>
                            {:else}
                                <p class="text-cyber-dim">
                                    Response will appear here...
                                </p>
                            {/if}
                        </div>
                        <div
                            class="flex justify-between mt-2 text-xs text-cyber-dim"
                        >
                            <span
                                >Tokens: {playground.tokens.input +
                                    playground.tokens.output || "--"}</span
                            >
                            <span
                                >Latency: {playground.latency
                                    ? `${playground.latency}ms`
                                    : "--"}</span
                            >
                        </div>
                    </div>
                </div>
            </div>
        {:else if activeTab === "logs"}
            <div class="h-full space-y-4">
                <div class="flex items-center justify-between">
                    <h2 class="font-mono text-xl text-cyber-cyan">
                        // LIVE LOGS
                    </h2>
                    <div class="flex items-center gap-4">
                        <div class="flex items-center gap-2">
                            <div
                                class={`w-2 h-2 rounded-full ${wsConnected ? "bg-cyber-green status-online" : "bg-cyber-red"}`}
                            ></div>
                            <span class="text-xs text-cyber-muted"
                                >{wsConnected
                                    ? "Connected"
                                    : "Disconnected"}</span
                            >
                        </div>
                        <select
                            bind:value={logFilter}
                            class="cyber-input text-sm py-1"
                        >
                            <option value="all">All Levels</option>
                            <option value="info">Info</option>
                            <option value="warning">Warning</option>
                            <option value="error">Error</option>
                        </select>
                        <button
                            onclick={() => {
                                if (!wsConnected) connectWebSocket();
                            }}
                            class="text-cyber-cyan text-sm hover:underline"
                            disabled={wsConnected}
                        >
                            {wsConnected ? "Connected" : "Connect"}
                        </button>
                        <button
                            onclick={clearLogs}
                            class="text-cyber-muted text-sm hover:text-cyber-red"
                            >Clear</button
                        >
                    </div>
                </div>

                <div
                    class="cyber-card h-[calc(100vh-280px)] p-4 font-mono text-xs overflow-auto flex flex-col-reverse"
                >
                    {#if logs.length === 0}
                        <p class="text-cyber-dim">
                            No logs yet. Click Connect to start streaming.
                        </p>
                    {:else}
                        <div class="space-y-1">
                            {#each logs.filter((l) => logFilter === "all" || l.level === logFilter) as log}
                                <div
                                    class="flex gap-2 {log.level === 'error'
                                        ? 'text-cyber-red'
                                        : log.level === 'warning'
                                          ? 'text-cyber-amber'
                                          : 'text-cyber-muted'}"
                                >
                                    <span class="text-cyber-dim shrink-0"
                                        >{log.timestamp?.slice(11, 19) ||
                                            "--:--:--"}</span
                                    >
                                    <span class="w-14 shrink-0 uppercase"
                                        >[{log.level || "INFO"}]</span
                                    >
                                    <span class="text-cyber-text"
                                        >{log.message}</span
                                    >
                                    {#if log.model}<span class="text-cyber-cyan"
                                            >({log.model})</span
                                        >{/if}
                                    {#if log.duration_ms}<span
                                            class="text-cyber-magenta"
                                            >{log.duration_ms}ms</span
                                        >{/if}
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        {/if}
    </main>

    <!-- Footer -->
    <footer class="border-t border-cyber-border bg-cyber-surface px-6 py-3">
        <div
            class="flex items-center justify-between text-xs font-mono text-cyber-dim"
        >
            <span>Claude Code Proxy</span>
            <span>localhost:8082</span>
        </div>
    </footer>
</div>

<!-- Setup Wizard Modal -->
{#if showWizard}
    <div
        class="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
    >
        <div class="cyber-card p-6 max-w-md w-full mx-4 gradient-border">
            <h2 class="font-mono text-xl text-cyber-cyan mb-2">
                // SETUP WIZARD
            </h2>
            <p class="text-cyber-muted text-sm mb-6">
                Configure your API provider to get started.
            </p>

            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-mono text-cyber-muted mb-2"
                        >Provider</label
                    >
                    <select
                        bind:value={config.default_provider}
                        class="cyber-input w-full"
                    >
                        <option value="openrouter">OpenRouter</option>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="google">Google AI</option>
                        <option value="custom">Custom</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-mono text-cyber-muted mb-2"
                        >API Key</label
                    >
                    <input
                        type="password"
                        class="cyber-input w-full"
                        placeholder="sk-..."
                    />
                </div>

                {#if config.default_provider === "custom"}
                    <div>
                        <label
                            class="block text-sm font-mono text-cyber-muted mb-2"
                            >Base URL</label
                        >
                        <input
                            type="text"
                            bind:value={config.provider_base_url}
                            class="cyber-input w-full"
                            placeholder="https://api.example.com/v1"
                        />
                    </div>
                {/if}

                <div
                    class="cyber-card p-3 bg-cyber-bg border-l-4 border-cyber-cyan"
                >
                    <p class="text-xs text-cyber-muted">
                        <strong class="text-cyber-cyan">Quick Start:</strong>
                        Set API key in
                        <code class="bg-cyber-elevated px-1 rounded">.env</code>
                        file and restart proxy.
                    </p>
                </div>
            </div>

            <div class="flex gap-3 mt-6">
                <button
                    onclick={() => {
                        saveConfig();
                        showWizard = false;
                    }}
                    class="cyber-btn flex-1"
                >
                    SAVE & CONTINUE
                </button>
                <button
                    onclick={() => (showWizard = false)}
                    class="px-4 py-2 border border-cyber-border rounded-lg text-cyber-muted"
                >
                    SKIP
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- Save Message Toast -->
{#if saveMessage}
    <div
        class="fixed bottom-6 right-6 bg-cyber-surface border border-cyber-border rounded-lg px-4 py-3 font-mono text-sm z-50"
    >
        {saveMessage}
    </div>
{/if}
