<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { 
        Activity, Zap, Server, RefreshCw, TrendingUp, DollarSign, 
        BarChart3, CheckCircle2, AlertCircle, Cpu, Database,
        Wifi, Tool, Cache, Clock, Layers, ArrowUpRight, ArrowDownRight
    } from "lucide-svelte";
    import NanoBanana from '$lib/components/icons/NanoBanana.svelte';
    import Particles from '$lib/components/icons/Particles.svelte';

    // Real-time metrics state
    let aggregateMetrics = $state<any>(null);
    let sessions = $state<any[]>([]);
    let toolAnalytics = $state<any>(null);
    let cacheAnalytics = $state<any>(null);
    let loading = $state(true);
    let lastUpdate = $state<Date>(new Date());
    let wsConnected = $state(false);

    // Animation states
    let metricAnimations = $state<Record<string, { from: number, to: number, progress: number }>>({});
    let pulseStates = $state<Record<string, boolean>>({});

    // Fetch all metrics
    async function fetchAllMetrics() {
        try {
            const [aggRes, sessionsRes, toolRes, cacheRes] = await Promise.all([
                fetch('/api/metrics/aggregate'),
                fetch('/api/metrics/sessions'),
                fetch('/api/metrics/tool-analytics?hours=24'),
                fetch('/api/metrics/cache-analytics?hours=24')
            ]);

            aggregateMetrics = await aggRes.json();
            sessions = (await sessionsRes.json()).sessions || [];
            toolAnalytics = await toolRes.json();
            cacheAnalytics = await cacheRes.json();
            
            lastUpdate = new Date();
            loading = false;

            // Trigger animations
            triggerAnimations();
        } catch (error) {
            console.error('Failed to fetch metrics:', error);
            loading = false;
        }
    }

    // Trigger number animations
    function triggerAnimations() {
        if (!aggregateMetrics?.metrics) return;
        
        const metrics = aggregateMetrics.metrics;
        ['total_requests', 'total_tokens', 'total_cost', 'avg_tokens_per_second'].forEach(key => {
            const value = metrics[key] || 0;
            metricAnimations[key] = {
                from: 0,
                to: value,
                progress: 0
            };
            
            // Animate
            const duration = 1000;
            const start = performance.now();
            
            const animate = (current: number) => {
                const elapsed = current - start;
                const progress = Math.min(elapsed / duration, 1);
                
                // Easing function
                const easeOut = 1 - Math.pow(1 - progress, 3);
                
                metricAnimations[key].progress = easeOut;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };
            
            requestAnimationFrame(animate);
        });
    }

    // Pulse animation for live indicators
    function triggerPulse(elementId: string) {
        pulseStates[elementId] = true;
        setTimeout(() => {
            pulseStates[elementId] = false;
        }, 200);
    }

    // WebSocket for real-time updates
    let ws: WebSocket | null = null;
    
    function connectWebSocket() {
        try {
            ws = new WebSocket(`ws://${window.location.host}/ws/live`);
            
            ws.onopen = () => {
                wsConnected = true;
                console.log('✅ WebSocket connected');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'metrics_update') {
                    // Update aggregate metrics
                    if (data.metrics) {
                        aggregateMetrics = {
                            ...aggregateMetrics,
                            metrics: data.metrics
                        };
                        triggerPulse('live-metrics');
                    }
                }
                
                if (data.type === 'request_event') {
                    // New request - trigger pulse
                    triggerPulse('request-feed');
                }
            };
            
            ws.onclose = () => {
                wsConnected = false;
                // Reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                ws?.close();
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }

    // Format helpers
    function formatNumber(num: number): string {
        if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
        if (num >= 1_000) return (num / 1_000).toFixed(1) + 'k';
        return num.toFixed(0);
    }

    function formatCurrency(num: number): string {
        return '$' + num.toFixed(4);
    }

    function formatTime(date: Date): string {
        return date.toLocaleTimeString();
    }

    function getAnimatedValue(key: string): number {
        const anim = metricAnimations[key];
        if (!anim) return 0;
        return anim.from + (anim.to - anim.from) * anim.progress;
    }

    // Auto-refresh every 10 seconds
    let refreshInterval: number;

    onMount(() => {
        fetchAllMetrics();
        connectWebSocket();
        refreshInterval = setInterval(fetchAllMetrics, 10000);
    });

    onDestroy(() => {
        clearInterval(refreshInterval);
        ws?.close();
    });
</script>

<svelte:head>
    <title>Real-Time Dashboard | Claude Code Proxy</title>
</svelte:head>

<div class="dashboard-container">
    <!-- Hero Section with Live Indicator -->
    <section class="hero-section">
        <div class="hero-content">
            <div class="hero-title">
                <Particles class="particles-icon" />
                <h1>Real-Time Dashboard</h1>
                <div class="live-indicator" class:connected={wsConnected}>
                    <span class="pulse-dot"></span>
                    <span>{wsConnected ? 'LIVE' : 'DISCONNECTED'}</span>
                </div>
            </div>
            <p class="hero-subtitle">Monitor sessions, tool calls, and cache performance in real-time</p>
            <div class="last-update">
                <Clock size={14} />
                <span>Updated: {formatTime(lastUpdate)}</span>
                <button class="refresh-btn" onclick={fetchAllMetrics}>
                    <RefreshCw size={14} />
                </button>
            </div>
        </div>
    </section>

    {#if loading}
        <div class="loading-state">
            <NanoBanana class="loading-icon" />
            <p>Loading metrics...</p>
        </div>
    {:else}
        <!-- Aggregate Metrics Cards -->
        <section class="metrics-grid">
            <!-- Total Requests -->
            <div class="metric-card" id="live-metrics">
                <div class="metric-header">
                    <div class="metric-icon requests">
                        <Activity size={20} />
                    </div>
                    <span class="metric-trend positive">
                        <ArrowUpRight size={14} />
                        Live
                    </span>
                </div>
                <div class="metric-value">
                    {formatNumber(getAnimatedValue('total_requests') || aggregateMetrics?.metrics?.total_requests || 0)}
                </div>
                <div class="metric-label">Total Requests</div>
                <div class="metric-detail">
                    {aggregateMetrics?.metrics?.total_sessions || 0} active sessions
                </div>
            </div>

            <!-- Total Tokens -->
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon tokens">
                        <Layers size={20} />
                    </div>
                </div>
                <div class="metric-value">
                    {formatNumber(getAnimatedValue('total_tokens') || aggregateMetrics?.metrics?.total_tokens || 0)}
                </div>
                <div class="metric-label">Total Tokens</div>
                <div class="metric-detail">
                    {aggregateMetrics?.metrics?.avg_tokens_per_request?.toFixed(0) || 0} avg/request
                </div>
            </div>

            <!-- Tokens/Second -->
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon speed">
                        <Zap size={20} />
                    </div>
                    <span class="metric-speed">
                        {aggregateMetrics?.metrics?.avg_tokens_per_second?.toFixed(0) || 0} t/s
                    </span>
                </div>
                <div class="metric-value">
                    {formatNumber(getAnimatedValue('avg_tokens_per_second') || aggregateMetrics?.metrics?.avg_tokens_per_second || 0)}
                </div>
                <div class="metric-label">Tokens/Second</div>
                <div class="metric-detail">
                    {aggregateMetrics?.metrics?.avg_latency_ms?.toFixed(0) || 0}ms avg latency
                </div>
            </div>

            <!-- Total Cost -->
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon cost">
                        <DollarSign size={20} />
                    </div>
                </div>
                <div class="metric-value">
                    {formatCurrency(getAnimatedValue('total_cost') || aggregateMetrics?.metrics?.total_cost || 0)}
                </div>
                <div class="metric-label">Estimated Cost</div>
                <div class="metric-detail">
                    Cache saved {formatCurrency(cacheAnalytics?.estimated_cost_savings || 0)}
                </div>
            </div>

            <!-- Tool Success Rate -->
            <div class="metric-card" id="request-feed">
                <div class="metric-header">
                    <div class="metric-icon tools">
                        <Tool size={20} />
                    </div>
                    <span class="metric-trend {((toolAnalytics?.success_rate || 0) >= 95) ? 'positive' : 'warning'}">
                        {toolAnalytics?.success_rate || 0}%
                    </span>
                </div>
                <div class="metric-value">
                    {toolAnalytics?.total_tool_calls?.toLocaleString() || 0}
                </div>
                <div class="metric-label">Tool Calls</div>
                <div class="metric-detail">
                    {toolAnalytics?.tools ? Object.keys(toolAnalytics.tools).length : 0} unique tools
                </div>
            </div>

            <!-- Cache Hit Rate -->
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon cache">
                        <Cache size={20} />
                    </div>
                    <span class="metric-trend {(cacheAnalytics?.cache_hit_rate || 0) >= 50 ? 'positive' : 'neutral'}">
                        {cacheAnalytics?.cache_hit_rate || 0}%
                    </span>
                </div>
                <div class="metric-value">
                    {formatNumber(cacheAnalytics?.cached_tokens || 0)}
                </div>
                <div class="metric-label">Cached Tokens</div>
                <div class="metric-detail">
                    {cacheAnalytics?.token_savings_percent || 0}% token savings
                </div>
            </div>
        </section>

        <!-- Active Sessions -->
        <section class="sessions-section">
            <div class="section-header">
                <h2>
                    <Server size={20} />
                    Active Sessions
                </h2>
                <span class="session-count">{sessions.length} sessions</span>
            </div>
            
            {#if sessions.length === 0}
                <div class="empty-state">
                    <Server size={48} />
                    <p>No active sessions</p>
                    <span>Sessions will appear here when users connect</span>
                </div>
            {:else}
                <div class="sessions-grid">
                    {#each sessions as session (session.session_id)}
                        <div class="session-card">
                            <div class="session-header">
                                <div class="session-id">
                                    <Database size={14} />
                                    <code>{session.session_id}</code>
                                </div>
                                <span class="session-status active">●</span>
                            </div>
                            
                            <div class="session-metrics">
                                <div class="session-metric">
                                    <span class="label">Requests</span>
                                    <span class="value">{session.requests}</span>
                                </div>
                                <div class="session-metric">
                                    <span class="label">Tokens</span>
                                    <span class="value">{formatNumber(session.tokens)}</span>
                                </div>
                                <div class="session-metric">
                                    <span class="label">Cost</span>
                                    <span class="value">{formatCurrency(session.cost)}</span>
                                </div>
                            </div>
                            
                            <div class="session-footer">
                                <div class="tool-success">
                                    <CheckCircle2 size={12} />
                                    <span>{session.tool_success_rate}% tool success</span>
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </section>

        <!-- Tool Analytics -->
        <section class="analytics-section">
            <div class="section-header">
                <h2>
                    <BarChart3 size={20} />
                    Tool Analytics (24h)
                </h2>
            </div>
            
            {#if toolAnalytics?.tools && Object.keys(toolAnalytics.tools).length > 0}
                <div class="tools-grid">
                    {#each Object.entries(toolAnalytics.tools) as [toolName, stats]: any}
                        <div class="tool-card">
                            <div class="tool-header">
                                <Tool size={16} />
                                <span class="tool-name">{toolName}</span>
                            </div>
                            <div class="tool-stats">
                                <div class="tool-stat">
                                    <span class="stat-label">Total</span>
                                    <span class="stat-value">{(stats as any).total}</span>
                                </div>
                                <div class="tool-stat">
                                    <span class="stat-label">Success</span>
                                    <span class="stat-value positive">{(stats as any).success}</span>
                                </div>
                                <div class="tool-stat">
                                    <span class="stat-label">Failed</span>
                                    <span class="stat-value negative">{(stats as any).failure}</span>
                                </div>
                            </div>
                            <div class="tool-progress">
                                <div class="progress-bar">
                                    <div 
                                        class="progress-fill" 
                                        style="width: {(stats as any).success_rate}%"
                                        class:success={(stats as any).success_rate >= 95}
                                        class:warning={(stats as any).success_rate < 95 && (stats as any).success_rate >= 80}
                                        class:error={(stats as any).success_rate < 80}
                                    ></div>
                                </div>
                                <span class="progress-label">{(stats as any).success_rate}% success</span>
                            </div>
                        </div>
                    {/each}
                </div>
            {:else}
                <div class="empty-state">
                    <Tool size={48} />
                    <p>No tool call data yet</p>
                    <span>Tool calls will be tracked here</span>
                </div>
            {/if}
        </section>
    {/if}
</div>

<style>
    /* Dashboard Container */
    .dashboard-container {
        max-width: 1600px;
        margin: 0 auto;
        padding: 2rem;
        animation: fadeIn 0.5s ease-out;
    }

    /* Hero Section */
    .hero-section {
        margin-bottom: 2rem;
        animation: slideDown 0.6s ease-out;
    }

    .hero-content {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    .hero-title {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }

    .hero-title h1 {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6, #9333ea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .particles-icon {
        width: 32px;
        height: 32px;
        animation: float 3s ease-in-out infinite;
    }

    .live-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
    }

    .live-indicator.connected {
        background: rgba(34, 197, 94, 0.1);
        color: #22c55e;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
        animation: pulse 2s infinite;
    }

    .hero-subtitle {
        color: var(--text-muted);
        margin-bottom: 1rem;
    }

    .last-update {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .refresh-btn {
        background: transparent;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 4px;
        transition: all 0.2s;
    }

    .refresh-btn:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
        transform: rotate(90deg);
    }

    /* Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        animation: scaleIn 0.5s ease-out backwards;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        border-color: var(--primary);
        box-shadow: 0 12px 24px rgba(59, 130, 246, 0.15);
    }

    .metric-card:nth-child(1) { animation-delay: 0.1s; }
    .metric-card:nth-child(2) { animation-delay: 0.15s; }
    .metric-card:nth-child(3) { animation-delay: 0.2s; }
    .metric-card:nth-child(4) { animation-delay: 0.25s; }
    .metric-card:nth-child(5) { animation-delay: 0.3s; }
    .metric-card:nth-child(6) { animation-delay: 0.35s; }

    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .metric-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .metric-icon.requests { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
    .metric-icon.tokens { background: rgba(147, 51, 234, 0.1); color: #9333ea; }
    .metric-icon.speed { background: rgba(251, 191, 36, 0.1); color: #fbbf24; }
    .metric-icon.cost { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
    .metric-icon.tools { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
    .metric-icon.cache { background: rgba(6, 182, 212, 0.1); color: #06b7d4; }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
    }

    .metric-detail {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .metric-trend {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
    }

    .metric-trend.positive { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
    .metric-trend.warning { background: rgba(251, 191, 36, 0.1); color: #fbbf24; }
    .metric-trend.neutral { background: rgba(107, 114, 128, 0.1); color: #6b7280; }

    .metric-speed {
        font-size: 0.75rem;
        font-weight: 600;
        color: #fbbf24;
    }

    /* Sessions Section */
    .sessions-section {
        margin-bottom: 2rem;
    }

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .section-header h2 {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.25rem;
    }

    .session-count {
        font-size: 0.875rem;
        color: var(--text-muted);
        background: var(--bg-secondary);
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
    }

    .sessions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
    }

    .session-card {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
    }

    .session-card:hover {
        transform: translateY(-2px);
        border-color: var(--primary);
    }

    .session-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .session-id {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
    }

    .session-id code {
        font-family: 'JetBrains Mono', monospace;
        background: var(--bg-secondary);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }

    .session-status.active {
        color: #22c55e;
        animation: pulse 2s infinite;
    }

    .session-metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    .session-metric {
        text-align: center;
    }

    .session-metric .label {
        display: block;
        font-size: 0.625rem;
        color: var(--text-muted);
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .session-metric .value {
        display: block;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .session-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .tool-success {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        color: #22c55e;
    }

    /* Tool Analytics */
    .analytics-section {
        margin-bottom: 2rem;
    }

    .tools-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1rem;
    }

    .tool-card {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--border-color);
    }

    .tool-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }

    .tool-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    .tool-stat {
        text-align: center;
    }

    .tool-stat .stat-label {
        display: block;
        font-size: 0.625rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .tool-stat .stat-value {
        display: block;
        font-size: 1rem;
        font-weight: 600;
    }

    .tool-stat .stat-value.positive { color: #22c55e; }
    .tool-stat .stat-value.negative { color: #ef4444; }

    .tool-progress {
        margin-top: 0.5rem;
    }

    .progress-bar {
        height: 6px;
        background: var(--bg-secondary);
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 0.25rem;
    }

    .progress-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }

    .progress-fill.success { background: #22c55e; }
    .progress-fill.warning { background: #fbbf24; }
    .progress-fill.error { background: #ef4444; }

    .progress-label {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    /* Loading & Empty States */
    .loading-state, .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--text-muted);
    }

    .loading-icon {
        width: 64px;
        height: 64px;
        margin-bottom: 1rem;
        animation: spin 1s linear infinite;
    }

    .empty-state svg {
        opacity: 0.5;
        margin-bottom: 1rem;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideDown {
        from { 
            opacity: 0;
            transform: translateY(-20px);
        }
        to { 
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes scaleIn {
        from { 
            opacity: 0;
            transform: scale(0.9);
        }
        to { 
            opacity: 1;
            transform: scale(1);
        }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
</style>
