// Claude Code Proxy - Modern Web UI JavaScript

// ═══════════════════════════════════════════════════════════════
// PAGE NAVIGATION
// ═══════════════════════════════════════════════════════════════

const pageNames = {
    dashboard: 'Dashboard',
    monitor: 'Monitor',
    core: 'Provider',
    models: 'Models',
    routing: 'Routing',
    terminal: 'Terminal',
    profiles: 'Profiles',
    logs: 'Logs'
};

function switchPage(pageName, buttonEl) {
    // Hide all pages
    document.querySelectorAll('.page-section').forEach(page => {
        page.style.display = 'none';
    });
    
    // Show selected page
    const pageEl = document.getElementById(`page-${pageName}`);
    if (pageEl) {
        pageEl.style.display = 'block';
        pageEl.classList.add('animate-slide-up');
    }
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (buttonEl) {
        buttonEl.classList.add('active');
    } else {
        const btn = document.querySelector(`[data-page="${pageName}"]`);
        if (btn) btn.classList.add('active');
    }
    
    // Update title
    document.getElementById('page-title').textContent = pageNames[pageName] || pageName;
    
    // Load data for page
    if (pageName === 'profiles') {
        loadProfiles();
    } else if (pageName === 'models') {
        loadModels();
        loadFreeRecommended();
    } else if (pageName === 'monitor') {
        refreshStats();
    } else if (pageName === 'logs') {
        connectWebSocket();
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ═══════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════

function showToast(message, type = 'success') {
    const container = document.getElementById('toast');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            ${type === 'success' ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>' : 
              type === 'error' ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' :
              type === 'warning' ? '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>' :
              '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'}
        </svg>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
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
            indicator.classList.remove('offline');
            statusText.textContent = 'Online';
        } else {
            indicator.classList.add('offline');
            statusText.textContent = 'Unhealthy';
        }
    } catch (error) {
        const indicator = document.getElementById('proxy-status');
        const statusText = document.getElementById('proxy-status-text');
        indicator.classList.add('offline');
        statusText.textContent = 'Offline';
    }
}

// ═══════════════════════════════════════════════════════════════
// PROVIDER PRESETS
// ═══════════════════════════════════════════════════════════════

