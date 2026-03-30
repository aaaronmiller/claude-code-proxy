<script lang="ts">
    import { onMount } from 'svelte';
    import { ChevronDown, Check, Search, X, Zap, Gem, Flame, Brain, BookOpen, TrendingUp, Loader2 } from 'lucide-svelte';

    interface Props {
        currentModels?: { big?: string; middle?: string; small?: string };
        onSelect?: (tier: 'big' | 'middle' | 'small', modelId: string) => void;
    }

    let { currentModels = {}, onSelect }: Props = $props();

    interface Model {
        id: string;
        name: string;
        provider: string;
        context_length: number;
        pricing: { prompt: number; completion: number } | null;
        top_provider: { popularity_score: number } | null;
        supports_reasoning: boolean;
    }

    let allModels = $state<Model[]>([]);
    let loading = $state(true);
    let error = $state('');

    let bigTierOpen = $state(false);
    let middleTierOpen = $state(false);
    let smallTierOpen = $state(false);

    let bigSearch = $state('');
    let middleSearch = $state('');
    let smallSearch = $state('');

    const tierConfig = {
        big: { label: 'BIG', color: 'text-purple-400', desc: 'Complex reasoning & tasks', icon: Brain },
        middle: { label: 'MIDDLE', color: 'text-cyan-400', desc: 'Balanced performance', icon: Zap },
        small: { label: 'SMALL', color: 'text-green-400', desc: 'Fast & economical', icon: Flame }
    };

    onMount(async () => {
        await fetchModels();
    });

    async function fetchModels() {
        loading = true;
        error = '';
        
        try {
            const res = await fetch('https://openrouter.ai/api/v1/models?limit=300', {
                headers: {
                    'Authorization': `Bearer ${import.meta.env.VITE_OPENROUTER_API_KEY || ''}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!res.ok) throw new Error('Failed to fetch models');
            
            const data = await res.json();
            allModels = (data.data || []).filter((m: Model) => m.pricing && m.top_provider);
        } catch (e) {
            console.error('Failed to fetch models:', e);
            error = 'Could not load models. Using cached data.';
            // Fallback to common models
            allModels = getFallbackModels();
        } finally {
            loading = false;
        }
    }

    function getFallbackModels(): Model[] {
        return [
            { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'anthropic', context_length: 200000, pricing: { prompt: 0.000003, completion: 0.000015 }, top_provider: { popularity_score: 98 }, supports_reasoning: false },
            { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'openai', context_length: 128000, pricing: { prompt: 0.0000025, completion: 0.00001 }, top_provider: { popularity_score: 97 }, supports_reasoning: false },
            { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai', context_length: 128000, pricing: { prompt: 0.00000015, completion: 0.0000006 }, top_provider: { popularity_score: 96 }, supports_reasoning: false },
            { id: 'google/gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash', provider: 'google', context_length: 1000000, pricing: { prompt: 0, completion: 0 }, top_provider: { popularity_score: 95 }, supports_reasoning: true },
            { id: 'anthropic/claude-3-opus', name: 'Claude 3 Opus', provider: 'anthropic', context_length: 200000, pricing: { prompt: 0.000015, completion: 0.000075 }, top_provider: { popularity_score: 94 }, supports_reasoning: false },
            { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Llama 3.3 70B', provider: 'meta-llama', context_length: 128000, pricing: { prompt: 0.0000008, completion: 0.0000008 }, top_provider: { popularity_score: 92 }, supports_reasoning: false },
            { id: 'deepseek/deepseek-chat', name: 'DeepSeek Chat', provider: 'deepseek', context_length: 64000, pricing: { prompt: 0.00000014, completion: 0.00000028 }, top_provider: { popularity_score: 90 }, supports_reasoning: true },
            { id: 'qwen/qwen-2.5-72b-instruct', name: 'Qwen 2.5 72B', provider: 'qwen', context_length: 32768, pricing: { prompt: 0.0000009, completion: 0.0000009 }, top_provider: { popularity_score: 88 }, supports_reasoning: false },
            { id: 'mistralai/mistral-large', name: 'Mistral Large', provider: 'mistralai', context_length: 128000, pricing: { prompt: 0.000002, completion: 0.000006 }, top_provider: { popularity_score: 85 }, supports_reasoning: false },
            { id: 'google/gemini-pro-1.5', name: 'Gemini Pro 1.5', provider: 'google', context_length: 2000000, pricing: { prompt: 0.00000125, completion: 0.000005 }, top_provider: { popularity_score: 93 }, supports_reasoning: false }
        ];
    }

    // Category getters
    let topFreeModels = $derived(
        allModels
            .filter(m => m.pricing && m.pricing.prompt === 0 && m.pricing.completion === 0)
            .sort((a, b) => (b.top_provider?.popularity_score || 0) - (a.top_provider?.popularity_score || 0))
            .slice(0, 5)
    );

    let pricePerfModels = $derived(
        [...allModels]
            .filter(m => m.pricing && m.context_length && m.context_length >= 128000)
            .sort((a, b) => {
                const aPrice = (a.pricing?.prompt || 0) + (a.pricing?.completion || 0);
                const bPrice = (b.pricing?.prompt || 0) + (b.pricing?.completion || 0);
                const aScore = ((a.top_provider?.popularity_score || 0) / (aPrice * 10000 + 0.001));
                const bScore = ((b.top_provider?.popularity_score || 0) / (bPrice * 10000 + 0.001));
                return bScore - aScore;
            })
            .slice(0, 5)
    );

    let mostPopularModels = $derived(
        [...allModels]
            .sort((a, b) => (b.top_provider?.popularity_score || 0) - (a.top_provider?.popularity_score || 0))
            .slice(0, 5)
    );

    let mostUsedModels = $derived(mostPopularModels); // Popularity ≈ usage

    function formatPrice(pricing: { prompt: number; completion: number } | null): string {
        if (!pricing) return 'N/A';
        const total = pricing.prompt + pricing.completion;
        if (total === 0) return 'FREE';
        return `$${total.toFixed(4)}/M`;
    }

    function formatContext(ctx: number | null): string {
        if (!ctx) return 'N/A';
        if (ctx >= 1000000) return `${(ctx / 1000000).toFixed(0)}M`;
        if (ctx >= 1000) return `${(ctx / 1000).toFixed(0)}K`;
        return ctx.toString();
    }

    function getModelName(id: string): string {
        return id.split('/').pop() || id;
    }

    function filterModels(models: Model[], query: string): Model[] {
        if (!query) return models;
        const q = query.toLowerCase();
        return models.filter(m => 
            m.id.toLowerCase().includes(q) || 
            m.name.toLowerCase().includes(q)
        );
    }

    function selectModelForTier(tier: 'big' | 'middle' | 'small', model: Model) {
        if (onSelect) {
            onSelect(tier, model.id);
        }
        bigTierOpen = false;
        middleTierOpen = false;
        smallTierOpen = false;
    }

    function closeAll() {
        bigTierOpen = false;
        middleTierOpen = false;
        smallTierOpen = false;
    }
</script>

<svelte:window onclick={closeAll} />

<div class="space-y-4">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- BIG Tier -->
        <div class="relative">
            <button
                type="button"
                onclick={(e) => { e.stopPropagation(); bigTierOpen = !bigTierOpen; middleTierOpen = false; smallTierOpen = false; }}
                class="w-full p-4 rounded-lg border text-left transition-all hover:border-purple-500 cursor-pointer"
                style="background-color: var(--base-200); border-color: {bigTierOpen ? 'var(--accent-default)' : 'var(--border-default)'};"
            >
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold uppercase text-purple-400">{tierConfig.big.label}</span>
                    <ChevronDown class="w-4 h-4 transition-transform {bigTierOpen ? 'rotate-180' : ''}" style="color: var(--text-tertiary);" />
                </div>
                <div class="font-mono text-sm truncate" style="color: var(--text-primary);">
                    {currentModels.big ? getModelName(currentModels.big) : 'Select model...'}
                </div>
                <div class="text-xs mt-1" style="color: var(--text-tertiary);">{tierConfig.big.desc}</div>
            </button>

            {#if bigTierOpen}
                <div 
                    class="absolute z-50 w-full mt-2 rounded-lg border overflow-hidden animate-scale-in"
                    style="background-color: var(--base-200); border-color: var(--border-default); max-height: 400px;"
                    onclick={(e) => e.stopPropagation()}
                >
                    <div class="p-2 border-b" style="border-color: var(--border-default);">
                        <input
                            type="text"
                            bind:value={bigSearch}
                            placeholder="Search..."
                            class="w-full px-3 py-2 rounded border text-sm"
                            style="background-color: var(--base-100); border-color: var(--border-default); color: var(--text-primary);"
                        />
                    </div>
                    <div class="overflow-y-auto max-h-72">
                        {#if loading}
                            <div class="p-4 text-center">
                                <Loader2 class="w-6 h-6 animate-spin mx-auto text-cyan-400" />
                            </div>
                        {:else}
                            <!-- Top Free -->
                            <div class="p-2">
                                <div class="text-xs font-bold uppercase px-2 py-1" style="color: var(--text-tertiary);">🆓 Top Free</div>
                                {#each filterModels(topFreeModels, bigSearch) as model}
                                    <button
                                        type="button"
                                        onclick={() => selectModelForTier('big', model)}
                                        class="w-full p-2 rounded text-left hover:bg-[var(--base-300)] cursor-pointer transition-colors"
                                    >
                                        <div class="font-mono text-sm" style="color: var(--text-primary);">{getModelName(model.id)}</div>
                                        <div class="text-xs flex gap-2" style="color: var(--text-tertiary);">
                                            <span>{formatPrice(model.pricing)}</span>
                                            <span>{formatContext(model.context_length)}</span>
                                        </div>
                                    </button>
                                {/each}
                            </div>
                            <!-- Best Value -->
                            <div class="p-2 border-t" style="border-color: var(--border-default);">
                                <div class="text-xs font-bold uppercase px-2 py-1" style="color: var(--text-tertiary);">💎 Best Value</div>
                                {#each filterModels(pricePerfModels, bigSearch) as model}
                                    <button
                                        type="button"
                                        onclick={() => selectModelForTier('big', model)}
                                        class="w-full p-2 rounded text-left hover:bg-[var(--base-300)] cursor-pointer transition-colors"
                                    >
                                        <div class="font-mono text-sm" style="color: var(--text-primary);">{getModelName(model.id)}</div>
                                        <div class="text-xs flex gap-2" style="color: var(--text-tertiary);">
                                            <span>{formatPrice(model.pricing)}</span>
                                            <span>{formatContext(model.context_length)}</span>
                                        </div>
                                    </button>
                                {/each}
                            </div>
                            <!-- Most Popular -->
                            <div class="p-2 border-t" style="border-color: var(--border-default);">
                                <div class="text-xs font-bold uppercase px-2 py-1" style="color: var(--text-tertiary);">🔥 Most Popular</div>
                                {#each filterModels(mostPopularModels, bigSearch) as model}
                                    <button
                                        type="button"
                                        onclick={() => selectModelForTier('big', model)}
                                        class="w-full p-2 rounded text-left hover:bg-[var(--base-300)] cursor-pointer transition-colors"
                                    >
                                        <div class="font-mono text-sm" style="color: var(--text-primary);">{getModelName(model.id)}</div>
                                        <div class="text-xs flex gap-2" style="color: var(--text-tertiary);">
                                            <span>{formatPrice(model.pricing)}</span>
                                            <span>{formatContext(model.context_length)}</span>
                                        </div>
                                    </button>
                                {/each}
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}
        </div>

        <!-- MIDDLE Tier -->
        <div class="relative">
            <button
                type="button"
                onclick={(e) => { e.stopPropagation(); middleTierOpen = !middleTierOpen; bigTierOpen = false; smallTierOpen = false; }}
                class="w-full p-4 rounded-lg border text-left transition-all hover:border-cyan-500 cursor-pointer"
                style="background-color: var(--base-200); border-color: {middleTierOpen ? 'var(--accent-default)' : 'var(--border-default)'};"
            >
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold uppercase text-cyan-400">{tierConfig.middle.label}</span>
                    <ChevronDown class="w-4 h-4 transition-transform {middleTierOpen ? 'rotate-180' : ''}" style="color: var(--text-tertiary);" />
                </div>
                <div class="font-mono text-sm truncate" style="color: var(--text-primary);">
                    {currentModels.middle ? getModelName(currentModels.middle) : 'Select model...'}
                </div>
                <div class="text-xs mt-1" style="color: var(--text-tertiary);">{tierConfig.middle.desc}</div>
            </button>

            {#if middleTierOpen}
                <div 
                    class="absolute z-50 w-full mt-2 rounded-lg border overflow-hidden animate-scale-in"
                    style="background-color: var(--base-200); border-color: var(--border-default); max-height: 400px;"
                    onclick={(e) => e.stopPropagation()}
                >
                    <div class="p-2 border-b" style="border-color: var(--border-default);">
                        <input
                            type="text"
                            bind:value={middleSearch}
                            placeholder="Search..."
                            class="w-full px-3 py-2 rounded border text-sm"
                            style="background-color: var(--base-100); border-color: var(--border-default); color: var(--text-primary);"
                        />
                    </div>
                    <div class="overflow-y-auto max-h-72">
                        {#if loading}
                            <div class="p-4 text-center">
                                <Loader2 class="w-6 h-6 animate-spin mx-auto text-cyan-400" />
                            </div>
                        {:else}
                            {#each filterModels(pricePerfModels, middleSearch) as model}
                                <button
                                    type="button"
                                    onclick={() => selectModelForTier('middle', model)}
                                    class="w-full p-2 rounded text-left hover:bg-[var(--base-300)] cursor-pointer transition-colors"
                                >
                                    <div class="font-mono text-sm" style="color: var(--text-primary);">{getModelName(model.id)}</div>
                                    <div class="text-xs flex gap-2" style="color: var(--text-tertiary);">
                                        <span>{formatPrice(model.pricing)}</span>
                                        <span>{formatContext(model.context_length)}</span>
                                    </div>
                                </button>
                            {/each}
                        {/if}
                    </div>
                </div>
            {/if}
        </div>

        <!-- SMALL Tier -->
        <div class="relative">
            <button
                type="button"
                onclick={(e) => { e.stopPropagation(); smallTierOpen = !smallTierOpen; bigTierOpen = false; middleTierOpen = false; }}
                class="w-full p-4 rounded-lg border text-left transition-all hover:border-green-500 cursor-pointer"
                style="background-color: var(--base-200); border-color: {smallTierOpen ? 'var(--accent-default)' : 'var(--border-default)'};"
            >
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold uppercase text-green-400">{tierConfig.small.label}</span>
                    <ChevronDown class="w-4 h-4 transition-transform {smallTierOpen ? 'rotate-180' : ''}" style="color: var(--text-tertiary);" />
                </div>
                <div class="font-mono text-sm truncate" style="color: var(--text-primary);">
                    {currentModels.small ? getModelName(currentModels.small) : 'Select model...'}
                </div>
                <div class="text-xs mt-1" style="color: var(--text-tertiary);">{tierConfig.small.desc}</div>
            </button>

            {#if smallTierOpen}
                <div 
                    class="absolute z-50 w-full mt-2 rounded-lg border overflow-hidden animate-scale-in"
                    style="background-color: var(--base-200); border-color: var(--border-default); max-height: 400px;"
                    onclick={(e) => e.stopPropagation()}
                >
                    <div class="p-2 border-b" style="border-color: var(--border-default);">
                        <input
                            type="text"
                            bind:value={smallSearch}
                            placeholder="Search..."
                            class="w-full px-3 py-2 rounded border text-sm"
                            style="background-color: var(--base-100); border-color: var(--border-default); color: var(--text-primary);"
                        />
                    </div>
                    <div class="overflow-y-auto max-h-72">
                        {#if loading}
                            <div class="p-4 text-center">
                                <Loader2 class="w-6 h-6 animate-spin mx-auto text-cyan-400" />
                            </div>
                        {:else}
                            {#each filterModels([...allModels].sort((a, b) => {
                                const aPrice = (a.pricing?.prompt || 0) + (a.pricing?.completion || 0);
                                const bPrice = (b.pricing?.prompt || 0) + (b.pricing?.completion || 0);
                                return aPrice - bPrice;
                            }).slice(0, 20), smallSearch) as model}
                                <button
                                    type="button"
                                    onclick={() => selectModelForTier('small', model)}
                                    class="w-full p-2 rounded text-left hover:bg-[var(--base-300)] cursor-pointer transition-colors"
                                >
                                    <div class="font-mono text-sm" style="color: var(--text-primary);">{getModelName(model.id)}</div>
                                    <div class="text-xs flex gap-2" style="color: var(--text-tertiary);">
                                        <span>{formatPrice(model.pricing)}</span>
                                        <span>{formatContext(model.context_length)}</span>
                                    </div>
                                </button>
                            {/each}
                        {/if}
                    </div>
                </div>
            {/if}
        </div>
    </div>

    {#if error}
        <div class="p-3 rounded border text-sm" style="background-color: var(--base-200); border-color: var(--border-default); color: var(--text-secondary);">
            {error}
        </div>
    {/if}
</div>
