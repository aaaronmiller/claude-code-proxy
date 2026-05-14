<script lang="ts">
	import { onMount } from "svelte";
	import {
		GripVertical,
		ChevronUp,
		ChevronDown,
		ToggleLeft,
		ToggleRight,
		Edit2,
		Trash2,
		Plus,
		X,
		Check
	} from "lucide-svelte";

	interface ChainEntry {
		id: string;
		name: string;
		url: string;
		auth_key: string;
		enabled: boolean;
		order: number;
		service_cmd: string;
		health_path: string;
		port: number;
		timeout: number;
		extra_headers: Record<string, string>;
		type: string;
		model_prefixes: string[];
	}

	let entries = $state<ChainEntry[]>([]);
	let loading = $state(false);
	let error = $state("");

	let editingId: string | null = null;
	let editDraft = $state<Partial<ChainEntry>>({});
	let addingNew = $state(false);
	let newEntry = $state<Partial<ChainEntry>>({
		id: "", name: "", url: "", auth_key: "", enabled: true,
		port: 0, service_cmd: "", health_path: "/health", timeout: 90,
		type: "http", extra_headers: {}, model_prefixes: []
	});

	let draggedId: string | null = null;

	async function fetchChain() {
		loading = true;
		error = "";
		try {
			const res = await fetch("/api/chain");
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const data = await res.json();
			// API returns array sorted by order already
			entries = data as ChainEntry[];
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function startAdd() {
		addingNew = true;
		newEntry = { id: "", name: "", url: "", auth_key: "", enabled: true, port: 0, service_cmd: "", health_path: "/health", timeout: 90, type: "http", extra_headers: {}, model_prefixes: [] };
	}

	function cancelAdd() {
		addingNew = false;
		newEntry = {};
	}

	async function addEntry() {
		if (!newEntry.id || !newEntry.name) {
			error = "ID and Name are required";
			return;
		}
		try {
			const payload = {
				id: newEntry.id!.trim(),
				name: newEntry.name!.trim(),
				url: (newEntry.url || "").trim(),
				enabled: !!newEntry.enabled,
				port: Number(newEntry.port) || 0,
				type: newEntry.type || "http",
				auth_key: (newEntry.auth_key || "").trim(),
				service_cmd: (newEntry.service_cmd || "").trim(),
				health_path: (newEntry.health_path || "/health").trim(),
				timeout: Number(newEntry.timeout) || 90,
				extra_headers: newEntry.extra_headers || {},
				model_prefixes: newEntry.model_prefixes || []
			};
			const resp = await fetch("/api/chain", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload)
			});
			if (!resp.ok) {
				const txt = await resp.text();
				throw new Error(txt || resp.statusText);
			}
			addingNew = false;
			await fetchChain();
		} catch (e: any) {
			error = `Add failed: ${e.message}`;
		}
	}

	function startEdit(entry: ChainEntry) {
		editingId = entry.id;
		editDraft = { ...entry };
	}

	function cancelEdit() {
		editingId = null;
		editDraft = {};
	}

	async function commitEdit() {
		if (!editingId) return;
		try {
			const payload: any = {};
			if ("name" in editDraft) payload.name = editDraft.name?.trim();
			if ("url" in editDraft) payload.url = (editDraft.url || "").trim();
			if ("enabled" in editDraft) payload.enabled = !!editDraft.enabled;
			if ("port" in editDraft) payload.port = Number(editDraft.port) || 0;
			if ("type" in editDraft) payload.type = editDraft.type;
			if ("auth_key" in editDraft) payload.auth_key = (editDraft.auth_key || "").trim();
			if ("service_cmd" in editDraft) payload.service_cmd = (editDraft.service_cmd || "").trim();
			if ("health_path" in editDraft) payload.health_path = (editDraft.health_path || "/health").trim();
			if ("timeout" in editDraft) payload.timeout = Number(editDraft.timeout) || 90;
			if ("extra_headers" in editDraft) payload.extra_headers = editDraft.extra_headers || {};
			if ("model_prefixes" in editDraft) payload.model_prefixes = editDraft.model_prefixes || [];

			const resp = await fetch(`/api/chain/${editingId}`, {
				method: "PATCH",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload)
			});
			if (!resp.ok) {
				const txt = await resp.text();
				throw new Error(txt || resp.statusText);
			}
			editingId = null;
			editDraft = {};
			await fetchChain();
		} catch (e: any) {
			error = `Update failed: ${e.message}`;
		}
	}

	async function confirmDelete(entry: ChainEntry) {
		if (!confirm(`Delete chain entry "${entry.name}"?`)) return;
		try {
			const resp = await fetch(`/api/chain/${entry.id}`, { method: "DELETE" });
			if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
			await fetchChain();
		} catch (e: any) {
			error = `Delete failed: ${e.message}`;
		}
	}

	// ── Toggle ────────────────────────────────────────────────────────────────────
	async function toggleEnabled(entry: ChainEntry) {
		try {
			const resp = await fetch(`/api/chain/${entry.id}`, {
				method: "PATCH",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ enabled: !entry.enabled })
			});
			if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
			await fetchChain();
		} catch (e: any) {
			error = `Toggle failed: ${e.message}`;
		}
	}

	// ── Move up / down ────────────────────────────────────────────────────────────
	async function moveUp(entry: ChainEntry) {
		const idx = entries.findIndex(e => e.id === entry.id);
		if (idx <= 0) return;
		const newOrder = entries.map(e => e.id);
		[newOrder[idx - 1], newOrder[idx]] = [newOrder[idx], newOrder[idx - 1]];
		await applyReorder(newOrder);
	}

	async function moveDown(entry: ChainEntry) {
		const idx = entries.findIndex(e => e.id === entry.id);
		if (idx === -1 || idx >= entries.length - 1) return;
		const newOrder = entries.map(e => e.id);
		[newOrder[idx], newOrder[idx + 1]] = [newOrder[idx + 1], newOrder[idx]];
		await applyReorder(newOrder);
	}

	async function applyReorder(order: string[]) {
		try {
			const resp = await fetch("/api/chain/reorder", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ order })
			});
			if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
			await fetchChain();
		} catch (e: any) {
			error = `Reorder failed: ${e.message}`;
		}
	}

	// ── Drag-and-drop (HTML5) ────────────────────────────────────────────────────
	function handleDragStart(e: DragEvent, entry: ChainEntry) {
		if (!e.dataTransfer) return;
		draggedId = entry.id;
		e.dataTransfer.effectAllowed = "move";
		// Set drag image feedback
		e.dataTransfer.setData("text/plain", entry.id);
	}

	function handleDragOver(e: Event) {
		e.preventDefault();
		if (!e.target) return;
		const t = e.target as HTMLElement;
		t.classList.add("drag-over");
	}

	function handleDragLeave(e: Event) {
		if (!e.target) return;
		const t = e.target as HTMLElement;
		t.classList.remove("drag-over");
	}

	async function handleDrop(e: DragEvent, targetEntry: ChainEntry) {
		e.preventDefault();
		if (!draggedId || draggedId === targetEntry.id) return;
		const draggedIdx = entries.findIndex(e => e.id === draggedId);
		const targetIdx = entries.findIndex(e => e.id === targetEntry.id);
		if (draggedIdx === -1 || targetIdx === -1) return;
		const newOrder = entries.map(e => e.id);
		// Remove dragged
		newOrder.splice(draggedIdx, 1);
		// Insert at target position
		newOrder.splice(targetIdx, 0, draggedId);
		await applyReorder(newOrder);
		draggedId = null;
	}

	onMount(fetchChain);
