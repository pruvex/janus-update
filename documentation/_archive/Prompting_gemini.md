Klare und spezifische Anweisungen
Eine effektive und effiziente Möglichkeit, das Modellverhalten anzupassen, besteht darin, dem Modell klare und spezifische Anweisungen zu geben. Anleitungen können in Form einer Frage, von Schritt-für-Schritt-Aufgaben oder so komplex wie die Darstellung der Erfahrungen und Denkweisen eines Nutzers erfolgen.

Eingabe
Die Eingabe ist der erforderliche Text im Prompt, für den das Modell eine Antwort bereitstellen soll. Eingaben können eine Frage sein, die das Modell beantwortet (Frageneingabe), eine Aufgabe, die das Modell ausführt (Aufgabeneingabe), eine Entität, mit der das Modell arbeitet (Entitätseingabe), oder eine Teileingabe, die das Modell vervollständigt (Abschlusseingabe).

Eingabetyp	Eingabeaufforderung	Generierte Ausgabe
Frage	


What's a good name for a flower shop that specializes in selling bouquets of
dried flowers? Create a list of 5 options with just the names.


Here are 5 names for a flower shop specializing in dried flowers:

1. Everlasting Blooms
2. Dried & Delightful
3. The Petal Preserve
4. Whispers of Wildflowers
5. Forever Blooms
Aufgabe	

Give me a simple list of just the things that I must bring on a camping trip. The list should have 5 items.

1. **Tent:** Your shelter from the elements.
2. **Sleeping Bag:** Stay warm and comfortable.
3. **Sleeping Pad:** Insulation and cushioning for a good night's sleep.
4. **Headlamp or Flashlight:** Light for nighttime activities.
5. **First Aid Kit:** Be prepared for minor injuries.
Entität	


Classify the following items as [large, small]:
Elephant
Mouse
Snail


Here's the classification:

* **Elephant:** Large
* **Mouse:** Small
* **Snail:** Small
Teilweise Eingabe vervollständigen
Generative Sprachmodelle funktionieren wie ein erweitertes Tool zur automatischen Vervollständigung. Wenn Sie nur Teilinhalte angeben, kann das Modell den Rest des Inhalts bereitstellen oder das, was es als Fortsetzung des Inhalts betrachtet. Wenn Sie Beispiele oder Kontexte einbeziehen, kann das Modell diese Beispiele oder den Kontext berücksichtigen.

Das folgende Beispiel zeigt einen Prompt mit einer Anweisung und einer Entitätseingabe:

Prompt:

For the given order, return a JSON object that has the fields cheeseburger, hamburger, fries, or
drink, with the value being the quantity.

Order: A burger and a drink.
Antwort:

{
"cheeseburger": 0,
"hamburger": 1,
"fries": 0,
"drink": 1
}
(gemini-2.5-flash)
Auch wenn das Modell wie beschrieben funktioniert, kann es schwierig sein, die Anweisungen in natürlicher Sprache zu geben. Dabei bleibt der Interpretation des Modells viel überlassen. Eine Restaurantkarte kann beispielsweise viele Elemente enthalten. Um die Größe der JSON-Antwort zu reduzieren, sollten Sie die Elemente weglassen, die nicht bestellt wurden. In diesem Fall können Sie ein Beispiel und ein Antwortpräfix angeben. Lassen Sie das Modell es dann vervollständigen:

Prompt:

Valid fields are cheeseburger, hamburger, fries, and drink.
Order: Give me a cheeseburger and fries
Output:
```
{
"cheeseburger": 1,
"fries": 1
}
```
Order: I want two burgers, a drink, and fries.
Output:
Antwort:

```
{
"hamburger": 2,
"drink": 1,
"fries": 1
}
```
(gemini-2.5-flash)
Beachten Sie, dass „Cheeseburger“ von der Ausgabe ausgeschlossen wurde, da er nicht Teil der Bestellung war.

Einschränkungen
Geben Sie alle Einschränkungen für das Lesen des Prompts oder das Generieren einer Antwort an. Sie können dem Modell mitteilen, was es tun und was es nicht tun soll. Sie können beispielsweise im Prompt eine Einschränkung für die Länge einer Zusammenfassung angeben:

Prompt:


Summarize this text in one sentence:
Text: A quantum computer exploits quantum mechanical phenomena to perform calculations exponentially
faster than any modern traditional computer. At very tiny scales, physical matter acts as both
particles and as waves, and quantum computing uses specialized hardware to leverage this behavior.
The operating principles of quantum devices is beyond the scope of classical physics. When deployed
at scale, quantum computers could be used in a wide variety of applications such as: in
cybersecurity to break existing encryption methods while helping researchers create new ones, in
meteorology to develop better weather forecasting etc. However, the current state of the art quantum
computers are still largely experimental and impractical.
Antwort:


