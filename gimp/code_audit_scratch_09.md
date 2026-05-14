# File Audit: /home/cheta/code/claude-code-proxy/src/services/predictive_alerting.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/predictive_alerting.py`

**Module Overview**: 
```text
Predictive Alerting Service - Phase 4

AI-powered anomaly detection and predictive alerting using statistical analysis
and pattern recognition to forecast issues before they occur.

Features:
- Trend analysis and forecasting
- Anomaly detection using statistical methods
- Cost prediction
- Smart threshold recommendations
- Seasonal pattern detection

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `predictive_alerting` = `PredictiveAlertingService()`
- `anomaly_detector` = `AnomalyDetector()`

## Dependencies & Imports
sqlite3, numpy, datetime.datetime, datetime.timedelta, typing.Dict, typing.List, typing.Optional, typing.Tuple, dataclasses.dataclass, json, logging, src.core.logging.logger

## Feature Class: `PredictionResult`
**Description:**
```text
Result from predictive analysis
```

---

## Feature Class: `Forecast`
**Description:**
```text
Multi-step forecast
```

---

## Feature Class: `PredictiveAlertingService`
**Description:**
```text
AI-powered predictive alerting engine
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Implementation:**
```python
def __init__(self, db_path: str='usage_tracking.db'):
    self.db_path = db_path
    self.logger = logger
```

### Method: `get_historical_data`
**Logic & Purpose:**
```text
Retrieve historical metrics data
```

**Parameters:** `self, days`
**Variables Used:** `cursor, data, end_date, rows, start_date, query, conn`
**Implementation:**
```python
def get_historical_data(self, days: int=30) -> Dict[str, List[float]]:
    """Retrieve historical metrics data"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        query = '\n                SELECT\n                    date(timestamp) as date,\n                    SUM(total_tokens) as tokens,\n                    SUM(estimated_cost) as cost,\n                    COUNT(*) as requests,\n                    AVG(duration_ms) as avg_latency\n                FROM api_requests\n                WHERE timestamp >= ? AND timestamp <= ?\n                GROUP BY date(timestamp)\n                ORDER BY date\n            '
        cursor = conn.execute(query, [start_date.isoformat(), end_date.isoformat()])
        rows = cursor.fetchall()
        conn.close()
        data = {'tokens': [row['tokens'] or 0 for row in rows], 'cost': [row['cost'] or 0 for row in rows], 'requests': [row['requests'] or 0 for row in rows], 'latency': [row['avg_latency'] or 0 for row in rows], 'dates': [row['date'] for row in rows]}
        return data
    except Exception as e:
        self.logger.error(f'Failed to get historical data: {e}')
        return {}
```

### Method: `calculate_trend`
**Logic & Purpose:**
```text
Calculate trend direction using linear regression
```

**Parameters:** `self, data`
**Variables Used:** `y, slope, x`
**Implementation:**
```python
def calculate_trend(self, data: List[float]) -> str:
    """Calculate trend direction using linear regression"""
    if len(data) < 3:
        return 'insufficient_data'
    x = np.arange(len(data))
    y = np.array(data)
    slope = np.polyfit(x, y, 1)[0]
    if abs(slope) < np.mean(y) * 0.05:
        return 'stable'
    elif slope > 0:
        return 'increasing'
    else:
        return 'decreasing'
```

### Method: `detect_anomalies`
**Logic & Purpose:**
```text
Detect anomalies using rolling mean and std deviation
```

**Parameters:** `self, data, window`
**Variables Used:** `std, score, mean, anomalies, window_data, z_score`
**Implementation:**
```python
def detect_anomalies(self, data: List[float], window: int=7) -> List[float]:
    """Detect anomalies using rolling mean and std deviation"""
    if len(data) < window:
        return [0.0] * len(data)
    anomalies = []
    for i in range(len(data)):
        if i < window:
            anomalies.append(0.0)
            continue
        window_data = data[i - window:i]
        mean = np.mean(window_data)
        std = np.std(window_data)
        if std == 0:
            z_score = 0
        else:
            z_score = abs(data[i] - mean) / std
        score = min(z_score / 3, 1.0)
        anomalies.append(score)
    return anomalies
```

### Method: `forecast_simple`
**Logic & Purpose:**
```text
Simple exponential smoothing forecast
```

**Parameters:** `self, data, steps`
**Variables Used:** `alpha, forecast, level`
**Implementation:**
```python
def forecast_simple(self, data: List[float], steps: int=7) -> List[float]:
    """Simple exponential smoothing forecast"""
    if len(data) == 0:
        return [0.0] * steps
    alpha = 0.3
    forecast = []
    level = data[-1]
    for _ in range(steps):
        level = alpha * level + (1 - alpha) * level
        forecast.append(max(0, level))
    return forecast
```

### Method: `predict_metrics`
**Logic & Purpose:**
```text
Main prediction method - predicts future metrics
```

**Parameters:** `self, days_ahead`
**Variables Used:** `upper_bound, recent_anomaly, history, future_date, trend, predictions, forecast_values, tokens_predicted, risk_level, high_severity, historical_values, mean_val, anomalies, std_dev, cost_predicted, confidence, consistency, severity, recommendation, lower_bound`
**Implementation:**
```python
def predict_metrics(self, days_ahead: int=7) -> Forecast:
    """Main prediction method - predicts future metrics"""
    try:
        history = self.get_historical_data(days=30)
        if not history or len(history.get('tokens', [])) < 5:
            return Forecast(metric='all', predictions=[], total_tokens_predicted=0, cost_prediction=0, risk_level='unknown', recommended_action='Insufficient data for prediction')
        predictions = []
        for metric in ['tokens', 'cost', 'requests']:
            historical_values = history[metric]
            if len(historical_values) < 5:
                continue
            trend = self.calculate_trend(historical_values)
            anomalies = self.detect_anomalies(historical_values)
            forecast_values = self.forecast_simple(historical_values, days_ahead)
            std_dev = np.std(historical_values)
            mean_val = np.mean(historical_values)
            consistency = 1.0 - (std_dev / mean_val if mean_val > 0 else 1.0)
            confidence = max(0.5, min(0.95, consistency))
            if anomalies:
                recent_anomaly = np.mean(anomalies[-3:]) if len(anomalies) >= 3 else anomalies[-1]
            else:
                recent_anomaly = 0.0
            lower_bound = [max(0, val * 0.8) for val in forecast_values]
            upper_bound = [val * 1.2 for val in forecast_values]
            severity = 'low'
            if recent_anomaly > 0.5:
                severity = 'high'
            elif trend == 'increasing' and recent_anomaly > 0.3:
                severity = 'medium'
            for i, (pred_val, lower, upper) in enumerate(zip(forecast_values, lower_bound, upper_bound)):
                future_date = datetime.now() + timedelta(days=i + 1)
                predictions.append(PredictionResult(timestamp=future_date.isoformat(), metric=metric, predicted_value=pred_val, confidence=confidence, anomaly_score=recent_anomaly, expected_range=(lower, upper), trend=trend, severity=severity))
        tokens_predicted = sum((p.predicted_value for p in predictions if p.metric == 'tokens'))
        cost_predicted = sum((p.predicted_value for p in predictions if p.metric == 'cost'))
        high_severity = sum((1 for p in predictions if p.severity in ['high', 'critical']))
        risk_level = 'low'
        if high_severity > len(predictions) * 0.3:
            risk_level = 'high'
        elif high_severity > 0:
            risk_level = 'medium'
        recommendation = self._generate_recommendation(tokens_predicted, cost_predicted, risk_level, trend)
        return Forecast(metric='all', predictions=predictions, total_tokens_predicted=tokens_predicted, cost_prediction=cost_predicted, risk_level=risk_level, recommended_action=recommendation)
    except Exception as e:
        self.logger.error(f'Prediction failed: {e}')
        return Forecast(metric='all', predictions=[], total_tokens_predicted=0, cost_prediction=0, risk_level='error', recommended_action=f'Prediction error: {str(e)}')
```

### Method: `_generate_recommendation`
**Logic & Purpose:**
```text
Generate actionable recommendations
```

**Parameters:** `self, tokens, cost, risk, trend`
**Implementation:**
```python
def _generate_recommendation(self, tokens: float, cost: float, risk: str, trend: str) -> str:
    """Generate actionable recommendations"""
    if risk == 'high':
        return 'ALERT: High risk detected. Consider reducing model complexity or implementing rate limits.'
    elif risk == 'medium':
        if trend == 'increasing':
            return 'Monitor closely. Usage trending upward. Set up budget alerts.'
        else:
            return 'Medium risk. Review cost optimization opportunities.'
    elif risk == 'low':
        if trend == 'increasing':
            return 'Usage increasing normally. Monitor for continued growth.'
        else:
            return 'Usage stable. No immediate action required.'
    else:
        return 'Unable to determine risk level. Monitor manually.'
```

### Method: `get_smart_thresholds`
**Logic & Purpose:**
```text
Calculate intelligent thresholds based on historical data
```

**Parameters:** `self, metric`
**Variables Used:** `q75, values, q90, history`
**Implementation:**
```python
def get_smart_thresholds(self, metric: str) -> Dict[str, float]:
    """Calculate intelligent thresholds based on historical data"""
    history = self.get_historical_data(days=30)
    if metric not in history or len(history[metric]) < 5:
        return {'warning': 0, 'critical': 0}
    values = history[metric]
    q75 = np.percentile(values, 75)
    q90 = np.percentile(values, 90)
    return {'warning': float(q75), 'critical': float(q90), 'info': f'Based on 30-day p75/p90 percentiles'}
```

### Method: `detect_seasonal_patterns`
**Logic & Purpose:**
```text
Detect daily/weekly patterns in usage
```

**Parameters:** `self, days`
**Variables Used:** `cursor, peak_avg, cutoff, hourly_data, peak_hour, query2, rows, patterns, pattern_rows, query, conn`
**Implementation:**
```python
def detect_seasonal_patterns(self, days: int=30) -> Dict[str, any]:
    """Detect daily/weekly patterns in usage"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        query = "\n                SELECT\n                    strftime('%H', timestamp) as hour,\n                    AVG(total_tokens) as avg_tokens,\n                    COUNT(*) as request_count\n                FROM api_requests\n                WHERE timestamp >= ?\n                GROUP BY strftime('%H', timestamp)\n                ORDER BY hour\n            "
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = conn.execute(query, [cutoff])
        rows = cursor.fetchall()
        conn.close()
        hourly_data = {int(row['hour']): (row['avg_tokens'] or 0, row['request_count'] or 0) for row in rows}
        peak_hour = max(hourly_data.keys(), key=lambda h: hourly_data[h][0]) if hourly_data else None
        peak_avg = hourly_data[peak_hour][0] if peak_hour else 0
        query2 = "\n                SELECT\n                    CASE WHEN CAST(strftime('%w', timestamp) AS INTEGER) IN (0,6) THEN 'weekend' ELSE 'weekday' END as day_type,\n                    AVG(total_tokens) as avg_tokens,\n                    COUNT(*) as request_count\n                FROM api_requests\n                WHERE timestamp >= ?\n                GROUP BY day_type\n            "
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(query2, [cutoff])
        pattern_rows = cursor.fetchall()
        conn.close()
        patterns = {}
        for row in pattern_rows:
            patterns[row['day_type']] = {'avg_tokens': row['avg_tokens'] or 0, 'requests': row['request_count'] or 0}
        return {'peak_hour': peak_hour, 'peak_avg_tokens': peak_avg, 'patterns': patterns, 'recommendation': self._generate_pattern_recommendation(hourly_data, patterns)}
    except Exception as e:
        self.logger.error(f'Pattern detection failed: {e}')
        return {}
```

### Method: `_generate_pattern_recommendation`
**Logic & Purpose:**
```text
Generate scheduling recommendations based on patterns
```

