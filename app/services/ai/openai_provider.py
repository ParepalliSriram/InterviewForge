import json
import logging
from typing import List, Optional
from openai import AsyncOpenAI
from app.services.ai.base_provider import BaseAIProvider
from app.config import settings

logger = logging.getLogger("app.ai.openai")

class OpenAIProvider(BaseAIProvider):
    def __init__(self):
        self.api_key = settings.openai_key
        self.client = None
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)

    def _get_client(self) -> AsyncOpenAI:
        if not self.client:
            raise ValueError("OpenAI API key is not configured.")
        return self.client

    async def generate_questions(
        self, role: str, experience: str, interview_type: str, resume_summary: Optional[str] = None
    ) -> List[str]:
        client = self._get_client()
        resume_context = f"\nResume context (tailor questions to these skills/projects):\n{resume_summary}" if resume_summary else ""

        prompt = f"""
You are an expert interviewer. Generate 5 unique, realistic interview questions for:
Role: {role}
Experience Level: {experience}
Interview Type: {interview_type}
{resume_context}

Respond ONLY with a JSON object containing a key "questions" which is an array of 5 strings.
Example:
{{
  "questions": [
    "Question 1",
    "Question 2",
    "Question 3",
    "Question 4",
    "Question 5"
  ]
}}
"""
        try:
            logger.info("Calling OpenAI API to generate questions...")
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional hiring manager."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            data = json.loads(text)
            questions = data.get("questions")
            if isinstance(questions, list) and len(questions) >= 5:
                return [str(q) for q in questions[:5]]
            raise ValueError("Unexpected JSON response structure or insufficient questions.")
        except Exception as e:
            logger.error(f"OpenAI generate_questions failed: {e}")
            raise e

    async def evaluate_interview(
        self, role: str, experience: str, interview_type: str, questions: List[str], answers: List[str]
    ) -> dict:
        client = self._get_client()
        q_and_a_lines = []
        for idx, (q, a) in enumerate(zip(questions, answers)):
            q_and_a_lines.append(f"Question {idx+1}: {q}\nAnswer {idx+1}: {a}")
        q_and_a_text = "\n\n".join(q_and_a_lines)

        prompt = f"""
You are an expert AI interviewer and technical evaluator. Evaluate the following interview:
Role: {role}
Experience Level: {experience}
Interview Type: {interview_type}

User Answers:
{q_and_a_text}

Provide a single-pass feedback report in this strict JSON format:
{{
  "score": <integer score from 0 to 100>,
  "technical": <integer rating out of 10>,
  "problem_solving": <integer rating out of 10>,
  "strengths": [<list of key strengths observed>],
  "weaknesses": [<list of improvement areas>],
  "recommended_topics": [<list of specific topics to study next>],
  "topics_evaluated": {{
     "<TopicName1>": <integer score 0 to 100 for this topic>,
     "<TopicName2>": <integer score 0 to 100 for this topic>
  }}
}}

Make sure your JSON is valid, contains all required keys, and does not include extra text.
"""
        try:
            logger.info("Calling OpenAI API to evaluate interview...")
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional technical evaluator."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            data = json.loads(text)

            # Normalization
            required_keys = ["score", "technical", "problem_solving", "strengths", "weaknesses", "recommended_topics"]
            for r_key in required_keys:
                if r_key not in data:
                    data[r_key] = [] if isinstance(data.get(r_key), list) else 0

            # Map fields for database
            data["final_score"] = int(data.get("score", 70))
            data["technical_score"] = int(data.get("technical", 7))
            data["problem_solving_score"] = int(data.get("problem_solving", 7))
            
            if "topics_evaluated" not in data:
                data["topics_evaluated"] = {}

            return data
        except Exception as e:
            logger.error(f"OpenAI evaluate_interview failed: {e}")
            raise e