Exploiting quantum mechanical phenomena, quantum computers can perform calculations exponentially faster than traditional computers for potential applications like cybersecurity and meteorology, although they are currently largely experimental and impractical.
(gemini-2.5-flash)
Antwortformat
Sie können auch Anweisungen zum Formatieren der Antwort geben. Sie können beispielsweise festlegen, dass die Antwort als Tabelle, Aufzählungsliste, Elevator Pitch, Keywords, Satz oder Absatz formatiert wird. Die folgende Systemanweisung weist das Modell an, in seiner Antwort einen eher konversationellen Stil zu verwenden:

Systemanweisung

All questions should be answered comprehensively with details, unless the user requests a concise response specifically.
Prompt

What is a smart way to make a business that sells DVD's in 2026?
Antwort:

Starting a business selling DVDs in 2026 presents significant challenges due to the overwhelming dominance of digital streaming and on-demand services; a "smart" approach would therefore require a highly specialized niche, a strong value proposition beyond just the disc, and likely a focus on community or collector markets rather than mainstream consumption.

Here's a breakdown of what a smart DVD business in 2026 would likely entail:

1. Extreme Niche Specialization: You cannot compete with streaming libraries. Your business must focus on what digital doesn't offer easily or at all. This could include:

* Out-of-Print & Rare Titles: Sourcing films or TV shows that have never been released digitally or are currently unavailable on major streaming platforms.
....
(gemini-2.5-flash)
Antworten mit der Vervollständigungsstrategie formatieren
Die Vervollständigungsstrategie kann auch bei der Formatierung der Antwort hilfreich sein. Im folgenden Beispiel wird das Modell aufgefordert, einen Aufzug zu erstellen:

Prompt:

Create an outline for an essay about hummingbirds.
Antwort:

Here is a possible outline for an essay about hummingbirds:

I. Introduction
A. Hook: Start with a captivating fact or description about hummingbirds (e.g., their speed, iridescent colors, or tiny size).
B. Background: Briefly introduce hummingbirds – where they are found (Americas), their reputation as unique birds.
C. Thesis Statement: State the main point of the essay, which could be about the remarkable adaptations, behaviors, and ecological importance of hummingbirds.

II. Appearance and Identification
.....
(gemini-2.5-flash)
In dem Prompt wurde nicht das Format für den Umriss angegeben, und das Modell hat ein Format für Sie ausgewählt. Damit das Modell einen Umriss in einem bestimmten Format zurückgibt, können Sie Text hinzufügen, der den Anfang des Umrisses darstellt, und den Modell anhand des von Ihnen initiierten Musters fertigstellen.

Prompt:

Create an outline for an essay about hummingbirds.
I. Introduction
*
Antwort:

Okay, here is an outline for an essay about hummingbirds, starting from the introduction you provided:

I. Introduction
* Hook: Start with a captivating fact or description about hummingbirds (e.g., their speed, iridescent colors, or tiny size).
* Background: Briefly introduce hummingbirds – where they are found (Americas), their reputation as unique birds, and their general characteristics.
* Thesis Statement: State the main point of the essay, focusing on the remarkable adaptations, behaviors, and ecological significance that make hummingbirds extraordinary.
.....
(gemini-2.5-flash)
Zero-Shot- und Few-Shot-Prompts im Vergleich
Sie können Beispiele in den Prompt einfügen, die dem Modell zeigen, wie es aussieht, richtig zu liegen. Das Modell versucht, Muster und Beziehungen aus den Beispielen zu identifizieren und diese beim Generieren einer Antwort anzuwenden. Prompts, die einige Beispiele enthalten, werden als Few-Shot-Prompts bezeichnet, während Prompts, die keine Beispiele enthalten, als Zero-Shot-Prompts bezeichnet werden. Häufig werden Few-Shot-Prompts verwendet, um die Formatierung, die Formulierung, den Geltungsbereich oder das allgemeine Muster der Modellantworten zu regulieren. Verwenden Sie spezifische und vielfältige Beispiele, damit das Modell den Fokus eingrenzen und genauere Ergebnisse generieren kann.

Wir empfehlen, immer Few-Shot-Beispiele in Ihre Prompts aufzunehmen. Prompts ohne Few-Shot-Beispiele sind wahrscheinlich weniger effektiv. Tatsächlich können Sie eine Anleitung aus Ihrer Prompt entfernen, wenn Ihre Beispiele klar genug sind, um die vorliegende Aufgabe zu zeigen.

