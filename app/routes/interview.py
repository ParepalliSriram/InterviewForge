import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, status
from bson import ObjectId
from app.database import get_db
from app.models import InterviewSetupRequest, InterviewSubmitRequest, ReportResponse
from app.services.ai.provider_manager import ai_manager
from app.services.resume import extract_resume_summary
from app.auth import get_current_user_id

logger = logging.getLogger("app.routes.interview")
router = APIRouter(prefix="/api/interview", tags=["interview"])

@router.post("/setup")
async def setup_interview(payload: InterviewSetupRequest):
    """
    Sets up an interview session by parsing resume (if provided) 
    and generating 5 unique questions via the fallback-capable AI manager.
    """
    resume_summary = None
    if payload.resume_text:
        try:
            logger.info("Extracting resume summary locally...")
            resume_summary = extract_resume_summary(payload.resume_text)
            logger.info(f"Resume summary extracted: {resume_summary[:100]}...")
        except Exception as e:
            logger.error(f"Failed to parse resume: {e}")
            # Non-blocking fallback: proceed without resume context
            pass

    try:
        # Call the AI provider via abstraction
        provider = ai_manager.get_provider()
        questions = await provider.generate_questions(
            role=payload.role,
            experience=payload.experience,
            interview_type=payload.interview_type,
            resume_summary=resume_summary
        )
        return {
            "questions": questions,
            "role": payload.role,
            "experience": payload.experience,
            "interview_type": payload.interview_type
        }
    except Exception as e:
        logger.error(f"Interview setup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions. Error: {str(e)}"
        )

@router.post("/submit")
async def submit_interview(
    payload: InterviewSubmitRequest,
    request: Request,
    db=Depends(get_db)
):
    """
    Evaluates the answers in a single pass batch request.
    Persists data if user is logged in; guest flow remains stateless.
    """
    # Extract questions and answers as lists
    questions = [a.question for a in payload.answers]
    answers = [a.answer for a in payload.answers]

    if len(questions) == 0:
        raise HTTPException(status_code=400, detail="No answers provided.")

    try:
        provider = ai_manager.get_provider()
        report = await provider.evaluate_interview(
            role=payload.role,
            experience=payload.experience,
            interview_type=payload.interview_type,
            questions=questions,
            answers=answers
        )
    except Exception as e:
        logger.error(f"Interview evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate interview answers. Error: {str(e)}"
        )

    # Check session auth
    user_id_str = await get_current_user_id(request)
    saved = False
    session_id_str = None

    if user_id_str:
        try:
            user_id = ObjectId(user_id_str)
            final_score = int(report.get("final_score", 0))
            
            # 1. Store Interview Session metadata (excluding questions and answers)
            session_doc = {
                "user_id": user_id,
                "role": payload.role,
                "interview_type": payload.interview_type,
                "experience_level": payload.experience,
                "final_score": final_score,
                "completed_at": datetime.utcnow()
            }
            session_res = await db.sessions.insert_one(session_doc)
            session_id_str = str(session_res.inserted_id)

            # 2. Store Interview Report (No summary stored, matching user request comment)
            report_doc = {
                "session_id": session_res.inserted_id,
                "technical_score": int(report.get("technical_score", 0)),
                "problem_solving_score": int(report.get("problem_solving_score", 0)),
                "strengths": report.get("strengths", []),
                "weaknesses": report.get("weaknesses", []),
                "recommended_topics": report.get("recommended_topics", [])
            }
            await db.reports.insert_one(report_doc)

            # 3. Update User Analytics Collection
            topics_evaluated = report.get("topics_evaluated", {})
            if not topics_evaluated:
                # Fallback to role name as a topic if AI did not return topics
                topics_evaluated = {payload.role: final_score}

            await update_user_analytics(db, user_id_str, topics_evaluated)
            saved = True
            logger.info(f"Successfully saved interview session {session_id_str} and report for user {user_id_str}")
        except Exception as db_err:
            logger.error(f"Database storage failed for registered user: {db_err}")
            # Non-blocking database failure: return report to user anyway
            pass

    return {
        "saved": saved,
        "session_id": session_id_str,
        "report": {
            "technical_score": report.get("technical_score", 0),
            "problem_solving_score": report.get("problem_solving_score", 0),
            "final_score": report.get("final_score", 0),
            "strengths": report.get("strengths", []),
            "weaknesses": report.get("weaknesses", []),
            "recommended_topics": report.get("recommended_topics", [])
        }
    }

async def update_user_analytics(db, user_id_str: str, topics_evaluated: dict):
    """
    Updates the running averages and attempts of specific topics in the analytics collection.
    """
    user_id = ObjectId(user_id_str)
    analytics_doc = await db.analytics.find_one({"user_id": user_id})
    if not analytics_doc:
        analytics_doc = {"user_id": user_id, "topic_stats": {}}
        await db.analytics.insert_one(analytics_doc)

    topic_stats = analytics_doc.get("topic_stats", {})

    for topic, score in topics_evaluated.items():
        topic_clean = topic.strip()
        if not topic_clean:
            continue
        
        try:
            score_val = float(score)
        except (ValueError, TypeError):
            score_val = 0.0

        if topic_clean in topic_stats:
            stats = topic_stats[topic_clean]
            attempts = int(stats.get("attempts", 0))
            avg_score = float(stats.get("average_score", 0.0))
            
            new_attempts = attempts + 1
            new_avg = ((avg_score * attempts) + score_val) / new_attempts
            topic_stats[topic_clean] = {
                "attempts": new_attempts,
                "average_score": round(new_avg, 2)
            }
        else:
            topic_stats[topic_clean] = {
                "attempts": 1,
                "average_score": round(score_val, 2)
            }

    await db.analytics.update_one(
        {"user_id": user_id},
        {"$set": {"topic_stats": topic_stats}}
    )
