"""
Grant Repository - Data access for grants within a Vessel context.

Stores grants in the vessel's knowledge graph and provides query capabilities.
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import GrantApplication, GrantOpportunity, GrantSearchCriteria, GrantStatus

logger = logging.getLogger(__name__)


class GrantRepository:
    """
    Repository for grant data storage and retrieval.

    Stores grants associated with a specific vessel, enabling
    vessel-scoped grant management.
    """

    def __init__(self, vessel_id: str, db_path: Optional[str] = None):
        """
        Initialize repository for a vessel.

        Args:
            vessel_id: The vessel ID this repository is scoped to
            db_path: Optional path to SQLite database (defaults to data/grants_{vessel_id}.db)
        """
        self.vessel_id = vessel_id
        self._lock = threading.RLock()

        if db_path:
            self.db_path = db_path
        else:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / f"grants_{vessel_id}.db")

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_schema()

    def _create_schema(self) -> None:
        """Create database schema."""
        with self._lock:
            cursor = self.conn.cursor()

            # Grants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grants (
                    id TEXT PRIMARY KEY,
                    vessel_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    funder TEXT,
                    amount TEXT,
                    deadline TEXT,
                    eligibility TEXT,
                    focus_areas TEXT,
                    geographic_scope TEXT,
                    application_url TEXT,
                    contact_info TEXT,
                    requirements TEXT,
                    status TEXT,
                    discovery_date TEXT,
                    analysis_score REAL,
                    match_reasoning TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id TEXT PRIMARY KEY,
                    grant_id TEXT NOT NULL,
                    vessel_id TEXT NOT NULL,
                    applicant_info TEXT,
                    narrative_sections TEXT,
                    budget TEXT,
                    supporting_documents TEXT,
                    compliance_checklist TEXT,
                    submission_date TEXT,
                    status TEXT,
                    version INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (grant_id) REFERENCES grants(id)
                )
            """)

            # Indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_vessel ON grants(vessel_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_status ON grants(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_grants_deadline ON grants(deadline)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_vessel ON applications(vessel_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_grant ON applications(grant_id)")

            self.conn.commit()

    # Grant Operations

    def save_grant(self, grant: GrantOpportunity) -> GrantOpportunity:
        """
        Save or update a grant opportunity.

        Args:
            grant: The grant to save

        Returns:
            The saved grant
        """
        # Ensure grant is associated with this vessel
        grant.vessel_id = self.vessel_id

        with self._lock:
            cursor = self.conn.cursor()
            now = datetime.utcnow().isoformat()

            cursor.execute("""
                INSERT OR REPLACE INTO grants
                (id, vessel_id, title, description, funder, amount, deadline,
                 eligibility, focus_areas, geographic_scope, application_url,
                 contact_info, requirements, status, discovery_date,
                 analysis_score, match_reasoning, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                grant.id,
                grant.vessel_id,
                grant.title,
                grant.description,
                grant.funder,
                grant.amount,
                grant.deadline.isoformat(),
                json.dumps(grant.eligibility),
                json.dumps(grant.focus_areas),
                grant.geographic_scope,
                grant.application_url,
                json.dumps(grant.contact_info),
                json.dumps(grant.requirements),
                grant.status.value,
                grant.discovery_date.isoformat(),
                grant.analysis_score,
                grant.match_reasoning,
                now,
                now,
            ))
            self.conn.commit()

        logger.debug(f"Saved grant {grant.id} for vessel {self.vessel_id}")
        return grant

    def get_grant(self, grant_id: str) -> Optional[GrantOpportunity]:
        """
        Get a grant by ID.

        Args:
            grant_id: The grant ID

        Returns:
            The grant if found, None otherwise
        """
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM grants WHERE id = ? AND vessel_id = ?",
                (grant_id, self.vessel_id)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_grant(row)

    def list_grants(
        self,
        status: Optional[GrantStatus] = None,
        limit: int = 100
    ) -> List[GrantOpportunity]:
        """
        List grants for this vessel.

        Args:
            status: Optional status filter
            limit: Maximum number of grants to return

        Returns:
            List of grants
        """
        with self._lock:
            cursor = self.conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM grants WHERE vessel_id = ? AND status = ? ORDER BY deadline ASC LIMIT ?",
                    (self.vessel_id, status.value, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM grants WHERE vessel_id = ? ORDER BY deadline ASC LIMIT ?",
                    (self.vessel_id, limit)
                )
            return [self._row_to_grant(row) for row in cursor.fetchall()]

    def search_grants(self, criteria: GrantSearchCriteria) -> List[GrantOpportunity]:
        """
        Search grants based on criteria.

        Args:
            criteria: Search criteria

        Returns:
            List of matching grants
        """
        with self._lock:
            cursor = self.conn.cursor()
            query = "SELECT * FROM grants WHERE vessel_id = ?"
            params: List[Any] = [self.vessel_id]

            if criteria.deadline_after:
                query += " AND deadline >= ?"
                params.append(criteria.deadline_after.isoformat())

            if criteria.deadline_before:
                query += " AND deadline <= ?"
                params.append(criteria.deadline_before.isoformat())

            if criteria.geographic_scope:
                query += " AND geographic_scope LIKE ?"
                params.append(f"%{criteria.geographic_scope}%")

            query += " ORDER BY deadline ASC"

            cursor.execute(query, params)
            grants = [self._row_to_grant(row) for row in cursor.fetchall()]

            # Apply focus areas filter (JSON field, filter in Python)
            if criteria.focus_areas:
                grants = [
                    g for g in grants
                    if any(fa.lower() in [f.lower() for f in g.focus_areas]
                           for fa in criteria.focus_areas)
                ]

            # Apply keywords filter
            if criteria.keywords:
                grants = [
                    g for g in grants
                    if any(kw.lower() in g.title.lower() or kw.lower() in g.description.lower()
                           for kw in criteria.keywords)
                ]

            return grants

    def delete_grant(self, grant_id: str) -> bool:
        """
        Delete a grant.

        Args:
            grant_id: The grant ID

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM grants WHERE id = ? AND vessel_id = ?",
                (grant_id, self.vessel_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0

    def update_grant_status(self, grant_id: str, status: GrantStatus) -> bool:
        """
        Update grant status.

        Args:
            grant_id: The grant ID
            status: New status

        Returns:
            True if updated, False if not found
        """
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE grants SET status = ?, updated_at = ? WHERE id = ? AND vessel_id = ?",
                (status.value, datetime.utcnow().isoformat(), grant_id, self.vessel_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0

    # Application Operations

    def save_application(self, application: GrantApplication) -> GrantApplication:
        """
        Save or update an application.

        Args:
            application: The application to save

        Returns:
            The saved application
        """
        application.vessel_id = self.vessel_id
        application.updated_at = datetime.utcnow()

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO applications
                (id, grant_id, vessel_id, applicant_info, narrative_sections,
                 budget, supporting_documents, compliance_checklist,
                 submission_date, status, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application.id,
                application.grant_id,
                application.vessel_id,
                json.dumps(application.applicant_info),
                json.dumps(application.narrative_sections),
                json.dumps(application.budget),
                json.dumps(application.supporting_documents),
                json.dumps(application.compliance_checklist),
                application.submission_date.isoformat() if application.submission_date else None,
                application.status.value,
                application.version,
                application.created_at.isoformat(),
                application.updated_at.isoformat(),
            ))
            self.conn.commit()

        logger.debug(f"Saved application {application.id} for grant {application.grant_id}")
        return application

    def get_application(self, application_id: str) -> Optional[GrantApplication]:
        """Get an application by ID."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM applications WHERE id = ? AND vessel_id = ?",
                (application_id, self.vessel_id)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_application(row)

    def get_application_for_grant(self, grant_id: str) -> Optional[GrantApplication]:
        """Get the application for a specific grant."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM applications WHERE grant_id = ? AND vessel_id = ? ORDER BY version DESC LIMIT 1",
                (grant_id, self.vessel_id)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_application(row)

    def list_applications(
        self,
        status: Optional[GrantStatus] = None,
        limit: int = 100
    ) -> List[GrantApplication]:
        """List applications for this vessel."""
        with self._lock:
            cursor = self.conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM applications WHERE vessel_id = ? AND status = ? ORDER BY updated_at DESC LIMIT ?",
                    (self.vessel_id, status.value, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM applications WHERE vessel_id = ? ORDER BY updated_at DESC LIMIT ?",
                    (self.vessel_id, limit)
                )
            return [self._row_to_application(row) for row in cursor.fetchall()]

    # Helper methods

    def _row_to_grant(self, row: tuple) -> GrantOpportunity:
        """Convert database row to GrantOpportunity."""
        return GrantOpportunity(
            id=row[0],
            vessel_id=row[1],
            title=row[2],
            description=row[3] or "",
            funder=row[4] or "",
            amount=row[5] or "",
            deadline=datetime.fromisoformat(row[6]) if row[6] else datetime.utcnow(),
            eligibility=json.loads(row[7] or "[]"),
            focus_areas=json.loads(row[8] or "[]"),
            geographic_scope=row[9] or "",
            application_url=row[10] or "",
            contact_info=json.loads(row[11] or "{}"),
            requirements=json.loads(row[12] or "[]"),
            status=GrantStatus(row[13]) if row[13] else GrantStatus.DISCOVERED,
            discovery_date=datetime.fromisoformat(row[14]) if row[14] else datetime.utcnow(),
            analysis_score=row[15] or 0.0,
            match_reasoning=row[16] or "",
        )

    def _row_to_application(self, row: tuple) -> GrantApplication:
        """Convert database row to GrantApplication."""
        return GrantApplication(
            id=row[0],
            grant_id=row[1],
            vessel_id=row[2],
            applicant_info=json.loads(row[3] or "{}"),
            narrative_sections=json.loads(row[4] or "{}"),
            budget=json.loads(row[5] or "{}"),
            supporting_documents=json.loads(row[6] or "[]"),
            compliance_checklist=json.loads(row[7] or "{}"),
            submission_date=datetime.fromisoformat(row[8]) if row[8] else None,
            status=GrantStatus(row[9]) if row[9] else GrantStatus.APPLICATION_DRAFT,
            version=row[10] or 1,
            created_at=datetime.fromisoformat(row[11]) if row[11] else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row[12]) if row[12] else datetime.utcnow(),
        )

    def close(self) -> None:
        """Close database connection."""
        with self._lock:
            self.conn.close()