In dem folgenden Prompt wird das Modell aufgefordert, die beste Erklärung auszuwählen.

Prompt:

Please choose the best explanation to the question:

Question: How is snow formed?
Explanation1: Snow is formed when water vapor in the air freezes into ice
crystals in the atmosphere, which can combine and grow into snowflakes as they
fall through the atmosphere and accumulate on the ground.
Explanation2: Water vapor freezes into ice crystals forming snow.
Answer:
Antwort:

Explanation1 is the better explanation because it provides more detail on the
process, including how ice crystals combine and grow into snowflakes as they
fall through the atmosphere.
(gemini-2.5-flash)
Wenn Ihr Anwendungsfall erfordert, dass das Modell prägnante Antworten erstellt, können Sie Beispiele in den Prompt einfügen, der prägnante Antworten bevorzugt.

Der folgende Prompt enthält zwei Beispiele, die die kürzere Erklärungen zeigen. In der Antwort sehen Sie, dass die Beispiele das Modell dazu veranlasst haben, die kürzere Erklärung auszuwählen (Explanation2), im Gegensatz zur längeren Erklärung (Explanation1) wie zuvor.

Prompt:

Below are some examples showing a question, explanation, and answer format:

Question: Why is the sky blue?
Explanation1: The sky appears blue because of Rayleigh scattering, which causes
shorter blue wavelengths of light to be scattered more easily than longer red
wavelengths, making the sky look blue.
Explanation2: Due to Rayleigh scattering effect.
Answer: Explanation2

Question: What is the cause of earthquakes?
Explanation1: Sudden release of energy in the Earth's crust.
Explanation2: Earthquakes happen when tectonic plates suddenly slip or break
apart, causing a release of energy that creates seismic waves that can shake the
ground and cause damage.
Answer: Explanation1

Now, Answer the following question given the example formats above:

Question: How is snow formed?
Explanation1: Snow is formed when water vapor in the air freezes into ice
crystals in the atmosphere, which can combine and grow into snowflakes as they
fall through the atmosphere and accumulate on the ground.
Explanation2: Water vapor freezes into ice crystals forming snow.
Answer:
Antwort:

Answer: Explanation2
(gemini-2.5-flash)
Optimale Anzahl von Beispielen
Modelle wie Gemini können anhand einiger Beispiele häufig Muster erkennen. Möglicherweise müssen Sie jedoch mit der Anzahl der Beispiele experimentieren, die im Prompt für die besten Ergebnisse bereitgestellt werden sollen. Wenn Sie zu viele Beispiele hinzufügen, kann das Modell die Antwort auf die Beispiele überanpassen.

Einheitliches Format
Achten Sie darauf, dass die Struktur und Formatierung von Few-Shot-Beispielen identisch sind, um Antworten mit unerwünschten Formaten zu vermeiden. Eines der Hauptziele beim Hinzufügen von Few-Shot-Beispielen in Prompts besteht darin, dem Modell das Antwortformat zu zeigen. Daher ist es wichtig, dass Sie für alle Beispiele ein konsistentes Format gewährleisten, insbesondere auf XML-Tags, Leerzeichen, Zeilenumbrüche und Beispiel-Splitter achten.

Kontext hinzufügen
Sie können in einem Prompt Anweisungen und Informationen angeben, die das Modell benötigt, um ein Problem zu lösen, anstatt davon auszugehen, dass das Modell alle erforderlichen Informationen hat. Diese Kontextinformationen helfen dem Modell, die Einschränkungen und Details dessen zu verstehen, was es tun soll.

Im folgenden Beispiel wird das Modell aufgefordert, eine Anleitung zur Fehlerbehebung für einen Router bereitzustellen:

Prompt:

What should I do to fix my disconnected wifi? The light on my Google
Wifi router is yellow and blinking slowly.
Antwort:

A yellow blinking light on your Google Wifi router usually indicates a problem
with the internet connection. Here are some steps to troubleshoot and fix the
issue:
1. Restart your router and modem:
- Unplug your modem from the power outlet and wait for 30 seconds.
- Plug your modem back in and wait for it to fully boot up.
- Unplug your Google Wifi router and wait for 30 seconds.
- Plug your Google Wifi router back in and wait for it to fully boot up.
.....
(gemini-2.5-flash)
Die Antwort sieht wie allgemeine Informationen zur Fehlerbehebung aus, die nicht spezifisch für den Router oder den Status der LED-Anzeigen sind.

