# تسلسل تشغيل مشروع Serva-S RAG يدويًا

هذا الملف هو الدليل العملي الذي تشغله بيدك خطوة بخطوة. الفكرة أن تفهم ماذا يحدث، لا أن تضغط زرًا واحدًا لا تعرف ما وراءه.

## 1. تثبيت المكتبات

نفّذ مرة واحدة داخل مجلد المشروع:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

إذا كنت فتحت طرفية جديدة لاحقًا، فعّل البيئة فقط:

```powershell
.\.venv\Scripts\activate
```

## 2. تجهيز ملف المفاتيح

انسخ `.env.example` إلى `.env` وضع مفاتيحك الخاصة:

```powershell
copy .env.example .env
```

أهم القيم:

```env
SUPABASE_URL=...
SUPABASE_KEY=...
GOOGLE_API_KEY=...
LLM_PROVIDER=neokens
NEOKENS_API_KEY=...
NEOKENS_MODEL=gemini-3.1-pro-low
```

لا تشارك ملف `.env` ولا ترفعه إلى GitHub.

## 3. تجهيز قاعدة البيانات

افتح Supabase SQL Editor وانسخ محتوى هذا الملف ونفّذه:

```text
supabase_final_setup.sql
```

ماذا يفعل؟

- ينشئ جدول `chat_sessions` لحفظ المحادثات.
- ينشئ جدول `ai_documents` لمعرفة الخدمات والسياسات والسيناريوهات القديمة.
- ينشئ جداول `ai_knowledge_sources` و `ai_knowledge_documents` للمعرفة العامة المنظمة.
- ينشئ جدول `ai_safety_rules` لقواعد الأمان.
- ينشئ دوال البحث المتجهي `match_services` و `match_knowledge_documents`.
- يمنع وصول `anon` و `authenticated` لهذه الجداول حتى لا يقرأها العميل من المتصفح.

## 4. حذف embeddings القديمة عند الحاجة

هذه خطوة اختيارية. استخدمها إذا أردت تنظيف معرفة الذكاء بالكامل وإعادة بنائها من الصفر.

افتح Supabase SQL Editor ونفّذ:

```text
supabase_reset_embeddings.sql
```

هذا يحذف فقط embeddings من:

- `ai_documents`
- `ai_knowledge_documents`
- `ai_knowledge_sources`

ولا يحذف الخدمات الأصلية أو المحادثات أو قواعد الأمان.

## 5. تعبئة قواعد الأمان

نفّذ:

```powershell
python scripts\fill_safety_rules.py
```

ماذا يفعل؟

- يضيف قواعد مثل: لا تخترع الأسعار، لا تطلب كلمة مرور، لا تعرض روابط، لا تشجع على خدمة معطلة.
- هذه ليست embeddings، بل قواعد مباشرة يقرأها المساعد أثناء الرد.

## 6. تعبئة الخدمات

نفّذ:

```powershell
$env:RESET_SERVICE_DOCUMENTS='true'
python scripts\fill_ai_pro.py
Remove-Item Env:RESET_SERVICE_DOCUMENTS
```

ماذا يفعل؟

- يقرأ جدول `services` من Supabase.
- يحول كل خدمة إلى نص واضح يحتوي الاسم، السعر، الحالة، الضمان، والحدود.
- يحفظ النص مع embedding داخل `ai_documents`.
- يضيف الخدمات المعطلة أيضًا، لكن يكتب أنها `غير متوفرة حاليًا / معطلة`.

## 7. تعبئة السياسات

نفّذ:

```powershell
$env:RESET_POLICY_DOCUMENTS='true'
python scripts\fill_policies_ai.py
Remove-Item Env:RESET_POLICY_DOCUMENTS
```

ماذا يفعل؟

- يضيف سياسة الاسترداد، الشروط، الخصوصية، طريقة الطلب، والدعم.
- يحفظها داخل `ai_documents`.

## 8. تعبئة سيناريوهات العملاء

نفّذ:

```powershell
$env:RESET_SCENARIO_DOCUMENTS='true'
python scripts\fill_scenarios_ai.py
Remove-Item Env:RESET_SCENARIO_DOCUMENTS
```

ماذا يفعل؟

- يضيف أمثلة محادثات متوقعة.
- مثال: كيف يرد على طلب شحن ببجي، فري فاير، أو سؤال عن Netflix غير المتوفر.

## 9. تعبئة سيناريوهات تصحيح الأخطاء

نفّذ:

```powershell
python scripts\fill_risk_scenarios.py
```

ماذا يفعل؟

- يضيف قواعد تعليمية للنموذج عن الأخطاء الشائعة.
- مثال: لا تخلط Netflix مع YouTube Premium، لا تقل إن الحساب الخاص تصله الخدمة، لا تعرض رابطًا.
- السكربت يحذف نسخته القديمة تلقائيًا ثم يرفع النسخة الجديدة.

## 10. تعبئة المعرفة العامة من جداول الموقع

نفّذ:

```powershell
python scripts\fill_public_knowledge.py
```

ماذا يفعل؟

- يقرأ الجداول العامة الآمنة مثل:
  `categories`, `main_groups`, `offers`, `offer_items`, `site_updates`, `public_settings`, `site_pages`.
- يحفظها في `ai_knowledge_documents`.
- يحذف الوثائق القديمة لكل مصدر قبل إعادة بنائه.

## 11. اختبار المساعد

نفّذ:

```powershell
python scripts\eval_test.py
```

ماذا يفعل؟

- يسأل المساعد مجموعة أسئلة.
- يحفظ تقريرًا جديدًا في `eval_results_full.md`.
- يفحص الروابط والكلمات الممنوعة وبعض الكلمات المطلوبة.

## 12. تجربة محادثة من الطرفية

نفّذ:

```powershell
python scripts\chat_ai.py
```

اكتب أسئلة مثل:

```text
هل عندكم Netflix؟
أريد اشتراك يوتيوب بريميوم
حسابي انستقرام خاص هل تصل الخدمة؟
كيف أشحن رصيدي؟
```

للخروج اكتب:

```text
exit
```

## 13. تشغيل واجهة محلية

نفّذ:

```powershell
python scripts\gradio_chat.py
```

ثم افتح:

```text
http://127.0.0.1:7860
```

## متى أعيد تشغيل سكربتات التعبئة؟

إذا عدّلت الخدمات في لوحة Supabase:

```powershell
$env:RESET_SERVICE_DOCUMENTS='true'
python scripts\fill_ai_pro.py
Remove-Item Env:RESET_SERVICE_DOCUMENTS
```

إذا عدّلت السياسات:

```powershell
$env:RESET_POLICY_DOCUMENTS='true'
python scripts\fill_policies_ai.py
Remove-Item Env:RESET_POLICY_DOCUMENTS
```

إذا عدّلت السيناريوهات:

```powershell
$env:RESET_SCENARIO_DOCUMENTS='true'
python scripts\fill_scenarios_ai.py
Remove-Item Env:RESET_SCENARIO_DOCUMENTS
python scripts\fill_risk_scenarios.py
```

إذا عدّلت التصنيفات أو العروض أو صفحات الموقع:

```powershell
python scripts\fill_public_knowledge.py
```

بعد أي تحديث مهم:

```powershell
python scripts\eval_test.py
```