**Parameters:** `self, hourly_data, patterns`
**Variables Used:** `weekday_avg, peak_hour, weekend_avg`
**Implementation:**
```python
def _generate_pattern_recommendation(self, hourly_data: Dict, patterns: Dict) -> str:
    """Generate scheduling recommendations based on patterns"""
    if not hourly_data or not patterns:
        return 'Insufficient data for pattern analysis'
    peak_hour = max(hourly_data.keys(), key=lambda h: hourly_data[h][0])
    weekday_avg = patterns.get('weekday', {}).get('avg_tokens', 0)
    weekend_avg = patterns.get('weekend', {}).get('avg_tokens', 0)
    if weekday_avg > weekend_avg * 2:
        return f'Peak usage at hour {peak_hour}. Consider batch processing during off-peak hours (weekends).'
    elif peak_hour and (peak_hour >= 9 and peak_hour <= 17):
        return f'Business hours peak detected (hour {peak_hour}). Consider off-hours processing.'
    else:
        return 'Usage is well distributed. No scheduling optimization needed.'
```

---

## Feature Class: `Anomaly`
**Description:**
```text
Represents a detected anomaly
```

---

## Feature Class: `AnomalyDetector`
**Description:**
```text
Real-time anomaly detection for incoming requests
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Implementation:**
```python
def __init__(self, db_path: str='usage_tracking.db'):
    self.db_path = db_path
    self.baseline_cache = {}
```

### Method: `update_baseline`
**Logic & Purpose:**
```text
Update baseline statistics for a metric
```

**Parameters:** `self, metric, window_hours`
**Variables Used:** `cursor, cutoff, stats, query, conn, row`
**Implementation:**
```python
def update_baseline(self, metric: str, window_hours: int=24) -> Dict[str, float]:
    """Update baseline statistics for a metric"""
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(hours=window_hours)).isoformat()
    if metric == 'cost':
        query = 'SELECT AVG(estimated_cost) as mean, STDDEV(estimated_cost) as std FROM api_requests WHERE timestamp >= ?'
    elif metric == 'tokens':
        query = 'SELECT AVG(total_tokens) as mean, STDDEV(total_tokens) as std FROM api_requests WHERE timestamp >= ?'
    elif metric == 'latency':
        query = 'SELECT AVG(duration_ms) as mean, STDDEV(duration_ms) as std FROM api_requests WHERE timestamp >= ?'
    else:
        conn.close()
        return {}
    cursor = conn.execute(query, [cutoff])
    row = cursor.fetchone()
    conn.close()
    if not row or row['mean'] is None:
        return {}
    stats = {'mean': row['mean'], 'std': row['std'] or 0, 'upper_bound': row['mean'] + 3 * (row['std'] or 0), 'lower_bound': max(0, row['mean'] - 3 * (row['std'] or 0))}
    self.baseline_cache[metric] = stats
    return stats
```

### Method: `check_request`
**Logic & Purpose:**
```text
Check a single request for anomalies
```

**Parameters:** `self, request_data`
**Variables Used:** `baseline, deviation, cost`
**Implementation:**
```python
def check_request(self, request_data: Dict) -> Optional[Anomaly]:
    """Check a single request for anomalies"""
    baseline = self.update_baseline('cost')
    if not baseline:
        return None
    cost = request_data.get('estimated_cost', 0)
    if cost > baseline['upper_bound']:
        deviation = (cost - baseline['mean']) / baseline['mean'] * 100
        return Anomaly(timestamp=datetime.now().isoformat(), metric='cost', value=cost, expected=baseline['mean'], deviation=deviation, severity='high' if deviation > 200 else 'medium', description=f"Cost anomaly: ${cost:.4f} vs expected ${baseline['mean']:.4f} (+{deviation:.1f}%)")
    return None
```

---

## Feature Class: `PredictionAPI`
**Description:**
```text
API interface for predictive features
```

### Method: `get_predictions`
**Logic & Purpose:**
```text
Get predictive forecast
```

**Parameters:** `days`
**Variables Used:** `forecast`
**Implementation:**
```python
@staticmethod
async def get_predictions(days: int=7) -> Dict:
    """Get predictive forecast"""
    try:
        forecast = predictive_alerting.predict_metrics(days)
        return {'success': True, 'data': {'predictions': [{'timestamp': p.timestamp, 'metric': p.metric, 'value': round(p.predicted_value, 4), 'confidence': round(p.confidence, 3), 'anomaly_score': round(p.anomaly_score, 3), 'expected_range': [round(r, 4) for r in p.expected_range], 'trend': p.trend, 'severity': p.severity} for p in forecast.predictions], 'summary': {'total_tokens': round(forecast.total_tokens_predicted, 0), 'total_cost': round(forecast.cost_prediction, 4), 'risk_level': forecast.risk_level, 'recommendation': forecast.recommended_action}}}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### Method: `get_smart_thresholds`
**Logic & Purpose:**
```text
Get intelligent thresholds
```

**Parameters:** `metric`
**Variables Used:** `thresholds`
**Implementation:**
```python
@staticmethod
async def get_smart_thresholds(metric: str) -> Dict:
    """Get intelligent thresholds"""
    thresholds = predictive_alerting.get_smart_thresholds(metric)
    return {'metric': metric, 'thresholds': thresholds, 'source': '30-day historical analysis'}
```

### Method: `get_patterns`
**Logic & Purpose:**
```text
Get usage patterns
```

**Parameters:** ``
**Variables Used:** `patterns`
**Implementation:**
```python
@staticmethod
async def get_patterns() -> Dict:
    """Get usage patterns"""
    patterns = predictive_alerting.detect_seasonal_patterns()
    return {'patterns': patterns}
```

### Method: `detect_current_anomaly`
**Logic & Purpose:**
```text
Detect if current request is anomalous
```

**Parameters:** `request_data`
**Variables Used:** `anomaly`
**Implementation:**
```python
@staticmethod
async def detect_current_anomaly(request_data: Dict) -> Dict:
    """Detect if current request is anomalous"""
    anomaly = anomaly_detector.check_request(request_data)
    if anomaly:
        return {'is_anomaly': True, 'details': {'metric': anomaly.metric, 'value': anomaly.value, 'expected': anomaly.expected, 'deviation_percent': anomaly.deviation, 'severity': anomaly.severity, 'description': anomaly.description}}
    return {'is_anomaly': False}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/integrations.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/integrations.py`

**Module Overview**: 
```text
Third-Party Integrations Service - Phase 4

Integration adapters for popular monitoring, alerting, and incident management platforms:
- Datadog
- New Relic
- PagerDuty
- Opsgenie
- Microsoft Teams
- Slack (advanced)

Features:
- Unified integration interface
- Event forwarding
- Metric synchronization
- Alert forwarding
- Status sync
- Webhook management

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `integration_manager` = `IntegrationManager()`
- `integration_forwarder` = `IntegrationForwarder()`
- `monitoring_bridge` = `MonitoringBridge()`

## Dependencies & Imports
aiohttp, json, datetime.datetime, typing.Dict, typing.List, typing.Optional, typing.Any, dataclasses.dataclass, enum.Enum, os, src.core.logging.logger

## Feature Class: `IntegrationType`
---

## Feature Class: `IntegrationConfig`
**Description:**
```text
Configuration for a third-party integration
```

---

## Feature Class: `IntegrationEvent`
**Description:**
```text
Event to be forwarded to third-party service
```

---

## Feature Class: `IntegrationManager`
**Description:**
```text
Central manager for all third-party integrations
```

### Method: `__init__`
**Parameters:** `self, config_path`
**Implementation:**
```python
def __init__(self, config_path: str='config/integrations.json'):
    self.config_path = config_path
    self.integrations: Dict[str, IntegrationConfig] = {}
    self.logger = logger
    self.load_config()
```

### Method: `load_config`
**Logic & Purpose:**
```text
Load integration configurations
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def load_config(self):
    """Load integration configurations"""
    try:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                for name, config in data.items():
                    self.integrations[name] = IntegrationConfig(type=IntegrationType(config['type']), enabled=config.get('enabled', False), api_key=config.get('api_key'), endpoint=config.get('endpoint'), extra_config=config.get('extra_config', {}), created_at=config.get('created_at', datetime.now().isoformat()))
        else:
            self._load_from_env()
    except Exception as e:
        self.logger.error(f'Failed to load integration config: {e}')
        self._load_from_env()
```

### Method: `_load_from_env`
**Logic & Purpose:**
```text
Load configs from environment variables
```

**Parameters:** `self`
**Variables Used:** `env_configs`
**Implementation:**
```python
def _load_from_env(self):
    """Load configs from environment variables"""
    env_configs = {'datadog': {'type': IntegrationType.DATADOG, 'api_key': os.getenv('DATADOG_API_KEY'), 'endpoint': os.getenv('DATADOG_ENDPOINT', 'https://api.datadoghq.com'), 'enabled': bool(os.getenv('DATADOG_API_KEY'))}, 'newrelic': {'type': IntegrationType.NEWRELIC, 'api_key': os.getenv('NEWRELIC_API_KEY'), 'endpoint': os.getenv('NEWRELIC_ENDPOINT', 'https://api.newrelic.com'), 'enabled': bool(os.getenv('NEWRELIC_API_KEY'))}, 'pagerduty': {'type': IntegrationType.PAGERDUTY, 'api_key': os.getenv('PAGERDUTY_API_KEY'), 'endpoint': os.getenv('PAGERDUTY_ENDPOINT', 'https://events.pagerduty.com'), 'enabled': bool(os.getenv('PAGERDUTY_API_KEY')), 'extra_config': {'service_key': os.getenv('PAGERDUTY_SERVICE_KEY'), 'routing_key': os.getenv('PAGERDUTY_ROUTING_KEY')}}, 'slack': {'type': IntegrationType.SLACK, 'api_key': os.getenv('SLACK_BOT_TOKEN'), 'endpoint': os.getenv('SLACK_WEBHOOK_URL'), 'enabled': bool(os.getenv('SLACK_WEBHOOK_URL'))}, 'teams': {'type': IntegrationType.TEAMS, 'endpoint': os.getenv('TEAMS_WEBHOOK_URL'), 'enabled': bool(os.getenv('TEAMS_WEBHOOK_URL'))}}
    for name, config in env_configs.items():
        if config['enabled']:
            self.integrations[name] = IntegrationConfig(type=config['type'], enabled=config['enabled'], api_key=config.get('api_key'), endpoint=config.get('endpoint'), extra_config=config.get('extra_config', {}), created_at=datetime.now().isoformat())
```

### Method: `save_config`
**Logic & Purpose:**
```text
Save integration configurations
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def save_config(self):
    """Save integration configurations"""
    try:
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        data = {}
        for name, config in self.integrations.items():
            data[name] = {'type': config.type.value, 'enabled': config.enabled, 'api_key': config.api_key, 'endpoint': config.endpoint, 'extra_config': config.extra_config, 'created_at': config.created_at}
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        self.logger.error(f'Failed to save integration config: {e}')
```

### Method: `send_event`
**Logic & Purpose:**
```text
Send event to specified integrations
```

**Parameters:** `self, event, integration_names`
**Variables Used:** `results, result, targets, config`
**Implementation:**
```python
async def send_event(self, event: IntegrationEvent, integration_names: Optional[List[str]]=None):
    """Send event to specified integrations"""
    results = {}
    targets = []
    if integration_names:
        targets = [name for name in integration_names if name in self.integrations]
    else:
        targets = [name for name, config in self.integrations.items() if config.enabled]
    for name in targets:
        config = self.integrations[name]
        try:
            result = await self._send_to_integration(config, event)
            results[name] = result
        except Exception as e:
            self.logger.error(f'Failed to send to {name}: {e}')
            results[name] = {'success': False, 'error': str(e)}
    return results
```

### Method: `_send_to_integration`
**Logic & Purpose:**
```text
Send event to specific integration
```

**Parameters:** `self, config, event`
**Implementation:**
```python
async def _send_to_integration(self, config: IntegrationConfig, event: IntegrationEvent):
    """Send event to specific integration"""
    if config.type == IntegrationType.DATADOG:
        return await self._send_to_datadog(config, event)
    elif config.type == IntegrationType.NEWRELIC:
        return await self._send_to_newrelic(config, event)
    elif config.type == IntegrationType.PAGERDUTY:
        return await self._send_to_pagerduty(config, event)
    elif config.type == IntegrationType.SLACK:
        return await self._send_to_slack(config, event)
    elif config.type == IntegrationType.TEAMS:
        return await self._send_to_teams(config, event)
    elif config.type == IntegrationType.WEBHOOK:
        return await self._send_to_webhook(config, event)
    else:
        return {'success': False, 'error': f'Unknown integration type: {config.type}'}
