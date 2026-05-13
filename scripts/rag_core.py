"""Core RAG logic for the Serva-S assistant.

This file is the brain of the project. UI scripts, CLI scripts, and tests
should call this module instead of duplicating search and answer logic.
"""

from __future__ import annotations

import ast
import re
import time
import uuid
from datetime import datetime, timedelta, timezone

import requests
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings

try:
    from .app_config import HEADERS, REQUEST_TIMEOUT, SUPABASE_URL, require_runtime_secrets
    from .llm_client import chat_text
except ImportError:
    from app_config import HEADERS, REQUEST_TIMEOUT, SUPABASE_URL, require_runtime_secrets
    from llm_client import chat_text


require_runtime_secrets()

embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

RULE_CACHE = {"expires_at": 0.0, "text": ""}

SERVICE_SELECT = (
    "id,smm_service_id,name_ar,name_en,description,description_en,category,platform,"
    "price,min_qty,max_qty,active,has_guarantee,guarantee_days,start_time_text,"
    "service_disclaimer,requires_support_chat"
)

STOPWORDS = {
    "اريد", "أريد", "ابي", "أبي", "بدي", "عندي", "هل", "كم", "ما", "هي",
    "عن", "على", "في", "من", "الى", "إلى", "لكم", "لديكم", "خدمة", "خدمات",
    "سعر", "اسعار", "أسعار", "اشتري", "شراء", "ممكن", "فيه", "يوجد",
    "اشتراك", "اشتراكات", "زيادة", "شحن", "عندكم", "لديكم",
    "حقيقي", "حقيقية", "مضمون", "مضمونة", "ضمان", "مضمونه",
    "فقط",
}

TERM_EXPANSIONS = {
    "يوتيوب": ["يوتيوب", "يويتوب", "youtube"],
    "يويتوب": ["يويتوب", "يوتيوب", "youtube"],
    "youtube": ["youtube", "يوتيوب", "يويتوب"],
    "yt": ["youtube", "يوتيوب", "يويتوب"],
    "بريميوم": ["بريميوم", "premium"],
    "premium": ["premium", "بريميوم"],
    "انستقرام": ["انستقرام", "انستجرام", "instagram"],
    "انستجرام": ["انستجرام", "انستقرام", "instagram"],
    "انستا": ["انستقرام", "انستجرام", "instagram"],
    "instagram": ["instagram", "انستقرام", "انستجرام"],
    "ig": ["instagram", "انستقرام", "انستجرام"],
    "تيك": ["تيك", "tiktok", "tik"],
    "توك": ["توك", "tiktok", "tok"],
    "tiktok": ["tiktok", "تيك", "توك"],
    "tt": ["tiktok", "تيك", "توك"],
    "لايكات": ["لايكات", "اعجابات", "إعجابات", "likes", "like"],
    "اعجابات": ["اعجابات", "إعجابات", "لايكات", "likes", "like"],
    "متابعين": ["متابعين", "followers", "follower"],
    "مشاهدات": ["مشاهدات", "views", "view"],
    "مشتركين": ["مشتركين", "subscribers", "subs"],
    "ببجي": ["ببجي", "pubg"],
    "pubg": ["pubg", "ببجي"],
    "uc": ["uc", "pubg", "ببجي"],
    "فري": ["فري", "free fire"],
    "فاير": ["فاير", "free fire"],
    "free": ["free fire", "فري", "فاير"],
    "fire": ["free fire", "فري", "فاير"],
    "اوفيس": ["office", "office 365", "مايكروسوفت"],
    "أوفيس": ["office", "office 365", "مايكروسوفت"],
    "office": ["office", "office 365", "اوفيس", "أوفيس"],
    "كورسيرا": ["coursera"],
    "coursera": ["coursera", "كورسيرا"],
    "جيميني": ["gemini"],
    "جمني": ["gemini"],
    "برو": ["pro", "premium"],
    "gemini": ["gemini", "جيميني", "جمني"],
    "كاب": ["capcut", "cap cut"],
    "كت": ["capcut", "cap cut"],
    "capcut": ["capcut", "cap cut", "كاب كت"],
    "spotify": ["spotify", "سبوتيفاي"],
    "سبوتيفاي": ["spotify", "سبوتيفاي"],
}

SMM_KIND_ALIASES = {
    "followers": ["متابعين", "followers", "follower"],
    "likes": ["لايكات", "اعجابات", "إعجابات", "likes", "like"],
    "views": ["مشاهدات", "views", "view"],
    "subscribers": ["مشتركين", "subscribers", "subs"],
}

NON_DIGITAL_TERMS = ["سيارات", "سيارة", "cars", "car", "عقارات", "عقار", "أدوية", "دواء", "ملابس", "clothes", "طعام"]
HARMFUL_TERMS = ["اختراق", "سرقة", "تزوير", "سبام", "تهكير", "هاك", "hack", "hacking", "spam", "steal", "theft"]
SOCIAL_PRIVATE_TERMS = ["خاص", "private", "مقفل"]
GENERAL_SERVICES_TERMS = ["ماذا تقدمون", "ما خدماتكم", "شو خدماتكم", "ماذا تبيعون"]
SUPPORT_REQUEST_TERMS = [
    "الدعم الفني", "الدعم", "تواصل مع الدعم", "اكلم الدعم", "أكلم الدعم",
    "حولني للدعم", "حوّلني للدعم", "موظف", "خدمة العملاء", "support",
]
NETFLIX_TERMS = ["netflix", "نتفلكس", "نتفليكس", "نيتفلكس"]
CHATGPT_TERMS = ["chatgpt", "chat gpt", "gpt", "شات جي بي تي", "شات جيبيتي", "شات جي بيتي"]
GEMINI_TERMS = ["gemini", "جيميني", "جمني"]
CHEAPEST_TERMS = ["أرخص", "ارخص", "الأرخص", "اقل سعر", "أقل سعر", "cheap", "cheapest"]

