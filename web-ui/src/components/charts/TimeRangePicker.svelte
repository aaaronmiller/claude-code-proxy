<!-- TimeRangePicker.svelte - Date range selection for analytics -->
<script>
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  // Props
  export let startDate = '';
  export let endDate = '';
  export let presets = [
    { label: 'Last 24 Hours', days: 1 },
    { label: 'Last 7 Days', days: 7 },
    { label: 'Last 30 Days', days: 30 },
    { label: 'Last 90 Days', days: 90 }
  ];

  // Local state
  let showCustom = false;
  let tempStart = startDate;
  let tempEnd = endDate;

  // Format date for input
  function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  // Get preset date range
  function getPresetDate(days) {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - days);
    return {
      start: formatDate(start),
      end: formatDate(end)
    };
  }

  // Handle preset selection
  function selectPreset(days) {
    const { start, end } = getPresetDate(days);
    startDate = start;
    endDate = end;
    tempStart = start;
    tempEnd = end;
    showCustom = false;
    dispatch('change', { start: startDate, end: endDate });
  }

  // Handle custom date apply
  function applyCustom() {
    if (tempStart && tempEnd) {
      // Validate dates
      if (new Date(tempStart) <= new Date(tempEnd)) {
        startDate = tempStart;
        endDate = tempEnd;
        showCustom = false;
        dispatch('change', { start: startDate, end: endDate });
      } else {
        alert('End date must be after start date');
      }
    }
  }

  // Reset to today
  function resetToToday() {
    const today = formatDate(new Date());
    startDate = today;
    endDate = today;
    tempStart = today;
    tempEnd = today;
    showCustom = false;
    dispatch('change', { start: startDate, end: endDate });
  }

  // Toggle custom date picker
  function toggleCustom() {
    showCustom = !showCustom;
    if (showCustom) {
      tempStart = startDate;
      tempEnd = endDate;
    }
  }

  // Export methods
  export function getRange() {
    return { start: startDate, end: endDate };
  }

  export function setRange(start, end) {
    startDate = start;
    endDate = end;
    tempStart = start;
    tempEnd = end;
    dispatch('change', { start: startDate, end: endDate });
  }

  // Initialize with default if not provided
  if (!startDate || !endDate) {
    const { start, end } = getPresetDate(7);
    startDate = start;
    endDate = end;
  }
</script>

<div class="time-range-picker">
  <!-- Preset Buttons -->
  <div class="presets">
    <button
      class="preset-btn"
      on:click={() => resetToToday()}
      class:active={startDate === formatDate(new Date()) && endDate === formatDate(new Date())}
    >
      Today
    </button>

    {#each presets as preset}
      <button
        class="preset-btn"
        on:click={() => selectPreset(preset.days)}
        class:active={false}
      >
        {preset.label}
      </button>
    {/each}

    <button
      class="preset-btn {showCustom ? 'active' : ''}"
      on:click={toggleCustom}
    >
      Custom
    </button>
  </div>

  <!-- Current Selection Display -->
  <div class="current-selection">
    <span class="label">Selected:</span>
    <span class="date-range">
      {new Date(startDate).toLocaleDateString()} - {new Date(endDate).toLocaleDateString()}
    </span>
  </div>

  <!-- Custom Date Picker (collapsible) -->
  {#if showCustom}
    <div class="custom-picker" transition:slide|local={{ duration: 300 }}>
      <div class="date-inputs">
        <div class="input-group">
          <label for="start-date">Start Date</label>
          <input
            type="date"
            id="start-date"
            bind:value={tempStart}
            max={tempEnd || formatDate(new Date())}
          />
        </div>

        <div class="input-group">
          <label for="end-date">End Date</label>
          <input
            type="date"
            id="end-date"
            bind:value={tempEnd}
            max={formatDate(new Date())}
          />
        </div>
      </div>

      <div class="actions">
        <button class="btn btn-secondary" on:click={() => showCustom = false}>
          Cancel
        </button>
        <button class="btn btn-primary" on:click={applyCustom}>
          Apply Range
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .time-range-picker {
    background: var(--bg-card, #ffffff);
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--border-color, #e5e7eb);
  }

  .presets {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .preset-btn {
    padding: 0.5rem 1rem;
    background: var(--bg-secondary, #f3f4f6);
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary, #374151);
    cursor: pointer;
    transition: all 0.2s;
  }

  .preset-btn:hover {
    background: var(--bg-tertiary, #e5e7eb);
    border-color: var(--border-hover, #9ca3af);
  }

  .preset-btn.active {
    background: var(--primary, #3b82f6);
    color: white;
    border-color: var(--primary, #3b82f6);
  }

  .current-selection {
    padding: 0.75rem;
    background: var(--bg-secondary, #f3f4f6);
    border-radius: 6px;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .label {
    font-weight: 600;
    color: var(--text-secondary, #6b7280);
  }

  .date-range {
    color: var(--text-primary, #1f2937);
    font-weight: 500;
  }

  .custom-picker {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color, #e5e7eb);
  }

  .date-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .input-group label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary, #6b7280);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .input-group input {
    padding: 0.5rem;
    border: 1px solid var(--border-color, #e5e7eb);
    border-radius: 6px;
    font-size: 0.875rem;
    background: white;
  }

  .input-group input:focus {
    outline: none;
    border-color: var(--primary, #3b82f6);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }

  .btn {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn-primary {
    background: var(--primary, #3b82f6);
    color: white;
  }

  .btn-primary:hover {
    background: #2563eb;
  }

  .btn-secondary {
    background: var(--bg-secondary, #f3f4f6);
    color: var(--text-primary, #374151);
    border: 1px solid var(--border-color, #e5e7eb);
  }

  .btn-secondary:hover {
    background: var(--bg-tertiary, #e5e7eb);
  }

  /* Animations */
  .custom-picker {
    overflow: hidden;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .custom-picker {
    animation: slideDown 0.3s ease-out;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .presets {
      flex-wrap: wrap;
    }

    .preset-btn {
      font-size: 0.8rem;
      padding: 0.4rem 0.8rem;
    }

    .date-inputs {
      grid-template-columns: 1fr;
    }

    .actions {
      flex-direction: column;
    }

    .btn {
      width: 100%;
    }
  }
</style>

<!-- Add slide transition -->
<script>
  function slide(node, { duration = 300 } = {}) {
    return {
      duration,
      css: (t) => `
        opacity: ${t};
        transform: translateY(${(1 - t) * -10}px);
      `
    };
  }
</script>