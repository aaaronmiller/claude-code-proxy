<script lang="ts">
	/** ProvenanceBadge — inline badge showing which config layer supplied a value.
	 *
	 * Color coding per spec (T067):
	 *   cli        → yellow
	 *   shell_env  → blue
	 *   dotenv     → cyan
	 *   stored     → green
	 *   default    → gray
	 *
	 * Clicking opens a tooltip with raw_value and layer details.
	 *
	 * Usage:
	 *   <ProvenanceBadge {source_layer} {raw_value} {field_path} />
	 */

	export let source_layer: string;
	export let raw_value: any = null;
	export let field_path: string = "";

	let show_tooltip: boolean = false;

	function getBadgeClass(): string {
		switch (source_layer) {
			case "cli":
				return "badge badge-yellow";
			case "shell_env":
				return "badge badge-blue";
			case "dotenv":
				return "badge badge-cyan";
			case "stored":
				return "badge badge-green";
			case "default":
				return "badge badge-gray";
			default:
				return "badge badge-gray";
		}
	}

	function toggleTooltip() {
		show_tooltip = !show_tooltip;
	}
</script>

<span class="provenance-wrapper">
	<span class={getBadgeClass()} on:click={toggleTooltip} on:keydown={(e)=>{ if(e.key==='Enter'||e.key===' ') toggleTooltip(); }} role="button" tabindex="0" title="Click for provenance details">
		{source_layer}
	</span>

	{#if show_tooltip}
		<div class="tooltip" on:click={() => show_tooltip = false} on:keydown={(e)=>{ if(e.key==='Escape') show_tooltip=false; }}>
			<strong>Provenance</strong><br />
			Field: <code>{field_path}</code><br />
			Raw value: <pre class="raw-value">{JSON.stringify(raw_value, null, 2)}</pre>
			<em>Source layer: {source_layer}</em>
		</div>
	{/if}
</span>

<style>
	.provenance-wrapper {
		position: relative;
		display: inline-flex;
		vertical-align: middle;
	}

	.badge {
		display: inline-block;
		padding: 0.15rem 0.5rem;
		border-radius: 9999px;
		font-size: 0.7rem;
		font-weight: 600;
		cursor: pointer;
		user-select: none;
		line-height: 1;
	}

	.badge-yellow {
		background-color: #fef3c7;
		color: #92400e;
		border: 1px solid #f59e0b;
	}

	.badge-blue {
		background-color: #dbeafe;
		color: #1e40af;
		border: 1px solid #3b82f6;
	}

	.badge-cyan {
		background-color: #cffafe;
		color: #155e75;
		border: 1px solid #06b6d4;
	}

	.badge-green {
		background-color: #d1fae5;
		color: #065f46;
		border: 1px solid #10b981;
	}

	.badge-gray {
		background-color: #f3f4f6;
		color: #374151;
		border: 1px solid #9ca3af;
	}

	.tooltip {
		position: absolute;
		top: 100%;
		left: 0;
		margin-top: 0.5rem;
		padding: 0.75rem;
		background: var(--color-surface, #1e1e1e);
		border: 1px solid var(--color-border, #444);
		border-radius: 0.5rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
		z-index: 100;
		min-width: 200px;
		max-width: 320px;
		font-size: 0.8rem;
		color: var(--color-text, #eee);
	}

	.tooltip::before {
		content: "";
		position: absolute;
		top: -6px;
		left: 12px;
		width: 12px;
		height: 12px;
		background: var(--color-surface, #1e1e1e);
		border-top: 1px solid var(--color-border, #444);
		border-left: 1px solid var(--color-border, #444);
		transform: rotate(45deg);
	}

	.raw-value {
		background: rgba(0, 0, 0, 0.2);
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		margin-top: 0.25rem;
		margin-bottom: 0.25rem;
		font-family: monospace;
		font-size: 0.75rem;
		white-space: pre-wrap;
		word-break: break-all;
		max-height: 80px;
		overflow: auto;
	}
</style>