SYSTEM_PROMPT = """
أنت المساعد الذكي الرسمي لمتجر Serva-S.
دورك مساعدة العميل في فهم الخدمات والسياسات والشراء بأسلوب عربي واضح ومهني.

[السياق المسترجع من قاعدة المعرفة]:
{context}

[قواعد صارمة]:
1. أجب بنفس لغة العميل: إن كتب بالعربية فالعربية، وإن كتب بالإنجليزية فالإنجليزية. لا تخلط اللغتين إلا إذا كان سؤال العميل مختلطًا.
2. لا تخترع خدمة أو سعرًا أو سياسة غير موجودة في السياق.
3. إذا كان السؤال عامًا بدون منصة مثل "أريد متابعين"، اسأل عن المنصة أولًا.
   أما إذا ذكر العميل المنصة ونوع الخدمة مثل "متابعين تيك توك" أو "لايكات انستقرام"، فلا تسأله عن المنصة مرة أخرى واعرض الخدمات المطابقة من السياق.
4. إذا كانت الخدمة "غير متوفرة حاليًا" أو "معطلة"، قل ذلك بوضوح ولا تشجع العميل على طلبها.
5. إذا لم تجد معلومة كافية، اعتذر ووجّه العميل للدعم بدل التخمين.
6. اجعل الرد مختصرًا ومفيدًا. عند وجود خيارات كثيرة، اعرض أفضل 3 خيارات فقط افتراضيًا، ولا تعرض قائمة طويلة إلا إذا طلب العميل "كل الخيارات" أو "القائمة كاملة".
7. إذا طلب العميل الأرخص، ابدأ بأرخص خيار واضح مع السعر والحالة، ولا تعرض القائمة الكاملة إلا إذا طلبها.
8. لا تكرر التحية في كل رد. استخدم التحية فقط عند رد مباشر على تحية أو بداية محادثة عامة.
9. استخدم تنسيقًا بسيطًا وواضحًا عند عرض أكثر من خيار.
10. خدمات SMM مثل المتابعين واللايكات والمشاهدات ليست تفاعلًا عضويًا طبيعيًا؛ إذا سألك العميل هل هي حقيقية، قل بوضوح إنها خدمات SMM لزيادة الأرقام أو التفاعل وليست تفاعلًا عضويًا طبيعيًا.
11. الضمان في خدمات SMM يعني التعويض أو المتابعة حسب بيانات الخدمة فقط، ولا يعني جودة حقيقية أو تفاعلًا طبيعيًا. اذكر الضمان فقط إذا كان موجودًا في سياق الخدمة.
12. لا تقل إن خدمة SMM تعتمد على إعلانات أو مستخدمين حقيقيين أو حسابات حقيقية أو تفاعل عضوي إلا إذا ورد ذلك نصًا في سياق الخدمة.
13. عند عرض خدمة محددة موجودة في السياق، اذكر الاسم والحالة والسعر والضمان فقط.
14. لا تعرض أي روابط URL أو روابط Markdown نهائيًا. بدل الرابط المباشر، وجّه العميل إلى البحث من الصفحة الرئيسية عن اسم الخدمة.
15. عند شرح طريقة طلب أي خدمة، استخدم الصياغة المختصرة: من الصفحة الرئيسية ابحث عن اسم الخدمة، افتح الخدمة المناسبة، املأ المعلومات المطلوبة، ثم أكّد الطلب. لا تطلب من العميل إرسال بيانات الطلب داخل المحادثة إلا في حالات الدعم.
16. إذا طلب العميل الدعم، لا تدّعِ وجود تحويل تلقائي ولا تطلب منه إنشاء طلب دعم منفصل. وضّح أن هذه المحادثة نفسها هي تذكرة الدعم، واطلب رقم الطلب ووصف المشكلة هنا.
"""


def supabase_get(table: str, params: dict) -> requests.Response:
    return requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )


def supabase_post(path: str, payload: dict) -> requests.Response:
    return requests.post(
        f"{SUPABASE_URL}/rest/v1/{path}",
        headers=HEADERS,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )


def load_answer_rules(limit: int = 20) -> str:
    """Load dynamic safety rules from ai_safety_rules."""
    now = time.time()
    if RULE_CACHE["expires_at"] > now:
        return RULE_CACHE["text"]

    try:
        response = supabase_get(
            "ai_safety_rules",
            {
                "select": "rule_type,title,instruction,severity",
                "is_active": "eq.true",
                "order": "severity.desc",
                "limit": str(limit),
            },
        )
        if response.status_code != 200:
            RULE_CACHE.update({"expires_at": now + 60, "text": ""})
            return ""

        rules = [
            f"- [{row.get('rule_type', 'rule')}] {row.get('title', '')}: {row.get('instruction', '')}"
            for row in response.json()
        ]
        text = "\n".join(rules)
        RULE_CACHE.update({"expires_at": now + 300, "text": text})
        return text
    except Exception as exc:
        print(f"⚠️ تعذر تحميل قواعد الأمان: {exc}")
        RULE_CACHE.update({"expires_at": now + 60, "text": ""})
        return ""


def save_message(session_id: str, role: str, message: str) -> None:
    try:
        supabase_post(
            "chat_sessions",
            {"session_id": session_id, "role": role, "message": message},
        )
    except Exception as exc:
        print(f"⚠️ تعذر حفظ الرسالة: {exc}")


def load_history(session_id: str, limit: int = 20) -> list[HumanMessage | AIMessage]:
    try:
        response = supabase_get(
            "chat_sessions",
            {
                "session_id": f"eq.{session_id}",
                "order": "created_at.desc",
                "limit": str(limit),
            },
        )
        if response.status_code != 200:
            return []

        messages = []
        for row in reversed(response.json()):
            cls = HumanMessage if row.get("role") == "user" else AIMessage
            messages.append(cls(content=row.get("message", "")))
        return messages
    except Exception as exc:
        print(f"⚠️ تعذر تحميل الذاكرة: {exc}")
        return []


def rewrite_query(question: str) -> str:
    prompt = f"""
أعد صياغة سؤال العميل ليكون أفضل للبحث في قاعدة خدمات رقمية.
إذا كان واضحًا، أعده كما هو. لا تشرح.

    السؤال: {question}
"""
    try:
        improved = chat_text([HumanMessage(content=prompt)], helper=True).strip().strip('"')
        return improved if len(improved) > 3 else question
    except Exception:
        return question


def rerank_results(question: str, results: list[dict], limit: int = 3) -> list[dict]:
    if len(results) <= limit:
        return results

    choices = "\n".join(
        f"[{index + 1}] {row.get('content', '')[:180]}"
        for index, row in enumerate(results)
    )
    prompt = f"""
اختر أكثر النتائج صلة بسؤال العميل.

السؤال: {question}

النتائج:
{choices}

أعد أرقام أفضل {limit} نتائج فقط، مفصولة بفواصل. مثال: 1,3,5
"""
    try:
        response = chat_text([HumanMessage(content=prompt)], helper=True)
        numbers = re.findall(r"\d+", response)
        indexes = [int(n) - 1 for n in numbers if 0 < int(n) <= len(results)]
        return [results[i] for i in indexes[:limit]] or results[:limit]
    except Exception:
        return results[:limit]


def is_smm_service(service: dict) -> bool:
    provider_id = str(service.get("smm_service_id") or "").lower()
    if not provider_id:
        return False
    if provider_id.startswith("swgames:"):
        return False

    text = normalize_search_text(
        " ".join(
            [
                service.get("name_ar") or "",
                service.get("name_en") or "",
                service.get("platform") or "",
                service.get("category") or "",
                service.get("description") or "",
                service.get("description_en") or "",
            ]
        )
    )
    smm_terms = [
        "متابع", "لايك", "اعجاب", "إعجاب", "مشاهد", "مشترك", "تفاعل",
        "followers", "likes", "views", "subscribers", "instagram",
        "tiktok", "youtube", "telegram", "facebook", "twitter", "snap",
    ]
    return any(term.lower() in text for term in smm_terms)


