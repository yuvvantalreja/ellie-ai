import json
import os
import datetime as dt
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


class QueryRouter:
    """LLM-based router that decides whether to use course docs, web search, or both."""

    def __init__(self, model_name: Optional[str] = None, groq_api_key: Optional[str] = None) -> None:
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.model_name = model_name or os.getenv("GROQ_MODEL", "llama3-70b-8192")
        self.llm = ChatGroq(api_key=api_key, model_name=self.model_name, temperature=0)

        self.prompt = ChatPromptTemplate.from_template(
            """
System: You are a routing controller for an AI teaching assistant for course {course_id}. Decide whether to answer using course materials, web search, or both. Prefer course materials when sufficient. Use web for recency/external facts or when course coverage is weak.

Today's date: {today}

User query:
{query}

Recent conversation (brief):
{history_summary}

Course retrieval preview (top 3):
{retrieval_preview}

Return strict JSON only with keys exactly as follows:
{{
  "decision": "course_only" | "web_primary" | "course_then_web",
  "reasons": "short rationale",
  "k_course": 3,
  "k_web": 0,
  "web_queries": ["..."]
}}
            """
        )

    @staticmethod
    def build_preview(docs_with_scores: List[Any]) -> str:
        lines: List[str] = []
        for (doc, score) in docs_with_scores[:3]:
            meta = doc.metadata or {}
            title = meta.get("page_title") or meta.get("slide_title") or meta.get("title") or meta.get("file_name") or ""
            snippet = (doc.page_content or "").strip().replace("\n", " ")[:160]
            lines.append(f"- [score={score}] {title} — {snippet}")
        return "\n".join(lines) if lines else "(no matches)"

    def summarize_history(self, history: List[Dict[str, Any]], max_turns: int = 2) -> str:
        if not history:
            return "(no history)"
        last = history[-max_turns:]
        bits = []
        for m in last:
            role = m.get("role", "user")
            content = (m.get("content", "").strip().replace("\n", " ")[:120])
            bits.append(f"{role}: {content}")
        return " | ".join(bits)

    def route(self, *, course_id: str, query: str, history: List[Dict[str, Any]], docs_with_scores: List[Any]) -> Dict[str, Any]:
        today = dt.date.today().isoformat()
        history_summary = self.summarize_history(history)
        retrieval_preview = self.build_preview(docs_with_scores)

        msg = self.prompt.format_messages(
            course_id=course_id,
            today=today,
            query=query,
            history_summary=history_summary,
            retrieval_preview=retrieval_preview,
        )

        raw = self.llm.invoke(msg)
        text = raw.content if hasattr(raw, "content") else str(raw)
        print("LLM Decision: ", text)
        try:
            data = json.loads(text)
        except Exception:
            # Fallback to course_then_web with safe defaults
            data = {
                "decision": "course_then_web",
                "reasons": "fallback",
                "k_course": 4,
                "k_web": 2,
                "web_queries": [query],
            }
        # Coerce fields
        data.setdefault("decision", "course_then_web")
        data.setdefault("k_course", 4)
        data.setdefault("k_web", 0)
        if data.get("k_web", 0) > 0 and not data.get("web_queries"):
            data["web_queries"] = [query]
        return data


