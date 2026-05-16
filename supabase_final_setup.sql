-- ============================================================
-- Serva-S RAG Assistant - Final Supabase Setup
-- ============================================================
-- Execute this file in Supabase SQL Editor.
--
-- Safe content only:
-- - public service descriptions and prices
-- - approved policies and FAQs
-- - generic support/sales scenarios
-- - answer safety rules
-- - synthetic evaluation cases
--
-- Do NOT store secrets, passwords, payment details, private customer data,
-- or raw chat logs in the knowledge tables.

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Persistent chat sessions
-- ============================================================

CREATE TABLE IF NOT EXISTS public.chat_sessions (
  id SERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  rate_limit_key TEXT,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.chat_sessions
ADD COLUMN IF NOT EXISTS rate_limit_key TEXT;

CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id
ON public.chat_sessions(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_rate_limit_key_created_at
ON public.chat_sessions(rate_limit_key, created_at DESC)
WHERE rate_limit_key IS NOT NULL;

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_full_access" ON public.chat_sessions;
DROP POLICY IF EXISTS "deny_client_access" ON public.chat_sessions;

CREATE POLICY "deny_client_access" ON public.chat_sessions
  FOR ALL TO anon, authenticated
  USING (false)
  WITH CHECK (false);

REVOKE ALL ON public.chat_sessions FROM anon, authenticated;

-- ============================================================
-- Legacy RAG documents
-- ============================================================
-- سكربتات fill_ai_pro.py و fill_policies_ai.py و fill_scenarios_ai.py
-- تحفظ وثائقها هنا. نتركه باسم ai_documents لأنه مستخدم في الكود.

CREATE TABLE IF NOT EXISTS public.ai_documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL CHECK (char_length(content) BETWEEN 20 AND 12000),
  embedding vector(3072) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- pgvector لا يسمح بإنشاء ivfflat index على vector(3072) في Supabase الحالي.
-- لذلك لا ننشئ فهرسًا متجهيًا هنا. هذا مناسب لحجم معرفة صغير أو متوسط.
DROP INDEX IF EXISTS idx_ai_documents_embedding;

ALTER TABLE public.ai_documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "deny_client_access" ON public.ai_documents;

CREATE POLICY "deny_client_access" ON public.ai_documents
  FOR ALL TO anon, authenticated
  USING (false)
  WITH CHECK (false);

REVOKE ALL ON public.ai_documents FROM anon, authenticated;

-- ============================================================
-- Shared updated_at trigger helper
-- ============================================================

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- ============================================================
-- Safe knowledge sources
-- ============================================================

CREATE TABLE IF NOT EXISTS public.ai_knowledge_sources (
  id BIGSERIAL PRIMARY KEY,
  source_key TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL CHECK (
    source_type IN ('service', 'policy', 'faq', 'scenario', 'glossary', 'manual')
  ),
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_knowledge_sources_type_status
ON public.ai_knowledge_sources(source_type, status);

DROP TRIGGER IF EXISTS trg_ai_knowledge_sources_updated_at ON public.ai_knowledge_sources;
CREATE TRIGGER trg_ai_knowledge_sources_updated_at
BEFORE UPDATE ON public.ai_knowledge_sources
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.ai_knowledge_sources ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "deny_client_access" ON public.ai_knowledge_sources;

CREATE POLICY "deny_client_access" ON public.ai_knowledge_sources
  FOR ALL TO anon, authenticated
  USING (false)
  WITH CHECK (false);

REVOKE ALL ON public.ai_knowledge_sources FROM anon, authenticated;

-- ============================================================
-- Safe knowledge documents
-- ============================================================

CREATE TABLE IF NOT EXISTS public.ai_knowledge_documents (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT REFERENCES public.ai_knowledge_sources(id) ON DELETE CASCADE,
  document_type TEXT NOT NULL CHECK (
    document_type IN ('service', 'policy', 'faq', 'scenario', 'glossary', 'manual')
  ),
  title TEXT NOT NULL,
  content TEXT NOT NULL CHECK (char_length(content) BETWEEN 20 AND 8000),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(3072) NOT NULL,
  content_hash TEXT,
  priority INTEGER NOT NULL DEFAULT 0 CHECK (priority BETWEEN -100 AND 100),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_knowledge_documents_type_active
ON public.ai_knowledge_documents(document_type, is_active);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_knowledge_documents_content_hash
ON public.ai_knowledge_documents(content_hash)
WHERE content_hash IS NOT NULL;

-- ملاحظة مهمة:
-- embedding المستخدم هنا أبعاده 3072، و pgvector لا يسمح بإنشاء ivfflat index
-- على vector بأكثر من 2000 بُعد. لذلك نترك البحث يعمل بدون فهرس متجهي الآن.
-- هذا آمن وصحيح للبيانات الصغيرة والمتوسطة، ويمكن لاحقًا تحسينه بأحد خيارين:
-- 1. استخدام embedding بأبعاد <= 2000.
-- 2. استخدام halfvec(3072) إذا كانت نسخة pgvector في Supabase تدعمه.
DROP INDEX IF EXISTS idx_ai_knowledge_documents_embedding;

DROP TRIGGER IF EXISTS trg_ai_knowledge_documents_updated_at ON public.ai_knowledge_documents;
CREATE TRIGGER trg_ai_knowledge_documents_updated_at
BEFORE UPDATE ON public.ai_knowledge_documents
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.ai_knowledge_documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "deny_client_access" ON public.ai_knowledge_documents;

CREATE POLICY "deny_client_access" ON public.ai_knowledge_documents
  FOR ALL TO anon, authenticated
  USING (false)
  WITH CHECK (false);

REVOKE ALL ON public.ai_knowledge_documents FROM anon, authenticated;

-- ============================================================
-- Assistant safety rules
-- ============================================================

CREATE TABLE IF NOT EXISTS public.ai_safety_rules (
  id BIGSERIAL PRIMARY KEY,
  rule_key TEXT NOT NULL UNIQUE,
  rule_type TEXT NOT NULL CHECK (
    rule_type IN ('allowed_claim', 'forbidden_claim', 'escalation', 'tone', 'pricing', 'privacy')
  ),
  title TEXT NOT NULL,
  instruction TEXT NOT NULL CHECK (char_length(instruction) BETWEEN 10 AND 2000),
  severity INTEGER NOT NULL DEFAULT 50 CHECK (severity BETWEEN 0 AND 100),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_safety_rules_active
ON public.ai_safety_rules(is_active, severity DESC);

DROP TRIGGER IF EXISTS trg_ai_safety_rules_updated_at ON public.ai_safety_rules;
CREATE TRIGGER trg_ai_safety_rules_updated_at
BEFORE UPDATE ON public.ai_safety_rules
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.ai_safety_rules ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "deny_client_access" ON public.ai_safety_rules;

CREATE POLICY "deny_client_access" ON public.ai_safety_rules
  FOR ALL TO anon, authenticated
  USING (false)
  WITH CHECK (false);

REVOKE ALL ON public.ai_safety_rules FROM anon, authenticated;

-- ============================================================
-- Evaluation cases
-- ============================================================

CREATE TABLE IF NOT EXISTS public.ai_eval_cases (
  id BIGSERIAL PRIMARY KEY,
  case_key TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  question TEXT NOT NULL CHECK (char_length(question) BETWEEN 3 AND 1000),
  expected_behavior TEXT NOT NULL CHECK (char_length(expected_behavior) BETWEEN 10 AND 2000),
  expected_keywords TEXT[] NOT NULL DEFAULT '{}',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_eval_cases_active
ON public.ai_eval_cases(is_active, category);

DROP TRIGGER IF EXISTS trg_ai_eval_cases_updated_at ON public.ai_eval_cases;
CREATE TRIGGER trg_ai_eval_cases_updated_at
BEFORE UPDATE ON public.ai_eval_cases
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.ai_eval_cases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "deny_client_access" ON public.ai_eval_cases;

CREATE POLICY "deny_client_access" ON public.ai_eval_cases
  FOR ALL TO anon, authenticated
  USING (false)
  WITH CHECK (false);

REVOKE ALL ON public.ai_eval_cases FROM anon, authenticated;

-- ============================================================
-- Knowledge vector search RPC
-- ============================================================

CREATE OR REPLACE FUNCTION public.match_knowledge_documents(
  query_embedding vector(3072),
  match_threshold DOUBLE PRECISION DEFAULT 0.25,
  match_count INTEGER DEFAULT 8,
  filter_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  title TEXT,
  document_type TEXT,
  metadata JSONB,
  similarity DOUBLE PRECISION
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    d.id,
    d.content,
    d.title,
    d.document_type,
    d.metadata,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM public.ai_knowledge_documents d
  JOIN public.ai_knowledge_sources s ON s.id = d.source_id
  WHERE d.is_active = TRUE
    AND s.status = 'active'
    AND (d.expires_at IS NULL OR d.expires_at > NOW())
    AND (filter_types IS NULL OR d.document_type = ANY(filter_types))
    AND 1 - (d.embedding <=> query_embedding) >= match_threshold
  ORDER BY d.priority DESC, d.embedding <=> query_embedding
  LIMIT LEAST(match_count, 20);
$$;

REVOKE ALL ON FUNCTION public.match_knowledge_documents(
  vector(3072), DOUBLE PRECISION, INTEGER, TEXT[]
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.match_knowledge_documents(
  vector(3072), DOUBLE PRECISION, INTEGER, TEXT[]
) TO service_role;

-- ============================================================
-- Legacy service/policy/scenario vector search RPC
-- ============================================================

CREATE OR REPLACE FUNCTION public.match_services(
  query_embedding vector(3072),
  match_threshold DOUBLE PRECISION DEFAULT 0.25,
  match_count INTEGER DEFAULT 8
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  similarity DOUBLE PRECISION
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    d.id,
    d.content,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM public.ai_documents d
  WHERE 1 - (d.embedding <=> query_embedding) >= match_threshold
  ORDER BY d.embedding <=> query_embedding
  LIMIT LEAST(match_count, 20);
$$;

REVOKE ALL ON FUNCTION public.match_services(
  vector(3072), DOUBLE PRECISION, INTEGER
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.match_services(
  vector(3072), DOUBLE PRECISION, INTEGER
) TO service_role;

-- ============================================================
-- Done
-- ============================================================
