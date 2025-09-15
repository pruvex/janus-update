import time
from openai import OpenAI

# Client initialisieren (setzt voraus, dass OPENAI_API_KEY in der Umgebung gesetzt ist)
client = OpenAI()

def benchmark(model: str, prompt: str = "hallo"):
    """Sendet eine einfache Anfrage und misst die Latenz."""
    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    duration = time.time() - start
    answer = response.choices[0].message.content
    return duration, answer

if __name__ == "__main__":
    for m in ["gpt-4o-mini", "gpt-5-mini"]:
        duration, answer = benchmark(m)
        print(f"Modell: {m}")
        print(f"Antwortzeit: {duration:.2f} Sekunden")
        print(f"Antwort: {answer}")
        print("-" * 40)