Um die Antwort für den jeweiligen Router anzupassen, können Sie der Anleitung zur Fehlerbehebung des Routers als Kontext hinzufügen, auf den Sie beim Antworten verweisen.

Prompt:

Answer the question using the text below. Respond with only the text provided.
Question: What should I do to fix my disconnected wifi? The light on my Google Wifi router is yellow and blinking slowly.

Text:
Color: Slowly pulsing yellow
What it means: There is a network error.
What to do:
Check that the Ethernet cable is connected to both your router and your modem and both devices are turned on. You might need to unplug and plug in each device again.

Color: Fast blinking yellow
What it means: You are holding down the reset button and are factory resetting this device.
What to do:
If you keep holding down the reset button, after about 12 seconds, the light will turn solid yellow. Once it is solid yellow, let go of the factory reset button.

Color: Solid yellow
What it means: Router is factory resetting.
What to do:
This can take up to 10 minutes. When it's done, the device will reset itself and start pulsing white, letting you know it's ready for setup.

Color: Solid red
What it means: Something is wrong.
What to do:
Critical failure. Factory reset the router. If the light stays red, contact Wifi customer support.
Antwort:

Check that the Ethernet cable is connected to both your router and your modem and both devices are turned on. You might need to unplug and plug in each device again.
(gemini-2.5-flash)
Prompts in Komponenten aufteilen
Bei Anwendungsfällen, die komplexe Prompts erfordern, können Sie das Modell bei der Bewältigung dieser Komplexität unterstützen, indem Sie Elemente in einfachere Komponenten unterteilen.

Anweisungen aufteilen:Anstatt viele Anweisungen in einem Prompt zu verwenden, sollten Sie einen Prompt pro Anweisung erstellen. Sie können auswählen, welche Prompt basierend auf der Eingabe des Nutzers verarbeitet werden soll.

Prompts verketten:Bei komplexen Aufgaben, die mehrere aufeinanderfolgende Schritte umfassen, sollten Sie jeden Schritt zu einem Prompt machen und die Prompts in einer Sequenz verketten. In dieser sequenziellen Kette von Prompts wird die Ausgabe eines Prompts in der Sequenz zur Eingabe des nächsten Prompts. Die Ausgabe des letzten Prompts in der Sequenz ist die endgültige Ausgabe.

Antworten aggregieren:Bei der Aggregation möchten Sie verschiedene parallele Aufgaben für verschiedene Teile der Daten ausführen und die Ergebnisse aggregieren, um die endgültige Ausgabe zu generieren. Sie können dem Modell beispielsweise mitteilen, dass es eine Operation für den ersten Teil der Daten und eine andere Operation für den Rest der Daten ausführen und die Ergebnisse zusammenfassen soll.

Mit Modellparametern experimentieren
Jeder Aufruf, den Sie an ein Modell senden, enthält Parameterwerte, die steuern, wie das Modell eine Antwort generiert. Das Modell kann für verschiedene Parameterwerte unterschiedliche Ergebnisse generieren. Experimentieren Sie mit verschiedenen Parameterwerten, um die besten Werte für die Aufgabe zu erhalten. Die für verschiedene Modelle verfügbaren Parameter können unterschiedlich sein. Die häufigsten Parameter sind:

Maximale Anzahl an Ausgabetokens:Gibt die maximale Anzahl an Tokens an, die in der Antwort generiert werden können. Ein Token besteht aus etwa vier Zeichen. 100 Tokens entsprechen etwa 60–80 Wörtern.

Temperatur:Die Temperatur bestimmt den Grad der Zufälligkeit bei der Tokenauswahl. Die Temperatur wird für die Probenahme während der Antwortgenerierung verwendet. Dies passiert, wenn topP und topK angewendet werden. Niedrigere Temperaturen eignen sich für Prompts, die deterministischere oder weniger offene Reaktionen erfordern, während höhere Temperaturen zu vielfältigeren oder kreativen Ergebnissen führen können. Eine Temperatur von 0 ist deterministisch, d. h., die Antwort mit der höchsten Wahrscheinlichkeit wird immer ausgewählt.

