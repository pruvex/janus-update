#!/usr/bin/env python3
"""
Key Diagnostic Script
Checks which API keys are stored in the keyring and their naming conventions.
"""
import keyring
import os
from typing import Dict, List


def check_keyring_keys() -> Dict[str, Dict[str, str]]:
    """Check for keys in keyring with various service/username combinations."""
    results = {}
    
    # Common service names to check
    services = ["Janus-Projekt", "janus-projekt", "Janus", "janus"]
    
    # Common provider names to check (case-sensitive!)
    providers = [
        "openai",
        "OpenAI",
        "OPENAI",
        "gemini",
        "Gemini",
        "GEMINI",
        "google",
        "Google",
        "GOOGLE"
    ]
    
    print("🔑 KEYRING DIAGNOSTIC SCRIPT")
    print("=" * 60)
    
    for service in services:
        print(f"\n🔍 Checking service: '{service}'")
        service_results = {}
        
        for provider in providers:
            try:
                password = keyring.get_password(service, provider)
                if password:
                    # Mask the password for security
                    masked = password[:4] + "*" * (len(password) - 8) + password[-4:] if len(password) > 8 else "****"
                    service_results[provider] = {
                        "found": True,
                        "masked_value": masked,
                        "length": len(password)
                    }
                    print(f"  ✅ Found key for provider '{provider}': {masked} (length: {len(password)})")
                else:
                    service_results[provider] = {"found": False}
                    print(f"  ❌ No key found for provider '{provider}'")
            except Exception as e:
                service_results[provider] = {"found": False, "error": str(e)}
                print(f"  ⚠️ Error checking provider '{provider}': {e}")
        
        if service_results:
            results[service] = service_results
    
    # Check environment variables
    print("\n" + "=" * 60)
    print("🔍 Checking Environment Variables")
    print("=" * 60)
    
    env_vars = [
        "OPENAI_API_KEY",
        "openai_api_key",
        "GEMINI_API_KEY",
        "gemini_api_key",
        "GOOGLE_API_KEY",
        "google_api_key"
    ]
    
    env_results = {}
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
            env_results[var] = {
                "found": True,
                "masked_value": masked,
                "length": len(value)
            }
            print(f"  ✅ {var}: {masked} (length: {len(value)})")
        else:
            env_results[var] = {"found": False}
            print(f"  ❌ {var}: Not set")
    
    # Check backend/.env file
    print("\n" + "=" * 60)
    print("🔍 Checking backend/.env file")
    print("=" * 60)
    
    env_file_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_file_results = {}
    
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if "API_KEY" in key.upper():
                            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                            env_file_results[key] = {
                                "found": True,
                                "masked_value": masked,
                                "length": len(value)
                            }
                            print(f"  ✅ {key}: {masked} (length: {len(value)})")
        except Exception as e:
            print(f"  ⚠️ Error reading .env file: {e}")
    else:
        print(f"  ❌ .env file not found at: {env_file_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    keyring_found = any(any(p["found"] for p in s.values()) for s in results.values())
    env_found = any(e["found"] for e in env_results.values())
    env_file_found = any(e["found"] for e in env_file_results.values())
    
    print(f"Keyring keys found: {'Yes' if keyring_found else 'No'}")
    print(f"Environment variables found: {'Yes' if env_found else 'No'}")
    print(f"backend/.env keys found: {'Yes' if env_file_found else 'No'}")
    
    # Recommendation
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATION")
    print("=" * 60)
    
    if keyring_found:
        print("✅ Keys found in keyring. Use keyring.get_password() with the correct service/username combination.")
    elif env_found:
        print("⚠️ Keys found in environment variables. Consider using os.environ.get() as fallback.")
    elif env_file_found:
        print("⚠️ Keys found in backend/.env. Consider loading from .env as fallback.")
    else:
        print("❌ No API keys found in any location. You need to configure API keys for the audit to work.")
    
    return {
        "keyring": results,
        "environment": env_results,
        "env_file": env_file_results
    }


if __name__ == "__main__":
    check_keyring_keys()
