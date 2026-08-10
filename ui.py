"""FastHTML views and shared visual system for FastSurvey."""
from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import quote

from fasthtml.common import *


ACCENT = "#6d5dfc"
TINT = "#f4f2ff"
FAVICON = "data:image/svg+xml," + quote(
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="9" fill="#6d5dfc"/><path d="M9 10.5h14M9 16h10M9 21.5h6" stroke="white" stroke-width="2.6" stroke-linecap="round"/><circle cx="23" cy="21.5" r="3" fill="#b6f09c"/></svg>""",
    safe="",
)

PARTNERS = (
    ("SAASPASS", "https://saaspass.com/", "Identity and access management for secure FastSME deployments."),
    ("Sixty Four", "https://sixtyfour.ee/", "Senior product, service-design and software delivery from Tallinn."),
    ("EDI Labs", "https://edilabs.tech/", "AI and data engineering for production-grade research workflows."),
    ("Predictive Labs", "https://predictivelabs.ai/", "Auditable AI systems for evidence-heavy organisations."),
    ("Consistente", "https://consistente.tech/", "Enterprise AI delivery across regulated and high-trust sectors."),
)

CSS = """
:root{--accent:#6d5dfc;--accent-dark:#5143d9;--tint:#f4f2ff;--ink:#17152a;--muted:#6d6a7e;--line:#e8e6f0;--surface:#fff;--bg:#f8f8fb;--good:#16835b;--warn:#a96500;--danger:#c43850;--shadow:0 18px 50px rgba(43,35,90,.09)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}button,input,textarea{font:inherit}a{color:inherit}.hidden{display:none!important}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:780;letter-spacing:-.02em}.mark{width:32px;height:32px;border-radius:10px;background:var(--accent);display:grid;place-items:center;color:#fff;font-size:16px;box-shadow:0 6px 18px rgba(109,93,252,.22)}
.topbar{height:68px;padding:0 28px;border-bottom:1px solid var(--line);background:rgba(255,255,255,.92);backdrop-filter:blur(14px);display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:30}.top-actions{display:flex;align-items:center;gap:10px}.navlink{font-size:14px;text-decoration:none;color:var(--muted);font-weight:620;padding:9px 10px;border-radius:9px}.navlink:hover,.navlink.active{color:var(--ink);background:var(--tint)}
.button,.button-ghost,.button-danger{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;border-radius:10px;padding:10px 15px;text-decoration:none;font-weight:680;font-size:14px;cursor:pointer;white-space:nowrap}.button{background:var(--accent);color:#fff;box-shadow:0 6px 16px rgba(109,93,252,.18)}.button:hover{background:var(--accent-dark)}.button-ghost{background:#fff;color:var(--ink);border:1px solid var(--line)}.button-danger{background:#fff0f2;color:var(--danger);border:1px solid #ffd4db}.small-button{padding:7px 11px;font-size:12px}.icon-button{width:38px;height:38px;padding:0}
.shell{display:grid;grid-template-columns:220px minmax(0,1fr);min-height:calc(100vh - 68px)}.sidebar{border-right:1px solid var(--line);padding:24px 14px;background:#fff}.side-group{display:grid;gap:5px;position:sticky;top:92px}.side-link{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;color:var(--muted);font-size:14px;font-weight:620;text-decoration:none}.side-link:hover,.side-link.active{background:var(--tint);color:var(--accent)}.side-foot{margin-top:28px;padding:14px 12px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
.workspace{padding:36px clamp(22px,4vw,56px);min-width:0}.page-head{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:28px}.eyebrow{color:var(--accent);font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.page-head h1,.auth-card h1{font-size:30px;line-height:1.15;letter-spacing:-.04em;margin:8px 0}.subtle{color:var(--muted);line-height:1.55;margin:0}.notice{padding:12px 14px;background:#fff8e9;border:1px solid #f2d7a4;border-radius:11px;color:#79500c;font-size:13px;margin:0 0 18px}.empty{border:1px dashed #d9d5e9;border-radius:18px;text-align:center;padding:64px 24px;background:rgba(255,255,255,.6)}.empty h2{font-size:20px;margin:12px 0 8px}.empty p{color:var(--muted);margin:0 auto 22px;max-width:430px;line-height:1.55}
.stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:28px}.stat{background:#fff;border:1px solid var(--line);border-radius:15px;padding:19px}.stat-label{color:var(--muted);font-size:12px;font-weight:650}.stat-value{font-size:28px;font-weight:780;letter-spacing:-.04em;margin-top:9px}.survey-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.survey-card{background:#fff;border:1px solid var(--line);border-radius:17px;padding:20px;text-decoration:none;transition:.18s ease;min-width:0}.survey-card:hover{transform:translateY(-2px);border-color:#cfc9ff;box-shadow:var(--shadow)}.survey-card h2{font-size:17px;margin:20px 0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.card-top,.card-foot,.row-between{display:flex;align-items:center;justify-content:space-between;gap:12px}.card-foot{border-top:1px solid var(--line);padding-top:14px;margin-top:18px;color:var(--muted);font-size:12px}.status{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 9px;background:#f1f0f5;color:var(--muted);font-size:11px;font-weight:750;text-transform:capitalize}.status.live{background:#eaf9f2;color:var(--good)}.status.closed{background:#fff0f2;color:var(--danger)}.dot{width:6px;height:6px;border-radius:50%;background:currentColor}
.panel{background:#fff;border:1px solid var(--line);border-radius:17px;padding:22px}.panel h2{font-size:18px;margin:0 0 6px}.panel h3{font-size:14px;margin:20px 0 8px}.two-col{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(310px,.75fr);gap:20px}.detail-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:20px}.stack{display:grid;gap:14px}.field{display:grid;gap:7px}.field label{font-size:12px;font-weight:700}.input,.textarea{width:100%;border:1px solid var(--line);border-radius:11px;padding:12px 13px;background:#fff;color:var(--ink);outline:none}.textarea{resize:vertical;min-height:96px;line-height:1.5}.input:focus,.textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(109,93,252,.10)}
.studio{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(330px,.95fr);gap:18px;align-items:start}.chat-panel{padding:0;overflow:hidden}.chat-head{padding:18px 20px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between}.chat-head h2{font-size:15px;margin:0}.chat-scroll{padding:20px;display:flex;flex-direction:column;gap:14px;min-height:410px;max-height:56vh;overflow:auto;scroll-behavior:smooth}.bubble{max-width:82%;padding:12px 14px;border-radius:15px;line-height:1.52;font-size:14px;white-space:pre-wrap}.bubble.assistant{align-self:flex-start;background:var(--tint);border-bottom-left-radius:5px}.bubble.user{align-self:flex-end;background:var(--accent);color:#fff;border-bottom-right-radius:5px}.bubble-meta{font-size:10px;opacity:.62;margin-top:6px}.composer{border-top:1px solid var(--line);padding:14px;display:flex;gap:10px;background:#fff}.composer textarea{min-height:46px;max-height:130px;resize:none}.composer .button{align-self:flex-end;height:46px}.guide-panel{max-height:calc(100vh - 120px);overflow:auto;position:sticky;top:86px}.guide-meta{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.pill{border:1px solid var(--line);border-radius:999px;padding:5px 9px;font-size:11px;color:var(--muted);background:#fff}.objective{padding:10px 0;border-top:1px solid var(--line);font-size:13px;line-height:1.45}.question{padding:13px;border:1px solid var(--line);border-radius:12px;margin-top:9px}.question-type{font-size:10px;font-weight:800;color:var(--accent);text-transform:uppercase;letter-spacing:.08em}.question p{font-size:13px;line-height:1.48;margin:7px 0 0}.guide-actions{display:flex;gap:8px;margin-top:18px;flex-wrap:wrap}
.response-table{width:100%;border-collapse:collapse}.response-table th{text-align:left;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.07em;padding:10px;border-bottom:1px solid var(--line)}.response-table td{padding:13px 10px;border-bottom:1px solid var(--line);font-size:13px}.response-table tr:last-child td{border:0}.text-link{color:var(--accent);font-weight:680;text-decoration:none}.codebox{display:block;padding:12px;border-radius:10px;background:#1d1935;color:#ebe8ff;font:12px/1.5 ui-monospace,SFMono-Regular,monospace;overflow:auto;white-space:pre-wrap}.quote{border-left:3px solid var(--accent);padding:8px 12px;margin:8px 0;background:var(--tint);font-size:13px;line-height:1.5}.insight-answer{background:var(--tint);padding:14px;border-radius:12px;line-height:1.55;white-space:pre-wrap;font-size:14px}
.lp-body{background:#fff}.lp-nav{height:68px;display:flex;align-items:center;justify-content:space-between;max-width:1180px;margin:auto;padding:0 24px;border-bottom:1px solid var(--line)}.lp-nav-actions{display:flex;align-items:center;gap:12px}.lp-hero{max-width:1180px;margin:auto;padding:112px 24px 84px}.lp-hero h1{font-size:clamp(44px,7vw,80px);line-height:1.01;letter-spacing:-.06em;max-width:980px;margin:22px 0}.lp-lede{font-size:20px;line-height:1.65;color:var(--muted);max-width:740px}.lp-actions{display:flex;gap:12px;margin-top:32px;flex-wrap:wrap}.mock{max-width:1000px;margin:0 auto 90px;padding:0 24px}.mock-window{display:grid;grid-template-columns:.34fr .66fr;min-height:430px;background:#fff;border:1px solid var(--line);border-radius:24px;padding:10px;box-shadow:0 34px 90px rgba(43,35,90,.13);overflow:hidden}.mock-side{background:#211c3f;color:#fff;border-radius:16px;padding:24px}.mock-side h3{font-size:15px}.mock-item{padding:12px;border-radius:10px;color:#bcb6dc;font-size:13px;margin-top:8px}.mock-item.active{background:#37305e;color:#fff}.mock-chat{background:#fbfaff;border-radius:16px;padding:32px;display:flex;flex-direction:column;gap:14px}.mock-chat .bubble{font-size:13px}.typing{display:flex;gap:5px;padding:14px;width:max-content;background:var(--tint);border-radius:14px}.typing i{width:6px;height:6px;background:#aaa2d8;border-radius:50%}.feature-band{background:var(--tint);border-block:1px solid #e3defe}.feature-grid{max-width:1180px;margin:auto;padding:72px 24px;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.feature-card{background:rgba(255,255,255,.8);border:1px solid #e1dcfc;border-radius:18px;padding:25px}.feature-card span{color:var(--accent);font-size:11px;font-weight:800}.feature-card h2{font-size:19px;margin:20px 0 8px}.feature-card p{color:var(--muted);font-size:14px;line-height:1.58;margin:0}.lp-footer{max-width:1180px;margin:auto;padding:32px 24px 50px;display:flex;justify-content:space-between;color:var(--muted);font-size:13px}
.lp-demo{max-width:1000px;margin:0 auto 86px;padding:0 24px}.lp-demo-frame{padding:10px;background:#fff;border:1px solid var(--line);border-radius:24px;box-shadow:0 34px 90px rgba(43,35,90,.13)}.lp-demo img{display:block;width:100%;height:auto;aspect-ratio:16/10;object-fit:cover;object-position:top;border-radius:16px;background:var(--tint)}.lp-demo p{text-align:center;color:var(--muted);font-size:13px;margin:14px 0 3px}.lp-partners{max-width:1180px;margin:auto;padding:76px 24px}.lp-section-head{max-width:720px}.lp-section-head h2{font-size:34px;letter-spacing:-.04em;margin:12px 0}.lp-section-head p{color:var(--muted);line-height:1.6}.partner-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin-top:30px}.partner-card{border:1px solid var(--line);border-radius:17px;padding:20px;text-decoration:none;transition:.18s;background:#fff}.partner-card:hover{transform:translateY(-2px);border-color:#ccc5ff;box-shadow:var(--shadow)}.partner-card h3{font-size:16px;margin:0 0 9px}.partner-card p{font-size:12px;color:var(--muted);line-height:1.55;margin:0}.partner-type{display:block;color:var(--accent);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:16px}.lp-developers{max-width:1180px;margin:auto;padding:68px 24px;border-top:1px solid var(--line);display:grid;grid-template-columns:1fr auto;gap:30px;align-items:center}.lp-developers h2{font-size:32px;letter-spacing:-.04em;margin:10px 0}.lp-developers p{color:var(--muted);line-height:1.6;max-width:680px}
.auth-wrap{min-height:100vh;display:grid;place-items:center;padding:24px;background:radial-gradient(circle at 50% 0,#ebe8ff,transparent 42%),var(--bg)}.auth-card{width:min(430px,100%);background:#fff;border:1px solid var(--line);border-radius:20px;padding:30px;box-shadow:var(--shadow)}.auth-brand{margin-bottom:32px}.auth-card form{display:grid;gap:13px}.auth-card .button{width:100%;padding:12px}.or{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:12px;margin:18px 0}.or:before,.or:after{content:"";height:1px;background:var(--line);flex:1}.auth-switch{text-align:center;color:var(--muted);font-size:13px;margin:20px 0 0}.error{color:var(--danger);background:#fff0f2;border:1px solid #ffd7de;padding:10px 12px;border-radius:10px;font-size:13px}
.interview-body{min-height:100vh;background:#fbfbfd}.interview-top{height:64px;display:flex;align-items:center;justify-content:space-between;max-width:800px;margin:auto;padding:0 20px}.progress-wrap{width:150px;height:5px;background:#e9e7f0;border-radius:999px;overflow:hidden}.progress-bar{height:100%;background:var(--accent);border-radius:inherit;transition:width .3s}.interview-main{max-width:720px;margin:auto;padding:36px 20px 130px}.interview-chat{display:flex;flex-direction:column;gap:17px}.interview-chat .bubble{font-size:16px;padding:14px 16px}.choices{display:flex;gap:8px;flex-wrap:wrap;align-self:flex-start;max-width:92%}.choice-form{margin:0}.choice{border:1px solid #d8d3fa;background:#fff;color:var(--accent-dark);border-radius:999px;padding:9px 13px;font-size:13px;font-weight:650;cursor:pointer}.choice:hover{background:var(--tint)}.respondent-composer{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(transparent,#fbfbfd 24%);padding:28px 20px 20px}.respondent-form{max-width:720px;margin:auto;background:#fff;border:1px solid var(--line);border-radius:16px;padding:8px;display:flex;gap:8px;box-shadow:0 15px 38px rgba(43,35,90,.12)}.respondent-form textarea{border:0;min-height:44px;max-height:120px;padding:11px;resize:none;flex:1;outline:none}.consent{max-width:620px;margin:9vh auto;padding:34px;background:#fff;border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow)}.consent h1{font-size:32px;letter-spacing:-.04em;margin:18px 0 12px}.consent-list{display:grid;gap:12px;margin:24px 0}.consent-item{display:flex;gap:11px;color:var(--muted);font-size:14px;line-height:1.48}.check{color:var(--good);font-weight:800}.done-card{text-align:center;background:#fff;border:1px solid var(--line);border-radius:18px;padding:24px;margin:28px auto;max-width:520px}.done-card h2{margin:8px 0}.done-card p{color:var(--muted)}
@media(max-width:1000px){.survey-grid{grid-template-columns:repeat(2,1fr)}.studio{grid-template-columns:1fr}.guide-panel{position:static;max-height:none}.two-col,.detail-grid{grid-template-columns:1fr}.stat-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:760px){.topbar{height:60px;padding:0 16px}.topbar .navlink{display:none}.shell{display:block}.sidebar{display:none}.workspace{padding:24px 16px}.page-head{align-items:stretch}.page-head h1{font-size:26px}.survey-grid,.stat-grid{grid-template-columns:1fr}.page-head{flex-direction:column}.lp-nav{height:60px}.lp-nav-actions .navlink{display:none}.lp-hero{padding:76px 20px 58px}.lp-hero h1{font-size:45px}.lp-lede{font-size:17px}.mock-window{grid-template-columns:1fr}.mock-side{display:none}.mock-chat{padding:20px;min-height:390px}.feature-grid{grid-template-columns:1fr;padding:52px 20px}.lp-footer{flex-direction:column;gap:10px}.chat-scroll{max-height:none}.bubble{max-width:90%}.guide-panel{padding:16px}.response-table{display:block;overflow:auto}.interview-main{padding-top:20px}}
@media(max-width:1000px){.partner-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:760px){.lp-demo{padding:0 14px;margin-bottom:60px}.lp-demo-frame{padding:6px;border-radius:17px}.lp-demo img{border-radius:12px}.partner-grid{grid-template-columns:1fr}.lp-partners{padding:58px 20px}.lp-developers{grid-template-columns:1fr;padding:54px 20px}}
"""


def _head(title: str, description: str = "AI-moderated conversational surveys with adaptive interviews and structured insight."):
    return Head(
        Title(f"{title} · FastSurvey"),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="description", content=description),
        Link(rel="icon", type="image/svg+xml", href=FAVICON),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"),
        Script(src="https://unpkg.com/htmx.org@2.0.4", defer=True),
        Style(CSS),
    )


def brand(href: str = "/"):
    return A(Span("✦", cls="mark"), Span("FastSurvey"), href=href, cls="brand")


def landing_page():
    features = [
        ("01", "Design in conversation", "Describe the decision you need to make. The designer turns it into objectives, questions, branching and probing rules."),
        ("02", "Interview, don’t interrogate", "Participants answer naturally while the interviewer listens, follows up, and keeps one clear question on screen."),
        ("03", "Evidence you can use", "Every transcript becomes structured answers, themes, sentiment, quote-ready evidence and exportable data."),
    ]
    return Html(
        _head("Conversational research"),
        Body(
            Nav(
                brand(),
                Div(
                    A("How it works", href="#how", cls="navlink"),
                    A("Partners", href="#partners", cls="navlink"),
                    A("Open source", href="https://github.com/predictivelabsai/FastSurvey", cls="navlink"),
                    A("Sign In", href="/login", cls="button-ghost"),
                    cls="lp-nav-actions",
                ),
                cls="lp-nav",
            ),
            Main(
                Section(
                    Span("AI-moderated customer research", cls="eyebrow"),
                    H1("Ask better questions. Hear what people really mean."),
                    P("Create adaptive interviews in chat, let every participant answer in their own words, and turn the conversation into decision-ready evidence.", cls="lp-lede"),
                    Div(A("Design your first survey", href="/register", cls="button"), A("See how it works ↓", href="#how", cls="button-ghost"), cls="lp-actions"),
                    cls="lp-hero",
                ),
                Section(
                    Div(
                        Img(src="/static/product-demo.gif", alt="FastSurvey product tour", width="1440", height="900", loading="eager"),
                        P("Product tour · from research brief to structured evidence"),
                        cls="lp-demo-frame",
                    ),
                    cls="lp-demo", aria_label="FastSurvey product tour",
                ),
                Section(Div(*[Article(Span(number), H2(title), P(copy), cls="feature-card") for number, title, copy in features], cls="feature-grid"), id="how", cls="feature-band"),
                Section(
                    Div(
                        Span("Integration partners", cls="eyebrow"),
                        H2("Connect with trusted implementation specialists."),
                        P("Identity, software delivery, data engineering and applied-AI support for self-hosted FastSurvey deployments."),
                        cls="lp-section-head",
                    ),
                    Div(*[
                        A(Span("Integration partner", cls="partner-type"), H3(name), P(copy),
                          href=url, target="_blank", rel="noopener noreferrer", cls="partner-card")
                        for name, url, copy in PARTNERS
                    ], cls="partner-grid"),
                    id="partners", cls="lp-partners",
                ),
                Section(
                    Div(Span("Developers", cls="eyebrow"), H2("Own the research stack."),
                        P("FastSurvey is a small, inspectable FastHTML application with SQLite persistence, HTMX interactions and a direct xAI integration.")),
                    A("View the source on GitHub ↗", href="https://github.com/predictivelabsai/FastSurvey",
                      target="_blank", rel="noopener noreferrer", cls="button"),
                    cls="lp-developers",
                ),
            ),
            Footer(Span("FastSurvey is part of the open-source FastSME suite."), A("View all products ↗", href="https://fastsme.com/products", cls="text-link"), cls="lp-footer"),
            cls="lp-body",
        ),
    )


def auth_page(mode: str = "login", error: str = "", google_enabled: bool = False):
    register_mode = mode == "register"
    title = "Create your workspace" if register_mode else "Welcome back"
    return Html(
        _head("Register" if register_mode else "Sign in"),
        Body(
            Main(
                Div(
                    Div(brand(), cls="auth-brand"),
                    Span("Start a better conversation", cls="eyebrow"),
                    H1(title),
                    P("Design, run and understand adaptive interviews.", cls="subtle"),
                    P(error, cls="error") if error else None,
                    A("Continue with Google" if google_enabled else "Google sign-in is not configured", href="/auth/google" if google_enabled else "#", cls="button-ghost", style="width:100%;margin-top:22px"),
                    Div("or use email", cls="or"),
                    Form(
                        Div(Label("Name", fr="name"), Input(id="name", name="name", autocomplete="name", required=True, cls="input"), cls="field") if register_mode else None,
                        Div(Label("Email", fr="email"), Input(id="email", name="email", type="email", autocomplete="email", required=True, cls="input"), cls="field"),
                        Div(Label("Password", fr="password"), Input(id="password", name="password", type="password", minlength="10" if register_mode else None, autocomplete="new-password" if register_mode else "current-password", required=True, cls="input"), cls="field"),
                        Button("Create account" if register_mode else "Sign in", type="submit", cls="button"),
                        method="post", action="/register" if register_mode else "/login",
                    ),
                    P("Already have an account? " if register_mode else "New to FastSurvey? ", A("Sign in" if register_mode else "Create an account", href="/login" if register_mode else "/register", cls="text-link"), cls="auth-switch"),
                    cls="auth-card",
                ),
                cls="auth-wrap",
            ),
        ),
    )


def status_badge(value: str):
    return Span(Span(cls="dot"), value, cls=f"status {value}")


def app_page(title: str, user: dict, active: str, *content):
    return Html(
        _head(title),
        Body(
            Header(
                brand(),
                Div(A("New survey", href="/surveys/new", cls="button small-button"), A(user.get("name") or user["email"], href="#", cls="navlink"), A("Log out", href="/logout", cls="button-ghost small-button"), cls="top-actions"),
                cls="topbar",
            ),
            Div(
                Aside(
                    Nav(
                        A("◫  Overview", href="/", cls=f"side-link {'active' if active == 'dashboard' else ''}"),
                        A("✦  Surveys", href="/surveys", cls=f"side-link {'active' if active == 'surveys' else ''}"),
                        A("＋  New survey", href="/surveys/new", cls=f"side-link {'active' if active == 'new' else ''}"),
                        cls="side-group",
                    ),
                    Div("Conversational research, from question to evidence.", cls="side-foot"),
                    cls="sidebar",
                ),
                Main(*content, cls="workspace"),
                cls="shell",
            ),
        ),
    )


def dashboard_page(user: dict, surveys: list[dict]):
    total = sum(item["response_count"] or 0 for item in surveys)
    complete = sum(item["complete_count"] or 0 for item in surveys)
    live = sum(item["status"] == "live" for item in surveys)
    head = Div(Div(Span("Research workspace", cls="eyebrow"), H1(f"Good to see you, {(user.get('name') or 'researcher').split()[0]}"), P("Design an interview, share it, and watch the evidence take shape.", cls="subtle")), A("＋ New survey", href="/surveys/new", cls="button"), cls="page-head")
    if not surveys:
        body = Div(Span("✦", cls="mark"), H2("Start with the question behind the question"), P("Tell the survey designer what decision you need to make. It will turn your goal into an adaptive interview you can refine in conversation."), A("Design your first survey", href="/surveys/new", cls="button"), cls="empty")
    else:
        cards = [
            A(
                Div(status_badge(item["status"]), Span(f"{item['complete_count'] or 0} complete", cls="subtle"), cls="card-top"),
                H2(item["title"]),
                P((item["goals"][:120] + "…") if len(item["goals"]) > 120 else item["goals"], cls="subtle"),
                Div(Span(f"{item['response_count'] or 0} responses"), Span("Open →", cls="text-link"), cls="card-foot"),
                href=f"/surveys/{item['id']}", cls="survey-card",
            ) for item in surveys
        ]
        body = Div(
            Div(Div(Span("Surveys", cls="stat-label"), Div(str(len(surveys)), cls="stat-value"), cls="stat"), Div(Span("Live", cls="stat-label"), Div(str(live), cls="stat-value"), cls="stat"), Div(Span("Responses", cls="stat-label"), Div(str(total), cls="stat-value"), cls="stat"), Div(Span("Completed", cls="stat-label"), Div(str(complete), cls="stat-value"), cls="stat"), cls="stat-grid"),
            Div(*cards, cls="survey-grid"),
        )
    return app_page("Workspace", user, "dashboard", head, body)


def new_survey_page(user: dict, ai_enabled: bool):
    content = Div(
        Div(Span("Survey designer", cls="eyebrow"), H1("What do you need to understand?"), P("Describe the decision, audience and uncertainty in plain language. You can refine the guide in chat.", cls="subtle"), cls="page-head"),
        P("Grok is not configured, so FastSurvey will use its local demo designer. The complete workflow remains available." if not ai_enabled else f"Connected to Grok. Your next message will become a structured interview guide.", cls="notice") if not ai_enabled else None,
        Div(
            Div(
                Div(Div("Tell me about the research decision you’re facing. Who should we speak to, and what do you need to learn?", cls="bubble assistant"), cls="chat-scroll"),
                Form(Textarea(name="message", placeholder="Example: Understand why mid-market customers churn after using automation…", required=True, autofocus=True, cls="textarea"), Button("Create guide →", type="submit", cls="button"), method="post", action="/surveys/design", cls="composer"),
                cls="panel chat-panel",
            ),
            Div(H2("A strong starting brief"), P("You do not need to write survey questions. Share the context the designer cannot infer.", cls="subtle"), H3("Include when useful"), Div(Span("The decision", cls="pill"), Span("Target audience", cls="pill"), Span("Known hypotheses", cls="pill"), Span("Time limit", cls="pill"), cls="guide-meta"), H3("You’ll get"), P("Objectives, question mix, adaptive probes, screening, completion criteria and a share-ready respondent experience.", cls="subtle"), cls="panel"),
            cls="two-col",
        ),
    )
    return app_page("New survey", user, "new", content)


def guide_view(guide: dict, survey: dict):
    objectives = guide.get("research_objectives") or []
    questions = guide.get("questions") or []
    return Div(
        Div(Span("Interview guide", cls="eyebrow"), status_badge(survey["status"]), cls="row-between"),
        H2(guide.get("title") or survey["title"], style="margin-top:12px"),
        Div(Span(f"~{guide.get('estimated_minutes', 5)} min", cls="pill"), Span(f"{len(questions)} questions", cls="pill"), Span(f"{len(objectives)} objectives", cls="pill"), cls="guide-meta"),
        H3("Objectives"),
        *[Div(Strong(f"{index}. "), objective.get("label", objective.get("key", "Objective")), cls="objective") for index, objective in enumerate(objectives, 1)],
        H3("Conversation path"),
        *[Div(Span(question.get("type", "open").replace("_", " "), cls="question-type"), P(question.get("prompt", "")), cls="question") for question in questions],
        Div(
            Form(Button("Publish survey" if survey["status"] != "live" else "Close survey", type="submit", cls="button" if survey["status"] != "live" else "button-danger"), method="post", action=f"/surveys/{survey['id']}/status"),
            A("Open overview", href=f"/surveys/{survey['id']}", cls="button-ghost"),
            cls="guide-actions",
        ),
        cls="panel guide-panel",
        id="guide-panel",
    )


def designer_workbench(survey: dict, messages: list[dict], ai_enabled: bool):
    return Div(
        Div(
            Div(H2("Design conversation"), Span("Grok" if ai_enabled else "Local demo", cls="pill"), cls="chat-head"),
            Div(*[Div(item["content"], Div("You" if item["role"] == "user" else "Survey Designer", cls="bubble-meta"), cls=f"bubble {item['role']}") for item in messages], cls="chat-scroll", id="designer-messages"),
            Form(Textarea(name="message", placeholder="Make it shorter, add a pricing ranking, probe emotion…", required=True, cls="textarea", onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();this.form.requestSubmit()}"), Button("Send ↑", type="submit", cls="button"), hx_post=f"/surveys/{survey['id']}/design/message", hx_target="#studio", hx_swap="outerHTML", cls="composer"),
            cls="panel chat-panel",
        ),
        guide_view(survey["guide"], survey),
        cls="studio", id="studio",
    )


def designer_page(user: dict, survey: dict, messages: list[dict], ai_enabled: bool):
    head = Div(Div(Span("Survey designer", cls="eyebrow"), H1(survey["title"]), P("Refine the interview in conversation, then publish when the path feels right.", cls="subtle")), cls="page-head")
    return app_page("Design survey", user, "surveys", head, designer_workbench(survey, messages, ai_enabled))


def survey_detail_page(user: dict, survey: dict, conversations: list[dict], insight_messages: list[dict]):
    share_url = f"/s/{survey['slug']}"
    response_rows = [
        Tr(Td(A(f"Response {item['id']}", href=f"/responses/{item['id']}", cls="text-link")), Td(status_badge(item["status"])), Td(f"{item['progress']}%"), Td(f"{item['quality_score']:.0%}"), Td(item["started_at"][:16].replace("T", " "))) for item in conversations
    ]
    insight_history = []
    for item in insight_messages[-6:]:
        insight_history.append(Div(Strong("You: " if item["role"] == "user" else "FastSurvey: "), item["content"], cls="insight-answer" if item["role"] == "assistant" else "quote"))
    content = (
        Div(Div(Span("Survey overview", cls="eyebrow"), H1(survey["title"]), P(survey["goals"], cls="subtle")), Div(status_badge(survey["status"]), A("Edit guide", href=f"/surveys/{survey['id']}/design", cls="button-ghost"), cls="top-actions"), cls="page-head"),
        Div(
            Div(
                Div(H2("Responses"), P(f"{len(conversations)} started · {sum(item['status'] == 'complete' for item in conversations)} complete", cls="subtle"), cls="panel"),
                Div(H2("Share"), P("Send the public link or embed the respondent experience.", cls="subtle"), Code(share_url, cls="codebox"), Div(A("Open interview ↗", href=share_url, target="_blank", cls="button small-button"), A("CSV", href=f"/surveys/{survey['id']}/export.csv", cls="button-ghost small-button"), A("JSON", href=f"/surveys/{survey['id']}/export.json", cls="button-ghost small-button"), cls="guide-actions"), Details(Summary("Embed code"), Code(f'<iframe src="{{your-domain}}{share_url}" width="100%" height="720" frameborder="0"></iframe>', cls="codebox")), cls="panel"),
                cls="stack",
            ),
            Div(H2("Ask your evidence"), P("Synthesis uses only completed response evidence.", cls="subtle"), *insight_history, Form(Input(name="question", placeholder="What are the strongest reasons behind this?", required=True, cls="input"), Button("Ask →", type="submit", cls="button"), method="post", action=f"/surveys/{survey['id']}/insights", style="display:flex;gap:8px;margin-top:14px"), cls="panel"),
            cls="detail-grid",
        ),
        Div(H2("Interview activity"), Table(Thead(Tr(Th("Response"), Th("Status"), Th("Progress"), Th("Quality"), Th("Started"))), Tbody(*response_rows) if response_rows else Tbody(Tr(Td("No responses yet. Publish and share the link to begin.", colspan="5", cls="subtle"))), cls="response-table"), cls="panel", style="margin-top:20px"),
    )
    return app_page(survey["title"], user, "surveys", *content)


def consent_page(survey: dict):
    return Html(
        _head(survey["title"]),
        Body(
            Header(brand("/"), Span(f"About {survey['guide'].get('estimated_minutes', 5)} minutes", cls="subtle"), cls="interview-top"),
            Main(
                Span("You’re invited", cls="eyebrow"),
                H1(survey["title"]),
                P(survey["guide"].get("opening") or "Thanks for helping us understand your experience.", cls="subtle"),
                Div(Div(Span("✓", cls="check"), Span("This is a conversation. Answer naturally and skip anything you prefer not to answer."), cls="consent-item"), Div(Span("✓", cls="check"), Span("Your responses and transcript will be shared with the research owner and analysed for themes."), cls="consent-item"), Div(Span("✓", cls="check"), Span("Do not include confidential, identifying or sensitive information unless the research owner requested it."), cls="consent-item"), cls="consent-list"),
                Form(Button("I agree — start the conversation", type="submit", cls="button", style="width:100%;padding:13px"), Input(name="website", tabindex="-1", autocomplete="off", cls="hidden"), method="post", action=f"/s/{survey['slug']}/start"),
                P("By starting, you consent to this research use. You can close the page at any time.", cls="subtle", style="font-size:11px;text-align:center;margin-top:12px"),
                cls="consent",
            ),
            cls="interview-body",
        ),
    )


def interview_shell(survey: dict, conversation: dict, messages: list[dict]):
    done = conversation["status"] != "active"
    last_assistant = next((item for item in reversed(messages) if item["role"] == "assistant"), None)
    choices = (last_assistant or {}).get("metadata", {}).get("choices", []) if not done else []
    bubbles = [Div(item["content"], cls=f"bubble {item['role']}") for item in messages]
    if choices:
        bubbles.append(Div(*[
            Form(Input(type="hidden", name="message", value=choice), Button(choice, type="submit", cls="choice"), hx_post=f"/i/{conversation['token']}/message", hx_target="#interview-shell", hx_swap="outerHTML", cls="choice-form")
            for choice in choices
        ], cls="choices"))
    if done:
        bubbles.append(Div(Span("✓", cls="check"), H2("Response complete"), P("You can close this window. Your answers have been saved."), cls="done-card"))
    composer = None if done else Div(Form(Textarea(name="message", placeholder="Type your answer…", required=True, autofocus=True, onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();this.form.requestSubmit()}"), Button("Send ↑", type="submit", cls="button"), hx_post=f"/i/{conversation['token']}/message", hx_target="#interview-shell", hx_swap="outerHTML", cls="respondent-form"), cls="respondent-composer")
    return Div(
        Header(brand("/"), Div(Div(Div(cls="progress-bar", style=f"width:{conversation['progress']}%"), cls="progress-wrap"), Span(f"{conversation['progress']}%", cls="subtle"), cls="top-actions"), cls="interview-top"),
        Main(Div(*bubbles, cls="interview-chat"), cls="interview-main"),
        composer,
        id="interview-shell",
    )


def interview_page(survey: dict, conversation: dict, messages: list[dict]):
    return Html(
        _head(survey["title"]),
        Body(
            interview_shell(survey, conversation, messages),
            Script("document.body.addEventListener('htmx:afterSwap',()=>{window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'})})"),
            cls="interview-body",
        ),
    )


def response_detail_page(user: dict, conversation: dict, transcript: list[dict], answers: list[dict]):
    content = (
        Div(Div(Span("Response review", cls="eyebrow"), H1(f"Response {conversation['id']}"), P(conversation["survey_title"], cls="subtle")), A("← Survey", href=f"/surveys/{conversation['survey_id']}", cls="button-ghost"), cls="page-head"),
        Div(
            Div(H2("Transcript"), Div(*[Div(item["content"], cls=f"bubble {item['role']}") for item in transcript], cls="chat-scroll", style="max-height:none"), cls="panel"),
            Div(H2("Structured evidence"), Div(status_badge(conversation["status"]), Span(f"Quality {conversation['quality_score']:.0%}", cls="pill"), cls="guide-meta"), *[Div(Span(item["objective_key"].replace("_", " "), cls="question-type"), P(json.dumps(item["value"], ensure_ascii=False) if not isinstance(item["value"], str) else item["value"] or "No evidence"), Div(f"Confidence {item['confidence']:.0%} · {item['sentiment']}", cls="subtle"), Div(f'“{item["raw_quote"]}”', cls="quote") if item["raw_quote"] else None, cls="question") for item in answers], cls="panel guide-panel"),
            cls="studio",
        ),
    )
    return app_page(f"Response {conversation['id']}", user, "surveys", *content)
