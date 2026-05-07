
import asyncio
import openai
import os

async def test_openai_tool_call():
    """
    Testet die Tool-Nutzung mit einem minimalen Setup für ein OpenAI-Modell.
    """
    if "OPENAI_API_KEY" not in os.environ:
        print("SKIP: Bitte setzen Sie die Umgebungsvariable OPENAI_API_KEY.")
        return

    client = openai.AsyncOpenAI()

    # 1. Ein einfacher, direkter System-Prompt, der die Tool-Nutzung fördert
    system_prompt = "Du bist ein Assistent, der Werkzeuge benutzt, wenn die Anfrage des Benutzers dies erfordert. Wenn der Benutzer nach dem Wetter fragt, MUSST du das 'get_weather'-Werkzeug benutzen."

    # 2. Eine minimale Tool-Definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Gibt das aktuelle Wetter für einen bestimmten Ort zurück.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Der Ort, für den das Wetter abgerufen werden soll, z.B. 'Berlin'.",
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    # 3. Eine klare Benutzeranfrage, die das Tool auslösen sollte
    user_message = "Wie ist das Wetter in Köln?"

    # 4. Die Nachrichtenliste
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    print("--- Starte OpenAI API-Aufruf ---")
    print(f"Modell: gpt-5.4-nano")
    print(f"System-Prompt: {system_prompt}")
    print(f"Benutzer-Nachricht: {user_message}")
    print("-" * 30)

    try:
        # 5. Der API-Aufruf
        response = await client.chat.completions.create(
            model="gpt-5.4-nano",  # Ein Modell, das Tool-Calling gut unterstützt
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message

        # 6. Ausgabe und Überprüfung
        print("--- API-Antwort erhalten ---")
        print(response_message)
        print("-" * 30)

        if response_message.tool_calls:
            print("✅ ERFOLG: Die KI hat einen Tool-Aufruf ausgelöst!")
            for tool_call in response_message.tool_calls:
                print(f"   - Tool-Name: {tool_call.function.name}")
                print(f"   - Argumente: {tool_call.function.arguments}")
        else:
            print("❌ FEHLER: Die KI hat KEINEN Tool-Aufruf ausgelöst.")
            print(f"   Antwort der KI: {response_message.content}")

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai_tool_call())
