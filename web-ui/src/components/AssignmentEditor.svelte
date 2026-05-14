<script lang="ts">
	import { onMount } from "svelte";
	import type { Assignment } from "$lib/services/config-client";
	import { createAssignment, updateAssignment } from "$lib/services/config-client";
	import ProvenanceBadge from "./ProvenanceBadge.svelte";

	interface Props {
		assignment: Assignment | null; // null indicates creation mode
		onSaved?: () => void;
		onCancelled?: () => void;
	}

	let { assignment = null, onSaved, onCancelled }: Props = $props();

	// Form state — initialise with assignment or blanks
	let id = $state(assignment?.id ?? "");
	let kind = $state<"tier" | "slot">(assignment?.kind ?? "tier");
	let model = $state(assignment?.model ?? "");
	let provider = $state(assignment?.provider ?? "");
	let base_url = $state(assignment?.base_url ?? "");
	let api_key = $state(assignment?.api_key ?? "");
	let enabled = $state(assignment?.enabled ?? true);
	let cascade = $state(assignment?.cascade ?? []);

	let error = $state("");

	// Provenance cache (T068): { field_name: { source_layer, raw_value } }
	let provenance = $state<Record<string, { source_layer: string; raw_value: any }>>({});

	async function fetchProvenance() {
		if (!assignment) return;
		const fields = ["model", "provider", "base_url", "api_key", "enabled"];
		const results: typeof provenance = {};
		await Promise.all(
			fields.map(async (f) => {
				try {
					const resp = await fetch(`/api/config/assignments.${assignment.id}.${f}`);
					if (resp.ok) {
						const data = await resp.json();
						results[f] = {
							source_layer: data.source_layer,
							raw_value: data.raw_value,
						};
					}
				} catch {
					// silently ignore — badge just won't show
				}
			})
		);
		provenance = results;
	}

	onMount(fetchProvenance);

	async function save() {
		error = "";
		if (!id.trim()) {
			error = "ID is required";
			return;
		}

		const payload = {
			id: id.trim(),
			kind,
			model: model.trim(),
			provider: provider.trim(),
			base_url: base_url.trim(),
			api_key: api_key.trim(),
			enabled,
			cascade,
		};

		try {
			if (assignment) {
				await updateAssignment(assignment.id, payload);
			} else {
				// create expects id to be set
				const { id: _, ...createPayload } = payload;
				await createAssignment(createPayload);
			}
			onSaved?.();
		} catch (e: any) {
			error = e?.message ?? "Save failed";
		}
	}

	function cancel() {
		onCancelled?.();
	}
</script>

<div class="editor">
	<h2>{assignment ? "Edit Assignment" : "New Assignment"}</h2>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	<div class="field">
		<label for="id">ID (slot/tier name, lowercase)</label>
		<input id="id" bind:value={id} disabled={!!assignment} placeholder="e.g. big, my_slot" />
	</div>

	<div class="field">
		<label for="kind">Kind</label>
		<select id="kind" bind:value={kind} disabled={!!assignment}>
			<option value="tier">tier</option>
			<option value="slot">slot</option>
		</select>
	</div>

	<div class="field">
		<label for="model">
			Model
			{#if provenance.model}
				<ProvenanceBadge
					source_layer={provenance.model.source_layer}
					raw_value={provenance.model.raw_value}
					field_path={`assignments.${id}.model`}
				/>
			{/if}
		</label>
		<input id="model" bind:value={model} placeholder="openai/gpt-4" />
	</div>

	<div class="field">
		<label for="provider">
			Provider
			{#if provenance.provider}
				<ProvenanceBadge
					source_layer={provenance.provider.source_layer}
					raw_value={provenance.provider.raw_value}
					field_path={`assignments.${id}.provider`}
				/>
			{/if}
		</label>
		<input id="provider" bind:value={provider} placeholder="openai" />
	</div>

	<div class="field">
		<label for="base_url">
			Base URL
			{#if provenance.base_url}
				<ProvenanceBadge
					source_layer={provenance.base_url.source_layer}
					raw_value={provenance.base_url.raw_value}
					field_path={`assignments.${id}.base_url`}
				/>
			{/if}
		</label>
		<input id="base_url" bind:value={base_url} placeholder="https://api.openai.com/v1" />
	</div>

	<div class="field">
		<label for="api_key">
			API Key
			{#if provenance.api_key}
				<ProvenanceBadge
					source_layer={provenance.api_key.source_layer}
					raw_value={provenance.api_key.raw_value}
					field_path={`assignments.${id}.api_key`}
				/>
			{/if}
		</label>
		<input id="api_key" type="password" bind:value={api_key} />
	</div>

	<div class="field checkbox">
		<input id="enabled" type="checkbox" bind:checked={enabled} />
		<label for="enabled">
			Enabled
			{#if provenance.enabled}
				<ProvenanceBadge
					source_layer={provenance.enabled.source_layer}
					raw_value={provenance.enabled.raw_value}
					field_path={`assignments.${id}.enabled`}
				/>
			{/if}
		</label>
	</div>

	<div class="actions">
		<button class="primary" onclick={save}>Save</button>
		<button onclick={cancel}>Cancel</button>
	</div>
</div>

<style>
	.editor {
		max-width: 480px;
		margin: 0 auto;
		padding: 1rem;
	}
	h2 {
		margin: 0 0 1rem 0;
		font-size: 1.25rem;
	}
	.field {
		margin-bottom: 0.75rem;
	}
	label {
		display: block;
		font-size: 0.875rem;
		color: var(--color-text-muted);
		margin-bottom: 0.25rem;
	}
	input,
	select {
		width: 100%;
		padding: 0.375rem 0.5rem;
		border: 1px solid var(--color-border);
		border-radius: 4px;
		font-size: 0.875rem;
		background: var(--color-surface);
		color: var(--color-text);
	}
	input:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.checkbox {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.checkbox input {
		width: auto;
	}
	.checkbox label {
		margin: 0;
	}
	.actions {
		margin-top: 1rem;
		display: flex;
		gap: 0.5rem;
		justify-content: flex-end;
	}
	button {
		padding: 0.375rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: 4px;
		background: var(--color-surface);
		color: var(--color-text);
		cursor: pointer;
		font-size: 0.875rem;
	}
	button.primary {
		background: var(--color-primary);
		color: var(--color-on-primary);
		border-color: var(--color-primary);
	}
	.error {
		color: var(--color-error);
		margin-bottom: 0.75rem;
		font-size: 0.875rem;
	}
</style>
