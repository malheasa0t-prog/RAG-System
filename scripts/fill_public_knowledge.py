"""Embed safe public store knowledge into ai_knowledge_documents.

Sources:
- categories
- main_groups
- offers + offer_items
- site_updates
- public_settings
- site_pages

The script intentionally excludes private, financial, operational, and secret
fields. It writes to the newer safe knowledge tables, not raw chat/customer
tables.
"""

from __future__ import annotations

import hashlib
import html
import re
from typing import Any

import requests

try:
    from .app_config import HEADERS, REQUEST_TIMEOUT, SUPABASE_URL, require_runtime_secrets
    from .embedding_utils import embed_with_retry
except ImportError:
    from app_config import HEADERS, REQUEST_TIMEOUT, SUPABASE_URL, require_runtime_secrets
    from embedding_utils import embed_with_retry


require_runtime_secrets()


SOURCES = {
    "categories": {
        "source_key": "table_categories",
        "source_type": "glossary",
        "title": "تصنيفات الخدمات",
    },
    "main_groups": {
        "source_key": "table_main_groups",
        "source_type": "glossary",
        "title": "المجموعات الرئيسية",
    },
    "offers": {
        "source_key": "table_offers",
        "source_type": "service",
        "title": "العروض والباقات",
    },
    "site_updates": {
        "source_key": "table_site_updates",
        "source_type": "manual",
        "title": "تحديثات وإعلانات الموقع",
    },
    "public_settings": {
        "source_key": "table_public_settings",
        "source_type": "faq",
        "title": "إعدادات ومعلومات الموقع العامة",
    },
    "site_pages": {
        "source_key": "table_site_pages",
        "source_type": "manual",
        "title": "صفحات الموقع العامة",
    },
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def api_get(table: str, select: str, **filters: str) -> list[dict[str, Any]]:
    params = {"select": select, **filters}
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch {table}: {response.status_code} {response.text[:500]}")
    return response.json()


def ensure_source(source_name: str) -> int:
    source = SOURCES[source_name]
    headers = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/ai_knowledge_sources",
        headers=headers,
        params={"on_conflict": "source_key"},
        json={
            "source_key": source["source_key"],
            "source_type": source["source_type"],
            "title": source["title"],
            "status": "active",
        },
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"Failed to upsert source {source_name}: {response.text[:500]}")
    rows = response.json()
    if not rows:
        raise RuntimeError(f"Source {source_name} was upserted without returning an id.")
    return rows[0]["id"]


