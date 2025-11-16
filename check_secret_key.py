"""
Check if FLASK_SECRET_KEY is properly configured
"""

import os
from dotenv import load_dotenv

print("="*60)
print("Checking Flask Secret Key Configuration")
print("="*60)

load_dotenv()

secret_key = os.getenv('FLASK_SECRET_KEY')

print("\nFLASK_SECRET_KEY Status:")

if not secret_key:
    print("   [ERROR] FLASK_SECRET_KEY is not set!")
    print("   Flask will use a random key (sessions won't persist)")
    print("\n   FIX:")
    print("   1. Generate a key:")
    print('      python -c "import secrets; print(secrets.token_hex(32))"')
    print("   2. Add to .env file:")
    print("      FLASK_SECRET_KEY=your_generated_key_here")
elif 'your_secret_key' in secret_key:
    print("   [ERROR] FLASK_SECRET_KEY is still the placeholder!")
    print(f"   Current value: {secret_key}")
    print("\n   FIX:")
    print("   1. Generate a key:")
    print('      python -c "import secrets; print(secrets.token_hex(32))"')
    print("   2. Replace the placeholder in .env")
elif len(secret_key) < 32:
    print(f"   [WARNING] FLASK_SECRET_KEY is too short ({len(secret_key)} chars)")
    print("   Should be at least 32 characters for security")
    print("\n   FIX:")
    print('      python -c "import secrets; print(secrets.token_hex(32))"')
else:
    print(f"   [OK] FLASK_SECRET_KEY is set (length: {len(secret_key)})")
    print(f"   Value: {secret_key[:8]}...{secret_key[-8:]}")

print("\n" + "="*60)
print("What to do now:")
print("="*60)

if secret_key and 'your_secret_key' not in secret_key and len(secret_key) >= 32:
    print("""
[OK] Your secret key looks good!

Next steps:
1. Restart Flask: python app.py
2. Clear browser cookies/cache OR use incognito mode
3. Try connecting to Spotify again
4. The "state mismatch" error should be gone!
""")
else:
    print("""
[ACTION NEEDED]

1. Generate a secret key:
   python -c "import secrets; print(secrets.token_hex(32))"

2. Copy the output (it will look like):
   9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e

3. Open .env file:
   notepad .env

4. Set FLASK_SECRET_KEY to the generated value:
   FLASK_SECRET_KEY=9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e

5. Save and restart Flask:
   python app.py

6. Clear browser cache or use incognito mode

7. Try again!
""")

print("="*60)