def service_to_context(service: dict) -> str:
    service_id = service.get("smm_service_id") or service.get("id") or ""
    title = service.get("name_ar") or service.get("name_en") or "خدمة بدون اسم"
    description = service.get("description") or service.get("description_en") or "لا يوجد وصف"
    is_active = service.get("active") is True
    is_smm = is_smm_service(service)
    status = "متاحة حاليًا" if is_active else "غير متوفرة حاليًا / معطلة"

    lines = [
        f"الخدمة: {title}",
        f"الحالة: {status}",
        f"نوع الخدمة: {'SMM - زيادة أرقام أو تفاعل، وليست تفاعلًا عضويًا طبيعيًا' if is_smm else 'خدمة رقمية'}",
        f"المنصة: {service.get('platform') or 'غير محدد'}",
        f"القسم: {service.get('category') or 'غير محدد'}",
        f"الوصف: {description}",
        f"السعر: {service.get('price') or 0}$",
        f"الحد الأدنى للكمية: {service.get('min_qty') or 'غير محدد'}",
        f"الحد الأقصى للكمية: {service.get('max_qty') or 'غير محدد'}",
        f"يوجد ضمان: {'نعم' if service.get('has_guarantee') else 'لا'}",
        f"مدة الضمان بالأيام: {service.get('guarantee_days') or 0}",
        f"وقت البدء المتوقع: {service.get('start_time_text') or 'غير محدد'}",
    ]
    if service.get("service_disclaimer"):
        lines.append(f"تنبيه الخدمة: {service['service_disclaimer']}")
    if is_smm:
        lines.append(
            "ملاحظة SMM: لا تصف هذه الخدمة بأنها حقيقية أو عضوية. "
            "الضمان، إن وجد، يعني التعويض أو المتابعة حسب بيانات الخدمة فقط."
        )
    if is_active:
        lines.append(
            "طريقة الطلب: من الصفحة الرئيسية ابحث عن اسم الخدمة، افتح الخدمة المناسبة، "
            "املأ المعلومات المطلوبة داخل نموذج الطلب، ثم أكّد الطلب."
        )
    else:
        lines.append("تنبيه مهم: هذه الخدمة معطلة وغير متوفرة للطلب حاليًا. لا تشجع العميل على شرائها.")
    return "\n".join(lines)


def money(value) -> str:
    try:
        number = float(value)
        return f"{number:g}$"
    except (TypeError, ValueError):
        return f"{value}$" if value not in (None, "") else "غير محدد"


def preferred_language(text: str) -> str:
    """Return 'en' only when the user message is clearly English-first."""
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text or ""))
    english_chars = len(re.findall(r"[a-zA-Z]", text or ""))
    if arabic_chars:
        return "ar"
    return "en" if english_chars else "ar"


def order_instruction(language: str = "ar", extra: str = "") -> str:
    if language == "en":
        base = (
            "To order: go to the home page, search for the service name, open the matching service, "
            "fill in the required information in the order form, then confirm the order."
        )
        return f"{base} {extra}".strip()

    base = (
        "طريقة الطلب: من الصفحة الرئيسية ابحث عن اسم الخدمة التي تريدها، افتح الخدمة المناسبة، "
        "املأ المعلومات المطلوبة داخل نموذج الطلب، ثم أكّد الطلب."
    )
    return f"{base} {extra}".strip()


def support_instruction(language: str = "ar", include_order_number: bool = True) -> str:
    if language == "en":
        details = (
            "Send your order number if you have one, briefly describe the issue, "
            "and attach proof or a screenshot when needed."
            if include_order_number
            else "Briefly describe the issue and attach proof or a screenshot when needed."
        )
        return f"This chat is your support ticket. {details}"

    details = (
        "اكتب رقم الطلب إن وجد، واشرح المشكلة باختصار، وأرفق أي إثبات أو صورة عند الحاجة."
        if include_order_number
        else "اشرح المشكلة باختصار، وأرفق أي إثبات أو صورة عند الحاجة."
    )
    return f"هذه المحادثة هي تذكرة الدعم الخاصة بك. {details}"


def wants_cheapest(text: str) -> bool:
    return has_any(text, CHEAPEST_TERMS)


def is_plain_greeting(text: str) -> bool:
    normalized = normalize_search_text(text)
    greeting_terms = ["مرحبا", "مرحبًا", "اهلا", "أهلا", "أهلاً", "السلام عليكم", "hi", "hello"]
    return len(normalized) <= 40 and has_any(normalized, greeting_terms)


def remove_repetitive_greeting(answer: str, user_message: str) -> str:
    if is_plain_greeting(user_message):
        return answer

    patterns = [
        r"^\s*أهلاً بك(?:م)?(?: في متجر Serva-S)?[!.؟،.\s]*",
        r"^\s*أهلا بك(?:م)?(?: في متجر Serva-S)?[!.؟،.\s]*",
        r"^\s*مرحبًا بك(?:م)?(?: في متجر Serva-S)?[!.؟،.\s]*",
        r"^\s*مرحباً بك(?:م)?(?: في متجر Serva-S)?[!.؟،.\s]*",
    ]
    cleaned = answer
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, count=1)
    return cleaned.lstrip()


def history_text(history: list | None) -> str:
    parts = []
    for item in history or []:
        if isinstance(item, (list, tuple)):
            parts.extend(str(part or "") for part in item)
        elif isinstance(item, dict):
            parts.append(str(item.get("content", "")))
        else:
            parts.append(str(item))
    return " ".join(parts).lower()


def contextualize_followup(message: str, history: list | None) -> str:
    """Make short follow-ups searchable without changing standalone questions."""
    text = message.strip()
    normalized = normalize_search_text(text)
    prior = history_text(history)
    if not prior:
        return text

    if wants_cheapest(normalized) or normalized in {"والأرخص؟", "والارخص؟", "ارخص؟", "الأرخص؟"}:
        if has_any(prior, ["pubg", "ببجي", "uc"]):
            return "cheapest PUBG UC" if preferred_language(text) == "en" else "أرخص شحن ببجي UC"
        if has_any(prior, ["free fire", "فري فاير"]):
            return "cheapest Free Fire top up" if preferred_language(text) == "en" else "أرخص شحن فري فاير"

    if has_any(normalized, ["available", "متوفر", "متاحة", "متوفره"]):
        if has_any(prior, CHATGPT_TERMS):
            return "Is ChatGPT available now?" if preferred_language(text) == "en" else "هل ChatGPT متوفر الآن؟"

    if has_any(normalized, ["بديل", "alternative"]):
        if has_any(prior, ["capcut", "cap cut", "كاب", "CAPCUT".lower()]):
            return "CapCut alternative" if preferred_language(text) == "en" else "بديل CapCut"

    return text


def service_name(service: dict) -> str:
    return service.get("name_ar") or service.get("name_en") or "خدمة بدون اسم"


def service_scope_text(service: dict) -> str:
    return normalize_search_text(
        " ".join(
            [
                service_name(service),
                service.get("platform") or "",
                service.get("category") or "",
                service.get("description") or "",
                service.get("description_en") or "",
            ]
        )
    )


def fetch_services_for_terms(terms: list[str], limit: int = 80) -> list[dict]:
    services_by_id = {}
    for term in terms:
        response = supabase_get(
            "services",
            {
                "select": SERVICE_SELECT,
                "or": (
                    f"(name_ar.ilike.*{term}*,name_en.ilike.*{term}*,"
                    f"description.ilike.*{term}*,description_en.ilike.*{term}*,"
                    f"platform.ilike.*{term}*,category.ilike.*{term}*)"
                ),
                "limit": str(limit),
            },
        )
        if response.status_code != 200:
            continue

        for service in response.json():
            service_id = service.get("id")
            if service_id:
                services_by_id[service_id] = service
    return list(services_by_id.values())


