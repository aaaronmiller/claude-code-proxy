<!--
  Alert History Dashboard - Phase 3
  View and manage alert history with filtering and bulk actions
-->
<script>
  import { onMount } from 'svelte';

  // State
  let alerts = [];
  let filteredAlerts = [];
  let stats = null;
  let loading = false;

  // Filters
  let filters = {
    severity: 'all',
    status: 'all',
    searchTerm: '',
    dateRange: '7d'
  };

  // Bulk actions
  let selectedAlerts = new Set();
  let showBulkActions = false;

  // UI State
  let message = '';

  // Severity mapping
  const severityColors = {
    critical: { bg: '#fee2e2', text: '#991b1b', icon: '🔴' },
    high: { bg: '#ffedd5', text: '#9a3412', icon: '🟠' },
    medium: { bg: '#fef3c7', text: '#92400e', icon: '🟡' },
    low: { bg: '#dbeafe', text: '#1e40af', icon: '🔵' }
  };

  // Load alerts
  async function loadAlerts() {
    loading = true;
    try {
      const params = new URLSearchParams({
        limit: '100',
        status: filters.status === 'all' ? '' : filters.status,
        severity: filters.severity === 'all' ? '' : filters.severity
      });

      const res = await fetch(`/api/alerts/history?${params}`);
      const data = await res.json();
      alerts = data.alerts || [];
      applyFilters();
    } catch (error) {
      console.error('Failed to load alerts:', error);
      message = 'Failed to load alerts';
    } finally {
      loading = false;
    }
  }

  // Load statistics
  async function loadStats() {
    try {
      const res = await fetch('/api/alerts/stats?days=30');
      stats = await res.json();
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }

  // Apply filters
  function applyFilters() {
    filteredAlerts = alerts.filter(alert => {
      // Search term
      if (filters.searchTerm) {
        const search = filters.searchTerm.toLowerCase();
        const matchName = alert.rule_name.toLowerCase().includes(search);
        const matchDesc = alert.description?.toLowerCase().includes(search);
        if (!matchName && !matchDesc) return false;
      }
      return true;
    });
  }

  // Handle filter change
  function onFilterChange() {
    loadAlerts();
  }

  // Acknowledge alert
  async function acknowledgeAlert(alertId) {
    try {
      const res = await fetch(`/api/alerts/history/${alertId}/ack`, {
        method: 'POST'
      });
      if (res.ok) {
        loadAlerts();
        message = 'Alert acknowledged';
        setTimeout(() => message = '', 2000);
      }
    } catch (error) {
      console.error('Failed to acknowledge:', error);
    }
  }

  // Resolve alert
  async function resolveAlert(alertId) {
    const notes = prompt('Add resolution notes (optional):');
    if (notes === null) return; // User cancelled

    try {
      const res = await fetch(`/api/alerts/history/${alertId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: notes || undefined })
      });
      if (res.ok) {
        loadAlerts();
        message = 'Alert resolved';
        setTimeout(() => message = '', 2000);
      }
    } catch (error) {
      console.error('Failed to resolve:', error);
    }
  }

  // Delete alert
  async function deleteAlert(alertId) {
    if (!confirm('Delete this alert?')) return;

    try {
      const res = await fetch(`/api/alerts/history/${alertId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        loadAlerts();
        message = 'Alert deleted';
        setTimeout(() => message = '', 2000);
      }
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  }

  // Bulk selection
  function toggleSelect(alertId) {
    if (selectedAlerts.has(alertId)) {
      selectedAlerts.delete(alertId);
    } else {
      selectedAlerts.add(alertId);
    }
    updateBulkActions();
  }

  function updateBulkActions() {
    showBulkActions = selectedAlerts.size > 0;
  }

  function selectAll() {
    selectedAlerts = new Set(filteredAlerts.map(a => a.id));
    updateBulkActions();
  }

  function clearSelection() {
    selectedAlerts.clear();
    updateBulkActions();
  }

  // Bulk operations
  async function bulkAction(action) {
    if (selectedAlerts.size === 0) return;

    const alertIds = Array.from(selectedAlerts);

    let notes = undefined;
    if (action === 'resolve') {
      notes = prompt('Add resolution notes for all selected alerts:');
      if (notes === null) return;
    }

    try {
      const res = await fetch('/api/alerts/history/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: action,
          alert_ids: alertIds,
          notes: notes
        })
      });

      const data = await res.json();

      if (res.ok) {
        message = data.message;
        setTimeout(() => message = '', 3000);
        clearSelection();
        loadAlerts();
      }
    } catch (error) {
      console.error('Bulk action failed:', error);
      message = 'Bulk action failed';
    }
  }

  // Export to CSV
  function exportToCSV() {
    if (filteredAlerts.length === 0) return;

    const headers = ['ID', 'Rule', 'Severity', 'Triggered At', 'Status', 'Description'];
    const rows = filteredAlerts.map(a => [
      a.id,
      a.rule_name,
      a.severity,
      a.triggered_at,
      a.resolved ? 'Resolved' : (a.acknowledged ? 'Acknowledged' : 'Open'),
      a.description.replace(/"/g, '""')
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alerts_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Format date
  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString();
  }

  function timeAgo(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  }

  // Auto-refresh
  let autoRefreshInterval;

  onMount(() => {
    loadAlerts();
    loadStats();

    // Auto-refresh every 30 seconds
    autoRefreshInterval = setInterval(() => {
      loadAlerts();
      loadStats();
    }, 30000);

    return () => {
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
      }
    };
  });
</script>

<svelte:head>
  <title>Alert History - Claude Proxy</title>
</svelte:head>

<div class="alerts-container">
  <!-- Header -->
  <div class="header">
    <div class="title-section">
      <h1>Alert History</h1>
      <p class="subtitle">View and manage triggered alerts</p>
    </div>
    <div class="actions">
      <button class="btn btn-secondary" on:click={exportToCSV} disabled={filteredAlerts.length === 0}>
        Export CSV
      </button>
      <a href="/alerts/builder" class="btn btn-primary">
        Create Alert Rule
      </a>
    </div>
  </div>

  <!-- Statistics Cards -->
  {#if stats}
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total Alerts (30d)</div>
        <div class="stat-value">{stats.total}</div>
        <div class="stat-meta">Open: {stats.open}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Resolved</div>
        <div class="stat-value">{stats.resolved}</div>
        <div class="stat-meta">Resolution Rate: {stats.total > 0 ? Math.round((stats.resolved / stats.total) * 100) : 0}%</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Critical/High</div>
        <div class="stat-value">{(stats.severity_breakdown.critical || 0) + (stats.severity_breakdown.high || 0)}</div>
        <div class="stat-meta">Need attention</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Active Rules</div>
        <div class="stat-value">{stats.unique_rules}</div>
        <div class="stat-meta">Monitored</div>
      </div>
    </div>
  {/if}

  <!-- Message -->
  {#if message}
    <div class="message">{message}</div>
  {/if}

  <!-- Filters -->
  <div class="filters-section">
    <div class="filter-group">
      <label>Severity</label>
      <select bind:value={filters.severity} on:change={onFilterChange}>
        <option value="all">All</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>

    <div class="filter-group">
      <label>Status</label>
      <select bind:value={filters.status} on:change={onFilterChange}>
        <option value="all">All</option>
        <option value="unresolved">Unresolved</option>
        <option value="resolved">Resolved</option>
      </select>
    </div>

    <div class="filter-group">
      <label>Search</label>
      <input
        type="text"
        placeholder="Search rule name or description..."
        bind:value={filters.searchTerm}
        on:input={applyFilters}
      />
    </div>

    <div class="filter-group">
      <label> </label>
      <button class="btn btn-secondary" on:click={loadAlerts}>
        Refresh
      </button>
    </div>
  </div>

  <!-- Bulk Actions -->
  {#if showBulkActions}
    <div class="bulk-actions">
      <span>{selectedAlerts.size} selected</span>
      <div class="bulk-buttons">
        <button class="btn btn-small" on:click={() => bulkAction('acknowledge')}>
          Acknowledge
        </button>
        <button class="btn btn-small btn-resolve" on:click={() => bulkAction('resolve')}>
          Resolve
        </button>
        <button class="btn btn-small btn-delete" on:click={() => bulkAction('delete')}>
          Delete
        </button>
        <button class="btn btn-small" on:click={clearSelection}>
          Clear
        </button>
      </div>
    </div>
  {/if}

  <!-- Alert List -->
  <div class="alerts-list-section">
    {#if loading}
      <div class="loading">Loading alerts...</div>
    {:else if filteredAlerts.length === 0}
      <div class="empty-state">
        <div class="empty-icon">🔔</div>
        <h3>No alerts found</h3>
        <p>Create an alert rule to start monitoring</p>
        <a href="/alerts/builder" class="btn btn-primary">Create First Rule</a>
      </div>
    {:else}
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th class="select-column">
                <input
                  type="checkbox"
                  on:change={(e) => e.target.checked ? selectAll() : clearSelection()}
                />
              </th>
              <th>Severity</th>
              <th>Rule</th>
              <th>Triggered</th>
              <th>Time Ago</th>
              <th>Status</th>
              <th>Description</th>
              <th class="actions-column">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredAlerts as alert}
              <tr class:selected={selectedAlerts.has(alert.id)}>
                <td class="select-column">
                  <input
                    type="checkbox"
                    checked={selectedAlerts.has(alert.id)}
                    on:change={() => toggleSelect(alert.id)}
                  />
                </td>
                <td>
                  <span
                    class="severity-badge {alert.severity}"
                    style="background: {severityColors[alert.severity].bg}; color: {severityColors[alert.severity].text};"
                  >
                    {severityColors[alert.severity].icon} {alert.severity.toUpperCase()}
                  </span>
                </td>
                <td class="rule-name">{alert.rule_name}</td>
                <td>{formatDate(alert.triggered_at)}</td>
                <td>{timeAgo(alert.triggered_at)}</td>
                <td>
                  {#if alert.resolved}
                    <span class="status-badge resolved">Resolved</span>
                  {:else if alert.acknowledged}
                    <span class="status-badge acknowledged">Acknowledged</span>
                  {:else}
                    <span class="status-badge open">Open</span>
                  {/if}
                </td>
                <td class="description">{alert.description || '-'}</td>
                <td class="actions">
                  {#if !alert.resolved}
                    <button
                      class="btn-action ack"
                      on:click={() => acknowledgeAlert(alert.id)}
                      title="Acknowledge"
                    >
                      ✓
                    </button>
                    <button
                      class="btn-action resolve"
                      on:click={() => resolveAlert(alert.id)}
                      title="Resolve"
                    >
                      ✓✓
                    </button>
                  {/if}
                  <button
                    class="btn-action delete"
                    on:click={() => deleteAlert(alert.id)}
                    title="Delete"
                  >
                    ×
                  </button>
                </td>
              </tr>
              {#if alert.alert_data && alert.alert_data.triggered_conditions}
                <tr class="details-row">
                  <td colspan="8">
                    <div class="alert-details">
                      <strong>Triggered Conditions:</strong>
                      <ul>
                        {#each alert.alert_data.triggered_conditions as cond}
                          <li>
                            {cond.metric || cond.field}: {cond.actual} {cond.operator} {cond.value}
                          </li>
                        {/each}
                      </ul>
                      {#if alert.notes}
                        <div class="notes">
                          <strong>Notes:</strong> {alert.notes}
                        </div>
                      {/if}
                    </div>
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

<style>
  .alerts-container {
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
  }

  .btn {
    padding: 0.625rem 1.25rem;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
    font-size: 0.9rem;
    text-decoration: none;
    display: inline-block;
  }

  .btn-secondary {
    background: white;
    color: #374151;
    border: 1px solid #e5e7eb;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #3b82f6;
    color: white;
  }

  .btn-primary:hover {
    background: #2563eb;
  }

  .btn-small {
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
  }

  .btn-resolve {
    background: #10b981;
    color: white;
  }

  .btn-resolve:hover {
    background: #059669;
  }

  .btn-delete {
    background: #ef4444;
    color: white;
  }

  .btn-delete:hover {
    background: #dc2626;
  }

  /* Stats */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    background: white;
    padding: 1.25rem;
    border-radius: 8px;
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
    margin-bottom: 0.25rem;
  }

  .stat-meta {
    font-size: 0.8rem;
    color: #9ca3af;
  }

  /* Message */
  .message {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    font-weight: 500;
  }

  /* Filters */
  .filters-section {
    background: white;
    padding: 1.25rem;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    margin-bottom: 1rem;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
  }

  .filter-group label {
    display: block;
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  .filter-group select,
  .filter-group input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.9rem;
  }

  .filter-group input:focus,
  .filter-group select:focus {
    outline: none;
    border-color: #3b82f6;
  }

  /* Bulk Actions */
  .bulk-actions {
    background: #fef3c7;
    border: 1px solid #fbbf24;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .bulk-buttons {
    display: flex;
    gap: 0.5rem;
  }

  /* Alerts List */
  .alerts-list-section {
    background: white;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    overflow: hidden;
  }

  .loading {
    text-align: center;
    padding: 3rem;
    color: #6b7280;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
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
    margin-bottom: 1.5rem;
  }

  .table-container {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th {
    background: #f9fafb;
    text-align: left;
    padding: 1rem;
    font-weight: 600;
    color: #374151;
    border-bottom: 2px solid #e5e7eb;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  td {
    padding: 1rem;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.9rem;
    color: #4b5563;
  }

  tr:hover {
    background: #f9fafb;
  }

  tr.selected {
    background: #eff6ff;
  }

  tr.details-row {
    background: #f9fafb;
  }

  tr.details-row td {
    padding: 0.75rem 1rem 1rem 3.5rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .select-column {
    width: 40px;
    text-align: center;
  }

  .actions-column {
    width: 120px;
  }

  .severity-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
  }

  .status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .status-badge.open {
    background: #fee2e2;
    color: #991b1b;
  }

  .status-badge.acknowledged {
    background: #fef3c7;
    color: #92400e;
  }

  .status-badge.resolved {
    background: #dcfce7;
    color: #166534;
  }

  .rule-name {
    font-weight: 600;
    color: #1f2937;
  }

  .description {
    max-width: 300px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .actions {
    display: flex;
    gap: 0.25rem;
  }

  .btn-action {
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 700;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .btn-action.ack {
    background: #fef3c7;
    color: #92400e;
  }

  .btn-action.ack:hover {
    background: #fde68a;
  }

  .btn-action.resolve {
    background: #dcfce7;
    color: #166534;
  }

  .btn-action.resolve:hover {
    background: #bbf7d0;
  }

  .btn-action.delete {
    background: #fee2e2;
    color: #991b1b;
  }

  .btn-action.delete:hover {
    background: #fecaca;
  }

  .alert-details {
    background: white;
    padding: 1rem;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
  }

  .alert-details ul {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .alert-details li {
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: #6b7280;
  }

  .notes {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
    font-style: italic;
    color: #6b7280;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .alerts-container {
      padding: 1rem;
    }

    .filters-section {
      grid-template-columns: 1fr 1fr;
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .header {
      flex-direction: column;
      align-items: flex-start;
    }

    .actions {
      width: 100%;
      flex-direction: column;
    }

    .btn {
      width: 100%;
      text-align: center;
    }

    table {
      font-size: 0.8rem;
    }

    td, th {
      padding: 0.5rem;
    }

    .description {
      max-width: 150px;
    }
  }
</style>