<script lang="ts">
    import { onMount, onDestroy } from "svelte";
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
        Palette,
        Book,
        X,
        TrendingUp,
        DollarSign,
        BarChart3,
        CheckCircle2,
        AlertCircle,
        Info,
        User,
        Key,
        Link2,
        Layers,
        Cpu,
        // New icons
        Bell,
        Clock,
        AlertTriangle,
        TrendingDown,
        Activity as ActivityIcon,
        Heart,
        Wifi,
        Power,
        Globe,
        Database,
        ShieldCheck,
        ArrowRight,
        Flame,
        Target,
        Award
    } from "lucide-svelte";
    import ThemeSelector from "$lib/components/ThemeSelector.svelte";
    import HeroBackground from "$lib/components/HeroBackground.svelte";
    import BrainCircuit from "$lib/components/icons/BrainCircuit.svelte";
    import ModelIcon from "$lib/components/icons/ModelIcon.svelte";
    import AnalyticsIcon from "$lib/components/icons/AnalyticsIcon.svelte";
    import MultiModelIcon from "$lib/components/icons/MultiModelIcon.svelte";
    import CacheIcon from "$lib/components/icons/CacheIcon.svelte";
    import RoutingIcon from "$lib/components/icons/RoutingIcon.svelte";
    import ShieldIcon from "$lib/components/icons/ShieldIcon.svelte";
    import ZapIcon from "$lib/components/icons/ZapIcon.svelte";
    import ModelSelector from "$lib/components/ModelSelector.svelte";
    import NanoBanana from "$lib/components/icons/NanoBanana.svelte";
    import Particles from "$lib/components/icons/Particles.svelte";

    // State management
    let activeTab = $state("dashboard");  // Changed to dashboard as default

    // Provider selection state
    let selectedProvider = $state("");
    let api_key = $state("");
    let applyingConfig = $state(false);
    let configMessage = $state("");

    // Model selection state
    let availableModels = $state<any[]>([]);
    let groupedModels = $state<any[]>([]);
    let modelsLoading = $state(false);

    // Configuration state
    let config = $state<Record<string, any>>({
        big_model: "",
        middle_model: "",
        small_model: "",
        openai_base_url: "https://api.openai.com/v1",
        default_provider: "openrouter"
    });

    // Stats and analytics state
    let stats = $state({
        requests_today: 0,
        total_tokens: 0,
        est_cost: 0,
        avg_latency: 0
    });

    let analyticsData = $state<any>(null);
    let analyticsLoading = $state(false);

    // NEW: Live metrics for dashboard
    let liveMetrics = $state({
        requests_per_second: 0,
        tokens_per_second: 0,
        cost_per_second: 0,
        active_requests: 0,
        error_rate: 0,
        model_distribution: {},
        timestamp: ""
    });

    // NEW: System health
    let systemHealth = $state({
        uptime: "0m",
        cpu_usage: 0,
        memory_usage: 0,
        db_size: 0,
        websocket_connected: false
    });

    // NEW: Alerts
    let activeAlerts = $state<any[]>([]);
    let recentAlerts = $state<any[]>([]);
    let hasCriticalAlerts = $state(false);

    // NEW: WebSocket connection
    let ws: WebSocket | null = null;
    let wsStatus = $state("disconnected");
    let wsReconnecting = $state(false);

    // NEW: Crosstalk stats
    let crosstalkStats = $state({
        active_sessions: 0,
        total_sessions: 0,
        avg_cost_per_session: 0,
        avg_rounds: 0,
        top_paradigm: "none"
    });

    // NEW: Budget tracking
    let budgetData = $state({
        daily_limit: 100,
        monthly_limit: 3000,
        current_daily: 0,
        current_monthly: 0,
        usage_percentage: 0
    });

    // NEW: Status tracking for the main dashboard
    let dashboardLoading = $state(false);
    let lastUpdate = $state("Never");
    let updateInterval: number | null = null;

    // NEW: Initialize WebSocket connection
    function initWebSocket() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/live`;

        try {
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                wsStatus = "connected";
                systemHealth.websocket_connected = true;
                wsReconnecting = false;
                console.log("✅ WebSocket connected");
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);

                    if (message.type === "metrics") {
                        liveMetrics = message.data;
                        lastUpdate = new Date().toLocaleTimeString();
                    } else if (message.type === "alert") {
                        handleAlert(message);
                    } else if (message.type === "request_event") {
                        // Could update request feed if we add one
                    }
                } catch (e) {
                    console.error("WebSocket message parse error:", e);
                }
            };

            ws.onclose = () => {
                wsStatus = "disconnected";
                systemHealth.websocket_connected = false;
                console.log("🔌 WebSocket disconnected");

                // Attempt reconnection
                if (!wsReconnecting) {
                    wsReconnecting = true;
                    setTimeout(() => {
                        if (activeTab === "dashboard") {
                            initWebSocket();
                        }
                    }, 3000);
                }
            };

            ws.onerror = (error) => {
                console.error("WebSocket error:", error);
                wsStatus = "error";
            };

        } catch (e) {
            console.error("WebSocket init failed:", e);
            wsStatus = "error";
        }
    }

    // NEW: Handle incoming alerts
    function handleAlert(alert: any) {
        activeAlerts = [...activeAlerts, alert];

        // Keep only last 10
        if (activeAlerts.length > 10) {
            activeAlerts = activeAlerts.slice(-10);
        }

        // Track critical alerts
        if (alert.severity === "critical") {
            hasCriticalAlerts = true;
        }

        // Add to recent alerts history
        recentAlerts = [{
            ...alert,
            time: new Date().toLocaleTimeString()
        }, ...recentAlerts].slice(0, 20);

        // Show browser notification if supported
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification("Claude Proxy Alert", {
                body: alert.message,
                icon: "/favicon.ico"
            });
        }
    }

    // NEW: Request notification permission
    function requestNotificationPermission() {
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission();
        }
    }

    // NEW: Load dashboard data (combined stats)
    async function loadDashboardData() {
        dashboardLoading = true;

        // Load traditional stats
        await Promise.all([
            loadStats(),
            loadSystemHealth(),
            loadCrosstalkStats(),
            loadBudgetData()
        ]);

        dashboardLoading = false;
    }

    // NEW: Load system health
    async function loadSystemHealth() {
        try {
            // Calculate pseudo-health (since we don't have the backend endpoint yet)
            // This will be replaced with actual /api/system/health call
            const uptime = calculateUptime();
            systemHealth = {
                uptime: uptime,
                cpu_usage: Math.floor(Math.random() * 30) + 20,  // Mock data
                memory_usage: Math.floor(Math.random() * 20) + 40,
                db_size: Math.floor(Math.random() * 500) + 100,
                websocket_connected: wsStatus === "connected"
            };
        } catch (e) {
            console.error("Health check failed:", e);
        }
    }

    // NEW: Calculate uptime from start time
    function calculateUptime(): string {
        const startTime = new Date("2026-01-04T00:00:00").getTime(); // Mock start
        const uptimeMs = Date.now() - startTime;
        const hours = Math.floor(uptimeMs / (1000 * 60 * 60));
        const minutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60));
        return `${hours}h ${minutes}m`;
    }

    // NEW: Load Crosstalk statistics
    async function loadCrosstalkStats() {
        try {
            const res = await fetch("/api/crosstalk/sessions");
            if (res.ok) {
                const sessions = await res.json();

                crosstalkStats = {
                    active_sessions: 0, // Would come from real-time tracking
                    total_sessions: sessions.length,
                    avg_cost_per_session: sessions.length > 0
                        ? sessions.reduce((sum, s) => sum + (s.total_cost || 0), 0) / sessions.length
                        : 0,
                    avg_rounds: sessions.length > 0
                        ? Math.floor(sessions.reduce((sum, s) => sum + (s.rounds || 0), 0) / sessions.length)
                        : 0,
                    top_paradigm: sessions.length > 0
                        ? sessions[0].paradigm || "relay"
                        : "none"
                };
            }
        } catch (e) {
            console.error("Crosstalk stats failed:", e);
        }
    }

    // NEW: Load budget data
    async function loadBudgetData() {
        try {
            // For now, use mock data since budget endpoint doesn't exist yet
            const currentDaily = stats.est_cost;  // Use actual cost from stats
            const currentMonthly = currentDaily * 30;  // Approximation

            budgetData = {
                daily_limit: 100,
                monthly_limit: 3000,
                current_daily: currentDaily,
                current_monthly: currentMonthly,
                usage_percentage: Math.min(100, (currentDaily / 100) * 100)
            };
        } catch (e) {
            console.error("Budget data failed:", e);
        }
    }

    // ORIGINAL: Select provider with auto-routing
    async function selectProvider(provider: string) {
        selectedProvider = provider;
        configMessage = `Selected ${provider} - configuring automatically...`;

        try {
            const res = await fetch(`/api/routing/auto?provider=${provider}`);
            if (res.ok) {
                const data = await res.json();
                if (data.routing) {
                    const applyRes = await fetch(`/api/routing/apply?provider=${provider}`, {
                        method: "POST"
                    });

                    if (applyRes.ok) {
                        const applyData = await applyRes.json();
                        configMessage = `✅ Configured for ${provider}!`;

                        config.openai_base_url = data.routing.base_url;
                        config.big_model = data.routing.recommended_big;
                        config.middle_model = data.routing.recommended_middle;
                        config.small_model = data.routing.recommended_small;
                        config.default_provider = provider;

                        loadModelsGrouped();
                        activeTab = "models";
                    } else {
                        configMessage = "❌ Failed to apply configuration";
                    }
                }
            } else {
                configMessage = "❌ Unknown provider or configuration error";
            }
        } catch (e) {
            configMessage = `❌ Error: ${e}`;
        }
    }

    // NEW: Navigate to Crosstalk Studio
    function openCrosstalk() {
        window.location.href = '/crosstalk';
    }

    // ORIGINAL: Load models
    async function loadModelsGrouped() {
        modelsLoading = true;
        try {
            const res = await fetch("/api/models?group_by_provider=true&limit=100");
            if (res.ok) {
                const data = await res.json();
                if (data.grouped) {
                    groupedModels = data.grouped;
                    availableModels = data.flat;
                } else {
                    availableModels = data.models || [];
                    groupedModels = [];
                }
            }
        } catch (e) {
            console.error("Failed to load models:", e);
        }
        modelsLoading = false;
    }

    // ORIGINAL: Select model
    async function selectModel(tier: "big" | "middle" | "small", modelId: string) {
        if (tier === "big") config.big_model = modelId;
        else if (tier === "middle") config.middle_model = modelId;
        else if (tier === "small") config.small_model = modelId;

        configMessage = `✅ ${tier.toUpperCase()} tier set to ${modelId.split('/').pop() || modelId}`;

        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    [`${tier}_model`]: modelId
                })
            });

            if (!res.ok) {
                configMessage = "⚠️ Model selected but may need server restart";
            }
        } catch (e) {
            configMessage = "⚠️ Local model selection - restart server to apply";
        }
    }

    // ORIGINAL: Load stats
    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            if (res.ok) {
                stats = await res.json();
            }
        } catch (e) {
            console.log("Stats not available:", e);
        }
    }

    // ORIGINAL: Save API key
    async function saveApiKey() {
        if (!selectedProvider || !api_key) return;

        applyingConfig = true;
        try {
            const res = await fetch(`/api/config/api-key?provider=${selectedProvider}&api_key=${encodeURIComponent(api_key)}`, {
                method: "POST"
            });

            if (res.ok) {
                const data = await res.json();
                configMessage = `✅ ${data.message}`;
                api_key = "";
            } else {
                const error = await res.json();
                configMessage = `❌ ${error.detail || "Failed to save API key"}`;
            }
        } catch (e) {
            configMessage = `❌ Error: ${e}`;
        }
        applyingConfig = false;
    }

    // Helper: Format currency
    function formatCurrency(amount: number): string {
        return `$${amount.toFixed(4)}`;
    }

    // Helper: Format tokens
    function formatTokens(tokens: number): string {
        if (tokens > 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
        if (tokens > 1000) return `${(tokens / 1000).toFixed(1)}K`;
        return tokens.toString();
    }

    // Helper: Get provider display name
    function getProviderDisplayName(provider: string): string {
        const names: Record<string, string> = {
            "openrouter": "OpenRouter",
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "google": "Google",
            "vibeproxy": "VibeProxy"
        };
        return names[provider] || provider;
    }

    // Helper: Get provider icon
    function getProviderIcon(provider: string): any {
        const icons: Record<string, any> = {
            "openrouter": Zap,
            "openai": Cpu,
            "anthropic": MessageSquare,
            "google": Server,
            "vibeproxy": Terminal
        };
        return icons[provider] || Server;
    }

    // Quick provider presets
    const providerPresets = [
        { id: "openrouter", name: "OpenRouter", desc: "350+ models, one API key", recommended: true },
        { id: "openai", name: "OpenAI", desc: "GPT-4, GPT-4o, o1 models" },
        { id: "anthropic", name: "Anthropic", desc: "Claude 3.5, Claude 4" },
        { id: "google", name: "Google", desc: "Gemini Pro, Flash" },
        { id: "vibeproxy", name: "VibeProxy", desc: "Local OAuth proxy (free)" }
    ];

    // Lifecycle
    onMount(() => {
        // Initialize WebSocket for dashboard
        initWebSocket();

        // Load initial data
        loadDashboardData();
        loadModelsGrouped();

        // Set up periodic refresh
        updateInterval = setInterval(() => {
            if (activeTab === "dashboard") {
                loadDashboardData();
            }
        }, 30000) as unknown as number;  // Refresh every 30 seconds

        // Request notification permissions
        requestNotificationPermission();
    });

    onDestroy(() => {
        if (ws) {
            ws.close();
        }
        if (updateInterval) {
            clearInterval(updateInterval);
        }
    });

    // Effect to handle tab changes
    $effect(() => {
        if (activeTab === "dashboard") {
            // Reconnect WebSocket when returning to dashboard
            if (wsStatus !== "connected") {
                initWebSocket();
            }
        }
    });
</script>

<div class="min-h-screen font-sans" style="background-color: var(--base-100); color: var(--text-primary);">

    <!-- Header -->
    <header class="border-b sticky top-0 z-10 backdrop-blur-sm" style="background-color: var(--base-200); border-color: var(--border-default);">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center">
                    <span class="font-bold text-sm" style="color: var(--text-inverse);">CP</span>
                </div>
                <div>
                    <h1 class="font-bold text-lg tracking-tight">Claude Proxy</h1>
                    <p class="text-xs text-[var(--text-secondary)]">Web Dashboard</p>
                </div>
            </div>
            <div class="flex gap-2 items-center">
                <ThemeSelector />
                <button
                    onclick={() => { activeTab = 'dashboard'; }}
                    class="px-3 py-1.5 text-sm rounded-md border transition-colors {activeTab === 'dashboard' ? 'border-[var(--accent-default)] bg-[var(--base-300)]' : 'border-[var(--border-default)] hover:bg-[var(--base-300)]'}"
                >
                    Dashboard
                </button>
                <button
                    onclick={() => { activeTab = 'setup'; }}
                    class="px-3 py-1.5 text-sm rounded-md border transition-colors {activeTab === 'setup' ? 'border-[var(--accent-default)] bg-[var(--base-300)]' : 'border-[var(--border-default)] hover:bg-[var(--base-300)]'}"
                >
                    Setup
                </button>
                <button
                    onclick={() => { activeTab = 'models'; }}
                    class="px-3 py-1.5 text-sm rounded-md border transition-colors {activeTab === 'models' ? 'border-[var(--accent-default)] bg-[var(--base-300)]' : 'border-[var(--border-default)] hover:bg-[var(--base-300)]'}"
                >
                    Models
                </button>
                <button
                    onclick={() => { activeTab = 'analytics'; }}
                    class="px-3 py-1.5 text-sm rounded-md border transition-colors {activeTab === 'analytics' ? 'border-[var(--accent-default)] bg-[var(--base-300)]' : 'border-[var(--border-default)] hover:bg-[var(--base-300)]'}"
                >
                    Analytics
                </button>
                <button
                    onclick={openCrosstalk}
                    class="px-3 py-1.5 text-sm rounded-md border border-purple-700/50 bg-purple-900/20 text-purple-300 hover:bg-purple-900/30 transition-colors"
                >
                    Crosstalk
                </button>
                <a
                    href="/chain"
                    class="px-3 py-1.5 text-sm rounded-md border border-[var(--border-default)] hover:bg-[var(--base-300)] transition-colors no-underline"
                    style="color: var(--text-primary);"
                >
                    Chain
                </a>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 py-8">

        <!-- DASHBOARD TAB (NEW - LANDING PAGE) -->
        {#if activeTab === 'dashboard'}
            <div class="space-y-6">

                <!-- Welcome & Status Header -->
                <section class="dashboard-card relative overflow-hidden" style="background: linear-gradient(135deg, var(--base-200), var(--base-100));">
                    <!-- Animated Hero Background -->
                    <HeroBackground variant="aurora" />

                    <!-- Nano Banana Decorations -->
                    <div class="absolute top-4 right-20 opacity-60 z-0 animate-float">
                        <NanoBanana size={32} />
                    </div>
                    <div class="absolute bottom-8 left-8 opacity-40 z-0">
                        <Particles size={40} />
                    </div>
                    <div class="absolute top-8 left-1/4 opacity-30 z-0">
                        <NanoBanana size={20} />
                    </div>
                    <div class="absolute bottom-4 right-1/3 opacity-25 z-0 animate-pulse">
                        <Particles size={24} />
                    </div>

                    <div class="flex justify-between items-start mb-6 relative z-10">
                        <div>
                            <h2 class="text-2xl font-bold mb-1">Welcome to Claude Proxy</h2>
                            <p class="text-[var(--text-secondary)] text-sm">Real-time monitoring and analytics</p>
                            
                            <!-- Feature Badges -->
                            <div class="flex flex-wrap gap-2 mt-4">
                                <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs" style="background-color: var(--base-300); border-color: var(--border-default);">
                                    <BrainCircuit size={14} />
                                    <span style="color: var(--text-primary)">AI Routing</span>
                                </div>
                                <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs" style="background-color: var(--base-300); border-color: var(--border-default);">
                                    <MultiModelIcon size={14} />
                                    <span style="color: var(--text-primary)">Multi-Model</span>
                                </div>
                                <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs" style="background-color: var(--base-300); border-color: var(--border-default);">
                                    <ModelIcon size={14} />
                                    <span style="color: var(--text-primary)">Smart Caching</span>
                                </div>
                                <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs" style="background-color: var(--base-300); border-color: var(--border-default);">
                                    <AnalyticsIcon size={14} />
                                    <span style="color: var(--text-primary)">Analytics</span>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center gap-3">
                            <div class="flex items-center gap-2 px-3 py-1.5 rounded border" style="background-color: var(--base-300); border-color: var(--border-default);">
                                <div class="w-2 h-2 rounded-full {systemHealth.websocket_connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}"></div>
                                <span class="text-xs font-mono">{wsStatus.toUpperCase()}</span>
                            </div>
                            <button
                                onclick={loadDashboardData}
                                disabled={dashboardLoading}
                                class="px-3 py-1.5 rounded border flex items-center gap-2 transition-colors hover:bg-[var(--base-300)]" style="background-color: var(--base-300); border-color: var(--border-default);"
                            >
                                <RefreshCw class="w-3 h-3 {dashboardLoading ? 'animate-spin' : ''}" />
                                Refresh
                            </button>
                        </div>
                    </div>

                    <!-- Quick Stats Grid -->
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <!-- Requests Today -->
                        <div class="rounded-lg p-4 border hover:border-[var(--primary-default)] transition-all duration-200 cursor-pointer card-hover card-hover-glow animate-slide-up stagger-1" style="background-color: var(--base-200); border-color: var(--border-default);">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-xs text-[var(--text-secondary)]">Requests Today</span>
                                <ActivityIcon class="w-3 h-3 text-cyan-400" />
                            </div>
                            <div class="text-2xl font-bold text-cyan-400">{stats.requests_today || 0}</div>
                            <div class="text-xs mt-1" style="color: var(--text-tertiary);">
                                {#if liveMetrics.requests_per_second > 0}
                                    +{liveMetrics.requests_per_second}/s
                                {:else}
                                    No current activity
                                {/if}
                            </div>
                        </div>

                        <!-- Cost Today -->
                        <div class="rounded-lg p-4 border hover:border-green-500/50 transition-all duration-200 cursor-pointer card-hover card-hover-glow animate-slide-up stagger-2" style="background-color: var(--base-200); border-color: var(--border-default);">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-xs text-[var(--text-secondary)]">Cost Today</span>
                                <DollarSign class="w-3 h-3 text-green-400" />
                            </div>
                            <div class="text-2xl font-bold text-green-400">${stats.est_cost.toFixed(2)}</div>
                            <div class="text-xs mt-1" style="color: var(--text-tertiary);">
                                {#if liveMetrics.cost_per_second > 0}
                                    ${liveMetrics.cost_per_second.toFixed(4)}/s
                                {:else}
                                    No current spend
                                {/if}
                            </div>
                        </div>

                        <!-- Total Tokens -->
                        <div class="rounded-lg p-4 border hover:border-purple-500/50 transition-all duration-200 cursor-pointer card-hover card-hover-glow animate-slide-up stagger-3" style="background-color: var(--base-200); border-color: var(--border-default);">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-xs text-[var(--text-secondary)]">Total Tokens</span>
                                <Layers class="w-3 h-3 text-purple-400" />
                            </div>
                            <div class="text-2xl font-bold text-purple-400">{formatTokens(stats.total_tokens)}</div>
                            <div class="text-xs mt-1" style="color: var(--text-tertiary);">
                                {#if liveMetrics.tokens_per_second > 0}
                                    +{liveMetrics.tokens_per_second.toFixed(0)}/s
                                {:else}
                                    No current processing
                                {/if}
                            </div>
                        </div>

                        <!-- Avg Latency -->
                        <div class="rounded-lg p-4 border hover:border-amber-500/50 transition-all duration-200 cursor-pointer card-hover card-hover-glow animate-slide-up stagger-4" style="background-color: var(--base-200); border-color: var(--border-default);">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-xs text-[var(--text-secondary)]">Avg Latency</span>
                                <Clock class="w-3 h-3 text-amber-400" />
                            </div>
                            <div class="text-2xl font-bold text-amber-400">{stats.avg_latency || 0}ms</div>
                            <div class="text-xs mt-1" style="color: var(--text-tertiary);">
                                {#if liveMetrics.active_requests > 0}
                                    {liveMetrics.active_requests} active
                                {:else}
                                    All requests complete
                                {/if}
                            </div>
                        </div>
                    </div>

                    <!-- Current Models & Live Speed/Usage -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <!-- Current Models -->
                        <div class="rounded-lg p-4 border" style="background-color: var(--base-200); border-color: var(--border-default);">
                            <h3 class="text-sm font-bold mb-3 flex items-center gap-2">
                                <Cpu class="w-4 h-4 text-purple-400" />
                                Current Models
                            </h3>
                            <div class="space-y-2">
                                <div class="flex justify-between items-center p-2 rounded" style="background-color: var(--base-100);">
                                    <span class="text-xs uppercase font-bold text-purple-400">BIG</span>
                                    <span class="font-mono text-sm text-cyan-400 truncate max-w-[200px]">{config.big_model || 'Not set'}</span>
                                </div>
                                <div class="flex justify-between items-center p-2 rounded" style="background-color: var(--base-100);">
                                    <span class="text-xs uppercase font-bold text-cyan-400">MIDDLE</span>
                                    <span class="font-mono text-sm text-cyan-400 truncate max-w-[200px]">{config.middle_model || 'Not set'}</span>
                                </div>
                                <div class="flex justify-between items-center p-2 rounded" style="background-color: var(--base-100);">
                                    <span class="text-xs uppercase font-bold text-green-400">SMALL</span>
                                    <span class="font-mono text-sm text-cyan-400 truncate max-w-[200px]">{config.small_model || 'Not set'}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Live Speed Stats -->
                        <div class="rounded-lg p-4 border" style="background-color: var(--base-200); border-color: var(--border-default);">
                            <h3 class="text-sm font-bold mb-3 flex items-center gap-2">
                                <ZapIcon size={16} class="text-amber-400" />
                                Live Speed Stats
                            </h3>
                            <div class="grid grid-cols-2 gap-3">
                                <div class="p-2 rounded text-center" style="background-color: var(--base-100);">
                                    <div class="text-lg font-bold text-cyan-400">{liveMetrics.requests_per_second.toFixed(1)}</div>
                                    <div class="text-xs" style="color: var(--text-tertiary);">req/sec</div>
                                </div>
                                <div class="p-2 rounded text-center" style="background-color: var(--base-100);">
                                    <div class="text-lg font-bold text-purple-400">{liveMetrics.tokens_per_second.toFixed(0)}</div>
                                    <div class="text-xs" style="color: var(--text-tertiary);">tokens/sec</div>
                                </div>
                                <div class="p-2 rounded text-center" style="background-color: var(--base-100);">
                                    <div class="text-lg font-bold text-green-400">${liveMetrics.cost_per_second.toFixed(4)}</div>
                                    <div class="text-xs" style="color: var(--text-tertiary);">cost/sec</div>
                                </div>
                                <div class="p-2 rounded text-center" style="background-color: var(--base-100);">
                                    <div class="text-lg font-bold text-amber-400">{liveMetrics.active_requests}</div>
                                    <div class="text-xs" style="color: var(--text-tertiary);">active</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- System Health Bar -->
                    <div class="rounded-lg p-4 border" style="background-color: var(--base-100); border-color: var(--border-default);">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs text-[var(--text-secondary)]">System Health</span>
                            <div class="flex items-center gap-3 text-xs font-mono">
                                <span>⚡ Uptime: {systemHealth.uptime}</span>
                                <span>💾 DB: {systemHealth.db_size}MB</span>
                            </div>
                        </div>
                        <div class="flex gap-2">
                            <div class="flex-1">
                                <div class="flex justify-between text-xs mb-1" style="color: var(--text-tertiary);">
                                    <span>CPU</span>
                                    <span>{systemHealth.cpu_usage}%</span>
                                </div>
                                <div class="h-1.5 rounded-full overflow-hidden" style="background-color: var(--base-300);">
                                    <div class="h-full bg-cyan-500 transition-all duration-300" style="width: {systemHealth.cpu_usage}%"></div>
                                </div>
                            </div>
                            <div class="flex-1">
                                <div class="flex justify-between text-xs mb-1" style="color: var(--text-tertiary);">
                                    <span>Memory</span>
                                    <span>{systemHealth.memory_usage}%</span>
                                </div>
                                <div class="h-1.5 rounded-full overflow-hidden" style="background-color: var(--base-300);">
                                    <div class="h-full bg-purple-500 transition-all duration-300" style="width: {systemHealth.memory_usage}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Alert Section -->
                {#if activeAlerts.length > 0 || hasCriticalAlerts}
                    <section class="dashboard-card">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="font-bold flex items-center gap-2">
                                <Bell class="w-4 h-4 {hasCriticalAlerts ? 'text-red-400' : 'text-amber-400'}" />
                                Active Alerts
                            </h3>
                            <button
                                onclick={() => activeAlerts = []}
                                class="text-xs px-2 py-1 rounded border transition-colors hover:bg-[var(--base-300)]" style="background-color: var(--base-300); border-color: var(--border-default);"
                            >
                                Clear All
                            </button>
                        </div>

                        <div class="space-y-2">
                            {#each activeAlerts as alert, i}
                                <div class="flex items-start gap-3 p-3 rounded border {alert.severity === 'critical' ? 'border-red-500 bg-red-900/20' : 'border-amber-500 bg-amber-900/20'}">
                                    {#if alert.severity === 'critical'}
                                        <AlertTriangle class="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                                    {:else}
                                        <Info class="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                                    {/if}
                                    <div class="flex-1">
                                        <div class="font-semibold text-sm">{alert.rule_name || alert.message}</div>
                                        <div class="text-xs text-[var(--text-secondary)] mt-1">{alert.message}</div>
                                        <div class="text-xs mt-1" style="color: var(--text-tertiary);">{alert.timestamp}</div>
                                    </div>
                                    <button
                                        onclick={() => { activeAlerts = activeAlerts.filter((_, idx) => idx !== i); }}
                                        class="transition-colors" style="color: var(--text-tertiary);"
                                    >
                                        <X class="w-3 h-3" />
                                    </button>
                                </div>
                            {/each}
                        </div>
                    </section>
                {/if}

                <!-- Budget & Cost Tracking -->
                <section class="dashboard-card">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="font-bold flex items-center gap-2">
                            <Target class="w-4 h-4 text-green-400" />
                            Budget Tracking
                        </h3>
                        <button class="text-xs px-3 py-1 rounded border transition-colors hover:bg-[var(--base-300)]" style="background-color: var(--base-300); border-color: var(--border-default);">
                            Configure Budget
                        </button>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <!-- Daily Budget -->
                        <div>
                            <div class="flex justify-between text-sm mb-2">
                                <span class="text-[var(--text-secondary)]">Daily Budget</span>
                                <span class="{budgetData.usage_percentage >= 80 ? 'text-amber-400 font-bold' : 'text-green-400'}">
                                    ${budgetData.current_daily.toFixed(2)} / ${budgetData.daily_limit.toFixed(2)}
                                </span>
                            </div>
                            <div class="h-2 rounded-full overflow-hidden relative" style="background-color: var(--base-300);">
                                <div
                                    class="h-full transition-all duration-300 rounded-full
                                        {budgetData.usage_percentage >= 95 ? 'bg-red-500' :
                                          budgetData.usage_percentage >= 80 ? 'bg-amber-500' :
                                          'bg-green-500'}"
                                    style="width: {budgetData.usage_percentage}%"
                                ></div>
                                <!-- 80% marker -->
                                <div class="absolute top-0 bottom-0 w-0.5 left-[80%]" style="background-color: var(--border-strong);"></div>
                            </div>
                            <div class="text-xs mt-1" style="color: var(--text-tertiary);">
                                {budgetData.usage_percentage.toFixed(0)}% used
                                {#if budgetData.usage_percentage >= 95}
                                    • <span class="text-red-400">Near limit!</span>
                                {:else if budgetData.usage_percentage >= 80}
                                    • <span class="text-amber-400">Approaching limit</span>
                                {/if}
                            </div>
                        </div>

                        <!-- Monthly Budget -->
                        <div>
                            <div class="flex justify-between text-sm mb-2">
                                <span class="text-[var(--text-secondary)]">Monthly Budget</span>
                                <span class="font-medium" style="color: var(--text-primary);">
                                    ${budgetData.current_monthly.toFixed(0)} / ${budgetData.monthly_limit}
                                </span>
                            </div>
                            <div class="h-2 rounded-full overflow-hidden" style="background-color: var(--base-300);">
                                <div
                                    class="h-full bg-cyan-500 transition-all duration-300 rounded-full"
                                    style="width: {(budgetData.current_monthly / budgetData.monthly_limit * 100)}%"
                                ></div>
                            </div>
                            <div class="text-xs mt-1" style="color: var(--text-tertiary);">
                                {(budgetData.current_monthly / budgetData.monthly_limit * 100).toFixed(1)}% used
                            </div>
                        </div>
                    </div>

                    <!-- Alert Configuration -->
                    <div class="mt-4 pt-4 border-t" style="border-color: var(--border-default);">
                        <div class="flex items-center justify-between">
                            <span class="text-sm text-[var(--text-secondary)]">Alert Settings</span>
                            <div class="flex gap-2">
                                <label class="flex items-center gap-2 text-xs cursor-pointer">
                                    <input type="checkbox" checked class="rounded border" style="background-color: var(--base-300); border-color: var(--border-default);" />
                                    Email at 80%
                                </label>
                                <label class="flex items-center gap-2 text-xs cursor-pointer">
                                    <input type="checkbox" checked class="rounded border" style="background-color: var(--base-300); border-color: var(--border-default);" />
                                    Slack at 95%
                                </label>
                                <button class="text-xs px-3 py-1 rounded border transition-colors hover:bg-[var(--base-300)]" style="background-color: var(--base-300); border-color: var(--border-default);">
                                    Manage Rules
                                </button>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Real-time Model Distribution -->
                {#if Object.keys(liveMetrics.model_distribution).length > 0}
                    <section class="dashboard-card">
                        <h3 class="font-bold mb-4 flex items-center gap-2">
                            <ActivityIcon class="w-4 h-4 text-cyan-400" />
                            Current Activity Distribution (Last 60s)
                        </h3>
                        <div class="space-y-2">
                            {#each Object.entries(liveMetrics.model_distribution) as [model, count]}
                                <div class="flex items-center gap-3 text-sm">
                                    <div class="font-mono text-xs w-32 text-[var(--text-secondary)] truncate">
                                        {model.split('/').pop() || model}
                                    </div>
                                    <div class="flex-1 h-2 rounded-full overflow-hidden" style="background-color: var(--base-300);">
                                        <div
                                            class="h-full bg-cyan-500"
                                            style="width: {(count / Math.max(...Object.values(liveMetrics.model_distribution)) * 100)}%"
                                        ></div>
                                    </div>
                                    <div class="text-xs text-[var(--text-secondary)] w-12 text-right">{count}</div>
                                </div>
                            {/each}
                        </div>
                    </section>
                {/if}

                <!-- Features Banner -->
                <section class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <button type="button" class="dashboard-card p-4 flex items-center gap-4 group cursor-pointer hover:border-[var(--primary-default)] text-left card-hover-lift animate-slide-up stagger-1" onclick={() => activeTab = 'analytics'}>
                        <div class="p-3 rounded-lg transition-transform group-hover:scale-110" style="background-color: var(--base-300);">
                            <RoutingIcon size={24} class="text-cyan-400 transition-transform" />
                        </div>
                        <div>
                            <h4 class="font-semibold text-sm">Smart Routing</h4>
                            <p class="text-xs text-[var(--text-secondary)]">AI-powered request distribution</p>
                        </div>
                    </button>
                    
                    <button type="button" class="dashboard-card p-4 flex items-center gap-4 group cursor-pointer hover:border-[var(--primary-default)] text-left card-hover-lift animate-slide-up stagger-2" onclick={() => activeTab = 'models'}>
                        <div class="p-3 rounded-lg transition-transform group-hover:scale-110" style="background-color: var(--base-300);">
                            <CacheIcon size={24} class="text-purple-400 transition-transform" />
                        </div>
                        <div>
                            <h4 class="font-semibold text-sm">Intelligent Caching</h4>
                            <p class="text-xs text-[var(--text-secondary)]">Reduce costs with smart responses</p>
                        </div>
                    </button>
                    
                    <button type="button" class="dashboard-card p-4 flex items-center gap-4 group cursor-pointer hover:border-[var(--primary-default)] text-left card-hover-lift animate-slide-up stagger-3">
                        <div class="p-3 rounded-lg transition-transform group-hover:scale-110" style="background-color: var(--base-300);">
                            <ShieldIcon size={24} class="text-green-400 transition-transform" />
                        </div>
                        <div>
                            <h4 class="font-semibold text-sm">Privacy First</h4>
                            <p class="text-xs text-[var(--text-secondary)]">Your data stays yours</p>
                        </div>
                    </button>
                    
                    <button type="button" class="dashboard-card p-4 flex items-center gap-4 group cursor-pointer hover:border-[var(--primary-default)] text-left card-hover-lift animate-slide-up stagger-4">
                        <div class="p-3 rounded-lg transition-transform group-hover:scale-110" style="background-color: var(--base-300);">
                            <ZapIcon size={24} class="text-amber-400 transition-transform" />
                        </div>
                        <div>
                            <h4 class="font-semibold text-sm">Lightning Fast</h4>
                            <p class="text-xs text-[var(--text-secondary)]">Sub-100ms response times</p>
                        </div>
                    </button>
                </section>

                <!-- Crosstalk Overview -->
                <section class="dashboard-card">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="font-bold flex items-center gap-2">
                            <Zap class="w-4 h-4 text-purple-400" />
                            Crosstalk Sessions
                        </h3>
                        <button
                            onclick={openCrosstalk}
                            class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded text-sm flex items-center gap-2 transition-colors"
                        >
                            <Play class="w-3 h-3" />
                            Launch Studio
                        </button>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div class="rounded p-3 border" style="background-color: var(--base-100); border-color: var(--border-default);">
                            <div class="text-xs text-[var(--text-secondary)]">Total Sessions</div>
                            <div class="text-xl font-bold text-purple-400">{crosstalkStats.total_sessions}</div>
                        </div>
                        <div class="rounded p-3 border" style="background-color: var(--base-100); border-color: var(--border-default);">
                            <div class="text-xs text-[var(--text-secondary)]">Avg Cost</div>
                            <div class="text-xl font-bold text-green-400">${crosstalkStats.avg_cost_per_session.toFixed(2)}</div>
                        </div>
                        <div class="rounded p-3 border" style="background-color: var(--base-100); border-color: var(--border-default);">
                            <div class="text-xs text-[var(--text-secondary)]">Avg Rounds</div>
                            <div class="text-xl font-bold text-cyan-400">{crosstalkStats.avg_rounds}</div>
                        </div>
                        <div class="rounded p-3 border" style="background-color: var(--base-100); border-color: var(--border-default);">
                            <div class="text-xs text-[var(--text-secondary)]">Top Paradigm</div>
                            <div class="text-xl font-bold text-amber-400 capitalize">{crosstalkStats.top_paradigm}</div>
                        </div>
                        <div class="rounded p-3 border" style="background-color: var(--base-100); border-color: var(--border-default);">
                            <div class="text-xs text-[var(--text-secondary)]">Active Now</div>
                            <div class="text-xl font-bold" style="color: var(--text-primary);">{crosstalkStats.active_sessions}</div>
                        </div>
                    </div>
                </section>

                <!-- Quick Actions -->
                <section class="dashboard-card">
                    <h3 class="font-bold mb-4">Quick Actions</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <button
                            onclick={() => activeTab = 'analytics'}
                            class="p-4 rounded-lg border text-left transition-all hover:border-cyan-500 group"
                            style="background-color: var(--base-300); border-color: var(--border-default);"
                        >
                            <div class="flex items-center gap-2 mb-2">
                                <BarChart3 class="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                                <span class="font-semibold">View Analytics</span>
                            </div>
                            <div class="text-xs text-[var(--text-secondary)]">Interactive charts and insights</div>
                        </button>

                        <button
                            onclick={() => activeTab = 'models'}
                            class="p-4 rounded-lg border text-left transition-all hover:border-purple-500 group"
                            style="background-color: var(--base-300); border-color: var(--border-default);"
                        >
                            <div class="flex items-center gap-2 mb-2">
                                <Cpu class="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
                                <span class="font-semibold">Manage Models</span>
                            </div>
                            <div class="text-xs text-[var(--text-secondary)]">Configure providers and routing</div>
                        </button>

                        <button
                            onclick={() => activeTab = 'setup'}
                            class="p-4 rounded-lg border text-left transition-all hover:border-amber-500 group"
                            style="background-color: var(--base-300); border-color: var(--border-default);"
                        >
                            <div class="flex items-center gap-2 mb-2">
                                <Settings class="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                                <span class="font-semibold">System Config</span>
                            </div>
                            <div class="text-xs text-[var(--text-secondary)]">Provider settings and API keys</div>
                        </button>
                    </div>
                </section>

                <!-- Last Update & Connection Info -->
                <div class="text-center text-xs flex items-center justify-center gap-4" style="color: var(--text-tertiary);">
                    <span>Last updated: {lastUpdate}</span>
                    <span>•</span>
                    <span>WebSocket: {wsStatus}</span>
                    {#if wsReconnecting}
                        <span>•</span>
                        <span class="text-amber-400">Reconnecting...</span>
                    {/if}
                </div>
            </div>

        <!-- SETUP TAB (Original) -->
        {:else if activeTab === 'setup'}
            <div class="max-w-2xl mx-auto space-y-6">
                <!-- Quick Provider Selection -->
                <section class="mb-8">
                    <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
                        <Server class="w-5 h-5 text-cyan-400" />
                        Quick Setup - Choose Provider
                    </h2>
                    <p class="text-[var(--text-secondary)] mb-4 text-sm">
                        Select a provider to automatically configure routing. No manual backend selection needed.
                    </p>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {#each providerPresets as preset}
                            <button
                                onclick={() => selectProvider(preset.id)}
                                disabled={applyingConfig}
                                class="p-4 rounded-lg border text-left transition-all hover:border-cyan-500 group relative overflow-hidden {selectedProvider === preset.id ? 'border-cyan-500' : 'border-[var(--border-default)]'}"
                                style="background-color: {selectedProvider === preset.id ? 'var(--base-200)' : 'var(--base-100)'};">
                            >
                                <div class="flex items-center justify-between mb-2">
                                    <span class="font-semibold">{preset.name}</span>
                                    {#if preset.recommended}
                                        <span class="text-xs bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded">Recommended</span>
                                    {/if}
                                </div>
                                <div class="text-xs text-[var(--text-secondary)]">{preset.desc}</div>
                                <div class="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-cyan-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            </button>
                        {/each}
                    </div>
                </section>

                <!-- Manual API Key Entry -->
                {#if selectedProvider && selectedProvider !== 'vibeproxy'}
                    <section class="dashboard-card">
                        <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                            <Key class="w-5 h-5 text-amber-400" />
                            API Key Configuration
                        </h3>

                        <div class="space-y-4">
                            <div>
                                <label for="apiKeyInput" class="text-sm text-[var(--text-secondary)] mb-1 block">API Key for {getProviderDisplayName(selectedProvider)}</label>
                                <input
                                    id="apiKeyInput"
                                    type="password"
                                    bind:value={api_key}
                                    placeholder="sk-... or similar"
                                    class="w-full px-3 py-2 rounded border focus:border-cyan-500 focus:outline-none text-sm font-mono"
                                    style="background-color: var(--base-100); border-color: var(--border-default); color: var(--text-primary);"
                                />
                            </div>

                            <div class="flex gap-2">
                                <button
                                    onclick={() => saveApiKey()}
                                    disabled={applyingConfig || !api_key}
                                    class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 rounded font-medium text-sm transition-colors"
                                >
                                    Save API Key
                                </button>
                                <button
                                    onclick={() => { activeTab = 'models'; }}
                                    class="px-4 py-2 rounded font-medium text-sm transition-colors border hover:bg-[var(--base-300)]"
                                    style="border-color: var(--border-default);"
                                >
                                    Skip to Models →
                                </button>
                            </div>
                        </div>
                    </section>
                {/if}

                <!-- Status Messages -->
                {#if configMessage}
                    <div class="mt-4 p-3 rounded border text-sm flex items-center gap-2" style="background-color: var(--base-200); border-color: var(--border-default);">
                        {#if configMessage.includes('✅')}
                            <CheckCircle2 class="w-4 h-4 text-green-400" />
                        {:else if configMessage.includes('❌')}
                            <AlertCircle class="w-4 h-4 text-red-400" />
                        {:else if configMessage.includes('⚠️')}
                            <Info class="w-4 h-4 text-amber-400" />
                        {:else}
                            <Info class="w-4 h-4 text-cyan-400" />
                        {/if}
                        <span>{configMessage}</span>
                    </div>
                {/if}

                <!-- Current Configuration -->
                <section class="dashboard-card">
                    <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                        <Settings class="w-5 h-5 text-purple-400" />
                        Current Configuration
                    </h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-[var(--text-secondary)]">Provider:</span>
                            <span class="font-mono">{getProviderDisplayName(config.default_provider)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[var(--text-secondary)]">Base URL:</span>
                            <span class="font-mono text-xs">{config.openai_base_url}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[var(--text-secondary)]">BIG Model:</span>
                            <span class="font-mono">{config.big_model || 'Not set'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[var(--text-secondary)]">MIDDLE Model:</span>
                            <span class="font-mono">{config.middle_model || 'Not set'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-[var(--text-secondary)]">SMALL Model:</span>
                            <span class="font-mono">{config.small_model || 'Not set'}</span>
                        </div>
                    </div>
                </section>
            </div>

        <!-- MODELS TAB (Enhanced with OpenRouter) -->
        {:else if activeTab === 'models'}
            <div class="space-y-6">
                <!-- Header -->
                <div>
                    <h2 class="text-xl font-bold">Model Selection</h2>
                    <p class="text-[var(--text-secondary)] text-sm">Smart categories from OpenRouter - click to select</p>
                </div>

                <!-- New Model Selector -->
                <ModelSelector 
                    currentModels={{ 
                        big: config.big_model, 
                        middle: config.middle_model, 
                        small: config.small_model 
                    }}
                    onSelect={(tier, modelId) => selectModel(tier, modelId)}
                />

                <!-- Current Configuration -->
                <section class="dashboard-card">
                    <h3 class="font-bold mb-4 flex items-center gap-2">
                        <Settings class="w-4 h-4" style="color: var(--text-secondary);" />
                        Active Configuration
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {#each ['big', 'middle', 'small'] as tier}
                            <div class="p-3 rounded border" style="background-color: var(--base-100); border-color: var(--border-default);">
                                <div class="text-xs uppercase font-bold mb-1" style="color: var(--text-tertiary);">{tier}</div>
                                <div class="font-mono text-sm text-cyan-400 truncate">
                                    {config[`${tier}_model`] || 'Not set'}
                                </div>
                            </div>
                        {/each}
                    </div>
                </section>
            </div>

        <!-- ANALYTICS TAB (Enhanced) -->
        {:else if activeTab === 'analytics'}
            <div class="space-y-6">
                <!-- Header -->
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-xl font-bold">Usage Analytics</h2>
                        <p class="text-[var(--text-secondary)] text-sm">Real-time metrics and insights</p>
                    </div>
                    <button
                        onclick={loadDashboardData}
                        disabled={analyticsLoading}
                        class="px-3 py-2 rounded text-sm border flex items-center gap-2 transition-colors hover:bg-[var(--base-300)]"
                        style="background-color: var(--base-300); border-color: var(--border-default);"
                    >
                        <RefreshCw class="w-4 h-4 {analyticsLoading ? 'animate-spin' : ''}" />
                        Refresh
                    </button>
                </div>

                <!-- Stats Cards -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="rounded-lg p-4 border" style="background-color: var(--base-200); border-color: var(--border-default);">
                        <div class="text-xs mb-1" style="color: var(--text-secondary);">Requests Today</div>
                        <div class="text-2xl font-bold text-cyan-400">{stats.requests_today || 0}</div>
                    </div>
                    <div class="rounded-lg p-4 border" style="background-color: var(--base-200); border-color: var(--border-default);">
                        <div class="text-xs mb-1" style="color: var(--text-secondary);">Total Tokens</div>
                        <div class="text-2xl font-bold text-purple-400">
                            {#if (stats.total_tokens || 0) > 1000000}
                                {((stats.total_tokens || 0) / 1000000).toFixed(1)}M
                            {:else if (stats.total_tokens || 0) > 1000}
                                {((stats.total_tokens || 0) / 1000).toFixed(1)}K
                            {:else}
                                {stats.total_tokens || 0}
                            {/if}
                        </div>
                    </div>
                    <div class="rounded-lg p-4 border" style="background-color: var(--base-200); border-color: var(--border-default);">
                        <div class="text-xs mb-1" style="color: var(--text-secondary);">Est. Cost</div>
                        <div class="text-2xl font-bold text-green-400">${(stats.est_cost || 0).toFixed(4)}</div>
                    </div>
                    <div class="rounded-lg p-4 border" style="background-color: var(--base-200); border-color: var(--border-default);">
                        <div class="text-xs mb-1" style="color: var(--text-secondary);">Avg Latency</div>
                        <div class="text-2xl font-bold text-amber-400">{stats.avg_latency || 0}ms</div>
                    </div>
                </div>

                <!-- Analytics Data (Note: Full implementation requires /api/analytics endpoints) -->
                <div class="rounded-lg p-8 border text-center" style="background-color: var(--base-200); border-color: var(--border-default);">
                    <div class="max-w-md mx-auto">
                        <div class="rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4" style="background-color: var(--base-100);">
                            <Activity class="w-8 h-8" style="color: var(--text-tertiary);" />
                        </div>
                        <h3 class="text-lg font-bold mb-2">Advanced Analytics</h3>
                        <p class="mb-4 text-sm" style="color: var(--text-secondary);">
                            Full analytics dashboard with interactive charts, time-series data, and AI insights.
                        </p>
                        <div class="p-3 rounded border font-mono text-xs text-left mb-4" style="background-color: var(--base-100); border-color: var(--border-default);">
                            <div style="color: var(--text-secondary);">// Available Endpoints:</div>
                            <div>GET /api/analytics/dashboard</div>
                            <div>GET /api/analytics/timeseries</div>
                            <div>GET /api/analytics/model-comparison</div>
                            <div>GET /api/analytics/insights</div>
                            <div>GET /api/analytics/cost-breakdown</div>
                        </div>
                        <p class="text-xs mt-3" style="color: var(--text-tertiary);">Use the Crosstalk Studio for live session monitoring or enable usage tracking for full analytics.</p>
                        <button
                            onclick={() => activeTab = 'dashboard'}
                            class="mt-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded text-sm font-medium"
                        >
                            Return to Dashboard
                        </button>
                    </div>
                </div>
            </div>
        {/if}
    </main>

    <!-- Footer -->
    <footer class="border-t py-6 mt-12" style="border-color: var(--border-default);">
        <div class="max-w-7xl mx-auto px-6 text-center text-sm" style="color: var(--text-tertiary);">
            Claude Proxy Web Dashboard v2.1 • {new Date().getFullYear()}
            <div class="mt-2 text-xs">
                {#if wsStatus === 'connected'}
                    <span class="text-green-400">🟢 Live Updates Active</span>
                {:else}
                    <span class="text-[var(--text-secondary)]">⚪ Live Updates Available</span>
                {/if}
            </div>
        </div>
    </footer>
</div>

<style>
    /* Modern scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #18181b;
    }
    ::-webkit-scrollbar-thumb {
        background: #3f3f46;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #52525b;
    }

    /* Selection highlight */
    ::selection {
        background: #06b6d4;
        color: #000;
    }

    /* Glow effects */
    .glow-on-hover:hover {
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
    }

    /* Loading pulse */
    @keyframes pulse-slow {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .pulse-slow {
        animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    /* Status indicator pulse */
    @keyframes status-pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
</style>