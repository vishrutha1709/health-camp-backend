from supabase import create_client, Client
from flask import current_app

_supabase_client = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = current_app.config['SUPABASE_URL']
        key = current_app.config['SUPABASE_KEY']
        if not url or not key:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY missing")
        _supabase_client = create_client(url, key)
    return _supabase_client