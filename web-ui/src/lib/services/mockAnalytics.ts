export function generateMockTimeSeries(days: number = 7) {
    const labels: string[] = [];
    const tokens: number[] = [];
    const cost: number[] = [];
    const requests: number[] = [];
    
    const now = new Date();
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        labels.push(date.toISOString().split('T')[0]);
        
        tokens.push(Math.floor(Math.random() * 500000 + 100000));
        cost.push(Math.random() * 50 + 10);
        requests.push(Math.floor(Math.random() * 5000 + 1000));
    }
    
    return {
        labels,
        datasets: [
            { name: 'Tokens', data: tokens, color: '#8B5CF6' },
            { name: 'Requests', data: requests, color: '#06B6D4' }
        ],
        cost: {
            labels,
            datasets: [{ name: 'Cost ($)', data: cost, color: '#10B981' }]
        },
        requests: {
            labels,
            datasets: [{ name: 'Requests', data: requests, color: '#6366F1' }]
        }
    };
}

export function generateMockAggregate() {
    return {
        total_requests: Math.floor(Math.random() * 50000 + 10000),
        total_tokens: Math.floor(Math.random() * 2000000 + 500000),
        total_cost: Math.random() * 500 + 100,
        avg_latency: Math.floor(Math.random() * 2000 + 500),
        cache_hit_rate: Math.random() * 0.4 + 0.5,
        unique_models: Math.floor(Math.random() * 20 + 5),
        avg_tokens_per_request: Math.floor(Math.random() * 3000 + 1000),
        uptime_percent: 99.5 + Math.random() * 0.5
    };
}

export function generateMockProviderComparison() {
    const providers = [
        { name: 'OpenRouter', color: '#F97316' },
        { name: 'OpenAI', color: '#10B981' },
        { name: 'Anthropic', color: '#8B5CF6' },
        { name: 'Google', color: '#3B82F6' }
    ];
    
    return providers.map(p => ({
        provider: p.name,
        color: p.color,
        requests: Math.floor(Math.random() * 20000 + 5000),
        tokens: Math.floor(Math.random() * 1000000 + 200000),
        cost: Math.random() * 200 + 50,
        avg_latency: Math.floor(Math.random() * 3000 + 1000),
        error_rate: Math.random() * 0.05
    }));
}

export function generateMockModelComparison() {
    const models = [
        'claude-3-5-sonnet',
        'gpt-4o',
        'gpt-4o-mini',
        'gemini-1.5-pro',
        'claude-3-opus'
    ];
    
    return models.map(m => ({
        model: m,
        requests: Math.floor(Math.random() * 10000 + 1000),
        tokens: Math.floor(Math.random() * 500000 + 50000),
        cost: Math.random() * 100 + 20,
        avg_latency: Math.floor(Math.random() * 5000 + 500),
        popularity: Math.random()
    })).sort((a, b) => b.popularity - a.popularity);
}

export function generateMockTopEndpoints() {
    return [
        { endpoint: '/v1/chat/completions', method: 'POST', requests: 45230, avg_latency: 1200, error_rate: 0.02 },
        { endpoint: '/v1/completions', method: 'POST', requests: 12450, avg_latency: 800, error_rate: 0.01 },
        { endpoint: '/v1/embeddings', method: 'POST', requests: 8920, avg_latency: 300, error_rate: 0.005 },
        { endpoint: '/health', method: 'GET', requests: 5230, avg_latency: 5, error_rate: 0 },
        { endpoint: '/api/models', method: 'GET', requests: 3210, avg_latency: 50, error_rate: 0.01 }
    ];
}