const providerPresets = {
    vibeproxy: { apiKey: 'dummy', baseUrl: 'http://127.0.0.1:8317/v1', bigModel: '', middleModel: '', smallModel: '' },
    openrouter: { apiKey: '', baseUrl: 'https://openrouter.ai/api/v1', bigModel: 'anthropic/claude-sonnet-4', middleModel: 'anthropic/claude-sonnet-4', smallModel: 'google/gemini-flash-1.5' },
    gemini: { apiKey: '', baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/', bigModel: 'gemini-2.5-pro-preview-03-25', middleModel: 'gemini-2.5-flash-preview-04-17', smallModel: 'gemini-2.5-flash-preview-04-17' },
    openai: { apiKey: '', baseUrl: 'https://api.openai.com/v1', bigModel: 'gpt-4o', middleModel: 'gpt-4o', smallModel: 'gpt-4o-mini' },
    ollama: { apiKey: 'dummy', baseUrl: 'http://localhost:11434/v1', bigModel: 'qwen2.5:72b', middleModel: 'qwen2.5:72b', smallModel: 'qwen2.5:7b' },
    lmstudio: { apiKey: 'dummy', baseUrl: 'http://127.0.0.1:1234/v1', bigModel: 'local-model', middleModel: 'local-model', smallModel: 'local-model' }
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
        const hostEl = document.getElementById('server-host');
        if (hostEl) hostEl.value = config.host || '0.0.0.0';
        const portEl = document.getElementById('server-port');
        if (portEl) portEl.value = config.port || '8082';
        const logLevelEl = document.getElementById('log-level');
        if (logLevelEl) logLevelEl.value = config.log_level || 'INFO';
        
        // Model settings
        document.getElementById('big-model').value = config.big_model || '';
        document.getElementById('middle-model').value = config.middle_model || '';
        document.getElementById('small-model').value = config.small_model || '';
        
        // Reasoning settings
        document.getElementById('reasoning-effort').value = config.reasoning_effort || '';
        const reasoningTokensEl = document.getElementById('reasoning-max-tokens');
        if (reasoningTokensEl) reasoningTokensEl.value = config.reasoning_max_tokens || '';
        const reasoningExcludeEl = document.getElementById('reasoning-exclude');
        if (reasoningExcludeEl) reasoningExcludeEl.checked = config.reasoning_exclude === 'true';
        
        // Terminal settings
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
        
        const displayModeEl = document.getElementById('terminal-display-mode');
        if (displayModeEl) displayModeEl.value = config.terminal_display_mode || 'detailed';
        const colorSchemeEl = document.getElementById('terminal-color-scheme');
        if (colorSchemeEl) colorSchemeEl.value = config.terminal_color_scheme || 'auto';
        const logStyleEl = document.getElementById('log-style');
        if (logStyleEl) logStyleEl.value = config.log_style || 'rich';
        const dashboardLayoutEl = document.getElementById('dashboard-layout');
        if (dashboardLayoutEl) dashboardLayoutEl.value = config.dashboard_layout || 'default';
        const dashboardRefreshEl = document.getElementById('dashboard-refresh');
        if (dashboardRefreshEl) dashboardRefreshEl.value = config.dashboard_refresh || '0.5';
        
        // Cascade settings
        setCheckbox('model-cascade', config.model_cascade);
        const bigCascadeEl = document.getElementById('big-cascade');
        if (bigCascadeEl) bigCascadeEl.value = config.big_cascade || '';
        const middleCascadeEl = document.getElementById('middle-cascade');
        if (middleCascadeEl) middleCascadeEl.value = config.middle_cascade || '';
        const smallCascadeEl = document.getElementById('small-cascade');
        if (smallCascadeEl) smallCascadeEl.value = config.small_cascade || '';
        const cascadeLimitEl = document.getElementById('model-cascade-daily-limit');
        if (cascadeLimitEl) cascadeLimitEl.value = config.model_cascade_daily_limit || '1000';
        
        // Hybrid mode
        loadHybridConfig(config);
        
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
        
        // Update routing visualizer
        updateRoutingVisualizer(config);
        
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

function setCheckbox(id, value) {
    const el = document.getElementById(id);
    if (el) el.checked = value === 'true' || value === true;
}

function loadHybridConfig(config) {
    const bigEnabled = config.enable_big_endpoint === 'true';
    setCheckbox('enable-big-endpoint', bigEnabled);
    toggleHybridSection('big', bigEnabled);
    if (document.getElementById('big-endpoint')) document.getElementById('big-endpoint').value = config.big_endpoint || '';
    if (document.getElementById('big-api-key')) document.getElementById('big-api-key').value = config.big_api_key || '';
    
    const middleEnabled = config.enable_middle_endpoint === 'true';
    setCheckbox('enable-middle-endpoint', middleEnabled);
    toggleHybridSection('middle', middleEnabled);
    if (document.getElementById('middle-endpoint')) document.getElementById('middle-endpoint').value = config.middle_endpoint || '';
    if (document.getElementById('middle-api-key')) document.getElementById('middle-api-key').value = config.middle_api_key || '';
    
    const smallEnabled = config.enable_small_endpoint === 'true';
    setCheckbox('enable-small-endpoint', smallEnabled);
    toggleHybridSection('small', smallEnabled);
    if (document.getElementById('small-endpoint')) document.getElementById('small-endpoint').value = config.small_endpoint || '';
    if (document.getElementById('small-api-key')) document.getElementById('small-api-key').value = config.small_api_key || '';
}

function toggleHybridSection(tier, forceState = null) {
    const checkbox = document.getElementById(`enable-${tier}-endpoint`);
    const section = document.getElementById(`${tier}-hybrid-section`);
    if (section) {
        const isEnabled = forceState !== null ? forceState : checkbox.checked;
        section.style.display = isEnabled ? 'block' : 'none';
    }
}

function updateRoutingVisualizer(config) {
    const bigEl = document.getElementById('route-big');
    const middleEl = document.getElementById('route-middle');
    const smallEl = document.getElementById('route-small');
    const modeEl = document.getElementById('routing-mode');
    
    if (bigEl) bigEl.textContent = config.big_model || 'Not set';
    if (middleEl) middleEl.textContent = config.middle_model || 'Not set';
    if (smallEl) smallEl.textContent = config.small_model || 'Not set';
    if (modeEl) modeEl.textContent = config.passthrough_mode ? 'Passthrough Mode' : 'Proxy Mode';
}

async function saveConfig() {
    const config = {
        provider_api_key: document.getElementById('provider-api-key').value,
        provider_base_url: document.getElementById('provider-base-url').value,
        proxy_auth_key: document.getElementById('proxy-auth-key').value,
        host: document.getElementById('server-host')?.value || '0.0.0.0',
        port: document.getElementById('server-port')?.value || '8082',
        log_level: document.getElementById('log-level')?.value || 'INFO',
        big_model: document.getElementById('big-model').value,
        middle_model: document.getElementById('middle-model').value,
        small_model: document.getElementById('small-model').value,
        reasoning_effort: document.getElementById('reasoning-effort').value,
        reasoning_max_tokens: document.getElementById('reasoning-max-tokens')?.value,
        reasoning_exclude: document.getElementById('reasoning-exclude')?.checked ? 'true' : 'false',
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
        track_usage: document.getElementById('track-usage')?.checked ? 'true' : 'false',
        enable_dashboard: document.getElementById('enable-dashboard')?.checked ? 'true' : 'false',
        dashboard_layout: document.getElementById('dashboard-layout')?.value || 'default',
        dashboard_refresh: document.getElementById('dashboard-refresh')?.value || '0.5',
        enable_big_endpoint: document.getElementById('enable-big-endpoint')?.checked ? 'true' : 'false',
        big_endpoint: document.getElementById('big-endpoint')?.value || '',
        big_api_key: document.getElementById('big-api-key')?.value || '',
        enable_middle_endpoint: document.getElementById('enable-middle-endpoint')?.checked ? 'true' : 'false',
        middle_endpoint: document.getElementById('middle-endpoint')?.value || '',
        middle_api_key: document.getElementById('middle-api-key')?.value || '',
        enable_small_endpoint: document.getElementById('enable-small-endpoint')?.checked ? 'true' : 'false',
        small_endpoint: document.getElementById('small-endpoint')?.value || '',
        small_api_key: document.getElementById('small-api-key')?.value || '',
        model_cascade: document.getElementById('model-cascade')?.checked ? 'true' : 'false',
        big_cascade: document.getElementById('big-cascade')?.value || '',
        middle_cascade: document.getElementById('middle-cascade')?.value || '',
        small_cascade: document.getElementById('small-cascade')?.value || '',
        model_cascade_daily_limit: document.getElementById('model-cascade-daily-limit')?.value || '1000'
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
            showToast(`Failed: ${error.detail}`, 'error');
        }
    } catch (error) {
        showToast('Failed to save configuration', 'error');
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
            showToast(`Failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Connection test failed', 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
// MODELS
// ═══════════════════════════════════════════════════════════════

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const payload = await response.json();
        const models = payload.models || payload || [];
        
        const listDiv = document.getElementById('models-list');
        if (!Array.isArray(models) || models.length === 0) {
            listDiv.innerHTML = '<div class="text-muted">No models available</div>';
            return;
        }
        
        listDiv.innerHTML = models.slice(0, 50).map(model => `
            <div class="model-item" data-provider="${model.provider || ''}" onclick="selectModel('${escapeHtml(model.id)}')">
                <div class="model-card-header">
                    <div class="model-name">${escapeHtml(model.id)}</div>
                    ${model.pricing && (model.pricing.is_free === true || model.pricing.prompt === '0') ? '<span class="model-badge free">FREE</span>' : ''}
                </div>
                ${model.context_length ? `<div class="model-context">${(model.context_length / 1000).toFixed(0)}k context</div>` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function filterModels() {
    const searchTerm = document.getElementById('model-search').value.toLowerCase();
    const providerFilter = document.getElementById('model-provider-filter').value.toLowerCase();
    
    document.querySelectorAll('.model-item').forEach(item => {
        const modelName = item.querySelector('.model-name').textContent.toLowerCase();
        const matchesSearch = modelName.includes(searchTerm);
        const matchesProvider = !providerFilter || modelName.includes(providerFilter);
        item.style.display = (matchesSearch && matchesProvider) ? 'block' : 'none';
    });
}

function selectModel(modelId) {
    navigator.clipboard.writeText(modelId);
    showToast(`Copied: ${modelId}`, 'success');
}

async function loadFreeRecommended() {
    try {
        const response = await fetch('/api/models/free-recommended?limit=15');
        const payload = await response.json();
        const models = payload.models || [];
        if (!models.length) return;
        
        window._freeModels = models.map(m => m.id);
    } catch (error) {
        console.error('Failed to load free models:', error);
    }
}

async function applyFreeCascadeTemplate() {
    if (!window._freeModels || !window._freeModels.length) {
        showToast('No free models loaded', 'warning');
        return;
    }
    
    const models = window._freeModels;
    if (document.getElementById('model-cascade')) document.getElementById('model-cascade').checked = true;
    if (document.getElementById('big-cascade')) document.getElementById('big-cascade').value = models.slice(0, 6).join(',');
    if (document.getElementById('middle-cascade')) document.getElementById('middle-cascade').value = models.slice(0, 6).join(',');
    if (document.getElementById('small-cascade')) document.getElementById('small-cascade').value = models.slice(0, 6).join(',');
    
    showToast('Applied free cascade template', 'success');
}

// ═══════════════════════════════════════════════════════════════
// MODEL SCOUT
// ═══════════════════════════════════════════════════════════════

async function loadScoutStatus() {
    try {
        const response = await fetch('/api/models/scout-status');
        const status = await response.json();
        
        // Update scout status UI if it exists
        const statusEl = document.getElementById('scout-status');
        if (statusEl) {
            if (status.last_sync) {
                const lastSync = new Date(status.last_sync).toLocaleString();
                statusEl.innerHTML = `
                    <div class="text-xs text-muted">
                        Last sync: ${lastSync}<br>
                        Free models: ${status.free_models_count || 0}<br>
                        Total: ${status.total_models_count || 0}
                    </div>
                `;
            } else {
                statusEl.innerHTML = '<div class="text-xs text-muted">Never synced</div>';
            }
        }
        
        return status;
    } catch (error) {
        console.error('Failed to load scout status:', error);
        return null;
    }
}

async function runScoutSync(force = false) {
    showToast('Running model scout sync...', 'info');
    try {
        const response = await fetch(`/api/models/scout-sync?force=${force}`, { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            showToast(`Synced ${result.models_count} models!`, 'success');
            loadScoutStatus();
            loadModels();
        } else if (result.status === 'skipped') {
            showToast('Sync skipped (recently synced)', 'info');
        } else {
            showToast(`Sync failed: ${result.error}`, 'error');
        }
        
        return result;
    } catch (error) {
        showToast('Model scout sync failed', 'error');
        console.error('Scout sync error:', error);
        return null;
    }
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
            listDiv.innerHTML = '<div class="text-muted">No profiles saved yet</div>';
            return;
        }
        
        listDiv.innerHTML = profiles.map(profile => `
            <div class="profile-card">
                <div class="profile-header">
                    <div class="profile-name">${escapeHtml(profile.name)}</div>
                    <div class="profile-actions">
                        <button class="btn btn-secondary btn-sm" onclick="loadProfile('${escapeHtml(profile.name)}')">Load</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteProfile('${escapeHtml(profile.name)}')">×</button>
                    </div>
                </div>
                <div class="profile-models">
                    <div class="profile-model-item">
                        <span class="profile-model-tier big">BIG</span>
                        <span class="profile-model-name">${escapeHtml(profile.config?.big_model || '—')}</span>
                    </div>
                    <div class="profile-model-item">
                        <span class="profile-model-tier middle">MID</span>
                        <span class="profile-model-name">${escapeHtml(profile.config?.middle_model || '—')}</span>
                    </div>
                    <div class="profile-model-item">
                        <span class="profile-model-tier small">SML</span>
                        <span class="profile-model-name">${escapeHtml(profile.config?.small_model || '—')}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load profiles:', error);
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
        small_model: document.getElementById('small-model').value
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
        
        showToast(`Profile "${name}" loaded`, 'success');
    } catch (error) {
        showToast('Failed to load profile', 'error');
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
    }
}

function exportConfig() {
    const fields = [
        ['PROVIDER_API_KEY', 'provider-api-key'],
        ['PROVIDER_BASE_URL', 'provider-base-url'],
        ['BIG_MODEL', 'big-model'],
        ['MIDDLE_MODEL', 'middle-model'],
        ['SMALL_MODEL', 'small-model']
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
// MONITOR & STATS
// ═══════════════════════════════════════════════════════════════

async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Dashboard page
        const dashRequests = document.getElementById('dash-requests');
        if (dashRequests) dashRequests.textContent = stats.requests_today || '0';
        
        const dashLatency = document.getElementById('dash-latency');
        if (dashLatency) dashLatency.textContent = stats.avg_latency || '—';
        
        const dashCost = document.getElementById('dash-cost');
        if (dashCost) dashCost.textContent = stats.est_cost ? `$${stats.est_cost.toFixed(2)}` : '$0.00';
        
        const dashSuccess = document.getElementById('dash-success');
        if (dashSuccess) dashSuccess.textContent = '100%';
        
        // Monitor page
        const monRequests = document.getElementById('mon-requests');
        if (monRequests) monRequests.textContent = stats.requests_today || '0';
        
        const monTokens = document.getElementById('mon-tokens');
        if (monTokens) monTokens.textContent = stats.total_tokens ? stats.total_tokens.toLocaleString() : '0';
        
        const monCost = document.getElementById('mon-cost');
        if (monCost) monCost.textContent = stats.est_cost ? `$${stats.est_cost.toFixed(2)}` : '$0.00';
        
        const monLatency = document.getElementById('mon-latency');
        if (monLatency) monLatency.textContent = stats.avg_latency ? `${stats.avg_latency}ms` : '—';
        
        const cascade = stats.cascade || {};
        const switches = cascade.switches ?? 0;
        const successRate = cascade.success_rate ?? 0;
        
        const monSwitches = document.getElementById('mon-cascade-switches');
        if (monSwitches) monSwitches.textContent = String(switches);
        
        const monSuccess = document.getElementById('mon-cascade-success');
        if (monSuccess) monSuccess.textContent = `${successRate}%`;
        
        const monSummary = document.getElementById('mon-cascade-summary');
        if (monSummary) {
            monSummary.textContent = cascade.total_events ? 
                `Cascade: ${cascade.total_events} events, ${switches} switches` : 
                'No cascade events yet';
        }
        
        // Recent requests
        if (stats.recent_requests) {
            const requestsDiv = document.getElementById('mon-recent-requests');
            if (requestsDiv) {
                requestsDiv.innerHTML = stats.recent_requests.map(req => `
                    <div class="activity-item">
                        <div class="activity-icon ${req.status === 'success' ? 'success' : 'error'}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                ${req.status === 'success' ? '<polyline points="20 6 9 17 4 12"/>' : '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'}
                            </svg>
                        </div>
                        <div class="activity-content">
                            <div class="activity-title">${escapeHtml(req.model || 'Unknown')}</div>
                            <div class="activity-meta">${req.tokens || 0} tokens · ${req.duration || 0}ms</div>
                        </div>
                    </div>
                `).join('');
            }
        }
        
        // Update activity feed
        updateActivityFeed(stats.recent_requests || []);
        
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function updateActivityFeed(requests) {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;
    
    if (!requests || requests.length === 0) {
        feed.innerHTML = `
            <div class="activity-item">
                <div class="activity-icon pending">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                </div>
                <div class="activity-content">
                    <div class="activity-title">No recent activity</div>
                    <div class="activity-meta">Waiting for requests...</div>
                </div>
            </div>
        `;
        return;
    }
    
    feed.innerHTML = requests.slice(0, 5).map(req => `
        <div class="activity-item">
            <div class="activity-icon ${req.status === 'success' ? 'success' : 'error'}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    ${req.status === 'success' ? '<polyline points="20 6 9 17 4 12"/>' : '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'}
                </svg>
            </div>
            <div class="activity-content">
                <div class="activity-title">${escapeHtml(req.model || 'Unknown')}</div>
                <div class="activity-meta">${req.tokens || 0} tokens · ${req.duration || 0}ms</div>
            </div>
        </div>
    `).join('');
}

function refreshActivity() {
    refreshStats();
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
            if (wsReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                wsReconnectAttempts++;
                setTimeout(connectWebSocket, Math.min(1000 * Math.pow(2, wsReconnectAttempts), 30000));
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
    if (!logsDiv) return;
    
    const colors = {
        info: 'var(--info)',
        warning: 'var(--warning)',
        error: 'var(--error)',
        success: 'var(--success)'
    };
    
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `
        <span class="log-timestamp">${timestamp}</span>
        <span class="log-level ${level}" style="color: ${colors[level]}">${level.toUpperCase()}</span>
        <span class="log-message">${escapeHtml(message)}</span>
    `;
    entry.dataset.level = level;
    
    logsDiv.appendChild(entry);
    logsDiv.scrollTop = logsDiv.scrollHeight;
    
    while (logsDiv.children.length > 100) {
        logsDiv.removeChild(logsDiv.firstChild);
    }
}

function clearLogs() {
    const logsDiv = document.getElementById('live-logs');
    if (logsDiv) {
        logsDiv.innerHTML = '<div class="log-entry"><span class="log-timestamp">—</span><span class="log-level info">INFO</span><span class="log-message">[Logs cleared]</span></div>';
    }
}

function filterLogs() {
    const filterText = document.getElementById('log-filter')?.value.toLowerCase() || '';
    const levelFilter = document.getElementById('log-level-filter')?.value.toLowerCase() || '';
    
    document.querySelectorAll('#live-logs > .log-entry').forEach(entry => {
        const text = entry.textContent.toLowerCase();
        const matchesText = !filterText || text.includes(filterText);
        const matchesLevel = !levelFilter || entry.dataset.level === levelFilter;
        entry.style.display = (matchesText && matchesLevel) ? 'flex' : 'none';
    });
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

window.addEventListener('DOMContentLoaded', () => {
    checkProxyStatus();
    loadConfig();
    refreshStats();
    loadScoutStatus();
    
    // Refresh status every 30 seconds
    setInterval(checkProxyStatus, 30000);
    
    // Refresh stats every 10 seconds
    setInterval(refreshStats, 10000);
});