def sort_services_by_price(services: list[dict]) -> list[dict]:
    return sorted(
        services,
        key=lambda service: (
            service.get("active") is not True,
            float(service.get("price") or 0),
            service_name(service).lower(),
        ),
    )


def format_service_options(
    services: list[dict],
    include_status: bool = False,
    limit: int | None = None,
) -> str:
    lines = []
    sorted_services = sort_services_by_price(services)
    if limit is not None:
        sorted_services = sorted_services[:limit]

    for index, service in enumerate(sorted_services, start=1):
        status = "متاحة" if service.get("active") is True else "غير متوفرة حاليًا"
        details = [
            f"{index}. {service_name(service)}",
            f"السعر: {money(service.get('price'))}",
        ]
        if include_status:
            details.append(f"الحالة: {status}")
        if service.get("has_guarantee"):
            details.append(f"الضمان: {service.get('guarantee_days') or 0} يوم")
        lines.append(" - ".join(details))
    return "\n".join(lines)


def format_service_options_en(
    services: list[dict],
    include_status: bool = False,
    limit: int | None = None,
) -> str:
    lines = []
    sorted_services = sort_services_by_price(services)
    if limit is not None:
        sorted_services = sorted_services[:limit]

    for index, service in enumerate(sorted_services, start=1):
        status = "available" if service.get("active") is True else "not available"
        details = [
            f"{index}. {service_name(service)}",
            f"price: {money(service.get('price'))}",
        ]
        if include_status:
            details.append(f"status: {status}")
        if service.get("has_guarantee"):
            details.append(f"guarantee: {service.get('guarantee_days') or 0} days")
        lines.append(" - ".join(details))
    return "\n".join(lines)


def chatgpt_status_answer(message: str) -> str | None:
    services = [
        service for service in fetch_services_for_terms(CHATGPT_TERMS)
        if has_any(service_scope_text(service), CHATGPT_TERMS)
    ]
    active_services = [service for service in services if service.get("active") is True]

    if not services or not active_services:
        if preferred_language(message) == "en":
            return (
                "ChatGPT services are not available right now, so they cannot be purchased at the moment. "
                "You can check again later or choose another available AI service such as Gemini if it fits your needs."
            )
        return (
            "خدمات ChatGPT غير متوفرة حاليًا، لذلك لا يمكن شراؤها الآن. "
            "يمكنك متابعة توفرها لاحقًا أو اختيار خدمة ذكاء اصطناعي أخرى متاحة مثل Gemini إذا كانت مناسبة لك."
        )

    options = format_service_options(active_services, include_status=True, limit=3)
    if preferred_language(message) == "en":
        return (
            "These ChatGPT services are currently available:\n"
            f"{options}\n\n"
            f"{order_instruction('en')}"
        )
    return (
        "هذه خدمات ChatGPT المتاحة حاليًا:\n"
        f"{options}\n\n"
        f"{order_instruction('ar')}"
    )


def direct_catalog_answer(message: str) -> str | None:
    text = message.strip().lower()

    if has_any(text, SUPPORT_REQUEST_TERMS):
        if preferred_language(message) == "en":
            return support_instruction("en")
        return support_instruction("ar")

    if has_any(text, CHATGPT_TERMS) and not has_any(text, GEMINI_TERMS):
        return chatgpt_status_answer(message)

    if has_any(text, NETFLIX_TERMS):
        services = [
            service for service in fetch_services_for_terms(NETFLIX_TERMS)
            if has_any(service_scope_text(service), NETFLIX_TERMS)
        ]
        active_services = [service for service in services if service.get("active") is True]
        if preferred_language(message) == "en":
            if active_services:
                return (
                    "Yes, these Netflix services are currently available:\n"
                    f"{format_service_options_en(active_services, include_status=True, limit=3)}\n\n"
                    f"{order_instruction('en')}"
                )
            return (
                "Netflix is not available right now, so I cannot show packages or prices for it. "
                "You can choose another available digital service inside the site."
            )
        if active_services:
            return (
                "نعم، هذه خدمات Netflix المتاحة حاليًا حسب بيانات الموقع:\n"
                f"{format_service_options(active_services, include_status=True)}\n\n"
                f"{order_instruction('ar')}"
            )
        if services:
            return (
                "خدمة Netflix موجودة في البيانات لكنها غير متوفرة حاليًا، لذلك لا أنصحك بطلبها الآن. "
                "يمكنك اختيار خدمة رقمية أخرى متاحة داخل الموقع أو متابعة توفرها لاحقًا."
            )
        return (
            "لا، لا تتوفر لدينا خدمة Netflix حاليًا في متجر Serva-S. "
            "لذلك لا أستطيع عرض أسعار أو باقات لها. يمكنك اختيار خدمة رقمية أخرى متاحة داخل الموقع."
        )

    if has_any(text, ["يوتيوب بريميوم", "youtube premium"]):
        services = [
            service for service in fetch_services_for_terms(["youtube premium", "يوتيوب بريميوم"])
            if "premium" in service_scope_text(service) or "بريميوم" in service_scope_text(service)
        ]
        active_services = [service for service in services if service.get("active") is True]
        if not active_services:
            return None

        options = format_service_options(active_services, include_status=True)
        if len(active_services) == 1:
            intro = "المتوفر حاليًا ليوتيوب بريميوم هو:"
            duration_note = "إذا كنت تريد مدة مختلفة، أخبرني بالمدة المطلوبة لأتأكد لك إن كانت متاحة."
        else:
            intro = "هذه مدد يوتيوب بريميوم المتاحة حاليًا، اختر المدة التي تناسبك:"
            duration_note = "اختر المدة التي تريدها قبل تأكيد الطلب."

        if preferred_language(message) == "en":
            en_options = format_service_options_en(active_services, include_status=True)
            return (
                f"These YouTube Premium durations are currently available:\n{en_options}\n\n"
                f"{order_instruction('en', 'Enter the email you want the subscription activated on inside the order form only, not in this chat.')}"
            )

        return (
            f"{intro}\n{options}\n\n"
            f"{order_instruction('ar', 'اكتب البريد الذي تريد تفعيل الاشتراك عليه داخل نموذج الطلب فقط، وليس داخل المحادثة.')}\n\n"
            f"{duration_note}"
        )

    if has_any(text, ["ببجي", "pubg", "uc"]) and has_any(text, ["فري فاير", "free fire"]):
        if preferred_language(message) == "en":
            return (
                "Both PUBG UC and Free Fire top-ups are available. "
                "Tell me which game you want first, or ask for the cheapest option for one of them, and I will show the matching packages."
            )
        return (
            "يتوفر لدينا شحن ببجي UC وشحن فري فاير. "
            "حدد اللعبة التي تريدها أولًا، أو اطلب الأرخص لإحداهما، وسأعرض لك الباقات المطابقة."
        )

    if has_any(text, ["غير ببجي", "not pubg", "except pubg"]) and has_any(text, ["لعبة", "ألعاب", "game", "games"]):
        if preferred_language(message) == "en":
            return (
                "For games other than PUBG, Free Fire top-ups are available. "
                "Tell me the game name or ask for Free Fire packages, and I will show the matching options."
            )
        return (
            "لخدمات الألعاب غير ببجي، يتوفر لدينا شحن فري فاير وخدمات ألعاب أخرى حسب المتاح. "
            "حدد اسم اللعبة أو اطلب باقات فري فاير لأعرض لك الخيارات المطابقة."
        )

    if has_any(text, ["ببجي", "pubg", "uc"]) and not has_any(text, ["غير ببجي", "not pubg", "except pubg"]):
        services = [
            service for service in fetch_services_for_terms(["pubg", "ببجي", "uc"])
            if service.get("active") is True
            and ("pubg" in service_scope_text(service) or "ببجي" in service_scope_text(service))
            and "uc" in service_name(service).lower()
        ]
        if not services:
            return None

        if wants_cheapest(text):
            cheapest = sort_services_by_price(services)[0]
            if preferred_language(message) == "en":
                return (
                    "The cheapest available PUBG UC package is:\n"
                    f"{format_service_options_en([cheapest])}\n\n"
                    f"{order_instruction('en', 'Enter the Player ID and player name accurately. No account password is needed.')}"
                )
            return (
                "أرخص باقة شحن ببجي UC متاحة حاليًا هي:\n"
                f"{format_service_options([cheapest])}\n\n"
                f"{order_instruction('ar', 'اكتب Player ID واسم اللاعب بدقة داخل نموذج الطلب. لا تحتاج إلى كلمة مرور الحساب.')}"
            )

        if preferred_language(message) == "en":
            return (
                "Yes, these PUBG UC packages are currently available, sorted by price:\n"
                f"{format_service_options_en(services)}\n\n"
                f"{order_instruction('en', 'Enter the Player ID and player name accurately. No account password is needed.')}"
            )

        return (
            "نعم، هذه باقات شحن ببجي UC المتاحة حاليًا مرتبة حسب السعر:\n"
            f"{format_service_options(services)}\n\n"
            f"{order_instruction('ar', 'اكتب Player ID واسم اللاعب بدقة داخل نموذج الطلب. لا تحتاج إلى كلمة مرور الحساب.')}"
        )

    if has_any(text, ["فري فاير", "free fire"]):
        services = [
            service for service in fetch_services_for_terms(["free fire", "فري فاير"])
            if service.get("active") is True
            and ("free fire" in service_scope_text(service) or "فري فاير" in service_scope_text(service))
        ]
        if not services:
            return None

        if wants_cheapest(text):
            cheapest = sort_services_by_price(services)[0]
            if preferred_language(message) == "en":
                return (
                    "The cheapest available Free Fire top-up option is:\n"
                    f"{format_service_options_en([cheapest])}\n\n"
                    f"{order_instruction('en', 'Enter the Player ID accurately inside the order form.')}"
                )
            return (
                "أرخص خيار شحن فري فاير متاح حاليًا هو:\n"
                f"{format_service_options([cheapest])}\n\n"
                f"{order_instruction('ar', 'اكتب Player ID بدقة داخل نموذج الطلب.')}"
            )

        if preferred_language(message) == "en":
            return (
                "These Free Fire top-up options are currently available, sorted by price:\n"
                f"{format_service_options_en(services)}\n\n"
                f"{order_instruction('en', 'Enter the Player ID accurately inside the order form.')}"
            )

        return (
            "هذه خدمات شحن فري فاير المتاحة حاليًا مرتبة حسب السعر:\n"
            f"{format_service_options(services)}\n\n"
            f"{order_instruction('ar', 'اكتب Player ID بدقة داخل نموذج الطلب.')}"
        )

    return None