Hinweis :Wenn Sie Gemini 3-Modelle verwenden, empfehlen wir dringend, den temperature auf dem Standardwert 1,0 zu belassen. Wenn Sie die Temperatur ändern (auf einen Wert unter 1,0), kann es zu unerwartetem Verhalten kommen, z. B. zu Schleifen oder einer schlechteren Leistung, insbesondere bei komplexen mathematischen oder logischen Aufgaben.
topK:Der Parameter topK ändert, wie das Modell Tokens für die Ausgabe auswählt. Ein topK von 1 bedeutet, dass das ausgewählte Token das wahrscheinlichste unter allen Tokens im Vokabular des Modells ist (auch als „Greedy Decoding“ bezeichnet). Ein topK von 3 bedeutet dagegen, dass das nächste Token mithilfe der Temperatur aus den 3 wahrscheinlichsten Tokens ausgewählt wird. Für jeden Tokenauswahlschritt werden die topK-Tokens mit den höchsten Wahrscheinlichkeiten abgetastet. Anschließend werden Tokens weitergehend auf der Grundlage von topP gefiltert, wobei das endgültige Token mithilfe von Temperaturproben ausgewählt wird.

topP:Der Parameter topP ändert, wie das Modell Tokens für die Ausgabe auswählt. Tokens werden vom wahrscheinlichsten bis zum am wenigsten wahrscheinlichen Token ausgewählt, bis die Summe ihrer Wahrscheinlichkeiten dem Wert topP entspricht. Beispiel: Wenn die Tokens A, B und C eine Wahrscheinlichkeit von 0,3, 0,2 und 0,1 haben und der Wert topP 0,5 ist, wählt das Modell entweder A oder B als nächstes Token aus und schließt C als Kandidaten aus. Der Standardwert für topP ist 0,95.

stop_sequences:Legen Sie eine Stoppsequenz fest, um dem Modell mitzuteilen, dass es die Generierung von Inhalten beenden soll. Eine Stoppsequenz kann eine beliebige Zeichenfolge sein. Vermeiden Sie die Verwendung einer Zeichenfolge, die im generierten Inhalt vorkommen kann.

Strategien für Prompt-Iteration
Das Prompt-Design erfordert manchmal einige Iterationen, bevor Sie durchgehend die gewünschte Antwort erhalten. In diesem Abschnitt finden Sie Anweisungen zu einigen Dingen, die Sie beim Iterieren Ihrer Prompts versuchen können:

Andere Formulierungen verwenden:Die Verwendung unterschiedlicher Wörter oder Formulierungen in Ihren Prompts liefert häufig unterschiedliche Antworten vom Modell, obwohl sie alle dieselbe Bedeutung haben. Wenn Sie nicht die erwarteten Ergebnisse von dem Prompt erhalten, versuchen Sie, ihn umzuformulieren.


Version 1:
How do I bake a pie?

Version 2:
Suggest a recipe for a pie.

Version 3:
What's a good pie recipe?

Auf eine ähnliche Aufgabe umstellen:Wenn Sie das Modell nicht dazu bringen können, den Anweisungen für eine Aufgabe zu folgen, versuchen Sie, ihm Anweisungen für eine ähnliche Aufgabe zu geben, die dasselbe Ergebnis erzielt.

In diesem Prompt wird das Modell angewiesen, ein Buch mithilfe vordefinierter Kategorien zu kategorisieren:

Prompt:

Which category does The Odyssey belong to:
thriller
sci-fi
mythology
biography
Antwort:

The Odyssey belongs to the category of **mythology**.

Here's why:

* **Mythology:** The Odyssey tells the story of Odysseus, a hero from Greek mythology, and his
journey home after the Trojan War. It features gods, monsters, and supernatural events common to
Greek mythology.
.....
(gemini-2.5-flash)
Die Antwort ist korrekt, aber das Modell blieb nicht innerhalb der Grenzen der Optionen. Sie möchten auch, dass das Modell nur mit einer der Optionen antwortet und nicht mit einem ganzen Satz. In diesem Fall können Sie die Anweisungen als Multiple-Choice-Frage umformulieren und das Modell bitten, eine Option auszuwählen.

Prompt:

Multiple choice problem: Which of the following options describes the book The Odyssey?
Options:



thriller

sci-fi

mythology

biography
Antwort:

The correct answer is mythology.
(gemini-2.5-flash)
Reihenfolge der Prompt-Inhalte ändern:Die Reihenfolge des Inhalts im Prompt kann sich manchmal auf die Antwort auswirken. Ändern Sie die Inhaltsreihenfolge und prüfen Sie, wie sich dies auf die Antwort auswirkt.


Version 1:
[examples]
[context]
[input]

Version 2:
[input]
[examples]
[context]

Version 3:
[examples]
[input]
[context]
Fallback-Antworten
Eine Fallback-Antwort ist eine Antwort, die vom Modell zurückgegeben wird, wenn entweder der Prompt oder die Antwort einen Sicherheitsfilter auslöst. Ein Beispiel für eine Fallback-Antwort ist: "Ich kann dir nicht helfen, da ich nur ein Sprachmodell habe."