</script>

{#if error}
	<div class="error-toast">{error}</div>
{/if}

<div class="chain-list">
	{#if loading}
		<div class="status">Loading chain…</div>
	{:else if entries.length === 0}
		<div class="status empty">No chain entries configured.</div>
	{:else}
		<div class="header-row">
			<span class="col drag">↕</span>
			<span class="col name">Name</span>
			<span class="col type">Type</span>
			<span class="col url">URL / Mode</span>
			<span class="col status">Status</span>
			<span class="col actions">Actions</span>
		</div>

		{#each entries as entry (entry.id)}
			<div
				class="row"
				class:disabled={!entry.enabled}
				draggable="true"
				ondragstart={(e) => handleDragStart(e, entry)}
				ondragover={(e) => handleDragOver(e)}
				ondragleave={(e) => handleDragLeave(e)}
				ondrop={(e) => handleDrop(e, entry)}
			>
				<span class="col drag"><GripVertical size={16} /></span>
				<span class="col name">{entry.name}</span>
				<span class="col type">{entry.type === "cli_wrapper" ? "CLI" : "HTTP"}</span>
				<span class="col url">
					{entry.url ? (entry.url.length > 38 ? entry.url.slice(0, 38) + "…" : entry.url) : "(CLI wrapper)"}
				</span>
				<span class="col status">
					{#if entry.enabled}
						<span class="enabled"><ToggleRight size={18} class="ok" /> enabled</span>
					{:else}
						<span class="disabled-state"><ToggleLeft size={18} /> disabled</span>
					{/if}
				</span>
				<span class="col actions">
					<button class="icon-btn" onclick={() => moveUp(entry)} title="Move Up" disabled={entries[0].id === entry.id}>
						<ChevronUp size={14} />
					</button>
					<button class="icon-btn" onclick={() => moveDown(entry)} title="Move Down" disabled={entries[entries.length - 1].id === entry.id}>
						<ChevronDown size={14} />
					</button>
					<button class="icon-btn" onclick={() => toggleEnabled(entry)} title="Toggle Enabled">
						{#if entry.enabled}<ToggleRight size={16} class="text-green"/>{:else}<ToggleLeft size={16} />{/if}
					</button>
					<button class="icon-btn" onclick={() => startEdit(entry)} title="Edit">
						<Edit2 size={14} />
					</button>
					<button class="icon-btn danger" onclick={() => confirmDelete(entry)} title="Delete">
						<Trash2 size={14} />
					</button>
				</span>
			</div>
		{/each}
	{/if}

	{#if addingNew}
		<div class="add-form">
			<input bind:value={newEntry.id} placeholder="ID (slug)" />
			<input bind:value={newEntry.name} placeholder="Display name" />
			<select bind:value={newEntry.type}>
				<option value="http">HTTP</option>
				<option value="cli_wrapper">CLI wrapper</option>
			</select>
			<input bind:value={newEntry.url} placeholder="URL (blank for CLI)" />
			<input type="number" bind:value={newEntry.port} placeholder="Port" />
			<input bind:value={newEntry.service_cmd} placeholder="service_cmd (optional)" />
			<div class="form-actions">
				<button class="primary" onclick={addEntry}><Check size={14} /> Add</button>
				<button onclick={cancelAdd}><X size={14} /> Cancel</button>
			</div>
		</div>
	{/if}

	{#if editingId}
		<div class="edit-form">
			<h4>Edit Entry</h4>
			<div class="form-row">
				<label>Name <input bind:value={editDraft.name} /></label>
				<label>URL <input bind:value={editDraft.url} /></label>
				<label>Port <input type="number" bind:value={editDraft.port} /></label>
			</div>
			<div class="form-row">
				<label>Auth key <input bind:value={editDraft.auth_key} /></label>
				<label>Health path <input bind:value={editDraft.health_path} /></label>
				<label>Timeout (s) <input type="number" bind:value={editDraft.timeout} /></label>
			</div>
			<div class="form-row">
				<label class="grow">Service cmd <input bind:value={editDraft.service_cmd} /></label>
			</div>
			<div class="form-actions">
				<button class="primary" onclick={commitEdit}><Check size={14} /> Save</button>
				<button onclick={cancelEdit}><X size={14} /> Cancel</button>
			</div>
		</div>
	{/if}

	<div class="bottom-actions">
		<button class="btn-add" onclick={startAdd}><Plus size={14} /> Add Entry</button>
	</div>
</div>

<style>
	.chain-list {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.status {
		text-align: center;
		color: var(--text-tertiary);
		font-size: 0.85rem;
		padding: 2rem;
	}
	.status.empty {
		font-style: italic;
	}
	.error-toast {
		color: var(--error);
		font-size: 0.85rem;
		padding: 0.5rem 1rem;
		background: color-mix(in srgb, var(--error) 12%, transparent);
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}

	.header-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 600;
		font-size: 0.75rem;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0 0.5rem;
	}
	.row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		border: 1px solid var(--border-default);
		border-radius: 8px;
		background: var(--base-200);
		transition: background 0.12s, box-shadow 0.12s;
	}
	.row:hover {
		background: var(--base-300);
	}
	.row.drag-over {
		outline: 2px dashed var(--primary-default);
		background: color-mix(in srgb, var(--primary-default) 12%, transparent);
	}
	.row.disabled {
		opacity: 0.55;
	}

	.col {
		flex-shrink: 0;
	}
	.col.drag { width: 28px; display: flex; justify-content: center; color: var(--text-tertiary); cursor: grab; }
	.col.name { width: 180px; font-weight: 600; }
	.col.type { width: 80px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }
	.col.url { width: 240px; font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.col.status { flex: 1; font-size: 0.8rem; }
	.col.actions { display: flex; gap: 0.25rem; align-items: center; }

	.enabled { color: var(--success); display: flex; align-items: center; gap: 0.25rem; }
	.disabled-state { color: var(--text-tertiary); display: flex; align-items: center; gap: 0.25rem; }

	.icon-btn {
		display: flex; align-items: center; justify-content: center;
		width: 26px; height: 26px;
		background: transparent;
		border: none;
		border-radius: 5px;
		cursor: pointer;
		color: var(--text-tertiary);
	}
	.icon-btn:hover:not(:disabled) { background: var(--base-400); color: var(--text-primary); }
	.icon-btn:disabled { opacity: 0.2; cursor: not-allowed; }
	.icon-btn.danger:hover { color: var(--error); background: color-mix(in srgb, var(--error) 12%, transparent); }

	/* Add / Edit forms */
	.add-form, .edit-form {
		padding: 0.75rem 1rem;
		background: var(--base-300);
		border: 1px solid var(--border-strong);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	.add-form .form-row, .edit-form .form-row {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
	.add-form label, .edit-form label {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		font-size: 0.75rem;
		color: var(--text-secondary);
		flex: 1;
		min-width: 120px;
	}
	.add-form label.grow, .edit-form label.grow { flex: 2; }
	.add-form input, .add-form select,
	.edit-form input, .edit-form select {
		background: var(--base-200);
		border: 1px solid var(--border-strong);
		border-radius: 5px;
		padding: 0.3rem 0.5rem;
		font-size: 0.8rem;
		color: var(--text-primary);
		font-family: var(--font-mono);
	}
	.form-actions {
		display: flex;
		gap: 0.5rem;
		justify-content: flex-end;
		margin-top: 0.25rem;
	}
	.btn-add {
		display: flex; align-items: center; gap: 0.4rem;
		padding: 0.4rem 0.85rem;
		background: var(--primary-default);
		color: white;
		border: none;
		border-radius: 6px;
		font-weight: 600;
		cursor: pointer;
	}
	.btn-add:hover { background: var(--primary-vivid); }
</style>
