<script lang="ts">
    import { Svg, Chart, Axis, Line, Tooltip, ResponsiveContainer } from 'layerchart';
    import { scaleLinear } from 'd3-scale';
    
    interface DataPoint {
        date: Date;
        value: number;
    }
    
    interface Props {
        data?: DataPoint[];
        height?: string;
        showAxis?: boolean;
        color?: string;
    }
    
    let { data = [], height = '200px', showAxis = true, color }: Props = $props();
    
    let chartData = $derived(
        data.map(d => ({ ...d, date: new Date(d.date) }))
    );
    
    let chartColor = $derived(color || 'var(--accent-default)');
</script>

<div class="chart-wrapper" style="height: {height}">
    {#if data.length === 0}
        <div class="empty-state">
            <span style="color: var(--text-secondary)">No data available</span>
        </div>
    {:else}
        <Chart
            data={chartData}
            x="date"
            y="value"
            xScale={scaleLinear()}
            yScale={scaleLinear()}
            padding={{ top: 10, right: 10, bottom: showAxis ? 30 : 10, left: showAxis ? 40 : 10 }}
            let:xScale
            let:yScale
        >
            <Svg>
                <Line
                    x={xScale}
                    y={yScale}
                    stroke={chartColor}
                    strokeWidth={2}
                    curve="curveMonotoneX"
                    class="chart-line"
                />
            </Svg>
            
            {#if showAxis}
                <Axis axis="x" format={(d) => d.toLocaleDateString()} />
                <Axis axis="y" />
            {/if}
            
            <Tooltip>
                {#snippet children({ datum })}
                    <div class="tooltip-content">
                        <span style="color: var(--text-primary)">
                            {datum.date.toLocaleDateString()}
                        </span>
                        <span style="color: {chartColor}; font-weight: 600">
                            {datum.value.toLocaleString()}
                        </span>
                    </div>
                {/snippet}
            </Tooltip>
        </Chart>
    {/if}
</div>

<style>
    .chart-wrapper {
        width: 100%;
        position: relative;
    }
    
    .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
    
    :global(.chart-line) {
        filter: drop-shadow(0 0 4px var(--glow-color, currentColor));
    }
    
    .tooltip-content {
        display: flex;
        flex-direction: column;
        gap: 2px;
        padding: 8px;
        background: var(--base-300);
        border: 1px solid var(--border-strong);
        border-radius: 6px;
        font-size: 12px;
    }
</style>
