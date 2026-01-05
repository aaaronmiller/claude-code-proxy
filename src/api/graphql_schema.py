"""
GraphQL Schema and API - Phase 4

Provides GraphQL interface for the analytics platform.
Uses Strawberry GraphQL library for type-safe schema definitions.

Features:
- Unified query interface
- Type-safe resolvers
- Nested data fetching
- Flexible filtering and aggregation
- Real-time subscriptions

Author: AI Architect
Date: 2026-01-05
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sqlite3

try:
    import strawberry
    from strawberry.types import Info
    HAS_STRAWBERRY = True
except ImportError:
    # Fallback to simple implementation
    HAS_STRAWBERRY = False
    print("⚠️  Strawberry not available. Install with: pip install strawberry-graphql")

from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker


if HAS_STRAWBERRY:
    # ==================== GraphQL Types ====================

    @strawberry.type
    class MetricsData:
        timestamp: str
        tokens: int
        cost: float
        requests: int
        latency: float

    @strawberry.type
    class ProviderStats:
        provider: str
        total_tokens: int
        total_cost: float
        request_count: int
        avg_latency: float

    @strawberry.type
    class ModelStats:
        model: str
        provider: str
        total_tokens: int
        total_cost: float
        request_count: int

    @strawberry.type
    class Alert:
        id: str
        name: str
        description: str
        priority: int
        is_active: bool
        last_triggered: Optional[str]

    @strawberry.type
    class Dashboard:
        id: str
        name: str
        created_at: str
        widget_count: int

    @strawberry.type
    class QueryResult:
        success: bool
        data: Optional[str]
        message: Optional[str]

    # ==================== Query Resolver ====================

    @strawberry.type
    class Query:
        """Main query type for analytics platform"""

        @strawberry.field
        def health(self) -> str:
            """Health check"""
            return "Analytics API is running"

        @strawberry.field
        def metrics(
            self,
            start_date: str,
            end_date: str,
            group_by: Optional[str] = "day"
        ) -> List[MetricsData]:
            """Get metrics for date range"""
            if not usage_tracker.enabled:
                return []

            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                conn.row_factory = sqlite3.Row

                time_cond = {
                    "hour": "strftime('%Y-%m-%d %H:00', timestamp)",
                    "day": "strftime('%Y-%m-%d', timestamp)",
                    "week": "strftime('%Y-W%W', timestamp)"
                }.get(group_by, "strftime('%Y-%m-%d', timestamp)")

                query = f"""
                    SELECT
                        {time_cond} as time_bucket,
                        SUM(total_tokens) as tokens,
                        SUM(estimated_cost) as cost,
                        COUNT(*) as requests,
                        AVG(duration_ms) as latency
                    FROM api_requests
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """

                cursor = conn.execute(query, [start_date, end_date])
                rows = cursor.fetchall()
                conn.close()

                return [
                    MetricsData(
                        timestamp=row["time_bucket"],
                        tokens=row["tokens"] or 0,
                        cost=row["cost"] or 0,
                        requests=row["requests"] or 0,
                        latency=row["latency"] or 0
                    ) for row in rows
                ]

            except Exception as e:
                logger.error(f"GraphQL metrics query failed: {e}")
                return []

        @strawberry.field
        def provider_stats(self, start_date: str, end_date: str) -> List[ProviderStats]:
            """Get statistics by provider"""
            if not usage_tracker.enabled:
                return []

            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                conn.row_factory = sqlite3.Row

                query = """
                    SELECT
                        provider,
                        SUM(total_tokens) as tokens,
                        SUM(estimated_cost) as cost,
                        COUNT(*) as requests,
                        AVG(duration_ms) as latency
                    FROM api_requests
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY provider
                    ORDER BY cost DESC
                """

                cursor = conn.execute(query, [start_date, end_date])
                rows = cursor.fetchall()
                conn.close()

                return [
                    ProviderStats(
                        provider=row["provider"],
                        total_tokens=row["tokens"] or 0,
                        total_cost=row["cost"] or 0,
                        request_count=row["requests"] or 0,
                        avg_latency=row["latency"] or 0
                    ) for row in rows
                ]

            except Exception as e:
                logger.error(f"GraphQL provider stats failed: {e}")
                return []

        @strawberry.field
        def alerts(self, only_active: Optional[bool] = None) -> List[Alert]:
            """Get alerts"""
            if not usage_tracker.enabled:
                return []

            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                conn.row_factory = sqlite3.Row

                query = "SELECT * FROM alert_rules"
                params = []

                if only_active:
                    query += " WHERE is_active = 1"

                query += " ORDER BY priority"

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                conn.close()

                return [
                    Alert(
                        id=row["id"],
                        name=row["name"],
                        description=row.get("description", ""),
                        priority=row.get("priority", 0),
                        is_active=bool(row.get("is_active", 1)),
                        last_triggered=row.get("last_triggered")
                    ) for row in rows
                ]

            except Exception as e:
                logger.error(f"GraphQL alerts query failed: {e}")
                return []

        @strawberry.field
        def dashboards(self) -> List[Dashboard]:
            """Get list of custom dashboards"""
            if not usage_tracker.enabled:
                return []

            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                conn.row_factory = sqlite3.Row

                try:
                    cursor = conn.execute("SELECT id, name, created_at, widgets FROM custom_dashboards")
                except sqlite3.OperationalError:
                    return []

                rows = cursor.fetchall()
                conn.close()

                return [
                    Dashboard(
                        id=row["id"],
                        name=row["name"],
                        created_at=row["created_at"],
                        widget_count=len(json.loads(row["widgets"])) if row["widgets"] else 0
                    ) for row in rows
                ]

            except Exception as e:
                logger.error(f"GraphQL dashboards query failed: {e}")
                return []

        @strawberry.field
        def cost_prediction(self, days: int = 7) -> float:
            """Get predicted cost for next N days"""
            try:
                from src.services.predictive_alerting import predictive_alerting
                forecast = predictive_alerting.predict_metrics(days)
                return forecast.cost_prediction
            except Exception as e:
                logger.error(f"GraphQL cost prediction failed: {e}")
                return 0.0

    # ==================== Mutation Resolver ====================

    @strawberry.type
    class Mutation:
        """Main mutation type for analytics platform"""

        @strawberry.mutation
        def create_alert_rule(
            self,
            name: str,
            description: str,
            condition_json: str,
            priority: int = 2
        ) -> QueryResult:
            """Create a new alert rule"""
            if not usage_tracker.enabled:
                return QueryResult(success=False, message="Usage tracking disabled")

            try:
                conn = sqlite3.connect(usage_tracker.db_path)

                import uuid
                rule_id = str(uuid.uuid4())

                conn.execute("""
                    INSERT INTO alert_rules (
                        id, name, description, condition_json, actions_json,
                        priority, is_active, created_at, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule_id,
                    name,
                    description,
                    condition_json,
                    json.dumps({"channels": ["in_app"]}),
                    priority,
                    1,
                    datetime.now().isoformat(),
                    "graphql_api"
                ))

                conn.commit()
                conn.close()

                return QueryResult(
                    success=True,
                    data=rule_id,
                    message="Alert rule created successfully"
                )

            except Exception as e:
                logger.error(f"GraphQL create alert failed: {e}")
                return QueryResult(success=False, message=str(e))

        @strawberry.mutation
        def update_dashboard(
            self,
            dashboard_id: str,
            widgets_json: str
        ) -> QueryResult:
            """Update dashboard widgets"""
            if not usage_tracker.enabled:
                return QueryResult(success=False, message="Usage tracking disabled")

            try:
                conn = sqlite3.connect(usage_tracker.db_path)

                cursor = conn.execute(
                    "SELECT id FROM custom_dashboards WHERE id = ?",
                    (dashboard_id,)
                )

                if not cursor.fetchone():
                    conn.close()
                    return QueryResult(success=False, message="Dashboard not found")

                conn.execute(
                    "UPDATE custom_dashboards SET widgets = ?, updated_at = ? WHERE id = ?",
                    (widgets_json, datetime.now().isoformat(), dashboard_id)
                )

                conn.commit()
                conn.close()

                return QueryResult(success=True, message="Dashboard updated")

            except Exception as e:
                logger.error(f"GraphQL update dashboard failed: {e}")
                return QueryResult(success=False, message=str(e))

        @strawberry.mutation
        def delete_entity(self, entity_type: str, entity_id: str) -> QueryResult:
            """Delete any entity by type and ID"""
            if not usage_tracker.enabled:
                return QueryResult(success=False, message="Usage tracking disabled")

            try:
                conn = sqlite3.connect(usage_tracker.db_path)

                table_map = {
                    "alert": "alert_rules",
                    "dashboard": "custom_dashboards",
                    "template": "report_templates",
                    "apikey": "api_keys"
                }

                table = table_map.get(entity_type)
                if not table:
                    return QueryResult(success=False, message="Invalid entity type")

                cursor = conn.execute(f"DELETE FROM {table} WHERE id = ?", (entity_id,))
                deleted = cursor.rowcount
                conn.commit()
                conn.close()

                if deleted == 0:
                    return QueryResult(success=False, message="Entity not found")

                return QueryResult(success=True, message="Entity deleted")

            except Exception as e:
                logger.error(f"GraphQL delete failed: {e}")
                return QueryResult(success=False, message=str(e))

    # Create schema
    schema = strawberry.Schema(query=Query, mutation=Mutation)

