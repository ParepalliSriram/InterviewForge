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

Evaluation Guidelines:
- CRITICAL: Assess how well and correctly each answer addresses its respective question. Perfect, relevant, and well-explained answers should receive high/full marks.
- CRITICAL: Answers that are extremely brief (e.g., 'yes', 'no', 'okay', 'agree', 'skip', 'don't know', 'none'), irrelevant to the question, empty, or nonsensical must receive a score of 0 for that question/topic.
- CRITICAL: For questions requiring explanations or descriptions (like "Describe a time...", "Explain standard...", "How do you handle..."), one-word or simple affirmative/negative answers (like "yes", "no", "okay") must be scored as 0. Do NOT award points for positive-sounding but empty answers.
- CRITICAL: The overall "score" (0-100), "technical" rating (0-10), and "problem_solving" rating (0-10) must be a direct mathematical reflection of the answers' quality. Do not inflate scores. If all or most answers are irrelevant, extremely brief, or incorrect, the final scores must be 0 (or close to 0, e.g. <= 5).
- CRITICAL: Keep feedback extremely brief to minimize token usage:
  * Limit 'strengths', 'weaknesses', and 'recommended_topics' to a maximum of 2 items each. This is a strict limit.
  * Keep each item under 10 words. Avoid verbose explanations.
  * If the candidate provided no substantial answers, do NOT hallucinate strengths (e.g. do not say "Explains standard inheritance" if they only answered "yes"). Under strengths, list only one item: "None".

Provide a single-pass feedback report in this strict JSON format.

Example evaluation for a poor response:
If the User Q&A was:
"Question 1: Explain standard inheritance in Python.
Answer 1: yes
Question 2: Describe a time you resolved a performance bottleneck.
Answer 2: okay"

The corresponding JSON output would be:
{{
  "score": 0,
  "technical": 0,
  "problem_solving": 0,
  "strengths": ["None"],
  "weaknesses": ["Failed to explain Python inheritance", "Did not describe a performance bottleneck"],
  "recommended_topics": ["Python inheritance", "Performance optimization"],
  "topics_evaluated": {{
     "Python Standard Inheritance": 0,
     "Performance Bottleneck": 0
  }}
}}

Generate the JSON report for the actual interview conforming to this schema:
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
                    {
                        "role": "system",
                        "content": (
                            "You are a strict, precise technical evaluator. You grade answers strictly based on relevance, detail, and accuracy. "
                            "Extremely brief answers (like 'yes', 'no', 'okay') or irrelevant answers must be scored as 0. Do not inflate scores. "
                            "Keep feedback brief and token-efficient. If an answer consists of single words like 'yes', 'no', 'okay', 'skip', etc. "
                            "without any description, it must receive a score of 0 and must not be considered a strength."
                        )
                    },
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
            data["final_score"] = int(data.get("score", 0))
            data["technical_score"] = int(data.get("technical", 0))
            data["problem_solving_score"] = int(data.get("problem_solving", 0))
            
            if "topics_evaluated" not in data:
                data["topics_evaluated"] = {}

            return data
        except Exception as e:
            logger.error(f"OpenAI evaluate_interview failed: {e}")
            raise e
