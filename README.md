# Threads Insights Tool

自分のThreads運用を可視化し、改善PDCAを高速化するツール

## セットアップ

### 1. 仮想環境作成
```bash
python -m venv threads-env
source threads-env/bin/activate  # macOS/Linux
# threads-env\Scripts\activate  # Windows
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. 環境変数設定
```bash
cp .env.template .env
# .envファイルを編集して必要な値を設定
```

### 4. データベース初期化
```bash
python app/db/init_tables.py
```

### 5. アプリケーション起動
```bash
uvicorn app.api.main:app --reload
```

## API エンドポイント

- `GET /health` - ヘルスチェック
- `POST /ingest/run` - 手動データ収集
- `GET /metrics/posts` - 投稿指標一覧
- `GET /metrics/user/summary` - ユーザー指標サマリー

## プロジェクト構造

```
threads-insights-tool/
├── app/
│   ├── ingest/          # データ取得処理
│   ├── services/        # 外部API連携
│   ├── db/             # データベース関連
│   └── api/            # FastAPI エンドポイント
├── infra/              # インフラ設定
├── dashboards/         # BI ダッシュボード
└── tests/             # テストコード
```