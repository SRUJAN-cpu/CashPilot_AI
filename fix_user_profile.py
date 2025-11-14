"""
Quick fix script to manually create missing user profile
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def fix_user_profile(user_email):
    """Create missing user profile in public.users table"""

    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        print("[ERROR] Missing Supabase credentials in .env")
        return

    # Create admin client (bypasses RLS)
    supabase = create_client(supabase_url, service_role_key)

    print(f"\nLooking for user with email: {user_email}")

    # Get user from auth.users
    try:
        auth_users = supabase.auth.admin.list_users()
        user = None
        for u in auth_users:
            if u.email == user_email:
                user = u
                break

        if not user:
            print(f"[ERROR] No auth user found with email: {user_email}")
            return

        print(f"[OK] Found auth user: {user.id}")

        # Check if profile exists
        profile = supabase.table("users").select("*").eq("id", user.id).execute()

        if profile.data:
            print(f"[OK] User profile already exists!")
            print(f"   ID: {profile.data[0]['id']}")
            print(f"   Email: {profile.data[0]['email']}")
            print(f"   Name: {profile.data[0].get('name', 'N/A')}")
            return

        # Create profile
        print(f"\nCreating user profile...")
        user_profile = {
            "id": user.id,
            "email": user.email,
            "name": user.user_metadata.get("name") if user.user_metadata else None,
        }

        result = supabase.table("users").insert(user_profile).execute()

        if result.data:
            print(f"[SUCCESS] User profile created successfully!")
            print(f"   ID: {result.data[0]['id']}")
            print(f"   Email: {result.data[0]['email']}")
            print(f"   Name: {result.data[0].get('name', 'N/A')}")
        else:
            print(f"[ERROR] Failed to create profile")

    except Exception as e:
        print(f"[ERROR] Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_user_profile.py <user_email>")
        print("\nExample: python fix_user_profile.py user@example.com")
        sys.exit(1)

    fix_user_profile(sys.argv[1])
