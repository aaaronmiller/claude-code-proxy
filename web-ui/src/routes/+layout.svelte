<script lang="ts">
  import "../app.css";
  import type { Snippet } from "svelte";

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();
</script>

<div class="min-h-screen bg-cyber-bg">
  {@render children()}
</div>
