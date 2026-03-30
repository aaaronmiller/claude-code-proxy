export interface OpenRouterModel {
    id: string;
    name: string;
    provider: string;
    pricing?: {
        prompt: number;
        completion: number;
    };
    context_length?: number;
    supports_reasoning?: boolean;
    top_provider?: {
        popularity_score: number;
    };
}

export interface ModelCategory {
    id: string;
    name: string;
    description: string;
    icon: string;
    models: OpenRouterModel[];
}

export async function fetchOpenRouterModels(): Promise<OpenRouterModel[]> {
    try {
        const res = await fetch('https://openrouter.ai/api/v1/models');
        if (!res.ok) throw new Error('Failed to fetch models');
        
        const data = await res.json();
        return data.data || [];
    } catch (e) {
        console.error('OpenRouter fetch error:', e);
        return [];
    }
}

export function categorizeModels(models: OpenRouterModel[]): ModelCategory[] {
    const withPricing = models.filter(m => m.pricing && m.top_provider);
    
    const topFree = [...withPricing]
        .filter(m => (m.pricing?.prompt || 0) === 0 && (m.pricing?.completion || 0) === 0)
        .sort((a, b) => (b.top_provider?.popularity_score || 0) - (a.top_provider?.popularity_score || 0))
        .slice(0, 10);
    
    const topPopular = [...withPricing]
        .sort((a, b) => (b.top_provider?.popularity_score || 0) - (a.top_provider?.popularity_score || 0))
        .slice(0, 15);
    
    const pricePerf = [...withPricing]
        .filter(m => m.context_length && m.context_length >= 128000)
        .sort((a, b) => {
            const aPrice = (a.pricing?.prompt || 0) + (a.pricing?.completion || 0);
            const bPrice = (b.pricing?.prompt || 0) + (b.pricing?.completion || 0);
            const aPerf = (a.top_provider?.popularity_score || 0) / (aPrice + 0.0001);
            const bPerf = (b.top_provider?.popularity_score || 0) / (bPrice + 0.0001);
            return bPerf - aPerf;
        })
        .slice(0, 10);
    
    const reasoning = models.filter(m => m.supports_reasoning).slice(0, 10);
    
    const longContext = [...models]
        .filter(m => m.context_length && m.context_length >= 200000)
        .sort((a, b) => (b.context_length || 0) - (a.context_length || 0))
        .slice(0, 10);
    
    const fast = [...withPricing]
        .sort((a, b) => {
            const aPrice = (a.pricing?.prompt || 0) + (a.pricing?.completion || 0);
            const bPrice = (b.pricing?.prompt || 0) + (b.pricing?.completion || 0);
            return aPrice - bPrice;
        })
        .slice(0, 10);

    return [
        {
            id: 'top-free',
            name: 'Top Free',
            description: 'Best free models by popularity',
            icon: '🆓',
            models: topFree
        },
        {
            id: 'best-price-performance',
            name: 'Best Value',
            description: 'Top price/performance ratio',
            icon: '💎',
            models: pricePerf
        },
        {
            id: 'most-popular',
            name: 'Most Popular',
            description: 'Trending models right now',
            icon: '🔥',
            models: topPopular
        },
        {
            id: 'reasoning',
            name: 'Reasoning',
            description: 'Extended thinking models',
            icon: '🧠',
            models: reasoning
        },
        {
            id: 'long-context',
            name: '200K+ Context',
            description: 'Massive context windows',
            icon: '📚',
            models: longContext
        },
        {
            id: 'fast-cheap',
            name: 'Fast & Cheap',
            description: 'Quick & economical',
            icon: '⚡',
            models: fast
        }
    ];
}

export function formatPrice(pricing?: { prompt: number; completion: number }): string {
    if (!pricing) return 'Unknown';
    const total = pricing.prompt + pricing.completion;
    if (total === 0) return 'Free';
    if (total < 0.001) return `$${(total * 1000).toFixed(2)}/1M`;
    return `$${total.toFixed(4)}/1M`;
}

export function formatContext(length?: number): string {
    if (!length) return 'Unknown';
    if (length >= 1000000) return `${(length / 1000000).toFixed(0)}M`;
    if (length >= 1000) return `${(length / 1000).toFixed(0)}K`;
    return length.toString();
}
