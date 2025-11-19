# Web UI for Claude Code Proxy

## Features

### 🎯 Configuration Management
- **Visual Editor**: Edit all proxy settings through a modern web interface
- **Hot Reload**: Apply configuration changes without restarting the proxy
- **Validation**: Real-time validation of configuration values
- **Export**: Download configuration as `.env` file

### 📁 Profile Management
- **Save Profiles**: Save different configuration sets with custom names
- **Quick Load**: Switch between profiles with one click
- **Profile Library**: Manage multiple configurations (dev, prod, testing, etc.)
- **Automatic Timestamps**: Track when each profile was last modified

### 🤖 Model Browser
- **352+ Models**: Browse all available models from OpenRouter
- **Smart Search**: Filter by name, provider, or capabilities
- **Model Details**: View context limits, pricing, and features
- **Quick Copy**: Click to copy model IDs to clipboard

### 📊 Real-Time Monitoring
- **Request Statistics**: View requests, tokens, cost, and latency
- **Recent Activity**: See the last 10 requests with full details
- **Live Status**: Proxy health and mode indicator
- **Usage Analytics**: When TRACK_USAGE is enabled

## Access

The Web UI is automatically available at:
- **http://localhost:8082/** - Main interface
- **http://localhost:8082/config** - Direct to config tab

## Usage

### 1. Basic Configuration

1. Open http://localhost:8082 in your browser
2. Click the "⚙️ Configuration" tab (default)
3. Update settings:
   - API keys (OpenAI, Anthropic)
   - Model mappings (BIG, MIDDLE, SMALL)
   - Reasoning configuration
   - Monitoring options
4. Click "💾 Save & Apply" to apply changes (no restart!)

### 2. Profile Management

1. Configure your settings in the Configuration tab
2. Switch to the "📁 Profiles" tab
3. Enter a profile name (e.g., "Production", "Testing", "GPT-4")
4. Click "💾 Save Current as Profile"
5. Load any profile later with one click

**Use Cases:**
- **Dev/Prod**: Separate configurations for development and production
- **Provider Testing**: Switch between OpenAI, OpenRouter, local models
- **Model Experiments**: Different model configurations for testing
- **Team Sharing**: Export profiles as JSON and share with team

### 3. Model Selection

1. Go to the "🤖 Models" tab
2. Use the search box to find models by name
3. Filter by provider (OpenAI, Anthropic, Google, Meta, etc.)
4. Click any model to copy its ID to clipboard
5. Paste into Configuration tab or .env file

### 4. Monitoring

1. Navigate to the "📊 Monitor" tab
2. View real-time statistics:
   - Requests today
   - Total tokens used
   - Estimated cost (24h)
   - Average latency
3. See recent requests with details
4. Click "🔄 Refresh Stats" to update

## API Endpoints

The Web UI uses these REST API endpoints:

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration (hot reload)
- `POST /api/config/reload` - Reload from environment variables

### Profiles
- `GET /api/profiles` - List all profiles
- `POST /api/profiles` - Save a profile
- `GET /api/profiles/{name}` - Load a specific profile
- `DELETE /api/profiles/{name}` - Delete a profile

### Models & Stats
- `GET /api/models` - List available models
- `GET /api/stats` - Get proxy statistics

## Hot Reload

Configuration changes are applied **immediately without restart**:
- ✅ API keys
- ✅ Model mappings
- ✅ Reasoning settings
- ✅ Monitoring options
- ✅ Base URLs

This allows you to:
- Test different providers instantly
- Switch models on the fly
- Enable/disable features
- Debug configuration issues

## Profile Storage

Profiles are stored in `configs/profiles/` as JSON files:

```json
{
  "name": "Production",
  "modified": "2025-01-19T10:30:00Z",
  "config": {
    "openai_api_key": "sk-...",
    "big_model": "gpt-4o",
    "middle_model": "gpt-4o",
    "small_model": "gpt-4o-mini",
    "track_usage": true
  }
}
```

You can:
- Share profiles by copying JSON files
- Version control profiles in Git
- Backup profiles for disaster recovery
- Programmatically generate profiles

## Security

- **API Keys**: Masked in the UI (shown as `***`)
- **Local Storage**: All data stored on your machine
- **No Cloud Sync**: Profiles never leave your server
- **HTTPS Ready**: Works with reverse proxies (nginx, Caddy)

## Troubleshooting

### Web UI Not Loading
1. Check proxy is running: `curl http://localhost:8082/health`
2. Verify static files exist: `ls static/index.html`
3. Check browser console for errors (F12)

### Configuration Not Saving
1. Check write permissions on `configs/` directory
2. Look for errors in proxy logs
3. Verify JSON syntax if editing profiles manually

### Stats Not Showing
1. Enable usage tracking: `TRACK_USAGE=true` in .env
2. Restart proxy to initialize database
3. Make some API requests to generate data

## Browser Support

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Development

The Web UI is built with:
- **Vanilla JavaScript** - No frameworks, fast loading
- **CSS3** - Modern styling with dark theme
- **FastAPI** - Backend REST API
- **SQLite** - Statistics storage (via usage_tracker)

To customize:
1. Edit files in `static/`
2. Refresh browser (changes apply immediately)
3. No build step required
