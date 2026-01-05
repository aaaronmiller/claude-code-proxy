<!-- BarChart.svelte - Reusable Chart.js bar chart component -->
<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';

  // Register Chart.js components
  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

  const dispatch = createEventDispatcher();

  export let labels = [];
  export let datasets = [];
  export let title = '';
  export let height = '300px';
  export let showLegend = true;
  export let horizontal = false;
  export let stacked = false;

  let canvas;
  let chart;

  // Colors for datasets
  const colors = [
    'rgba(59, 130, 246, 0.8)',   // blue
    'rgba(16, 185, 129, 0.8)',   // green
    'rgba(249, 115, 22, 0.8)',   // orange
    'rgba(236, 72, 153, 0.8)',   // pink
    'rgba(139, 92, 246, 0.8)',   // purple
    'rgba(234, 179, 8, 0.8)'     // yellow
  ];

  const borderColors = [
    'rgba(59, 130, 246, 1)',
    'rgba(16, 185, 129, 1)',
    'rgba(249, 115, 22, 1)',
    'rgba(236, 72, 153, 1)',
    'rgba(139, 92, 246, 1)',
    'rgba(234, 179, 8, 1)'
  ];

  function createChart() {
    if (!canvas || !labels || labels.length === 0) return;

    if (chart) {
      chart.destroy();
    }

    const chartDatasets = datasets.map((ds, index) => ({
      label: ds.label || `Dataset ${index + 1}`,
      data: ds.data || [],
      backgroundColor: colors[index % colors.length],
      borderColor: borderColors[index % borderColors.length],
      borderWidth: 1,
      borderRadius: 4,
      maxBarThickness: 40
    }));

    const ctx = canvas.getContext('2d');

    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: chartDatasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: horizontal ? 'y' : 'x',
        plugins: {
          legend: {
            display: showLegend,
            position: 'top',
            labels: {
              color: '#333',
              usePointStyle: true,
              padding: 15
            }
          },
          tooltip: {
            enabled: true,
            backgroundColor: 'rgba(17, 24, 39, 0.9)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                if (context.parsed.y !== null) {
                  label += context.parsed.y.toLocaleString();
                }
                return label;
              }
            }
          }
        },
        scales: {
          x: {
            display: !horizontal,
            stacked: stacked,
            grid: {
              display: false
            },
            ticks: {
              color: '#666'
            }
          },
          y: {
            display: !horizontal || stacked,
            stacked: stacked,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              color: '#666',
              callback: function(value) {
                return value.toLocaleString();
              }
            }
          }
        }
      }
    });

    dispatch('chartCreated', { chart });
  }

  $: if (labels && datasets && canvas) {
    setTimeout(() => createChart(), 10);
  }

  export function getChart() {
    return chart;
  }

  export function exportChart(format = 'png') {
    if (!chart) return null;
    if (format === 'png') {
      return chart.toBase64Image();
    }
    return null;
  }

  onMount(() => {
    if (labels.length > 0 && datasets.length > 0) {
      createChart();
    }

    return () => {
      if (chart) {
        chart.destroy();
      }
    };
  });
</script>

<div class="chart-container" style="height: {height};">
  {#if title}
    <div class="chart-title">{title}</div>
  {/if}

  {#if labels.length === 0 || datasets.length === 0}
    <div class="empty-state">
      <div class="empty-message">No data available</div>
    </div>
  {:else}
    <canvas bind:this={canvas} aria-label={title || 'Bar chart'} role="img"></canvas>
  {/if}
</div>

<style>
  .chart-container {
    position: relative;
    width: 100%;
    background: var(--bg-card, #ffffff);
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .chart-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary, #1f2937);
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color, #e5e7eb);
  }

  canvas {
    width: 100% !important;
    height: 100% !important;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 200px;
    color: var(--text-secondary, #6b7280);
  }

  .empty-message {
    font-size: 1rem;
    font-weight: 500;
  }
</style>