def extract_lookup_terms(question: str, limit: int = 4) -> list[str]:
    words = re.findall(r"[\w\u0600-\u06FF،؟]+", str(question))
    terms = []
    for word in words:
        term = word.strip(".,!?،؟:؛()[]{}\"'")
        if term.startswith("و") and len(term) > 4:
            term = term[1:]
        if len(term) < 3 or term in STOPWORDS:
            continue
        terms.append(term)
    return terms[:limit]


def expand_lookup_terms(terms: list[str]) -> list[str]:
    expanded = []
    for term in terms:
        aliases = TERM_EXPANSIONS.get(term.lower(), [term])
        for alias in aliases:
            if alias not in expanded:
                expanded.append(alias)
    return expanded


def normalize_search_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower())


def detect_requested_smm_kind(terms: list[str]) -> str | None:
    text = normalize_search_text(" ".join(terms))
    for kind, aliases in SMM_KIND_ALIASES.items():
        if any(normalize_search_text(alias) in text for alias in aliases):
            return kind
    return None


def text_has_smm_kind(text: str, kind: str) -> bool:
    text = normalize_search_text(text)
    return any(normalize_search_text(alias) in text for alias in SMM_KIND_ALIASES.get(kind, []))


def text_has_other_smm_kind(text: str, requested_kind: str) -> bool:
    return any(
        kind != requested_kind and text_has_smm_kind(text, kind)
        for kind in SMM_KIND_ALIASES
    )


def score_service_match(service: dict, original_terms: list[str], expanded_terms: list[str]) -> int:
    name_text = normalize_search_text(
        " ".join(
            [
                service.get("name_ar") or "",
                service.get("name_en") or "",
                service.get("platform") or "",
                service.get("category") or "",
            ]
        )
    )
    all_text = normalize_search_text(
        " ".join(
            [
                name_text,
                service.get("description") or "",
                service.get("description_en") or "",
            ]
        )
    )

    score = 0
    matched_original_groups = 0

    for term in original_terms:
        aliases = TERM_EXPANSIONS.get(term.lower(), [term])
        matched = False
        for alias in aliases:
            alias_norm = normalize_search_text(alias)
            if alias_norm and alias_norm in all_text:
                matched = True
                score += 3
                if alias_norm in name_text:
                    score += 5
        if matched:
            matched_original_groups += 1

    if original_terms and matched_original_groups == len(original_terms):
        score += 10
    if len(original_terms) > 1 and matched_original_groups >= 2:
        score += 8

    for term in expanded_terms:
        term_norm = normalize_search_text(term)
        if term_norm and term_norm in name_text:
            score += 1

    if service.get("active") is True:
        score += 1

    requested_kind = detect_requested_smm_kind(original_terms)
    if requested_kind:
        if text_has_smm_kind(name_text, requested_kind):
            score += 35
        elif text_has_other_smm_kind(name_text, requested_kind):
            score -= 35

    return score


def count_service_term_matches(service: dict, original_terms: list[str]) -> int:
    all_text = normalize_search_text(
        " ".join(
            [
                service.get("name_ar") or "",
                service.get("name_en") or "",
                service.get("platform") or "",
                service.get("category") or "",
                service.get("description") or "",
                service.get("description_en") or "",
            ]
        )
    )
    matches = 0
    for term in original_terms:
        aliases = TERM_EXPANSIONS.get(term.lower(), [term])
        if any(normalize_search_text(alias) in all_text for alias in aliases):
            matches += 1
    return matches


