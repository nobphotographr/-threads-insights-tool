#!/usr/bin/env python3
"""
データベーステーブルの初期化スクリプト
"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from urllib.parse import urlparse

def get_db_connection():
    """PostgreSQL直接接続を取得"""
    load_dotenv()
    
    # SupabaseのURLからPostgreSQL接続情報を構築
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    # edltrnproepezcuagzxf.supabase.co から DB接続情報を構築
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    conn_string = f"postgresql://postgres:{db_password}@db.{project_id}.supabase.co:5432/postgres"
    
    return psycopg2.connect(conn_string)

def init_database():
    """データベーススキーマを初期化"""
    
    # SQLファイル読み込み
    schema_file = Path(__file__).parent / "schema.sql"
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # PostgreSQL直接接続でスキーマ実行
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 複数のSQL文を分割して実行
        # コメント行と空行を除去してから分割
        cleaned_sql = '\n'.join([
            line for line in schema_sql.split('\n') 
            if line.strip() and not line.strip().startswith('--')
        ])
        statements = [stmt.strip() for stmt in cleaned_sql.split(';') if stmt.strip()]
        
        print(f"📝 Found {len(statements)} SQL statements")
        
        # CREATE TABLE文とCREATE INDEX文を分離して順序よく実行
        create_table_statements = []
        create_index_statements = []
        other_statements = []
        
        print("\n🔍 Analyzing SQL statements:")
        for i, statement in enumerate(statements):
            stmt_upper = statement.upper()
            if stmt_upper.startswith('CREATE TABLE'):
                create_table_statements.append(statement)
                print(f"  TABLE: {statement[:60]}...")
            elif stmt_upper.startswith('CREATE INDEX'):
                create_index_statements.append(statement)
                print(f"  INDEX: {statement[:60]}...")
            elif stmt_upper.startswith(('CREATE', 'DROP', 'ALTER', 'INSERT')):
                other_statements.append(statement)
                print(f"  OTHER: {statement[:60]}...")
            else:
                print(f"  SKIP: {statement[:60]}...")
        
        print(f"\n📊 Summary: {len(create_table_statements)} tables, {len(create_index_statements)} indexes, {len(other_statements)} others")
        
        # 順序付きで実行: テーブル → その他 → インデックス
        all_ordered = create_table_statements + other_statements + create_index_statements
        
        for i, statement in enumerate(all_ordered):
            try:
                print(f"🔄 [{i+1}/{len(all_ordered)}] Executing: {statement[:100]}...")
                cursor.execute(statement)
                print(f"✓ [{i+1}] Success")
            except Exception as e:
                print(f"❌ [{i+1}] Error: {e}")
                print(f"   Statement: {statement}")
                raise
        
        conn.commit()
        
        print("\n✅ Database schema initialized successfully!")
        
        # テーブル一覧確認
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'threads_%' OR table_name LIKE '%_insights%' OR table_name = 'ingest_runs'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print("\n📋 Created tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
        cursor.close()
        conn.close()
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

def test_connection():
    """データベース接続テスト"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT current_timestamp as now")
        result = cursor.fetchone()
        
        print(f"✅ Database connection successful!")
        print(f"   Current time: {result[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_supabase_client():
    """Supabaseクライアント接続テスト"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return False
        
    try:
        supabase: Client = create_client(url, key)
        
        # 簡単なテーブル存在確認
        result = supabase.table('threads_media').select('count', count='exact').limit(0).execute()
        
        print(f"✅ Supabase client connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Supabase client connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initializing Threads Insights Database...")
    
    # 接続テスト
    if test_connection():
        # スキーマ初期化
        init_database()
        
        # Supabaseクライアントテスト
        print("\n🔍 Testing Supabase client...")
        test_supabase_client()
    else:
        print("❌ Cannot proceed without database connection")