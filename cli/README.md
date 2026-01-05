# Claude Proxy CLI & SDK

Command-line interface and Python SDK for the Claude Proxy analytics platform.

## Installation

### From PyPI (when published)
```bash
pip install claude-proxy-cli
```

### From Source
```bash
cd cli
pip install .
```

## Quick Start

### 1. Configure API Connection

```bash
# Set base URL
claude-proxy config set base_url http://localhost:8082

# Set API key
claude-proxy config set api_key cp_your_api_key_here

# Or login with username/password
claude-proxy auth login --username admin --password admin123
```

### 2. Query Analytics

```bash
# Basic metrics
claude-proxy analytics --start 2026-01-01 --end 2026-01-05

# Specific metric
claude-proxy analytics --start 2026-01-01 --end 2026-01-05 --metric cost

# Custom query with export
claude-proxy analytics --custom --metrics tokens,cost,requests --export report.csv
```

### 3. Predictive Analytics

```bash
# Get 7-day forecast
claude-proxy predictive forecast --days 7

# Get smart thresholds
claude-proxy predictive thresholds --metric cost

# Detect anomalies
claude-proxy predictive detect --data '{"cost": 150, "tokens": 5000}'
```

### 4. Alert Management

```bash
# List alerts
claude-proxy alerts list

# Create alert
claude-proxy alerts create --name "High Cost Alert" --condition "cost>100" --priority 2

# View history
claude-proxy alerts history --limit 20
```

### 5. Reports

```bash
# List templates
claude-proxy reports templates

# Generate report
claude-proxy reports generate --template tpl_weekly_summary --start 2026-01-01 --end 2026-01-07 --format pdf --output report.pdf
```

### 6. Integrations

```bash
# List integrations
claude-proxy integrations list

# Test integration
claude-proxy integrations test --name slack
```

### 7. GraphQL Queries

```bash
# Execute GraphQL query
claude-proxy graphql --query '{
  metrics(startDate: "2026-01-01", endDate: "2026-01-05") {
    timestamp
    tokens
    cost
  }
}'
```

## Python SDK

### Installation

```bash
pip install requests  # Only dependency
```

### Basic Usage

```python
from claude_proxy import ClaudeProxyClient

# Initialize client
client = ClaudeProxyClient(
    base_url="http://localhost:8082",
    api_key="cp_your_api_key_here"
)

# Query analytics
analytics = client.get_analytics(
    start_date="2026-01-01",
    end_date="2026-01-05",
    metric="tokens",
    group_by="day"
)
print(analytics)

# Get predictions
forecast = client.get_predictions(days=7)
print(f"Predicted cost: ${forecast['summary']['total_cost']:.2f}")

# Create alert
alert = client.create_alert(
    name="Daily Cost Limit",
    condition={"metric": "cost", "operator": ">", "threshold": 500},
    priority=1
)
print(alert)
```

### Advanced Usage

```python
# Custom queries
result = client.get_custom_query(
    metrics="tokens,cost,requests",
    start_date="2026-01-01",
    end_date="2026-01-05",
    group_by="day"
)

# Anomaly detection
is_anomaly = client.detect_anomaly({
    "estimated_cost": 150,
    "total_tokens": 10000
})

# Report generation
report = client.generate_report(
    template_id="tpl_weekly_summary",
    start_date="2026-01-01",
    end_date="2026-01-07",
    format_type="pdf"
)

# GraphQL queries
data = client.graphql_query("""
    query {
        health
        providerStats(startDate: "2026-01-01", endDate: "2026-01-05") {
            provider
            totalCost
            totalTokens
        }
    }
""")
```

## Configuration

### Configuration File

Location: `~/.claude_proxy/config.json`

```json
{
  "base_url": "http://localhost:8082",
  "api_key": "cp_your_key_here"
}
```

### Environment Variables

