import json
import logging
import warnings

# Suppress the deprecation warning from the google.generativeai package
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from typing import List, Optional
from app.services.ai.base_provider import BaseAIProvider
from app.config import settings

logger = logging.getLogger("app.ai.gemini")

class GeminiProvider(BaseAIProvider):
    def __init__(self):
        self.api_key = settings.gemini_key
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _get_model(self):
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")
        return genai.GenerativeModel("gemini-1.5-flash")

    async def generate_questions(
        self, role: str, experience: str, interview_type: str, resume_summary: Optional[str] = None
    ) -> List[str]:
        model = self._get_model()
        resume_context = f"\nResume context (tailor questions to these skills/projects):\n{resume_summary}" if resume_summary else ""
        
        prompt = f"""
You are an expert interviewer. Generate 5 unique, realistic interview questions for:
Role: {role}
Experience Level: {experience}
Interview Type: {interview_type}
{resume_context}

Respond ONLY with a JSON array of strings containing the questions. Do not include markdown formatting or backticks around the JSON.
Example output:
[
  "Explain standard inheritance in Python and how super() is used.",
  "How do you handle DB transaction rollbacks in FastAPI?",
  "What is the difference between SQL and NoSQL databases like MongoDB?",
  "Describe a time you resolved a performance bottleneck in code.",
  "How do you approach writing clean unit tests?"
]
"""
        try:
            logger.info("Calling Gemini API to generate questions...")
            response = await model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            text = response.text.strip()
            data = json.loads(text)
            if isinstance(data, list) and len(data) >= 5:
                return [str(q) for q in data[:5]]
            raise ValueError("Questions response is not a list of 5 elements.")
        except Exception as e:
            logger.error(f"Gemini generate_questions failed: {e}")
            raise e

    async def evaluate_interview(
        self, role: str, experience: str, interview_type: str, questions: List[str], answers: List[str]
    ) -> dict:
        model = self._get_model()
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
            logger.info("Calling Gemini API to evaluate interview...")
            response = await model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            text = response.text.strip()
            data = json.loads(text)
            
            # Normalization
            required_keys = ["score", "technical", "problem_solving", "strengths", "weaknesses", "recommended_topics"]
            for r_key in required_keys:
                if r_key not in data:
                    data[r_key] = [] if isinstance(data.get(r_key), list) else 0

            # Ensure final_score exists (mapping score -> final_score)
            data["final_score"] = int(data.get("score", 0))
            data["technical_score"] = int(data.get("technical", 0))
            data["problem_solving_score"] = int(data.get("problem_solving", 0))
            
            if "topics_evaluated" not in data:
                data["topics_evaluated"] = {}

            return data
        except Exception as e:
            logger.error(f"Gemini evaluate_interview failed: {e}")
            raise e
