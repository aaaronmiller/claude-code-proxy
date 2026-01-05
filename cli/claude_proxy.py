#!/usr/bin/env python3
"""
Claude Proxy CLI Tool - Phase 4

Command-line interface for interacting with the Claude Proxy analytics platform.

Features:
- Authentication and API key management
- Query analytics data
- Generate reports
- Manage alerts
- Predictive analytics
- Integration with CI/CD

Author: AI Architect
Date: 2026-01-05

Usage:
    claude-proxy analytics --start 2026-01-01 --end 2026-01-05
    claude-proxy alerts list
    claude-proxy report generate --template weekly --format pdf
    claude-proxy predictive forecast --days 7
    claude-proxy auth login --api-key your_key_here
"""

import argparse
import json
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
from pathlib import Path
import csv


class ClaudeProxyClient:
    """Python SDK for Claude Proxy API"""

    def __init__(self, base_url: str = "http://localhost:8082", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"Authorization": api_key})

    def set_api_key(self, api_key: str):
        """Set API key for authentication"""
        self.api_key = api_key
        self.session.headers["Authorization"] = api_key

    # ==================== Analytics ====================

    def get_analytics(
        self,
        start_date: str,
        end_date: str,
        metric: str = "tokens",
        group_by: str = "day"
    ) -> Dict[str, Any]:
        """Get analytics data"""
        params = {
            "metric": metric,
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by
        }
        response = self.session.get(f"{self.base_url}/api/analytics/timeseries", params=params)
        response.raise_for_status()
        return response.json()

    def get_custom_query(self, metrics: str, start_date: str, end_date: str, **kwargs) -> Dict[str, Any]:
        """Execute custom query"""
        params = {
            "metrics": metrics,
            "start_date": start_date,
            "end_date": end_date,
            **kwargs
        }
        response = self.session.get(f"{self.base_url}/api/analytics/custom", params=params)
        response.raise_for_status()
        return response.json()

    def get_aggregate_stats(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get aggregate statistics"""
        params = {"start_date": start_date, "end_date": end_date}
        response = self.session.get(f"{self.base_url}/api/analytics/aggregate", params=params)
        response.raise_for_status()
        return response.json()

    # ==================== Predictive ====================

    def get_predictions(self, days: int = 7) -> Dict[str, Any]:
        """Get predictive forecast"""
        params = {"days": days}
        response = self.session.get(f"{self.base_url}/api/predictive/forecast", params=params)
        response.raise_for_status()
        return response.json()

    def get_smart_thresholds(self, metric: str) -> Dict[str, Any]:
        """Get smart thresholds"""
        params = {"metric": metric}
        response = self.session.get(f"{self.base_url}/api/predictive/thresholds", params=params)
        response.raise_for_status()
        return response.json()

    def detect_anomaly(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if request is anomalous"""
        response = self.session.post(
            f"{self.base_url}/api/predictive/detect-anomaly",
            json=request_data
        )
        response.raise_for_status()
        return response.json()

    # ==================== Alerts ====================

    def list_alerts(self) -> Dict[str, Any]:
        """List all alert rules"""
        response = self.session.get(f"{self.base_url}/api/alerts/rules")
        response.raise_for_status()
        return response.json()

    def create_alert(self, name: str, condition: Dict[str, Any], priority: int = 2) -> Dict[str, Any]:
        """Create alert rule"""
        payload = {
            "name": name,
            "description": f"CLI created alert: {name}",
            "condition_json": json.dumps(condition),
            "priority": priority
        }
        response = self.session.post(f"{self.base_url}/api/alerts/rules", json=payload)
        response.raise_for_status()
        return response.json()

    def get_alert_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get alert history"""
        params = {"limit": limit}
        response = self.session.get(f"{self.base_url}/api/alerts/history", params=params)
        response.raise_for_status()
        return response.json()

    # ==================== Reports ====================

    def list_templates(self) -> Dict[str, Any]:
        """List report templates"""
        response = self.session.get(f"{self.base_url}/api/reports/templates")
        response.raise_for_status()
        return response.json()

    def generate_report(self, template_id: str, start_date: str, end_date: str, format_type: str = "excel") -> Dict[str, Any]:
        """Generate report"""
        payload = {
            "template_id": template_id,
            "start_date": start_date,
            "end_date": end_date,
            "format": format_type
        }
        response = self.session.post(f"{self.base_url}/api/reports/generate", json=payload)
        response.raise_for_status()
        return response.json()

    def get_scheduled_reports(self) -> Dict[str, Any]:
        """Get scheduled reports"""
        response = self.session.get(f"{self.base_url}/api/reports/schedule")
        response.raise_for_status()
        return response.json()

    # ==================== Integrations ====================

    def list_integrations(self) -> Dict[str, Any]:
        """List integrations"""
        response = self.session.get(f"{self.base_url}/api/integrations")
        response.raise_for_status()
        return response.json()

    def test_integration(self, name: str) -> Dict[str, Any]:
        """Test integration"""
        response = self.session.post(f"{self.base_url}/api/integrations/{name}/test")
        response.raise_for_status()
        return response.json()

    # ==================== Auth & API Keys ====================

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and get session token"""
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def create_api_key(self, name: str, permissions: list) -> Dict[str, Any]:
        """Create API key"""
        response = self.session.post(
            f"{self.base_url}/api/api-keys",
            json={"name": name, "permissions": permissions}
        )
        response.raise_for_status()
        return response.json()

    def list_api_keys(self) -> Dict[str, Any]:
        """List API keys"""
        response = self.session.get(f"{self.base_url}/api/api-keys")
        response.raise_for_status()
        return response.json()

    # ==================== GraphQL ====================

    def graphql_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        response = self.session.post(f"{self.base_url}/graphql", json=payload)
        response.raise_for_status()
        return response.json()


# ==================== CLI Commands ====================

def config_command(args):
    """Configure CLI settings"""
    config_dir = Path.home() / ".claude_proxy"
    config_file = config_dir / "config.json"

    if args.action == "set":
        config = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)

        config[args.key] = args.value
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Set {args.key} = {args.value}")

    elif args.action == "get":
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(config.get(args.key, ""))
        else:
            print("")

    elif args.action == "show":
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(json.dumps(config, indent=2))
        else:
            print("No configuration found")