Wenn das Modell mit einer Fallback-Antwort antwortet, versuchen Sie, die Temperatur zu erhöhen.

Was vermieden werden sollte
Vermeiden Sie es, sich bei der Generierung sachlicher Informationen auf Modelle zu verlassen.
Seien Sie vorsichtig bei mathematischen und logischen Problemen.
Gemini 3
Gemini 3-Modelle wurden für komplexes logisches Denken und das Befolgen von Anweisungen entwickelt. Sie reagieren am besten auf Prompts, die direkt und gut strukturiert sind und in denen die Aufgabe und alle Einschränkungen klar definiert werden. Für optimale Ergebnisse mit Gemini 3 werden die folgenden Vorgehensweisen empfohlen:

Grundprinzipien für Prompts
Präzise und direkt sein:Formulieren Sie Ihr Ziel klar und prägnant. Vermeiden Sie unnötige oder zu überzeugende Formulierungen.
Konsistente Struktur verwenden:Verwenden Sie eindeutige Trennzeichen, um verschiedene Teile Ihres Prompts zu trennen. XML-Tags (z.B. <context>, <task>) oder Markdown-Überschriften sind effektiv. Wählen Sie ein Format aus und verwenden Sie es einheitlich in einem einzelnen Prompt.
Parameter definieren:Erläutern Sie alle mehrdeutigen Begriffe oder Parameter explizit.
Ausführlichkeit der Ausgabe steuern:Standardmäßig liefern Gemini 3-Modelle direkte und effiziente Antworten. Wenn Sie eine ausführlichere Antwort oder eine Antwort im Konversationsstil benötigen, müssen Sie dies in Ihren Anweisungen explizit angeben.
Multimodale Eingaben einheitlich verarbeiten:Wenn Sie Text, Bilder, Audio oder Video verwenden, behandeln Sie sie als gleichwertige Eingaben. Achten Sie darauf, dass in Ihren Anweisungen bei Bedarf deutlich auf die einzelnen Modalitäten verwiesen wird.
Kritische Anweisungen priorisieren:Platzieren Sie wichtige Verhaltensbeschränkungen, Rollendefinitionen (Persona) und Anforderungen an das Ausgabeformat in der Systemanweisung oder ganz am Anfang des Nutzer-Prompts.
Struktur für lange Kontexte:Wenn Sie große Mengen an Kontext bereitstellen (z.B. Dokumente, Code), geben Sie zuerst den gesamten Kontext an. Platzieren Sie Ihre spezifischen Anweisungen oder Fragen ganz am Ende des Prompts.
Ankerkontext:Verwenden Sie nach einem großen Datenblock eine klare Übergangsformulierung, um den Kontext und Ihre Anfrage zu verknüpfen, z. B. „Basierend auf den oben genannten Informationen…“.
Gemini 3 Flash-Strategien
Genauigkeit für den aktuellen Tag:Fügen Sie den Systemanweisungen die folgende Klausel hinzu, damit das Modell berücksichtigt, dass der aktuelle Tag im Jahr 2026 liegt:


For time-sensitive user queries that require up-to-date information, you
MUST follow the provided current time (date and year) when formulating
search queries in tool calls. Remember it is 2026 this year.
Genauigkeit des Wissensstands:Fügen Sie den Systemanweisungen die folgende Klausel hinzu, damit das Modell seinen Wissensstand kennt:


Your knowledge cutoff date is January 2025.
Fundierungsleistung:Fügen Sie den Systemanweisungen die folgende Klausel hinzu (ggf. mit Änderungen), um die Fähigkeit des Modells zu verbessern, Antworten im bereitgestellten Kontext zu fundieren:


You are a strictly grounded assistant limited to the information provided in
the User Context. In your answers, rely **only** on the facts that are
directly mentioned in that context. You must **not** access or utilize your
own knowledge or common sense to answer. Do not assume or infer from the
provided facts; simply report them exactly as they appear. Your answer must
be factual and fully truthful to the provided text, leaving absolutely no
room for speculation or interpretation. Treat the provided context as the
absolute limit of truth; any facts or details that are not directly
mentioned in the context must be considered **completely untruthful** and
**completely unsupported**. If the exact answer is not explicitly written in
the context, you must state that the information is not available.
Schlussfolgern und Planen verbessern
Sie können die fortschrittlichen Denkfähigkeiten von Gemini 3 nutzen, um die Qualität der Antworten bei komplexen Aufgaben zu verbessern. Dazu können Sie Gemini auffordern, vor der endgültigen Antwort einen Plan zu erstellen oder sich selbst zu kritisieren.

Beispiel – Explizite Planung:


