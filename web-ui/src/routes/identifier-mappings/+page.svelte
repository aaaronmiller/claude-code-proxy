<script lang="ts">
	import { onMount } from "svelte";
	import { identifierMappings, initConfigStore } from "$lib/stores/config-store";
	import IdentifierMappingTable from "../../components/IdentifierMappingTable.svelte";
	import type { IdentifierMapping } from "$lib/services/config-client";
	import { deleteIdentifierMapping } from "$lib/services/config-client";

	onMount(() => {
		initConfigStore();
	});

	function confirmDelete(m: IdentifierMapping) {
		if (confirm(`Delete mapping for "${m.incoming_identifier}"?`)) {
			deleteIdentifierMapping(m.id);
		}
	}
</script>

<svelte:head>
	<title>Identifier Mappings — Claude Code Proxy</title>
</svelte:head>

<div class="page">
	<h1>Identifier Mappings</h1>
	<p class="desc">
		Map incoming model identifiers from upstreams (Hermes, future Anthropic task types)
		to assignment IDs. The first enabled match (highest priority) wins.
	</p>

	<IdentifierMappingTable />
</div>

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
</style>