```bash
export CLAUDE_PROXY_URL=http://localhost:8082
export CLAUDE_PROXY_API_KEY=cp_your_key_here
```

## API Methods

### Analytics
- `get_analytics(start_date, end_date, metric, group_by)`
- `get_custom_query(metrics, start_date, end_date, **kwargs)`
- `get_aggregate_stats(start_date, end_date)`

### Predictive
- `get_predictions(days)`
- `get_smart_thresholds(metric)`
- `detect_anomaly(request_data)`

### Alerts
- `list_alerts()`
- `create_alert(name, condition, priority)`
- `get_alert_history(limit)`

### Reports
- `list_templates()`
- `generate_report(template_id, start_date, end_date, format_type)`
- `get_scheduled_reports()`

### Integrations
- `list_integrations()`
- `test_integration(name)`

### Auth
- `login(username, password)`
- `create_api_key(name, permissions)`
- `list_api_keys()`

### GraphQL
- `graphql_query(query, variables)`

## CI/CD Integration

### GitHub Actions

```yaml
name: Cost Monitoring
on: [push]

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install CLI
        run: pip install claude-proxy-cli

      - name: Get Usage Stats
        env:
          CLAUDE_PROXY_API_KEY: ${{ secrets.CLAUDE_PROXY_API_KEY }}
        run: |
          claude-proxy analytics \
            --start $(date -d '7 days ago' +%Y-%m-%d) \
            --end $(date +%Y-%m-%d) \
            --metric cost \
            --export cost_report.csv

      - name: Check Forecast
        run: |
          claude-proxy predictive forecast --days 7
```

### Docker

```dockerfile
FROM python:3.11-slim
RUN pip install claude-proxy-cli
COPY . /app
WORKDIR /app
```

## Examples

### Cost Monitoring Script

```python
#!/usr/bin/env python3
from claude_proxy import ClaudeProxyClient
from datetime import datetime, timedelta

client = ClaudeProxyClient(
    base_url="http://localhost:8082",
    api_key="cp_your_key"
)

# Get last 7 days
end = datetime.now()
start = end - timedelta(days=7)

# Get analytics
analytics = client.get_analytics(
    start_date=start.strftime('%Y-%m-%d'),
    end_date=end.strftime('%Y-%m-%d'),
    metric="cost"
)

# Get forecast
forecast = client.get_predictions(days=7)

# Alert if high
if forecast["summary"]["total_cost"] > 100:
    print("⚠️ High cost predicted!")
    client.create_alert(
        name="CLI Auto Alert",
        condition={"metric": "cost", "operator": ">", "threshold": 100},
        priority=2
    )
```

### Automated Reporting

```python
from claude_proxy import ClaudeProxyClient
import schedule
import time

def generate_daily_report():
    client = ClaudeProxyClient(base_url="http://localhost:8082")

    # Generate report
    report = client.generate_report(
        template_id="tpl_daily_summary",
        start_date="2026-01-01",
        end_date="2026-01-01",
        format_type="pdf"
    )

    # Send to Slack
    client.graphql_query("""
        mutation {
            sendNotification(
                channel: "slack"
                message: "Daily report generated"
            )
        }
    """)

# Schedule daily at 9 AM
schedule.every().day.at("09:00").do(generate_daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Error Handling

```python
from claude_proxy import ClaudeProxyClient
import requests

client = ClaudeProxyClient(base_url="http://localhost:8082")

try:
    analytics = client.get_analytics("2026-01-01", "2026-01-05")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("❌ Authentication failed")
    elif e.response.status_code == 429:
        print("⚠️ Rate limit exceeded")
    else:
        print(f"❌ HTTP Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Development

### Install for Development

```bash
cd cli
pip install -e .
```

### Running Tests

```bash
pip install pytest
pytest tests/
```

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://claude-proxy.readthedocs.io/
- GitHub Issues: https://github.com/claude-proxy/claude-proxy/issues
- Email: support@claude-proxy.com
