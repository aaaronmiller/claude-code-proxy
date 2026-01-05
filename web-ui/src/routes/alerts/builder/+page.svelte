<!--
  Alert Rule Builder - Phase 3
  Visual interface for creating complex alert rules with multi-condition logic
-->
<script>
  import { onMount } from 'svelte';

  // Form state
  let ruleName = '';
  let ruleDescription = '';
  let conditions = [];
  let logicType = 'AND'; // AND or OR
  let timeWindow = 5; // minutes
  let cooldown = 15; // minutes
  let priority = 'high';
  let actions = {
    in_app: true,
    email: true,
    email_address: '',
    slack: false,
    slack_webhook: '',
    webhook: false,
    webhook_url: '',
    webhook_headers: ''
  };

  // Available metrics for conditions
  const metrics = [
    { value: 'cost', label: 'Total Cost', type: 'currency' },
    { value: 'tokens', label: 'Total Tokens', type: 'number' },
    { value: 'requests', label: 'Request Count', type: 'number' },
    { value: 'error_rate', label: 'Error Rate', type: 'percentage' },
    { value: 'avg_latency', label: 'Average Latency', type: 'duration' },
    { value: 'cost_per_token', label: 'Cost per Token', type: 'currency' },
    { value: 'cost_change_percent', label: 'Cost Change %', type: 'percentage' }
  ];

  const operators = [
    { value: '>', label: 'Greater than (>)' },
    { value: '<', label: 'Less than (<)' },
    { value: '>=', label: 'Greater or Equal (>=)' },
    { value: '<=', label: 'Less or Equal (<=)' },
    { value: '=', label: 'Equal (=)' },
    { value: '!=', label: 'Not Equal (!=)' }
  ];

  const priorities = [
    { value: '0', label: 'Critical' },
    { value: '1', label: 'High' },
    { value: '2', label: 'Medium' },
    { value: '3', label: 'Low' }
  ];

  // UI State
  let showTestResults = false;
  let testResults = null;
  let loading = false;
  let previewOpen = false;
  let successMessage = '';
  let errorMessage = '';

  // Add a new condition
  function addCondition() {
    conditions = [
      ...conditions,
      {
        metric: 'cost',
        operator: '>',
        value: 100,
        id: Date.now()
      }
    ];
  }

  // Remove a condition
  function removeCondition(id) {
    conditions = conditions.filter(c => c.id !== id);
  }

  // Update condition
  function updateCondition(id, field, value) {
    conditions = conditions.map(c =>
      c.id === id ? { ...c, [field]: value } : c
    );
  }

  // Test the alert rule
  async function testRule() {
    if (conditions.length === 0) {
      errorMessage = 'Add at least one condition';
      return;
    }

    loading = true;
    errorMessage = '';
    showTestResults = false;

    try {
      // Simulate test (would call backend test endpoint)
      const testPayload = {
        conditions: conditions.map(c => ({
          metric: c.metric,
          operator: c.operator,
          threshold: parseFloat(c.value)
        })),
        logic: logicType,
        time_window: timeWindow
      };

      // Call test API
      const res = await fetch('/api/alerts/rules/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testPayload)
      });

      const data = await res.json();
      testResults = data;
      showTestResults = true;
      successMessage = 'Test completed! See results below.';
    } catch (error) {
      errorMessage = `Test failed: ${error.message}`;
    } finally {
      loading = false;
    }
  }

  // Generate rule preview
  function generatePreview() {
    const conditionText = conditions.map(c => {
      const metric = metrics.find(m => m.value === c.metric)?.label || c.metric;
      return `${metric} ${c.operator} ${c.value}`;
    }).join(` ${logicType} `);

    return {
      name: ruleName || 'Untitled Rule',
      description: ruleDescription,
      trigger_when: conditionText,
      time_window: `${timeWindow} minutes`,
      cooldown: `${cooldown} minutes`,
      priority: priorities.find(p => p.value === priority)?.label,
      actions: getSelectedActions()
    };
  }

  function getSelectedActions() {
    const selected = [];
    if (actions.in_app) selected.push('In-app notification');
    if (actions.email) selected.push(`Email to ${actions.email_address || 'configured address'}`);
    if (actions.slack) selected.push('Slack webhook');
    if (actions.webhook) selected.push('Custom webhook');
    return selected.length > 0 ? selected.join(', ') : 'None selected';
  }

  // Save the rule
  async function saveRule() {
    if (!ruleName) {
      errorMessage = 'Rule name is required';
      return;
    }

    if (conditions.length === 0) {
      errorMessage = 'Add at least one condition';
      return;
    }

    loading = true;
    errorMessage = '';
    successMessage = '';

    // Build action config
    const actionConfig = { channels: [] };
    if (actions.in_app) actionConfig.channels.push('in_app');
    if (actions.email) {
      actionConfig.channels.push('email');
      actionConfig.email = actions.email_address;
    }
    if (actions.slack) {
      actionConfig.channels.push('slack_webhook');
      actionConfig.slack_webhook = actions.slack_webhook;
    }
    if (actions.webhook) {
      actionConfig.channels.push('webhook');
      actionConfig.webhook_url = actions.webhook_url;
      actionConfig.webhook_headers = actions.webhook_headers;
    }

    // Build rule payload
    const payload = {
      name: ruleName,
      description: ruleDescription,
      conditions: conditions.map(c => ({
        metric: c.metric,
        operator: c.operator,
        threshold: parseFloat(c.value)
      })),
      logic: { type: logicType, conditions: conditions.map(c => ({
        metric: c.metric,
        operator: c.operator,
        threshold: parseFloat(c.value)
      })) },
      actions: actionConfig,
      cooldown_minutes: parseInt(cooldown),
      priority: parseInt(priority),
      time_window: parseInt(timeWindow),
      created_by: 'web_ui'
    };

    try {
      const res = await fetch('/api/alerts/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (res.ok && data.success) {
        successMessage = `✅ Rule "${ruleName}" created successfully! (ID: ${data.rule_id})`;
        // Reset form
        setTimeout(() => {
          resetForm();
        }, 2000);
      } else {
        errorMessage = data.detail || 'Failed to create rule';
      }
    } catch (error) {
      errorMessage = `Error: ${error.message}`;
    } finally {
      loading = false;
    }
  }

  function resetForm() {
    ruleName = '';
    ruleDescription = '';
    conditions = [];
    logicType = 'AND';
    timeWindow = 5;
    cooldown = 15;
    priority = 'high';
    actions = {
      in_app: true,
      email: true,
      email_address: '',
      slack: false,
      slack_webhook: '',
      webhook: false,
      webhook_url: '',
      webhook_headers: ''
    };
    showTestResults = false;
    testResults = null;
    successMessage = '';
    errorMessage = '';
  }

  // Check form validity
  $: isValid = ruleName && conditions.length > 0;

  onMount(() => {
    // Add default condition if empty
    if (conditions.length === 0) {
      addCondition();
    }
  });
