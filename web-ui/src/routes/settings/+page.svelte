<script lang="ts">
	import { onMount } from "svelte";
	import {
		getConfigSchema,
		getConfigValues,
		saveSettings,
		type ConfigGroup,
		type ConfigSetting,
	} from "$lib/services/config-client";

	let groups = $state<ConfigGroup[]>([]);
	let values = $state<Record<string, unknown>>({});
	let edited = $state<Record<string, unknown>>({});
	let activeGroup = $state<string>("");
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let result = $state<{ saved: string[]; rejected: Record<string, string> } | null>(null);

	const dirtyCount = $derived(Object.keys(edited).length);
	const active = $derived(groups.find((g) => g.name === activeGroup));

	onMount(load);

	async function load() {
		loading = true;
		error = null;
		try {
			const [schema, vals] = await Promise.all([getConfigSchema(), getConfigValues()]);
			groups = schema.groups;
			values = vals;
			if (groups.length && !activeGroup) activeGroup = groups[0].name;
		} catch (e) {
			error = (e as Error).message;
		} finally {
			loading = false;
		}
	}

	// current effective value for a setting (edited overrides loaded)
	function valueOf(s: ConfigSetting): unknown {
		return s.key in edited ? edited[s.key] : values[s.key];
	}

	function setEdited(s: ConfigSetting, v: unknown) {
		// drop the edit if it matches the loaded value again
		if (v === values[s.key]) {
			const { [s.key]: _, ...rest } = edited;
			edited = rest;
		} else {
			edited = { ...edited, [s.key]: v };
		}
		result = null;
	}

	function onBool(s: ConfigSetting, e: Event) {
		setEdited(s, (e.target as HTMLInputElement).checked);
	}
	function onNum(s: ConfigSetting, e: Event) {
		const raw = (e.target as HTMLInputElement).value;
		setEdited(s, raw === "" ? "" : Number(raw));
	}
	function onText(s: ConfigSetting, e: Event) {
		setEdited(s, (e.target as HTMLInputElement | HTMLTextAreaElement).value);
	}

	async function save() {
		if (!dirtyCount) return;
		saving = true;
		error = null;
		try {
			result = await saveSettings(edited);
			// merge accepted edits into loaded values, then clear the dirty set
			values = { ...values, ...edited };
			edited = {};
		} catch (e) {
			error = (e as Error).message;
		} finally {
			saving = false;
		}
	}

	function reset() {
		edited = {};
		result = null;
	}
</script>

<div class="settings">
	<header>
		<h1>Settings</h1>
		<div class="actions">
			{#if dirtyCount}
				<span class="dirty">{dirtyCount} unsaved</span>
				<button class="ghost" onclick={reset} disabled={saving}>Reset</button>
			{/if}
			<button class="primary" onclick={save} disabled={!dirtyCount || saving}>
				{saving ? "Saving…" : "Save changes"}
			</button>
		</div>
	</header>

	{#if error}
		<div class="banner err">{error}</div>
	{/if}
	{#if result}
		<div class="banner ok">
			Saved {result.saved.length} setting(s).
			{#if Object.keys(result.rejected).length}
				Rejected: {Object.entries(result.rejected)
					.map(([k, v]) => `${k} (${v})`)
					.join(", ")}
			{/if}
		</div>
	{/if}

	{#if loading}
		<p class="muted">Loading configuration…</p>
	{:else}
		<div class="layout">
			<nav class="groups">
				{#each groups as g (g.name)}
					<button class:active={g.name === activeGroup} onclick={() => (activeGroup = g.name)}>
						{g.label}
					</button>
				{/each}
			</nav>

			<section class="fields">
				{#if active}
					<h2>{active.label}</h2>
					{#each active.settings as s (s.key)}
						<div class="field">
							<label for={s.key}>
								<span class="name">{s.env_var}</span>
								{#if s.units}<span class="units">{s.units}</span>{/if}
								{#if s.cli_flag}<code class="flag">{s.cli_flag}</code>{/if}
							</label>
							<p class="desc">{s.description}</p>

							{#if s.web_component === "switch" || s.type === "bool"}
								<input
									id={s.key}
									type="checkbox"
									checked={Boolean(valueOf(s))}
									onchange={(e) => onBool(s, e)}
								/>
							{:else if s.web_component === "select" && s.choices}
								<select id={s.key} onchange={(e) => onText(s, e)}>
									{#each s.choices as c (c)}
										<option value={c} selected={String(valueOf(s)) === c}>{c}</option>
									{/each}
								</select>
							{:else if s.web_component === "number" || s.web_component === "slider" || s.type === "int" || s.type === "float"}
								<input
									id={s.key}
									type="number"
									value={valueOf(s) ?? ""}
									oninput={(e) => onNum(s, e)}
								/>
							{:else if s.web_component === "textarea"}
								<textarea id={s.key} value={String(valueOf(s) ?? "")} oninput={(e) => onText(s, e)}
								></textarea>
							{:else}
								<input
									id={s.key}
									type={s.secret ? "password" : "text"}
									value={s.secret ? "" : String(valueOf(s) ?? "")}
									placeholder={s.secret ? (valueOf(s) === "***" ? "•••• (set — leave blank to keep)" : "") : ""}
									oninput={(e) => onText(s, e)}
								/>
							{/if}
						</div>
					{/each}
				{/if}
			</section>
		</div>
	{/if}
</div>

<style>
	.settings {
		max-width: 920px;
		margin: 0 auto;
	}
	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}
	h1 {
		font-size: 1.5rem;
		font-weight: 700;
	}
	.actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	.dirty {
		font-size: 0.85rem;
		opacity: 0.75;
	}
	button {
		cursor: pointer;
		border-radius: 0.5rem;
		padding: 0.4rem 0.85rem;
		font-weight: 600;
		border: 1px solid var(--color-border);
		background: var(--color-surface);
		color: var(--color-text);
	}
	button.primary {
		background: var(--color-accent, #6366f1);
		color: #fff;
		border-color: transparent;
	}
	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.banner {
		padding: 0.6rem 0.9rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}
	.banner.err {
		background: #fef2f2;
		color: #b91c1c;
	}
	.banner.ok {
		background: #ecfdf5;
		color: #047857;
	}
	.layout {
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 1.5rem;
		align-items: start;
	}
	.groups {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		position: sticky;
		top: 1rem;
	}
	.groups button {
		text-align: left;
		border: none;
		background: transparent;
		font-weight: 500;
		opacity: 0.75;
	}
	.groups button.active {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		opacity: 1;
	}
	h2 {
		font-size: 1.1rem;
		font-weight: 700;
		margin-bottom: 0.75rem;
	}
	.field {
		padding: 0.75rem 0;
		border-bottom: 1px solid var(--color-border);
	}
	.field label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.name {
		font-weight: 600;
		font-family: ui-monospace, monospace;
		font-size: 0.85rem;
	}
	.units {
		font-size: 0.75rem;
		opacity: 0.6;
	}
	.flag {
		font-size: 0.7rem;
		opacity: 0.6;
		margin-left: auto;
	}
	.desc {
		font-size: 0.8rem;
		opacity: 0.7;
		margin: 0.2rem 0 0.5rem;
	}
	.field input[type="text"],
	.field input[type="password"],
	.field input[type="number"],
	.field select,
	.field textarea {
		width: 100%;
		padding: 0.4rem 0.6rem;
		border-radius: 0.4rem;
		border: 1px solid var(--color-border);
		background: var(--base-100, #fff);
		color: var(--color-text);
	}
	.muted {
		opacity: 0.7;
	}
</style>
