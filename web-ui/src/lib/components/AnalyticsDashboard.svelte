<script lang="ts">
    import { onMount } from 'svelte';
    import { Activity, TrendingUp, DollarSign, Clock, Zap, Database, AlertCircle, CheckCircle2, BarChart3, PieChart } from "lucide-svelte";
    import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
    import { Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs";

    let analyticsData = $state<any>(null);
    let loading = $state(true);
    let error = $state("");
    let timeRange = $state("7"); // days

    interface ChartData {
        labels: string[];
        datasets: {
            label: string;
            data: number[];
            borderColor?: string;
            backgroundColor?: string;
            fill?: boolean;
        }[];
    }

    // Load analytics data
    async function loadAnalytics() {
        loading = true;
        error = "";

        try {
            const res = await fetch(`/api/analytics/dashboard?days=${timeRange}`);
            if (res.ok) {
                analyticsData = await res.json();
            } else {
                const err = await res.json();
                error = err.detail || "Failed to load analytics";
            }
        } catch (e) {
            error = "Connection error loading analytics";
        }

        loading = false;
    }

    // Load insights separately
    let insights = $state<any[]>([]);
    let insightsLoading = $state(false);

    async function loadInsights() {
        insightsLoading = true;
        try {
            const res = await fetch(`/api/analytics/insights?days=${timeRange}`);
            if (res.ok) {
                const data = await res.json();
                insights = data.insights || [];
            }
        } catch (e) {
            console.error("Failed to load insights:", e);
        }
        insightsLoading = false;
    }

    // Auto-load on mount and when timeRange changes
    $effect(() => {
        loadAnalytics();
        loadInsights();
    });

    // Formatting helpers
    function formatCurrency(value: number): string {
        if (value === undefined || value === null || isNaN(value)) return "$0.00";
        if (value === 0) return "$0.00";
        if (value < 0.01) return `$${value.toFixed(5)}`;
        return `$${value.toFixed(4)}`;
    }

    function formatNumber(value: number): string {
        if (value === undefined || value === null || isNaN(value)) return "0";
        return value.toLocaleString();
    }

    function formatPercent(value: number): string {
        if (value === undefined || value === null || isNaN(value)) return "0.0%";
        return `${value.toFixed(1)}%`;
    }

    function formatTokens(value: number): string {
        if (value === undefined || value === null || isNaN(value)) return "0";
        if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
        return value.toString();
    }

    function formatTime(value: number): string {
        if (value === undefined || value === null || isNaN(value)) return "0ms";
        if (value >= 1000) return `${(value / 1000).toFixed(1)}s`;
        return `${value.toFixed(0)}ms`;
    }

    // Generate simple line chart data (for manual SVG rendering)
    function generateLineChart(data: number[], labels: string[], color: string): string {
        if (!data || data.length === 0) return "";

        const width = 280;
        const height = 100;
        const max = Math.max(...data, 1);
        const min = Math.min(...data, 0);
        const range = max - min || 1;

        const points = data.map((val, idx) => {
            const x = (idx / (data.length - 1)) * width;
            const y = height - ((val - min) / range) * height;
            return `${x},${y}`;
        }).join(" ");

        return `
            <svg width="${width}" height="${height}" class="w-full h-full">
                <polyline points="${points}"
                    fill="none"
                    stroke="${color}"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    opacity="0.8"/>
                <polyline points="${points} ${width},${height} 0,${height}"
                    fill="${color}20"
                    stroke="none"/>
            </svg>
        `;
    }

    // Generate bar chart data
    function generateBarChart(data: number[], labels: string[], color: string): string {
        if (!data || data.length === 0) return "";

        const width = 280;
        const height = 100;
        const max = Math.max(...data, 1);
        const barWidth = width / data.length;
        const gap = 2;

        const bars = data.map((val, idx) => {
            const barHeight = (val / max) * height;
            const x = idx * barWidth + gap;
            const y = height - barHeight;
            return `<rect x="${x}" y="${y}" width="${barWidth - gap * 2}" height="${barHeight}" fill="${color}" opacity="0.8" rx="2"/>`;
        }).join("");

        return `<svg width="${width}" height="${height}" class="w-full h-full">${bars}</svg>`;
    }

    // Generate pie chart segments (simple SVG)
    function generatePieChart(data: number[], colors: string[]): string {
        if (!data || data.length === 0) return "";

        const total = data.reduce((a, b) => a + b, 0);
        if (total === 0) return "";

        const size = 80;
        const radius = size / 2;
        const center = radius;

        let currentAngle = -Math.PI / 2; // Start from top
        const segments = data.map((val, idx) => {
            const sliceAngle = (val / total) * 2 * Math.PI;
            const x1 = center + radius * Math.cos(currentAngle);
            const y1 = center + radius * Math.sin(currentAngle);
            const x2 = center + radius * Math.cos(currentAngle + sliceAngle);
            const y2 = center + radius * Math.sin(currentAngle + sliceAngle);
            const largeArc = sliceAngle > Math.PI ? 1 : 0;

            const path = `M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
            currentAngle += sliceAngle;

            return `<path d="${path}" fill="${colors[idx % colors.length]}" opacity="0.8"/>`;
        }).join("");

        return `<svg width="${size}" height="${size}" class="mx-auto">${segments}</svg>`;
    }

    // Download export
    async function downloadExport(format: 'csv' | 'json') {
        console.log(`🔥🔥🔥 downloadExport CALLED - format: ${format}, timeRange: ${timeRange}`);
        try {
            const res = await fetch(`/api/analytics/export?days=${timeRange}&format=${format}`);
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `analytics_export_${timeRange}days.${format}`;
                a.click();
                window.URL.revokeObjectURL(url);
                console.log(`✅ Export ${format} downloaded successfully`);
            } else {
                console.log(`❌ Export ${format} failed - status:`, res.status);
            }
        } catch (e) {
            console.error("🔥🔥🔥 Download failed:", e);
        }
    }

    // Test function for AnalyticsDashboard buttons
    function testAnalyticsButton() {
        console.log("🐛🐛🐛 Analytics TEST BUTTON - onclick works in AnalyticsDashboard!");
        alert("Analytics test button works! Check console.");
    }
</script>

<div class="space-y-6">
    <!-- 🧪 Analytics Test Button -->
    <div class="p-3 border-2 border-purple-500/50 bg-purple-500/10 rounded-lg">
        <p class="text-xs text-purple-200 mb-1">🧪 Analytics Test:</p>
        <button
            onclick={testAnalyticsButton}
            class="px-3 py-1 bg-purple-500 text-white font-bold rounded text-sm hover:bg-purple-400"
        >
            Test Analytics Button
        </button>
    </div>

    <!-- Controls -->
    <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-2">
            <span class="text-sm text-muted-foreground">Time Range:</span>
            <select
                class="px-3 py-1.5 rounded-lg border border-input bg-background text-sm"
                bind:value={timeRange}
            >
                <option value="1">Last 24h</option>
                <option value="7">Last 7 days</option>
                <option value="14">Last 14 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
            </select>
        </div>

        <div class="flex gap-2">
            <button
                onclick={() => downloadExport('csv')}
                class="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-accent transition-colors"
            >
                Export CSV
            </button>
            <button
                onclick={() => downloadExport('json')}
                class="px-3 py-1.5 text-sm rounded-lg border border-border hover:bg-accent transition-colors"
            >
                Export JSON
            </button>
        </div>
    </div>

    {#if loading}
        <div class="text-center py-8 text-muted-foreground">
            <div class="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-3"></div>
            Loading analytics...
        </div>
    {:else if error}
        <div class="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {error}
        </div>
    {:else if !analyticsData}
        <div class="text-center py-8 text-muted-foreground">
            No analytics data available. Enable usage tracking to see insights.
        </div>
    {:else}
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
                <CardHeader class="pb-2">
                    <CardTitle class="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Activity class="w-4 h-4" /> Requests
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="text-2xl font-bold">
                        {formatNumber(analyticsData.summary?.total_requests || 0)}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader class="pb-2">
                    <CardTitle class="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Zap class="w-4 h-4" /> Tokens
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="text-2xl font-bold">
                        {formatTokens(analyticsData.summary?.total_tokens || 0)}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader class="pb-2">
                    <CardTitle class="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <DollarSign class="w-4 h-4" /> Cost
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="text-2xl font-bold text-emerald-400">
                        {formatCurrency(analyticsData.summary?.total_cost || 0)}
                    </div>
                    <div class="text-xs text-emerald-500/80 mt-1">
                        Saved: {formatCurrency(analyticsData.summary?.total_savings || 0)}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader class="pb-2">
                    <CardTitle class="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Clock class="w-4 h-4" /> Latency
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div class="text-2xl font-bold">
                        {formatTime(analyticsData.summary?.avg_latency_ms || 0)}
                    </div>
                </CardContent>
            </Card>
        </div>

        <!-- Main Analytics Tabs -->
        <Tabs value="charts" class="w-full">
            <TabsList class="grid w-full grid-cols-4">
                <TabsTrigger value="charts">Charts</TabsTrigger>
                <TabsTrigger value="models">Models</TabsTrigger>
                <TabsTrigger value="savings">Savings</TabsTrigger>
                <TabsTrigger value="insights">Insights</TabsTrigger>
            </TabsList>

            <!-- Charts Tab -->
            <TabsContent value="charts" class="space-y-4 mt-4">
                <!-- Time Series Chart -->
                <Card>
                    <CardHeader>
                        <CardTitle>Time Series</CardTitle>
                        <CardDescription>Requests, tokens, and cost over time</CardDescription>
                    </CardHeader>
                    <CardContent class="space-y-4">
                        {#if analyticsData.time_series && analyticsData.time_series.dates.length > 0}
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="space-y-2">
                                    <div class="text-sm font-medium text-muted-foreground">Requests & Tokens</div>
                                    <div class="border border-border rounded-lg p-2 bg-background/50">
                                        {@html generateLineChart(
                                            analyticsData.time_series.requests,
                                            analyticsData.time_series.dates,
                                            'rgb(59, 130, 246)'
                                        )}
                                    </div>
                                    <div class="flex gap-3 text-xs text-muted-foreground justify-center">
                                        <span class="flex items-center gap-1"><span class="w-3 h-1 bg-blue-500 inline-block"></span> Requests</span>
                                        <span class="flex items-center gap-1"><span class="w-3 h-1 bg-purple-500 inline-block"></span> Tokens</span>
                                    </div>
                                </div>
                                <div class="space-y-2">
                                    <div class="text-sm font-medium text-muted-foreground">Cost</div>
                                    <div class="border border-border rounded-lg p-2 bg-background/50">
                                        {@html generateLineChart(
                                            analyticsData.time_series.cost,
                                            analyticsData.time_series.dates,
                                            'rgb(16, 185, 129)'
                                        )}
                                    </div>
                                    <div class="text-center text-xs text-muted-foreground">
                                        Total: {formatCurrency(analyticsData.summary?.total_cost || 0)}
                                    </div>
                                </div>
                            </div>

                            <!-- Token Breakdown Chart -->
                            {#if analyticsData.time_series?.token_breakdown}
                                <div class="space-y-2 mt-4">
                                    <div class="text-sm font-medium text-muted-foreground">Token Breakdown</div>
                                    <div class="grid grid-cols-3 gap-2 text-xs">
                                        <div class="text-center">
                                            <div class="h-20 border border-border rounded bg-blue-500/20 flex items-end justify-center pb-1">
                                                {analyticsData.time_series.token_breakdown.input?.reduce((a: number, b: number)=>(a||0)+(b||0),0) || 0}
                                            </div>
                                            <div class="mt-1">Input</div>
                                        </div>
                                        <div class="text-center">
                                            <div class="h-20 border border-border rounded bg-purple-500/20 flex items-end justify-center pb-1">
                                                {analyticsData.time_series.token_breakdown.output?.reduce((a: number, b: number)=>(a||0)+(b||0),0) || 0}
                                            </div>
                                            <div class="mt-1">Output</div>
                                        </div>
                                        <div class="text-center">
                                            <div class="h-20 border border-border rounded bg-orange-500/20 flex items-end justify-center pb-1">
                                                {analyticsData.time_series.token_breakdown.thinking?.reduce((a: number, b: number)=>(a||0)+(b||0),0) || 0}
                                            </div>
                                            <div class="mt-1">Thinking</div>
                                        </div>
                                    </div>
                                </div>
                            {/if}
                        {:else}
                            <div class="text-center py-4 text-muted-foreground text-sm">
                                No time series data available for this period
                            </div>
                        {/if}
                    </CardContent>
                </Card>

                <!-- Token Breakdown Analysis -->
                <Card>
                    <CardHeader>
                        <CardTitle>Token Composition</CardTitle>
                        <CardDescription>Detailed token type breakdown</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {#if analyticsData.token_breakdown && Object.keys(analyticsData.token_breakdown.breakdown || {}).length > 0}
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {#each ['prompt', 'completion', 'reasoning', 'cached', 'tool_use', 'audio'] as type}
                                    {#if analyticsData.token_breakdown.breakdown[type]?.absolute > 0}
                                        <div class="border border-border rounded-lg p-3">
                                            <div class="flex items-center justify-between mb-2">
                                                <span class="text-sm font-medium capitalize">{type.replace('_', ' ')}</span>
                                                <span class="text-sm font-bold">
                                                    {analyticsData.token_breakdown.breakdown[type]?.percentage || 0}%
                                                </span>
                                            </div>
                                            <div class="w-full bg-accent/30 rounded-full h-2">
                                                <div
                                                    class="h-2 rounded-full bg-primary transition-all"
                                                    style="width: {analyticsData.token_breakdown.breakdown[type]?.percentage || 0}%"
                                                ></div>
                                            </div>
                                            <div class="text-xs text-muted-foreground mt-1">
                                                {formatNumber(analyticsData.token_breakdown.breakdown[type]?.absolute)} tokens
                                            </div>
                                        </div>
                                    {/if}
                                {/each}
                            </div>
                        {:else}
                            <div class="text-center py-4 text-muted-foreground text-sm">
                                No token breakdown data available
                            </div>
                        {/if}
                    </CardContent>
                </Card>
            </TabsContent>

            <!-- Models Tab -->
            <TabsContent value="models" class="space-y-4 mt-4">
                <Card>
                    <CardHeader>
                        <CardTitle>Model Performance</CardTitle>
                        <CardDescription>Compare efficiency across models</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {#if analyticsData.models && analyticsData.models.length > 0}
                            <div class="overflow-x-auto">
                                <table class="w-full text-sm">
                                    <thead>
                                        <tr class="border-b border-border text-muted-foreground">
                                            <th class="text-left py-2 px-2">Model</th>
                                            <th class="text-right py-2 px-2">Requests</th>
                                            <th class="text-right py-2 px-2">Tokens/Req</th>
                                            <th class="text-right py-2 px-2">Cost/1K</th>
                                            <th class="text-right py-2 px-2">Latency</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {#each analyticsData.models.slice(0, 10) as model}
                                            <tr class="border-b border-border/50 hover:bg-accent/50">
                                                <td class="py-2 px-2 font-mono text-xs">
                                                    {model.model ? (model.model.split('/').pop() || model.model) : 'Unknown'}
                                                    <div class="text-[10px] text-muted-foreground">{model.provider || 'N/A'}</div>
                                                </td>
                                                <td class="py-2 px-2 text-right">{formatNumber(model.total_requests || 0)}</td>
                                                <td class="py-2 px-2 text-right">{formatNumber(model.avg_tokens_per_request || 0)}</td>
                                                <td class="py-2 px-2 text-right ${(model.avg_cost_per_1k_tokens || 0) > 5 ? 'text-amber-400' : 'text-emerald-400'}">
                                                    ${model.avg_cost_per_1k_tokens ? model.avg_cost_per_1k_tokens.toFixed(2) : '0.00'}
                                                </td>
                                                <td class="py-2 px-2 text-right">{formatTime(model.avg_duration_ms || 0)}</td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            </div>
                        {:else}
                            <div class="text-center py-4 text-muted-foreground text-sm">
                                No model comparison data available
                            </div>
                        {/if}
                    </CardContent>
                </Card>
            </TabsContent>

            <!-- Savings Tab -->
            <TabsContent value="savings" class="space-y-4 mt-4">
                <Card>
                    <CardHeader>
                        <CardTitle>Cost Optimization</CardTitle>
                        <CardDescription>Savings from smart model routing</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {#if analyticsData.savings && analyticsData.savings.length > 0}
                            <div class="space-y-3">
                                {#each analyticsData.savings as saving}
                                    <div class="border border-border rounded-lg p-4 flex items-center justify-between hover:bg-accent/50 transition-colors">
                                        <div class="flex-1">
                                            <div class="flex items-center gap-2 text-sm">
                                                <span class="font-mono">
                                                    {saving.original_model ? (saving.original_model.split('/').pop() || saving.original_model) : 'Unknown'}
                                                </span>
                                                <span class="text-muted-foreground">→</span>
                                                <span class="font-mono font-bold text-emerald-400">
                                                    {saving.routed_model ? (saving.routed_model.split('/').pop() || saving.routed_model) : 'Unknown'}
                                                </span>
                                            </div>
                                            <div class="text-xs text-muted-foreground mt-1">
                                                {formatNumber(saving.request_count)} requests
                                            </div>
                                        </div>
                                        <div class="text-right">
                                            <div class="text-emerald-400 font-bold">
                                                -{formatPercent(saving.avg_savings_percent)}
                                            </div>
                                            <div class="text-xs text-muted-foreground">
                                                {formatCurrency(saving.total_savings)} saved
                                            </div>
                                        </div>
                                    </div>
                                {/each}
                            </div>
                            <div class="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                                <div class="flex items-center gap-2 text-emerald-400 font-bold mb-1">
                                    <CheckCircle2 class="w-4 h-4" />
                                    Total Savings: {formatCurrency(analyticsData.summary?.total_savings || 0)}
                                </div>
                                <div class="text-xs text-emerald-500/80">
                                    Smart routing has saved you significant costs this period.
                                </div>
                            </div>
                        {:else}
                            <div class="text-center py-4 text-muted-foreground text-sm">
                                No savings data available. Routing is cost-optimized when original cost differs from actual cost.
                            </div>
                        {/if}
                    </CardContent>
                </Card>

                <!-- Provider Stats -->
                <Card>
                    <CardHeader>
                        <CardTitle>Provider Usage</CardTitle>
                        <CardDescription>Cost and performance by provider</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {#if analyticsData.providers && analyticsData.providers.length > 0}
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {#each analyticsData.providers as provider}
                                    <div class="border border-border rounded-lg p-3">
                                        <div class="flex items-center justify-between mb-2">
                                            <span class="font-medium">{provider.provider}</span>
                                            <span class="text-emerald-400 font-bold">{formatCurrency(provider.total_cost || 0)}</span>
                                        </div>
                                        <div class="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                                            <div>Reqs: {formatNumber(provider.total_requests || 0)}</div>
                                            <div>Tokens: {formatTokens(provider.total_tokens || 0)}</div>
                                            <div>Latency: {formatTime(provider.avg_duration_ms || 0)}</div>
                                            <div>Tools: {formatNumber(provider.tool_requests || 0)}</div>
                                        </div>
                                    </div>
                                {/each}
                            </div>
                        {:else}
                            <div class="text-center py-4 text-muted-foreground text-sm">
                                No provider data available
                            </div>
                        {/if}
                    </CardContent>
                </Card>
            </TabsContent>

            <!-- Insights Tab -->
            <TabsContent value="insights" class="space-y-4 mt-4">
                {#if insightsLoading}
                    <div class="text-center py-4 text-muted-foreground text-sm">
                        Generating insights...
                    </div>
                {:else if insights.length > 0}
                    <div class="space-y-3">
                        {#each insights as insight}
                            <div class="border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                                <div class="flex items-start gap-3">
                                    <div class="mt-1">
                                        {#if insight.type === 'cost_saving'}
                                            <DollarSign class="w-4 h-4 text-emerald-400" />
                                        {:else if insight.type === 'efficiency'}
                                            <Zap class="w-4 h-4 text-blue-400" />
                                        {:else if insight.type === 'performance'}
                                            <Clock class="w-4 h-4 text-amber-400" />
                                        {:else if insight.type === 'model_efficiency'}
                                            <BarChart3 class="w-4 h-4 text-purple-400" />
                                        {:else}
                                            <AlertCircle class="w-4 h-4 text-muted-foreground" />
                                        {/if}
                                    </div>
                                    <div class="flex-1">
                                        <div class="flex items-center gap-2 mb-1">
                                            <span class="font-medium">{insight.title}</span>
                                            <span class="text-[10px] px-1.5 py-0.5 rounded-full
                                                {insight.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                                                  insight.priority === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                                                  'bg-blue-500/20 text-blue-400'}">
                                                {insight.priority.toUpperCase()}
                                            </span>
                                        </div>
                                        <p class="text-sm text-muted-foreground">{insight.description}</p>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <div class="text-center py-8 text-muted-foreground">
                        <AlertCircle class="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p class="text-sm">No insights available for this period</p>
                    </div>
                {/if}
            </TabsContent>
        </Tabs>
    {/if}
</div>

<style>
    /* Note: .model-tier CSS classes are defined in app.css and used in +page.svelte */
</style>