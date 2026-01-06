<!-- QueryBuilder.svelte - Interactive query builder for advanced analytics -->
<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import { Plus, Trash2, Filter, Play, Save, Download, X } from "lucide-svelte";

  const dispatch = createEventDispatcher();

  // Available metrics
  const METRICS = [
    { value: "tokens", label: "Total Tokens", icon: "📝" },
    { value: "cost", label: "Cost ($)", icon: "💰" },
    { value: "requests", label: "Requests", icon: "📨" },
    { value: "latency", label: "Avg Latency (ms)", icon: "⏱️" },
  ];

  // Available providers (will be populated dynamically)
  let providers: string[] = $state([]);
  let models: Array<{ value: string; label: string; provider: string }> =
    $state([]);

  interface QueryFilter {
    field: string;
    operator: string;
    value: string;
  }

  interface Query {
    metrics: string[];
    filters: QueryFilter[];
    dateRange: { start: string; end: string };
    groupBy: string;
    aggregator: string;
  }

  // Props with default
  let {
    query = $bindable({
      metrics: ["tokens", "cost"],
      filters: [] as QueryFilter[],
      dateRange: { start: "", end: "" },
      groupBy: "day",
      aggregator: "sum",
    }),
  } = $props<{ query?: Query }>();

  let loading = $state(false);
  let results = $state<any>(null);
  let showPreview = $state(false);

  // Date presets
  const DATE_PRESETS = [
    { label: "Today", days: 1 },
    { label: "Last 7 Days", days: 7 },
    { label: "Last 30 Days", days: 30 },
    { label: "Last 90 Days", days: 90 },
  ];

  // Filter operators
  const OPERATORS = [
    { value: "equals", label: "=" },
    { value: "not_equals", label: "!=" },
    { value: "contains", label: "contains" },
    { value: "greater", label: ">" },
    { value: "less", label: "<" },
  ];

  // Load available providers and models
  onMount(async () => {
    try {
      // Fetch providers
      const providersRes = await fetch("/api/models/providers");
      if (providersRes.ok) {
        providers = await providersRes.json();
      }

      // Fetch models
      const modelsRes = await fetch("/api/models/list");
      if (modelsRes.ok) {
        const allModels = await modelsRes.json();
        models = allModels.map((m) => ({
          value: m.id,
          label: m.name,
          provider: m.provider,
        }));
      }
    } catch (error) {
      console.error("Error loading providers/models:", error);
    }

    // Initialize dates if not set
    if (!query.dateRange.start || !query.dateRange.end) {
      applyPreset(7);
    }
  });

  // Apply date preset
  function applyPreset(days) {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - days);

    query.dateRange.start = formatDate(start);
    query.dateRange.end = formatDate(end);
  }

  // Format date to YYYY-MM-DD
  function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  // Toggle metric selection
  function toggleMetric(metric) {
    const index = query.metrics.indexOf(metric);
    if (index > -1) {
      query.metrics.splice(index, 1);
    } else {
      query.metrics.push(metric);
    }
  }

  // Add filter
  function addFilter() {
    query.filters.push({
      field: "provider",
      operator: "equals",
      value: "",
    });
  }

  // Remove filter
  function removeFilter(index) {
    query.filters.splice(index, 1);
  }

  // Update filter
  function updateFilter(index, key, value) {
    query.filters[index][key] = value;
  }

  // Get filtered models based on provider
  function getFilteredModels(provider) {
    if (!provider) return models;
    return models.filter((m) => m.provider === provider);
  }

  // Execute query
  async function executeQuery() {
    loading = true;
    showPreview = true;

    try {
      // Build query parameters
      const params = new URLSearchParams();

      // Add metrics
      if (query.metrics.length > 0) {
        params.append("metrics", query.metrics.join(","));
      }

      // Add date range
      if (query.dateRange.start && query.dateRange.end) {
        params.append("start_date", query.dateRange.start);
        params.append("end_date", query.dateRange.end);
      }

      // Add group by
      params.append("group_by", query.groupBy);

      // Add filters
      query.filters.forEach((filter) => {
        if (filter.field && filter.value) {
          params.append(
            `filter_${filter.field}`,
            `${filter.operator}:${filter.value}`,
          );
        }
      });

      // Fetch results
      const response = await fetch(
        `/api/analytics/custom?${params.toString()}`,
      );
      if (response.ok) {
        results = await response.json();
        dispatch("results", results);
      } else {
        results = { error: "Query failed", details: await response.text() };
      }
    } catch (error) {
      results = { error: "Network error", details: error.message };
    } finally {
      loading = false;
    }
  }

  // Export results
  function exportCSV() {
    if (!results || !results.data) return;

    const headers = ["Date", ...query.metrics];
    const rows = results.data.map((row) => {
      return [row.date, ...query.metrics.map((m) => row[m] || 0)].join(",");
    });

    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `query_${Date.now()}.csv`;
    a.click();
  }

  // Save query
  async function saveQuery() {
    const name = prompt("Enter query name:");
    if (!name) return;

    try {
      const response = await fetch("/api/analytics/queries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          query: query,
          created_at: new Date().toISOString(),
        }),
      });

      if (response.ok) {
        alert("Query saved successfully!");
        dispatch("saved");
      }
    } catch (error) {
      alert("Failed to save query");
    }
  }

  // Reset query
  function resetQuery() {
    query = {
      metrics: ["tokens", "cost"],
      filters: [],
      dateRange: { start: "", end: "" },
      groupBy: "day",
      aggregator: "sum",
    };
    results = null;
    showPreview = false;
    applyPreset(7);
  }
