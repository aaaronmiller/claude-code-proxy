<script lang="ts">
	import { onMount } from "svelte";
	import { identifierMappings } from "$lib/stores/config-store";
	import type { IdentifierMapping } from "$lib/services/config-client";
	import { createIdentifierMapping, updateIdentifierMapping, deleteIdentifierMapping } from "$lib/services/config-client";

	let editing = $state<IdentifierMapping | null>(null);
	let creating = $state(false);
	let form = $state<Partial<IdentifierMapping>>({});
	let error = $state("");

	// Derive a sorted copy of mappings (by priority asc, then name)
	const sortedMappings = $derived(
		($identifierMappings ?? []).slice().sort((a, b) => a.priority - b.priority || a.incoming_identifier.localeCompare(b.incoming_identifier)),
	);

	function startCreate() {
		creating = true;
		editing = null;
		form = { enabled: true, priority: 0, notes: "" };
		error = "";
	}

	function startEdit(m: IdentifierMapping) {
		creating = false;
		editing = m;
		form = { ...m };
		error = "";
	}

	function cancelEdit() {
		creating = false;
		editing = null;
		form = {};
		error = "";
	}

	async function save() {
		error = "";
		if (!form.incoming_identifier?.trim() || !form.assignment_id?.trim()) {
			error = "Incoming identifier and assignment ID are required";
			return;
		}

		try {
			if (creating) {
				await createIdentifierMapping({
					incoming_identifier: form.incoming_identifier.trim(),
					assignment_id: form.assignment_id.trim(),
					enabled: form.enabled ?? true,
					priority: Number(form.priority) || 0,
					notes: form.notes ?? "",
				});
			} else if (editing) {
				await updateIdentifierMapping(editing.id, {
					incoming_identifier: form.incoming_identifier?.trim(),
					assignment_id: form.assignment_id?.trim(),
					enabled: form.enabled ?? true,
					priority: Number(form.priority) || 0,
					notes: form.notes ?? "",
				});
			}
			creating = false;
			editing = null;
			form = {};
		} catch (e: any) {
			error = e?.message ?? "Save failed";
		}
	}

	async function confirmDelete(m: IdentifierMapping) {
		if (!confirm(`Delete mapping for "${m.incoming_identifier}"?`)) return;
		await deleteIdentifierMapping(m.id);
	}

	async function moveUp(m: IdentifierMapping) {
		const idx = sortedMappings.findIndex((x) => x.id === m.id);
		if (idx <= 0) return;
		const other = sortedMappings[idx - 1];
		await swapPriorities(m, other);
	}

	async function moveDown(m: IdentifierMapping) {
		const idx = sortedMappings.findIndex((x) => x.id === m.id);
		if (idx >= sortedMappings.length - 1) return;
		const other = sortedMappings[idx + 1];
		await swapPriorities(m, other);
	}

	async function swapPriorities(a: IdentifierMapping, b: IdentifierMapping) {
		// Swap priorities via two PATCH calls
		await updateIdentifierMapping(a.id, { priority: b.priority });
		await updateIdentifierMapping(b.id, { priority: a.priority });
	}
</script>

<div class="table">
	{#if creating || editing}
		<div class="form-row">
			<input placeholder="Incoming" bind:value={form.incoming_identifier} />
			<input placeholder="Assignment ID" bind:value={form.assignment_id} />
			<input type="number" placeholder="Pri" bind:value={form.priority} style="width: 60px" />
			<label><input type="checkbox" bind:checked={form.enabled} /> Enabled</label>
			<input placeholder="Notes" bind:value={form.notes} />
			<button class="primary" onclick={save}>Save</button>
			<button onclick={cancelEdit}>Cancel</button>
		</div>
		{#if error}<div class="error">{error}</div>{/if}
	{/if}

	{#each sortedMappings as m (m.id)}
		<div class="row">
			<span class="col identifier">{m.incoming_identifier}</span>
			<span class="col assignment">{m.assignment_id}</span>
			<span class="col pri">{m.priority}</span>
			<span class="col enabled">{m.enabled ? "✓" : "✗"}</span>
			<div class="col actions">
				<button onclick={() => moveUp(m)} title="Move Up">↑</button>
				<button onclick={() => moveDown(m)} title="Move Down">↓</button>
				<button onclick={() => startEdit(m)} title="Edit">✎</button>
				<button onclick={() => confirmDelete(m)} title="Delete">🗑</button>
			</div>
		</div>
	{:else}
		<div class="empty">No identifier mappings — create one to get started.</div>
	{/each}
</div>

<button class="fab" onclick={startCreate}>+ New Mapping</button>

<style>
	.table {
		padding: 1rem;
	}
	.row,
	.form-row {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		padding: 0.375rem 0;
		border-bottom: 1px solid var(--color-border);
	}
	.form-row {
		background: var(--color-surface-alt);
		padding: 0.5rem;
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}
	.col {
		flex-shrink: 0;
	}
	.col.identifier {
		width: 200px;
		font-family: var(--font-mono);
	}
	.col.assignment {
		width: 140px;
		font-family: var(--font-mono);
	}
	.col.pri {
		width: 50px;
		text-align: center;
	}
	.col.enabled {
		width: 50px;
		text-align: center;
	}
	.col.actions {
		margin-left: auto;
		display: flex;
		gap: 0.25rem;
	}
	input {
		padding: 0.25rem 0.375rem;
		border: 1px solid var(--color-border);
		border-radius: 4px;
		font-size: 0.8125rem;
		background: var(--color-surface);
		color: var(--color-text);
	}
	button {
		padding: 0.25rem 0.5rem;
		border: 1px solid var(--color-border);
		border-radius: 4px;
		background: var(--color-surface);
		cursor: pointer;
		font-size: 0.8125rem;
	}
	button.primary {
		background: var(--color-primary);
		color: var(--color-on-primary);
		border-color: var(--color-primary);
	}
	button:hover {
		opacity: 0.85;
	}
	.error {
		color: var(--color-error);
		font-size: 0.8125rem;
		margin-top: 0.25rem;
	}
	.empty {
		color: var(--color-text-muted);
		font-style: italic;
		padding: 1rem;
		text-align: center;
	}
	.fab {
		position: fixed;
		bottom: 1.5rem;
		right: 1.5rem;
		padding: 0.625rem 1rem;
		border-radius: 999px;
		background: var(--color-primary);
		color: var(--color-on-primary);
		border: none;
		font-weight: 600;
		box-shadow: var(--shadow-2);
	}
</style>
