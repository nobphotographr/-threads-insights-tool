-- 外部キー制約を後から追加
-- テーブル作成後に実行

ALTER TABLE media_insights 
ADD CONSTRAINT fk_media_insights_media_id 
FOREIGN KEY (media_id) REFERENCES threads_media(media_id) ON DELETE CASCADE;