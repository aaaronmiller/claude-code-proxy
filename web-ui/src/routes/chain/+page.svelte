<script lang="ts">
  import { onMount } from "svelte";
  import {
    Server, Link2, Zap, ChevronUp, ChevronDown, Plus, Trash2,
    Save, RefreshCw, ToggleLeft, ToggleRight, Edit2, X, Check,
    AlertCircle, CheckCircle2, Wrench, Route, ArrowRight
  } from "lucide-svelte";

  // ── Types ──────────────────────────────────────────────────────────────────
  interface ChainEntry {
    id: string;
    name: string;
    url: string;
    auth_key: string;
    enabled: boolean;
    order: number;
    service_cmd: string;
    service_stop_cmd: string;
    health_path: string;
    port: number;
    timeout: number;
    extra_headers: Record<string, string>;
    type: string;
    model_prefixes: string[];
  }

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

  interface HealthStatus {
    [id: string]: "ok" | "down" | "passive" | "checking";
  }

  // ── State ──────────────────────────────────────────────────────────────────
  let entries = $state<ChainEntry[]>([]);
  let router  = $state<RouterConfig>({
    default: "", background: "", think: "", long_context: "",
    long_context_threshold: 60000, web_search: "", image: "", custom_router_path: ""
  });

  let health        = $state<HealthStatus>({});
  let loading       = $state(true);
  let saving        = $state(false);
  let savingRouter  = $state(false);
  let message       = $state("");
  let messageType   = $state<"ok" | "err">("ok");
  let editingId     = $state<string | null>(null);
  let editDraft     = $state<Partial<ChainEntry>>({});
  let addingNew     = $state(false);
  let newEntry      = $state<Partial<ChainEntry>>({
    id: "", name: "", url: "", auth_key: "", enabled: true,
    order: 99, service_cmd: "", health_path: "/health", port: 0,
    timeout: 90, type: "http", extra_headers: {}, model_prefixes: [],
    service_stop_cmd: ""
  });

  // ── Load ───────────────────────────────────────────────────────────────────
  async function loadChain() {
    loading = true;
    try {
      const [chainRes, routerRes] = await Promise.all([
        fetch("/api/proxy-chain"),
        fetch("/api/router-config")
      ]);
      const chainData  = await chainRes.json();
      const routerData = await routerRes.json();
      entries = (chainData.entries || []).sort((a: ChainEntry, b: ChainEntry) => a.order - b.order);
      router  = { ...router, ...routerData };
      await checkHealth();
    } catch (e) {
      showMsg("Failed to load chain config", "err");
    } finally {
      loading = false;
    }
  }

  async function checkHealth() {
    for (const e of entries) {
      if (e.type === "cli_wrapper" || !e.port || !e.enabled) {
        health[e.id] = e.type === "cli_wrapper" ? "passive" : "down";
        continue;
      }
      health[e.id] = "checking";
      try {
        const r = await fetch(`http://127.0.0.1:${e.port}${e.health_path || "/health"}`, {
          signal: AbortSignal.timeout(2000)
        });
        health[e.id] = r.ok ? "ok" : "down";
      } catch {
        health[e.id] = "down";
      }
    }
  }

  // ── Save chain ─────────────────────────────────────────────────────────────
  async function saveChain() {
    saving = true;
    try {
      const body = { entries: entries.map((e, i) => ({ ...e, order: i })) };
      const res  = await fetch("/api/proxy-chain", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!res.ok) throw new Error(await res.text());
      showMsg("Chain saved and reloaded", "ok");
      await checkHealth();
    } catch (e: any) {
      showMsg(`Save failed: ${e.message}`, "err");
    } finally {
      saving = false;
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

  // ── Chain manipulation ─────────────────────────────────────────────────────
  function moveUp(idx: number) {
    if (idx === 0) return;
    [entries[idx - 1], entries[idx]] = [entries[idx], entries[idx - 1]];
    entries = [...entries];
  }

  function moveDown(idx: number) {
    if (idx === entries.length - 1) return;
    [entries[idx], entries[idx + 1]] = [entries[idx + 1], entries[idx]];
    entries = [...entries];
  }

  function toggleEnabled(idx: number) {
    entries[idx] = { ...entries[idx], enabled: !entries[idx].enabled };
  }

  function startEdit(entry: ChainEntry) {
    editingId = entry.id;
    editDraft = { ...entry };
  }

  function cancelEdit() {
    editingId = null;
    editDraft = {};
  }

  function commitEdit() {
    const idx = entries.findIndex(e => e.id === editingId);
    if (idx !== -1) {
      entries[idx] = { ...entries[idx], ...editDraft } as ChainEntry;
      entries = [...entries];
    }
    editingId = null;
    editDraft = {};
  }

  function deleteEntry(idx: number) {
    entries = entries.filter((_, i) => i !== idx);
  }

  function addEntry() {
    if (!newEntry.id || !newEntry.name) {
      showMsg("ID and Name are required", "err");
      return;
    }
    entries = [...entries, { ...newEntry, order: entries.length } as ChainEntry];
    addingNew = false;
    newEntry = {
      id: "", name: "", url: "", auth_key: "", enabled: true,
      order: 99, service_cmd: "", health_path: "/health", port: 0,
      timeout: 90, type: "http", extra_headers: {}, model_prefixes: [],
      service_stop_cmd: ""
    };
  }

  // ── Utils ──────────────────────────────────────────────────────────────────
  function showMsg(text: string, type: "ok" | "err") {
    message = text;
    messageType = type;
    setTimeout(() => { message = ""; }, 4000);
  }

  function healthColor(id: string) {
    const s = health[id];
    if (s === "ok")       return "var(--success)";
    if (s === "down")     return "var(--error)";
    if (s === "passive")  return "var(--warning)";
    return "var(--text-tertiary)";
  }

  function healthLabel(id: string) {
    return health[id] === "ok" ? "healthy"
         : health[id] === "down" ? "unreachable"
         : health[id] === "passive" ? "passive"
         : "checking…";
  }

  onMount(loadChain);
</script>

<!-- ── Page ──────────────────────────────────────────────────────────────────── -->
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
      <button class="btn-ghost" onclick={loadChain} disabled={loading}>
        <RefreshCw size={15} class={loading ? "spin" : ""} />
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

  <!-- ── Chain entries ──────────────────────────────────────────────────────── -->
  <section class="card">
    <div class="card-header">
      <div class="section-title">
        <Link2 size={16} />
        <span>Upstream Chain</span>
        <span class="badge">{entries.filter(e => e.enabled).length} active</span>
      </div>
      <div class="card-actions">
        <button class="btn-ghost" onclick={() => { addingNew = !addingNew; }}>
          <Plus size={14} /> Add entry
        </button>
        <button class="btn-primary" onclick={saveChain} disabled={saving}>
          <Save size={14} />
          {saving ? "Saving…" : "Save chain"}
        </button>
      </div>
    </div>

    <!-- Flow diagram -->
    {#if entries.length > 0}
      <div class="flow-row">
        <span class="flow-chip flow-client">Client</span>
        {#each entries.filter(e => e.enabled) as e}
          <ArrowRight size={12} class="flow-arrow" />
          <span class="flow-chip" style="border-color: {healthColor(e.id)}">
            {e.name}{e.port ? ` :${e.port}` : ""}
          </span>
        {/each}
        <ArrowRight size={12} class="flow-arrow" />
        <span class="flow-chip flow-origin">Origin</span>
      </div>
    {/if}

    <!-- Add new entry form -->
    {#if addingNew}
      <div class="entry-form new-form">
        <div class="form-row">
          <label>ID <input bind:value={newEntry.id} placeholder="headroom" /></label>
          <label>Name <input bind:value={newEntry.name} placeholder="Headroom Compression" /></label>
          <label>Type
            <select bind:value={newEntry.type}>
              <option value="http">HTTP proxy</option>
              <option value="cli_wrapper">CLI wrapper</option>
            </select>
          </label>
        </div>
        <div class="form-row">
          <label>URL <input bind:value={newEntry.url} placeholder="http://127.0.0.1:8787/v1" /></label>
          <label>Port <input type="number" bind:value={newEntry.port} placeholder="8787" /></label>
          <label>Health path <input bind:value={newEntry.health_path} placeholder="/health" /></label>
        </div>
        <div class="form-row">
          <label class="grow">Service cmd <input bind:value={newEntry.service_cmd} placeholder="headroom proxy --port 8787 …" /></label>
        </div>
        <div class="form-row">
          <label>Auth key <input bind:value={newEntry.auth_key} placeholder="${OPENROUTER_API_KEY}" /></label>
          <label>Timeout (s) <input type="number" bind:value={newEntry.timeout} /></label>
        </div>
        <div class="form-actions">
          <button class="btn-ghost" onclick={() => addingNew = false}><X size={13} /> Cancel</button>
          <button class="btn-primary" onclick={addEntry}><Check size={13} /> Add</button>
        </div>
      </div>
    {/if}

    <!-- Entry list -->
    {#if loading}
      <div class="loading-state">Loading chain config…</div>
    {:else if entries.length === 0}
      <div class="empty-state">No chain entries. Add one above.</div>
    {:else}
      {#each entries as entry, idx (entry.id)}
        <div class="entry" class:entry-disabled={!entry.enabled}>

          <!-- Reorder + enable controls -->
          <div class="entry-controls">
            <button class="icon-btn" onclick={() => moveUp(idx)} disabled={idx === 0}><ChevronUp size={14} /></button>
            <span class="order-num">{idx + 1}</span>
            <button class="icon-btn" onclick={() => moveDown(idx)} disabled={idx === entries.length - 1}><ChevronDown size={14} /></button>
          </div>

          <!-- Main info -->
          {#if editingId === entry.id}
            <div class="entry-form">
              <div class="form-row">
                <label>Name <input bind:value={editDraft.name} /></label>
                <label>URL  <input bind:value={editDraft.url} /></label>
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
                <button class="btn-ghost" onclick={cancelEdit}><X size={13} /> Cancel</button>
                <button class="btn-primary" onclick={commitEdit}><Check size={13} /> Apply</button>
              </div>
            </div>
          {:else}
            <div class="entry-info">
              <div class="entry-main">
                <span class="entry-name">{entry.name}</span>
                {#if entry.port}
                  <span class="entry-port">:{entry.port}</span>
                {/if}
                <span class="type-badge type-{entry.type}">{entry.type === "cli_wrapper" ? "CLI" : "HTTP"}</span>
              </div>
              <div class="entry-meta">
                {#if entry.url}
                  <span class="entry-url">{entry.url}</span>
                {/if}
                {#if health[entry.id]}
                  <span class="health-dot" style="color: {healthColor(entry.id)}">
                    ● {healthLabel(entry.id)}
                  </span>
                {/if}
              </div>
            </div>
          {/if}

          <!-- Row actions -->
          {#if editingId !== entry.id}
            <div class="entry-actions">
              <button class="icon-btn toggle-btn" onclick={() => toggleEnabled(idx)}
                title={entry.enabled ? "Disable" : "Enable"}>
                {#if entry.enabled}<ToggleRight size={18} style="color:var(--success)" />{:else}<ToggleLeft size={18} />{/if}
              </button>
              <button class="icon-btn" onclick={() => startEdit(entry)} title="Edit"><Edit2 size={14} /></button>
              <button class="icon-btn danger" onclick={() => deleteEntry(idx)} title="Delete"><Trash2 size={14} /></button>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </section>

  <!-- ── Router config ──────────────────────────────────────────────────────── -->
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

  <!-- ── Info ───────────────────────────────────────────────────────────────── -->
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
  .badge {
    font-size: 0.7rem; font-weight: 600;
    padding: 0.15rem 0.5rem;
    background: var(--primary-muted);
    color: var(--primary-vivid);
    border-radius: 99px;
  }
  .section-hint {
    font-size: 0.78rem;
    color: var(--text-tertiary);
    padding: 0.75rem 1.25rem 0;
    margin: 0;
  }

  /* Flow diagram */
  .flow-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.75rem 1.25rem;
    border-bottom: 1px solid var(--border-default);
    flex-wrap: wrap;
  }
  .flow-chip {
    font-size: 0.72rem; font-weight: 500;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    border: 1px solid var(--border-strong);
    background: var(--base-300);
    white-space: nowrap;
  }
  .flow-client { border-color: var(--accent-default); color: var(--accent-default); }
  .flow-origin { border-color: var(--text-tertiary); color: var(--text-tertiary); }
  :global(.flow-arrow) { color: var(--text-tertiary); flex-shrink: 0; }

  /* Entry rows */
  .entry {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.85rem 1.25rem;
    border-bottom: 1px solid var(--border-default);
    transition: background 0.15s;
  }
  .entry:last-child { border-bottom: none; }
  .entry:hover { background: var(--base-300); }
  .entry-disabled { opacity: 0.45; }

  .entry-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    flex-shrink: 0;
  }
  .order-num {
    font-size: 0.7rem;
    color: var(--text-tertiary);
    font-family: 'IBM Plex Mono', monospace;
  }

  .entry-info { flex: 1; min-width: 0; }
  .entry-main {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  .entry-name { font-weight: 600; font-size: 0.9rem; }
  .entry-port {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent-default);
  }
  .entry-meta {
    display: flex;
    gap: 1rem;
    margin-top: 0.2rem;
    flex-wrap: wrap;
  }
  .entry-url {
    font-size: 0.75rem;
    font-family: 'IBM Plex Mono', monospace;
    color: var(--text-tertiary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 300px;
  }
  .health-dot { font-size: 0.75rem; }
  .type-badge {
    font-size: 0.65rem; font-weight: 700;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .type-http        { background: color-mix(in srgb, var(--info) 20%, transparent); color: var(--info); }
  .type-cli_wrapper { background: color-mix(in srgb, var(--warning) 20%, transparent); color: var(--warning); }

  .entry-actions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex-shrink: 0;
  }

  /* Entry edit form */
  .entry-form {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }
  .new-form {
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border-default);
    background: var(--base-300);
  }
  .form-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }
  .form-row label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    flex: 1;
    min-width: 140px;
  }
  .form-row label.grow { flex: 3; }
  .form-row input, .form-row select {
    background: var(--base-200);
    border: 1px solid var(--border-strong);
    border-radius: 6px;
    padding: 0.35rem 0.6rem;
    font-size: 0.8rem;
    color: var(--text-primary);
    font-family: 'IBM Plex Mono', monospace;
    outline: none;
    width: 100%;
  }
  .form-row input:focus, .form-row select:focus {
    border-color: var(--primary-default);
  }
  .form-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 0.25rem;
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
    font-family: 'IBM Plex Mono', monospace;
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
    font-family: 'IBM Plex Mono', monospace;
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

  .icon-btn {
    display: flex; align-items: center; justify-content: center;
    width: 26px; height: 26px;
    background: transparent;
    border: none;
    border-radius: 5px;
    color: var(--text-tertiary);
    cursor: pointer;
    transition: all 0.12s;
    padding: 0;
  }
  .icon-btn:hover:not(:disabled) {
    background: var(--base-300);
    color: var(--text-primary);
  }
  .icon-btn:disabled { opacity: 0.3; cursor: not-allowed; }
  .icon-btn.danger:hover { color: var(--error); background: color-mix(in srgb, var(--error) 12%, transparent); }
  .toggle-btn:hover { background: transparent !important; }

  /* Loading / empty */
  .loading-state, .empty-state {
    padding: 2rem;
    text-align: center;
    color: var(--text-tertiary);
    font-size: 0.85rem;
  }

  :global(.spin) { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
