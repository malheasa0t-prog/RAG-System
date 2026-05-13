# Serva-S RAG Assistant

مشروع مساعد عربي لمتجر Serva-S يعتمد على RAG:

1. يستقبل سؤال العميل.
2. يبحث في خدمات المتجر والمعرفة المخزنة في Supabase.
3. يرسل السياق للنموذج المختار.
4. ينظف الرد من الروابط أو الادعاءات غير الآمنة.
5. يعيد إجابة عربية مناسبة للعميل.

## أهم الملفات

| الملف | الوظيفة |
|---|---|
| `scripts/rag_core.py` | قلب المشروع: البحث، بناء السياق، الردود المباشرة، وحماية المخرجات |
| `scripts/llm_client.py` | تشغيل مزود النموذج: Groq أو OpenRouter أو Neokens أو Ollama |
| `scripts/app_config.py` | قراءة `.env` وتجميع الإعدادات |
| `scripts/embedding_utils.py` | أدوات مشتركة لإنشاء embeddings والحفظ في Supabase |
| `scripts/fill_ai_pro.py` | تحويل جدول الخدمات إلى embeddings |
| `scripts/fill_policies_ai.py` | تحويل السياسات والأسئلة الشائعة إلى embeddings |
| `scripts/fill_scenarios_ai.py` | تحويل سيناريوهات العملاء إلى embeddings |
| `scripts/fill_risk_scenarios.py` | تحويل سيناريوهات تصحيح الأخطاء إلى embeddings |
| `scripts/fill_public_knowledge.py` | تحويل التصنيفات، المجموعات، العروض، التحديثات، والصفحات العامة إلى embeddings |
| `scripts/fill_safety_rules.py` | تعبئة قواعد الأمان في جدول منفصل |
| `scripts/eval_test.py` | اختبار المساعد على مجموعة أسئلة |
| `scripts/chat_ai.py` | اختبار سريع من الطرفية |
| `scripts/gradio_chat.py` | واجهة محلية بسيطة للتجربة |
| `supabase_final_setup.sql` | كود إنشاء جداول ودوال Supabase |
| `supabase_reset_embeddings.sql` | كود اختياري لحذف embeddings فقط وإعادة بنائها |
| `RUN_MANUAL_AR.md` | تسلسل التشغيل اليدوي خطوة بخطوة |

## التشغيل السريع

اتبع الملف:

```text
RUN_MANUAL_AR.md
```

أهم الأوامر بعد تجهيز `.env` وقاعدة البيانات:

```powershell
python scripts\fill_safety_rules.py

$env:RESET_SERVICE_DOCUMENTS='true'; python scripts\fill_ai_pro.py; Remove-Item Env:RESET_SERVICE_DOCUMENTS
$env:RESET_POLICY_DOCUMENTS='true'; python scripts\fill_policies_ai.py; Remove-Item Env:RESET_POLICY_DOCUMENTS
$env:RESET_SCENARIO_DOCUMENTS='true'; python scripts\fill_scenarios_ai.py; Remove-Item Env:RESET_SCENARIO_DOCUMENTS

python scripts\fill_risk_scenarios.py
python scripts\fill_public_knowledge.py
python scripts\eval_test.py
python scripts\chat_ai.py
```

## ملاحظات مهمة

- لا ترفع ملف `.env` ولا تضع المفاتيح داخل الكود.
- `SUPABASE_KEY` يجب أن يكون في السيرفر فقط، وليس في المتصفح.
- لا تشغّل `supabase_reset_embeddings.sql` إلا إذا أردت حذف معرفة الذكاء القديمة وإعادة بنائها.
- إذا عدّلت الخدمات أو السياسات أو السيناريوهات، أعد تشغيل سكربت التعبئة المناسب ثم شغّل الاختبار.
- المشروع جاهز للتعلم والتجربة، أما الإطلاق على موقع حقيقي فيحتاج API backend وحماية rate limit ومراقبة تكاليف.
