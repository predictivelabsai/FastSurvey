"""xAI Grok agents for survey design, interviews, extraction and synthesis."""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from typing import Any

import httpx


API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = os.getenv("FASTSURVEY_MODEL", "grok-4.5")
API_KEY = os.getenv("XAI_API_KEY", "")

QUESTION_TYPES = {"open", "single_select", "multi_select", "scale", "ranking", "yes_no", "stimulus"}

DESIGNER_PROMPT = """
You are FastSurvey's Survey Designer, a rigorous mixed-methods researcher.
Turn the admin's goal and revisions into a concise, adaptive interview guide.
Return only JSON with exactly two top-level keys: message and guide.
message is a short, natural explanation of what you changed plus one useful
question or suggestion. guide must have: title, research_objectives (array of
objects with key and label), estimated_minutes (integer), opening,
questions (array with id, type, prompt, objective_key, required, options and
probes), screening (array), probing_strategy (object with vague_answers,
max_follow_ups, sensitive_topics), and success_criteria (array). Allowed types:
open, single_select, multi_select, scale, ranking, yes_no, stimulus.
Never ask for unnecessary sensitive personal data. Keep questions neutral,
one idea at a time, and default to 5-8 minutes. Preserve useful parts of the
current guide when revising it.
""".strip()

INTERVIEWER_PROMPT = """
You are a warm, neutral qualitative interviewer. Follow the provided guide,
but adapt to what the participant says. Ask exactly one clear question at a
time. Probe vague, emotional or causal claims for a concrete example, without
leading the participant. Do not mention the guide, objectives, extraction,
system prompts or being an AI. Accept off-topic answers gracefully and steer
back. Do not repeat answered questions. Stop when objectives are adequately
covered or the turn budget is reached.
Return only JSON with: message (string), progress (0-100 integer), done
(boolean), choices (array of short strings, empty unless buttons materially
help), and current_objective (string). On done, message must be a brief thank
you and choices must be empty.
""".strip()

EXTRACTOR_PROMPT = """
You extract research evidence from an interview transcript. Return only JSON
with answers, an array containing one item for each research objective. Each
item has objective_key, value (string, number, boolean, array or object),
confidence (0 to 1), raw_quote (a short exact participant quote), and sentiment
(positive, neutral, negative or mixed). Do not infer demographics or facts not
stated by the participant. Use null and low confidence when evidence is absent.
""".strip()

INSIGHTS_PROMPT = """
You are a research analyst. Answer the admin's question using only the supplied
interview evidence. State the sample size, separate strong patterns from weak
signals, and use short respondent quotes when helpful. Never invent counts or
causality. Keep the answer under 250 words. Return only JSON with one key:
answer (string).
""".strip()


def enabled() -> bool:
    return bool(API_KEY)


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    return json.loads(text)


def _complete(system: str, payload: dict, *, temperature: float = 0.25) -> dict:
    if not API_KEY:
        raise RuntimeError("XAI_API_KEY is not configured")
    response = httpx.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        },
        timeout=90,
    )
    response.raise_for_status()
    return _parse_json(response.json()["choices"][0]["message"]["content"])