def analytics_command(client, args):
    """Query analytics data"""
    try:
        start_date = args.start
        end_date = args.end

        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if args.custom:
            metrics = args.metrics or "tokens,cost,requests"
            result = client.get_custom_query(
                metrics=metrics,
                start_date=start_date,
                end_date=end_date,
                group_by=args.group_by
            )
        else:
            metric = args.metric or "tokens"
            result = client.get_analytics(start_date, end_date, metric, args.group_by)

        print(json.dumps(result, indent=2))

        if args.export:
            # Export to CSV
            if "data" in result and result["data"]:
                with open(args.export, 'w', newline='') as f:
                    if isinstance(result["data"], list) and result["data"]:
                        writer = csv.DictWriter(f, fieldnames=result["data"][0].keys())
                        writer.writeheader()
                        writer.writerows(result["data"])
                print(f"📊 Exported to {args.export}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def predictive_command(client, args):
    """Get predictive analytics"""
    try:
        if args.action == "forecast":
            result = client.get_predictions(args.days)
            print(json.dumps(result, indent=2))

        elif args.action == "thresholds":
            metric = args.metric or "cost"
            result = client.get_smart_thresholds(metric)
            print(json.dumps(result, indent=2))

        elif args.action == "detect":
            if not args.data:
                print("❌ --data required for anomaly detection")
                return
            data = json.loads(args.data)
            result = client.detect_anomaly(data)
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")


def alerts_command(client, args):
    """Manage alerts"""
    try:
        if args.action == "list":
            result = client.list_alerts()
            print(json.dumps(result, indent=2))

        elif args.action == "create":
            # Parse condition from string like "cost>100"
            condition = {"metric": "cost", "operator": ">", "threshold": 100}
            if args.condition:
                parts = args.condition.split(">")
                if len(parts) == 2:
                    condition = {"metric": parts[0], "operator": ">", "threshold": float(parts[1])}

            result = client.create_alert(args.name, condition, args.priority)
            print(json.dumps(result, indent=2))

        elif args.action == "history":
            result = client.get_alert_history(args.limit)
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")


def reports_command(client, args):
    """Manage reports"""
    try:
        if args.action == "templates":
            result = client.list_templates()
            print(json.dumps(result, indent=2))

        elif args.action == "generate":
            result = client.generate_report(
                args.template,
                args.start,
                args.end,
                args.format
            )
            print(json.dumps(result, indent=2))

            if result.get("data") and args.output:
                # Decode hex data if provided
                try:
                    import binascii
                    data = binascii.unhexlify(result["data"])
                    with open(args.output, 'wb') as f:
                        f.write(data)
                    print(f"📄 Report saved to {args.output}")
                except:
                    print("⚠️ Could not decode report data")

        elif args.action == "schedule":
            result = client.get_scheduled_reports()
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")


def integrations_command(client, args):
    """Manage integrations"""
    try:
        if args.action == "list":
            result = client.list_integrations()
            print(json.dumps(result, indent=2))

        elif args.action == "test":
            result = client.test_integration(args.name)
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")


def auth_command(client, args):
    """Authentication"""
    try:
        if args.action == "login":
            if args.api_key:
                # Set API key
                config_dir = Path.home() / ".claude_proxy"
                config_file = config_dir / "config.json"
                config_dir.mkdir(parents=True, exist_ok=True)

                config = {}
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)

                config["api_key"] = args.api_key
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)

                print("✅ API key saved to config")

            elif args.username and args.password:
                result = client.login(args.username, args.password)
                print(json.dumps(result, indent=2))

        elif args.action == "keys":
            if args.create:
                permissions = ["analytics:view", "alerts:view"]
                result = client.create_api_key(args.create, permissions)
                print(json.dumps(result, indent=2))
            else:
                result = client.list_api_keys()
                print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")


