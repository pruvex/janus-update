import asyncio
import os
import sys
import logging

# Pfade anpassen - ROOT ist C:\KI\Janus-Projekt
# Wir brauchen C:\KI\Janus-Projekt als Basis
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Debug
# print(f"DEBUG: __file__ is {__file__}")
# print(f"DEBUG: root_dir determined as {root_dir}")

# Explizit sicherstellen, dass backend.data importiert werden kann
try:
    from backend.data import schemas
    from backend.tool_registry import websearch_wrapper
except ImportError as e:
    print(f"PFAD-ERROR: {e}")
    print(f"SYS.PATH: {sys.path}")
    sys.exit(1)

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diamond_test")

async def test_websearch_diamond():
    """Testet den system.websearch Skill auf Diamond-Niveau."""
    print("\n💎 START DIAMOND TEST: system.websearch (V0.5.0) 💎")
    
    # 1. Test-Input (Realistisches Szenario)
    test_args = schemas.WebsearchArgsV2(
        query="Nintendo Switch 2 Release Preis Deutschland",
        provider="openai" # Wir nutzen OpenAI für den "Extraktions-Mut"
    )
    
    print(f"📡 Sende Suchanfrage: '{test_args.query}' via {test_args.provider}...")
    
    try:
        # 2. Skill-Ausführung
        response_dict = await websearch_wrapper(test_args)
        if hasattr(response_dict, "model_dump"):
            response_dict = response_dict.model_dump()
        exec_ms = None
        meta = response_dict.get("metadata")
        if isinstance(meta, dict):
            exec_ms = meta.get("execution_time_ms")

        # 3. Validierung des Contracts (SkillResponse-kompatibel aus ToolResultV1)
        response = schemas.SkillResponse.model_validate(
            {
                "status": response_dict.get("status"),
                "data": response_dict.get("data"),
                "error": response_dict.get("error"),
                "execution_time_ms": exec_ms,
            }
        )

        if response.status == "ok":
            print(f"✅ STATUS: OK (Execution Time: {response.execution_time_ms}ms)")
            
            data = response.data
            if isinstance(data, dict):
                text = data.get("text", "")
                urls = data.get("urls", [])
                source = data.get("source", "unknown")
                
                print(f"📊 QUELLE: {source}")
                print(f"🔗 URLS GEFUNDEN: {len(urls)}")
                
                # Stichprobenartige Inhaltsprüfung für "Extraktions-Mut"
                content_preview = text[:200].replace('\n', ' ')
                print(f"📝 INHALT (Vorschau): {content_preview}...")
                
                # Check auf Kosten-Persistierung (indirekt über Tool-Return)
                cost = data.get("cost", {})
                print(f"💰 KOSTEN: {cost.get('total_cost', '0.00')} {cost.get('currency', 'USD')}")
                
                if len(text) > 500:
                    print("💎 QUALITÄTS-CHECK: EXZELLENT (Detaillierter Text vorhanden)")
                else:
                    print("⚠️ QUALITÄTS-CHECK: NIEDRIG (Text zu kurz)")
            else:
                print("❌ FEHLER: data ist kein Dictionary.")
        else:
            print(f"❌ STATUS: ERROR ({response.error})")
            
    except Exception as e:
        print(f"💥 TEST ABGEBROCHEN: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websearch_diamond())
