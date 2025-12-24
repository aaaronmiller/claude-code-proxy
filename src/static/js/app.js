// Claude Code Proxy - Web UI JavaScript
// Cyberpunk Terminal Theme

// ═══════════════════════════════════════════════════════════════
// TAB SWITCHING
// ═══════════════════════════════════════════════════════════════

function switchTab(tabName, buttonEl = null) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const tabEl = document.getElementById(`${tabName}-tab`);
    if (tabEl) tabEl.classList.add('active');

    // Activate the clicked button (handle both direct calls and event-based)
    if (buttonEl) {
        buttonEl.classList.add('active');
    } else if (event && event.target) {
        event.target.classList.add('active');
    }

    // Load data for the tab
    if (tabName === 'profiles') {
        loadProfiles();
    } else if (tabName === 'models') {
        loadModels();
    } else if (tabName === 'monitor') {
        refreshStats();
    } else if (tabName === 'logs') {
        connectWebSocket();
    }
}

// HTML entity escape helper to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ═══════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ═══════════════════════════════════════════════════════════════
// PROXY STATUS
// ═══════════════════════════════════════════════════════════════

async function checkProxyStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        const indicator = document.getElementById('proxy-status');
        const statusText = document.getElementById('proxy-status-text');

        if (data.status === 'healthy') {
            indicator.classList.add('online');
            indicator.classList.remove('offline');
            statusText.textContent = 'Online';
        } else {
            indicator.classList.add('offline');
            indicator.classList.remove('online');
            statusText.textContent = 'Unhealthy';
        }
    } catch (error) {
        const indicator = document.getElementById('proxy-status');
        const statusText = document.getElementById('proxy-status-text');
        indicator.classList.add('offline');
        indicator.classList.remove('online');
        statusText.textContent = 'Offline';
    }
}

// ═══════════════════════════════════════════════════════════════
// PROVIDER PRESETS
// ═══════════════════════════════════════════════════════════════

const providerPresets = {
    vibeproxy: {
        apiKey: 'dummy',
        baseUrl: 'http://127.0.0.1:8317/v1',
        bigModel: 'gemini-claude-opus-4-5-thinking',
        middleModel: 'gemini-3-pro-preview',
        smallModel: 'gemini-3-flash',
        reasoningMaxTokens: '128000'
    },
    openrouter: {
        apiKey: '',
        baseUrl: 'https://openrouter.ai/api/v1',
        bigModel: 'anthropic/claude-sonnet-4',
        middleModel: 'anthropic/claude-sonnet-4',
        smallModel: 'google/gemini-flash-1.5'
    },
    gemini: {
        apiKey: '',
        baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
        bigModel: 'gemini-2.5-pro-preview-03-25',
        middleModel: 'gemini-2.5-flash-preview-04-17',
        smallModel: 'gemini-2.5-flash-preview-04-17'
    },
    openai: {
        apiKey: '',
        baseUrl: 'https://api.openai.com/v1',
        bigModel: 'gpt-4o',
        middleModel: 'gpt-4o',
        smallModel: 'gpt-4o-mini'
    },
    ollama: {
        apiKey: 'dummy',
        baseUrl: 'http://localhost:11434/v1',
        bigModel: 'qwen2.5:72b',
        middleModel: 'qwen2.5:72b',
        smallModel: 'qwen2.5:7b'
    },
    lmstudio: {
        apiKey: 'dummy',
        baseUrl: 'http://127.0.0.1:1234/v1',
        bigModel: 'local-model',
        middleModel: 'local-model',
        smallModel: 'local-model'
    }
};

