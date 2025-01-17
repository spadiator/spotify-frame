import os
from supabase import create_client, Client

# Use your actual Supabase credentials
SUPABASE_URL = "https://lsbbqdhbhnxhosrrmqkn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzYmJxZGhiaG54aG9zcnJtcWtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwNDY0ODYsImV4cCI6MjA1MjYyMjQ4Nn0.RJqYuXQAV5KJiC5_PNUPOQq_qukUlMF2NYm-osZK-PE"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test inserting a new user
def test_create_user():
    response = supabase.table("users").insert({"email": "test@example.com", "password": "hashed_password"}).execute()
    print("User Created:", response)

if __name__ == "__main__":
    test_create_user()