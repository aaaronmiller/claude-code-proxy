<!-- LineChart.svelte - Reusable Chart.js line chart component -->
<script lang="ts">
  import { onMount, createEventDispatcher } from "svelte";
  import {
    Chart,
    LineController,
    LineElement,
    PointElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend,
  } from "chart.js";
  import type { Chart as ChartType } from "chart.js";

  // Register Chart.js components
  Chart.register(
    LineController,
    LineElement,
    PointElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend,
  );

  interface Dataset {
    label?: string;
    data: number[];
  }

  const dispatch = createEventDispatcher();

  export let labels: string[] = [];
  export let datasets: Dataset[] = [];
  export let title: string = "";
  export let height: string = "300px";
  export let showLegend: boolean = true;
  export let showTooltip: boolean = true;

  let canvas: HTMLCanvasElement | null = null;
  let chart: ChartType | null = null;
  let loading: boolean = false;

  // Colors for datasets
  const colors: string[] = [
    "rgba(59, 130, 246, 1)", // blue
    "rgba(16, 185, 129, 1)", // green
    "rgba(249, 115, 22, 1)", // orange
    "rgba(236, 72, 153, 1)", // pink
    "rgba(139, 92, 246, 1)", // purple
    "rgba(234, 179, 8, 1)", // yellow
  ];

  const bgColors: string[] = [
    "rgba(59, 130, 246, 0.1)",
    "rgba(16, 185, 129, 0.1)",
    "rgba(249, 115, 22, 0.1)",
    "rgba(236, 72, 153, 0.1)",
    "rgba(139, 92, 246, 0.1)",
    "rgba(234, 179, 8, 0.1)",
  ];

  function createChart(): void {
    if (!canvas || !labels || labels.length === 0) return;

    // Destroy existing chart
    if (chart) {
      chart.destroy();
    }

    // Prepare datasets with colors
    const chartDatasets = datasets.map((ds: Dataset, index: number) => ({
      label: ds.label || `Dataset ${index + 1}`,
      data: ds.data || [],
      borderColor: colors[index % colors.length],
      backgroundColor: bgColors[index % bgColors.length],
      borderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 5,
      tension: 0.3,
      fill: true,
    }));

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: chartDatasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: showLegend,
            position: "top",
            labels: {
              color:
                getComputedStyle(document.documentElement).getPropertyValue(
                  "--text-primary",
                ) || "#333",
              usePointStyle: true,
              padding: 15,
            },
          },
          tooltip: {
            enabled: showTooltip,
            mode: "index",
            intersect: false,
            backgroundColor: "rgba(17, 24, 39, 0.9)",
            titleColor: "#fff",
            bodyColor: "#fff",
            borderColor: "rgba(59, 130, 246, 1)",
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || "";
                if (label) {
                  label += ": ";
                }
                if (context.parsed.y !== null) {
                  label += context.parsed.y.toLocaleString();
                }
                return label;
              },
            },
          },
        },
        scales: {
          x: {
            display: true,
            grid: {
              display: false,
            },
            ticks: {
              color:
                getComputedStyle(document.documentElement).getPropertyValue(
                  "--text-secondary",
                ) || "#666",
            },
          },
          y: {
            display: true,
            grid: {
              color: "rgba(0, 0, 0, 0.05)",
            },
            ticks: {
              color:
                getComputedStyle(document.documentElement).getPropertyValue(
                  "--text-secondary",
                ) || "#666",
              callback: function (value) {
                return typeof value === "number"
                  ? value.toLocaleString()
                  : value;
              },
            },
          },
        },
        interaction: {
          mode: "nearest",
          axis: "x",
          intersect: false,
        },
      },
    });

    // Emit chart created event
    dispatch("chartCreated", { chart });
  }

  // Watch for data changes
  $: if (labels && datasets && canvas) {
    // Small delay to ensure DOM is ready
    setTimeout(() => {
      createChart();
    }, 10);
  }

  // Export chart methods
  export function getChart(): ChartType | null {
    return chart;
  }

  export function updateData(
    newLabels: string[],
    newDatasets: Dataset[],
  ): void {
    if (!chart) return;

    chart.data.labels = newLabels;
    chart.data.datasets = newDatasets.map((ds: Dataset, index: number) => ({
      ...chart!.data.datasets[index],
      data: ds.data || [],
      label: ds.label,
    }));
    chart.update("active");
  }

  export function exportChart(format: string = "png"): string | null {
    if (!chart) return null;

    if (format === "png") {
      return chart.toBase64Image();
    }
    return null;
  }

  onMount(() => {
    // Initialize chart when component mounts
    if (labels.length > 0 && datasets.length > 0) {
      createChart();
    }

    // Cleanup on destroy
    return () => {
      if (chart) {
        chart.destroy();
      }
    };
  });
</script>

<div class="chart-container" style="height: {height};">
  {#if loading}
    <div class="loading-overlay">
      <div class="spinner"></div>
    </div>
  {/if}

  {#if title}
    <div class="chart-title">{title}</div>
  {/if}

  {#if labels.length === 0 || datasets.length === 0}
    <div class="empty-state">
      <div class="empty-message">No data available</div>
      <div class="empty-hint">Select a date range to visualize metrics</div>
    </div>
  {:else}
    <canvas bind:this={canvas} aria-label={title || "Chart visualization"}
    ></canvas>
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

  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    z-index: 10;
  }

  .spinner {
    width: 24px;
    height: 24px;
    border: 3px solid var(--border-color, #e5e7eb);
    border-top-color: var(--primary, #3b82f6);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
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
    margin-bottom: 0.25rem;
  }

  .empty-hint {
    font-size: 0.875rem;
    opacity: 0.7;
  }
</style>