def delete_source_documents(source_id: int) -> None:
    """Remove generated docs for one source before rebuilding it.

    This avoids relying on ON CONFLICT for content_hash, which may fail when
    the database has a partial unique index.
    """
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/ai_knowledge_documents",
        headers=HEADERS,
        params={"source_id": f"eq.{source_id}"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code not in {200, 204}:
        raise RuntimeError(f"Failed to delete old documents: {response.text[:500]}")


def content_hash(source_key: str, record_key: str, content: str) -> str:
    raw = f"{source_key}:{record_key}:{content}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def save_documents(source_name: str, documents: list[dict[str, Any]]) -> int:
    if not documents:
        return 0

    source_id = ensure_source(source_name)
    delete_source_documents(source_id)
    source_key = SOURCES[source_name]["source_key"]

    success = 0
    headers = HEADERS

    for index, doc in enumerate(documents, start=1):
        content = clean_text(doc["content"])
        if len(content) < 20:
            continue

        vector = embed_with_retry(content)
        record_key = str(doc.get("record_key") or doc["title"])
        payload = {
            "source_id": source_id,
            "document_type": doc["document_type"],
            "title": clean_text(doc["title"])[:300],
            "content": content[:8000],
            "metadata": doc.get("metadata", {}),
            "embedding": vector,
            "content_hash": content_hash(source_key, record_key, content),
            "priority": doc.get("priority", 0),
            "is_active": True,
            "expires_at": doc.get("expires_at"),
        }
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/ai_knowledge_documents",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code in {200, 201, 204}:
            success += 1
        else:
            print(f"⚠️ فشل حفظ وثيقة {source_name} #{index}: {response.text[:300]}")

    return success


def build_category_documents() -> list[dict[str, Any]]:
    rows = api_get(
        "categories",
        "id,name_ar,name_en,description,main_group,show_in_nav,price_display_decimals,active,sort_order",
        active="eq.true",
        order="sort_order.asc",
    )
    documents = []
    for row in rows:
        name = row.get("name_ar") or row.get("name_en") or f"Category {row.get('id')}"
        content = (
            f"تصنيف خدمات: {name}\n"
            f"الاسم الإنجليزي: {row.get('name_en') or 'غير محدد'}\n"
            f"الوصف: {row.get('description') or 'لا يوجد وصف'}\n"
            f"المجموعة الرئيسية: {row.get('main_group') or 'غير محدد'}\n"
            f"ظاهر في التصفح: {'نعم' if row.get('show_in_nav') else 'لا'}"
        )
        documents.append({
            "record_key": row.get("id"),
            "document_type": "glossary",
            "title": f"تصنيف: {name}",
            "content": content,
            "metadata": {"table": "categories", "id": row.get("id")},
            "priority": 20,
        })
    return documents


def build_main_group_documents() -> list[dict[str, Any]]:
    rows = api_get(
        "main_groups",
        "key,name_ar,name_en,description,redirect_url,show_in_nav,price_display_decimals,is_active,active,sort_order",
        order="sort_order.asc",
    )
    documents = []
    for row in rows:
        if row.get("is_active") is False or row.get("active") is False:
            continue
        name = row.get("name_ar") or row.get("name_en") or row.get("key")
        content = (
            f"مجموعة رئيسية في المتجر: {name}\n"
            f"الاسم الإنجليزي: {row.get('name_en') or 'غير محدد'}\n"
            f"الوصف: {row.get('description') or 'لا يوجد وصف'}\n"
            f"الرابط/التحويل: {row.get('redirect_url') or 'غير محدد'}\n"
            f"ظاهرة في التصفح: {'نعم' if row.get('show_in_nav') else 'لا'}"
        )
        documents.append({
            "record_key": row.get("key"),
            "document_type": "glossary",
            "title": f"مجموعة: {name}",
            "content": content,
            "metadata": {"table": "main_groups", "key": row.get("key")},
            "priority": 20,
        })
    return documents


def build_offer_documents() -> list[dict[str, Any]]:
    offers = api_get(
        "offers",
        "id,slug,title_ar,title_en,subtitle_ar,subtitle_en,description_ar,description_en,badge_text,original_price,offer_price,currency,is_active,is_featured,starts_at,ends_at,cta_label",
        is_active="eq.true",
        order="sort_order.asc",
    )
    items = api_get(
        "offer_items",
        "id,offer_id,service_id,quantity,item_label,item_description,is_required,sort_order",
        order="sort_order.asc",
    )
    items_by_offer: dict[Any, list[dict[str, Any]]] = {}
    for item in items:
        items_by_offer.setdefault(item.get("offer_id"), []).append(item)

    documents = []
    for offer in offers:
        title = offer.get("title_ar") or offer.get("title_en") or offer.get("slug")
        offer_items = items_by_offer.get(offer.get("id"), [])
        item_lines = []
        for item in offer_items:
            item_lines.append(
                "- "
                f"{item.get('item_label') or 'عنصر عرض'}"
                f" | الكمية: {item.get('quantity') or 'غير محدد'}"
                f" | الوصف: {item.get('item_description') or 'لا يوجد'}"
                f" | مطلوب: {'نعم' if item.get('is_required') else 'لا'}"
            )
        content = (
            f"عرض فعال في المتجر: {title}\n"
            f"العنوان الإنجليزي: {offer.get('title_en') or 'غير محدد'}\n"
            f"الوصف: {offer.get('description_ar') or offer.get('description_en') or 'لا يوجد وصف'}\n"
            f"النص الفرعي: {offer.get('subtitle_ar') or offer.get('subtitle_en') or 'غير محدد'}\n"
            f"شارة العرض: {offer.get('badge_text') or 'غير محدد'}\n"
            f"السعر قبل العرض: {offer.get('original_price')} {offer.get('currency') or 'USD'}\n"
            f"سعر العرض: {offer.get('offer_price')} {offer.get('currency') or 'USD'}\n"
            f"عرض مميز: {'نعم' if offer.get('is_featured') else 'لا'}\n"
            f"يبدأ في: {offer.get('starts_at') or 'غير محدد'}\n"
            f"ينتهي في: {offer.get('ends_at') or 'غير محدد'}\n"
            f"رابط العرض: https://serva-s.com/offers/{offer.get('slug')}\n"
            "عناصر العرض:\n"
            + ("\n".join(item_lines) if item_lines else "لا توجد عناصر مفصلة.")
        )
        documents.append({
            "record_key": offer.get("id"),
            "document_type": "service",
            "title": f"عرض: {title}",
            "content": content,
            "metadata": {"table": "offers", "id": offer.get("id"), "slug": offer.get("slug")},
            "priority": 45 if offer.get("is_featured") else 35,
            "expires_at": offer.get("ends_at"),
        })
    return documents


def build_site_update_documents() -> list[dict[str, Any]]:
    rows = api_get(
        "site_updates",
        "id,title,summary,body_html,badge,cta_label,cta_url,is_published,is_pinned,published_at",
        is_published="eq.true",
        order="published_at.desc",
    )
    documents = []
    for row in rows:
        title = row.get("title") or f"تحديث {row.get('id')}"
        content = (
            f"تحديث منشور في الموقع: {title}\n"
            f"الملخص: {row.get('summary') or 'لا يوجد ملخص'}\n"
            f"التفاصيل: {clean_text(row.get('body_html')) or 'لا توجد تفاصيل'}\n"
            f"شارة: {row.get('badge') or 'غير محدد'}\n"
            f"رابط الإجراء: {row.get('cta_url') or 'غير محدد'}\n"
            f"منشور بتاريخ: {row.get('published_at') or 'غير محدد'}\n"
            f"مثبت: {'نعم' if row.get('is_pinned') else 'لا'}"
        )
        documents.append({
            "record_key": row.get("id"),
            "document_type": "manual",
            "title": f"تحديث: {title}",
            "content": content,
            "metadata": {"table": "site_updates", "id": row.get("id")},
            "priority": 55 if row.get("is_pinned") else 30,
        })
    return documents


def build_public_settings_documents() -> list[dict[str, Any]]:
    rows = api_get(
        "public_settings",
        "id,site_name,site_description,footer_description,how_to_order,faq_content,refund_policy,contact_page,whatsapp_number,telegram_username,support_email",
    )
    documents = []
    for row in rows:
        field_map = {
            "how_to_order": ("faq", "طريقة الطلب", 50),
            "faq_content": ("faq", "الأسئلة الشائعة", 50),
            "refund_policy": ("policy", "سياسة الاسترداد", 60),
            "contact_page": ("manual", "الدعم داخل المحادثة", 45),
            "footer_description": ("manual", "وصف المتجر", 25),
            "site_description": ("manual", "وصف الموقع", 25),
        }
        for field, (document_type, title, priority) in field_map.items():
            value = clean_text(row.get(field))
            if field == "contact_page":
                value = (
                    "هذه المحادثة هي تذكرة الدعم الخاصة بك. اكتب رقم الطلب إن وجد، "
                    "واشرح المشكلة باختصار، وأرفق أي إثبات أو صورة عند الحاجة.\n"
                    + value.replace("صفحة التواصل", "هذه المحادثة")
                )
            if len(value) < 20:
                continue
            documents.append({
                "record_key": f"{row.get('id')}:{field}",
                "document_type": document_type,
                "title": title,
                "content": value,
                "metadata": {"table": "public_settings", "id": row.get("id"), "field": field},
                "priority": priority,
            })
        support = (
            f"معلومات التواصل الرسمية:\n"
            f"واتساب: {row.get('whatsapp_number') or 'غير محدد'}\n"
            f"تيليجرام: {row.get('telegram_username') or 'غير محدد'}\n"
            f"البريد الإلكتروني: {row.get('support_email') or 'غير محدد'}"
        )
        documents.append({
            "record_key": f"{row.get('id')}:support_contacts",
            "document_type": "manual",
            "title": "معلومات التواصل الرسمية",
            "content": support,
            "metadata": {"table": "public_settings", "id": row.get("id"), "field": "support_contacts"},
            "priority": 55,
        })
    return documents


def build_site_page_documents() -> list[dict[str, Any]]:
    rows = api_get("site_pages", "slug,title,content,updated_at", order="slug.asc")
    documents = []
    for row in rows:
        slug = row.get("slug")
        title = row.get("title") or slug
        content = clean_text(row.get("content"))
        if len(content) < 20:
            continue
        page_type = "policy" if any(word in str(slug).lower() for word in ["privacy", "refund", "terms"]) else "manual"
        documents.append({
            "record_key": slug,
            "document_type": page_type,
            "title": f"صفحة: {title}",
            "content": f"صفحة عامة من الموقع: {title}\nالمحتوى: {content}\nآخر تحديث: {row.get('updated_at') or 'غير محدد'}",
            "metadata": {"table": "site_pages", "slug": slug},
            "priority": 50 if page_type == "policy" else 30,
        })
    return documents


def main() -> None:
    builders = [
        ("categories", build_category_documents),
        ("main_groups", build_main_group_documents),
        ("offers", build_offer_documents),
        ("site_updates", build_site_update_documents),
        ("public_settings", build_public_settings_documents),
        ("site_pages", build_site_page_documents),
    ]

    total = 0
    for source_name, builder in builders:
        print(f"🚀 تجهيز {source_name}...")
        documents = builder()
        saved = save_documents(source_name, documents)
        total += saved
        print(f"✅ {source_name}: تم حفظ/تحديث {saved}/{len(documents)} وثيقة.")

    print(f"\n🎉 انتهى بناء المعرفة العامة. الإجمالي: {total} وثيقة نشطة.")


if __name__ == "__main__":
    main()
