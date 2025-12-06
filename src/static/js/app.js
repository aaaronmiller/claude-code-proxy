// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');

    // Load data for the tab
    if (tabName === 'profiles') {
        loadProfiles();
    } else if (tabName === 'models') {
        loadModels();
    } else if (tabName === 'monitor') {
        refreshStats();
    }
}

// Toast notifications
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Check proxy status
async function checkProxyStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        const indicator = document.getElementById('proxy-status');
        const statusText = document.getElementById('proxy-status-text');

        if (data.status === 'healthy') {
            indicator.classList.add('online');
            indicator.classList.remove('offline');
            statusText.textContent = 'Proxy Online';
        } else {
            indicator.classList.add('offline');
            indicator.classList.remove('online');
            statusText.textContent = 'Proxy Offline';
        }
    } catch (error) {
        const indicator = document.getElementById('proxy-status');
        const statusText = document.getElementById('proxy-status-text');
        indicator.classList.add('offline');
        indicator.classList.remove('online');
        statusText.textContent = 'Cannot Connect';
    }
}

// Load current configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        // Populate form fields
        document.getElementById('openai-api-key').value = config.openai_api_key || '';
        document.getElementById('anthropic-api-key').value = config.anthropic_api_key || '';
        document.getElementById('openai-base-url').value = config.openai_base_url || '';
        document.getElementById('big-model').value = config.big_model || '';
        document.getElementById('middle-model').value = config.middle_model || '';
        document.getElementById('small-model').value = config.small_model || '';
        document.getElementById('reasoning-effort').value = config.reasoning_effort || '';
        document.getElementById('reasoning-max-tokens').value = config.reasoning_max_tokens || '';
        document.getElementById('track-usage').checked = config.track_usage === 'true';
        document.getElementById('compact-logger').checked = config.use_compact_logger === 'true';

        // Update mode indicator
        const modeText = config.passthrough_mode ? 'Passthrough' : 'Proxy';
        document.getElementById('current-mode').textContent = modeText;
        document.getElementById('current-mode').style.color = config.passthrough_mode ? '#f59e0b' : '#22c55e';
    } catch (error) {
        showToast('Failed to load configuration', 'error');
        console.error(error);
    }
}

// Save configuration
async function saveConfig() {
    const config = {
        openai_api_key: document.getElementById('openai-api-key').value,
        anthropic_api_key: document.getElementById('anthropic-api-key').value,
        openai_base_url: document.getElementById('openai-base-url').value,
        big_model: document.getElementById('big-model').value,
        middle_model: document.getElementById('middle-model').value,
        small_model: document.getElementById('small-model').value,
        reasoning_effort: document.getElementById('reasoning-effort').value,
        reasoning_max_tokens: document.getElementById('reasoning-max-tokens').value,
        track_usage: document.getElementById('track-usage').checked ? 'true' : 'false',
        use_compact_logger: document.getElementById('compact-logger').checked ? 'true' : 'false'
    };

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            showToast('Configuration saved and applied!', 'success');
            loadConfig(); // Reload to show updated state
        } else {
            const error = await response.json();
            showToast(`Failed to save: ${error.detail}`, 'error');
        }
    } catch (error) {
        showToast('Failed to save configuration', 'error');
        console.error(error);
    }
}

// Reload configuration
async function reloadConfig() {
    try {
        const response = await fetch('/api/config/reload', {
            method: 'POST'
        });

        if (response.ok) {
            showToast('Configuration reloaded from environment', 'success');
            loadConfig();
        } else {
            showToast('Failed to reload configuration', 'error');
        }
    } catch (error) {
        showToast('Failed to reload configuration', 'error');
        console.error(error);
    }
}

