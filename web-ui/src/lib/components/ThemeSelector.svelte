<script lang="ts">
  import { Palette, Check } from "lucide-svelte";
  import { theme } from "$lib/stores/theme";
  import { onMount } from "svelte";

  let isOpen = $state(false);

  const themes = [
    {
      id: "midnight",
      name: "Midnight Aurora",
      description: "Indigo blue with teal accents",
      colors: ["#6366f1", "#14b8a6", "#8b5cf6"]
    },
    {
      id: "ember",
      name: "Ember Console",
      description: "Warm orange with cool blue",
      colors: ["#f97316", "#0ea5e9", "#eab308"]
    },
    {
      id: "synthwave",
      name: "Synthwave",
      description: "Violet with magenta glow",
      colors: ["#8b5cf6", "#ec4899", "#06b6d4"]
    }
  ];

  onMount(() => {
    theme.init();
  });

  function selectTheme(themeId: string) {
    theme.set(themeId);
    isOpen = false;
  }

  function toggleDropdown() {
    isOpen = !isOpen;
  }
</script>

  <div class="relative">
  <button
    onclick={toggleDropdown}
    class="flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-150 hover:bg-[var(--base-300)] cursor-pointer"
    style="color: var(--text-secondary);"
    aria-label="Select theme"
    aria-expanded={isOpen}
  >
    <Palette size={18} />
    <span class="text-sm hidden sm:inline">Theme</span>
  </button>

  {#if isOpen}
    <div
      class="absolute right-0 top-full mt-2 w-64 rounded-lg p-2 z-50 animate-scale-in"
      style="background: var(--base-200); border: 1px solid var(--border-default); box-shadow: var(--shadow-lg);"
      role="menu"
    >
      {#each themes as t}
        <button
          onclick={() => selectTheme(t.id)}
          class="w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-150 cursor-pointer"
          class:bg-[var(--base-300)]={$theme === t.id}
          style="color: var(--text-primary);"
          role="menuitem"
        >
          <div class="flex gap-1">
            {#each t.colors as color}
              <div
                class="w-4 h-4 rounded-full"
                style="background: {color};"
              ></div>
            {/each}
          </div>
          <div class="flex-1 text-left">
            <div class="text-sm font-medium">{t.name}</div>
            <div class="text-xs" style="color: var(--text-tertiary);">{t.description}</div>
          </div>
          {#if $theme === t.id}
            <Check size={16} style="color: var(--accent-default);" />
          {/if}
        </button>
      {/each}
    </div>
  {/if}
</div>

<svelte:window onclick={(e) => {
  if (isOpen && !(e.target as Element).closest('.relative')) {
    isOpen = false;
  }
}} />