import logging
from typing import List, Optional
from app.services.ai.base_provider import BaseAIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.groq_provider import GroqProvider
from app.config import settings

logger = logging.getLogger("app.ai.manager")

class FallbackProviderProxy(BaseAIProvider):
    def __init__(self):
        # Instantiate the providers
        self.providers = {
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "claude": ClaudeProvider(),
            "groq": GroqProvider()
        }

    def _get_provider_chain(self) -> List[str]:
        """
        Determines the priority order for providers. 
        Primary provider runs first, followed by others in Gemini -> OpenAI -> Claude -> Groq fallback order.
        """
        primary = settings.PRIMARY_PROVIDER.lower() if settings.PRIMARY_PROVIDER else "gemini"
        if primary not in self.providers:
            primary = "gemini"
        
        chain = [primary]
        fallback_order = ["gemini", "openai", "claude", "groq"]
        for p in fallback_order:
            if p not in chain:
                chain.append(p)
        return chain

    async def generate_questions(
        self, role: str, experience: str, interview_type: str, resume_summary: Optional[str] = None
    ) -> List[str]:
        chain = self._get_provider_chain()
        errors = []
        
        for provider_name in chain:
            provider = self.providers[provider_name]
            try:
                # Check if API key is present before attempting
                if provider_name == "gemini" and not settings.gemini_key:
                    raise ValueError("Gemini key is missing from configuration.")
                elif provider_name == "openai" and not settings.openai_key:
                    raise ValueError("OpenAI key is missing from configuration.")
                elif provider_name == "claude" and not settings.claude_key:
                    raise ValueError("Claude/Anthropic key is missing from configuration.")
                elif provider_name == "groq" and not settings.groq_key:
                    raise ValueError("Groq key is missing from configuration.")
                
                logger.info(f"Attempting generate_questions using provider: {provider_name}")
                questions = await provider.generate_questions(role, experience, interview_type, resume_summary)
                logger.info(f"Success: questions generated via provider: {provider_name}")
                return questions
            except Exception as e:
                logger.warning(f"AI Provider '{provider_name}' failed to generate questions: {e}")
                errors.append(f"{provider_name}: {str(e)}")
        
        raise RuntimeError(f"All AI providers failed to generate questions. Errors: {'; '.join(errors)}")

    async def evaluate_interview(
        self, role: str, experience: str, interview_type: str, questions: List[str], answers: List[str]
    ) -> dict:
        chain = self._get_provider_chain()
        errors = []
        
        for provider_name in chain:
            provider = self.providers[provider_name]
            try:
                # Check if API key is present before attempting
                if provider_name == "gemini" and not settings.gemini_key:
                    raise ValueError("Gemini key is missing from configuration.")
                elif provider_name == "openai" and not settings.openai_key:
                    raise ValueError("OpenAI key is missing from configuration.")
                elif provider_name == "claude" and not settings.claude_key:
                    raise ValueError("Claude/Anthropic key is missing from configuration.")
                elif provider_name == "groq" and not settings.groq_key:
                    raise ValueError("Groq key is missing from configuration.")

                logger.info(f"Attempting evaluate_interview using provider: {provider_name}")
                report = await provider.evaluate_interview(role, experience, interview_type, questions, answers)
                logger.info(f"Success: evaluation completed via provider: {provider_name}")
                return report
            except Exception as e:
                logger.warning(f"AI Provider '{provider_name}' failed to evaluate interview: {e}")
                errors.append(f"{provider_name}: {str(e)}")

        raise RuntimeError(f"All AI providers failed to evaluate interview. Errors: {'; '.join(errors)}")

class ProviderManager:
    def __init__(self):
        self._proxy = FallbackProviderProxy()

    def get_provider(self) -> BaseAIProvider:
        return self._proxy

ai_manager = ProviderManager()
