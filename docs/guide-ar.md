# دليل التشغيل العربي

هذا الدليل يجمع نظرة المشروع العملية مع خطوات التشغيل اليومية في ملف واحد، حتى يبقى المستودع مرتبًا وواضحًا.

## فكرة المشروع

المشروع عبارة عن مساعد RAG لمتجر Serva-S. عند وصول سؤال من العميل، يبحث في خدمات المتجر وسياساته وسيناريوهات الدعم المخزنة في Supabase، ثم يرسل السياق المناسب إلى النموذج المختار ويعيد ردًا مضبوطًا بقواعد أمان واضحة.

## مكونات المستودع

| المسار | الوظيفة |
|---|---|
| `scripts/app_config.py` | تحميل `.env` وتجهيز الإعدادات المشتركة |
| `scripts/rag_core.py` | منطق البحث وبناء السياق والحماية والرد |
| `scripts/llm_client.py` | الربط مع Groq وOpenRouter وNeokens وOllama |
| `scripts/fill_*.py` | تعبئة الخدمات والسياسات والمعرفة وقواعد الأمان |
| `scripts/chat_ai.py` | تجربة سريعة من الطرفية |
| `scripts/gradio_chat.py` | واجهة محلية عبر Gradio |
| `scripts/eval_test.py` | اختبار سريع قبل أي تعديل مهم |
| `scripts/eval_test_extended.py` | اختبار موسع قبل الإطلاق أو بعد تغييرات كبيرة |

## الإعداد السريع

1. أنشئ البيئة الافتراضية وثبت المكتبات:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. انسخ ملف البيئة:

   ```powershell
   copy .env.example .env
   ```

3. عبئ القيم الأساسية في `.env`:

   ```env
   SUPABASE_URL=...
   SUPABASE_KEY=...
   GOOGLE_API_KEY=...
   LLM_PROVIDER=neokens
   NEOKENS_API_KEY=...
   ```

## تجهيز قاعدة البيانات

نفذ الملف التالي في Supabase SQL Editor:

```text
supabase_final_setup.sql
```

هذا الملف ينشئ الجداول والدوال اللازمة للمحادثات والبحث المتجهي وقواعد الأمان.

إذا أردت فقط حذف الـ embeddings وإعادة بنائها دون حذف الجداول نفسها، استخدم:

```text
supabase_reset_embeddings.sql
```

## تعبئة المعرفة

نفذ هذه الخطوات بالترتيب:

```powershell
python scripts\fill_safety_rules.py

$env:RESET_SERVICE_DOCUMENTS='true'; python scripts\fill_ai_pro.py; Remove-Item Env:RESET_SERVICE_DOCUMENTS
$env:RESET_POLICY_DOCUMENTS='true'; python scripts\fill_policies_ai.py; Remove-Item Env:RESET_POLICY_DOCUMENTS
$env:RESET_SCENARIO_DOCUMENTS='true'; python scripts\fill_scenarios_ai.py; Remove-Item Env:RESET_SCENARIO_DOCUMENTS

python scripts\fill_risk_scenarios.py
python scripts\fill_public_knowledge.py
```

## التشغيل المحلي

للتجربة من الطرفية:

```powershell
python scripts\chat_ai.py
```

لتشغيل واجهة محلية:

```powershell
python scripts\gradio_chat.py
```

## التقييم

اختبار سريع:

```powershell
python scripts\eval_test.py
```

اختبار موسع:

```powershell
python scripts\eval_test_extended.py
```

جميع التقارير الناتجة تحفظ داخل `reports/` ولا ترفع إلى GitHub.

## ملاحظات تشغيل مهمة

- لا ترفع `.env` إلى GitHub.
- استخدم `SUPABASE_KEY` على الخادم فقط، وليس في الواجهة الأمامية.
- إذا عدلت الخدمات أو السياسات أو السيناريوهات، أعد تشغيل سكربتات التعبئة المناسبة.
- إذا أجريت تعديلًا كبيرًا في المنطق أو قواعد الأمان، شغّل الاختبارين السريع والموسع قبل النشر.
