# C:\KI\Janus-Projekt\backend\test_google_import.py
import sys
from pprint import pprint

print("--- STARTING FINAL DIAGNOSTIC TEST ---")
print("\n1. Current Python executable:")
print(sys.executable)

print("\n2. Current sys.path:")
pprint(sys.path)

try:
    print("\n3. Attempting to import 'google.genai'...")
    import google.genai as genai
    print("\n--- IMPORT SUCCESSFUL! ---")
    print(f"Successfully imported 'genai'. Location: {genai.__file__}")
except ImportError as e:
    print("\n--- IMPORT FAILED! ---")
    print(f"Error: {e}")
    try:
        import google
        print("\nImporting 'google' base package was successful.")
        print(f"Path of 'google' package found: {google.__path__}")
        print("Conclusion: The 'google' namespace is found, but the 'genai' sub-module is missing or conflicting.")
    except Exception as e_inner:
        print(f"Could not even import the base 'google' package. Error: {e_inner}")
except Exception as e:
    print(f"\n--- UNEXPECTED ERROR DURING IMPORT ---")
    print(e)

print("\n--- TEST FINISHED ---")