def graphql_command(client, args):
    """Execute GraphQL query"""
    try:
        query = args.query or """
        query {
            health
            metrics(startDate: "2026-01-01", endDate: "2026-01-05", groupBy: "day") {
                timestamp
                tokens
                cost
                requests
            }
        }
        """

        result = client.graphql_query(query)
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Proxy CLI - Analytics and Monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-proxy analytics --start 2026-01-01 --end 2026-01-05
  claude-proxy predictive forecast --days 7
  claude-proxy alerts list
  claude-proxy auth login --api-key cp_xxx
  claude-proxy graphql --query '{ health }'
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Config command
    config_parser = subparsers.add_parser("config", help="Configure CLI")
    config_parser.add_argument("action", choices=["set", "get", "show"], help="Action")
    config_parser.add_argument("key", nargs="?", help="Config key")
    config_parser.add_argument("value", nargs="?", help="Config value")

    # Analytics command
    analytics_parser = subparsers.add_parser("analytics", help="Query analytics")
    analytics_parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    analytics_parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    analytics_parser.add_argument("--metric", help="Metric (tokens, cost, requests)")
    analytics_parser.add_argument("--group-by", default="day", choices=["hour", "day", "week"])
    analytics_parser.add_argument("--custom", action="store_true", help="Use custom query")
    analytics_parser.add_argument("--metrics", help="Metrics for custom query (comma-separated)")
    analytics_parser.add_argument("--export", help="Export to CSV file")

    # Predictive command
    predictive_parser = subparsers.add_parser("predictive", help="Predictive analytics")
    predictive_parser.add_argument("action", choices=["forecast", "thresholds", "detect"])
    predictive_parser.add_argument("--days", type=int, default=7, help="Days to forecast")
    predictive_parser.add_argument("--metric", help="Metric for thresholds")
    predictive_parser.add_argument("--data", help="JSON data for anomaly detection")

    # Alerts command
    alerts_parser = subparsers.add_parser("alerts", help="Manage alerts")
    alerts_parser.add_argument("action", choices=["list", "create", "history"])
    alerts_parser.add_argument("--name", help="Alert name")
    alerts_parser.add_argument("--condition", help="Condition (e.g., cost>100)")
    alerts_parser.add_argument("--priority", type=int, default=2, help="Priority 0-3")
    alerts_parser.add_argument("--limit", type=int, default=50, help="History limit")

    # Reports command
    reports_parser = subparsers.add_parser("reports", help="Manage reports")
    reports_parser.add_argument("action", choices=["templates", "generate", "schedule"])
    reports_parser.add_argument("--template", help="Template ID")
    reports_parser.add_argument("--start", help="Start date")
    reports_parser.add_argument("--end", help="End date")
    reports_parser.add_argument("--format", default="excel", choices=["pdf", "excel", "csv"])
    reports_parser.add_argument("--output", help="Output file")

    # Integrations command
    integrations_parser = subparsers.add_parser("integrations", help="Manage integrations")
    integrations_parser.add_argument("action", choices=["list", "test"])
    integrations_parser.add_argument("--name", help="Integration name")

    # Auth command
    auth_parser = subparsers.add_parser("auth", help="Authentication")
    auth_parser.add_argument("action", choices=["login", "keys"])
    auth_parser.add_argument("--username", help="Username")
    auth_parser.add_argument("--password", help="Password")
    auth_parser.add_argument("--api-key", help="API key")
    auth_parser.add_argument("--create", help="Create API key with name")

    # GraphQL command
    graphql_parser = subparsers.add_parser("graphql", help="GraphQL queries")
    graphql_parser.add_argument("--query", help="GraphQL query string")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load config
    config_file = Path.home() / ".claude_proxy" / "config.json"
    config = {}
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

    base_url = config.get("base_url", "http://localhost:8082")
    api_key = config.get("api_key")

    client = ClaudeProxyClient(base_url, api_key)

    # Route to commands
    if args.command == "config":
        config_command(args)
    elif args.command == "analytics":
        analytics_command(client, args)
    elif args.command == "predictive":
        predictive_command(client, args)
    elif args.command == "alerts":
        alerts_command(client, args)
    elif args.command == "reports":
        reports_command(client, args)
    elif args.command == "integrations":
        integrations_command(client, args)
    elif args.command == "auth":
        auth_command(client, args)
    elif args.command == "graphql":
        graphql_command(client, args)


if __name__ == "__main__":
    main()
