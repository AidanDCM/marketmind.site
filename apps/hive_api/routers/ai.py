"""
AI Decision Making and Reasoning API Router

Provides endpoints for AI decision tracking, reasoning patterns,
and system intelligence monitoring for the Command Center.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from apps.hive_api.security import SubjectScope, get_subject_scope_optional

router = APIRouter(prefix="/ai", tags=["AI Decision Making"])

# Pydantic Models
class AIDecision(BaseModel):
    id: int
    timestamp: str
    decision: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    factors: List[str]
    outcome: str
    brain_id: Optional[str] = None
    model_version: Optional[str] = None
    impact_score: Optional[float] = None

class ReasoningPattern(BaseModel):
    pattern: str
    usage: str
    accuracy: str
    active_since: Optional[datetime] = None
    success_rate: Optional[float] = None
    last_used: Optional[datetime] = None

class AIDecisionResponse(BaseModel):
    ok: bool = True
    items: List[AIDecision]
    total: int
    limit: int
    offset: int

class ReasoningPatternResponse(BaseModel):
    ok: bool = True
    items: List[ReasoningPattern]
    total: int
    limit: int
    offset: int

class AIInsight(BaseModel):
    insight_type: str
    title: str
    description: str
    confidence: float
    created_at: datetime
    tags: List[str]

class AIInsightResponse(BaseModel):
    ok: bool = True
    items: List[AIInsight]
    total: int

# Mock data generators for development
def generate_mock_decisions(limit: int = 10, offset: int = 0) -> List[AIDecision]:
    """Generate realistic mock AI decision data"""
    base_decisions = [
        {
            "decision": "Price Optimization",
            "reasoning": "Competitor analysis shows 15% price gap. Market demand stable at current volume. Recommended 8% price increase to maximize profit margin while maintaining conversion rate.",
            "confidence": 0.87,
            "factors": ["competitor_pricing", "demand_elasticity", "inventory_levels", "market_trends"],
            "outcome": "implemented",
            "brain_id": "pricing_brain_v2.1",
            "model_version": "neural_net_v3.2",
            "impact_score": 0.92
        },
        {
            "decision": "Inventory Restock",
            "reasoning": "Sales velocity increased 23% over 7 days. Current stock will deplete in 4 days. Lead time is 6 days. Triggering restock order to prevent stockout.",
            "confidence": 0.94,
            "factors": ["sales_velocity", "lead_time", "demand_forecast", "supplier_reliability"],
            "outcome": "pending",
            "brain_id": "inventory_brain_v1.8",
            "model_version": "lstm_v2.1",
            "impact_score": 0.88
        },
        {
            "decision": "Marketing Budget Allocation",
            "reasoning": "Google Ads showing 34% higher ROAS than Facebook. Amazon PPC conversion rate declined 12%. Reallocating 40% budget from Facebook to Google Ads.",
            "confidence": 0.76,
            "factors": ["roas_comparison", "conversion_rates", "budget_efficiency", "audience_overlap"],
            "outcome": "implemented",
            "brain_id": "marketing_brain_v1.5",
            "model_version": "ensemble_v1.9",
            "impact_score": 0.79
        },
        {
            "decision": "Product Listing Optimization",
            "reasoning": "A/B test results show new title format increases CTR by 18%. Keywords 'premium' and 'durable' show 25% higher conversion. Updating listing copy.",
            "confidence": 0.91,
            "factors": ["ab_test_results", "keyword_performance", "ctr_analysis", "competitor_analysis"],
            "outcome": "implemented",
            "brain_id": "listing_brain_v2.3",
            "model_version": "nlp_v4.1",
            "impact_score": 0.85
        },
        {
            "decision": "Supplier Diversification",
            "reasoning": "Primary supplier showing 15% delivery delays. Risk assessment indicates 67% probability of further delays. Adding secondary supplier to reduce risk.",
            "confidence": 0.83,
            "factors": ["supplier_performance", "risk_assessment", "delivery_metrics", "cost_analysis"],
            "outcome": "in_progress",
            "brain_id": "supply_brain_v1.2",
            "model_version": "risk_model_v2.0",
            "impact_score": 0.71
        },
        {
            "decision": "Customer Segmentation Update",
            "reasoning": "Clustering analysis reveals new high-value segment: tech professionals aged 28-35. This segment shows 45% higher LTV. Adjusting targeting strategy.",
            "confidence": 0.89,
            "factors": ["clustering_analysis", "ltv_calculation", "demographic_data", "purchase_behavior"],
            "outcome": "implemented",
            "brain_id": "customer_brain_v2.0",
            "model_version": "clustering_v3.1",
            "impact_score": 0.93
        }
    ]
    
    decisions = []
    for i in range(limit):
        base_idx = (i + offset) % len(base_decisions)
        decision_data = base_decisions[base_idx].copy()
        
        # Add realistic timestamp variations
        minutes_ago = (i + offset) * 45 + (base_idx * 120)
        timestamp = datetime.now() - timedelta(minutes=minutes_ago)
        
        decisions.append(AIDecision(
            id=i + offset + 1,
            timestamp=timestamp.isoformat(),
            **decision_data
        ))
    
    return decisions

def generate_mock_patterns(limit: int = 8, offset: int = 0) -> List[ReasoningPattern]:
    """Generate realistic mock reasoning pattern data"""
    base_patterns = [
        {
            "pattern": "Price Sensitivity Analysis",
            "usage": "Active",
            "accuracy": "89%",
            "success_rate": 0.89,
            "active_since": datetime.now() - timedelta(days=45)
        },
        {
            "pattern": "Demand Forecasting",
            "usage": "Active", 
            "accuracy": "92%",
            "success_rate": 0.92,
            "active_since": datetime.now() - timedelta(days=67)
        },
        {
            "pattern": "Competitor Monitoring",
            "usage": "Active",
            "accuracy": "85%",
            "success_rate": 0.85,
            "active_since": datetime.now() - timedelta(days=23)
        },
        {
            "pattern": "Inventory Optimization",
            "usage": "Active",
            "accuracy": "91%",
            "success_rate": 0.91,
            "active_since": datetime.now() - timedelta(days=89)
        },
        {
            "pattern": "Customer Behavior Analysis",
            "usage": "Active",
            "accuracy": "87%",
            "success_rate": 0.87,
            "active_since": datetime.now() - timedelta(days=34)
        },
        {
            "pattern": "Risk Assessment",
            "usage": "Standby",
            "accuracy": "83%",
            "success_rate": 0.83,
            "active_since": datetime.now() - timedelta(days=12)
        },
        {
            "pattern": "Market Trend Detection",
            "usage": "Active",
            "accuracy": "88%",
            "success_rate": 0.88,
            "active_since": datetime.now() - timedelta(days=56)
        },
        {
            "pattern": "Seasonal Pattern Recognition",
            "usage": "Seasonal",
            "accuracy": "94%",
            "success_rate": 0.94,
            "active_since": datetime.now() - timedelta(days=120)
        }
    ]
    
    patterns = []
    for i in range(min(limit, len(base_patterns))):
        pattern_data = base_patterns[(i + offset) % len(base_patterns)].copy()
        pattern_data["last_used"] = datetime.now() - timedelta(minutes=(i * 30))
        patterns.append(ReasoningPattern(**pattern_data))
    
    return patterns

@router.get("/decisions", response_model=AIDecisionResponse)
async def get_ai_decisions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    outcome: Optional[str] = Query(None, description="Filter by outcome: implemented, pending, rejected"),
    brain_id: Optional[str] = Query(None, description="Filter by brain ID"),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    """
    Get recent AI decisions with reasoning and outcomes.
    
    Returns paginated list of AI decisions made by the system,
    including confidence scores, reasoning, and implementation status.
    """
    
    # In a real implementation, this would query the database
    # For now, return mock data for development
    decisions = generate_mock_decisions(limit, offset)
    
    # Apply filters if provided
    if outcome:
        decisions = [d for d in decisions if d.outcome == outcome]
    
    if brain_id:
        decisions = [d for d in decisions if d.brain_id == brain_id]
    
    return AIDecisionResponse(
        items=decisions,
        total=len(decisions) + offset,  # Mock total
        limit=limit,
        offset=offset
    )

@router.get("/reasoning", response_model=ReasoningPatternResponse)
async def get_reasoning_patterns(
    limit: int = Query(8, ge=1, le=50),
    offset: int = Query(0, ge=0),
    usage: Optional[str] = Query(None, description="Filter by usage: Active, Standby, Seasonal"),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    """
    Get active reasoning patterns and their performance metrics.
    
    Returns information about AI reasoning patterns currently in use,
    their accuracy rates, and usage statistics.
    """
    
    patterns = generate_mock_patterns(limit, offset)
    
    # Apply usage filter if provided
    if usage:
        patterns = [p for p in patterns if p.usage.lower() == usage.lower()]
    
    return ReasoningPatternResponse(
        items=patterns,
        total=len(patterns) + offset,  # Mock total
        limit=limit,
        offset=offset
    )

@router.get("/insights", response_model=AIInsightResponse)
async def get_ai_insights(
    limit: int = Query(5, ge=1, le=20),
    insight_type: Optional[str] = Query(None, description="Filter by type: market, customer, product, risk"),
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    """
    Get latest AI-generated business insights and recommendations.
    
    Returns actionable insights generated by AI analysis of business data,
    market trends, and customer behavior patterns.
    """
    
    mock_insights = [
        {
            "insight_type": "market",
            "title": "Emerging Market Opportunity",
            "description": "Analysis shows 34% growth potential in eco-friendly product segment. Competitor gap identified in premium sustainable goods.",
            "confidence": 0.87,
            "created_at": datetime.now() - timedelta(hours=2),
            "tags": ["market_expansion", "sustainability", "premium_segment"]
        },
        {
            "insight_type": "customer",
            "title": "High-Value Customer Pattern",
            "description": "Customers who purchase on weekends show 23% higher repeat purchase rate. Weekend promotions could increase retention.",
            "confidence": 0.91,
            "created_at": datetime.now() - timedelta(hours=6),
            "tags": ["customer_behavior", "retention", "timing"]
        },
        {
            "insight_type": "product",
            "title": "Cross-Sell Opportunity",
            "description": "Product bundle analysis reveals 67% of customers buying Item A also need Item B within 30 days. Bundle recommendation implemented.",
            "confidence": 0.84,
            "created_at": datetime.now() - timedelta(hours=12),
            "tags": ["cross_sell", "bundling", "product_affinity"]
        },
        {
            "insight_type": "risk",
            "title": "Supply Chain Alert",
            "description": "Predictive model indicates 78% probability of shipping delays from primary supplier next month. Diversification recommended.",
            "confidence": 0.78,
            "created_at": datetime.now() - timedelta(hours=18),
            "tags": ["supply_chain", "risk_management", "supplier_diversification"]
        }
    ]
    
    insights = [AIInsight(**insight) for insight in mock_insights[:limit]]
    
    # Apply type filter if provided
    if insight_type:
        insights = [i for i in insights if i.insight_type == insight_type]
    
    return AIInsightResponse(
        items=insights,
        total=len(insights)
    )

@router.get("/health")
async def get_ai_health(
    scope: SubjectScope = Depends(get_subject_scope_optional),
):
    """
    Get AI system health and performance metrics.
    
    Returns overall health status of AI decision-making systems,
    including model performance, processing times, and error rates.
    """
    
    return {
        "ok": True,
        "status": "healthy",
        "models_active": 12,
        "decisions_per_hour": 47,
        "avg_confidence": 0.86,
        "error_rate": 0.02,
        "processing_time_ms": 145,
        "last_model_update": datetime.now() - timedelta(hours=4),
        "brain_status": {
            "pricing_brain": "active",
            "inventory_brain": "active", 
            "marketing_brain": "active",
            "customer_brain": "active",
            "supply_brain": "active"
        }
    }