function applyProviderPreset() {
    const preset = document.getElementById('provider-preset').value;
    if (!preset || !providerPresets[preset]) return;

    const p = providerPresets[preset];
    document.getElementById('provider-api-key').value = p.apiKey;
    document.getElementById('provider-base-url').value = p.baseUrl;
    document.getElementById('big-model').value = p.bigModel || '';
    document.getElementById('middle-model').value = p.middleModel || '';
    document.getElementById('small-model').value = p.smallModel || '';

    if (p.reasoningMaxTokens) {
        document.getElementById('reasoning-max-tokens').value = p.reasoningMaxTokens;
    }

    // Update provider display
    document.getElementById('current-provider').textContent = preset.charAt(0).toUpperCase() + preset.slice(1);

    showToast(`Applied ${preset} preset`, 'success');
}

// ═══════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        // Core settings
        document.getElementById('provider-api-key').value = config.provider_api_key || config.openai_api_key || '';
        document.getElementById('provider-base-url').value = config.provider_base_url || config.openai_base_url || '';
        document.getElementById('proxy-auth-key').value = config.proxy_auth_key || config.anthropic_api_key || '';

        // Server settings
        if (document.getElementById('server-host')) {
            document.getElementById('server-host').value = config.host || '0.0.0.0';
        }
        if (document.getElementById('server-port')) {
            document.getElementById('server-port').value = config.port || '8082';
        }
        if (document.getElementById('log-level')) {
            document.getElementById('log-level').value = config.log_level || 'INFO';
        }

        // Model settings
        document.getElementById('big-model').value = config.big_model || '';
        document.getElementById('middle-model').value = config.middle_model || '';
        document.getElementById('small-model').value = config.small_model || '';

        // Reasoning settings
        document.getElementById('reasoning-effort').value = config.reasoning_effort || '';
        document.getElementById('reasoning-max-tokens').value = config.reasoning_max_tokens || '';
        if (document.getElementById('reasoning-exclude')) {
            document.getElementById('reasoning-exclude').checked = config.reasoning_exclude === 'true';
        }

        // Token limits
        if (document.getElementById('max-tokens-limit')) {
            document.getElementById('max-tokens-limit').value = config.max_tokens_limit || '65536';
        }
        if (document.getElementById('min-tokens-limit')) {
            document.getElementById('min-tokens-limit').value = config.min_tokens_limit || '4096';
        }
        if (document.getElementById('request-timeout')) {
            document.getElementById('request-timeout').value = config.request_timeout || '120';
        }

        // Terminal settings
        if (document.getElementById('terminal-display-mode')) {
            document.getElementById('terminal-display-mode').value = config.terminal_display_mode || 'detailed';
        }
        if (document.getElementById('terminal-color-scheme')) {
            document.getElementById('terminal-color-scheme').value = config.terminal_color_scheme || 'auto';
        }
        if (document.getElementById('log-style')) {
            document.getElementById('log-style').value = config.log_style || 'rich';
        }

        // Checkboxes
        setCheckbox('terminal-show-workspace', config.terminal_show_workspace);
        setCheckbox('terminal-show-context-pct', config.terminal_show_context_pct);
        setCheckbox('terminal-show-task-type', config.terminal_show_task_type);
        setCheckbox('terminal-show-speed', config.terminal_show_speed);
        setCheckbox('terminal-show-cost', config.terminal_show_cost);
        setCheckbox('terminal-show-duration-colors', config.terminal_show_duration_colors);
        setCheckbox('terminal-session-colors', config.terminal_session_colors);
        setCheckbox('compact-logger', config.compact_logger || config.use_compact_logger);
        setCheckbox('track-usage', config.track_usage);
        setCheckbox('enable-dashboard', config.enable_dashboard);

        // Dashboard settings
        if (document.getElementById('dashboard-layout')) {
            document.getElementById('dashboard-layout').value = config.dashboard_layout || 'default';
        }
        if (document.getElementById('dashboard-refresh')) {
            document.getElementById('dashboard-refresh').value = config.dashboard_refresh || '0.5';
        }

        // Hybrid mode
        loadHybridConfig(config);

        // Update mode indicator
        const modeText = config.passthrough_mode ? 'Passthrough' : 'Proxy';
        document.getElementById('current-mode').textContent = modeText;
        document.getElementById('current-mode').style.color = config.passthrough_mode ? 'var(--accent-amber)' : 'var(--accent-green)';

        // Update provider display
        const providerUrl = config.provider_base_url || config.openai_base_url || '';
        let providerName = 'Unknown';
        if (providerUrl.includes('127.0.0.1:8317')) providerName = 'VibeProxy';
        else if (providerUrl.includes('openrouter')) providerName = 'OpenRouter';
        else if (providerUrl.includes('googleapis')) providerName = 'Gemini';
        else if (providerUrl.includes('openai.com')) providerName = 'OpenAI';
        else if (providerUrl.includes('11434')) providerName = 'Ollama';
        else if (providerUrl.includes('1234')) providerName = 'LM Studio';
        document.getElementById('current-provider').textContent = providerName;

    } catch (error) {
        showToast('Failed to load configuration', 'error');
        console.error(error);
    }
}