```

### Method: `_send_to_datadog`
**Logic & Purpose:**
```text
Send metrics/events to Datadog
```

**Parameters:** `self, config, event`
**Variables Used:** `content, url, headers, payload`
**Implementation:**
```python
async def _send_to_datadog(self, config: IntegrationConfig, event: IntegrationEvent):
    """Send metrics/events to Datadog"""
    if not config.api_key or not config.endpoint:
        return {'success': False, 'error': 'Missing Datadog configuration'}
    payload = {'title': event.title, 'text': event.message, 'alert_type': self._map_severity_to_datadog(event.severity), 'tags': [f'severity:{event.severity}', f'type:{event.event_type}', f'source:claude-proxy'] + [f'{k}:{v}' for k, v in event.metadata.items()], 'date_happened': int(datetime.fromisoformat(event.timestamp).timestamp())}
    async with aiohttp.ClientSession() as session:
        url = f'{config.endpoint}/api/v1/events'
        headers = {'DD-API-KEY': config.api_key, 'Content-Type': 'application/json'}
        async with session.post(url, json=payload, headers=headers) as response:
            content = await response.text()
            return {'success': response.status == 202, 'status': response.status, 'response': content}
```

### Method: `_send_to_newrelic`
**Logic & Purpose:**
```text
Send events to New Relic
```

**Parameters:** `self, config, event`
**Variables Used:** `content, url, headers, payload`
**Implementation:**
```python
async def _send_to_newrelic(self, config: IntegrationConfig, event: IntegrationEvent):
    """Send events to New Relic"""
    if not config.api_key or not config.endpoint:
        return {'success': False, 'error': 'Missing New Relic configuration'}
    payload = {'eventType': 'ClaudeProxyEvent', 'title': event.title, 'message': event.message, 'severity': event.severity, 'type': event.event_type, 'timestamp': event.timestamp, **event.metadata}
    async with aiohttp.ClientSession() as session:
        url = f"{config.endpoint}/v1/accounts/{config.extra_config.get('account_id', 'unknown')}/events"
        headers = {'X-Query-Key': config.api_key, 'Content-Type': 'application/json'}
        async with session.post(url, json=[payload], headers=headers) as response:
            content = await response.text()
            return {'success': response.status == 200, 'status': response.status, 'response': content}
```

### Method: `_send_to_pagerduty`
**Logic & Purpose:**
```text
Send incidents to PagerDuty
```

**Parameters:** `self, config, event`
**Variables Used:** `url, content, routing_key, pd_severity, payload`
**Implementation:**
```python
async def _send_to_pagerduty(self, config: IntegrationConfig, event: IntegrationEvent):
    """Send incidents to PagerDuty"""
    routing_key = config.extra_config.get('routing_key') or config.api_key
    if not routing_key:
        return {'success': False, 'error': 'Missing PagerDuty routing key'}
    pd_severity = {'info': 'info', 'warning': 'warning', 'error': 'error', 'critical': 'critical'}.get(event.severity, 'error')
    payload = {'routing_key': routing_key, 'event_action': 'trigger', 'dedup_key': f'claude-proxy-{event.event_type}-{int(datetime.fromisoformat(event.timestamp).timestamp())}', 'payload': {'summary': event.title, 'severity': pd_severity, 'source': 'claude-proxy', 'component': event.event_type, 'custom_details': {'message': event.message, **event.metadata}}}
    async with aiohttp.ClientSession() as session:
        url = f'{config.endpoint}/v2/enqueue'
        async with session.post(url, json=payload) as response:
            content = await response.text()
            return {'success': response.status == 202, 'status': response.status, 'response': content}
```

### Method: `_send_to_slack`
**Logic & Purpose:**
```text
Send messages to Slack
```

**Parameters:** `self, config, event`
**Variables Used:** `metadata_text, content, color_map, color, payload`
**Implementation:**
```python
async def _send_to_slack(self, config: IntegrationConfig, event: IntegrationEvent):
    """Send messages to Slack"""
    if not config.endpoint:
        return {'success': False, 'error': 'Missing Slack webhook URL'}
    color_map = {'info': '#36a64f', 'warning': '#ffcc00', 'error': '#ff6600', 'critical': '#ff0000'}
    color = color_map.get(event.severity, '#808080')
    payload = {'attachments': [{'color': color, 'title': event.title, 'text': event.message, 'fields': [{'title': 'Severity', 'value': event.severity.upper(), 'short': True}, {'title': 'Type', 'value': event.event_type, 'short': True}], 'footer': 'Claude Proxy', 'ts': int(datetime.fromisoformat(event.timestamp).timestamp())}]}
    if event.metadata:
        metadata_text = '\n'.join([f'*{k}*: {v}' for k, v in event.metadata.items()])
        payload['attachments'][0]['fields'].append({'title': 'Details', 'value': metadata_text, 'short': False})
    async with aiohttp.ClientSession() as session:
        async with session.post(config.endpoint, json=payload) as response:
            content = await response.text()
            return {'success': response.status == 200, 'status': response.status, 'response': content}
```

### Method: `_send_to_teams`
**Logic & Purpose:**
```text
Send messages to Microsoft Teams
```

**Parameters:** `self, config, event`
**Variables Used:** `color_map, color, content, payload`
**Implementation:**
```python
async def _send_to_teams(self, config: IntegrationConfig, event: IntegrationEvent):
    """Send messages to Microsoft Teams"""
    if not config.endpoint:
        return {'success': False, 'error': 'Missing Teams webhook URL'}
    color_map = {'info': '00ff00', 'warning': 'ffcc00', 'error': 'ff6600', 'critical': 'ff0000'}
    color = color_map.get(event.severity, '808080')
    payload = {'@type': 'MessageCard', '@context': 'https://schema.org/extensions', 'themeColor': color, 'summary': event.title, 'sections': [{'activityTitle': event.title, 'activitySubtitle': f'{event.event_type} - {event.severity.upper()}', 'facts': [{'name': 'Timestamp', 'value': event.timestamp}, {'name': 'Severity', 'value': event.severity.upper()}, {'name': 'Type', 'value': event.event_type}] + [{'name': k, 'value': str(v)} for k, v in event.metadata.items()], 'text': event.message}]}
    async with aiohttp.ClientSession() as session:
        async with session.post(config.endpoint, json=payload) as response:
            content = await response.text()
            return {'success': response.status == 200, 'status': response.status, 'response': content}
```

### Method: `_send_to_webhook`
**Logic & Purpose:**
```text
Send to generic webhook
```

**Parameters:** `self, config, event`
**Variables Used:** `headers, content, payload`
**Implementation:**
```python
async def _send_to_webhook(self, config: IntegrationConfig, event: IntegrationEvent):
    """Send to generic webhook"""
    if not config.endpoint:
        return {'success': False, 'error': 'Missing webhook URL'}
    payload = {'event_type': event.event_type, 'severity': event.severity, 'title': event.title, 'message': event.message, 'timestamp': event.timestamp, 'metadata': event.metadata, 'source': 'claude-proxy'}
    headers = config.extra_config.get('headers', {})
    if not isinstance(headers, dict):
        headers = {}
    async with aiohttp.ClientSession() as session:
        async with session.post(config.endpoint, json=payload, headers=headers) as response:
            content = await response.text()
            return {'success': 200 <= response.status < 300, 'status': response.status, 'response': content}
```

### Method: `_map_severity_to_datadog`
**Logic & Purpose:**
```text
Map our severity to Datadog alert types
```

**Parameters:** `self, severity`
**Implementation:**
```python
def _map_severity_to_datadog(self, severity: str) -> str:
    """Map our severity to Datadog alert types"""
    return {'info': 'info', 'warning': 'warning', 'error': 'error', 'critical': 'error'}.get(severity, 'info')
```

### Method: `test_integration`
**Logic & Purpose:**
```text
Test a specific integration
```

**Parameters:** `self, name`
**Variables Used:** `result, test_event, config`
**Implementation:**
```python
async def test_integration(self, name: str) -> Dict[str, Any]:
    """Test a specific integration"""
    if name not in self.integrations:
        return {'success': False, 'error': 'Integration not configured'}
    config = self.integrations[name]
    if not config.enabled:
        return {'success': False, 'error': 'Integration is disabled'}
    test_event = IntegrationEvent(event_type='test', severity='info', title='Integration Test', message='This is a test notification from Claude Proxy', timestamp=datetime.now().isoformat(), metadata={'test': 'true', 'integration': name})
    try:
        result = await self._send_to_integration(config, test_event)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### Method: `list_integrations`
**Logic & Purpose:**
```text
List all configured integrations
```

**Parameters:** `self`
**Implementation:**
```python
def list_integrations(self) -> List[Dict[str, Any]]:
    """List all configured integrations"""
    return [{'name': name, 'type': config.type.value, 'enabled': config.enabled, 'endpoint': config.endpoint, 'has_api_key': bool(config.api_key), 'extra_config': config.extra_config} for name, config in self.integrations.items()]
```

---

## Feature Class: `IntegrationForwarder`
**Description:**
```text
Automated event forwarding based on rules
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.manager = integration_manager
    self.logger = logger
```

### Method: `forward_alert`
**Logic & Purpose:**
```text
Forward alert to configured integrations
```

**Parameters:** `self, alert_data, target_integrations`
**Variables Used:** `event`
**Implementation:**
```python
async def forward_alert(self, alert_data: Dict[str, Any], target_integrations: Optional[List[str]]=None):
    """Forward alert to configured integrations"""
    event = IntegrationEvent(event_type='alert', severity=alert_data.get('severity', 'warning'), title=f"Alert: {alert_data.get('name', 'Unnamed Alert')}", message=alert_data.get('message', ''), timestamp=datetime.now().isoformat(), metadata={'rule_id': alert_data.get('id', ''), 'triggered_at': alert_data.get('triggered_at', ''), 'value': alert_data.get('value', ''), 'threshold': alert_data.get('threshold', '')})
    return await self.manager.send_event(event, target_integrations)
```

### Method: `forward_anomaly`
**Logic & Purpose:**
```text
Forward anomaly detection to integrations
```

**Parameters:** `self, anomaly_data, target_integrations`
**Variables Used:** `event`
**Implementation:**
```python
async def forward_anomaly(self, anomaly_data: Dict[str, Any], target_integrations: Optional[List[str]]=None):
    """Forward anomaly detection to integrations"""
    event = IntegrationEvent(event_type='anomaly', severity=anomaly_data.get('severity', 'warning'), title=f"Anomaly Detected: {anomaly_data.get('metric', 'unknown')}", message=f"Detected deviation of {anomaly_data.get('deviation', 0)}%", timestamp=datetime.now().isoformat(), metadata={'metric': anomaly_data.get('metric'), 'expected': anomaly_data.get('expected'), 'actual': anomaly_data.get('actual'), 'deviation': anomaly_data.get('deviation')})
    return await self.manager.send_event(event, target_integrations)
```

### Method: `forward_metric`
**Logic & Purpose:**
```text
Forward metrics to integrations (for observability)
```

**Parameters:** `self, metric_data, target_integrations`
**Variables Used:** `event`
**Implementation:**
```python
async def forward_metric(self, metric_data: Dict[str, Any], target_integrations: Optional[List[str]]=None):
    """Forward metrics to integrations (for observability)"""
    event = IntegrationEvent(event_type='metric', severity='info', title=f"Metrics: {metric_data.get('name', 'Unknown')}", message=f"Value: {metric_data.get('value', 0)}", timestamp=datetime.now().isoformat(), metadata={'metric': metric_data.get('name'), 'value': metric_data.get('value'), 'unit': metric_data.get('unit', '')})
    return await self.manager.send_event(event, target_integrations)
```

### Method: `forward_report`
**Logic & Purpose:**
```text
Forward report completion notification
```

**Parameters:** `self, report_data, target_integrations`
**Variables Used:** `event`
**Implementation:**
```python
async def forward_report(self, report_data: Dict[str, Any], target_integrations: Optional[List[str]]=None):
    """Forward report completion notification"""
    event = IntegrationEvent(event_type='report', severity='info', title=f"Report Generated: {report_data.get('name', 'Unknown')}", message=f"Format: {report_data.get('format', 'unknown')} - Size: {report_data.get('size', 0)} bytes", timestamp=datetime.now().isoformat(), metadata={'report_name': report_data.get('name'), 'format': report_data.get('format'), 'size': report_data.get('size'), 'recipients': report_data.get('recipients', [])})
    return await self.manager.send_event(event, target_integrations)
```

