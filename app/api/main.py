#!/usr/bin/env python3
"""
Threads Insights Tool - FastAPI メインアプリケーション
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv
from supabase import create_client, Client
from app.services.threads_auth import ThreadsAuthService

# 環境変数読み込み
load_dotenv()

# FastAPIアプリケーション作成
app = FastAPI(
    title="Threads Insights Tool",
    description="自分のThreads運用を可視化し、改善PDCAを高速化するAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabaseクライアント
def get_supabase_client() -> Client:
    """Supabaseクライアントを取得"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise HTTPException(
            status_code=500, 
            detail="Missing Supabase configuration"
        )
    
    return create_client(url, key)

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """API稼働確認"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "threads-insights-tool"
    }

# データベース接続テスト
@app.get("/health/database")
async def database_health():
    """データベース接続確認"""
    try:
        supabase = get_supabase_client()
        
        # 簡単なクエリでテスト
        result = supabase.table('ingest_runs').select('count', count='exact').limit(0).execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )

# 基本的な統計情報
@app.get("/stats/summary")
async def get_stats_summary():
    """基本統計情報取得"""
    try:
        supabase = get_supabase_client()
        
        # 各テーブルの件数取得
        stats = {}
        
        tables = [
            'threads_media', 
            'media_insights', 
            'user_insights_daily', 
            'ingest_runs'
        ]
        
        for table in tables:
            result = supabase.table(table).select('count', count='exact').limit(0).execute()
            stats[f"{table}_count"] = result.count if result.count else 0
        
        # 最新の実行日時
        latest_run = supabase.table('ingest_runs')\
            .select('started_at')\
            .order('started_at', desc=True)\
            .limit(1)\
            .execute()
        
        latest_run_time = None
        if latest_run.data:
            latest_run_time = latest_run.data[0]['started_at']
        
        return {
            "stats": stats,
            "latest_run": latest_run_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )

# 手動データ収集トリガー（今後実装）
@app.post("/ingest/run")
async def trigger_data_ingestion():
    """手動データ収集実行"""
    return {
        "message": "Data ingestion triggered (not implemented yet)",
        "timestamp": datetime.utcnow().isoformat()
    }

# OAuth認証フロー
@app.get("/auth/threads/login")
async def threads_login():
    """Threads OAuth認証を開始"""
    try:
        auth_service = ThreadsAuthService()
        auth_url, state = auth_service.generate_auth_url()
        
        # 実際のアプリでは、stateをセッションやDBに保存する
        return {
            "auth_url": auth_url,
            "state": state,
            "message": "Visit the auth_url to authorize the application"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/threads/callback")
async def threads_callback(request: Request):
    """Threads OAuth認証コールバック"""
    try:
        # クエリパラメータから認証コードを取得
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')
        
        if error:
            raise HTTPException(status_code=400, detail=f"Authorization failed: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        
        auth_service = ThreadsAuthService()
        
        # 短期トークンを取得
        token_response = auth_service.exchange_code_for_token(code)
        short_token = token_response['access_token']
        
        # 長期トークン（60日）に交換
        long_token_response = auth_service.get_long_lived_token(short_token)
        long_token = long_token_response['access_token']
        
        # ユーザー情報をテスト取得
        user_info = auth_service.test_token(long_token)
        
        # 成功レスポンス（実際のアプリでは.envファイルやDBに保存）
        success_html = f"""
        <html>
        <body>
            <h2>✅ Threads API 認証成功！</h2>
            <p><strong>ユーザー名:</strong> {user_info.get('username', 'Unknown')}</p>
            <p><strong>名前:</strong> {user_info.get('name', 'Unknown')}</p>
            <p><strong>User ID:</strong> {user_info.get('id', 'Unknown')}</p>
            
            <h3>🔑 アクセストークン</h3>
            <p><small>このトークンを.envファイルのTHREADS_ACCESS_TOKENに設定してください:</small></p>
            <textarea readonly style="width:100%;height:100px;">{long_token}</textarea>
            
            <h3>📝 次のステップ</h3>
            <ol>
                <li>上記のトークンをコピー</li>
                <li>.envファイルのTHREADS_ACCESS_TOKENに設定</li>
                <li>/threads/me エンドポイントでAPIテスト実行</li>
            </ol>
            
            <p><a href="/threads/me" target="_blank">→ APIテストを実行</a></p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=success_html)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Meta必須コールバックエンドポイント（ダミー実装）
@app.post("/auth/threads/uninstall")
async def threads_uninstall_callback(request: Request):
    """アプリアンインストール通知（ダミー）"""
    return {"status": "received", "message": "App uninstall callback"}

@app.post("/auth/threads/deauthorize")  
async def threads_deauthorize_callback(request: Request):
    """権限削除通知（ダミー）"""
    return {"status": "received", "message": "Deauthorize callback"}

# Threads API テストエンドポイント
@app.get("/threads/me")
async def get_threads_user():
    """認証済みユーザー情報を取得"""
    try:
        access_token = os.getenv("THREADS_ACCESS_TOKEN")
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Missing THREADS_ACCESS_TOKEN in environment variables"
            )
        
        auth_service = ThreadsAuthService()
        user_info = auth_service.test_token(access_token)
        
        return {
            "user_info": user_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)