function setCheckbox(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.checked = value === 'true' || value === true;
    }
}

function loadHybridConfig(config) {
    // BIG endpoint
    const bigEnabled = config.enable_big_endpoint === 'true';
    setCheckbox('enable-big-endpoint', bigEnabled);
    toggleHybridSection('big', bigEnabled);
    if (document.getElementById('big-endpoint')) {
        document.getElementById('big-endpoint').value = config.big_endpoint || '';
    }
    if (document.getElementById('big-api-key')) {
        document.getElementById('big-api-key').value = config.big_api_key || '';
    }

    // MIDDLE endpoint
    const middleEnabled = config.enable_middle_endpoint === 'true';
    setCheckbox('enable-middle-endpoint', middleEnabled);
    toggleHybridSection('middle', middleEnabled);
    if (document.getElementById('middle-endpoint')) {
        document.getElementById('middle-endpoint').value = config.middle_endpoint || '';
    }
    if (document.getElementById('middle-api-key')) {
        document.getElementById('middle-api-key').value = config.middle_api_key || '';
    }

    // SMALL endpoint
    const smallEnabled = config.enable_small_endpoint === 'true';
    setCheckbox('enable-small-endpoint', smallEnabled);
    toggleHybridSection('small', smallEnabled);
    if (document.getElementById('small-endpoint')) {
        document.getElementById('small-endpoint').value = config.small_endpoint || '';
    }
    if (document.getElementById('small-api-key')) {
        document.getElementById('small-api-key').value = config.small_api_key || '';
    }
}

function toggleHybridSection(tier, forceState = null) {
    const checkbox = document.getElementById(`enable-${tier}-endpoint`);
    const section = document.getElementById(`${tier}-hybrid-section`);

    if (section) {
        const isEnabled = forceState !== null ? forceState : checkbox.checked;
        section.style.display = isEnabled ? 'block' : 'none';
    }
}

