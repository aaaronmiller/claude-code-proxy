<script lang="ts">
  import "../app.css";
  import type { Snippet } from "svelte";
  import { onMount } from "svelte";
  import { theme } from "$lib/stores/theme";

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();

  onMount(() => {
    theme.init();
  });
</script>

<div class="min-h-screen" style="background-color: var(--base-100);">
  {@render children()}
</div>
