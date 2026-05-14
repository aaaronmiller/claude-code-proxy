<script lang="ts">
	import { onMount } from "svelte";
	import { initConfigStore } from "$lib/stores/config-store";
	import ChainList from "../../components/ChainList.svelte";
	import {
		Server, Link2, Zap, ChevronUp, ChevronDown, Plus, Trash2,
		Save, RefreshCw, ToggleLeft, ToggleRight, Edit2, X, Check,
		AlertCircle, CheckCircle2, Wrench, Route
	} from "lucide-svelte";

	interface RouterConfig {
		default: string;
		background: string;
		think: string;
		long_context: string;
		long_context_threshold: number;
		web_search: string;
		image: string;
		custom_router_path: string;
	}

	let router = $state<RouterConfig>({
		default: "", background: "", think: "", long_context: "",
		long_context_threshold: 60000, web_search: "", image: "", custom_router_path: ""
	});
	let savingRouter = $state(false);
	let message = $state("");
	let messageType = $state<"ok" | "err">("ok");

	onMount(() => {
		initConfigStore();
		loadRouter();
	});

	async function loadRouter() {
		try {
			const res = await fetch("/api/router-config");
			if (res.ok) {
				const data = await res.json();
				router = { ...router, ...data };
			}
		} catch (e) {
			showMsg("Failed to load router config", "err");
		}
	}

	async function saveRouter() {
		savingRouter = true;
		try {
			const res = await fetch("/api/router-config", {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(router)
			});
			if (!res.ok) throw new Error(await res.text());
			showMsg("Router config saved", "ok");
		} catch (e: any) {
			showMsg(`Save failed: ${e.message}`, "err");
		} finally {
			savingRouter = false;
		}
	}

	function showMsg(text: string, type: "ok" | "err") {
		message = text;
		messageType = type;
		setTimeout(() => { message = ""; }, 4000);
	}
</script>

