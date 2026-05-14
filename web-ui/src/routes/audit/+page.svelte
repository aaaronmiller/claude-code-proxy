<script lang="ts">
	import { onMount } from "svelte";
	import type { AuditEntry } from "$lib/services/audit-client";
	import { listAuditEntries } from "$lib/services/audit-client";

	let entries = $state<AuditEntry[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Filters
	let since = $state("");
	let principalFilter = $state("");
	let fieldPathFilter = $state("");
	let limit = $state(100);

	async function load() {
		loading = true;
		error = null;
		try {
			const params: any = { limit };
			if (since) params.since = since;
			if (principalFilter) params.principal = principalFilter;
			if (fieldPathFilter) params.field_path = fieldPathFilter;
			entries = await listAuditEntries(params);
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		load();
	});

	function formatDate(ts: string): string {
		const d = new Date(ts);
		return d.toLocaleString();
	}
</script>

<div class="page">
	<h1>Audit Log</h1>
	<p class="desc">
		Configuration change history (admin only). Filters below are ANDed.
	</p>

	<div class="filters">
		<div class="row">
			<label>
				Since (ISO-8601)
				<input type="text" bind:value={since} placeholder="2026-04-25T00:00:00Z" />
			</label>
			<label>
				Principal
				<input type="text" bind:value={principalFilter} placeholder="username" />
			</label>
			<label>
				Field Path
				<input type="text" bind:value={fieldPathFilter} placeholder="assignments.big.model" />
			</label>
			<label>
				Limit
				<input type="number" bind:value={limit} min="1" max="1000" />
			</label>
			<button on:click={load} disabled={loading}>Refresh</button>
		</div>
	</div>

	{#if loading}
		<p>Loading…</p>
	{:else if error}
		<p class="error">Error: {error}</p>
	{:else}
		<table>
			<thead>
				<tr>
					<th>Seq</th>
					<th>Time</th>
					<th>Principal</th>
					<th>Surface</th>
					<th>Field</th>
					<th>Before</th>
					<th>After</th>
				</tr>
			</thead>
			<tbody>
				{#each entries as e (e.seq)}
					<tr>
						<td class="seq">{e.seq}</td>
						<td class="time" title={e.timestamp}>{formatDate(e.timestamp)}</td>
						<td class="principal">{e.principal}</td>
						<td class="surface">{e.surface}</td>
						<td class="field"><code>{e.field_path}</code></td>
						<td class="val">{e.before_value}</td>
						<td class="val">{e.after_value}</td>
					</tr>
				{:else}
					<tr>
						<td colspan="7" class="empty">No audit entries match the filters.</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>

<style>
	.page {
		padding: 1.5rem;
		max-width: 1200px;
		margin: 0 auto;
	}
	h1 {
		margin: 0 0 0.5rem 0;
		font-size: 1.75rem;
	}
	.desc {
		color: var(--color-text-muted);
		margin-bottom: 1rem;
	}
	.filters {
		margin-bottom: 1.5rem;
	}
	.row {
		display: flex;
		gap: 0.75rem;
		align-items: flex-end;
		flex-wrap: wrap;
	}
	label {
		display: flex;
		flex-direction: column;
		font-size: 0.875rem;
		gap: 0.25rem;
	}
	input {
		padding: 0.375rem 0.5rem;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		min-width: 180px;
	}
	button {
		padding: 0.375rem 0.75rem;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		background: var(--color-surface);
		border-radius: 8px;
		overflow: hidden;
	}
	thead {
		background: var(--color-surface-alt);
	}
	th,
	td {
		padding: 0.5rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid var(--color-border);
		vertical-align: top;
	}
	td.seq {
		width: 3rem;
		font-family: var(--font-mono);
		color: var(--color-text-muted);
	}
	td.time {
		width: 10rem;
		font-size: 0.875rem;
		color: var(--color-text-muted);
	}
	td.principal {
		width: 8rem;
	}
	td.surface {
		width: 6rem;
		font-size: 0.8125rem;
	}
	td.field code {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		background: var(--color-surface-alt);
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
	}
	td.val {
		max-width: 250px;
		word-break: break-all;
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--color-text-muted);
	}
	.empty {
		text-align: center;
		color: var(--color-text-muted);
		padding: 2rem !important;
	}
	.error {
		color: var(--color-error);
	}
</style>
