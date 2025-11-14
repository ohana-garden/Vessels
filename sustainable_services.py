"""
Sustainable Community Services System

This module supports building self-sustaining community services where grants
act as seed money to launch services that eventually become financially independent
and serve the ongoing well-being of the community.

Philosophy:
- Grants are catalysts, not crutches
- Services should create value that communities will support
- Sustainability comes from serving real needs well
- Well-being is measured in community flourishing, not just financials
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
from datetime import datetime, timedelta
import sqlite3
import json


class ServiceType(Enum):
    """Types of community services that can be self-sustaining"""
    ELDER_CARE = "elder_care"
    FOOD_SYSTEMS = "food_systems"  # Community kitchens, food banks, CSAs
    EDUCATION = "education"  # Skills training, tutoring, workshops
    CHILDCARE = "childcare"
    HEALTH_WELLNESS = "health_wellness"  # Clinics, mental health, fitness
    HOUSING = "housing"  # Affordable housing, repair services
    TRANSPORTATION = "transportation"  # Ride sharing, shuttle services
    ARTS_CULTURE = "arts_culture"  # Studios, performance spaces, galleries
    COOPERATIVE = "cooperative"  # Worker co-ops, buying clubs
    TECHNOLOGY = "technology"  # Digital literacy, equipment access
    ENVIRONMENTAL = "environmental"  # Recycling, renewable energy, conservation
    MUTUAL_AID = "mutual_aid"  # Emergency assistance, resource sharing


class SustainabilityStage(Enum):
    """Journey from grant-dependent to self-sustaining"""
    CONCEPT = "concept"  # Idea phase, seeking seed funding
    SEED_FUNDED = "seed_funded"  # Grant received, launching service
    EARLY_OPERATION = "early_operation"  # Operating but grant-dependent
    REVENUE_EMERGING = "revenue_emerging"  # Some self-generated revenue
    PARTIALLY_SUSTAINABLE = "partially_sustainable"  # 50%+ self-funded
    MOSTLY_SUSTAINABLE = "mostly_sustainable"  # 80%+ self-funded
    FULLY_SUSTAINABLE = "fully_sustainable"  # 100% self-funded
    SURPLUS_GENERATING = "surplus_generating"  # Profitable, can seed others


class RevenueModel(Enum):
    """Ways services can generate sustainable revenue"""
    SLIDING_SCALE_FEES = "sliding_scale_fees"  # Pay what you can
    MEMBERSHIP_DUES = "membership_dues"  # Cooperative memberships
    SERVICE_CONTRACTS = "service_contracts"  # B2B or government contracts
    SOCIAL_ENTERPRISE = "social_enterprise"  # Selling products/services
    COMMUNITY_SUPPORTED = "community_supported"  # CSA model
    SPONSORSHIPS = "sponsorships"  # Business/organizational sponsors
    EARNED_INCOME = "earned_income"  # Fee for service
    HYBRID = "hybrid"  # Multiple revenue streams
    DONATION_BASED = "donation_based"  # Voluntary contributions
    TIME_BANKING = "time_banking"  # Service exchange economy


@dataclass
class WellBeingMetric:
    """Measures community well-being impact beyond financials"""
    metric_name: str
    description: str
    current_value: float
    target_value: float
    measurement_method: str
    frequency: str  # daily, weekly, monthly, quarterly
    data_points: List[Dict] = field(default_factory=list)

    def calculate_improvement(self) -> float:
        """Calculate percentage improvement toward target"""
        if len(self.data_points) < 2:
            return 0.0
        initial = self.data_points[0]['value']
        current = self.data_points[-1]['value']
        if self.target_value == initial:
            return 0.0
        return ((current - initial) / (self.target_value - initial)) * 100


@dataclass
class RevenueStrategy:
    """Plan for generating sustainable revenue"""
    revenue_model: RevenueModel
    description: str
    target_monthly_revenue: float
    current_monthly_revenue: float
    implementation_steps: List[str]
    timeline_months: int
    resources_needed: List[str]
    risks: List[str]
    mitigation_strategies: List[str]

    def sustainability_ratio(self) -> float:
        """What percentage of target revenue is achieved"""
        if self.target_monthly_revenue == 0:
            return 0.0
        return (self.current_monthly_revenue / self.target_monthly_revenue) * 100


@dataclass
class SustainableService:
    """A community service designed for long-term sustainability"""
    id: str
    name: str
    service_type: ServiceType
    description: str
    sustainability_stage: SustainabilityStage

    # Financial sustainability
    monthly_operating_cost: float
    revenue_strategies: List[RevenueStrategy]
    current_monthly_revenue: float
    grant_funding_remaining: float
    months_until_grant_depleted: int

    # Well-being impact
    well_being_metrics: List[WellBeingMetric]
    people_served_monthly: int
    community_satisfaction_score: float  # 0-100

    # Transition planning
    transition_plan: Dict  # Steps to achieve sustainability
    milestones: List[Dict]  # Key checkpoints
    risks: List[str]
    contingency_plans: Dict

    # Community engagement
    volunteers: int
    community_partners: List[str]
    stakeholder_groups: List[str]

    # Learning and adaptation
    lessons_learned: List[str]
    adaptations_made: List[Dict]
    success_factors: List[str]

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def self_sufficiency_percentage(self) -> float:
        """What percentage of operating costs are covered by earned revenue"""
        if self.monthly_operating_cost == 0:
            return 100.0
        return (self.current_monthly_revenue / self.monthly_operating_cost) * 100

    def months_to_sustainability(self) -> Optional[int]:
        """Estimate months until fully self-sustaining based on current trajectory"""
        if self.current_monthly_revenue >= self.monthly_operating_cost:
            return 0

        # Calculate average monthly revenue growth
        if len(self.revenue_strategies) == 0:
            return None

        # Simple projection based on planned growth
        total_target = sum(rs.target_monthly_revenue for rs in self.revenue_strategies)
        avg_timeline = sum(rs.timeline_months for rs in self.revenue_strategies) / len(self.revenue_strategies)

        gap = self.monthly_operating_cost - self.current_monthly_revenue
        monthly_growth_needed = gap / avg_timeline if avg_timeline > 0 else 0

        if monthly_growth_needed <= 0:
            return None

        return int(gap / monthly_growth_needed) if monthly_growth_needed > 0 else None

    def overall_health_score(self) -> float:
        """Composite score: financial sustainability + community well-being"""
        financial_score = min(self.self_sufficiency_percentage(), 100)

        # Average well-being improvement
        if self.well_being_metrics:
            wellbeing_score = sum(m.calculate_improvement() for m in self.well_being_metrics) / len(self.well_being_metrics)
        else:
            wellbeing_score = self.community_satisfaction_score

        # Weighted average: 60% financial, 40% well-being
        return (financial_score * 0.6) + (wellbeing_score * 0.4)


class SustainableServicesOrchestrator:
    """
    Manages portfolio of sustainable services, helping them transition
    from grant-funded startups to self-sustaining community assets
    """

    def __init__(self, db_path: str = "shoghi_grants.db"):
        self.db_path = db_path
        self.services: Dict[str, SustainableService] = {}
        self._init_database()
        self._load_services()

    def _init_database(self):
        """Initialize database tables for sustainable services"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sustainable_services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                description TEXT,
                sustainability_stage TEXT,
                monthly_operating_cost REAL,
                current_monthly_revenue REAL,
                grant_funding_remaining REAL,
                months_until_grant_depleted INTEGER,
                people_served_monthly INTEGER,
                community_satisfaction_score REAL,
                volunteers INTEGER,
                data JSON,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id TEXT,
                metric_name TEXT,
                metric_value REAL,
                measured_at TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES sustainable_services(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id TEXT,
                event_type TEXT,
                description TEXT,
                impact TEXT,
                occurred_at TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES sustainable_services(id)
            )
        """)

        conn.commit()
        conn.close()

    def _load_services(self):
        """Load existing services from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sustainable_services")
        # Implementation would deserialize services
        conn.close()

    def create_service(
        self,
        name: str,
        service_type: ServiceType,
        description: str,
        monthly_operating_cost: float,
        seed_grant_amount: float
    ) -> SustainableService:
        """Initialize a new sustainable service with seed funding"""
        service = SustainableService(
            id=f"{service_type.value}_{datetime.now().timestamp()}",
            name=name,
            service_type=service_type,
            description=description,
            sustainability_stage=SustainabilityStage.SEED_FUNDED,
            monthly_operating_cost=monthly_operating_cost,
            revenue_strategies=[],
            current_monthly_revenue=0.0,
            grant_funding_remaining=seed_grant_amount,
            months_until_grant_depleted=int(seed_grant_amount / monthly_operating_cost) if monthly_operating_cost > 0 else 0,
            well_being_metrics=[],
            people_served_monthly=0,
            community_satisfaction_score=0.0,
            transition_plan={},
            milestones=[],
            risks=[],
            contingency_plans={},
            volunteers=0,
            community_partners=[],
            stakeholder_groups=[],
            lessons_learned=[],
            adaptations_made=[],
            success_factors=[]
        )

        self.services[service.id] = service
        self._save_service(service)
        return service

    def add_revenue_strategy(
        self,
        service_id: str,
        revenue_model: RevenueModel,
        description: str,
        target_monthly_revenue: float,
        timeline_months: int,
        implementation_steps: List[str]
    ):
        """Add a revenue generation strategy to a service"""
        service = self.services.get(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        strategy = RevenueStrategy(
            revenue_model=revenue_model,
            description=description,
            target_monthly_revenue=target_monthly_revenue,
            current_monthly_revenue=0.0,
            implementation_steps=implementation_steps,
            timeline_months=timeline_months,
            resources_needed=[],
            risks=[],
            mitigation_strategies=[]
        )

        service.revenue_strategies.append(strategy)
        service.updated_at = datetime.now()
        self._save_service(service)

    def update_revenue(self, service_id: str, revenue_model: RevenueModel, monthly_revenue: float):
        """Update revenue generated from a specific model"""
        service = self.services.get(service_id)
        if not service:
            return

        for strategy in service.revenue_strategies:
            if strategy.revenue_model == revenue_model:
                strategy.current_monthly_revenue = monthly_revenue

        # Recalculate total revenue
        service.current_monthly_revenue = sum(
            s.current_monthly_revenue for s in service.revenue_strategies
        )

        # Update sustainability stage based on revenue
        self._update_sustainability_stage(service)
        self._save_service(service)

    def _update_sustainability_stage(self, service: SustainableService):
        """Update service's sustainability stage based on current metrics"""
        sufficiency = service.self_sufficiency_percentage()

        if sufficiency >= 100 and service.current_monthly_revenue > service.monthly_operating_cost * 1.2:
            service.sustainability_stage = SustainabilityStage.SURPLUS_GENERATING
        elif sufficiency >= 100:
            service.sustainability_stage = SustainabilityStage.FULLY_SUSTAINABLE
        elif sufficiency >= 80:
            service.sustainability_stage = SustainabilityStage.MOSTLY_SUSTAINABLE
        elif sufficiency >= 50:
            service.sustainability_stage = SustainabilityStage.PARTIALLY_SUSTAINABLE
        elif sufficiency >= 20:
            service.sustainability_stage = SustainabilityStage.REVENUE_EMERGING
        elif service.grant_funding_remaining > 0:
            service.sustainability_stage = SustainabilityStage.EARLY_OPERATION
        else:
            service.sustainability_stage = SustainabilityStage.SEED_FUNDED

    def add_wellbeing_metric(
        self,
        service_id: str,
        metric_name: str,
        description: str,
        target_value: float,
        measurement_method: str,
        frequency: str = "monthly"
    ):
        """Add a well-being metric to track community impact"""
        service = self.services.get(service_id)
        if not service:
            return

        metric = WellBeingMetric(
            metric_name=metric_name,
            description=description,
            current_value=0.0,
            target_value=target_value,
            measurement_method=measurement_method,
            frequency=frequency,
            data_points=[]
        )

        service.well_being_metrics.append(metric)
        self._save_service(service)

    def record_metric(self, service_id: str, metric_name: str, value: float):
        """Record a measurement for a well-being metric"""
        service = self.services.get(service_id)
        if not service:
            return

        for metric in service.well_being_metrics:
            if metric.metric_name == metric_name:
                data_point = {
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                }
                metric.data_points.append(data_point)
                metric.current_value = value

                # Save to database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO service_metrics (service_id, metric_name, metric_value, measured_at) VALUES (?, ?, ?, ?)",
                    (service_id, metric_name, value, datetime.now())
                )
                conn.commit()
                conn.close()
                break

        self._save_service(service)

    def generate_sustainability_report(self, service_id: str) -> Dict:
        """Generate comprehensive sustainability report for a service"""
        service = self.services.get(service_id)
        if not service:
            return {}

        return {
            'service_name': service.name,
            'service_type': service.service_type.value,
            'sustainability_stage': service.sustainability_stage.value,
            'financial_health': {
                'self_sufficiency_percentage': service.self_sufficiency_percentage(),
                'monthly_operating_cost': service.monthly_operating_cost,
                'monthly_revenue': service.current_monthly_revenue,
                'revenue_gap': service.monthly_operating_cost - service.current_monthly_revenue,
                'grant_funding_remaining': service.grant_funding_remaining,
                'months_until_grant_depleted': service.months_until_grant_depleted,
                'estimated_months_to_sustainability': service.months_to_sustainability()
            },
            'community_impact': {
                'people_served_monthly': service.people_served_monthly,
                'satisfaction_score': service.community_satisfaction_score,
                'volunteers': service.volunteers,
                'wellbeing_metrics': [
                    {
                        'name': m.metric_name,
                        'current': m.current_value,
                        'target': m.target_value,
                        'improvement': m.calculate_improvement()
                    }
                    for m in service.well_being_metrics
                ]
            },
            'revenue_strategies': [
                {
                    'model': rs.revenue_model.value,
                    'description': rs.description,
                    'target': rs.target_monthly_revenue,
                    'current': rs.current_monthly_revenue,
                    'completion': rs.sustainability_ratio()
                }
                for rs in service.revenue_strategies
            ],
            'overall_health_score': service.overall_health_score(),
            'recommendations': self._generate_recommendations(service)
        }

    def _generate_recommendations(self, service: SustainableService) -> List[str]:
        """Generate specific recommendations for improving sustainability"""
        recommendations = []

        sufficiency = service.self_sufficiency_percentage()

        if sufficiency < 50:
            recommendations.append("Focus on implementing revenue strategies - service is still heavily grant-dependent")
            recommendations.append("Consider diversifying revenue streams with hybrid model")

        if service.months_until_grant_depleted and service.months_until_grant_depleted < 6:
            recommendations.append("URGENT: Grant funding will be depleted soon - accelerate revenue generation")

        if service.community_satisfaction_score < 70:
            recommendations.append("Improve service quality and community engagement before focusing on revenue")

        if len(service.revenue_strategies) < 2:
            recommendations.append("Diversify revenue sources to reduce financial risk")

        if service.volunteers < 5:
            recommendations.append("Build volunteer base to reduce operating costs")

        months_to_sustain = service.months_to_sustainability()
        if months_to_sustain and months_to_sustain > service.months_until_grant_depleted:
            recommendations.append("Revenue trajectory won't reach sustainability before grant depletion - adjust strategy")

        return recommendations

    def identify_replication_opportunities(self, service_id: str) -> List[Dict]:
        """Identify if service model can be replicated in other communities"""
        service = self.services.get(service_id)
        if not service:
            return []

        if service.sustainability_stage not in [
            SustainabilityStage.FULLY_SUSTAINABLE,
            SustainabilityStage.SURPLUS_GENERATING
        ]:
            return []

        return [{
            'replication_ready': True,
            'success_factors': service.success_factors,
            'required_resources': {
                'initial_funding': service.monthly_operating_cost * 12,  # One year runway
                'volunteers_needed': service.volunteers,
                'key_partnerships': service.community_partners
            },
            'revenue_blueprint': [
                {
                    'model': rs.revenue_model.value,
                    'implementation_steps': rs.implementation_steps,
                    'timeline': rs.timeline_months,
                    'expected_revenue': rs.current_monthly_revenue
                }
                for rs in service.revenue_strategies
            ],
            'lessons_learned': service.lessons_learned
        }]

    def _save_service(self, service: SustainableService):
        """Save service to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = {
            'revenue_strategies': [
                {
                    'revenue_model': rs.revenue_model.value,
                    'description': rs.description,
                    'target_monthly_revenue': rs.target_monthly_revenue,
                    'current_monthly_revenue': rs.current_monthly_revenue,
                    'implementation_steps': rs.implementation_steps,
                    'timeline_months': rs.timeline_months,
                    'resources_needed': rs.resources_needed,
                    'risks': rs.risks,
                    'mitigation_strategies': rs.mitigation_strategies
                }
                for rs in service.revenue_strategies
            ],
            'well_being_metrics': [
                {
                    'metric_name': m.metric_name,
                    'description': m.description,
                    'current_value': m.current_value,
                    'target_value': m.target_value,
                    'measurement_method': m.measurement_method,
                    'frequency': m.frequency
                }
                for m in service.well_being_metrics
            ],
            'transition_plan': service.transition_plan,
            'milestones': service.milestones,
            'risks': service.risks,
            'contingency_plans': service.contingency_plans,
            'community_partners': service.community_partners,
            'stakeholder_groups': service.stakeholder_groups,
            'lessons_learned': service.lessons_learned,
            'adaptations_made': service.adaptations_made,
            'success_factors': service.success_factors
        }

        cursor.execute("""
            INSERT OR REPLACE INTO sustainable_services
            (id, name, service_type, description, sustainability_stage,
             monthly_operating_cost, current_monthly_revenue, grant_funding_remaining,
             months_until_grant_depleted, people_served_monthly, community_satisfaction_score,
             volunteers, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            service.id,
            service.name,
            service.service_type.value,
            service.description,
            service.sustainability_stage.value,
            service.monthly_operating_cost,
            service.current_monthly_revenue,
            service.grant_funding_remaining,
            service.months_until_grant_depleted,
            service.people_served_monthly,
            service.community_satisfaction_score,
            service.volunteers,
            json.dumps(data),
            service.created_at,
            service.updated_at
        ))

        conn.commit()
        conn.close()

    def get_portfolio_overview(self) -> Dict:
        """Overview of all services and their collective impact"""
        if not self.services:
            return {
                'total_services': 0,
                'total_people_served': 0,
                'total_monthly_revenue': 0,
                'avg_sustainability': 0
            }

        return {
            'total_services': len(self.services),
            'by_stage': {
                stage.value: len([s for s in self.services.values() if s.sustainability_stage == stage])
                for stage in SustainabilityStage
            },
            'by_type': {
                stype.value: len([s for s in self.services.values() if s.service_type == stype])
                for stype in ServiceType
            },
            'total_people_served': sum(s.people_served_monthly for s in self.services.values()),
            'total_monthly_revenue': sum(s.current_monthly_revenue for s in self.services.values()),
            'total_operating_cost': sum(s.monthly_operating_cost for s in self.services.values()),
            'avg_sustainability': sum(s.self_sufficiency_percentage() for s in self.services.values()) / len(self.services),
            'avg_health_score': sum(s.overall_health_score() for s in self.services.values()) / len(self.services),
            'services_at_risk': [
                s.name for s in self.services.values()
                if s.months_until_grant_depleted and s.months_until_grant_depleted < 6
                and s.self_sufficiency_percentage() < 50
            ],
            'services_thriving': [
                s.name for s in self.services.values()
                if s.sustainability_stage in [SustainabilityStage.FULLY_SUSTAINABLE, SustainabilityStage.SURPLUS_GENERATING]
            ]
        }
