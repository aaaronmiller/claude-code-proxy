<!-- Custom Dashboard Builder - Phase 4 -->
<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import {
        LayoutDashboard,
        Plus,
        Trash2,
        Settings,
        Save,
        Edit,
        Grid,
        X,
        Check,
        BarChart3,
        LineChart,
        Activity,
        AlertCircle,
        TrendingUp,
        DollarSign,
    } from "lucide-svelte";

    // Dashboard state
    let dashboardName = $state("My Dashboard");
    let widgets = $state<Widget[]>([]);
    let availableMetrics = $state<WidgetMetric[]>([]);
    let selectedWidget = $state<Widget | null>(null);
    let isEditing = $state(false);
    let showWidgetMenu = $state(false);

    interface WidgetMetric {
        id: string;
        name: string;
        type: "chart" | "stat" | "table";
        icon: any;
        description: string;
    }

    interface WidgetData {
        date: string;
        value: number;
    }

    interface Widget {
        id: string;
        metric: string;
        type: "chart" | "stat" | "table";
        title: string;
        config: {
            metric: string;
            period: string;
            visualization: string;
            color: string;
            aggregate: string;
        };
        position: {
            x: number;
            y: number;
            w: number;
            h: number;
        };
        data?: WidgetData[];
    }

    // Available metrics and visualizations
    const METRICS: WidgetMetric[] = [
        {
            id: "tokens",
            name: "Total Tokens",
            type: "chart",
            icon: BarChart3,
            description: "Token usage over time",
        },
        {
            id: "cost",
            name: "Cost ($)",
            type: "chart",
            icon: DollarSign,
            description: "Cost breakdown",
        },
        {
            id: "requests",
            name: "Requests",
            type: "stat",
            icon: Activity,
            description: "Request count",
        },
        {
            id: "latency",
            name: "Latency",
            type: "chart",
            icon: LineChart,
            description: "Response times",
        },
        {
            id: "error_rate",
            name: "Error Rate",
            type: "stat",
            icon: AlertCircle,
            description: "Error percentage",
        },
        {
            id: "efficiency",
            name: "Efficiency",
            type: "stat",
            icon: TrendingUp,
            description: "Tokens per dollar",
        },
    ];

    const VISUALIZATIONS = [
        { id: "line", name: "Line Chart" },
        { id: "bar", name: "Bar Chart" },
        { id: "area", name: "Area Chart" },
        { id: "metric", name: "Big Number" },
        { id: "table", name: "Table" },
    ];

    const PERIODS = [
        { id: "24h", name: "Last 24 Hours" },
        { id: "7d", name: "Last 7 Days" },
        { id: "30d", name: "Last 30 Days" },
        { id: "90d", name: "Last 90 Days" },
    ];

    // Initialize
    onMount(() => {
        loadSavedDashboards();
        availableMetrics = METRICS;
    });

    // Add widget
    function addWidget(metric: WidgetMetric) {
        const newWidget: Widget = {
            id: `widget_${Date.now()}`,
            metric: metric.id,
            type: metric.type,
            title: metric.name,
            config: {
                metric: metric.id,
                period: "7d",
                visualization: metric.type === "chart" ? "line" : "metric",
                color: "#3b82f6",
                aggregate: "sum",
            },
            position: {
                x: (widgets.length % 3) * 4,
                y: Math.floor(widgets.length / 3) * 3,
                w: 4,
                h: metric.type === "chart" ? 3 : 2,
            },
        };

        widgets = [...widgets, newWidget];
        isEditing = true;
    }

    // Remove widget
    function removeWidget(id: string) {
        widgets = widgets.filter((w) => w.id !== id);
        if (selectedWidget?.id === id) {
            selectedWidget = null;
        }
    }

    // Select widget for editing
    function selectWidget(widget: Widget) {
        selectedWidget = widget;
        showWidgetMenu = true;
    }

    // Update widget configuration
    function updateWidgetConfig(key: string, value: any) {
        if (!selectedWidget) return;

        selectedWidget = {
            ...selectedWidget,
            config: {
                ...selectedWidget.config,
                [key]: value,
            },
        };

        // Update in array
        const currentWidget = selectedWidget;
        widgets = widgets.map((w) =>
            w.id === currentWidget.id ? currentWidget : w,
        );
    }

    // Update widget title
    function updateWidgetTitle(title: string) {
        if (!selectedWidget) return;
        selectedWidget.title = title;
        const currentWidget = selectedWidget;
        widgets = widgets.map((w) =>
            w.id === currentWidget.id ? currentWidget : w,
        );
    }

    // Save dashboard
    async function saveDashboard() {
        const dashboard = {
            id: `dashboard_${Date.now()}`,
            name: dashboardName,
            widgets: widgets,
            created_at: new Date().toISOString(),
        };

        try {
            const response = await fetch("/api/dashboards", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dashboard),
            });

            if (response.ok) {
                isEditing = false;
                alert("Dashboard saved successfully!");
            } else {
                alert("Failed to save dashboard");
            }
        } catch (error) {
            console.error("Save error:", error);
            alert("Error saving dashboard");
        }
    }

    // Load saved dashboards
    async function loadSavedDashboards() {
        try {
            const response = await fetch("/api/dashboards");
            if (response.ok) {
                const dashboards = await response.json();
                // Could load one here
            }
        } catch (error) {
            console.error("Load error:", error);
        }
    }

    // Preview dashboard
    async function previewDashboard() {
        // Generate preview data for each widget
        for (const widget of widgets) {
            widget.data = await generateWidgetData(widget);
        }
        isEditing = false;
    }

    // Generate mock data for preview
    async function generateWidgetData(widget: Widget) {
        // In production, this would call actual API
        const data = [];
        const points =
            widget.config.period === "24h"
                ? 24
                : widget.config.period === "7d"
                  ? 7
                  : 30;

        for (let i = 0; i < points; i++) {
            data.push({
                date: new Date(Date.now() - (points - i) * 24 * 60 * 60 * 1000)
                    .toISOString()
                    .split("T")[0],
                value:
                    Math.random() * 1000 * (widget.metric === "cost" ? 0.1 : 1),
            });
        }

        return data;
    }

    // Import dashboard
    async function importDashboard() {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".json";
        input.onchange = async (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) {
                const text = await file.text();
                const imported = JSON.parse(text);
                dashboardName = imported.name;
                widgets = imported.widgets;
                isEditing = true;
            }
        };
        input.click();
    }

    // Export dashboard
    function exportDashboard() {
        const data = {
            name: dashboardName,
            widgets: widgets,
            version: "1.0",
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${dashboardName.replace(/\s+/g, "_")}.json`;
        a.click();
    }

    // Reset
    function reset() {
        if (confirm("Clear all widgets?")) {
            widgets = [];
            selectedWidget = null;
            isEditing = true;
        }
    }

    // Get widget visualization component (simplified for demo)
    function getWidgetComponent(type: string) {
        // In real implementation, this would return actual chart components
        return type === "chart" ? "LineChart" : "StatCard";
    }
</script>

<div class="dashboard-builder">
    <!-- Header -->
    <div class="header">
        <div class="title">
            <LayoutDashboard size={24} />
            <input
                type="text"
                bind:value={dashboardName}
                class="title-input"
                placeholder="Dashboard Name"
                readonly={!isEditing}
            />
        </div>

        <div class="actions">
            {#if isEditing}
                <button class="btn btn-secondary" onclick={importDashboard}>
                    <span class="icon">📂</span> Import
                </button>
                <button class="btn btn-secondary" onclick={reset}>
                    <span class="icon">↺</span> Reset
                </button>
                <button class="btn btn-primary" onclick={previewDashboard}>
                    <span class="icon"><Grid size={16} /></span> Preview
                </button>
                <button class="btn btn-success" onclick={saveDashboard}>
                    <span class="icon"><Save size={16} /></span> Save
                </button>
            {:else}
                <button
                    class="btn btn-secondary"
                    onclick={() => (isEditing = true)}
                >
                    <span class="icon"><Edit size={16} /></span> Edit
                </button>
                <button class="btn btn-primary" onclick={exportDashboard}>
                    <span class="icon">💾</span> Export
                </button>
            {/if}
        </div>
    </div>

    <div class="content">
        {#if isEditing}
            <!-- Widget Selection Sidebar -->
            <div class="widget-library">
                <h3>Add Widgets</h3>
                <div class="metrics-grid">
                    {#each METRICS as metric}
                        <button
                            class="metric-card"
                            onclick={() => addWidget(metric)}
                        >
                            <span class="metric-icon">
                                <svelte:component
                                    this={metric.icon}
                                    size={20}
                                />
                            </span>
                            <span class="metric-name">{metric.name}</span>
                            <span class="metric-desc">{metric.description}</span
                            >
                        </button>
                    {/each}
                </div>

                <!-- Selected Widget Settings -->
                {#if selectedWidget && showWidgetMenu}
                    <div class="widget-settings">
                        <div class="settings-header">
                            <h4>Widget Settings</h4>
                            <button
                                class="close-btn"
                                onclick={() => {
                                    selectedWidget = null;
                                    showWidgetMenu = false;
                                }}
                            >
                                <X size={16} />
                            </button>
                        </div>

                        <div class="setting-group">
                            <label>Title</label>
                            <input
                                type="text"
                                value={selectedWidget.title}
                                oninput={(e) =>
                                    updateWidgetTitle(
                                        (e.target as HTMLInputElement).value,
                                    )}
                            />
                        </div>

                        <div class="setting-group">
                            <label>Period</label>
                            <select
                                value={selectedWidget.config.period}
                                onchange={(e) =>
                                    updateWidgetConfig(
                                        "period",
                                        (e.target as HTMLSelectElement).value,
                                    )}
                            >
                                {#each PERIODS as period}
                                    <option value={period.id}
                                        >{period.name}</option
                                    >
                                {/each}
                            </select>
                        </div>

                        {#if selectedWidget.type === "chart"}
                            <div class="setting-group">
                                <label>Visualization</label>
                                <select
                                    value={selectedWidget.config.visualization}
                                    onchange={(e) =>
                                        updateWidgetConfig(
                                            "visualization",
                                            (e.target as HTMLSelectElement)
                                                .value,
                                        )}
                                >
                                    {#each VISUALIZATIONS.filter((v) => v.id !== "table" && v.id !== "metric") as viz}
                                        <option value={viz.id}
                                            >{viz.name}</option
                                        >
                                    {/each}
                                </select>
                            </div>

                            <div class="setting-group">
                                <label>Color</label>
                                <input
                                    type="color"
                                    value={selectedWidget.config.color}
                                    onchange={(e) =>
                                        updateWidgetConfig(
                                            "color",
                                            (e.target as HTMLInputElement)
                                                .value,
                                        )}
                                />
                            </div>
                        {/if}

                        <div class="setting-group">
                            <label>Aggregate</label>
                            <select
                                value={selectedWidget.config.aggregate}
                                onchange={(e) =>
                                    updateWidgetConfig(
                                        "aggregate",
                                        (e.target as HTMLSelectElement).value,
                                    )}
                            >
                                <option value="sum">Sum</option>
                                <option value="avg">Average</option>
                                <option value="max">Max</option>
                                <option value="min">Min</option>
                            </select>
                        </div>

                        <button
                            class="btn btn-danger"
                            style="width: 100%; margin-top: 1rem;"
                            onclick={() =>
                                selectedWidget &&
                                removeWidget(selectedWidget.id)}
                        >
                            <Trash2 size={14} /> Remove Widget
                        </button>
                    </div>
                {/if}
            </div>

            <!-- Canvas -->
            <div class="canvas">
                {#if widgets.length === 0}
                    <div class="empty-state">
                        <h3>No widgets yet</h3>
                        <p>Click on metrics to add widgets to your dashboard</p>
                    </div>
                {:else}
                    <div class="widget-grid">
                        {#each widgets as widget (widget.id)}
                            <div
                                class="widget-preview {selectedWidget?.id ===
                                widget.id
                                    ? 'selected'
                                    : ''}"
                                onclick={() => selectWidget(widget)}
                                style="border-color: {widget.config.color};"
                            >
                                <div class="widget-header">
                                    <span class="widget-icon">
                                        {#if widget.metric === "tokens"}📝{/if}
                                        {#if widget.metric === "cost"}💰{/if}
                                        {#if widget.metric === "requests"}📨{/if}
                                        {#if widget.metric === "latency"}⏱️{/if}
                                        {#if widget.metric === "error_rate"}⚠️{/if}
                                        {#if widget.metric === "efficiency"}📈{/if}
                                    </span>
                                    <span class="widget-title"
                                        >{widget.title}</span
                                    >
                                    <span class="widget-type"
                                        >{widget.config.visualization}</span
                                    >
                                </div>
                                <div class="widget-preview-body">
                                    {#if widget.type === "chart"}
                                        <div
                                            class="chart-placeholder"
                                            style="background-color: {widget
                                                .config.color}20;"
                                        >
                                            <LineChart
                                                size={32}
                                                opacity={0.5}
                                            />
                                        </div>
                                    {:else}
                                        <div
                                            class="stat-placeholder"
                                            style="background-color: {widget
                                                .config.color}20;"
                                        >
                                            <span
                                                style="font-size: 1.5rem; font-weight: 700; color: {widget
                                                    .config.color};">1,234</span
                                            >
                                            <span
                                                style="font-size: 0.875rem; color: #6b7280;"
                                                >{widget.metric}</span
                                            >
                                        </div>
                                    {/if}
                                </div>
                                <div class="widget-footer">
                                    <span class="period-badge"
                                        >{widget.config.period}</span
                                    >
                                    <span class="aggregate-badge"
                                        >{widget.config.aggregate}</span
                                    >
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        {:else}
            <!-- Preview Mode -->
            <div class="preview-mode">
                {#if widgets.length === 0}
                    <div class="empty-state">
                        <h3>Empty Dashboard</h3>
                        <p>Switch to edit mode to add widgets</p>
                    </div>
                {:else}
                    <div class="dashboard-grid">
                        {#each widgets as widget (widget.id)}
                            <div
                                class="dashboard-widget"
                                style="border-top: 3px solid {widget.config
                                    .color};"
                            >
                                <div class="dashboard-widget-header">
                                    <h4>{widget.title}</h4>
                                    <span class="period"
                                        >{widget.config.period}</span
                                    >
                                </div>
                                <div class="dashboard-widget-body">
                                    <!-- Widget content would be rendered here with real data -->
                                    <div class="preview-content">
                                        <p
                                            style="color: #6b7280; font-style: italic;"
                                        >
                                            Preview: {widget.config
                                                .visualization} of {widget.metric}
                                        </p>
                                        <div class="mock-data">
                                            {#if widget.data}
                                                {#each widget.data.slice(-5) as point}
                                                    <div class="data-point">
                                                        <span class="date"
                                                            >{point.date}</span
                                                        >
                                                        <span
                                                            class="value"
                                                            style="color: {widget
                                                                .config.color};"
                                                        >
                                                            {widget.metric ===
                                                            "cost"
                                                                ? "$"
                                                                : ""}{point.value.toFixed(
                                                                2,
                                                            )}
                                                        </span>
                                                    </div>
                                                {/each}
                                            {/if}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        {/if}
    </div>
</div>

<style>
    .dashboard-builder {
        display: flex;
        flex-direction: column;
        height: 100vh;
        background: var(--bg-primary, #f9fafb);
    }

    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background: white;
        border-bottom: 1px solid var(--border-color, #e5e7eb);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .title-input {
        font-size: 1.5rem;
        font-weight: 700;
        border: none;
        background: transparent;
        padding: 0.5rem;
        border-radius: 6px;
        color: var(--text-primary, #1f2937);
        min-width: 200px;
    }

    .title-input:focus {
        outline: 2px solid var(--primary, #3b82f6);
        background: white;
    }

    .actions {
        display: flex;
        gap: 0.5rem;
    }

    .btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        border: none;
        transition: all 0.2s;
        white-space: nowrap;
    }

    .btn-primary {
        background: var(--primary, #3b82f6);
        color: white;
    }

    .btn-primary:hover {
        background: #2563eb;
    }

    .btn-secondary {
        background: white;
        color: var(--text-primary, #374151);
        border: 1px solid var(--border-color, #e5e7eb);
    }

    .btn-secondary:hover {
        background: var(--bg-secondary, #f9fafb);
    }

    .btn-success {
        background: #10b981;
        color: white;
    }

    .btn-success:hover {
        background: #059669;
    }

    .btn-danger {
        background: #ef4444;
        color: white;
    }

    .btn-danger:hover {
        background: #dc2626;
    }

    .icon {
        display: flex;
        align-items: center;
    }

    .content {
        flex: 1;
        display: flex;
        overflow: hidden;
    }

    /* Widget Library (Sidebar) */
    .widget-library {
        width: 320px;
        background: white;
        border-right: 1px solid var(--border-color, #e5e7eb);
        overflow-y: auto;
        padding: 1.5rem;
    }

    .widget-library h3 {
        margin: 0 0 1rem 0;
        color: var(--text-primary, #1f2937);
    }

    .metrics-grid {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 1rem;
        background: var(--bg-secondary, #f9fafb);
        border: 1px solid var(--border-color, #e5e7eb);
        border-radius: 8px;
        cursor: pointer;
        text-align: left;
        transition: all 0.2s;
    }

    .metric-card:hover {
        background: var(--bg-primary, #eff6ff);
        border-color: var(--primary, #3b82f6);
        transform: translateY(-2px);
    }

    .metric-icon {
        color: var(--primary, #3b82f6);
        margin-bottom: 0.25rem;
    }

    .metric-name {
        font-weight: 600;
        font-size: 0.9rem;
    }

    .metric-desc {
        font-size: 0.75rem;
        color: var(--text-secondary, #6b7280);
    }

    /* Widget Settings */
    .widget-settings {
        background: var(--bg-secondary, #f9fafb);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid var(--border-color, #e5e7eb);
    }

    .settings-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color, #e5e7eb);
    }

    .settings-header h4 {
        margin: 0;
        font-size: 1rem;
    }

    .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--text-secondary, #6b7280);
        padding: 0.25rem;
        border-radius: 4px;
    }

    .close-btn:hover {
        background: rgba(0, 0, 0, 0.05);
        color: var(--text-primary, #1f2937);
    }

    .setting-group {
        margin-bottom: 0.75rem;
    }

    .setting-group label {
        display: block;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .setting-group input,
    .setting-group select {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid var(--border-color, #e5e7eb);
        border-radius: 6px;
        font-size: 0.875rem;
        background: white;
    }

    .setting-group input:focus,
    .setting-group select:focus {
        outline: none;
        border-color: var(--primary, #3b82f6);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* Canvas */
    .canvas {
        flex: 1;
        padding: 2rem;
        overflow-y: auto;
        background: var(--bg-primary, #f9fafb);
    }

    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--text-secondary, #6b7280);
        text-align: center;
    }

    .empty-state h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.5rem;
        color: var(--text-primary, #1f2937);
    }

    .widget-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
    }

    .widget-preview {
        background: white;
        border: 2px solid var(--border-color, #e5e7eb);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        overflow: hidden;
    }

    .widget-preview:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .widget-preview.selected {
        border-width: 2px;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
    }

    .widget-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem;
        background: var(--bg-secondary, #f9fafb);
        border-bottom: 1px solid var(--border-color, #e5e7eb);
    }

    .widget-icon {
        font-size: 1.2rem;
    }

    .widget-title {
        flex: 1;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .widget-type {
        font-size: 0.75rem;
        color: var(--text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .widget-preview-body {
        padding: 1rem;
        min-height: 100px;
    }

    .chart-placeholder,
    .stat-placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100px;
        border-radius: 6px;
        gap: 0.5rem;
        flex-direction: column;
    }

    .widget-footer {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0.75rem;
        background: var(--bg-secondary, #f9fafb);
        border-top: 1px solid var(--border-color, #e5e7eb);
        font-size: 0.75rem;
    }

    .period-badge,
    .aggregate-badge {
        padding: 0.25rem 0.5rem;
        background: white;
        border-radius: 4px;
        border: 1px solid var(--border-color, #e5e7eb);
    }

    /* Preview Mode */
    .preview-mode {
        flex: 1;
        padding: 2rem;
        overflow-y: auto;
    }

    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        gap: 1.5rem;
    }

    .dashboard-widget {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid var(--border-color, #e5e7eb);
    }

    .dashboard-widget-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color, #e5e7eb);
    }

    .dashboard-widget-header h4 {
        margin: 0;
        font-size: 1rem;
    }

    .period {
        font-size: 0.75rem;
        color: var(--text-secondary, #6b7280);
        background: var(--bg-secondary, #f9fafb);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }

    .dashboard-widget-body {
        min-height: 120px;
    }

    .mock-data {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .data-point {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem;
        background: var(--bg-secondary, #f9fafb);
        border-radius: 4px;
        font-size: 0.875rem;
    }

    .date {
        color: var(--text-secondary, #6b7280);
    }

    .value {
        font-weight: 600;
    }

    /* Responsive */
    @media (max-width: 1024px) {
        .widget-library {
            width: 280px;
        }

        .header {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }

        .actions {
            width: 100%;
            flex-wrap: wrap;
        }
    }

    @media (max-width: 768px) {
        .widget-library {
            display: none;
        }

        .content {
            flex-direction: column;
        }

        .widget-grid,
        .dashboard-grid {
            grid-template-columns: 1fr;
        }

        .header {
            padding: 1rem;
        }

        .canvas,
        .preview-mode {
            padding: 1rem;
        }
    }
</style>
