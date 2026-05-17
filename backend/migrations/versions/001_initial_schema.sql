-- ============================================================
-- Drama Factory — Initial Database Schema
-- Run once against a fresh PostgreSQL + pgvector database.
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- for fast text search

-- ── Users & Profiles ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    avatar_url      TEXT,
    bio             TEXT,
    timezone        TEXT DEFAULT 'UTC',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_users_email        ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_is_active    ON users (is_active);

-- ── Memories (MemoryOS core) ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS memories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    content_type    TEXT NOT NULL,          -- 'note' | 'article' | 'learning_event' | etc.
    topic           TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    fingerprint     TEXT NOT NULL,          -- SHA-256 for deduplication
    embedding       vector(1024),           -- Voyage-3 embeddings
    deleted_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vector similarity index (IVFFlat with 100 lists, suitable for < 1M rows)
CREATE INDEX IF NOT EXISTS ix_memories_embedding_cosine
    ON memories USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Full-text search index
CREATE INDEX IF NOT EXISTS ix_memories_fts
    ON memories USING GIN (to_tsvector('simple', content));

CREATE INDEX IF NOT EXISTS ix_memories_user_id      ON memories (user_id);
CREATE INDEX IF NOT EXISTS ix_memories_content_type ON memories (content_type);
CREATE INDEX IF NOT EXISTS ix_memories_topic        ON memories (topic);
CREATE INDEX IF NOT EXISTS ix_memories_fingerprint  ON memories (user_id, fingerprint);

-- ── Knowledge Graph (memory edges) ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS memory_edges (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_a_id       UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    node_b_id       UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,          -- 'related_to' | 'caused_by' | 'follows' | etc.
    weight          FLOAT NOT NULL DEFAULT 1.0,
    deleted_at      TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (node_a_id, node_b_id, relation_type)
);

CREATE INDEX IF NOT EXISTS ix_memory_edges_node_a ON memory_edges (node_a_id);
CREATE INDEX IF NOT EXISTS ix_memory_edges_node_b ON memory_edges (node_b_id);

-- ── InvestMind ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS watchlists (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol              TEXT NOT NULL,
    notes               TEXT,
    alert_price_above   DOUBLE PRECISION,
    alert_price_below   DOUBLE PRECISION,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, symbol)
);

CREATE INDEX IF NOT EXISTS ix_watchlists_user_id ON watchlists (user_id);
CREATE INDEX IF NOT EXISTS ix_watchlists_symbol  ON watchlists (symbol);

CREATE TABLE IF NOT EXISTS research_notes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol      TEXT,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    tags        TEXT[] NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_research_notes_user_id ON research_notes (user_id);
CREATE INDEX IF NOT EXISTS ix_research_notes_symbol  ON research_notes (symbol);
CREATE INDEX IF NOT EXISTS ix_research_notes_tags    ON research_notes USING GIN (tags);

CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    source_url      TEXT,
    content_type    TEXT NOT NULL DEFAULT 'pdf',
    raw_text        TEXT,
    summary         TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    processed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents (user_id);

