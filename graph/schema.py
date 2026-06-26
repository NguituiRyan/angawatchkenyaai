"""Neo4j schema: uniqueness constraints + an index. Idempotent."""
from __future__ import annotations

CONSTRAINTS = [
    "CREATE CONSTRAINT farmer_id IF NOT EXISTS FOR (f:Farmer) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT gh_id IF NOT EXISTS FOR (g:Greenhouse) REQUIRE g.id IS UNIQUE",
    "CREATE CONSTRAINT season_id IF NOT EXISTS FOR (s:Season) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT reading_id IF NOT EXISTS FOR (r:Reading) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT alert_id IF NOT EXISTS FOR (a:Alert) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT action_id IF NOT EXISTS FOR (x:Action) REQUIRE x.id IS UNIQUE",
    "CREATE CONSTRAINT harvest_id IF NOT EXISTS FOR (h:Harvest) REQUIRE h.id IS UNIQUE",
    "CREATE CONSTRAINT coop_id IF NOT EXISTS FOR (c:Cooperative) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT lender_id IF NOT EXISTS FOR (l:Lender) REQUIRE l.id IS UNIQUE",
    "CREATE CONSTRAINT audit_id IF NOT EXISTS FOR (u:AuditRecord) REQUIRE u.id IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX reading_ts IF NOT EXISTS FOR (r:Reading) ON (r.ts)",
]


def apply_schema(driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as s:
        for stmt in CONSTRAINTS + INDEXES:
            s.run(stmt)