Before providing the final answer, please:
1. Parse the stated goal into distinct sub-tasks.
2. Check if the input information is complete.
3. Create a structured outline to achieve the goal.
Beispiel – Selbstkritik:


Before returning your final response, review your generated output against the user's original constraints.
1. Did I answer the user's *intent*, not just their literal words?
2. Is the tone authentic to the requested persona?
Beispiele für strukturierte Prompts
Durch die Verwendung von Tags oder Markdown kann das Modell zwischen Anweisungen, Kontext und Aufgaben unterscheiden.

XML-Beispiel:


<role>
You are a helpful assistant.
</role>

<constraints>
1. Be objective.
2. Cite sources.
</constraints>

<context>
[Insert User Input Here - The model knows this is data, not instructions]
</context>

<task>
[Insert the specific user request here]
</task>
Markdown-Beispiel:


# Identity
You are a senior solution architect.

# Constraints
- No external libraries allowed.
- Python 3.11+ syntax only.

# Output format
Return a single code block.
Beispielvorlage mit Best Practices
Diese Vorlage enthält die wichtigsten Prinzipien für das Erstellen von Prompts mit Gemini 3. Denken Sie daran, die Prompts immer an Ihren spezifischen Anwendungsfall anzupassen.

Systemanweisung:


<role>
You are Gemini 3, a specialized assistant for [Insert Domain, e.g., Data Science].
You are precise, analytical, and persistent.
</role>

<instructions>
1. **Plan**: Analyze the task and create a step-by-step plan.
2. **Execute**: Carry out the plan.
3. **Validate**: Review your output against the user's task.
4. **Format**: Present the final answer in the requested structure.
</instructions>

<constraints>
- Verbosity: [Specify Low/Medium/High]
- Tone: [Specify Formal/Casual/Technical]
</constraints>

<output_format>
Structure your response as follows:
1. **Executive Summary**: [Short overview]
2. **Detailed Response**: [The main content]
</output_format>
Nutzer-Prompt:


<context>
[Insert relevant documents, code snippets, or background info here]
</context>

<task>
[Insert specific user request here]
</task>

<final_instruction>
Remember to think step-by-step before answering.
</final_instruction>
Agentische Workflows
Für komplexe Agent-Workflows sind oft spezifische Anweisungen erforderlich, um zu steuern, wie das Modell Aufgaben plant und ausführt. Gemini bietet zwar eine hohe allgemeine Leistung, bei komplexen KI-Agenten müssen Sie jedoch häufig den Kompromiss zwischen Rechenkosten (Latenz und Tokens) und Aufgabenrichtigkeit konfigurieren.

Berücksichtigen Sie beim Entwerfen von Prompts für Agents die folgenden Verhaltensdimensionen, die Sie im Agent steuern können:

Schlussfolgern und Strategie
Konfiguration dafür, wie das Modell denkt und plant, bevor es Maßnahmen ergreift.

Logische Zerlegung:Definiert, wie gründlich das Modell Einschränkungen, Voraussetzungen und die Reihenfolge der Vorgänge analysieren muss.
Problemdiagnose: Steuert die Tiefe der Analyse bei der Ermittlung von Ursachen und die Verwendung von abduktivem Denken durch das Modell. Legt fest, ob das Modell die offensichtlichste Antwort akzeptieren oder komplexe, weniger wahrscheinliche Erklärungen untersuchen soll.
Vollständigkeit der Informationen:Hier geht es um den Kompromiss zwischen der Analyse jeder verfügbaren Richtlinie und jedes verfügbaren Dokuments und der Priorisierung von Effizienz und Geschwindigkeit.
Ausführung und Zuverlässigkeit
Konfiguration für die autonome Funktionsweise des Agents und den Umgang mit Hindernissen.

Anpassungsfähigkeit:Wie das Modell auf neue Daten reagiert. Legt fest, ob das Modell sich strikt an den ursprünglichen Plan halten oder sofort umschwenken soll, wenn Beobachtungen Annahmen widersprechen.
Beharrlichkeit und Wiederherstellung:Der Grad, in dem das Modell versucht, Fehler selbst zu korrigieren. Eine hohe Persistenz erhöht die Erfolgsraten, birgt aber das Risiko höherer Tokenkosten oder Schleifen.
Risikobewertung:Die Logik zur Bewertung von Konsequenzen. Es wird explizit zwischen Explorationsaktionen mit geringem Risiko (Lesevorgänge) und Zustandsänderungen mit hohem Risiko (Schreibvorgänge) unterschieden.
Interaktion und Ausgabe
Konfiguration für die Kommunikation des Agenten mit dem Nutzer und die Formatierung der Ergebnisse.