async function saveConfig() {
    const config = {
        // Core
        provider_api_key: document.getElementById('provider-api-key').value,
        provider_base_url: document.getElementById('provider-base-url').value,
        proxy_auth_key: document.getElementById('proxy-auth-key').value,

        // Server
        host: document.getElementById('server-host')?.value || '0.0.0.0',
        port: document.getElementById('server-port')?.value || '8082',
        log_level: document.getElementById('log-level')?.value || 'INFO',

        // Models
        big_model: document.getElementById('big-model').value,
        middle_model: document.getElementById('middle-model').value,
        small_model: document.getElementById('small-model').value,

        // Reasoning
        reasoning_effort: document.getElementById('reasoning-effort').value,
        reasoning_max_tokens: document.getElementById('reasoning-max-tokens').value,
        reasoning_exclude: document.getElementById('reasoning-exclude')?.checked ? 'true' : 'false',

        // Token limits
        max_tokens_limit: document.getElementById('max-tokens-limit')?.value || '65536',
        min_tokens_limit: document.getElementById('min-tokens-limit')?.value || '4096',
        request_timeout: document.getElementById('request-timeout')?.value || '120',

        // Terminal
        terminal_display_mode: document.getElementById('terminal-display-mode')?.value || 'detailed',
        terminal_color_scheme: document.getElementById('terminal-color-scheme')?.value || 'auto',
        log_style: document.getElementById('log-style')?.value || 'rich',
        terminal_show_workspace: document.getElementById('terminal-show-workspace')?.checked ? 'true' : 'false',
        terminal_show_context_pct: document.getElementById('terminal-show-context-pct')?.checked ? 'true' : 'false',
        terminal_show_task_type: document.getElementById('terminal-show-task-type')?.checked ? 'true' : 'false',
        terminal_show_speed: document.getElementById('terminal-show-speed')?.checked ? 'true' : 'false',
        terminal_show_cost: document.getElementById('terminal-show-cost')?.checked ? 'true' : 'false',
        terminal_show_duration_colors: document.getElementById('terminal-show-duration-colors')?.checked ? 'true' : 'false',
        terminal_session_colors: document.getElementById('terminal-session-colors')?.checked ? 'true' : 'false',
        compact_logger: document.getElementById('compact-logger')?.checked ? 'true' : 'false',

        // Dashboard
        track_usage: document.getElementById('track-usage')?.checked ? 'true' : 'false',
        enable_dashboard: document.getElementById('enable-dashboard')?.checked ? 'true' : 'false',
        dashboard_layout: document.getElementById('dashboard-layout')?.value || 'default',
        dashboard_refresh: document.getElementById('dashboard-refresh')?.value || '0.5',

        // Hybrid mode
        enable_big_endpoint: document.getElementById('enable-big-endpoint')?.checked ? 'true' : 'false',
        big_endpoint: document.getElementById('big-endpoint')?.value || '',
        big_api_key: document.getElementById('big-api-key')?.value || '',
        enable_middle_endpoint: document.getElementById('enable-middle-endpoint')?.checked ? 'true' : 'false',
        middle_endpoint: document.getElementById('middle-endpoint')?.value || '',
        middle_api_key: document.getElementById('middle-api-key')?.value || '',
        enable_small_endpoint: document.getElementById('enable-small-endpoint')?.checked ? 'true' : 'false',
        small_endpoint: document.getElementById('small-endpoint')?.value || '',
        small_api_key: document.getElementById('small-api-key')?.value || ''
    };

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            showToast('Configuration saved!', 'success');
            loadConfig();
        } else {
            const error = await response.json();
            showToast(`Failed to save: ${error.detail}`, 'error');
        }
    } catch (error) {
        showToast('Failed to save configuration', 'error');
        console.error(error);
    }
}

async function reloadConfig() {
    try {
        const response = await fetch('/api/config/reload', { method: 'POST' });
        if (response.ok) {
            showToast('Configuration reloaded', 'success');
            loadConfig();
        } else {
            showToast('Failed to reload', 'error');
        }
    } catch (error) {
        showToast('Failed to reload', 'error');
        console.error(error);
    }
}

