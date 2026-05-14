<script lang="ts">
	import { onMount } from "svelte";
	import { assignments, initConfigStore } from "$lib/stores/config-store";
	import AssignmentEditor from "../../components/AssignmentEditor.svelte";
	import type { Assignment } from "$lib/services/config-client";
	import { deleteAssignment } from "$lib/services/config-client";

	onMount(() => {
		initConfigStore();
	});

	let showEditor = $state(false);
	let editing = $state<Assignment | null>(null);

	function startCreate() {
		editing = null;
		showEditor = true;
	}

	function startEdit(a: Assignment) {
		editing = a;
		showEditor = true;
	}

	async function remove(a: Assignment) {
		if (!confirm(`Delete assignment "${a.id}"?`)) return;
		await deleteAssignment(a.id);
	}

	function saved() {
		showEditor = false;
		editing = null;
	}
</script>

<svelte:head>
	<title>Assignments — Claude Code Proxy</title>
</svelte:head>

<div class="page">
	<h1>Assignments</h1>
	<p class="desc">
		Assignments define which model provider handles a given tier (big/middle/small)
		or slot (custom name). Changes take effect immediately.
	</p>

	<button class="primary" on:click={startCreate}>+ New Assignment</button>

	<table>
		<thead>
			<tr>
				<th>ID</th>
				<th>Kind</th>
				<th>Model</th>
				<th>Provider</th>
				<th>Base URL</th>
				<th>Enabled</th>
				<th>Actions</th>
			</tr>
		</thead>
	<tbody>
		{#each $assignments as a (a.id)}
			<tr>
				<td><code>{a.id}</code></td>
				<td>{a.kind}</td>
				<td>{a.model}</td>
				<td>{a.provider}</td>
				<td class="url">{a.base_url}</td>
				<td>{a.enabled ? "✓" : "✗"}</td>
				<td class="actions">
					<button class="sm" on:click={() => startEdit(a)}>Edit</button>
					<button class="danger" on:click={() => remove(a)}>Delete</button>
				</td>
			</tr>
		{:else}
			<tr>
				<td colspan="7" class="empty">No assignments configured yet.</td>
			</tr>
		{/each}
	</tbody>
	</table>
</div>

{#if showEditor}
	<div class="modal-backdrop" on:click={() => (showEditor = false)}>
		<div class="modal" on:click|stopPropagation>
			<AssignmentEditor assignment={editing} onSaved={saved} onCancelled={() => (showEditor = false)} />
		</div>
	</div>
{/if}

<style>
	.page {
		padding: 1.5rem;
		max-width: 1000px;
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
	button.primary {
		margin-bottom: 1rem;
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
	}
	code {
		font-family: var(--font-mono);
		font-size: 0.875rem;
		background: var(--color-surface-alt);
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
	}
	.url {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--color-text-muted);
		max-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.actions {
		display: flex;
		gap: 0.375rem;
	}
	button.sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.8125rem;
	}
	button.danger {
		background: var(--color-error);
		color: var(--color-on-error);
		border-color: var(--color-error);
	}
	.empty {
		text-align: center;
		color: var(--color-text-muted);
		padding: 2rem !important;
	}
	/* Modal */
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}
	.modal {
		background: var(--color-surface);
		border-radius: 8px;
		padding: 1.5rem;
		min-width: 320px;
		max-width: 480px;
		box-shadow: var(--shadow-3);
	}
</style>