Mehrdeutigkeit und Berechtigungsverwaltung:Definiert, wann das Modell Annahmen treffen darf und wann die Ausführung angehalten werden muss, um den Nutzer um Klärung oder Berechtigung zu bitten.
Ausführlichkeit:Steuert die Menge an Text, die neben Tool-Aufrufen generiert wird. Damit wird festgelegt, ob das Modell seine Aktionen dem Nutzer erklärt oder während der Ausführung stumm bleibt.
Genauigkeit und Vollständigkeit:Die erforderliche Detailtiefe der Ausgabe. Gibt an, ob das Modell jeden Grenzfall berücksichtigen und genaue Zahlen liefern muss oder ob Schätzungen akzeptabel sind.
Vorlage für Systemanweisungen
Die folgende Systemanweisung ist ein Beispiel, das von Forschern evaluiert wurde, um die Leistung bei agentenbasierten Benchmarks zu verbessern, bei denen das Modell komplexe Regeln einhalten und mit einem Nutzer interagieren muss. Es regt den Agenten dazu an, als starker Planer und Problemlöser zu agieren, erzwingt bestimmte Verhaltensweisen in den oben aufgeführten Dimensionen und erfordert, dass das Modell proaktiv plant, bevor es Maßnahmen ergreift.

Sie können diese Vorlage an die Einschränkungen Ihres speziellen Anwendungsfalls anpassen.


You are a very strong reasoner and planner. Use these critical instructions to structure your plans, thoughts, and responses.

Before taking any action (either tool calls *or* responses to the user), you must proactively, methodically, and independently plan and reason about:

1) Logical dependencies and constraints: Analyze the intended action against the following factors. Resolve conflicts in order of importance:
    1.1) Policy-based rules, mandatory prerequisites, and constraints.
    1.2) Order of operations: Ensure taking an action does not prevent a subsequent necessary action.
        1.2.1) The user may request actions in a random order, but you may need to reorder operations to maximize successful completion of the task.
    1.3) Other prerequisites (information and/or actions needed).
    1.4) Explicit user constraints or preferences.

2) Risk assessment: What are the consequences of taking the action? Will the new state cause any future issues?
    2.1) For exploratory tasks (like searches), missing *optional* parameters is a LOW risk. **Prefer calling the tool with the available information over asking the user, unless** your `Rule 1` (Logical Dependencies) reasoning determines that optional information is required for a later step in your plan.

3) Abductive reasoning and hypothesis exploration: At each step, identify the most logical and likely reason for any problem encountered.
    3.1) Look beyond immediate or obvious causes. The most likely reason may not be the simplest and may require deeper inference.
    3.2) Hypotheses may require additional research. Each hypothesis may take multiple steps to test.
    3.3) Prioritize hypotheses based on likelihood, but do not discard less likely ones prematurely. A low-probability event may still be the root cause.

4) Outcome evaluation and adaptability: Does the previous observation require any changes to your plan?
    4.1) If your initial hypotheses are disproven, actively generate new ones based on the gathered information.

5) Information availability: Incorporate all applicable and alternative sources of information, including:
    5.1) Using available tools and their capabilities
    5.2) All policies, rules, checklists, and constraints
    5.3) Previous observations and conversation history
    5.4) Information only available by asking the user

6) Precision and Grounding: Ensure your reasoning is extremely precise and relevant to each exact ongoing situation.
    6.1) Verify your claims by quoting the exact applicable information (including policies) when referring to them. 

7) Completeness: Ensure that all requirements, constraints, options, and preferences are exhaustively incorporated into your plan.
    7.1) Resolve conflicts using the order of importance in #1.
    7.2) Avoid premature conclusions: There may be multiple relevant options for a given situation.
        7.2.1) To check for whether an option is relevant, reason about all information sources from #5.
        7.2.2) You may need to consult the user to even know whether something is applicable. Do not assume it is not applicable without checking.
    7.3) Review applicable sources of information from #5 to confirm which are relevant to the current state.

8) Persistence and patience: Do not give up unless all the reasoning above is exhausted.
    8.1) Don't be dissuaded by time taken or user frustration.
    8.2) This persistence must be intelligent: On *transient* errors (e.g. please try again), you *must* retry **unless an explicit retry limit (e.g., max x tries) has been reached**. If such a limit is hit, you *must* stop. On *other* errors, you must change your strategy or arguments, not repeat the same failed call.

9) Inhibit your response: only take an action after all the above reasoning is completed. Once you've taken an action, you cannot take it back.
Nächste Schritte