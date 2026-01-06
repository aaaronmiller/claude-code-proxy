<!-- Advanced Query Builder Page -->
<script>
  import { onMount } from "svelte";
  import QueryBuilder from "../../../components/query/QueryBuilder.svelte";
  import { BarChart3, Database, Download, History } from "lucide-svelte";

  let activeTab = $state("builder");
  let savedQueries = $state([]);
  let queryResults = $state(null);

  // Load saved queries on mount
  onMount(async () => {
    try {
      const response = await fetch("/api/analytics/queries");
      if (response.ok) {
        savedQueries = await response.json();
      }
    } catch (error) {
      console.error("Error loading saved queries:", error);
    }
  });

  // Handle query results
  function handleResults(event) {
    queryResults = event.detail;
  }

  // Load saved query
  function loadQuery(queryData) {
    // This would populate the QueryBuilder with saved data
    alert("Loading query: " + queryData.name);
  }

  // Delete saved query
  async function deleteQuery(id) {
    if (!confirm("Delete this query?")) return;

    try {
      const response = await fetch(`/api/analytics/queries/${id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        savedQueries = savedQueries.filter((q) => q.id !== id);
      }
    } catch (error) {
      console.error("Error deleting query:", error);
    }
  }

  // Export all results as CSV
  function exportAllResults() {
    if (!queryResults || !queryResults.data) return;

    const metrics = ["tokens", "cost", "requests", "latency"];
    const headers = ["Date", ...metrics];
    const rows = queryResults.data.map((row) => {
      return [
        row.date || row.timestamp,
        ...metrics.map((m) => row[m] || 0),
      ].join(",");
    });

    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `analytics_export_${Date.now()}.csv`;
    a.click();
  }
</script>

<div class="query-page">
  <!-- Page Header -->
  <div class="page-header">
    <div class="title-section">
      <BarChart3 size={28} />
      <h1>Advanced Analytics Query</h1>
    </div>
    <div class="tabs">
      <button
        class="tab {activeTab === 'builder' ? 'active' : ''}"
        onclick={() => (activeTab = "builder")}
      >
        <Database size={16} /> Query Builder
      </button>
      <button
        class="tab {activeTab === 'saved' ? 'active' : ''}"
        onclick={() => (activeTab = "saved")}
      >
        <History size={16} /> Saved Queries
      </button>
    </div>
  </div>

  <!-- Content Area -->
  <div class="content">
    {#if activeTab === "builder"}
      <div class="builder-tab">
        <QueryBuilder on:results={handleResults} />

        <!-- Results Summary -->
        {#if queryResults}
          <div class="results-summary">
            <div class="summary-header">
              <h3>Query Results</h3>
              <button class="btn" onclick={exportAllResults}>
                <Download size={14} /> Export
              </button>
            </div>
            <div class="stats-grid">
              <div class="stat-card">
                <span class="stat-label">Total Records</span>
                <span class="stat-value">{queryResults.data?.length || 0}</span>
              </div>
              {#if queryResults.data && queryResults.data.length > 0}
                <div class="stat-card">
                  <span class="stat-label">Total Tokens</span>
                  <span class="stat-value"
                    >{queryResults.data
                      .reduce((sum, r) => sum + (r.tokens || 0), 0)
                      .toLocaleString()}</span
                  >
                </div>
                <div class="stat-card">
                  <span class="stat-label">Total Cost</span>
                  <span class="stat-value"
                    >${queryResults.data
                      .reduce((sum, r) => sum + (r.cost || 0), 0)
                      .toFixed(2)}</span
                  >
                </div>
                <div class="stat-card">
                  <span class="stat-label">Total Requests</span>
                  <span class="stat-value"
                    >{queryResults.data
                      .reduce((sum, r) => sum + (r.requests || 0), 0)
                      .toLocaleString()}</span
                  >
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    {:else}
      <div class="saved-tab">
        <div class="saved-header">
          <h3>Saved Queries</h3>
          <span class="count-badge">{savedQueries.length}</span>
        </div>

        {#if savedQueries.length === 0}
          <div class="empty-state">
            <p>No saved queries yet</p>
            <p class="hint">
              Create and save queries from the Query Builder tab
            </p>
          </div>
        {:else}
          <div class="queries-grid">
            {#each savedQueries as query}
              <div class="query-card">
                <div class="query-info">
                  <h4>{query.name}</h4>
                  <p class="meta">
                    Created: {new Date(query.created_at).toLocaleDateString()}
                    • Metrics: {query.query.metrics.join(", ")}
                  </p>
                  <p class="description">
                    {query.query.filters.length} filters • Group by: {query
                      .query.groupBy}
                  </p>
                </div>
                <div class="query-actions">
                  <button class="btn btn-load" onclick={() => loadQuery(query)}
                    >Load</button
                  >
                  <button
                    class="btn btn-delete"
                    onclick={() => deleteQuery(query.id)}>Delete</button
                  >
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
  .query-page {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--border-color, #e5e7eb);
  }

  .title-section {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .title-section h1 {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary, #1f2937);
  }

  .tabs {
    display: flex;
    gap: 0.5rem;
    background: var(--bg-secondary, #f9fafb);
    padding: 0.25rem;
    border-radius: 8px;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: transparent;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    color: var(--text-secondary, #6b7280);
    transition: all 0.2s;
  }

  .tab:hover {
    background: white;
  }

  .tab.active {
    background: white;
    color: var(--primary, #3b82f6);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .content {
    margin-top: 1.5rem;
  }

  .results-summary {
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: white;
    border-radius: 12px;
    border: 1px solid var(--border-color, #e5e7eb);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-color, #e5e7eb);
  }

  .summary-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .stat-card {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 1rem;
    background: var(--bg-secondary, #f9fafb);
    border-radius: 8px;
    text-align: center;
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary, #6b7280);
    font-weight: 500;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary, #3b82f6);
  }

  .saved-tab {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid var(--border-color, #e5e7eb);
  }

  .saved-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .saved-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .count-badge {
    background: var(--primary, #3b82f6);
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary, #6b7280);
  }

  .empty-state p {
    margin: 0.5rem 0;
  }

  .empty-state .hint {
    font-size: 0.875rem;
    opacity: 0.7;
  }

  .queries-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1rem;
  }

  .query-card {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
    background: var(--bg-secondary, #f9fafb);
    border-radius: 8px;
    border: 1px solid var(--border-color, #e5e7eb);
    transition: all 0.2s;
  }

  .query-card:hover {
    border-color: var(--primary, #3b82f6);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  }

  .query-info h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary, #1f2937);
  }

  .meta {
    margin: 0;
    font-size: 0.8rem;
    color: var(--text-secondary, #6b7280);
  }

  .description {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary, #6b7280);
  }

  .query-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn-load {
    background: var(--primary, #3b82f6);
    color: white;
  }

  .btn-load:hover {
    background: #2563eb;
  }

  .btn-delete {
    background: white;
    color: #dc2626;
    border: 1px solid #fca5a5;
  }

  .btn-delete:hover {
    background: #fef2f2;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .query-page {
      padding: 1rem;
    }

    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .tabs {
      width: 100%;
      justify-content: stretch;
    }

    .tab {
      flex: 1;
      justify-content: center;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .queries-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
