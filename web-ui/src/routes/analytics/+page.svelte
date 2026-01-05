<!--
  Analytics Dashboard - Phase 2
  Interactive metrics visualization and data exploration
-->
<script>
  import { onMount } from 'svelte';
  import { LineChart, BarChart, TimeRangePicker } from '../../components/charts/index.js';

  // State
  let metrics = {
    tokens: { labels: [], datasets: [] },
    cost: { labels: [], datasets: [] },
    requests: { labels: [], datasets: [] }
  };

  let aggregate = null;
  let providerComparison = null;
  let modelComparison = null;

  let dateRange = {
    start: '',
    end: ''
  };

  let loading = false;
  let activeTab = 'timeseries';

  // API Functions
  async function fetchTimeSeriesData(start, end) {
    loading = true;
    try {
      // Fetch tokens
      const tokenRes = await fetch(`/api/analytics/timeseries?metric=tokens&start_date=${start}&end_date=${end}&group_by=day`);
      const tokenData = await tokenRes.json();

      // Fetch cost
      const costRes = await fetch(`/api/analytics/timeseries?metric=cost&start_date=${start}&end_date=${end}&group_by=day`);
      const costData = await costRes.json();

      // Fetch requests
      const requestRes = await fetch(`/api/analytics/timeseries?metric=requests&start_date=${start}&end_date=${end}&group_by=day`);
      const requestData = await requestRes.json();

      metrics.tokens = tokenData;
      metrics.cost = costData;
      metrics.requests = requestData;

    } catch (error) {
      console.error('Error fetching time series:', error);
    } finally {
      loading = false;
    }
  }

  async function fetchAggregateData(start, end) {
    try {
      const res = await fetch(`/api/analytics/aggregate?start_date=${start}&end_date=${end}`);
      aggregate = await res.json();
    } catch (error) {
      console.error('Error fetching aggregate:', error);
    }
  }

  async function fetchProviderComparison(start, end) {
    try {
      const res = await fetch(`/api/analytics/provider-comparison?start_date=${start}&end_date=${end}`);
      providerComparison = await res.json();
    } catch (error) {
      console.error('Error fetching provider comparison:', error);
    }
  }

  async function fetchModelComparison(start, end) {
    try {
      const res = await fetch(`/api/analytics/model-comparison?start_date=${start}&end_date=${end}`);
      modelComparison = await res.json();
    } catch (error) {
      console.error('Error fetching model comparison:', error);
    }
  }

  // Handle date range change
  async function handleDateChange(event) {
    const { start, end } = event.detail;
    dateRange = { start, end };

    // Fetch all data
    await Promise.all([
      fetchTimeSeriesData(start, end),
      fetchAggregateData(start, end),
      fetchProviderComparison(start, end),
      fetchModelComparison(start, end)
    ]);
  }

  // Initialize with default date range (last 7 days)
  function initializeDates() {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 7);

    dateRange.start = start.toISOString().split('T')[0];
    dateRange.end = end.toISOString().split('T')[0];
  }

  // Format currency
  function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  }

  // Format number with commas
  function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
  }

  // Download chart as PNG
  function downloadChart(chartInstance, filename) {
    if (!chartInstance) return;
    const url = chartInstance.toBase64Image();
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.png`;
    a.click();
  }

  // Export data as CSV
  async function exportData(format) {
    const endpoint = format === 'csv' ? '/api/analytics/export/csv' : '/api/analytics/export/json';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: {
            filters: [
              { field: 'timestamp', operator: '>=', value: dateRange.start },
              { field: 'timestamp', operator: '<=', value: dateRange.end }
            ]
          },
          limit: 10000
        })
      });

      const data = await res.json();

      if (format === 'csv' && data.csv) {
        const blob = new Blob([data.csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_export_${dateRange.start}_${dateRange.end}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'json' && data.json) {
        const blob = new Blob([JSON.stringify(data.json, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_export_${dateRange.start}_${dateRange.end}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    }
  }

  // Initialize
  onMount(async () => {
    initializeDates();
    if (dateRange.start && dateRange.end) {
      await Promise.all([
        fetchTimeSeriesData(dateRange.start, dateRange.end),
        fetchAggregateData(dateRange.start, dateRange.end),
        fetchProviderComparison(dateRange.start, dateRange.end),
        fetchModelComparison(dateRange.start, dateRange.end)
      ]);
    }
  });
</script>

<svelte:head>
  <title>Analytics Dashboard - Claude Proxy</title>
</svelte:head>

<div class="analytics-container">
  <!-- Header -->
  <div class="header">
    <div class="title-section">
      <h1>Analytics Dashboard</h1>
      <p class="subtitle">Interactive metrics visualization and data exploration</p>
    </div>

    <div class="actions">
      <button class="btn btn-secondary" on:click={() => exportData('csv')}>
        Export CSV
      </button>
      <button class="btn btn-secondary" on:click={() => exportData('json')}>
        Export JSON
      </button>
    </div>
  </div>

  <!-- Date Range Picker -->
  <div class="date-range-section">
    <TimeRangePicker
      startDate={dateRange.start}
      endDate={dateRange.end}
      on:change={handleDateChange}
    />
  </div>

  <!-- Loading State -->
  {#if loading}
    <div class="loading-state">
      <div class="spinner"></div>
      <span>Loading analytics data...</span>
    </div>
  {/if}

  <!-- Aggregate Stats Cards -->
  {#if aggregate && !loading}
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total Requests</div>
        <div class="stat-value">{formatNumber(aggregate.requests.total)}</div>
        <div class="stat-meta">
          <span class="error-rate">Errors: {aggregate.requests.error_rate}%</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Total Tokens</div>
        <div class="stat-value">{formatNumber(aggregate.usage.tokens)}</div>
        <div class="stat-meta">
          <span class="efficiency">{aggregate.usage.efficiency} tokens/$</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Total Cost</div>
        <div class="stat-value">{formatCurrency(aggregate.usage.cost)}</div>
        <div class="stat-meta">
          <span>{formatNumber(aggregate.usage.tokens)} tokens</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Avg Latency</div>
        <div class="stat-value">{Math.round(aggregate.performance.avg)}ms</div>
        <div class="stat-meta">
          <span>Providers: {aggregate.distribution.providers}</span>
        </div>
      </div>
    </div>
  {/if}

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab-btn {activeTab === 'timeseries' ? 'active' : ''}" on:click={() => activeTab = 'timeseries'}>
      Time Series
    </button>
    <button class="tab-btn {activeTab === 'comparison' ? 'active' : ''}" on:click={() => activeTab = 'comparison'}>
      Provider/Model Comparison
    </button>
  </div>

  <!-- Tab Content: Time Series -->
  {#if activeTab === 'timeseries' && !loading}
    <div class="charts-grid">
      <div class="chart-card">
        <LineChart
          labels={metrics.tokens.labels}
          datasets={metrics.tokens.datasets}
          title="Token Usage Over Time"
          height="280px"
        />
      </div>

      <div class="chart-card">
        <LineChart
          labels={metrics.cost.labels}
          datasets={metrics.cost.datasets}
          title="Cost Over Time"
          height="280px"
        />
      </div>

      <div class="chart-card">
        <LineChart
          labels={metrics.requests.labels}
          datasets={metrics.requests.datasets}
          title="Requests Over Time"
          height="280px"
        />
      </div>
    </div>
  {/if}

  <!-- Tab Content: Comparison -->
  {#if activeTab === 'comparison' && !loading}
    <div class="comparison-grid">
      <!-- Provider Comparison -->
      {#if providerComparison && providerComparison.providers.length > 0}
        <div class="chart-card full-width">
          <h3>Cost by Provider</h3>
          <BarChart
            labels={providerComparison.providers.map(p => p.provider)}
            datasets={[{
              label: 'Cost ($)',
              data: providerComparison.providers.map(p => p.cost)
            }]}
            height="300px"
            showLegend={false}
          />
          <div class="comparison-table">
            <table>
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Requests</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                  <th>Cost/Token</th>
                </tr>
              </thead>
              <tbody>
                {#each providerComparison.providers as provider}
                  <tr>
                    <td>{provider.provider}</td>
                    <td>{formatNumber(provider.requests)}</td>
                    <td>{formatNumber(provider.tokens)}</td>
                    <td>{formatCurrency(provider.cost)}</td>
                    <td>${provider.cost_per_token.toFixed(6)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}

      <!-- Model Comparison -->
      {#if modelComparison && modelComparison.models.length > 0}
        <div class="chart-card full-width">
          <h3>Usage by Model</h3>
          <BarChart
            labels={modelComparison.models.map(m => m.model)}
            datasets={[{
              label: 'Tokens',
              data: modelComparison.models.map(m => m.tokens)
            }]}
            height="300px"
            showLegend={false}
          />
          <div class="comparison-table">
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Requests</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                  <th>Cost/Token</th>
                </tr>
              </thead>
              <tbody>
                {#each modelComparison.models as model}
                  <tr>
                    <td>{model.model}</td>
                    <td>{formatNumber(model.requests)}</td>
                    <td>{formatNumber(model.tokens)}</td>
                    <td>{formatCurrency(model.cost)}</td>
                    <td>${model.cost_per_token.toFixed(6)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Empty State -->
  {#if !loading && (!metrics.tokens.labels || metrics.tokens.labels.length === 0)}
    <div class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>No Data Available</h3>
      <p>Select a date range to start exploring your analytics</p>
    </div>
  {/if}
</div>

<style>
  .analytics-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .title-section h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0;
  }

  .subtitle {
    color: #6b7280;
    margin: 0.25rem 0 0;
  }

  .actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .btn {
    padding: 0.625rem 1.25rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid #e5e7eb;
    transition: all 0.2s;
  }

  .btn-secondary {
    background: white;
    color: #374151;
  }

  .btn-secondary:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  .date-range-section {
    margin-bottom: 2rem;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: white;
    border-radius: 8px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
    margin-bottom: 0.5rem;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 0.5rem;
  }

  .stat-meta {
    font-size: 0.8rem;
    color: #9ca3af;
  }

  .error-rate {
    color: #ef4444;
  }

  .efficiency {
    color: #10b981;
  }

  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #e5e7eb;
  }

  .tab-btn {
    padding: 0.75rem 1.5rem;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 0.95rem;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: -2px;
  }

  .tab-btn.active {
    color: #3b82f6;
    border-bottom-color: #3b82f6;
  }

  .tab-btn:hover {
    color: #374151;
  }

  .charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .chart-card {
    background: white;
    border-radius: 8px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
  }

  .chart-card h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 1rem;
  }

  .comparison-grid {
    display: grid;
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .full-width {
    grid-column: 1 / -1;
  }

  .comparison-table {
    margin-top: 1.5rem;
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  th, td {
    text-align: left;
    padding: 0.75rem;
    border-bottom: 1px solid #e5e7eb;
  }

  th {
    font-weight: 600;
    color: #374151;
    background: #f9fafb;
  }

  td {
    color: #4b5563;
  }

  tr:hover {
    background: #f9fafb;
  }

  .loading-state {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    margin: 1rem 0;
  }

  .spinner {
    width: 24px;
    height: 24px;
    border: 3px solid #e5e7eb;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 8px;
    border: 2px dashed #e5e7eb;
    margin-top: 2rem;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 0.5rem;
  }

  .empty-state p {
    color: #6b7280;
    margin: 0;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .analytics-container {
      padding: 1rem;
    }

    .header {
      flex-direction: column;
      align-items: flex-start;
    }

    .charts-grid {
      grid-template-columns: 1fr;
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .comparison-table {
      font-size: 0.75rem;
    }

    th, td {
      padding: 0.5rem;
    }
  }
</style>