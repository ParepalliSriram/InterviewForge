import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from bson import ObjectId
from app.database import get_db
from app.auth import require_user_id

logger = logging.getLogger("app.routes.dashboard")
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary")
async def get_dashboard_summary(request: Request, user_id_str: str = Depends(require_user_id), db=Depends(get_db)):
    """
    Computes dashboard analytics: overview metrics, recent activity, 
    strong/weak skill areas, and aggregated study recommendations.
    """
    user_id = ObjectId(user_id_str)
    
    # 1. Fetch sessions
    sessions_cursor = db.sessions.find({"user_id": user_id}).sort("completed_at", -1)
    sessions = await sessions_cursor.to_list(length=100)
    
    total_interviews = len(sessions)
    if total_interviews == 0:
        return {
            "total_interviews": 0,
            "average_score": 0,
            "best_score": 0,
            "topic_stats": {},
            "strong_areas": [],
            "weak_areas": [],
            "recommendations": [],
            "recent_activity": []
        }

    scores = [s.get("final_score", 0) for s in sessions]
    average_score = round(sum(scores) / total_interviews, 1)
    best_score = max(scores)

    # 2. Fetch Topic stats from analytics
    analytics_doc = await db.analytics.find_one({"user_id": user_id})
    topic_stats = {}
    if analytics_doc:
        topic_stats = analytics_doc.get("topic_stats", {})

    # Derive Strong/Weak Areas (Strong: >= 75, Weak: < 75)
    strong_areas = []
    weak_areas = []
    for topic, stats in topic_stats.items():
        avg = stats.get("average_score", 0.0)
        if avg >= 75.0:
            strong_areas.append(topic)
        else:
            weak_areas.append(topic)

    # 3. Aggregate study recommendations from recent reports
    session_ids = [s["_id"] for s in sessions[:5]]  # limit to last 5 sessions
    reports_cursor = db.reports.find({"session_id": {"$in": session_ids}})
    reports = await reports_cursor.to_list(length=10)
    
    recommendations_set = set()
    for rep in reports:
        for rec in rep.get("recommended_topics", []):
            recommendations_set.add(rec.strip())
            
    recent_activity = []
    for s in sessions[:5]:
        recent_activity.append({
            "id": str(s["_id"]),
            "role": s.get("role"),
            "interview_type": s.get("interview_type"),
            "experience_level": s.get("experience_level"),
            "final_score": s.get("final_score"),
            "completed_at": s.get("completed_at").isoformat()
        })

    return {
        "total_interviews": total_interviews,
        "average_score": average_score,
        "best_score": best_score,
        "topic_stats": topic_stats,
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "recommendations": list(recommendations_set)[:8],  # limit to top 8 unique recommendations
        "recent_activity": recent_activity
    }

@router.get("/history")
async def get_interview_history(request: Request, user_id_str: str = Depends(require_user_id), db=Depends(get_db)):
    """
    Returns full list of completed sessions with their detailed score sheets.
    """
    user_id = ObjectId(user_id_str)
    
    # Fetch sessions
    sessions_cursor = db.sessions.find({"user_id": user_id}).sort("completed_at", -1)
    sessions = await sessions_cursor.to_list(length=100)
    
    history_items = []
    for s in sessions:
        report = await db.reports.find_one({"session_id": s["_id"]})
        history_items.append({
            "session_id": str(s["_id"]),
            "role": s.get("role"),
            "interview_type": s.get("interview_type"),
            "experience_level": s.get("experience_level"),
            "final_score": s.get("final_score"),
            "completed_at": s.get("completed_at").isoformat(),
            "report": {
                "technical_score": report.get("technical_score", 0) if report else 0,
                "problem_solving_score": report.get("problem_solving_score", 0) if report else 0,
                "strengths": report.get("strengths", []) if report else [],
                "weaknesses": report.get("weaknesses", []) if report else [],
                "recommended_topics": report.get("recommended_topics", []) if report else []
            } if report else None
        })

    return history_items
