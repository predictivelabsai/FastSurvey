"""FastSurvey — conversational survey design, interviews and insight."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import os
import secrets
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

from fasthtml.common import fast_app, serve
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response

import ai
import auth
import db
import ui


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("fastsurvey")

PORT = int(os.getenv("FASTSURVEY_PORT", "5019"))
SECRET = os.getenv("FASTSURVEY_SECRET") or secrets.token_hex(32)

app, rt = fast_app(live=False, pico=False, secret_key=SECRET)
# FastHTML's optional static-file catch-all otherwise intercepts product routes
# ending in .csv, .json and .txt. FastSurvey uses no local static directory.
app.routes[:] = [route for route in app.routes if getattr(route, "name", "") != "static_route_exts_get"]


def current_user(session) -> dict | None:
    user_id = session.get("user_id")
    return db.row("SELECT * FROM users WHERE id=?", (user_id,)) if user_id else None


def require_user(session):
    user = current_user(session)
    return user, None if user else RedirectResponse("/login", status_code=303)


def owned_survey(session, survey_id: int):
    user = current_user(session)
    if not user:
        return None, None, RedirectResponse("/login", status_code=303)
    survey = db.get_survey(survey_id, user["id"])
    if not survey:
        return user, None, PlainTextResponse("Survey not found", status_code=404)
    return user, survey, None


@rt("/")
def get(session):
    user = current_user(session)
    if not user:
        return ui.landing_page()
    return ui.dashboard_page(user, db.list_surveys(user["id"]))


@rt("/surveys")
def get(session):
    user, redirect = require_user(session)
    if redirect:
        return redirect
    return ui.dashboard_page(user, db.list_surveys(user["id"]))


@rt("/login")
def get(session, error: str = ""):
    if current_user(session):
        return RedirectResponse("/", status_code=303)
    return ui.auth_page("login", error, auth.google_enabled())


@rt("/login")
def post(session, email: str = "", password: str = ""):
    user = auth.login(email, password)
    if not user:
        return ui.auth_page("login", "Email or password was not recognised.", auth.google_enabled())
    session.clear()
    session["user_id"] = user["id"]
    return RedirectResponse("/", status_code=303)


@rt("/register")
def get(session, error: str = ""):
    if current_user(session):
        return RedirectResponse("/", status_code=303)
    return ui.auth_page("register", error, auth.google_enabled())


@rt("/register")
def post(session, email: str = "", password: str = "", name: str = ""):
    user, error = auth.register(email, password, name)
    if not user:
        return ui.auth_page("register", error, auth.google_enabled())
    session.clear()
    session["user_id"] = user["id"]
    return RedirectResponse("/", status_code=303)


@rt("/logout")
def get(session):
    session.clear()
    return RedirectResponse("/", status_code=303)


@rt("/auth/google")
def get(session, request):
    if not auth.google_enabled():
        return RedirectResponse("/login?error=" + quote("Google sign-in is not configured."), status_code=303)
    state = auth.google_state()
    session["google_oauth_state"] = state
    return RedirectResponse(auth.google_authorize_url(request, state), status_code=303)


@rt("/auth/google/callback")
def get(session, request, code: str = "", state: str = "", error: str = ""):
    expected = session.pop("google_oauth_state", None)
    if error or not code or not state or not secrets.compare_digest(state, expected or ""):
        return RedirectResponse("/login?error=" + quote("Google sign-in failed."), status_code=303)
    user = auth.google_exchange(request, code)
    if not user:
        return RedirectResponse("/login?error=" + quote("That Google account is not authorised."), status_code=303)
    session.clear()
    session["user_id"] = user["id"]
    return RedirectResponse("/", status_code=303)


@rt("/surveys/new")
def get(session):
    user, redirect = require_user(session)
    if redirect:
        return redirect
    return ui.new_survey_page(user, ai.enabled())


@rt("/surveys/design")
def post(session, message: str = ""):
    user, redirect = require_user(session)
    if redirect:
        return redirect
    message = message.strip()[:6000]
    if not message:
        return RedirectResponse("/surveys/new", status_code=303)
    history = [{"role": "user", "content": message}]
    designer_message, guide, error = ai.design(history)
    title = str(guide.get("title") or "Untitled research")[:160]
    survey = db.create_survey(user["id"], message, title, guide)
    db.add_message(survey_id=survey["id"], channel="designer", role="user", content=message)
    db.add_message(survey_id=survey["id"], channel="designer", role="assistant", content=designer_message, metadata={"provider_error": error} if error else {})
    return RedirectResponse(f"/surveys/{survey['id']}/design", status_code=303)


@rt("/surveys/{survey_id}/design")
def get(session, survey_id: int):
    user, survey, error = owned_survey(session, survey_id)
    if error:
        return error
    return ui.designer_page(user, survey, db.messages(survey_id=survey_id, channel="designer"), ai.enabled())


@rt("/surveys/{survey_id}/design/message")
def post(session, survey_id: int, message: str = ""):
    user, survey, error = owned_survey(session, survey_id)
    if error:
        return error
    message = message.strip()[:6000]
    if message:
        db.add_message(survey_id=survey_id, channel="designer", role="user", content=message)
        history = db.messages(survey_id=survey_id, channel="designer")
        designer_message, guide, provider_error = ai.design(history, survey["guide"])
        db.save_guide(survey_id, guide, str(guide.get("title") or survey["title"]))
        db.add_message(survey_id=survey_id, channel="designer", role="assistant", content=designer_message, metadata={"provider_error": provider_error} if provider_error else {})
        survey = db.get_survey(survey_id, user["id"])
    return ui.designer_workbench(survey, db.messages(survey_id=survey_id, channel="designer"), ai.enabled())


@rt("/surveys/{survey_id}")
def get(session, survey_id: int):
    user, survey, error = owned_survey(session, survey_id)
    if error:
        return error
    return ui.survey_detail_page(
        user,
        survey,
        db.survey_conversations(survey_id),
        db.messages(survey_id=survey_id, channel="insights"),
    )


@rt("/surveys/{survey_id}/status")
def post(session, survey_id: int):
    _user, survey, error = owned_survey(session, survey_id)
    if error:
        return error
    db.set_survey_status(survey_id, "closed" if survey["status"] == "live" else "live")
    return RedirectResponse(f"/surveys/{survey_id}", status_code=303)


@rt("/s/{slug}")
def get(request, slug: str):
    survey = db.get_survey_by_slug(slug)
    if not survey or survey["status"] != "live":
        return PlainTextResponse("This interview is not currently accepting responses.", status_code=404)
    resume_token = request.cookies.get(f"fs_{slug}")
    if resume_token:
        conversation = db.get_conversation(resume_token)
        if conversation and conversation["survey_id"] == survey["id"] and conversation["status"] == "active":
            return RedirectResponse(f"/i/{resume_token}", status_code=303)
    return ui.consent_page(survey)


@rt("/s/{slug}/start")
def post(request, slug: str, website: str = ""):
    survey = db.get_survey_by_slug(slug)
    if not survey or survey["status"] != "live":
        return PlainTextResponse("This interview is not currently accepting responses.", status_code=404)
    if website:
        return PlainTextResponse("Unable to start this response.", status_code=400)
    ip = request.client.host if request.client else "unknown"
    meta = {
        "source": request.query_params.get("source", "direct")[:80],
        "locale": request.headers.get("accept-language", "")[:80],
        "user_agent": request.headers.get("user-agent", "")[:240],
        "ip_hash": hashlib.sha256(ip.encode()).hexdigest()[:16],
        "consented": True,
    }
    conversation = db.create_conversation(survey["id"], meta)
    result, provider_error = ai.interview(survey["guide"], [])
    db.add_message(
        conversation_id=conversation["id"], channel="interview", role="assistant",
        content=result["message"], metadata={"choices": result["choices"], "objective": result["current_objective"], "provider_error": provider_error},
    )
    db.update_conversation(conversation["id"], progress=result["progress"], status="complete" if result["done"] else "active")
    response = RedirectResponse(f"/i/{conversation['token']}", status_code=303)
    response.set_cookie(f"fs_{slug}", conversation["token"], max_age=30 * 24 * 3600, httponly=True, samesite="lax", secure=request.url.scheme == "https")
    return response


@rt("/i/{token}")
def get(token: str):
    conversation = db.get_conversation(token)
    if not conversation:
        return PlainTextResponse("Interview not found.", status_code=404)
    survey = db.get_survey(conversation["survey_id"])
    return ui.interview_page(survey, conversation, db.messages(conversation_id=conversation["id"], channel="interview"))


@rt("/i/{token}/message")
def post(token: str, message: str = ""):
    conversation = db.get_conversation(token)
    if not conversation:
        return PlainTextResponse("Interview not found.", status_code=404)
    survey = db.get_survey(conversation["survey_id"])
    if conversation["status"] != "active":
        return ui.interview_shell(survey, conversation, db.messages(conversation_id=conversation["id"], channel="interview"))
    message = message.strip()[:8000]
    if not message:
        return ui.interview_shell(survey, conversation, db.messages(conversation_id=conversation["id"], channel="interview"))
    db.add_message(conversation_id=conversation["id"], channel="interview", role="user", content=message)
    history = db.messages(conversation_id=conversation["id"], channel="interview")
    result, provider_error = ai.interview(survey["guide"], history)
    db.add_message(
        conversation_id=conversation["id"], channel="interview", role="assistant",
        content=result["message"], metadata={"choices": result["choices"], "objective": result["current_objective"], "provider_error": provider_error},
    )
    status = "complete" if result["done"] else "active"
    score = db.quality_score(conversation["id"])
    db.update_conversation(conversation["id"], progress=result["progress"], status=status, quality_score=score)
    if status == "complete":
        history = db.messages(conversation_id=conversation["id"], channel="interview")
        answers, extraction_error = ai.extract(survey["guide"], history)
        db.save_answers(conversation["id"], answers)
        if extraction_error:
            logger.info("Used local extraction for response %s: %s", conversation["id"], extraction_error)
    conversation = db.get_conversation(token)
    return ui.interview_shell(survey, conversation, db.messages(conversation_id=conversation["id"], channel="interview"))


@rt("/responses/{conversation_id}")
def get(session, conversation_id: int):
    user, redirect = require_user(session)
    if redirect:
        return redirect
    conversation = db.conversation_for_admin(conversation_id, user["id"])
    if not conversation:
        return PlainTextResponse("Response not found", status_code=404)
    return ui.response_detail_page(
        user,
        conversation,
        db.messages(conversation_id=conversation_id, channel="interview"),
        db.answers_for_conversation(conversation_id),
    )


@rt("/surveys/{survey_id}/insights")
def post(session, survey_id: int, question: str = ""):
    _user, survey, error = owned_survey(session, survey_id)
    if error:
        return error
    question = question.strip()[:3000]
    if question:
        evidence = db.all_answers(survey_id)
        complete = db.row("SELECT COUNT(*) count FROM conversations WHERE survey_id=? AND status='complete'", (survey_id,))["count"]
        db.add_message(survey_id=survey_id, channel="insights", role="user", content=question)
        answer, provider_error = ai.insights(question, evidence, complete)
        db.add_message(survey_id=survey_id, channel="insights", role="assistant", content=answer, metadata={"provider_error": provider_error} if provider_error else {})
    return RedirectResponse(f"/surveys/{survey_id}", status_code=303)


def _export_payload(survey: dict) -> dict:
    conversations = db.survey_conversations(survey["id"])
    payload = {"survey": {key: survey[key] for key in ("id", "slug", "title", "goals", "status", "created_at")}, "guide": survey["guide"], "responses": []}
    for conversation in conversations:
        payload["responses"].append({
            "id": conversation["id"],
            "status": conversation["status"],
            "progress": conversation["progress"],
            "quality_score": conversation["quality_score"],
            "started_at": conversation["started_at"],
            "completed_at": conversation["completed_at"],
            "transcript": [{"role": item["role"], "content": item["content"], "timestamp": item["created_at"]} for item in db.messages(conversation_id=conversation["id"], channel="interview")],
            "answers": db.answers_for_conversation(conversation["id"]),
        })
    return payload


@rt("/surveys/{survey_id}/export.json")
def get(session, survey_id: int):
    _user, survey, error = owned_survey(session, survey_id)
    if error:
        return error
    return Response(
        json.dumps(_export_payload(survey), ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="fastsurvey-{survey["slug"]}.json"'},
    )


@rt("/surveys/{survey_id}/export.csv")
def get(session, survey_id: int):
    _user, survey, error = owned_survey(session, survey_id)
    if error:
        return error
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["response_id", "status", "started_at", "completed_at", "quality_score", "objective_key", "value", "confidence", "sentiment", "raw_quote"])
    for conversation in db.survey_conversations(survey_id):
        answers = db.answers_for_conversation(conversation["id"]) or [{"objective_key": "", "value": "", "confidence": "", "sentiment": "", "raw_quote": ""}]
        for answer in answers:
            writer.writerow([
                conversation["id"], conversation["status"], conversation["started_at"], conversation["completed_at"] or "", conversation["quality_score"],
                answer["objective_key"], json.dumps(answer["value"], ensure_ascii=False) if not isinstance(answer["value"], str) else answer["value"], answer["confidence"], answer["sentiment"], answer["raw_quote"],
            ])
    return Response(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="fastsurvey-{survey["slug"]}.csv"'})


@rt("/healthz")
def get():
    db.row("SELECT 1 ok")
    return JSONResponse({"status": "ok", "service": "FastSurvey", "ai": "xai" if ai.enabled() else "local-demo"})


@rt("/robots.txt")
def get():
    return PlainTextResponse("User-agent: *\nAllow: /\nDisallow: /surveys\nDisallow: /responses\nDisallow: /i/\n")


@rt("/static/product-demo.gif")
def get():
    path = os.path.join(os.path.dirname(__file__), "docs", "demo", "fastsurvey-walkthrough.gif")
    if not os.path.exists(path):
        return PlainTextResponse("Product demo is being prepared.", status_code=404)
    return FileResponse(path, media_type="image/gif", headers={"Cache-Control": "public, max-age=3600"})


if __name__ == "__main__":
    serve(port=PORT)
