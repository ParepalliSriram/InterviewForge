from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional
from datetime import datetime

# Auth Models
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime

class UserUpdateUsername(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

# Interview Models
class InterviewSetupRequest(BaseModel):
    role: str = Field(..., description="e.g. Python Developer, Frontend Developer")
    experience: str = Field(..., description="e.g. Fresher, 1-3, 3-5, Senior")
    interview_type: str = Field(..., description="Technical, HR, Mixed")
    resume_text: Optional[str] = None

class AnswerSubmission(BaseModel):
    question: str
    answer: str

class InterviewSubmitRequest(BaseModel):
    role: str
    experience: str
    interview_type: str
    answers: List[AnswerSubmission]

# Report and Analytics Models
class ReportResponse(BaseModel):
    technical_score: int  # 1-10
    problem_solving_score: int  # 1-10
    final_score: int  # 1-100
    strengths: List[str]
    weaknesses: List[str]
    recommended_topics: List[str]

class SessionResponse(BaseModel):
    id: str
    role: str
    interview_type: str
    experience_level: str
    final_score: int
    completed_at: datetime
    report: Optional[ReportResponse] = None

class TopicStat(BaseModel):
    attempts: int
    average_score: float

class AnalyticsResponse(BaseModel):
    total_interviews: int
    average_score: float
    best_score: int
    topic_stats: Dict[str, TopicStat]
    strong_areas: List[str]
    weak_areas: List[str]
    recommendations: List[str]