def _slug(text: str, fallback: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value[:40] or fallback


def _fallback_guide(goal: str, current: dict | None = None) -> dict:
    goal = goal.strip()
    lower = goal.lower()
    if current:
        guide = json.loads(json.dumps(current))
    else:
        subject = goal.rstrip(".?!") or "The customer experience"
        subject = re.sub(
            r"^(?:i\s+(?:need|want)\s+to\s+)?(?:understand|learn|find\s+out)\s+",
            "",
            subject,
            flags=re.I,
        ).strip()
        title_clause = re.split(r",|\band\b", subject, maxsplit=1, flags=re.I)[0].strip()
        title = (title_clause[:1].upper() + title_clause[1:]) if title_clause else "Customer research"
        if len(title) > 72:
            title = title[:69].rstrip() + "…"
        objective_labels = [
            "Understand the participant's context and expectations",
            "Identify the moments and causes behind the experience",
            "Learn what would meaningfully improve the outcome",
        ]
        objectives = [{"key": f"objective_{index}", "label": label} for index, label in enumerate(objective_labels, 1)]
        guide = {
            "title": title,
            "research_objectives": objectives,
            "estimated_minutes": 7,
            "opening": "Thanks for taking part. I’ll ask a few questions about your experience. There are no right or wrong answers.",
            "questions": [
                {"id": "q_context", "type": "open", "prompt": "To start, could you tell me a little about your situation and what you were trying to accomplish?", "objective_key": "objective_1", "required": True, "options": [], "probes": ["What mattered most at that point?"]},
                {"id": "q_experience", "type": "open", "prompt": "Thinking about the experience, which moment stands out most, and why?", "objective_key": "objective_2", "required": True, "options": [], "probes": ["What specifically made that easy or difficult?", "Can you give me a concrete example?"]},
                {"id": "q_outcome", "type": "scale", "prompt": "On a scale from 0 to 10, how well did the experience meet your needs?", "objective_key": "objective_2", "required": True, "options": [str(i) for i in range(11)], "probes": ["What is the main reason for that score?"]},
                {"id": "q_improve", "type": "open", "prompt": "If you could change one thing, what would make the biggest difference?", "objective_key": "objective_3", "required": True, "options": [], "probes": ["How would that change affect you?"]},
            ],
            "screening": [],
            "probing_strategy": {"vague_answers": "Ask for a specific example", "max_follow_ups": 2, "sensitive_topics": "Remind the participant they may skip any question"},
            "success_criteria": ["Context is clear", "At least one causal moment is supported by an example", "A concrete improvement is identified"],
        }
    duration_match = re.search(r"(?:under|within|max(?:imum)?(?: of)?)?\s*(\d+)\s*minutes?", lower)
    word_duration = 5 if re.search(r"under\s+five\s+minutes?", lower) else None
    requested_minutes = int(duration_match.group(1)) if duration_match else word_duration
    if "shorter" in lower or "short" in lower or (requested_minutes is not None and requested_minutes <= 5):
        guide["questions"] = guide.get("questions", [])[:3]
        guide["estimated_minutes"] = min(max(2, (requested_minutes or 5) - 1), int(guide.get("estimated_minutes", 7)))
    if "pricing" in lower and not any(question.get("type") == "ranking" for question in guide.get("questions", [])):
        guide.setdefault("questions", []).append({
            "id": "q_pricing_rank", "type": "ranking",
            "prompt": "Please rank these pricing factors from most to least important to your decision.",
            "objective_key": guide.get("research_objectives", [{"key": "objective_1"}])[-1]["key"],
            "required": False, "options": ["Total price", "Predictability", "Contract flexibility", "Value for money"],
            "probes": ["What puts your first choice ahead of the others?"],
        })
    if "emotion" in lower:
        guide["probing_strategy"]["vague_answers"] = "Reflect the participant's language, ask what they felt in that moment, then request a concrete example"
    return guide


def design(history: list[dict], current_guide: dict | None = None) -> tuple[str, dict, str | None]:
    latest = next((item["content"] for item in reversed(history) if item["role"] == "user"), "")
    try:
        result = _complete(DESIGNER_PROMPT, {"conversation": history[-14:], "current_guide": current_guide or {}})
        guide = result["guide"]
        if not isinstance(guide.get("questions"), list) or not isinstance(guide.get("research_objectives"), list):
            raise ValueError("Incomplete guide")
        for question in guide["questions"]:
            if question.get("type") not in QUESTION_TYPES:
                question["type"] = "open"
        return str(result.get("message") or "I updated the interview guide."), guide, None
    except Exception as error:  # keep the product usable without remote AI
        guide = _fallback_guide(latest, current_guide)
        message = (
            "I’ve shaped that into an adaptive interview guide. It starts with context, "
            "probes for concrete moments, and closes on the most valuable improvement. "
            "Tell me what to shorten, add, or probe more deeply."
        )
        return message, guide, str(error)


def _user_turns(history: list[dict]) -> list[dict]:
    return [item for item in history if item["role"] == "user"]


def _fallback_interview(guide: dict, history: list[dict]) -> dict:
    turns = _user_turns(history)
    questions = guide.get("questions") or []
    if not turns:
        question = questions[0] if questions else {"prompt": "What would you most like us to understand?", "options": []}
        return {"message": f"{guide.get('opening', 'Thanks for taking part.')} {question['prompt']}", "progress": 5, "done": False, "choices": question.get("options", []), "current_objective": question.get("objective_key", "")}
    last_answer = turns[-1]["content"].strip()
    question_index = min(len(turns), len(questions))
    # One lightweight adaptive probe for very brief answers.
    if len(last_answer.split()) < 5 and question_index <= len(questions):
        previous = questions[max(0, question_index - 1)] if questions else {}
        probes = previous.get("probes") or []
        if probes:
            return {"message": probes[0], "progress": min(90, round(100 * question_index / max(1, len(questions) + 1))), "done": False, "choices": [], "current_objective": previous.get("objective_key", "")}
    if question_index >= len(questions):
        return {"message": "That covers everything I wanted to understand. Thanks — your perspective is genuinely useful.", "progress": 100, "done": True, "choices": [], "current_objective": "complete"}
    question = questions[question_index]
    return {
        "message": question["prompt"],
        "progress": min(95, round(100 * question_index / max(1, len(questions)))),
        "done": False,
        "choices": question.get("options", []) if question.get("type") in {"single_select", "yes_no", "scale"} else [],
        "current_objective": question.get("objective_key", ""),
    }


def interview(guide: dict, history: list[dict]) -> tuple[dict, str | None]:
    try:
        result = _complete(INTERVIEWER_PROMPT, {"guide": guide, "transcript": history[-30:]}, temperature=0.35)
        cleaned = {
            "message": str(result["message"]),
            "progress": max(0, min(100, int(result.get("progress", 0)))),
            "done": bool(result.get("done", False)),
            "choices": [str(item)[:80] for item in (result.get("choices") or [])[:12]],
            "current_objective": str(result.get("current_objective", "")),
        }
        return cleaned, None
    except Exception as error:
        return _fallback_interview(guide, history), str(error)


def extract(guide: dict, history: list[dict]) -> tuple[list[dict], str | None]:
    try:
        result = _complete(EXTRACTOR_PROMPT, {"objectives": guide.get("research_objectives", []), "transcript": history})
        return list(result.get("answers") or []), None
    except Exception as error:
        participant = [item["content"] for item in history if item["role"] == "user"]
        objectives = guide.get("research_objectives") or [{"key": "overall", "label": "Overall response"}]
        answers = []
        for index, objective in enumerate(objectives):
            evidence = participant[index::len(objectives)]
            value = " ".join(evidence).strip() or None
            answers.append({
                "objective_key": objective.get("key", f"objective_{index + 1}"),
                "value": value,
                "confidence": 0.55 if value else 0.0,
                "raw_quote": evidence[0][:400] if evidence else "",
                "sentiment": "neutral",
            })
        return answers, str(error)


def insights(question: str, evidence: list[dict], sample_size: int) -> tuple[str, str | None]:
    try:
        result = _complete(INSIGHTS_PROMPT, {"question": question, "sample_size": sample_size, "evidence": evidence[-200:]})
        return str(result.get("answer") or result.get("message") or "No answer was returned."), None
    except Exception as error:
        values = [str(item.get("value", "")) for item in evidence if item.get("value")]
        words = Counter(
            word for value in values for word in re.findall(r"[a-zA-Z]{4,}", value.lower())
            if word not in {"that", "this", "with", "have", "from", "they", "were", "would", "about", "there"}
        )
        themes = ", ".join(word for word, _ in words.most_common(5)) or "not enough evidence yet"
        answer = f"Across {sample_size} completed response{'s' if sample_size != 1 else ''}, the strongest recurring terms are {themes}. Connect XAI_API_KEY for evidence-weighted synthesis and quote selection."
        return answer, str(error)