</script>

<svelte:head>
  <title>Alert Rule Builder - Claude Proxy</title>
</svelte:head>

<div class="builder-container">
  <!-- Header -->
  <div class="header">
    <div class="title-section">
      <h1>Alert Rule Builder</h1>
      <p class="subtitle">Create custom alert rules with multi-condition logic</p>
    </div>
    <div class="actions">
      <button class="btn btn-secondary" on:click={resetForm}>
        Reset
      </button>
    </div>
  </div>

  <!-- Main Content -->
  <div class="content-grid">
    <!-- Left Column: Rule Configuration -->
    <div class="left-column">
      <!-- Basic Info -->
      <div class="section-card">
        <div class="section-header">
          <h2>Basic Information</h2>
        </div>
        <div class="form-group">
          <label for="rule-name">Rule Name *</label>
          <input
            id="rule-name"
            type="text"
            bind:value={ruleName}
            placeholder="e.g., Weekly Budget Alert"
            class="input-field"
          />
        </div>
        <div class="form-group">
          <label for="description">Description</label>
          <textarea
            id="description"
            bind:value={ruleDescription}
            placeholder="Brief description of what this rule monitors"
            class="textarea-field"
            rows="2"
          ></textarea>
        </div>
      </div>

      <!-- Conditions Builder -->
      <div class="section-card">
        <div class="section-header">
          <h2>Conditions</h2>
          <span class="badge">{conditions.length} condition{conditions.length !== 1 ? 's' : ''}</span>
        </div>

        <div class="logic-toggle">
          <span>Match logic:</span>
          <div class="toggle-group">
            <button
              class="toggle-btn {logicType === 'AND' ? 'active' : ''}"
              on:click={() => logicType = 'AND'}
            >
              ALL (AND)
            </button>
            <button
              class="toggle-btn {logicType === 'OR' ? 'active' : ''}"
              on:click={() => logicType = 'OR'}
            >
              ANY (OR)
            </button>
          </div>
        </div>

        <div class="conditions-list">
          {#each conditions as condition, index (condition.id)}
            <div class="condition-row">
              <div class="condition-number">{index + 1}</div>

              <div class="form-group">
                <label>Metric</label>
                <select
                  class="select-field"
                  bind:value={condition.metric}
                  on:change={(e) => updateCondition(condition.id, 'metric', e.target.value)}
                >
                  {#each metrics as m}
                    <option value={m.value}>{m.label}</option>
                  {/each}
                </select>
              </div>

              <div class="form-group">
                <label>Operator</label>
                <select
                  class="select-field"
                  bind:value={condition.operator}
                  on:change={(e) => updateCondition(condition.id, 'operator', e.target.value)}
                >
                  {#each operators as op}
                    <option value={op.value}>{op.label}</option>
                  {/each}
                </select>
              </div>

              <div class="form-group">
                <label>Threshold</label>
                <input
                  type="number"
                  step="0.01"
                  class="input-field"
                  bind:value={condition.value}
                  on:input={(e) => updateCondition(condition.id, 'value', e.target.value)}
                />
              </div>

              <button
                class="btn-remove"
                on:click={() => removeCondition(condition.id)}
                aria-label="Remove condition"
              >
                ×
              </button>
            </div>
          {/each}

          <button class="btn-add-condition" on:click={addCondition}>
            + Add Condition
          </button>
        </div>
      </div>

      <!-- Evaluation Settings -->
      <div class="section-card">
        <div class="section-header">
          <h2>Evaluation Settings</h2>
        </div>
        <div class="settings-grid">
          <div class="form-group">
            <label for="time-window">Time Window (minutes)</label>
            <input
              id="time-window"
              type="number"
              min="1"
              max="60"
              bind:value={timeWindow}
              class="input-field"
            />
            <span class="help-text">Evaluate every {timeWindow} minutes</span>
          </div>

          <div class="form-group">
            <label for="cooldown">Cooldown (minutes)</label>
            <input
              id="cooldown"
              type="number"
              min="5"
              max="1440"
              bind:value={cooldown}
              class="input-field"
            />
            <span class="help-text">Wait before re-triggering</span>
          </div>

          <div class="form-group">
            <label for="priority">Priority</label>
            <select id="priority" class="select-field" bind:value={priority}>
              {#each priorities as p}
                <option value={p.value}>{p.label}</option>
              {/each}
            </select>
          </div>
        </div>
      </div>

      <!-- Actions / Notifications -->
      <div class="section-card">
        <div class="section-header">
          <h2>Actions & Notifications</h2>
        </div>

        <div class="actions-list">
          <!-- In-App -->
          <div class="action-item">
            <input
              id="action-inapp"
              type="checkbox"
              bind:checked={actions.in_app}
            />
            <label for="action-inapp">In-app notification (bell icon)</label>
          </div>

          <!-- Email -->
          <div class="action-item">
            <input
              id="action-email"
              type="checkbox"
              bind:checked={actions.email}
            />
            <label for="action-email">Email notification</label>
          </div>
          {#if actions.email}
            <div class="action-detail">
              <input
                type="email"
                placeholder="Recipient email (leave blank for default)"
                class="input-field"
                bind:value={actions.email_address}
              />
            </div>
          {/if}

          <!-- Slack -->
          <div class="action-item">
            <input
              id="action-slack"
              type="checkbox"
              bind:checked={actions.slack}
            />
            <label for="action-slack">Slack webhook</label>
          </div>
          {#if actions.slack}
            <div class="action-detail">
              <input
                type="url"
                placeholder="Webhook URL"
                class="input-field"
                bind:value={actions.slack_webhook}
              />
            </div>
          {/if}

          <!-- Custom Webhook -->
          <div class="action-item">
            <input
              id="action-webhook"
              type="checkbox"
              bind:checked={actions.webhook}
            />
            <label for="action-webhook">Custom webhook</label>
          </div>
          {#if actions.webhook}
            <div class="action-detail">
              <input
                type="url"
                placeholder="Webhook URL"
                class="input-field"
                bind:value={actions.webhook_url}
              />
              <textarea
                placeholder="Custom headers (JSON format)"
                class="textarea-field"
                rows="2"
                bind:value={actions.webhook_headers}
              ></textarea>
            </div>
          {/if}
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button
          class="btn btn-test"
          on:click={testRule}
          disabled={loading || conditions.length === 0}
        >
          {loading ? 'Testing...' : 'Test Alert'}
        </button>
        <button
          class="btn btn-primary"
          on:click={saveRule}
          disabled={loading || !isValid}
        >
          {loading ? 'Saving...' : 'Create Rule'}
        </button>
      </div>

      <!-- Messages -->
      {#if successMessage}
        <div class="message success">{successMessage}</div>
      {/if}
      {#if errorMessage}
        <div class="message error">{errorMessage}</div>
      {/if}
    </div>

    <!-- Right Column: Preview & Test Results -->
    <div class="right-column">
      <!-- Rule Preview -->
      <div class="section-card">
        <div class="section-header">
          <h2>Rule Preview</h2>
        </div>

        {#if isValid}
          <div class="preview-content">
            <div class="preview-item">
              <strong>Name:</strong>
              <span>{ruleName}</span>
            </div>
            {#if ruleDescription}
              <div class="preview-item">
                <strong>Description:</strong>
                <span>{ruleDescription}</span>
              </div>
            {/if}
            <div class="preview-item">
              <strong>Trigger When:</strong>
              <div class="condition-preview">
                {#each conditions as condition, index}
                  <div>
                    {metrics.find(m => m.value === condition.metric)?.label}
                    {condition.operator}
                    {condition.value}
                    {#if index < conditions.length - 1}
                      <span class="logic-operator">{logicType}</span>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
            <div class="preview-item">
              <strong>Evaluation:</strong>
              <span>Every {timeWindow} minutes</span>
            </div>
            <div class="preview-item">
              <strong>Cooldown:</strong>
              <span>{cooldown} minutes</span>
            </div>
            <div class="preview-item">
              <strong>Priority:</strong>
              <span class="priority-badge priority-{priority}">
                {priorities.find(p => p.value === priority)?.label}
              </span>
            </div>
            <div class="preview-item">
              <strong>Actions:</strong>
              <span>{getSelectedActions()}</span>
            </div>
          </div>
        {:else}
          <div class="empty-preview">
            Complete the form to see rule preview
          </div>
        {/if}
      </div>

      <!-- Test Results -->
      {#if showTestResults && testResults}
        <div class="section-card">
          <div class="section-header">
            <h2>Test Results</h2>
            <span class="badge {testResults.triggered ? 'triggered' : 'not-triggered'}">
              {testResults.triggered ? 'Would Trigger' : 'Would Not Trigger'}
            </span>
          </div>

          <div class="test-results">
            <div class="result-item">
              <strong>Current Metrics:</strong>
              <div class="metrics-display">
                {#if testResults.metrics}
                  {#each Object.entries(testResults.metrics) as [key, value]}
                    <div class="metric-item">
                      <span class="metric-name">{key}</span>
                      <span class="metric-value">
                        {typeof value === 'number' ? value.toFixed(2) : value}
                      </span>
                    </div>
                  {/each}
                {/if}
              </div>
            </div>

            {#if testResults.alert_data?.triggered_conditions}
              <div class="result-item">
                <strong>Triggered Conditions:</strong>
                <ul class="condition-list">
                  {#each testResults.alert_data.triggered_conditions as cond}
                    <li>
                      {cond.metric || cond.field}: {cond.actual} {cond.operator} {cond.value}
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if testResults.alert_data?.rule_type}
              <div class="result-item">
                <strong>Rule Type:</strong>
                <span>{testResults.alert_data.rule_type}</span>
                {#if testResults.alert_data.logic_type}
                  <span>({testResults.alert_data.logic_type})</span>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- Tips -->
      <div class="section-card tips">
        <div class="section-header">
          <h2>💡 Tips</h2>
        </div>
        <ul>
          <li>Use ALL (AND) for strict thresholds</li>
          <li>Use ANY (OR) for flexible conditions</li>
          <li>Short cooldown prevents spam</li>
          <li>Test before saving</li>
          <li>Critical priority for urgent alerts</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<style>
  .builder-container {
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
  }

  .btn-secondary {
    background: white;
    color: #374151;
    border: 1px solid #e5e7eb;
  }

  .btn-secondary:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  .btn-primary {
    background: #3b82f6;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #2563eb;
  }

  .btn-primary:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .btn-test {
    background: #10b981;
    color: white;
  }

  .btn-test:hover:not(:disabled) {
    background: #059669;
  }

  .btn-test:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .content-grid {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 1.5rem;
  }

  .left-column {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .right-column {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .section-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .section-header h2 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .badge {
    background: #e5e7eb;
    color: #374151;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .badge.triggered {
    background: #fee2e2;
    color: #dc2626;
  }

  .badge.not-triggered {
    background: #dcfce7;
    color: #16a34a;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    display: block;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .input-field, .select-field, .textarea-field {
    width: 100%;
    padding: 0.625rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.9rem;
    background: white;
  }

  .input-field:focus, .select-field:focus, .textarea-field:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .textarea-field {
    resize: vertical;
    min-height: 60px;
  }

  .help-text {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: #6b7280;
  }

  /* Logic Toggle */
  .logic-toggle {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 6px;
  }

  .toggle-group {
    display: flex;
    gap: 0.25rem;
    background: white;
    border-radius: 6px;
    padding: 0.25rem;
    border: 1px solid #e5e7eb;
  }

  .toggle-btn {
    padding: 0.5rem 1rem;
    background: transparent;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.85rem;
    color: #6b7280;
    transition: all 0.2s;
  }

  .toggle-btn.active {
    background: #3b82f6;
    color: white;
  }

  /* Conditions List */
  .conditions-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .condition-row {
    display: grid;
    grid-template-columns: 30px 1fr 1fr 1fr 30px;
    gap: 0.5rem;
    align-items: start;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
  }

  .condition-number {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #3b82f6;
    color: white;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.85rem;
    width: 24px;
    height: 24px;
    margin-top: 1.75rem;
  }

  .btn-remove {
    width: 24px;
    height: 24px;
    border: none;
    background: #ef4444;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 700;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 1.75rem;
  }

  .btn-remove:hover {
    background: #dc2626;
  }

  .btn-add-condition {
    width: 100%;
    padding: 0.75rem;
    background: #10b981;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 0.5rem;
  }

  .btn-add-condition:hover {
    background: #059669;
  }

  /* Settings Grid */
  .settings-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  /* Actions List */
  .actions-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .action-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .action-item input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
  }

  .action-item label {
    margin: 0;
    cursor: pointer;
    font-weight: 500;
  }

  .action-detail {
    margin-left: 1.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  /* Action Buttons */
  .action-buttons {
    display: flex;
    gap: 0.75rem;
    margin-top: 0.5rem;
  }

  .action-buttons .btn {
    flex: 1;
  }

  /* Messages */
  .message {
    padding: 1rem;
    border-radius: 6px;
    margin-top: 1rem;
    font-weight: 500;
  }

  .message.success {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
  }

  .message.error {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
  }

  /* Preview */
  .preview-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .preview-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #f3f4f6;
  }

  .preview-item:last-child {
    border-bottom: none;
  }

  .preview-item strong {
    color: #374151;
    font-size: 0.85rem;
  }

  .preview-item span {
    color: #1f2937;
    font-weight: 500;
  }

  .condition-preview {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
  }

  .logic-operator {
    color: #3b82f6;
    font-weight: 700;
    margin: 0 0.25rem;
  }

  .priority-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .priority-0 { background: #fee2e2; color: #dc2626; }
  .priority-1 { background: #ffedd5; color: #ea580c; }
  .priority-2 { background: #fef3c7; color: #d97706; }
  .priority-3 { background: #dbeafe; color: #2563eb; }

  .empty-preview {
    text-align: center;
    color: #9ca3af;
    font-style: italic;
    padding: 2rem 0;
  }

  /* Test Results */
  .test-results {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .result-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .result-item strong {
    font-size: 0.9rem;
    color: #374151;
  }

  .metrics-display {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }

  .metric-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: #f9fafb;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  .metric-name {
    color: #6b7280;
    font-weight: 500;
  }

  .metric-value {
    color: #1f2937;
    font-weight: 700;
    font-family: 'Courier New', monospace;
  }

  .condition-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .condition-list li {
    background: #fef3c7;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  /* Tips */
  .tips ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .tips li {
    background: #eff6ff;
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    border-left: 3px solid #3b82f6;
    font-size: 0.85rem;
    color: #1e40af;
  }

  /* Responsive */
  @media (max-width: 1024px) {
    .content-grid {
      grid-template-columns: 1fr;
    }

    .settings-grid {
      grid-template-columns: 1fr;
    }

    .condition-row {
      grid-template-columns: 30px 1fr 1fr 1fr 30px;
    }
  }

  @media (max-width: 640px) {
    .builder-container {
      padding: 1rem;
    }

    .condition-row {
      grid-template-columns: 25px 1fr 25px;
      gap: 0.25rem;
    }

    .condition-row .form-group:nth-child(2),
    .condition-row .form-group:nth-child(3),
    .condition-row .form-group:nth-child(4) {
      grid-column: 1 / -1;
    }

    .action-buttons {
      flex-direction: column;
    }

    .metrics-display {
      grid-template-columns: 1fr;
    }
  }
</style>