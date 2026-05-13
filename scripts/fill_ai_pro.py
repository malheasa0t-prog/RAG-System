import requests

try:
    from .app_config import (
        HEADERS,
        REQUEST_TIMEOUT,
        RESET_SERVICE_DOCUMENTS,
        SUPABASE_URL,
        require_runtime_secrets,
    )
    from .embedding_utils import delete_legacy_documents, embed_with_retry, insert_legacy_document
except ImportError:
    from app_config import (
        HEADERS,
        REQUEST_TIMEOUT,
        RESET_SERVICE_DOCUMENTS,
        SUPABASE_URL,
        require_runtime_secrets,
    )
    from embedding_utils import delete_legacy_documents, embed_with_retry, insert_legacy_document

require_runtime_secrets()

def process_and_save_services():
    print("🚀 جاري الاتصال بقاعدة البيانات لجلب الخدمات...")
    
    if RESET_SERVICE_DOCUMENTS:
        print("🧹 جاري مسح وثائق الخدمات القديمة فقط...")
        delete_legacy_documents("الخدمة:", "وثائق الخدمات القديمة")
    else:
        print("ℹ️ لن يتم حذف أي وثائق قديمة. فعّل RESET_SERVICE_DOCUMENTS=true عند الحاجة.")
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/services"
        "?select=id,smm_service_id,name_ar,name_en,description,description_en,"
        "category,platform,price,min_qty,max_qty,active,has_guarantee,"
        "guarantee_days,start_time_text,service_disclaimer,requires_support_chat",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    
    if response.status_code != 200:
        print("❌ خطأ في جلب البيانات:", response.text)
        return
        
    services = response.json()
    print(
        f"✅ تم إيجاد {len(services)} خدمة. سيتم تضمين الخدمات الفعالة والمعطلة، "
        "مع وضع حالة واضحة لكل خدمة."
    )
    print("جاري معالجتها بالذكاء الاصطناعي الخاص بجوجل...")

    texts_to_embed = []
    services_info = []
    
    for service in services:
        service_id = service.get('smm_service_id') or service.get('id', '')
        title = service.get('name_ar') or service.get('name_en') or ''
        desc = service.get('description') or service.get('description_en') or 'لا يوجد وصف'
        price = service.get('price', 0)
        is_active = service.get('active') is True
        is_smm = bool(service.get('smm_service_id'))
        status_text = "متاحة حاليًا" if is_active else "غير متوفرة حاليًا / معطلة"
        platform = service.get('platform') or 'غير محدد'
        category = service.get('category') or 'غير محدد'
        min_qty = service.get('min_qty') or 'غير محدد'
        max_qty = service.get('max_qty') or 'غير محدد'
        guarantee = "نعم" if service.get('has_guarantee') else "لا"
        guarantee_days = service.get('guarantee_days') or 0
        start_time = service.get('start_time_text') or 'غير محدد'
        disclaimer = service.get('service_disclaimer') or ''
        support_required = "نعم" if service.get('requires_support_chat') else "لا"
        
        text_to_learn = (
            f"الخدمة: {title}\n"
            f"الحالة: {status_text}\n"
            f"نوع الخدمة: {'SMM - زيادة أرقام أو تفاعل، وليست تفاعلًا عضويًا طبيعيًا' if is_smm else 'خدمة رقمية'}\n"
            f"المنصة: {platform}\n"
            f"القسم: {category}\n"
            f"الوصف: {desc}\n"
            f"السعر: {price}$\n"
            f"الحد الأدنى للكمية: {min_qty}\n"
            f"الحد الأقصى للكمية: {max_qty}\n"
            f"يوجد ضمان: {guarantee}\n"
            f"مدة الضمان بالأيام: {guarantee_days}\n"
            f"وقت البدء المتوقع: {start_time}\n"
            f"تحتاج تواصل دعم قبل التنفيذ: {support_required}\n"
        )
        if disclaimer:
            text_to_learn += f"تنبيه الخدمة: {disclaimer}\n"
        if is_smm:
            text_to_learn += (
                "ملاحظة SMM: هذه الخدمة ليست تفاعلًا عضويًا طبيعيًا. "
                "لا تصفها بأنها حقيقية أو عضوية أو آمنة 100%. "
                "الضمان، إن وجد، يعني التعويض أو المتابعة حسب بيانات الخدمة فقط.\n"
            )
        if is_active:
            text_to_learn += (
                "طريقة الطلب: من الصفحة الرئيسية ابحث عن اسم الخدمة، افتح الخدمة المناسبة، "
                "املأ المعلومات المطلوبة داخل نموذج الطلب، ثم أكّد الطلب."
            )
        else:
            text_to_learn += (
                "تنبيه مهم: هذه الخدمة معطلة وغير متوفرة للطلب حاليًا. "
                "لا تشجع العميل على شرائها. "
                "اذكر أنها غير متوفرة حاليًا واقترح عليه اختيار خدمة بديلة متاحة. إذا كان لديه طلب سابق فليكتب رقم الطلب هنا."
            )
        texts_to_embed.append(text_to_learn)
        services_info.append({"service_id": service_id, "content": text_to_learn})
        
    print(f"🧠 جاري تحويل {len(texts_to_embed)} خدمة إلى متجهات...")
    
    success_count = 0
    
    for i, text in enumerate(texts_to_embed):
        info = services_info[i]
        progress = f"[{i+1}/{len(texts_to_embed)}]"
        
        try:
            vector = embed_with_retry(text, label=progress, max_attempts=5)
            post_res = insert_legacy_document(info["content"], vector)

            if post_res.status_code in [201, 200]:
                success_count += 1
                if (i + 1) % 50 == 0 or (i + 1) == len(texts_to_embed):
                    print(f"  ✅ {progress} تم حفظ {success_count} خدمة...")
            else:
                print(f"  ⚠️ {progress} خطأ حفظ:", post_res.text[:100])
        except Exception as exc:
            print(f"  ❌ {progress} خطأ: {exc}")
            
    print(f"\n🎉 تم الانتهاء! تم حفظ {success_count}/{len(texts_to_embed)} خدمة بنجاح.")

if __name__ == "__main__":
    process_and_save_services()