async function testConnection() {
    showToast('Testing connection...', 'info');
    try {
        const response = await fetch('/api/test-connection', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            showToast('Connection successful!', 'success');
        } else {
            showToast(`Connection failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Connection test failed', 'error');
        console.error(error);
    }
}

function exportConfig() {
    const fields = [
        ['PROVIDER_API_KEY', 'provider-api-key'],
        ['PROVIDER_BASE_URL', 'provider-base-url'],
        ['PROXY_AUTH_KEY', 'proxy-auth-key'],
        ['BIG_MODEL', 'big-model'],
        ['MIDDLE_MODEL', 'middle-model'],
        ['SMALL_MODEL', 'small-model'],
        ['REASONING_EFFORT', 'reasoning-effort'],
        ['REASONING_MAX_TOKENS', 'reasoning-max-tokens'],
        ['HOST', 'server-host'],
        ['PORT', 'server-port'],
        ['LOG_LEVEL', 'log-level']
    ];

    const envContent = fields
        .map(([key, id]) => {
            const el = document.getElementById(id);
            const value = el ? el.value : '';
            return value ? `${key}="${value}"` : null;
        })
        .filter(Boolean)
        .join('\n');

    const blob = new Blob([envContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'config.env';
    a.click();
    URL.revokeObjectURL(url);

    showToast('Configuration exported', 'success');
}

function importConfig() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.env,.txt';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const text = await file.text();
        const lines = text.split('\n');

        lines.forEach(line => {
            const match = line.match(/^([A-Z_]+)="?([^"]*)"?$/);
            if (match) {
                const [, key, value] = match;
                const fieldMap = {
                    'PROVIDER_API_KEY': 'provider-api-key',
                    'PROVIDER_BASE_URL': 'provider-base-url',
                    'PROXY_AUTH_KEY': 'proxy-auth-key',
                    'BIG_MODEL': 'big-model',
                    'MIDDLE_MODEL': 'middle-model',
                    'SMALL_MODEL': 'small-model'
                };
                const fieldId = fieldMap[key];
                if (fieldId) {
                    const el = document.getElementById(fieldId);
                    if (el) el.value = value;
                }
            }
        });

        showToast('Configuration imported', 'success');
    };
    input.click();
}

// ═══════════════════════════════════════════════════════════════
// PROFILES
// ═══════════════════════════════════════════════════════════════

async function loadProfiles() {
    try {
        const response = await fetch('/api/profiles');
        const profiles = await response.json();

        const listDiv = document.getElementById('profiles-list');
        if (profiles.length === 0) {
            listDiv.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">No profiles saved yet</p>';
            return;
        }

        listDiv.innerHTML = profiles.map(profile => {
            const safeName = escapeHtml(profile.name);
            const safeNameAttr = safeName.replace(/'/g, "\\'");
            return `
            <div class="profile-item">
                <div>
                    <strong style="color: var(--accent-cyan);">${safeName}</strong>
                    <span style="color: var(--text-muted); font-size: 0.8rem; margin-left: 1rem;">
                        ${escapeHtml(profile.big_model || 'No model')} / ${escapeHtml(profile.middle_model || '-')} / ${escapeHtml(profile.small_model || '-')}
                    </span>
                </div>
                <div>
                    <button class="btn btn-secondary" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;" onclick="loadProfile('${safeNameAttr}')">Load</button>
                    <button class="btn btn-danger" style="padding: 0.25rem 0.75rem; font-size: 0.8rem; margin-left: 0.5rem;" onclick="deleteProfile('${safeNameAttr}')">Delete</button>
                </div>
            </div>
        `}).join('');
    } catch (error) {
        showToast('Failed to load profiles', 'error');
        console.error(error);
    }
}

async function saveProfile() {
    const profileName = document.getElementById('new-profile-name').value.trim();
    if (!profileName) {
        showToast('Enter a profile name', 'warning');
        return;
    }

    const config = {
        provider_api_key: document.getElementById('provider-api-key').value,
        provider_base_url: document.getElementById('provider-base-url').value,
        big_model: document.getElementById('big-model').value,
        middle_model: document.getElementById('middle-model').value,
        small_model: document.getElementById('small-model').value,
        reasoning_effort: document.getElementById('reasoning-effort').value,
        reasoning_max_tokens: document.getElementById('reasoning-max-tokens').value
    };

    try {
        const response = await fetch('/api/profiles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: profileName, config })
        });

        if (response.ok) {
            showToast(`Profile "${profileName}" saved`, 'success');
            document.getElementById('new-profile-name').value = '';
            loadProfiles();
        } else {
            showToast('Failed to save profile', 'error');
        }
    } catch (error) {
        showToast('Failed to save profile', 'error');
        console.error(error);
    }
}

async function loadProfile(name) {
    try {
        const response = await fetch(`/api/profiles/${encodeURIComponent(name)}`);
        const profile = await response.json();

        document.getElementById('provider-api-key').value = profile.config.provider_api_key || '';
        document.getElementById('provider-base-url').value = profile.config.provider_base_url || '';
        document.getElementById('big-model').value = profile.config.big_model || '';
        document.getElementById('middle-model').value = profile.config.middle_model || '';
        document.getElementById('small-model').value = profile.config.small_model || '';
        document.getElementById('reasoning-effort').value = profile.config.reasoning_effort || '';
        document.getElementById('reasoning-max-tokens').value = profile.config.reasoning_max_tokens || '';

        // Switch to config tab (find and pass the button element)
        const configBtn = document.querySelector('.tab-button');
        switchTab('config', configBtn);
        showToast(`Profile "${name}" loaded`, 'success');
    } catch (error) {
        showToast('Failed to load profile', 'error');
        console.error(error);
    }
}

async function deleteProfile(name) {
    if (!confirm(`Delete profile "${name}"?`)) return;

    try {
        const response = await fetch(`/api/profiles/${encodeURIComponent(name)}`, { method: 'DELETE' });
        if (response.ok) {
            showToast(`Profile "${name}" deleted`, 'success');
            loadProfiles();
        } else {
            showToast('Failed to delete profile', 'error');
        }
    } catch (error) {
        showToast('Failed to delete profile', 'error');
        console.error(error);
    }
}

// ═══════════════════════════════════════════════════════════════
// MODELS
// ═══════════════════════════════════════════════════════════════

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();

        const listDiv = document.getElementById('models-list');
        if (!models || models.length === 0) {
            listDiv.innerHTML = '<p style="color: var(--text-muted);">No models available. Check provider connection.</p>';
            return;
        }

        listDiv.innerHTML = models.slice(0, 50).map(model => {
            const safeId = escapeHtml(model.id);
            const safeIdAttr = safeId.replace(/'/g, "\\'");
            return `
            <div class="model-item" data-provider="${escapeHtml(model.provider || '')}" onclick="selectModel('${safeIdAttr}')">
                <div>
                    <strong style="color: var(--text-primary);">${safeId}</strong>
                    ${model.context_length ? `<span style="color: var(--text-muted); font-size: 0.8rem; margin-left: 0.5rem;">${(model.context_length / 1000).toFixed(0)}k ctx</span>` : ''}
                </div>
                <div>
                    ${model.pricing && model.pricing.prompt === '0' ? '<span style="color: var(--accent-green); font-size: 0.75rem;">FREE</span>' : ''}
                </div>
            </div>
        `}).join('');
    } catch (error) {
        document.getElementById('models-list').innerHTML = '<p style="color: var(--accent-red);">Failed to load models</p>';
        console.error(error);
    }
}

function filterModels() {
    const searchTerm = document.getElementById('model-search').value.toLowerCase();
    const providerFilter = document.getElementById('model-provider-filter').value.toLowerCase();

    document.querySelectorAll('.model-item').forEach(item => {
        const modelName = item.querySelector('strong').textContent.toLowerCase();
        const matchesSearch = modelName.includes(searchTerm);
        const matchesProvider = !providerFilter || modelName.includes(providerFilter);
        item.style.display = (matchesSearch && matchesProvider) ? 'flex' : 'none';
    });
}

function selectModel(modelId) {
    navigator.clipboard.writeText(modelId);
    showToast(`Copied: ${modelId}`, 'success');
}

// ═══════════════════════════════════════════════════════════════
// MONITOR & STATS
// ═══════════════════════════════════════════════════════════════

async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('requests-today').textContent = stats.requests_today || '0';
        document.getElementById('total-tokens').textContent = stats.total_tokens ? stats.total_tokens.toLocaleString() : '0';
        document.getElementById('est-cost').textContent = stats.est_cost ? `$${stats.est_cost.toFixed(2)}` : '$0.00';
        document.getElementById('avg-latency').textContent = stats.avg_latency ? `${stats.avg_latency}ms` : '-';

        if (stats.recent_requests) {
            const requestsDiv = document.getElementById('recent-requests');
            requestsDiv.innerHTML = stats.recent_requests.map(req => `
                <div class="request-item">
                    <span style="color: var(--accent-cyan);">${req.model}</span>
                    <span style="color: ${req.status === 'success' ? 'var(--accent-green)' : 'var(--accent-red)'};">
                        ${req.tokens || '-'} tokens | ${req.duration || '-'}ms
                    </span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function checkProviderHealth() {
    const healthEl = document.getElementById('main-provider-health');
    healthEl.textContent = '⏳ Checking...';
    healthEl.style.color = 'var(--accent-amber)';

    try {
        const response = await fetch('/api/test-connection', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            healthEl.textContent = '● Healthy';
            healthEl.style.color = 'var(--accent-green)';
        } else {
            healthEl.textContent = '● Unhealthy';
            healthEl.style.color = 'var(--accent-red)';
        }
    } catch (error) {
        healthEl.textContent = '● Error';
        healthEl.style.color = 'var(--accent-red)';
    }
}

// ═══════════════════════════════════════════════════════════════
// LIVE LOGS (WebSocket)
// ═══════════════════════════════════════════════════════════════

let logsWebSocket = null;
let wsReconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

function connectWebSocket() {
    if (logsWebSocket && logsWebSocket.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

    try {
        logsWebSocket = new WebSocket(wsUrl);

        logsWebSocket.onopen = () => {
            wsReconnectAttempts = 0;
            addLogEntry('[Connected to log stream]', 'success');
        };

        logsWebSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            addLogEntry(data.message, data.level || 'info');
        };

        logsWebSocket.onclose = () => {
            addLogEntry('[Disconnected from log stream]', 'warning');
            // Auto-reconnect with exponential backoff
            if (wsReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                wsReconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, wsReconnectAttempts), 30000);
                setTimeout(connectWebSocket, delay);
            }
        };

        logsWebSocket.onerror = () => {
            addLogEntry('[WebSocket error - logs unavailable]', 'error');
        };
    } catch (e) {
        addLogEntry('[WebSocket not available]', 'error');
    }
}

function addLogEntry(message, level = 'info') {
    const logsDiv = document.getElementById('live-logs');
    const colors = {
        info: 'var(--accent-cyan)',
        warning: 'var(--accent-amber)',
        error: 'var(--accent-red)',
        success: 'var(--accent-green)'
    };

    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.style.color = colors[level] || 'var(--text-primary)';
    entry.textContent = `[${timestamp}] ${message}`;
    entry.dataset.level = level;

    logsDiv.appendChild(entry);
    logsDiv.scrollTop = logsDiv.scrollHeight;

    // Limit to 100 entries
    while (logsDiv.children.length > 100) {
        logsDiv.removeChild(logsDiv.firstChild);
    }
}

function clearLogs() {
    const logsDiv = document.getElementById('live-logs');
    logsDiv.innerHTML = '<div style="color: var(--text-muted);">[Logs cleared]</div>';
}

function filterLogs() {
    const filterText = document.getElementById('log-filter').value.toLowerCase();
    const levelFilter = document.getElementById('log-level-filter').value.toLowerCase();

    document.querySelectorAll('#live-logs > div').forEach(entry => {
        const text = entry.textContent.toLowerCase();
        const matchesText = !filterText || text.includes(filterText);
        const matchesLevel = !levelFilter || entry.dataset.level === levelFilter;
        entry.style.display = (matchesText && matchesLevel) ? 'block' : 'none';
    });
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

window.addEventListener('DOMContentLoaded', () => {
    checkProxyStatus();
    loadConfig();

    // Refresh status every 30 seconds
    setInterval(checkProxyStatus, 30000);
});
