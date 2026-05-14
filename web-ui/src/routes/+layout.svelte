<script lang="ts">
  import "../app.css";
  import type { Snippet } from "svelte";
  import { onMount } from "svelte";
  import { theme } from "$lib/stores/theme";
  import ConnectionStatus from "../components/ConnectionStatus.svelte";

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();

  onMount(() => {
    theme.init();
    // Initialize config store and SSE live-reload (T057)
    import("$lib/stores/config-store").then(({ initConfigStore }) => {
      initConfigStore();
    });
  });
</script>

<div class="min-h-screen" style="background-color: var(--base-100);">
  <nav class="navbar">
    <div class="brand">Claude Code Proxy</div>
    <div class="links">
      <a href="/">Chain</a>
      <a href="/assignments">Assignments</a>
      <a href="/identifier-mappings">Identifier Mappings</a>
    </div>
    <div class="status">
      <ConnectionStatus />
    </div>
  </nav>
  <main class="content">
    {@render children()}
  </main>
</div>

<style>
  .navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    height: 3.5rem;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
  }
  .brand {
    font-weight: 700;
    font-size: 1.125rem;
  }
  .links a {
    margin-left: 1.5rem;
    text-decoration: none;
    color: var(--color-text);
    font-weight: 500;
    opacity: 0.8;
  }
  .links a:hover {
    opacity: 1;
  }
  .status {
    margin-left: 1.5rem;
  }
  .content {
    padding: 1.5rem;
  }
</style>