<div class="chain-page">

	<!-- Header -->
	<div class="page-header">
		<div class="header-left">
			<div class="header-icon"><Server size={20} /></div>
			<div>
				<h1>Proxy Chain</h1>
				<p>Configure upstream service order, routing, and per-use-case model assignment</p>
			</div>
		</div>
		<div class="header-actions">
			<button class="btn-ghost" onclick={() => window.location.reload()} disabled={false}>
				<RefreshCw size={15} />
				Refresh
			</button>
		</div>
	</div>

	<!-- Toast -->
	{#if message}
		<div class="toast" class:toast-ok={messageType === "ok"} class:toast-err={messageType === "err"}>
			{#if messageType === "ok"}<CheckCircle2 size={14} />{:else}<AlertCircle size={14} />{/if}
			{message}
		</div>
	{/if}

	<!-- Chain list component -->
	<section class="card">
		<div class="card-header">
			<div class="section-title">
				<Link2 size={16} />
				<span>Upstream Chain</span>
			</div>
		</div>
		<ChainList />
	</section>

	<!-- Router config section -->
	<section class="card">
		<div class="card-header">
			<div class="section-title">
				<Route size={16} />
				<span>Per-Use-Case Routing</span>
			</div>
			<button class="btn-primary" onclick={saveRouter} disabled={savingRouter}>
				<Save size={14} />
				{savingRouter ? "Saving…" : "Save routing"}
			</button>
		</div>

		<p class="section-hint">
			Leave blank to fall through to tier model (BIG/MIDDLE/SMALL). Priority:
			custom → image → web_search → long_context → think → background → default.
		</p>

		<div class="router-grid">
			<div class="router-field">
				<label>
					<span class="field-label">Default</span>
					<span class="field-hint">Override BIG_MODEL for all requests</span>
					<input bind:value={router.default} placeholder="(uses BIG_MODEL)" />
				</label>
			</div>

			<div class="router-field">
				<label>
					<span class="field-label">Background</span>
					<span class="field-hint">Haiku-family / max_tokens ≤ 256</span>
					<input bind:value={router.background} placeholder="stepfun/step-3.5-flash:free" />
				</label>
			</div>

			<div class="router-field">
				<label>
					<span class="field-label">Think / Plan Mode</span>
					<span class="field-hint">extended_thinking or "plan mode" in system prompt</span>
					<input bind:value={router.think} placeholder="(uses BIG_MODEL)" />
				</label>
			</div>

			<div class="router-field">
				<label>
					<span class="field-label">Long Context</span>
					<span class="field-hint">Request token count exceeds threshold</span>
					<input bind:value={router.long_context} placeholder="minimax/minimax-m2.5:free" />
				</label>
			</div>

			<div class="router-field router-field-narrow">
				<label>
					<span class="field-label">Long Context Threshold</span>
					<span class="field-hint">Estimated tokens (chars ÷ 4)</span>
					<input type="number" bind:value={router.long_context_threshold} />
				</label>
			</div>

			<div class="router-field">
				<label>
					<span class="field-label">Web Search</span>
					<span class="field-hint">Tool named web_search / brave / exa detected</span>
					<input bind:value={router.web_search} placeholder="(uses BIG_MODEL)" />
				</label>
			</div>

			<div class="router-field">
				<label>
					<span class="field-label">Image</span>
					<span class="field-hint">Request contains image content blocks</span>
					<input bind:value={router.image} placeholder="qwen/qwen2.5-vl-72b-instruct" />
				</label>
			</div>

			<div class="router-field router-field-full">
				<label>
					<span class="field-label">Custom Router Path</span>
					<span class="field-hint">Path to custom_router.py or .js — return model string or null</span>
					<input bind:value={router.custom_router_path} placeholder="/path/to/custom_router.py" />
				</label>
			</div>
		</div>
	</section>

	<!-- Info card -->
	<section class="card info-card">
		<div class="section-title"><Wrench size={15} /><span>RTK & Chain Info</span></div>
		<div class="info-grid">
			<div class="info-item">
				<strong>RTK (Rust Token Killer)</strong>
				<p>CLI wrapper — no port, no daemon. Compresses shell command output before it enters context.
				   Use as: <code>rtk git status</code>, <code>rtk ls</code>, <code>rtk tree</code>.
				   Claude reads CLAUDE.md in this repo for instructions. Not a proxy server.</p>
			</div>
			<div class="info-item">
				<strong>Headroom :8787</strong>
				<p>HTTP context-compression proxy. Intercepts API requests and compresses message history
				   to prevent context-window exhaustion. Runs as a daemon. Health: checked above.</p>
			</div>
			<div class="info-item">
				<strong>Chain start order</strong>
				<p>Upstream services start in reverse order (top entry = last to start, first to receive traffic).
				   Use ↑↓ to reorder. Start all with <code>proxies up</code>.</p>
			</div>
		</div>
	</section>

</div>

<style>
	.chain-page {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		color: var(--text-primary);
		font-family: 'IBM Plex Sans', sans-serif;
	}

	/* Header */
	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}
	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	.header-icon {
		width: 36px; height: 36px;
		display: flex; align-items: center; justify-content: center;
		background: var(--primary-muted);
		border-radius: 8px;
		color: var(--primary-vivid);
		flex-shrink: 0;
	}
	.page-header h1 { font-size: 1.25rem; font-weight: 600; margin: 0; }
	.page-header p  { font-size: 0.8rem; color: var(--text-secondary); margin: 0; }
	.header-actions { display: flex; gap: 0.5rem; }

	/* Toast */
	.toast {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		font-size: 0.85rem;
		border: 1px solid transparent;
	}
	.toast-ok  { background: color-mix(in srgb, var(--success) 15%, transparent); border-color: var(--success); color: var(--success); }
	.toast-err { background: color-mix(in srgb, var(--error) 15%, transparent); border-color: var(--error); color: var(--error); }

	/* Card */
	.card {
		background: var(--base-200);
		border: 1px solid var(--border-default);
		border-radius: 12px;
		overflow: hidden;
	}
	.card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.25rem;
		border-bottom: 1px solid var(--border-default);
		gap: 1rem;
		flex-wrap: wrap;
	}
	.card-actions { display: flex; gap: 0.5rem; align-items: center; }
	.section-title {
		display: flex; align-items: center; gap: 0.5rem;
		font-weight: 600; font-size: 0.95rem;
		color: var(--text-primary);
	}
	.section-hint {
		font-size: 0.78rem;
		color: var(--text-tertiary);
		padding: 0.75rem 1.25rem 0;
		margin: 0;
	}

	/* Router grid */
	.router-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0;
		padding: 0.75rem 0 0;
	}
	.router-field {
		padding: 0.6rem 1.25rem;
	}
	.router-field-narrow { grid-column: span 1; }
	.router-field-full   { grid-column: span 2; }
	.router-field label {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}
	.field-label {
		font-size: 0.82rem;
		font-weight: 600;
		color: var(--text-primary);
	}
	.field-hint {
		font-size: 0.72rem;
		color: var(--text-tertiary);
		margin-bottom: 0.2rem;
	}
	.router-field input {
		background: var(--base-300);
		border: 1px solid var(--border-default);
		border-radius: 6px;
		padding: 0.4rem 0.65rem;
		font-size: 0.8rem;
		color: var(--text-primary);
		font-family: var(--font-mono);
		outline: none;
		width: 100%;
	}
	.router-field input:focus { border-color: var(--primary-default); }

	/* Info card */
	.info-card { padding: 1rem 1.25rem; }
	.info-card .section-title { margin-bottom: 0.75rem; }
	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 1rem;
	}
	.info-item strong { font-size: 0.82rem; display: block; margin-bottom: 0.25rem; }
	.info-item p { font-size: 0.75rem; color: var(--text-secondary); margin: 0; line-height: 1.5; }
	.info-item code {
		font-family: var(--font-mono);
		background: var(--base-300);
		padding: 0.05rem 0.3rem;
		border-radius: 3px;
		font-size: 0.72rem;
	}

	/* Buttons */
	.btn-primary {
		display: flex; align-items: center; gap: 0.35rem;
		padding: 0.45rem 0.9rem;
		background: var(--primary-default);
		color: #fff;
		border: none;
		border-radius: 7px;
		font-size: 0.82rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.15s;
		white-space: nowrap;
	}
	.btn-primary:hover:not(:disabled) { background: var(--primary-vivid); }
	.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

	.btn-ghost {
		display: flex; align-items: center; gap: 0.35rem;
		padding: 0.45rem 0.75rem;
		background: transparent;
		color: var(--text-secondary);
		border: 1px solid var(--border-default);
		border-radius: 7px;
		font-size: 0.82rem;
		cursor: pointer;
		transition: all 0.15s;
		white-space: nowrap;
	}
	.btn-ghost:hover:not(:disabled) {
		background: var(--base-300);
		color: var(--text-primary);
		border-color: var(--border-strong);
	}
	.btn-ghost:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