---

## Feature Class: `MonitoringBridge`
**Description:**
```text
Bridge for external monitoring systems
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.manager = integration_manager
    self.logger = logger
```

### Method: `get_datadog_metrics`
**Logic & Purpose:**
```text
Fetch metrics from Datadog for correlation
```

**Parameters:** `self, metric_name, hours`
**Variables Used:** `config`
**Implementation:**
```python
async def get_datadog_metrics(self, metric_name: str, hours: int=24):
    """Fetch metrics from Datadog for correlation"""
    config = self.manager.integrations.get('datadog')
    if not config or not config.api_key:
        return {'error': 'Datadog not configured'}
    return {'note': 'Datadog metric fetch requires additional configuration'}
```

### Method: `get_newrelic_metrics`
**Logic & Purpose:**
```text
Fetch metrics from New Relic
```

**Parameters:** `self, metric_name, hours`
**Variables Used:** `config`
**Implementation:**
```python
async def get_newrelic_metrics(self, metric_name: str, hours: int=24):
    """Fetch metrics from New Relic"""
    config = self.manager.integrations.get('newrelic')
    if not config or not config.api_key:
        return {'error': 'New Relic not configured'}
    return {'note': 'New Relic metric fetch requires additional configuration'}
```

### Method: `sync_status`
**Logic & Purpose:**
```text
Sync current status with all configured monitoring systems
```

**Parameters:** `self`
**Variables Used:** `results, status_event, forecast`
**Implementation:**
```python
async def sync_status(self):
    """Sync current status with all configured monitoring systems"""
    from src.services.predictive_alerting import predictive_alerting
    forecast = predictive_alerting.predict_metrics(1)
    status_event = IntegrationEvent(event_type='status', severity='info', title='System Status Update', message=f'Active requests: monitoring... Forecast risk: {forecast.risk_level}', timestamp=datetime.now().isoformat(), metadata={'risk_level': forecast.risk_level, 'predicted_cost': round(forecast.cost_prediction, 4), 'predicted_tokens': round(forecast.total_tokens_predicted, 0), 'timestamp': datetime.now().isoformat()})
    results = await self.manager.send_event(status_event)
    return {'status': 'synced', 'integrations': results}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/advanced_scheduler.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/advanced_scheduler.py`

**Module Overview**: 
```text
Advanced Report Scheduler - Phase 4

Intelligent report scheduling with ML-based timing optimization,
delivery preferences, and smart batch processing.

Features:
- Smart scheduling based on usage patterns
- Multi-recipient management
- Batch processing and queuing
- Delivery format optimization
- Performance analytics

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `advanced_scheduler` = `AdvancedScheduler()`
- `smart_template_manager` = `SmartTemplateManager()`

## Dependencies & Imports
sqlite3, json, asyncio, datetime.datetime, datetime.timedelta, typing.List, typing.Dict, typing.Any, typing.Optional, dataclasses.dataclass, enum.Enum, smtplib, email.mime.text.MIMEText, email.mime.multipart.MIMEMultipart, email.mime.application.MIMEApplication, src.core.logging.logger, src.services.report_generator.report_generator

## Feature Class: `ScheduleFrequency`
---

## Feature Class: `DeliveryMethod`
---

## Feature Class: `ScheduledReport`
**Description:**
```text
Represents a scheduled report configuration
```

---

## Feature Class: `ReportExecution`
**Description:**
```text
Represents a completed report execution
```

---

## Feature Class: `AdvancedScheduler`
**Description:**
```text
Intelligent report scheduler with optimization capabilities
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Implementation:**
```python
def __init__(self, db_path: str='usage_tracking.db'):
    self.db_path = db_path
    self.running = False
    self.check_interval = 60
    self.logger = logger
```

### Method: `start`
**Logic & Purpose:**
```text
Start the scheduler loop
```

**Parameters:** `self`
**Implementation:**
```python
async def start(self):
    """Start the scheduler loop"""
    if self.running:
        return
    self.running = True
    self.logger.info('Advanced scheduler started')
    self.initialize_tables()
    while self.running:
        try:
            await self.process_due_reports()
            await asyncio.sleep(self.check_interval)
        except Exception as e:
            self.logger.error(f'Scheduler error: {e}')
            await asyncio.sleep(self.check_interval)
```

### Method: `initialize_tables`
**Logic & Purpose:**
```text
Create necessary tables if they don't exist
```

**Parameters:** `self`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
def initialize_tables(self):
    """Create necessary tables if they don't exist"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                CREATE TABLE IF NOT EXISTS scheduled_reports (\n                    id TEXT PRIMARY KEY,\n                    template_id TEXT,\n                    name TEXT,\n                    frequency TEXT,\n                    recipients TEXT,\n                    timezone TEXT,\n                    is_active INTEGER,\n                    next_run TEXT,\n                    last_run TEXT,\n                    delivery_method TEXT,\n                    config TEXT\n                )')
        cursor.execute('\n                CREATE TABLE IF NOT EXISTS report_templates (\n                    id TEXT PRIMARY KEY,\n                    name TEXT,\n                    description TEXT,\n                    metrics TEXT,\n                    filters TEXT,\n                    chart_config TEXT,\n                    created_at TEXT,\n                    created_by TEXT\n                )')
        conn.commit()
        conn.close()
        logger.info('✅ Tables initialized for advanced scheduler')
    except Exception as e:
        logger.error(f'❌ Failed to initialize tables: {e}')
```

### Method: `stop`
**Logic & Purpose:**
```text
Stop the scheduler
```

**Parameters:** `self`
**Implementation:**
```python
async def stop(self):
    """Stop the scheduler"""
    self.running = False
    self.logger.info('Advanced scheduler stopped')
```

### Method: `process_due_reports`
**Logic & Purpose:**
```text
Process all due scheduled reports
```

**Parameters:** `self`
**Variables Used:** `due_reports`
**Implementation:**
```python
async def process_due_reports(self):
    """Process all due scheduled reports"""
    try:
        due_reports = self.get_due_reports()
        for report in due_reports:
            if not report.is_active:
                continue
            try:
                await self.execute_report(report)
            except Exception as e:
                self.logger.error(f'Failed to execute report {report.id}: {e}')
                await self.record_execution(report.id, report.template_id, 'failed', error_message=str(e))
    except Exception as e:
        self.logger.error(f'Failed to process due reports: {e}')
```

### Method: `get_due_reports`
**Logic & Purpose:**
```text
Get all reports that are due for execution
```

**Parameters:** `self`
**Variables Used:** `now, cursor, rows, report, conn, reports`
**Implementation:**
```python
def get_due_reports(self) -> List[ScheduledReport]:
    """Get all reports that are due for execution"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        now = datetime.now().isoformat()
        cursor = conn.execute('\n                SELECT * FROM scheduled_reports\n                WHERE is_active = 1\n                AND next_run <= ?\n                ORDER BY next_run ASC\n            ', [now])
        rows = cursor.fetchall()
        conn.close()
        reports = []
        for row in rows:
            report = ScheduledReport(id=row['id'], template_id=row['template_id'], name=row['name'] if 'name' in row.keys() else row['id'], frequency=ScheduleFrequency(row['frequency']), recipients=json.loads(row['recipients']), timezone=row['timezone'], is_active=bool(row['is_active']), next_run=datetime.fromisoformat(row['next_run']), last_run=datetime.fromisoformat(row['last_run']) if row['last_run'] else None, delivery_method=DeliveryMethod(row.get('delivery_method', 'email')), config=json.loads(row.get('config', '{}')))
            reports.append(report)
        return reports
    except Exception as e:
        self.logger.error(f'Failed to get due reports: {e}')
        return []
```

### Method: `execute_report`
**Logic & Purpose:**
```text
Execute a single scheduled report
```

**Parameters:** `self, report`
**Variables Used:** `report_data, template, file_data, end_date, format_type, start_date, delivery_results`
**Implementation:**
```python
async def execute_report(self, report: ScheduledReport):
    """Execute a single scheduled report"""
    self.logger.info(f'Executing scheduled report: {report.id}')
    template = report_generator.get_template(report.template_id)
    if not template:
        raise ValueError(f'Template {report.template_id} not found')
    end_date = datetime.now()
    if report.frequency == ScheduleFrequency.DAILY:
        start_date = end_date - timedelta(days=1)
    elif report.frequency == ScheduleFrequency.WEEKLY:
        start_date = end_date - timedelta(weeks=1)
    elif report.frequency == ScheduleFrequency.MONTHLY:
        start_date = end_date - timedelta(days=30)
    elif report.frequency == ScheduleFrequency.HOURLY:
        start_date = end_date - timedelta(hours=1)
    else:
        start_date = end_date - timedelta(days=1)
    report_data = report_generator.generate_report_data(template, start_date.isoformat(), end_date.isoformat())
    format_type = report.config.get('format', 'pdf')
    file_data = None
    if format_type == 'pdf':
        file_data = report_generator.generate_pdf(template, start_date.isoformat(), end_date.isoformat(), report.config.get('brand_logo'), report.config.get('brand_color', '#3b82f6'))
    elif format_type == 'excel':
        file_data = report_generator.generate_excel(template, start_date.isoformat(), end_date.isoformat())
    elif format_type == 'csv':
        file_data = report_generator.generate_csv(template, start_date.isoformat(), end_date.isoformat()).encode('utf-8')
    delivery_results = await self.deliver_report(report, file_data, format_type, start_date, end_date)
    await self.update_next_run(report.id)
    await self.record_execution(report.id, report.template_id, 'success', len(file_data) if file_data else 0, delivery_results=delivery_results)
    self.logger.info(f'Successfully executed report {report.id}')