def lookup_services_by_keywords(question: str, limit: int = 6) -> list[dict]:
    """Direct live lookup from services, so active/disabled status is current."""
    services_by_id = {}
    original_terms = extract_lookup_terms(question, limit=6)
    expanded_terms = expand_lookup_terms(original_terms)

    for term in expanded_terms:
        try:
            response = supabase_get(
                "services",
                {
                    "select": SERVICE_SELECT,
                    "or": (
                        f"(name_ar.ilike.*{term}*,name_en.ilike.*{term}*,"
                        f"description.ilike.*{term}*,description_en.ilike.*{term}*,"
                        f"platform.ilike.*{term}*,category.ilike.*{term}*)"
                    ),
                    "limit": "25",
                },
            )
        except requests.RequestException as exc:
            print(f"⚠️ تعذر البحث المباشر عن '{term}': {exc}")
            continue

        if response.status_code != 200:
            continue

        for service in response.json():
            service_id = service.get("id")
            if service_id:
                services_by_id[service_id] = service

    services = list(services_by_id.values())
    if len(original_terms) >= 2:
        strong_matches = [
            service for service in services
            if count_service_term_matches(service, original_terms) >= 2
        ]
        if strong_matches:
            services = strong_matches

    scored_services = sorted(
        services,
        key=lambda service: score_service_match(service, original_terms, expanded_terms),
        reverse=True,
    )
    return [
        {
            "content": service_to_context(service),
            "similarity": score_service_match(service, original_terms, expanded_terms),
        }
        for service in scored_services[:limit]
    ]


def vector_search(question: str) -> list[dict]:
    """Search old ai_documents and new ai_knowledge_documents."""
    vector = embeddings_model.embed_query(question)
    results = []

    service_response = supabase_post(
        "rpc/match_services",
        {"query_embedding": vector, "match_threshold": 0.25, "match_count": 8},
    )
    if service_response.status_code == 200:
        results.extend(service_response.json())

    knowledge_response = supabase_post(
        "rpc/match_knowledge_documents",
        {
            "query_embedding": vector,
            "match_threshold": 0.25,
            "match_count": 8,
            "filter_types": None,
        },
    )
    if knowledge_response.status_code == 200:
        for row in knowledge_response.json():
            title = row.get("title") or "وثيقة معرفة"
            doc_type = row.get("document_type") or "knowledge"
            content = row.get("content") or ""
            results.append({
                "content": f"[{doc_type}] {title}\n{content}",
                "similarity": row.get("similarity", 0),
            })

    return results


def search_knowledge(question: str) -> list[dict]:
    """Combine live keyword lookup with vector search."""
    direct_results = lookup_services_by_keywords(question)
    if direct_results and direct_results[0].get("similarity", 0) >= 30:
        return direct_results

    try:
        return direct_results + vector_search(question)
    except Exception as exc:
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
            print("⚠️ حصة Google Embeddings ممتلئة؛ سيتم استخدام البحث النصي المباشر فقط.")
        else:
            print(f"⚠️ فشل البحث المتجهي: {exc}")
        return direct_results


def build_context(results: list[dict]) -> str:
    if not results:
        return "لا توجد خدمات أو معلومات مطابقة لهذا الطلب."
    return "\n---\n".join(row.get("content", "") for row in results)


def parse_model_content(content) -> str:
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        content = "\n".join(parts)

    text = str(content).strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if parsed and isinstance(parsed, list):
                first = parsed[0]
                if isinstance(first, dict) and "text" in first:
                    return first["text"].strip()
                if isinstance(first, str):
                    return first.strip()
        except Exception:
            pass
    return text


