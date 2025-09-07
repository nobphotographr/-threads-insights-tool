#!/usr/bin/env python3
"""
Threads API OAuth認証サービス
"""

import os
import secrets
import requests
from urllib.parse import urlencode, parse_qs
from dotenv import load_dotenv

load_dotenv()

class ThreadsAuthService:
    def __init__(self):
        self.app_id = os.getenv("THREADS_APP_ID")
        self.app_secret = os.getenv("THREADS_APP_SECRET")
        # Vercelデプロイ時はHTTPS URL、ローカル開発時はlocalhost
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            self.redirect_uri = f"https://{vercel_url}/auth/threads/callback"
        else:
            self.redirect_uri = "https://threads-insights-tool.vercel.app/auth/threads/callback"
        
        if not self.app_id or not self.app_secret:
            raise ValueError("Missing THREADS_APP_ID or THREADS_APP_SECRET")
    
    def generate_auth_url(self, state: str = None) -> str:
        """OAuth認証URLを生成"""
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'threads_basic,threads_manage_insights',
            'response_type': 'code',
            'state': state
        }
        
        base_url = "https://threads.net/oauth/authorize"
        return f"{base_url}?{urlencode(params)}", state
    
    def exchange_code_for_token(self, authorization_code: str) -> dict:
        """認証コードをアクセストークンに交換"""
        token_url = "https://graph.threads.net/oauth/access_token"
        
        data = {
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code': authorization_code
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_long_lived_token(self, short_lived_token: str) -> dict:
        """短期トークンを長期トークン（60日）に交換"""
        exchange_url = "https://graph.threads.net/access_token"
        
        params = {
            'grant_type': 'th_exchange_token',
            'client_secret': self.app_secret,
            'access_token': short_lived_token
        }
        
        response = requests.get(exchange_url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_long_lived_token(self, long_lived_token: str) -> dict:
        """長期トークンをリフレッシュ"""
        refresh_url = "https://graph.threads.net/refresh_access_token"
        
        params = {
            'grant_type': 'th_refresh_token',
            'access_token': long_lived_token
        }
        
        response = requests.get(refresh_url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def test_token(self, access_token: str) -> dict:
        """アクセストークンの動作テスト"""
        test_url = "https://graph.threads.net/v1.0/me"
        
        params = {
            'fields': 'id,username,name,threads_profile_picture_url,threads_biography',
            'access_token': access_token
        }
        
        response = requests.get(test_url, params=params)
        response.raise_for_status()
        
        return response.json()