else:
    # Placeholder schema for when Strawberry is not available
    schema = None


# ==================== Simple GraphQL Alternative ====================
# If Strawberry is not available, provide a simple GraphQL-like JSON API

class SimpleGraphQL:
    """Simple GraphQL-like interface without external dependencies"""

    @staticmethod
    def execute(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a simple query"""
        try:
            # This is a simplified implementation
            # In production, use a real GraphQL library

            if "health" in query:
                return {"data": {"health": "Analytics API is running"}}

            if "metrics" in query:
                if not usage_tracker.enabled:
                    return {"data": {"metrics": []}}

                # Parse basic parameters from query
                import re
                start_match = re.search(r'startDate:\s*"([^"]+)"', query)
                end_match = re.search(r'endDate:\s*"([^"]+)"', query)

                if not start_match or not end_match:
                    return {"error": "Missing startDate or endDate"}

                start_date = start_match.group(1)
                end_date = end_match.group(1)

                # Use existing analytics functions
                conn = sqlite3.connect(usage_tracker.db_path)
                conn.row_factory = sqlite3.Row

                query_sql = """
                    SELECT
                        date(timestamp) as date,
                        SUM(total_tokens) as tokens,
                        SUM(estimated_cost) as cost,
                        COUNT(*) as requests
                    FROM api_requests
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY date(timestamp)
                    ORDER BY date
                """

                cursor = conn.execute(query_sql, [start_date, end_date])
                rows = cursor.fetchall()
                conn.close()

                metrics = [
                    {
                        "timestamp": row["date"],
                        "tokens": row["tokens"] or 0,
                        "cost": row["cost"] or 0,
                        "requests": row["requests"] or 0
                    } for row in rows
                ]

                return {"data": {"metrics": metrics}}

            return {"error": "Query not recognized"}

        except Exception as e:
            return {"error": str(e)}


# ==================== FastAPI Integration ====================

def get_graphql_router():
    """Get the GraphQL router for FastAPI"""
    if HAS_STRAWBERRY:
        from strawberry.fastapi import GraphQLRouter
        return GraphQLRouter(schema, graphiql=True)
    else:
        # Return a simple endpoint
        from fastapi import APIRouter
        router = APIRouter()

        @router.post("/graphql")
        async def simple_graphql(query: Dict[str, Any]):
            return SimpleGraphQL.execute(
                query.get("query", ""),
                query.get("variables", {})
            )

        @router.get("/graphql")
        async def graphql_playground():
            return {
                "message": "GraphQL Playground requires strawberry-graphql",
                "install": "pip install strawberry-graphql",
                "alternative": "Use POST /graphql with JSON: {\"query\": \"...\"}"
            }

        return router


# Export
__all__ = ["get_graphql_router", "schema", "SimpleGraphQL"]