-- ── AvatarOS ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS avatars (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    photo_url           TEXT,
    heygen_avatar_id    TEXT NOT NULL DEFAULT '',
    status              TEXT NOT NULL DEFAULT 'pending',  -- pending | active | deleted
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_avatars_user_id ON avatars (user_id);
CREATE INDEX IF NOT EXISTS ix_avatars_status  ON avatars (status);

CREATE TABLE IF NOT EXISTS generation_tasks (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    avatar_id           UUID NOT NULL REFERENCES avatars(id) ON DELETE CASCADE,
    script              TEXT NOT NULL,
    language            TEXT NOT NULL DEFAULT 'zh',
    voice_id            TEXT,
    stage               TEXT NOT NULL DEFAULT 'pending',
    heygen_video_id     TEXT,
    video_url           TEXT,
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_generation_tasks_avatar_id ON generation_tasks (avatar_id);
CREATE INDEX IF NOT EXISTS ix_generation_tasks_stage     ON generation_tasks (stage);

-- ── EduStar ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS courses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    topic           TEXT NOT NULL,
    difficulty      TEXT NOT NULL DEFAULT 'beginner',
    duration_weeks  INT NOT NULL DEFAULT 4,
    tags            TEXT[] NOT NULL DEFAULT '{}',
    is_published    BOOLEAN NOT NULL DEFAULT false,
    outline_json    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_courses_user_id      ON courses (user_id);
CREATE INDEX IF NOT EXISTS ix_courses_topic        ON courses (topic);
CREATE INDEX IF NOT EXISTS ix_courses_is_published ON courses (is_published);

CREATE TABLE IF NOT EXISTS lessons (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id           UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title               TEXT NOT NULL,
    lesson_type         TEXT NOT NULL DEFAULT 'article',
    content             TEXT NOT NULL DEFAULT '',
    order_index         INT NOT NULL DEFAULT 0,
    duration_minutes    INT NOT NULL DEFAULT 10,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_lessons_course_id    ON lessons (course_id);
CREATE INDEX IF NOT EXISTS ix_lessons_order_index  ON lessons (course_id, order_index);

CREATE TABLE IF NOT EXISTS learner_events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id   UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lesson_id   UUID REFERENCES lessons(id) ON DELETE SET NULL,
    event_type  TEXT NOT NULL,   -- started | completed | paused | quiz_submitted
    payload     JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_learner_events_user_course ON learner_events (user_id, course_id);
CREATE INDEX IF NOT EXISTS ix_learner_events_event_type  ON learner_events (event_type);

-- ── Billing ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS subscriptions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan                    TEXT NOT NULL DEFAULT 'free',    -- free | pro | enterprise
    status                  TEXT NOT NULL DEFAULT 'active',  -- active | cancelled | past_due | trialing
    stripe_subscription_id  TEXT,
    stripe_customer_id      TEXT,
    current_period_start    TIMESTAMPTZ NOT NULL DEFAULT now(),
    current_period_end      TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '30 days',
    cancel_at_period_end    BOOLEAN NOT NULL DEFAULT false,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions (user_id);
CREATE INDEX IF NOT EXISTS ix_subscriptions_status  ON subscriptions (status);

CREATE TABLE IF NOT EXISTS usage_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_type   TEXT NOT NULL,   -- llm_tokens | video_minutes | storage_mb
    quantity        DOUBLE PRECISION NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_usage_logs_user_id       ON usage_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_usage_logs_resource_type ON usage_logs (resource_type);
CREATE INDEX IF NOT EXISTS ix_usage_logs_created_at    ON usage_logs (created_at);

-- ── Notifications ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS notifications (
    id                  TEXT PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               TEXT NOT NULL,
    body                TEXT NOT NULL,
    notification_type   TEXT NOT NULL DEFAULT 'info',
    metadata            JSONB NOT NULL DEFAULT '{}',
    read_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_notifications_user_id   ON notifications (user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_read_at   ON notifications (user_id, read_at);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Enable RLS on all user-scoped tables so Supabase policies apply.

ALTER TABLE users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories           ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_edges       ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlists         ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_notes     ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents          ENABLE ROW LEVEL SECURITY;
ALTER TABLE avatars            ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_tasks   ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses            ENABLE ROW LEVEL SECURITY;
ALTER TABLE lessons            ENABLE ROW LEVEL SECURITY;
ALTER TABLE learner_events     ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs         ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications      ENABLE ROW LEVEL SECURITY;

-- Users can only read/write their own rows
-- (Service role key bypasses RLS for backend operations)

CREATE POLICY IF NOT EXISTS "users_self"
    ON users FOR ALL TO authenticated
    USING (id = auth.uid());

CREATE POLICY IF NOT EXISTS "memories_owner"
    ON memories FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "watchlists_owner"
    ON watchlists FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "research_notes_owner"
    ON research_notes FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "documents_owner"
    ON documents FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "avatars_owner"
    ON avatars FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "courses_owner"
    ON courses FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "learner_events_owner"
    ON learner_events FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "subscriptions_owner"
    ON subscriptions FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "usage_logs_owner"
    ON usage_logs FOR ALL TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY IF NOT EXISTS "notifications_owner"
    ON notifications FOR ALL TO authenticated
    USING (user_id = auth.uid());

-- ── Helper function: update updated_at automatically ─────────────────────────

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'users', 'watchlists', 'research_notes', 'avatars',
        'generation_tasks', 'courses', 'subscriptions'
    ] LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%1$s_updated_at ON %1$s;
             CREATE TRIGGER trg_%1$s_updated_at
             BEFORE UPDATE ON %1$s
             FOR EACH ROW EXECUTE FUNCTION set_updated_at();',
            t
        );
    END LOOP;
END;
$$;
