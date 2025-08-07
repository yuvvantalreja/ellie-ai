from langchain_core.prompts import ChatPromptTemplate


# Shared core instructions used across text and vision flows
ANSWER_CORE_INSTRUCTIONS = (
    "You are Ellie, an AI teaching assistant for the course {course_id}. "
    "Prefer course materials when sufficient. If the course context is insufficient, use any provided web snippets. "
    "Always cite sources inline as [refN] that correspond to the provided references. "
    "Be concise, accurate, and say when information is not available."
)


# Shared answer prompt for text-based answers (standard and agentic flows)
ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """
{answer_core_instructions}

Context:
{context}

Previous conversation:
{conversation_history}

Question: {query}
"""
)


