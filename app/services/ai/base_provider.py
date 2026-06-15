from abc import ABC, abstractmethod
from typing import List, Optional

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_questions(
        self, role: str, experience: str, interview_type: str, resume_summary: Optional[str] = None
    ) -> List[str]:
        """
        Generate 5 unique interview questions based on the role, experience level, 
        interview type, and optional resume context.
        """
        pass

    @abstractmethod
    async def evaluate_interview(
        self, role: str, experience: str, interview_type: str, questions: List[str], answers: List[str]
    ) -> dict:
        """
        Perform a single-pass evaluation of all user answers in one batch API request.
        Returns a dict conforming to the evaluation schema.
        """
        pass