```

### Method: `deliver_report`
**Logic & Purpose:**
```text
Deliver report to recipients via specified method
```

**Parameters:** `self, report, file_data, format_type, start_date, end_date`
**Variables Used:** `results`
**Implementation:**
```python
async def deliver_report(self, report: ScheduledReport, file_data: bytes, format_type: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Deliver report to recipients via specified method"""
    results = {}
    if report.delivery_method == DeliveryMethod.EMAIL:
        results = await self._deliver_email(report.recipients, file_data, format_type, report.name, start_date, end_date)
    elif report.delivery_method == DeliveryMethod.SLACK:
        results = await self._deliver_slack(report.recipients, report.name, start_date, end_date)
    elif report.delivery_method == DeliveryMethod.WEBHOOK:
        results = await self._deliver_webhook(report.recipients, report.name, file_data, format_type)
    elif report.delivery_method == DeliveryMethod.IN_APP:
        results = {'status': 'queued', 'recipients': report.recipients}
    return results
```

### Method: `_deliver_email`
**Logic & Purpose:**
```text
Deliver via email
```

**Parameters:** `self, recipients, file_data, format_type, report_name, start_date, end_date`
**Variables Used:** `smtp_server, smtp_port, from_email, smtp_password, smtp_user, body, msg, attachment, filename`
**Implementation:**
```python
async def _deliver_email(self, recipients: List[str], file_data: bytes, format_type: str, report_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Deliver via email"""
    try:
        import os
        smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        from_email = os.getenv('FROM_EMAIL', smtp_user or 'reports@localhost')
        msg = MIMEMultipart()
        msg['Subject'] = f'[Report] {report_name} ({start_date.date()} to {end_date.date()})'
        msg['From'] = from_email
        msg['To'] = ', '.join(recipients)
        body = f'\n            Hello,\n\n            Your scheduled report "{report_name}" is ready.\n\n            Period: {start_date.date()} to {end_date.date()}\n            Format: {format_type.upper()}\n\n            Please find the report attached.\n\n            This is an automated message from the analytics system.\n            '
        msg.attach(MIMEText(body, 'plain'))
        filename = f"{report_name.replace(' ', '_')}_{start_date.date()}_{end_date.date()}.{format_type}"
        attachment = MIMEApplication(file_data, _subtype=format_type)
        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(attachment)
        if smtp_server != 'localhost':
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_port == 587:
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
                return {'status': 'sent', 'recipients': recipients}
        else:
            return {'status': 'simulated', 'recipients': recipients, 'note': 'SMTP not configured'}
    except Exception as e:
        self.logger.error(f'Email delivery failed: {e}')
        return {'status': 'failed', 'error': str(e)}
```

### Method: `_deliver_slack`
**Logic & Purpose:**
```text
Deliver via Slack webhook
```

**Parameters:** `self, recipients, report_name, start_date, end_date`
**Variables Used:** `payload, webhook_url`
**Implementation:**
```python
async def _deliver_slack(self, recipients: List[str], report_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Deliver via Slack webhook"""
    try:
        import os
        import aiohttp
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return {'status': 'simulated', 'recipients': recipients, 'note': 'Slack webhook not configured'}
        payload = {'text': f'📊 Report Generated: {report_name}', 'blocks': [{'type': 'header', 'text': {'type': 'plain_text', 'text': f'📊 {report_name}'}}, {'type': 'section', 'fields': [{'type': 'mrkdown', 'text': f'*Period:*\n{start_date.date()} - {end_date.date()}'}, {'type': 'mrkdown', 'text': f'*Recipients:*\n{len(recipients)} users'}]}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    return {'status': 'sent', 'recipients': recipients}
                else:
                    return {'status': 'failed', 'error': f'Slack API returned {response.status}'}
    except Exception as e:
        self.logger.error(f'Slack delivery failed: {e}')
        return {'status': 'failed', 'error': str(e)}
```

### Method: `_deliver_webhook`
**Logic & Purpose:**
```text
Deliver via webhook
```

**Parameters:** `self, recipients, report_name, file_data, format_type`
**Variables Used:** `results, payload`
**Implementation:**
```python
async def _deliver_webhook(self, recipients: List[str], report_name: str, file_data: bytes, format_type: str) -> Dict[str, Any]:
    """Deliver via webhook"""
    try:
        import aiohttp
        import base64
        results = []
        for url in recipients:
            payload = {'report_name': report_name, 'format': format_type, 'data_base64': base64.b64encode(file_data).decode('utf-8'), 'timestamp': datetime.now().isoformat()}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    results.append({'url': url, 'status': response.status, 'success': response.status == 200})
        return {'status': 'completed', 'results': results}
    except Exception as e:
        self.logger.error(f'Webhook delivery failed: {e}')
        return {'status': 'failed', 'error': str(e)}
```

### Method: `update_next_run`
**Logic & Purpose:**
```text
Update next run time based on frequency
```

**Parameters:** `self, report_id`
**Variables Used:** `current_next, cursor, frequency, next_run, conn, row`
**Implementation:**
```python
async def update_next_run(self, report_id: str):
    """Update next run time based on frequency"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT frequency, next_run FROM scheduled_reports WHERE id = ?', (report_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        frequency = row[0]
        current_next = datetime.fromisoformat(row[1])
        if frequency == 'hourly':
            next_run = current_next + timedelta(hours=1)
        elif frequency == 'daily':
            next_run = current_next + timedelta(days=1)
        elif frequency == 'weekly':
            next_run = current_next + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_run = current_next + timedelta(days=30)
        else:
            next_run = current_next + timedelta(days=1)
        conn.execute('UPDATE scheduled_reports SET next_run = ?, last_run = ? WHERE id = ?', (next_run.isoformat(), datetime.now().isoformat(), report_id))
        conn.commit()
        conn.close()
    except Exception as e:
        self.logger.error(f'Failed to update next run: {e}')
```

### Method: `record_execution`
**Logic & Purpose:**
```text
Record report execution in database
```

**Parameters:** `self, scheduled_report_id, template_id, status, file_size, error_message, delivery_results`
**Variables Used:** `conn, execution_id`
**Implementation:**
```python
async def record_execution(self, scheduled_report_id: str, template_id: str, status: str, file_size: Optional[int]=None, error_message: Optional[str]=None, delivery_results: Optional[Dict[str, Any]]=None):
    """Record report execution in database"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.execute('\n                CREATE TABLE IF NOT EXISTS report_executions (\n                    id TEXT PRIMARY KEY,\n                    scheduled_report_id TEXT,\n                    template_id TEXT,\n                    execution_time TEXT,\n                    status TEXT,\n                    file_size INTEGER,\n                    error_message TEXT,\n                    delivery_results TEXT\n                )\n            ')
        import uuid
        execution_id = str(uuid.uuid4())
        conn.execute('\n                INSERT INTO report_executions (\n                    id, scheduled_report_id, template_id, execution_time,\n                    status, file_size, error_message, delivery_results\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            ', (execution_id, scheduled_report_id, template_id, datetime.now().isoformat(), status, file_size, error_message, json.dumps(delivery_results) if delivery_results else None))
        conn.commit()
        conn.close()
    except Exception as e:
        self.logger.error(f'Failed to record execution: {e}')
```

### Method: `get_execution_history`
**Logic & Purpose:**
```text
Get report execution history
```

**Parameters:** `self, limit`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_execution_history(self, limit: int=50) -> List[Dict[str, Any]]:
    """Get report execution history"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('\n                SELECT e.*, t.name as template_name, sr.name as schedule_name\n                FROM report_executions e\n                LEFT JOIN report_templates t ON e.template_id = t.id\n                LEFT JOIN scheduled_reports sr ON e.scheduled_report_id = sr.id\n                ORDER BY e.execution_time DESC\n                LIMIT ?\n            ', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        self.logger.error(f'Failed to get execution history: {e}')
        return []
```

### Method: `optimize_schedule`
**Logic & Purpose:**
```text
Analyze patterns and suggest optimal scheduling
```

**Parameters:** `self`
**Variables Used:** `cursor, success, hour, rows, total, conn, optimal, success_rates`
**Implementation:**
```python
def optimize_schedule(self) -> Dict[str, Any]:
    """Analyze patterns and suggest optimal scheduling"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("\n                SELECT\n                    strftime('%H', execution_time) as hour,\n                    COUNT(*) as total,\n                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success\n                FROM report_executions\n                WHERE execution_time >= ?\n                GROUP BY strftime('%H', execution_time)\n            ", [(datetime.now() - timedelta(days=30)).isoformat()])
        rows = cursor.fetchall()
        conn.close()
        success_rates = {}
        for row in rows:
            hour = row['hour']
            total = row['total']
            success = row['success']
            if total > 0:
                success_rates[int(hour)] = (success / total, total)
        optimal = sorted(success_rates.items(), key=lambda x: x[1][0], reverse=True)[:3]
        return {'optimal_hours': [hour for hour, _ in optimal], 'success_rates': {hour: round(rate, 2) for hour, (rate, _) in optimal}, 'sample_sizes': {hour: count for hour, (_, count) in optimal}, 'recommendation': f"Best times: {', '.join([f'{h}:00' for h, _ in optimal])}"}
    except Exception as e:
        self.logger.error(f'Schedule optimization failed: {e}')
        return {}
```

---

## Feature Class: `SmartTemplateManager`
**Description:**
```text
AI-powered template management and recommendations
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Implementation:**
```python
def __init__(self, db_path: str='usage_tracking.db'):
    self.db_path = db_path
```

### Method: `get_template_recommendations`
**Logic & Purpose:**
```text
Get recommendations for template creation based on usage patterns
```

**Parameters:** `self`
**Variables Used:** `cursor, cost_data, recommendations, providers, conn`
**Implementation:**
```python
def get_template_recommendations(self) -> List[Dict[str, Any]]:
    """Get recommendations for template creation based on usage patterns"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('\n                SELECT\n                    provider,\n                    COUNT(*) as count,\n                    SUM(total_tokens) as tokens,\n                    SUM(estimated_cost) as cost\n                FROM api_requests\n                WHERE timestamp >= ?\n                GROUP BY provider\n                ORDER BY count DESC\n            ', [(datetime.now() - timedelta(days=30)).isoformat()])
        providers = cursor.fetchall()
        recommendations = []
        for provider in providers:
            if provider['count'] > 10:
                recommendations.append({'name': f"{provider['provider'].title()} Usage Report", 'type': 'provider_specific', 'description': f"Monthly usage analysis for {provider['provider']}", 'metrics': ['tokens', 'cost', 'requests'], 'filters': {'provider': provider['provider']}, 'estimated_value': {'tokens': provider['tokens'], 'cost': provider['cost'], 'requests': provider['count']}})
        cursor = conn.execute('\n                SELECT\n                    AVG(estimated_cost) as avg_cost,\n                    SUM(estimated_cost) as total_cost\n                FROM api_requests\n                WHERE timestamp >= ?\n            ', [(datetime.now() - timedelta(days=30)).isoformat()])
        cost_data = cursor.fetchone()
        conn.close()
        if cost_data and cost_data['total_cost'] > 10:
            recommendations.append({'name': 'Cost Optimization Report', 'type': 'optimization', 'description': 'Identify cost-saving opportunities', 'metrics': ['cost', 'tokens'], 'analysis': 'efficiency', 'value': round(cost_data['total_cost'], 2)})
        return recommendations
    except Exception as e:
        logger.error(f'Template recommendations failed: {e}')
        return []
```

### Method: `generate_template_config`
**Logic & Purpose:**
```text
Generate a template configuration
```

**Parameters:** `self, name, filters, metrics`
**Implementation:**
```python
def generate_template_config(self, name: str, filters: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
    """Generate a template configuration"""
    return {'name': name, 'description': f'Auto-generated report for {name}', 'filters': filters, 'metrics': metrics, 'charts': ['token_trend', 'cost_over_time'] if 'tokens' in metrics and 'cost' in metrics else ['bar_chart'], 'tables': ['summary'], 'date_range': '30d', 'format': ['pdf', 'excel'], 'auto_generate': True}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/cli/session_collector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/cli/session_collector.py`

**Module Overview**: 
```text
CLI Tool Session Collector

Collects and aggregates session data from popular AI coding CLI tools:
- Claude Code (~/.claude/)
- OpenCode (~/.config/opencode/)
- OpenClaw (~/.openclaw/)
- Hermes (~/.hermes/)
- Aider (~/.aider/)
- And more...

Collects:
- Session count and duration
- Token usage (if available)
- Model preferences
- Tool/plugin usage
- Command history
```

## Dependencies & Imports
json, os, datetime.datetime, pathlib.Path, typing.Dict, typing.List, typing.Any, typing.Optional, collections.defaultdict

## Feature Class: `CLISessionCollector`
**Description:**
```text
Collects session data from AI coding CLI tools.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.home = Path.home()
    self.collected_data: Dict[str, Any] = {}
```

### Method: `expand_path`
**Logic & Purpose:**
```text
Expand ~ to home directory.
```

**Parameters:** `self, path`
**Implementation:**
```python
def expand_path(self, path: str) -> Path:
    """Expand ~ to home directory."""
    if path.startswith('~'):
        return self.home / path[2:]
    return Path(path)
```

### Method: `collect_all`
**Logic & Purpose:**
```text
Collect data from all available CLI tools.
```

**Parameters:** `self`
**Variables Used:** `results, tool_data`
**Implementation:**
```python
def collect_all(self) -> Dict[str, Any]:
    """Collect data from all available CLI tools."""
    results = {'timestamp': datetime.utcnow().isoformat() + 'Z', 'tools': {}, 'summary': {'total_tools': 0, 'total_sessions': 0, 'total_config_files': 0}}
    for tool_id, config in self.CLI_TOOLS.items():
        tool_data = self.collect_tool(tool_id, config)
        if tool_data['available']:
            results['tools'][tool_id] = tool_data
            results['summary']['total_tools'] += 1
            results['summary']['total_sessions'] += tool_data.get('sessions', {}).get('count', 0)
            results['summary']['total_config_files'] += len(tool_data.get('config_files', []))
    self.collected_data = results
    return results
```

### Method: `collect_tool`
**Logic & Purpose:**
```text
Collect data from a specific CLI tool.
```

**Parameters:** `self, tool_id, config`
**Variables Used:** `config_path, tool_data, sessions_path, session_dirs, settings_file, session_env, plugins, models, content, env_sessions, expanded, sessions, settings`
**Implementation:**
```python
def collect_tool(self, tool_id: str, config: Dict) -> Dict[str, Any]:
    """Collect data from a specific CLI tool."""
    tool_data = {'name': config['name'], 'available': False, 'settings': None, 'sessions': {'count': 0, 'items': []}, 'config_files': [], 'models_used': [], 'plugins': [], 'errors': []}
    for dir_path in config.get('dirs', []):
        expanded = self.expand_path(dir_path)
        if expanded.exists():
            tool_data['available'] = True
            if 'settings' in config.get('files', {}):
                settings_file = expanded / config['files']['settings']
                if settings_file.exists():
                    try:
                        with open(settings_file, 'r') as f:
                            if settings_file.suffix == '.json':
                                tool_data['settings'] = json.load(f)
                            else:
                                tool_data['settings'] = {'raw': settings_file.read_text()[:1000]}
                    except Exception as e:
                        tool_data['errors'].append(f'Settings error: {e}')
            if 'sessions' in config.get('files', {}):
                sessions_path = expanded / config['files']['sessions']
                if sessions_path.exists():
                    if sessions_path.is_file() and sessions_path.suffix == '.json':
                        try:
                            with open(sessions_path, 'r') as f:
                                sessions = json.load(f)
                                if isinstance(sessions, list):
                                    tool_data['sessions']['count'] = len(sessions)
                                    tool_data['sessions']['items'] = sessions[:10]
                                elif isinstance(sessions, dict):
                                    tool_data['sessions']['count'] = len(sessions.get('sessions', []))
                                    tool_data['sessions']['items'] = sessions.get('sessions', [])[:10]
                        except Exception as e:
                            tool_data['errors'].append(f'Sessions error: {e}')
                    elif sessions_path.is_dir():
                        session_dirs = [d for d in sessions_path.iterdir() if d.is_dir()]
                        tool_data['sessions']['count'] = len(session_dirs)
                        tool_data['sessions']['items'] = [{'id': d.name, 'path': str(d)} for d in sorted(session_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[:10]]
            session_env = expanded / 'session-env'
            if session_env.exists() and session_env.is_dir():
                env_sessions = [d for d in session_env.iterdir() if d.is_dir()]
                tool_data['sessions']['count'] += len(env_sessions)
            for config_file in config.get('config_files', []):
                config_path = expanded / config_file
                if config_path.exists():
                    try:
                        content = config_path.read_text()
                        tool_data['config_files'].append({'name': config_file, 'size': len(content), 'lines': content.count('\n') + 1, 'preview': content[:500]})
                    except Exception as e:
                        tool_data['errors'].append(f'Config file error: {e}')
            if tool_data['settings']:
                settings = tool_data['settings']
                if isinstance(settings, dict):
                    if 'model' in settings:
                        tool_data['models_used'].append(settings['model'])
                    if 'models' in settings:
                        models = settings['models']
                        if isinstance(models, list):
                            tool_data['models_used'].extend(models[:5])
                        elif isinstance(models, dict):
                            tool_data['models_used'].extend(list(models.keys())[:5])
                    if 'enabledPlugins' in settings:
                        plugins = settings['enabledPlugins']
                        if isinstance(plugins, dict):
                            tool_data['plugins'] = [k for k, v in plugins.items() if v]
                        elif isinstance(plugins, list):
                            tool_data['plugins'] = plugins[:10]
    return tool_data
```

### Method: `get_aggregate_stats`
**Logic & Purpose:**
```text
Get aggregate statistics across all CLI tools.
```

**Parameters:** `self`
**Variables Used:** `stats`
**Implementation:**
```python
def get_aggregate_stats(self) -> Dict[str, Any]:
    """Get aggregate statistics across all CLI tools."""
    if not self.collected_data:
        self.collect_all()
    stats = {'total_tools': self.collected_data['summary']['total_tools'], 'total_sessions': self.collected_data['summary']['total_sessions'], 'total_config_files': self.collected_data['summary']['total_config_files'], 'tools_breakdown': {}, 'all_models': [], 'all_plugins': [], 'config_file_types': defaultdict(int)}
    for tool_id, tool_data in self.collected_data.get('tools', {}).items():
        stats['tools_breakdown'][tool_id] = {'name': tool_data['name'], 'sessions': tool_data['sessions']['count'], 'config_files': len(tool_data['config_files'])}
        stats['all_models'].extend(tool_data.get('models_used', []))
        stats['all_plugins'].extend(tool_data.get('plugins', []))
        for config_file in tool_data.get('config_files', []):
            stats['config_file_types'][config_file['name']] += 1
    stats['all_models'] = list(set(stats['all_models']))
    stats['all_plugins'] = list(set(stats['all_plugins']))
    stats['config_file_types'] = dict(stats['config_file_types'])
    return stats
```

### Method: `get_session_timeline`
**Logic & Purpose:**
```text
Get timeline of recent sessions across all tools.
```

**Parameters:** `self, days`
**Variables Used:** `session_time, timeline, cutoff, session_path`
**Implementation:**
```python
def get_session_timeline(self, days: int=7) -> List[Dict[str, Any]]:
    """Get timeline of recent sessions across all tools."""
    timeline = []
    cutoff = datetime.utcnow() - timedelta(days=days)
    for tool_id, tool_data in self.collected_data.get('tools', {}).items():
        for session in tool_data.get('sessions', {}).get('items', []):
            try:
                session_time = None
                if 'created_at' in session:
                    session_time = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                elif 'timestamp' in session:
                    session_time = datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00'))
                elif 'id' in session and tool_id == 'claude':
                    if 'path' in session:
                        session_path = Path(session['path'])
                        if session_path.exists():
                            session_time = datetime.fromtimestamp(session_path.stat().st_mtime)
                if session_time and session_time.replace(tzinfo=None) >= cutoff:
                    timeline.append({'tool': tool_id, 'tool_name': tool_data['name'], 'session_id': session.get('id', 'unknown'), 'timestamp': session_time.isoformat() if session_time else None, 'data': session})
            except Exception:
                continue
    timeline.sort(key=lambda x: x['timestamp'] or '', reverse=True)
    return timeline[:50]
```

---

## Feature Function: `get_collector`
**Logic & Purpose:**
```text
Get or create global collector instance.
```

**Parameters:** ``
**Variables Used:** `_collector`
**Implementation:**
```python
def get_collector() -> CLISessionCollector:
    """Get or create global collector instance."""
    global _collector
    if _collector is None:
        _collector = CLISessionCollector()
    return _collector
```

---

## Feature Function: `collect_cli_sessions`
**Logic & Purpose:**
```text
Collect session data from all CLI tools.
```

**Parameters:** ``
**Implementation:**
```python
def collect_cli_sessions() -> Dict[str, Any]:
    """Collect session data from all CLI tools."""
    return get_collector().collect_all()
```

---

## Feature Function: `get_cli_stats`
**Logic & Purpose:**
```text
Get aggregate CLI tool statistics.
```

**Parameters:** ``
**Implementation:**
```python
def get_cli_stats() -> Dict[str, Any]:
    """Get aggregate CLI tool statistics."""
    return get_collector().get_aggregate_stats()
```

---

## Feature Function: `get_cli_timeline`
**Logic & Purpose:**
```text
Get session timeline from CLI tools.
```

**Parameters:** `days`
**Implementation:**
```python
def get_cli_timeline(days: int=7) -> List[Dict[str, Any]]:
    """Get session timeline from CLI tools."""
    return get_collector().get_session_timeline(days)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/prompts/prompt_injector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/prompts/prompt_injector.py`

**Module Overview**: 
```text
Prompt-Injectable Dashboard Modules

These modules format proxy state information that can be injected into
Claude Code's system prompt to give it awareness of:
- Current routing configuration
- Performance metrics
- Token usage patterns
- Cost tracking
- Recent errors

Formats:
- EXPANDED: Multi-line detailed format (10-20 lines)
- SINGLE: One-line compact format (1 line)
- MINI: Ultra-compact partial line (20-40 chars)
```

## Global Presets & Variables
- `prompt_injector` = `PromptInjector()`

## Dependencies & Imports
time, typing.Dict, typing.Any, typing.List, typing.Optional, datetime.datetime, datetime.timedelta

## Feature Class: `PromptDashboardModule`
**Description:**
```text
Base class for prompt-injectable dashboard modules
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.last_update = time.time()
    self.data = {}
```

### Method: `update`
**Logic & Purpose:**
```text
Update module data
```

**Parameters:** `self, data`
**Implementation:**
```python
def update(self, data: Dict[str, Any]):
    """Update module data"""
    self.data = data
    self.last_update = time.time()
```

### Method: `render_expanded`
**Logic & Purpose:**
```text
Multi-line detailed format (10-20 lines)
```

**Parameters:** `self`
**Implementation:**
```python
def render_expanded(self) -> str:
    """Multi-line detailed format (10-20 lines)"""
    raise NotImplementedError
```

### Method: `render_single`
**Logic & Purpose:**
```text
Single-line compact format
```

**Parameters:** `self`
**Implementation:**
```python
def render_single(self) -> str:
    """Single-line compact format"""
    raise NotImplementedError
```

### Method: `render_mini`
**Logic & Purpose:**
```text
Ultra-compact partial line (20-40 chars)
```

**Parameters:** `self`
**Implementation:**
```python
def render_mini(self) -> str:
    """Ultra-compact partial line (20-40 chars)"""
    raise NotImplementedError
```

---

## Feature Class: `ProxyStatusModule`
**Description:**
```text
Proxy status and routing configuration
```

### Method: `render_expanded`
**Logic & Purpose:**
```text
Example output:
╔═══════════════════════════════════════════════════════════╗
║ PROXY STATUS & ROUTING                                    ║
╠═══════════════════════════════════════════════════════════╣
║ Mode: Proxy (server key) / Passthrough (user keys)        ║
║ Provider: OpenRouter (https://openrouter.ai/api/v1)       ║
║ Routing:                                                  ║
║   • BIG (Opus)    → openai/gpt-4o                         ║
║   • MIDDLE (Sonnet) → openai/gpt-4o                       ║
║   • SMALL (Haiku)  → gpt-4o-mini                          ║
║ Reasoning: High effort, 8000 max tokens                   ║
║ Features: Usage tracking ✓ | Compact logger ✗            ║
╚═══════════════════════════════════════════════════════════╝
```

**Parameters:** `self`
**Variables Used:** `track_usage, big, base_url, reasoning_tokens, middle, reasoning, lines, mode, reasoning_str, compact_log, provider, features, small`
**Implementation:**
```python
def render_expanded(self) -> str:
    """
        Example output:
        ╔═══════════════════════════════════════════════════════════╗
        ║ PROXY STATUS & ROUTING                                    ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Mode: Proxy (server key) / Passthrough (user keys)        ║
        ║ Provider: OpenRouter (https://openrouter.ai/api/v1)       ║
        ║ Routing:                                                  ║
        ║   • BIG (Opus)    → openai/gpt-4o                         ║
        ║   • MIDDLE (Sonnet) → openai/gpt-4o                       ║
        ║   • SMALL (Haiku)  → gpt-4o-mini                          ║
        ║ Reasoning: High effort, 8000 max tokens                   ║
        ║ Features: Usage tracking ✓ | Compact logger ✗            ║
        ╚═══════════════════════════════════════════════════════════╝
        """
    mode = self.data.get('passthrough_mode', False)
    provider = self.data.get('provider', 'Unknown')
    base_url = self.data.get('base_url', '')
    big = self.data.get('big_model', '')
    middle = self.data.get('middle_model', '')
    small = self.data.get('small_model', '')
    reasoning = self.data.get('reasoning_effort', '')
    reasoning_tokens = self.data.get('reasoning_max_tokens', '')
    track_usage = self.data.get('track_usage', False)
    compact_log = self.data.get('compact_logger', False)
    lines = ['╔═══════════════════════════════════════════════════════════╗', '║ PROXY STATUS & ROUTING                                    ║', '╠═══════════════════════════════════════════════════════════╣', f"║ Mode: {('Passthrough (user keys)' if mode else 'Proxy (server key)'):51}║", f'║ Provider: {provider:48}║', f'║ Base URL: {base_url[:45]:48}║', '║ Routing:                                                  ║', f'║   • BIG (Opus)      → {big[:38]:38} ║', f'║   • MIDDLE (Sonnet) → {middle[:38]:38} ║', f'║   • SMALL (Haiku)   → {small[:38]:38} ║']
    if reasoning or reasoning_tokens:
        reasoning_str = f"{reasoning or 'N/A'}"
        if reasoning_tokens:
            reasoning_str += f', {reasoning_tokens} max tokens'
        lines.append(f'║ Reasoning: {reasoning_str[:45]:48}║')
    features = []
    if track_usage:
        features.append('Usage tracking ✓')
    else:
        features.append('Usage tracking ✗')
    if compact_log:
        features.append('Compact logger ✓')
    else:
        features.append('Compact logger ✗')
    lines.append(f"║ Features: {' | '.join(features)[:45]:48}║")
    lines.append('╚═══════════════════════════════════════════════════════════╝')
    return '\n'.join(lines)
```

### Method: `render_single`
**Logic & Purpose:**
```text
Example: [Proxy] OpenRouter: O→gpt-4o M→gpt-4o S→gpt-4o-mini | R:high/8k | Track✓ Log✗
```

**Parameters:** `self`
**Variables Used:** `big, middle, reasoning, mode, track, provider, tokens, log, r_str, small`
**Implementation:**
```python
def render_single(self) -> str:
    """
        Example: [Proxy] OpenRouter: O→gpt-4o M→gpt-4o S→gpt-4o-mini | R:high/8k | Track✓ Log✗
        """
    mode = 'Pass' if self.data.get('passthrough_mode') else 'Proxy'
    provider = self.data.get('provider', 'Unknown')
    big = self.data.get('big_model', '')[:15]
    middle = self.data.get('middle_model', '')[:15]
    small = self.data.get('small_model', '')[:15]
    reasoning = self.data.get('reasoning_effort', 'N/A')
    tokens = self.data.get('reasoning_max_tokens', '')
    track = '✓' if self.data.get('track_usage') else '✗'
    log = '✓' if self.data.get('compact_logger') else '✗'
    r_str = f'{reasoning}/{tokens}' if tokens else reasoning
    return f'[{mode}] {provider}: O→{big} M→{middle} S→{small} | R:{r_str} | Track{track} Log{log}'
```

### Method: `render_mini`
**Logic & Purpose:**
```text
Example: Proxy|OR|gpt4o|high
```

**Parameters:** `self`
**Variables Used:** `provider_map, reasoning, mode, provider, model`
**Implementation:**
```python
def render_mini(self) -> str:
    """
        Example: Proxy|OR|gpt4o|high
        """
    mode = 'P' if self.data.get('passthrough_mode') else 'S'
    provider_map = {'OpenRouter': 'OR', 'OpenAI': 'OAI', 'Azure': 'AZ', 'Anthropic': 'ANT', 'Ollama': 'OL'}
    provider = provider_map.get(self.data.get('provider', ''), 'XX')
    model = self.data.get('big_model', '')[:8]
    reasoning = (self.data.get('reasoning_effort', '') or 'N')[:1]
    return f'{mode}|{provider}|{model}|{reasoning}'
```

---

## Feature Class: `PerformanceModule`
**Description:**
```text
Performance metrics and token usage
```

### Method: `render_expanded`
**Logic & Purpose:**
```text
Example:
╔═══════════════════════════════════════════════════════════╗
║ PERFORMANCE METRICS (Last 10 Requests)                    ║
╠═══════════════════════════════════════════════════════════╣
║ Requests: 847 total (94 today)                            ║
║ Latency:  3,421ms avg | 1,234ms min | 8,765ms max        ║
║ Speed:    78 tok/s avg | 234 tok/s max                    ║
║ Tokens:                                                   ║
║   • Input:    2,145,678 (avg: 2,534/req)                 ║
║   • Output:     456,789 (avg: 539/req)                   ║
║   • Thinking:    12,345 (avg: 15/req)                    ║
║ Context: 43.7k/200k avg (22% utilization)                ║
║ Cost: $12.34 total | $2.47 today | $0.015 avg/req        ║
╚═══════════════════════════════════════════════════════════╝
```

**Parameters:** `self`
**Variables Used:** `total_cost, avg_output, today_cost, input_tok, lines, avg_speed, output_tok, max_lat, today_req, ctx_pct, think_tok, total_req, avg_cost, avg_ctx, avg_input, avg_lat, ctx_limit, max_speed, avg_think, min_lat`
**Implementation:**
```python
def render_expanded(self) -> str:
    """
        Example:
        ╔═══════════════════════════════════════════════════════════╗
        ║ PERFORMANCE METRICS (Last 10 Requests)                    ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Requests: 847 total (94 today)                            ║
        ║ Latency:  3,421ms avg | 1,234ms min | 8,765ms max        ║
        ║ Speed:    78 tok/s avg | 234 tok/s max                    ║
        ║ Tokens:                                                   ║
        ║   • Input:    2,145,678 (avg: 2,534/req)                 ║
        ║   • Output:     456,789 (avg: 539/req)                   ║
        ║   • Thinking:    12,345 (avg: 15/req)                    ║
        ║ Context: 43.7k/200k avg (22% utilization)                ║
        ║ Cost: $12.34 total | $2.47 today | $0.015 avg/req        ║
        ╚═══════════════════════════════════════════════════════════╝
        """
    total_req = self.data.get('total_requests', 0)
    today_req = self.data.get('today_requests', 0)
    avg_lat = self.data.get('avg_latency_ms', 0)
    min_lat = self.data.get('min_latency_ms', 0)
    max_lat = self.data.get('max_latency_ms', 0)
    avg_speed = self.data.get('avg_tokens_per_sec', 0)
    max_speed = self.data.get('max_tokens_per_sec', 0)
    input_tok = self.data.get('total_input_tokens', 0)
    output_tok = self.data.get('total_output_tokens', 0)
    think_tok = self.data.get('total_thinking_tokens', 0)
    avg_input = self.data.get('avg_input_tokens', 0)
    avg_output = self.data.get('avg_output_tokens', 0)
    avg_think = self.data.get('avg_thinking_tokens', 0)
    avg_ctx = self.data.get('avg_context_tokens', 0)
    ctx_limit = self.data.get('avg_context_limit', 200000)
    ctx_pct = int(avg_ctx / ctx_limit * 100) if ctx_limit else 0
    total_cost = self.data.get('total_cost', 0)
    today_cost = self.data.get('today_cost', 0)
    avg_cost = self.data.get('avg_cost_per_request', 0)
    lines = ['╔═══════════════════════════════════════════════════════════╗', '║ PERFORMANCE METRICS (Last 10 Requests)                    ║', '╠═══════════════════════════════════════════════════════════╣', f"║ Requests: {total_req:,} total ({today_req} today){' ' * (24 - len(str(total_req)) - len(str(today_req)))}║", f"║ Latency:  {avg_lat:,}ms avg | {min_lat:,}ms min | {max_lat:,}ms max{' ' * (11 - len(f'{avg_lat:,}') - len(f'{min_lat:,}') - len(f'{max_lat:,}'))}║", f"║ Speed:    {avg_speed} tok/s avg | {max_speed} tok/s max{' ' * (19 - len(str(avg_speed)) - len(str(max_speed)))}║", '║ Tokens:                                                   ║', f"║   • Input:    {input_tok:,} (avg: {avg_input:,}/req){' ' * (21 - len(f'{input_tok:,}') - len(f'{avg_input:,}'))}║", f"║   • Output:   {output_tok:,} (avg: {avg_output:,}/req){' ' * (20 - len(f'{output_tok:,}') - len(f'{avg_output:,}'))}║", f"║   • Thinking: {think_tok:,} (avg: {avg_think:,}/req){' ' * (18 - len(f'{think_tok:,}') - len(f'{avg_think:,}'))}║", f"║ Context: {avg_ctx / 1000:.1f}k/{ctx_limit / 1000:.0f}k avg ({ctx_pct}% utilization){' ' * (15 - len(str(ctx_pct)))}║", f"║ Cost: ${total_cost:.2f} total | ${today_cost:.2f} today | ${avg_cost:.4f} avg/req{' ' * (5 - len(f'{avg_cost:.4f}'))}║", '╚═══════════════════════════════════════════════════════════╝']
    return '\n'.join(lines)
```

### Method: `render_single`
**Logic & Purpose:**
```text
Example: Perf: 847req 3.4s⌀ 78t/s | Tok: 2.1M→456k💭12k | Ctx:44k/200k(22%) | Cost:$12.34
```

**Parameters:** `self`
**Variables Used:** `output_tok, total_cost, ctx_limit, input_tok, avg_ctx, ctx_pct, think_tok, total_req, avg_speed, avg_lat`
**Implementation:**
```python
def render_single(self) -> str:
    """
        Example: Perf: 847req 3.4s⌀ 78t/s | Tok: 2.1M→456k💭12k | Ctx:44k/200k(22%) | Cost:$12.34
        """
    total_req = self.data.get('total_requests', 0)
    avg_lat = self.data.get('avg_latency_ms', 0) / 1000
    avg_speed = self.data.get('avg_tokens_per_sec', 0)
    input_tok = self.data.get('total_input_tokens', 0)
    output_tok = self.data.get('total_output_tokens', 0)
    think_tok = self.data.get('total_thinking_tokens', 0)
    avg_ctx = self.data.get('avg_context_tokens', 0)
    ctx_limit = self.data.get('avg_context_limit', 200000)
    ctx_pct = int(avg_ctx / ctx_limit * 100) if ctx_limit else 0
    total_cost = self.data.get('total_cost', 0)
    return f'Perf: {total_req}req {avg_lat:.1f}s⌀ {avg_speed}t/s | Tok: {input_tok / 1000:.1f}k→{output_tok / 1000:.1f}k💭{think_tok / 1000:.1f}k | Ctx:{avg_ctx / 1000:.0f}k/{ctx_limit / 1000:.0f}k({ctx_pct}%) | Cost:${total_cost:.2f}'
```

### Method: `render_mini`
**Logic & Purpose:**
```text
Example: 847r|3.4s|78t/s|$12
```

**Parameters:** `self`
**Variables Used:** `total_req, total_cost, avg_speed, avg_lat`
**Implementation:**
```python
def render_mini(self) -> str:
    """
        Example: 847r|3.4s|78t/s|$12
        """
    total_req = self.data.get('total_requests', 0)
    avg_lat = self.data.get('avg_latency_ms', 0) / 1000
    avg_speed = self.data.get('avg_tokens_per_sec', 0)
    total_cost = self.data.get('total_cost', 0)
    return f'{total_req}r|{avg_lat:.1f}s|{avg_speed}t/s|${total_cost:.0f}'
```

---

## Feature Class: `ErrorTrackerModule`
**Description:**
```text
Error tracking and recent issues
```

### Method: `render_expanded`
**Logic & Purpose:**
```text
Example:
╔═══════════════════════════════════════════════════════════╗
║ ERROR TRACKING (Last 24 Hours)                            ║
╠═══════════════════════════════════════════════════════════╣
║ Success Rate: 98.7% (847/859 requests)                    ║
║ Errors: 12 total                                          ║
║   • Rate Limit:     7 (58%)                               ║
║   • Invalid Key:    3 (25%)                               ║
║   • Model Not Found: 2 (17%)                              ║
║                                                           ║
║ Recent Errors:                                            ║
║   [14:23] Rate limit exceeded (openai/gpt-4o)             ║
║   [14:18] Invalid API key (anthropic/claude-3.5-sonnet)   ║
║   [14:05] Model not found (fake/model-123)                ║
╚═══════════════════════════════════════════════════════════╝
```

**Parameters:** `self`
**Variables Used:** `error_types, total_count, success_count, recent_errors, timestamp, message, lines, pct, error_count, success_rate, model`
**Implementation:**
```python
def render_expanded(self) -> str:
    """
        Example:
        ╔═══════════════════════════════════════════════════════════╗
        ║ ERROR TRACKING (Last 24 Hours)                            ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Success Rate: 98.7% (847/859 requests)                    ║
        ║ Errors: 12 total                                          ║
        ║   • Rate Limit:     7 (58%)                               ║
        ║   • Invalid Key:    3 (25%)                               ║
        ║   • Model Not Found: 2 (17%)                              ║
        ║                                                           ║
        ║ Recent Errors:                                            ║
        ║   [14:23] Rate limit exceeded (openai/gpt-4o)             ║
        ║   [14:18] Invalid API key (anthropic/claude-3.5-sonnet)   ║
        ║   [14:05] Model not found (fake/model-123)                ║
        ╚═══════════════════════════════════════════════════════════╝
        """
    success_count = self.data.get('success_count', 0)
    total_count = self.data.get('total_count', 0)
    error_count = total_count - success_count
    success_rate = success_count / total_count * 100 if total_count else 100
    error_types = self.data.get('error_types', {})
    recent_errors = self.data.get('recent_errors', [])
    lines = ['╔═══════════════════════════════════════════════════════════╗', '║ ERROR TRACKING (Last 24 Hours)                            ║', '╠═══════════════════════════════════════════════════════════╣', f"║ Success Rate: {success_rate:.1f}% ({success_count}/{total_count} requests){' ' * (17 - len(str(success_count)) - len(str(total_count)))}║", f"║ Errors: {error_count} total{' ' * (43 - len(str(error_count)))}║"]
    if error_types:
        for error_type, count in sorted(error_types.items(), key=lambda x: -x[1])[:3]:
            pct = int(count / error_count * 100) if error_count else 0
            lines.append(f"║   • {error_type[:20]:20} {count:3} ({pct}%){' ' * (14 - len(str(count)) - len(str(pct)))}║")
    lines.append('║                                                           ║')
    lines.append('║ Recent Errors:                                            ║')
    for error in recent_errors[:3]:
        timestamp = error.get('time', '')[:5]
        message = error.get('message', '')[:44]
        model = error.get('model', '')
        if model:
            message = f'{message[:30]} ({model[:10]})'
        lines.append(f'║   [{timestamp}] {message:48}║')
    lines.append('╚═══════════════════════════════════════════════════════════╝')
    return '\n'.join(lines)
```

### Method: `render_single`
**Logic & Purpose:**
```text
Example: Errors: 12/859 (98.7% OK) | RateLimit:7 InvalidKey:3 NotFound:2 | Last:[14:23]RateLimit
```

**Parameters:** `self`
**Variables Used:** `error_types, total_count, success_count, recent_errors, last_error, error_str, last, error_count, success_rate`
**Implementation:**
```python
def render_single(self) -> str:
    """
        Example: Errors: 12/859 (98.7% OK) | RateLimit:7 InvalidKey:3 NotFound:2 | Last:[14:23]RateLimit
        """
    success_count = self.data.get('success_count', 0)
    total_count = self.data.get('total_count', 0)
    error_count = total_count - success_count
    success_rate = success_count / total_count * 100 if total_count else 100
    error_types = self.data.get('error_types', {})
    recent_errors = self.data.get('recent_errors', [])
    error_str = ' '.join([f'{k}:{v}' for k, v in sorted(error_types.items(), key=lambda x: -x[1])[:3]])
    last_error = ''
    if recent_errors:
        last = recent_errors[0]
        last_error = f" | Last:[{last.get('time', '')[:5]}]{last.get('type', '')}"
    return f'Errors: {error_count}/{total_count} ({success_rate:.1f}% OK) | {error_str}{last_error}'
```

### Method: `render_mini`
**Logic & Purpose:**
```text
Example: 12err|98.7%OK
```

**Parameters:** `self`
**Variables Used:** `success_count, success_rate, error_count, total_count`
**Implementation:**
```python
def render_mini(self) -> str:
    """
        Example: 12err|98.7%OK
        """
    success_count = self.data.get('success_count', 0)
    total_count = self.data.get('total_count', 0)
    error_count = total_count - success_count
    success_rate = success_count / total_count * 100 if total_count else 100
    return f'{error_count}err|{success_rate:.1f}%OK'
```

---

## Feature Class: `ModelUsageModule`
**Description:**
```text
Model usage patterns and recommendations
```

### Method: `render_expanded`
**Logic & Purpose:**
```text
Example:
╔═══════════════════════════════════════════════════════════╗
║ MODEL USAGE PATTERNS (Last 7 Days)                        ║
╠═══════════════════════════════════════════════════════════╣
║ Top Models by Request Count:                              ║
║   #1  openai/gpt-4o           245 req  125.3k tok  $1.45  ║
║   #2  anthropic/claude-3.5... 89 req   52.1k tok   $0.89  ║
║   #3  ollama/qwen2.5:72b       34 req   18.9k tok   FREE  ║
║                                                           ║
║ Usage by Type:                                            ║
║   • Text-only:  312 req (82%)                             ║
║   • With tools:  45 req (12%)                             ║
║   • With images: 23 req (6%)                              ║
║                                                           ║
║ Recommendations:                                          ║
║   💡 34 requests to FREE model (saved $0.45)              ║
║   💡 Consider: qwen/qwen-2.5-thinking for reasoning tasks ║
╚═══════════════════════════════════════════════════════════╝
```

**Parameters:** `self`
**Variables Used:** `usage_by_type, tok, cost, cost_str, req, lines, with_images, recommendations, text_only, total, with_tools, top_models, name`
**Implementation:**
```python
def render_expanded(self) -> str:
    """
        Example:
        ╔═══════════════════════════════════════════════════════════╗
        ║ MODEL USAGE PATTERNS (Last 7 Days)                        ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Top Models by Request Count:                              ║
        ║   #1  openai/gpt-4o           245 req  125.3k tok  $1.45  ║
        ║   #2  anthropic/claude-3.5... 89 req   52.1k tok   $0.89  ║
        ║   #3  ollama/qwen2.5:72b       34 req   18.9k tok   FREE  ║
        ║                                                           ║
        ║ Usage by Type:                                            ║
        ║   • Text-only:  312 req (82%)                             ║
        ║   • With tools:  45 req (12%)                             ║
        ║   • With images: 23 req (6%)                              ║
        ║                                                           ║
        ║ Recommendations:                                          ║
        ║   💡 34 requests to FREE model (saved $0.45)              ║
        ║   💡 Consider: qwen/qwen-2.5-thinking for reasoning tasks ║
        ╚═══════════════════════════════════════════════════════════╝
        """
    top_models = self.data.get('top_models', [])
    usage_by_type = self.data.get('usage_by_type', {})
    recommendations = self.data.get('recommendations', [])
    lines = ['╔═══════════════════════════════════════════════════════════╗', '║ MODEL USAGE PATTERNS (Last 7 Days)                        ║', '╠═══════════════════════════════════════════════════════════╣', '║ Top Models by Request Count:                              ║']
    for i, model in enumerate(top_models[:3], 1):
        name = model.get('name', '')[:25]
        req = model.get('requests', 0)
        tok = model.get('tokens', 0) / 1000
        cost = model.get('cost', 0)
        cost_str = 'FREE' if cost == 0 else f'${cost:.2f}'
        lines.append(f'║   #{i}  {name:25} {req:3} req  {tok:5.1f}k tok  {cost_str:5} ║')
    lines.append('║                                                           ║')
    lines.append('║ Usage by Type:                                            ║')
    text_only = usage_by_type.get('text_only', 0)
    with_tools = usage_by_type.get('with_tools', 0)
    with_images = usage_by_type.get('with_images', 0)
    total = text_only + with_tools + with_images
    if total:
        lines.append(f"║   • Text-only:  {text_only:3} req ({text_only / total * 100:.0f}%){' ' * 29}║")
        lines.append(f"║   • With tools:  {with_tools:2} req ({with_tools / total * 100:.0f}%){' ' * 30}║")
        lines.append(f"║   • With images: {with_images:2} req ({with_images / total * 100:.0f}%){' ' * 29}║")
    if recommendations:
        lines.append('║                                                           ║')
        lines.append('║ Recommendations:                                          ║')
        for rec in recommendations[:2]:
            lines.append(f'║   💡 {rec[:53]:53}║')
    lines.append('╚═══════════════════════════════════════════════════════════╝')
    return '\n'.join(lines)
```

### Method: `render_single`
**Logic & Purpose:**
```text
Example: Models: gpt-4o:245 claude:89 qwen:34 | Text:82% Tools:12% Img:6% | 34→FREE saved $0.45
```

**Parameters:** `self`
**Variables Used:** `type_str, usage_by_type, savings_str, model_str, with_images, savings, text_only, total, with_tools, free_count, top_models`
**Implementation:**
```python
def render_single(self) -> str:
    """
        Example: Models: gpt-4o:245 claude:89 qwen:34 | Text:82% Tools:12% Img:6% | 34→FREE saved $0.45
        """
    top_models = self.data.get('top_models', [])
    usage_by_type = self.data.get('usage_by_type', {})
    model_str = ' '.join([f"{m.get('name', '')[:8]}:{m.get('requests', 0)}" for m in top_models[:3]])
    text_only = usage_by_type.get('text_only', 0)
    with_tools = usage_by_type.get('with_tools', 0)
    with_images = usage_by_type.get('with_images', 0)
    total = text_only + with_tools + with_images
    type_str = ''
    if total:
        type_str = f' | Text:{text_only / total * 100:.0f}% Tools:{with_tools / total * 100:.0f}% Img:{with_images / total * 100:.0f}%'
    free_count = sum((1 for m in top_models if m.get('cost', 0) == 0))
    savings = self.data.get('free_savings', 0)
    savings_str = f' | {free_count}→FREE saved ${savings:.2f}' if free_count else ''
    return f'Models: {model_str}{type_str}{savings_str}'
```

### Method: `render_mini`
**Logic & Purpose:**
```text
Example: gpt4o:245|34free
```

**Parameters:** `self`
**Variables Used:** `top_model, req, free_count, top_models, name`
**Implementation:**
```python
def render_mini(self) -> str:
    """
        Example: gpt4o:245|34free
        """
    top_models = self.data.get('top_models', [])
    free_count = sum((1 for m in top_models if m.get('cost', 0) == 0))
    top_model = top_models[0] if top_models else {}
    name = top_model.get('name', '')[:8]
    req = top_model.get('requests', 0)
    return f'{name}:{req}|{free_count}free'
```

---

## Feature Class: `PromptInjector`
**Description:**
```text
Utility to inject dashboard modules into Claude Code prompts
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.modules = {'status': ProxyStatusModule(), 'performance': PerformanceModule(), 'errors': ErrorTrackerModule(), 'models': ModelUsageModule()}
```

### Method: `update_all`
**Logic & Purpose:**
```text
Update all modules with new data
```

**Parameters:** `self, data`
**Implementation:**
```python
def update_all(self, data: Dict[str, Dict[str, Any]]):
    """Update all modules with new data"""
    for module_name, module_data in data.items():
        if module_name in self.modules:
            self.modules[module_name].update(module_data)
```

### Method: `generate_prompt_context`
**Logic & Purpose:**
```text
Generate prompt context to inject into Claude Code system prompt.

Args:
    format: 'expanded', 'single', or 'mini'
    modules: List of module names to include (default: all)

Returns:
    Formatted string ready for prompt injection
```

**Parameters:** `self, format, modules`
**Variables Used:** `lines, modules, module`
**Implementation:**
```python
def generate_prompt_context(self, format: str='single', modules: Optional[List[str]]=None) -> str:
    """
        Generate prompt context to inject into Claude Code system prompt.

        Args:
            format: 'expanded', 'single', or 'mini'
            modules: List of module names to include (default: all)

        Returns:
            Formatted string ready for prompt injection
        """
    if modules is None:
        modules = list(self.modules.keys())
    lines = []
    lines.append('═' * 60)
    lines.append('PROXY STATUS INFORMATION')
    lines.append('(This information is from the Claude Code Proxy layer)')
    lines.append('═' * 60)
    lines.append('')
    for module_name in modules:
        if module_name not in self.modules:
            continue
        module = self.modules[module_name]
        if format == 'expanded':
            lines.append(module.render_expanded())
        elif format == 'single':
            lines.append(module.render_single())
        elif format == 'mini':
            lines.append(module.render_mini())
        if format in ['single', 'mini']:
            lines.append('')
    lines.append('═' * 60)
    return '\n'.join(lines)
```

### Method: `generate_compact_header`
**Logic & Purpose:**
```text
Generate ultra-compact header for every prompt.

Example:
[P|OR|gpt4o|h] 847r|3.4s|78t/s|$12 | 12err|98.7%OK | gpt4o:245|34free
```

**Parameters:** `self`
**Variables Used:** `parts`
**Implementation:**
```python
def generate_compact_header(self) -> str:
    """
        Generate ultra-compact header for every prompt.

        Example:
        [P|OR|gpt4o|h] 847r|3.4s|78t/s|$12 | 12err|98.7%OK | gpt4o:245|34free
        """
    parts = [self.modules['status'].render_mini(), self.modules['performance'].render_mini(), self.modules['errors'].render_mini(), self.modules['models'].render_mini()]
    return ' | '.join(parts)
```

---