// Export configuration
function exportConfig() {
    const config = {
        OPENAI_API_KEY: document.getElementById('openai-api-key').value,
        ANTHROPIC_API_KEY: document.getElementById('anthropic-api-key').value,
        OPENAI_BASE_URL: document.getElementById('openai-base-url').value,
        BIG_MODEL: document.getElementById('big-model').value,
        MIDDLE_MODEL: document.getElementById('middle-model').value,
        SMALL_MODEL: document.getElementById('small-model').value,
        REASONING_EFFORT: document.getElementById('reasoning-effort').value,
        REASONING_MAX_TOKENS: document.getElementById('reasoning-max-tokens').value,
        TRACK_USAGE: document.getElementById('track-usage').checked ? 'true' : 'false',
        USE_COMPACT_LOGGER: document.getElementById('compact-logger').checked ? 'true' : 'false'
    };

    const envContent = Object.entries(config)
        .filter(([key, value]) => value)
        .map(([key, value]) => `${key}="${value}"`)
        .join('\n');

    const blob = new Blob([envContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'config.env';
    a.click();
    URL.revokeObjectURL(url);

    showToast('Configuration exported to config.env', 'success');
}

// Load profiles
async function loadProfiles() {
    try {
        const response = await fetch('/api/profiles');
        const profiles = await response.json();

        const listDiv = document.getElementById('profiles-list');
        if (profiles.length === 0) {
            listDiv.innerHTML = '<p class="loading">No profiles saved yet</p>';
            return;
        }

        listDiv.innerHTML = profiles.map(profile => `
            <div class="profile-card">
                <div class="profile-info">
                    <h3>${profile.name}</h3>
                    <p>Last modified: ${new Date(profile.modified).toLocaleString()}</p>
                    <p>${profile.big_model} / ${profile.middle_model} / ${profile.small_model}</p>
                </div>
                <div class="profile-actions-buttons">
                    <button class="btn btn-primary btn-small" onclick="loadProfile('${profile.name}')">Load</button>
                    <button class="btn btn-danger btn-small" onclick="deleteProfile('${profile.name}')">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        showToast('Failed to load profiles', 'error');
        console.error(error);
    }
}

// Save profile
async function saveProfile() {
    const profileName = document.getElementById('new-profile-name').value.trim();
    if (!profileName) {
        showToast('Please enter a profile name', 'warning');
        return;
    }

    const config = {
        openai_api_key: document.getElementById('openai-api-key').value,
        anthropic_api_key: document.getElementById('anthropic-api-key').value,
        openai_base_url: document.getElementById('openai-base-url').value,
        big_model: document.getElementById('big-model').value,
        middle_model: document.getElementById('middle-model').value,
        small_model: document.getElementById('small-model').value,
        reasoning_effort: document.getElementById('reasoning-effort').value,
        reasoning_max_tokens: document.getElementById('reasoning-max-tokens').value,
        track_usage: document.getElementById('track-usage').checked,
        use_compact_logger: document.getElementById('compact-logger').checked
    };

    try {
        const response = await fetch('/api/profiles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: profileName, config })
        });

        if (response.ok) {
            showToast(`Profile "${profileName}" saved!`, 'success');
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

// Load profile
async function loadProfile(name) {
    try {
        const response = await fetch(`/api/profiles/${encodeURIComponent(name)}`);
        const profile = await response.json();

        // Populate form
        document.getElementById('openai-api-key').value = profile.config.openai_api_key || '';
        document.getElementById('anthropic-api-key').value = profile.config.anthropic_api_key || '';
        document.getElementById('openai-base-url').value = profile.config.openai_base_url || '';
        document.getElementById('big-model').value = profile.config.big_model || '';
        document.getElementById('middle-model').value = profile.config.middle_model || '';
        document.getElementById('small-model').value = profile.config.small_model || '';
        document.getElementById('reasoning-effort').value = profile.config.reasoning_effort || '';
        document.getElementById('reasoning-max-tokens').value = profile.config.reasoning_max_tokens || '';
        document.getElementById('track-usage').checked = profile.config.track_usage || false;
        document.getElementById('compact-logger').checked = profile.config.use_compact_logger || false;

        // Switch to config tab
        document.getElementById('config-tab').classList.add('active');
        document.getElementById('profiles-tab').classList.remove('active');
        document.querySelector('.tab-button:first-child').classList.add('active');
        document.querySelectorAll('.tab-button')[1].classList.remove('active');

        showToast(`Profile "${name}" loaded`, 'success');
    } catch (error) {
        showToast('Failed to load profile', 'error');
        console.error(error);
    }
}

// Delete profile
async function deleteProfile(name) {
    if (!confirm(`Delete profile "${name}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/profiles/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });

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

// Load models
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();

        const listDiv = document.getElementById('models-list');
        listDiv.innerHTML = models.map(model => `
            <div class="model-card" data-provider="${model.provider}" onclick="selectModel('${model.id}')">
                <div class="model-name">${model.id}</div>
                <div class="model-meta">
                    <span>Context: ${(model.context_length / 1000).toFixed(0)}k</span>
                    ${model.pricing ? `<span>$${model.pricing.prompt}/${model.pricing.completion}</span>` : ''}
                    ${model.pricing && model.pricing.prompt === '0' ? '<span class="model-badge badge-free">FREE</span>' : ''}
                    ${model.supports_reasoning ? '<span class="model-badge badge-reasoning">Reasoning</span>' : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        showToast('Failed to load models', 'error');
        console.error(error);
    }
}

// Filter models
function filterModels() {
    const searchTerm = document.getElementById('model-search').value.toLowerCase();
    const providerFilter = document.getElementById('model-provider-filter').value.toLowerCase();

    document.querySelectorAll('.model-card').forEach(card => {
        const modelName = card.querySelector('.model-name').textContent.toLowerCase();
        const provider = card.dataset.provider.toLowerCase();

        const matchesSearch = modelName.includes(searchTerm);
        const matchesProvider = !providerFilter || provider.includes(providerFilter);

        card.style.display = (matchesSearch && matchesProvider) ? 'block' : 'none';
    });
}

// Select model
function selectModel(modelId) {
    // Copy to clipboard
    navigator.clipboard.writeText(modelId);
    showToast(`Model ID copied: ${modelId}`, 'success');
}

// Refresh stats
async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('requests-today').textContent = stats.requests_today || '0';
        document.getElementById('total-tokens').textContent = stats.total_tokens ? stats.total_tokens.toLocaleString() : '0';
        document.getElementById('est-cost').textContent = stats.est_cost ? `$${stats.est_cost.toFixed(2)}` : '$0.00';
        document.getElementById('avg-latency').textContent = stats.avg_latency ? `${stats.avg_latency}ms` : '-';

        // Load recent requests
        if (stats.recent_requests) {
            const requestsDiv = document.getElementById('recent-requests');
            requestsDiv.innerHTML = stats.recent_requests.map(req => `
                <div class="request-card">
                    <div class="request-header">
                        <span class="request-model">${req.model}</span>
                        <span class="request-status status-${req.status}">${req.status}</span>
                    </div>
                    <div class="request-meta">
                        <span>Tokens: ${req.tokens}</span>
                        <span>Duration: ${req.duration}ms</span>
                        <span>Cost: $${req.cost}</span>
                        <span>${new Date(req.timestamp).toLocaleTimeString()}</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        showToast('Failed to load stats', 'error');
        console.error(error);
    }
}

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    checkProxyStatus();
    loadConfig();

    // Refresh status every 30 seconds
    setInterval(checkProxyStatus, 30000);
});