</script>

<div class="query-builder">
  <!-- Header -->
  <div class="builder-header">
    <h2>Interactive Query Builder</h2>
    <div class="header-actions">
      <button class="btn btn-secondary" onclick={resetQuery}>
        <span class="icon"><X size={16} /></span>
        Reset
      </button>
      <button
        class="btn btn-secondary"
        onclick={saveQuery}
        disabled={query.metrics.length === 0}
      >
        <span class="icon"><Save size={16} /></span>
        Save
      </button>
      <button
        class="btn btn-primary"
        onclick={executeQuery}
        disabled={loading || query.metrics.length === 0}
      >
        <span class="icon"><Play size={16} /></span>
        {loading ? "Running..." : "Run Query"}
      </button>
    </div>
  </div>

  <!-- Metrics Selection -->
  <div class="section">
    <div class="section-header">
      <span class="icon">📊</span>
      <h3>Select Metrics</h3>
    </div>
    <div class="metrics-grid">
      {#each METRICS as metric}
        <button
          class="metric-card {query.metrics.includes(metric.value)
            ? 'active'
            : ''}"
          onclick={() => toggleMetric(metric.value)}
        >
          <span class="metric-icon">{metric.icon}</span>
          <span class="metric-label">{metric.label}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Date Range -->
  <div class="section">
    <div class="section-header">
      <span class="icon">📅</span>
      <h3>Date Range</h3>
    </div>
    <div class="date-controls">
      <div class="presets">
        {#each DATE_PRESETS as preset}
          <button
            class="preset-btn"
            onclick={() => applyPreset(preset.days)}
            class:active={false}
          >
            {preset.label}
          </button>
        {/each}
      </div>
      <div class="date-inputs">
        <div class="input-group">
          <label>Start</label>
          <input
            type="date"
            bind:value={query.dateRange.start}
            max={query.dateRange.end || new Date().toISOString().split("T")[0]}
          />
        </div>
        <div class="input-group">
          <label>End</label>
          <input
            type="date"
            bind:value={query.dateRange.end}
            max={new Date().toISOString().split("T")[0]}
          />
        </div>
      </div>
    </div>
  </div>

  <!-- Filters -->
  <div class="section">
    <div class="section-header">
      <span class="icon"><Filter size={16} /></span>
      <h3>Filters</h3>
      <button class="btn btn-small" onclick={addFilter}>
        <Plus size={14} /> Add Filter
      </button>
    </div>

    {#if query.filters.length === 0}
      <div class="empty-state">No filters applied</div>
    {:else}
      <div class="filters-list">
        {#each query.filters as filter, index}
          <div class="filter-item">
            <select
              class="filter-field"
              bind:value={filter.field}
              onchange={(e) => updateFilter(index, "field", e.target.value)}
            >
              <option value="provider">Provider</option>
              <option value="model">Model</option>
              <option value="cost">Cost</option>
              <option value="tokens">Tokens</option>
            </select>

            <select
              class="filter-operator"
              bind:value={filter.operator}
              onchange={(e) => updateFilter(index, "operator", e.target.value)}
            >
              {#each OPERATORS as op}
                <option value={op.value}>{op.label}</option>
              {/each}
            </select>

            {#if filter.field === "provider"}
              <select
                class="filter-value"
                bind:value={filter.value}
                onchange={(e) => updateFilter(index, "value", e.target.value)}
              >
                <option value="">Select provider...</option>
                {#each providers as provider}
                  <option value={provider}>{provider}</option>
                {/each}
              </select>
            {:else if filter.field === "model"}
              <select
                class="filter-value"
                bind:value={filter.value}
                onchange={(e) => updateFilter(index, "value", e.target.value)}
              >
                <option value="">Select model...</option>
                {#each getFilteredModels(query.filters.find((f) => f.field === "provider")?.value) as model}
                  <option value={model.value}>{model.label}</option>
                {/each}
              </select>
            {:else}
              <input
                type="text"
                class="filter-value"
                placeholder="Value"
                bind:value={filter.value}
                oninput={(e) => updateFilter(index, "value", e.target.value)}
              />
            {/if}

            <button class="btn btn-danger" onclick={() => removeFilter(index)}>
              <Trash2 size={14} />
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Aggregation Settings -->
  <div class="section">
    <div class="section-header">
      <span class="icon">⚙️</span>
      <h3>Aggregation</h3>
    </div>
    <div class="agg-controls">
      <div class="input-group">
        <label>Group By</label>
        <select bind:value={query.groupBy}>
          <option value="hour">Hour</option>
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
        </select>
      </div>
      <div class="input-group">
        <label>Aggregator</label>
        <select bind:value={query.aggregator}>
          <option value="sum">Sum</option>
          <option value="avg">Average</option>
          <option value="max">Max</option>
          <option value="min">Min</option>
          <option value="count">Count</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Results Preview -->
  {#if showPreview}
    <div class="results-section">
      <div class="results-header">
        <h3>Results Preview</h3>
        {#if results && results.data}
          <div class="result-actions">
            <button class="btn btn-secondary" onclick={exportCSV}>
              <Download size={14} /> Export CSV
            </button>
          </div>
        {/if}
      </div>

      {#if loading}
        <div class="loading-state">Loading results...</div>
      {:else if results}
        {#if results.error}
          <div class="error-state">
            <strong>Error:</strong>
            {results.error}
            {#if results.details}<br />{results.details}{/if}
          </div>
        {:else if results.data && results.data.length > 0}
          <div class="results-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  {#each query.metrics as metric}
                    <th
                      >{METRICS.find((m) => m.value === metric)?.label ||
                        metric}</th
                    >
                  {/each}
                </tr>
              </thead>
              <tbody>
                {#each results.data as row}
                  <tr>
                    <td>{row.date || row.timestamp}</td>
                    {#each query.metrics as metric}
                      <td>{row[metric]?.toFixed(2) || "0.00"}</td>
                    {/each}
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else}
          <div class="empty-state">No data found for the selected criteria</div>
        {/if}
      {:else}
        <div class="empty-state">Run the query to see results</div>
      {/if}
    </div>
  {/if}

  <!-- Query Summary -->
  <div class="summary">
    <strong>Summary:</strong>
    <span>
      {query.metrics.length} metrics |
      {query.filters.length} filters | Group by: {query.groupBy} | Range: {query
        .dateRange.start} to {query.dateRange.end}
    </span>
  </div>
</div>

<style>
  .query-builder {
    background: var(--bg-card, #ffffff);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--border-color, #e5e7eb);
    max-width: 1000px;
    margin: 0 auto;
  }

  .builder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--border-color, #e5e7eb);
  }

  .builder-header h2 {
    margin: 0;
    color: var(--text-primary, #1f2937);
    font-size: 1.5rem;
    font-weight: 700;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
  }

  .section {
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: var(--bg-secondary, #f9fafb);
    border-radius: 8px;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .section-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary, #374151);
  }

  .section-header .icon {
    font-size: 1.2rem;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.75rem;
  }

  .metric-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 1rem;
    background: white;
    border: 2px solid var(--border-color, #e5e7eb);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .metric-card:hover {
    border-color: var(--primary, #3b82f6);
    transform: translateY(-2px);
  }

  .metric-card.active {
    background: var(--primary, #3b82f6);
    color: white;
    border-color: var(--primary, #3b82f6);
  }

  .metric-icon {
    font-size: 1.5rem;
  }

  .metric-label {
    font-size: 0.875rem;
    font-weight: 500;
    text-align: center;
  }

  .date-controls {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .presets {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .preset-btn {
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
  }

  .preset-btn:hover {
    border-color: var(--primary, #3b82f6);
    background: var(--bg-primary, #f0f9ff);
  }

  .date-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .input-group label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary, #6b7280);
  }

  .input-group input,
  .input-group select {
    padding: 0.5rem;
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 6px;
    font-size: 0.875rem;
    background: white;
  }

  .input-group input:focus,
  .input-group select:focus {
    outline: none;
    border-color: var(--primary, #3b82f6);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .filters-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .filter-item {
    display: grid;
    grid-template-columns: 1fr 100px 1fr auto;
    gap: 0.5rem;
    align-items: center;
    background: white;
    padding: 0.5rem;
    border-radius: 6px;
    border: 1px solid var(--border-color, #e5e7eb);
  }

  .filter-field,
  .filter-operator,
  .filter-value {
    padding: 0.5rem;
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .agg-controls {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .results-section {
    margin-top: 1.5rem;
    padding: 1rem;
    background: white;
    border-radius: 8px;
    border: 1px solid var(--border-color, #e5e7eb);
  }

  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color, #e5e7eb);
  }

  .results-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .result-actions {
    display: flex;
    gap: 0.5rem;
  }

  .results-table {
    overflow-x: auto;
  }

  .results-table table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  .results-table th,
  .results-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color, #e5e7eb);
  }

  .results-table th {
    background: var(--bg-secondary, #f9fafb);
    font-weight: 600;
    color: var(--text-primary, #374151);
  }

  .results-table tr:hover {
    background: var(--bg-secondary, #f9fafb);
  }

  .empty-state,
  .loading-state,
  .error-state {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary, #6b7280);
    border-radius: 6px;
    background: var(--bg-secondary, #f9fafb);
  }

  .error-state {
    color: #dc2626;
    background: #fef2f2;
    border: 1px solid #fecaca;
  }

  .summary {
    margin-top: 1.5rem;
    padding: 1rem;
    background: var(--bg-primary, #eff6ff);
    border-radius: 8px;
    font-size: 0.875rem;
    border-left: 4px solid var(--primary, #3b82f6);
  }

  .summary strong {
    color: var(--primary, #3b82f6);
    margin-right: 0.5rem;
  }

  /* Button styles */
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

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: var(--primary, #3b82f6);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #2563eb;
  }

  .btn-secondary {
    background: white;
    color: var(--text-primary, #374151);
    border: 1px solid var(--border-color, #e5e7eb);
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--bg-secondary, #f9fafb);
    border-color: var(--border-hover, #9ca3af);
  }

  .btn-danger {
    background: #ef4444;
    color: white;
    border: none;
    padding: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn-danger:hover {
    background: #dc2626;
  }

  .btn-small {
    padding: 0.35rem 0.75rem;
    font-size: 0.8rem;
    margin-left: auto;
  }

  .icon {
    display: flex;
    align-items: center;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .builder-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .header-actions {
      width: 100%;
      justify-content: stretch;
    }

    .header-actions .btn {
      flex: 1;
    }

    .metrics-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .date-inputs,
    .agg-controls {
      grid-template-columns: 1fr;
    }

    .filter-item {
      grid-template-columns: 1fr;
      gap: 0.25rem;
    }

    .filter-item .btn-danger {
      width: 100%;
    }
  }

  /* Custom scrollbar for results table */
  .results-table::-webkit-scrollbar {
    height: 8px;
  }

  .results-table::-webkit-scrollbar-track {
    background: var(--bg-secondary, #f3f4f6);
    border-radius: 4px;
  }

  .results-table::-webkit-scrollbar-thumb {
    background: var(--border-color, #d1d5db);
    border-radius: 4px;
  }

  .results-table::-webkit-scrollbar-thumb:hover {
    background: var(--border-hover, #9ca3af);
  }
</style>
