-- ============================================================
-- Serva-S RAG Assistant - Reset Embeddings Only
-- ============================================================
-- شغّل هذا الملف فقط عندما تريد حذف معرفة الذكاء القديمة
-- ثم إعادة بنائها من السكربتات.
--
-- هذا الملف لا يحذف:
-- - services
-- - categories / offers / site pages
-- - chat_sessions
-- - ai_safety_rules
--
-- يحذف فقط:
-- - ai_documents: خدمات + سياسات + سيناريوهات قديمة
-- - ai_knowledge_documents: معرفة عامة آمنة من الجداول العامة
-- - ai_knowledge_sources: مصادر المعرفة العامة المرتبطة بها

BEGIN;

TRUNCATE TABLE public.ai_documents RESTART IDENTITY;

TRUNCATE TABLE
  public.ai_knowledge_documents,
  public.ai_knowledge_sources
RESTART IDENTITY CASCADE;

COMMIT;

-- بعد نجاح الحذف، أعد تشغيل سكربتات التعبئة بالترتيب الموجود في RUN_MANUAL_AR.md.