def strip_disallowed_output(text: str) -> str:
    """Remove URLs, Markdown links, and internal debug markers from an answer."""
    cleaned = text
    cleaned = re.sub(r"(?m)^\s*(?:[*-]\s*)?\[SERVA_[A-Z_]+\].*$", "", cleaned)
    cleaned = re.sub(r"\[SERVA_[A-Z_]+\].*?\[/SERVA_[A-Z_]+\]", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\[/?SERVA_[A-Z_]+\]", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"(?i)\b(?:https?://)?(?:www\.)?serva-s\.com(?:/[^\s\)\]]*)?", "الموقع", cleaned)
    cleaned = re.sub(r"(?i)\b(?:https?://|www\.)[^\s\)\]]+", "", cleaned)
    cleaned = re.sub(r"(?i)\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}(?:/[^\s\)\]]*)?", "", cleaned)
    cleaned = cleaned.replace("موقعنا الموقع", "الموقع")
    cleaned = cleaned.replace("الموقع الموقع", "الموقع")
    cleaned = cleaned.replace("على موقعنا: الموقع", "داخل الموقع")
    cleaned = cleaned.replace("على موقعنا: الموقع.", "داخل الموقع.")
    cleaned = cleaned.replace("لا تعرض رابطًا مباشرًا، ولكن", "")
    cleaned = cleaned.replace("لا تعرض رابطًا مباشرًا", "")
    cleaned = cleaned.replace("يمكنك الاطلاع على تفاصيلها هنا: الموقع", "يمكنك اختيار الخدمة بالاسم داخل الموقع")
    cleaned = cleaned.replace("يمكنك الاطلاع على تفاصيلها هنا: الموقع.", "يمكنك اختيار الخدمة بالاسم داخل الموقع.")
    cleaned = cleaned.replace("رابط الطلب:", "طريقة الطلب:")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def apply_guardrails(answer: str, context: str, user_message: str = "") -> str:
    cleaned = strip_disallowed_output(answer)

    cleaned = cleaned.replace(
        "يرجى تزويدي ببريدك الإلكتروني",
        "أدخل البريد الإلكتروني المطلوب داخل نموذج الطلب عند الشراء",
    )
    cleaned = cleaned.replace(
        "يرجى تزويدي ببريدك الإلكتروني.",
        "أدخل البريد الإلكتروني المطلوب داخل نموذج الطلب عند الشراء.",
    )

    prices_in_answer = re.findall(r"(\d+\.?\d*)\$", cleaned)
    prices_in_context = re.findall(r"(\d+\.?\d*)\$", context)
    for price in prices_in_answer:
        if price not in prices_in_context and "لا توجد" not in context:
            cleaned = cleaned.replace(f"{price}$", f"{price}$ ⚠️")

    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", cleaned))
    total_letters = len(re.findall(r"[a-zA-Z\u0600-\u06FF]", cleaned))
    if preferred_language(user_message) == "ar" and total_letters and arabic_chars / total_letters < 0.3:
        cleaned += "\n\n_(الرد ليس عربيًا بما يكفي. يرجى المحاولة مرة أخرى.)_"

    if "نوع الخدمة: SMM" in context:
        cleaned = cleaned.replace("وذلك من خلال استخدام الإعلانات على المنصة", "حسب بيانات الخدمة فقط")
        cleaned = cleaned.replace("من خلال استخدام الإعلانات على المنصة", "حسب بيانات الخدمة فقط")
        cleaned = cleaned.replace("تعتمد على استخدام الإعلانات", "هي خدمة SMM لزيادة الأرقام أو التفاعل")
        cleaned = cleaned.replace("نضمن وصول عدد الإعجابات المطلوبة فقط", "نذكر الضمان فقط حسب بيانات الخدمة")
        if "استخدام الإعلانات" in cleaned or "تستخدم الإعلانات" in cleaned:
            cleaned += (
                "\n\nتوضيح مهم: لا يوجد في بيانات الخدمة ما يثبت أنها تعتمد على إعلانات. "
                "خدمات SMM هنا هي زيادة أرقام أو تفاعل وليست تفاعلًا عضويًا طبيعيًا، "
                "والضمان إن وجد يعني التعويض أو المتابعة حسب بيانات الخدمة فقط."
            )

    cleaned = remove_repetitive_greeting(cleaned, user_message)
    return strip_disallowed_output(cleaned)


def gradio_history_to_messages(history: list) -> list[HumanMessage | AIMessage]:
    messages = []
    for item in history or []:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            user_msg, ai_msg = item
            if user_msg:
                messages.append(HumanMessage(content=str(user_msg)))
            if ai_msg:
                messages.append(AIMessage(content=str(ai_msg)))
        elif isinstance(item, dict):
            role = item.get("role")
            content = str(item.get("content", ""))
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    return messages


def has_any(text: str, terms: list[str]) -> bool:
    text = text.lower()
    return any(term.lower() in text for term in terms)


def direct_policy_answer(message: str) -> str | None:
    text = message.strip().lower()

    if has_any(text, HARMFUL_TERMS):
        if preferred_language(message) == "en":
            return (
                "I can't help with hacking, theft, spam, or any harmful activity. "
                "I can only help with legal digital services available inside Serva-S."
            )
        return (
            "لا أستطيع المساعدة في طلبات الاختراق أو السرقة أو السبام أو أي نشاط ضار. "
            "أقدر أساعدك فقط في الخدمات الرقمية القانونية والمتاحة داخل متجر Serva-S."
        )

    if has_any(text, NON_DIGITAL_TERMS):
        if preferred_language(message) == "en":
            return (
                "No, Serva-S specializes in digital services only and does not sell physical products of this type. "
                "Tell me which digital service you need, such as social media services, subscriptions, or game top-ups."
            )
        return (
            "لا، متجر Serva-S متخصص بالخدمات الرقمية فقط، ولا يبيع منتجات مادية أو غير رقمية من هذا النوع. "
            "إذا أردت خدمة رقمية مثل خدمات السوشيال ميديا أو الاشتراكات أو شحن الألعاب، أخبرني بما تحتاجه."
        )

    if has_any(text, GENERAL_SERVICES_TERMS):
        return (
            "متجر Serva-S يقدم خدمات رقمية متنوعة حسب المتاح في الموقع، مثل خدمات السوشيال ميديا "
            "كالمتابعين واللايكات والمشاهدات، والاشتراكات الرقمية، وخدمات الذكاء الاصطناعي والدراسة، "
            "وشحن الألعاب والبطاقات. حدّد لي القسم أو المنصة التي تريدها حتى أعرض لك الخدمات المطابقة."
        )

    if has_any(text, ["رابط مباشر", "direct link", "url"]):
        if preferred_language(message) == "en":
            return (
                "I can't provide direct URLs in chat. Go to the home page, search for the service name, then choose the matching service. "
                "Tell me which service you need and I can guide you to the right category."
            )
        return (
            "لا أستطيع عرض رابط مباشر داخل المحادثة. من الصفحة الرئيسية ابحث عن اسم الخدمة، ثم اختر الخدمة المناسبة. "
            "اذكر لي اسم الخدمة التي تريدها لأوجهك إلى القسم الصحيح."
        )

    if has_any(text, ["كيف أشتري", "كيف اشتري", "طريقة الشراء", "اشتري خدمة"]):
        if has_any(text, ["chatgpt", "شات جي بي تي", "شات جيبيتي", "شات"]):
            return chatgpt_status_answer(message)
        if preferred_language(message) == "en":
            return order_instruction("en", "Review the service details, price, and guarantee before confirming.")
        return order_instruction("ar", "راجع تفاصيل الخدمة والسعر والضمان قبل التأكيد، وبعدها تابع الحالة من طلباتي.")

    if has_any(text, ["كلمة مرور", "password", "كود تحقق", "رمز تحقق"]):
        if preferred_language(message) == "en":
            return (
                "No, do not send your account password, verification code, card details, or any sensitive information. "
                "Services usually require only public details such as a link, username, or Player ID inside the site order form."
            )
        return (
            "لا، لا ترسل كلمة مرور حسابك أو كود التحقق أو أي بيانات حساسة. "
            "الخدمات عادة تطلب بيانات عامة فقط مثل الرابط أو اسم المستخدم أو Player ID حسب نوع الخدمة، "
            "وتعبئتها تكون داخل نموذج الطلب في الموقع."
        )

    if has_any(text, ["حقيقية", "حقيقي", "عضوية", "عضوي"]) and has_any(
        text,
        ["متابعين", "لايكات", "مشاهدات", "سوشيال", "smm", "followers", "likes", "views"],
    ):
        return (
            "خدمات السوشيال مثل المتابعين واللايكات والمشاهدات هي خدمات SMM لزيادة الأرقام أو التفاعل، "
            "وليست تفاعلًا عضويًا طبيعيًا. لذلك لا أصفها بأنها تفاعل حقيقي أو عضوي، "
            "والضمان إن وجد يعني التعويض أو المتابعة حسب بيانات الخدمة فقط."
        )

    if "ضمان" in text and has_any(text, ["سوشيال", "متابعين", "لايكات", "مشاهدات", "smm"]):
        return (
            "الضمان في خدمات السوشيال يعني التعويض أو المتابعة حسب بيانات الخدمة فقط، "
            "ولا يعني أن الخدمة تفاعل عضوي طبيعي أو جودة حقيقية. إذا كانت الخدمة بدون ضمان، فلا يوجد تعويض مؤكد."
        )

    if "ميزانيتي" in text or "budget" in text:
        clear_target = has_any(
            text,
            ["انستقرام", "instagram", "تيك", "tiktok", "يوتيوب", "youtube", "ببجي", "pubg", "فري فاير", "free fire"],
        )
        if not clear_target:
            return (
                "تمام، لكن أحتاج أعرف نوع الخدمة أو المنصة أولًا حتى لا أقترح شيئًا غير مناسب. "
                "هل تريد خدمة سوشيال ميديا، اشتراك رقمي، شحن لعبة، أو خدمة أخرى؟ بعد التحديد أبحث لك ضمن ميزانيتك."
            )

    if ("رابط" in text and ("غلط" in text or "خطأ" in text or "خاطئ" in text)) or "wrong link" in text:
        if preferred_language(message) == "en":
            return (
                "I can't edit the link directly from here. If the order has not started, support may be able to help; "
                "if it has already entered processing, it may not be possible to edit or stop it. "
                f"{support_instruction('en')} Send the correct link too."
            )
        return (
            "لا أقدر أعدّل الرابط مباشرة من هنا. إذا كان الطلب لم يبدأ فقد يستطيع الدعم مساعدتك، "
            "أما إذا دخل التنفيذ فقد لا يمكن تعديله أو إيقافه. "
            f"{support_instruction('ar')} واكتب الرابط الصحيح أيضًا."
        )

    if has_any(text, ["تأخر", "لم يصل", "ما وصل", "وين طلبي", "تأخر الطلب"]):
        if preferred_language(message) == "en":
            return (
                "If your order is late, send the order number here so support can check its status. "
                "Start and completion times vary by service, load, and order status. "
                f"{support_instruction('en', include_order_number=False)}"
            )
        return (
            "إذا تأخر الطلب، اكتب رقم الطلب هنا حتى يتم فحص حالته. وقت البدء والتنفيذ يختلف حسب الخدمة "
            "والضغط وحالة الطلب، لذلك لا أقدر أحدد السبب بدون رقم الطلب. "
            f"{support_instruction('ar', include_order_number=False)}"
        )

    if has_any(text, ["إلغاء", "الغاء", "استرجاع", "استرداد", "فلوسي", "refund", "cancel"]):
        if preferred_language(message) == "en":
            return (
                "Cancellation or refund depends on the order status and service policy. Some orders cannot be stopped after processing begins. "
                "Send your order number here so support can review it; I can't promise a confirmed refund or cancellation here. "
                f"{support_instruction('en', include_order_number=False)}"
            )
        return (
            "الإلغاء أو الاسترداد يعتمد على حالة الطلب وسياسة الخدمة. بعض الطلبات لا يمكن إيقافها بعد بدء التنفيذ. "
            "اكتب رقم الطلب هنا ليتم فحصه، ولا أستطيع أن أعدك باسترداد أو إلغاء مؤكد من هنا. "
            f"{support_instruction('ar', include_order_number=False)}"
        )

    if has_any(text, ["رصيدي", "أدفع", "ادفع", "الدفع", "محفظة", "اشحن رصيدي"]):
        if preferred_language(message) == "en":
            return (
                "To add balance, open My Wallet, choose the currency, transfer to the account shown on the deposit page, "
                "enter the exact transferred amount, add the transaction or transfer number, then submit the deposit request. "
                "Do not send passwords or card details in chat."
            )
        return (
            "لشحن الرصيد: ادخل إلى محفظتي، اختر العملة التي تريدها مثل الدولار أو الليرة السورية، ثم حوّل إلى الحساب الذي يظهر لك داخل صفحة الإيداع. "
            "بعد التحويل أدخل المبلغ نفسه بالضبط، ثم أدخل رقم العملية أو رقم الحوالة، وبعدها أرسل طلب الإيداع. "
            "لا ترسل كلمة مرور أو بيانات بطاقة داخل المحادثة، وإذا تأخر ظهور الرصيد اكتب تفاصيل العملية هنا وأرفق الإثبات."
        )

    if has_any(text, SOCIAL_PRIVATE_TERMS) and has_any(text, ["انستقرام", "instagram", "تيك", "tiktok", "حساب"]):
        return (
            "لا، خدمات السوشيال لا تصل أو لا تعمل بشكل صحيح على الحساب الخاص. "
            "اجعل الحساب عامًا قبل وضع الطلب، واتركه عامًا حتى يكتمل التنفيذ، ثم يمكنك إعادته خاصًا إذا أردت. "
            "إذا بقي الحساب خاصًا فقد يفشل الطلب أو لا تُحسب الخدمة بشكل صحيح."
        )

    return None


def check_rate_limit(session_id: str, limit: int = 15) -> tuple[bool, str | None]:
    """Check if the session has exceeded the rate limit (messages per hour)."""
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    try:
        response = supabase_get(
            "chat_sessions",
            {
                "select": "id",
                "session_id": f"eq.{session_id}",
                "role": "eq.user",
                "created_at": f"gte.{one_hour_ago}",
                "limit": str(limit + 1),
            }
        )
        if response.status_code == 200:
            count = len(response.json())
            
            if count >= limit:
                return True, "🚫 لقد تجاوزت الحد الأقصى من الرسائل المسموحة (15 رسالة في الساعة). تم إيقاف الخدمة مؤقتاً لتجنب إساءة الاستخدام. يرجى العودة بعد ساعة."
            
            if count == limit - 1:
                return False, "⚠️ تنبيه: لقد وصلت للحد الأقصى للرسائل في هذه الساعة (15 رسالة). رسالتك القادمة ستؤدي إلى حظر مؤقت لمدة ساعة."
                
            return False, None
    except Exception as exc:
        print(f"⚠️ تعذر التحقق من Rate Limit: {exc}")
    
    return False, None


def answer_question(
    message: str | dict,
    history: list | None = None,
    session_id: str | None = None,
    save: bool = True,
    use_helpers: bool = True,
) -> tuple[str, str]:
    """Answer one user message and optionally persist it."""
    if isinstance(message, dict):
        message = message.get("content", "")
    message = str(message or "").strip()
    session_id = session_id or str(uuid.uuid4())
    
    is_banned, rate_warning = check_rate_limit(session_id)
    if is_banned:
        return rate_warning, session_id

    effective_message = contextualize_followup(message, history)

    direct_answer = direct_catalog_answer(effective_message) or direct_policy_answer(effective_message)
    if direct_answer is not None:
        if save:
            save_message(session_id, "user", message)
            save_message(session_id, "assistant", direct_answer)
            
        if rate_warning:
            direct_answer = f"{direct_answer}\n\n{rate_warning}"
            
        return direct_answer, session_id

    chat_history = []
    if not history and save:
        chat_history.extend(load_history(session_id))
    chat_history.extend(gradio_history_to_messages(history or []))

    search_query = rewrite_query(effective_message) if use_helpers else effective_message
    raw_results = search_knowledge(search_query)
    best_results = rerank_results(effective_message, raw_results) if use_helpers else raw_results[:3]
    context = build_context(best_results)

    system_prompt = SYSTEM_PROMPT.format(context=context)
    dynamic_rules = load_answer_rules()
    if dynamic_rules:
        system_prompt += f"\n\n[قواعد أمان إضافية من قاعدة البيانات]:\n{dynamic_rules}"

    messages = [SystemMessage(content=system_prompt), *chat_history[-10:], HumanMessage(content=effective_message)]

    try:
        response = chat_text(messages)
        answer = apply_guardrails(parse_model_content(response), context, effective_message)
    except Exception as exc:
        print(f"❌ خطأ في توليد الإجابة: {exc}")
        if preferred_language(effective_message) == "en":
            answer = "Sorry, a temporary issue occurred while preparing the reply. Please try again, or write the issue here and support will follow up in this chat."
        else:
            answer = "عذرًا، حدثت مشكلة مؤقتة أثناء تجهيز الرد. جرّب مرة أخرى، أو اكتب المشكلة هنا وسيتم متابعتها ضمن هذه المحادثة."

    if save:
        save_message(session_id, "user", message)
        save_message(session_id, "assistant", answer)

    if rate_warning:
        answer = f"{answer}\n\n{rate_warning}"

    return answer, session_id
