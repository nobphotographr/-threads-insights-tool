-- Threads Insights Tool Database Schema

-- ユーザーのThreads投稿（メディア）情報
CREATE TABLE threads_media (
    media_id TEXT PRIMARY KEY,
    author_user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    media_type TEXT NOT NULL, -- TEXT, IMAGE, VIDEO, CAROUSEL_ALBUM
    permalink TEXT,
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);

-- 投稿ごとの指標データ（日次スナップショット）
CREATE TABLE media_insights (
    media_id TEXT NOT NULL,
    as_of_date DATE NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    quotes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    PRIMARY KEY (media_id, as_of_date)
);

-- ユーザー全体の指標データ（日次）
CREATE TABLE user_insights_daily (
    as_of_date DATE PRIMARY KEY,
    views INTEGER DEFAULT 0,           -- プロフィール閲覧数（時系列）
    likes INTEGER DEFAULT 0,          -- 総いいね数（累計）
    replies INTEGER DEFAULT 0,        -- 総リプライ数（累計）
    reposts INTEGER DEFAULT 0,        -- 総リポスト数（累計）
    quotes INTEGER DEFAULT 0,         -- 総引用数（累計）
    followers_count INTEGER DEFAULT 0, -- フォロワー数（スナップショット）
    clicks INTEGER DEFAULT 0          -- リンククリック数（累計）
);

-- リンククリック数（URL別・日次）
CREATE TABLE link_clicks_daily (
    as_of_date DATE NOT NULL,
    link_url TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    PRIMARY KEY (as_of_date, link_url)
);

-- フォロワー属性データ
CREATE TABLE follower_demographics (
    snapshot_date DATE NOT NULL,
    breakdown_type TEXT NOT NULL,     -- country, city, age, gender
    breakdown_key TEXT NOT NULL,      -- 具体的な値（JP, Tokyo, 25-34, male等）
    value INTEGER DEFAULT 0,
    PRIMARY KEY (snapshot_date, breakdown_type, breakdown_key)
);

-- データ取得実行履歴
CREATE TABLE ingest_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL,             -- success, failed, running
    error_message TEXT,
    media_count INTEGER DEFAULT 0,
    user_insights_updated BOOLEAN DEFAULT FALSE
);

-- インデックス作成
CREATE INDEX idx_media_insights_date ON media_insights(as_of_date);
CREATE INDEX idx_media_insights_media_id ON media_insights(media_id);
CREATE INDEX idx_threads_media_created_at ON threads_media(created_at);
CREATE INDEX idx_link_clicks_date ON link_clicks_daily(as_of_date);
CREATE INDEX idx_user_insights_date ON user_insights_daily(as_of_date);
CREATE INDEX idx_ingest_runs_status ON ingest_runs(status);
CREATE INDEX idx_ingest_runs_started_at ON ingest_runs(started_at);

-- RLS (Row Level Security) 設定は後で必要に応じて追加
-- 現在は単一ユーザー前提のため省略