Arbeitsanweisung für den Coding Agent
Ziel: Integration des Langzeitgedächtnisses (LTM) in den Kontext-Retrieval-Prozess und Implementierung einer "Least Recently Used" (LRU) Logik.
Schritt 1: Das Gedächtnis durchsuchbar machen (LTM-Retrieval)
Wir müssen eine Funktion schaffen, die für die Vektorsuche sowohl das Kurzzeit- als auch das Langzeitgedächtnis als eine einzige durchsuchbare Quelle behandelt.
Anweisung 1: Modifiziere backend/memory_manager.py
Fügen Sie am Ende der Datei memory_manager.py eine neue Funktion namens get_all_searchable_memories hinzu. Diese Funktion kombiniert alle Einträge aus Memory (STM) und LongTermMemory (LTM).
code
Python
# In backend/memory_manager.py HINZUFÜGEN:

def get_all_searchable_memories(db: Session) -> List[any]:
    """
    Gibt eine kombinierte Liste aller Erinnerungen aus dem STM (Memory)
    und LTM (LongTermMemory) für eine umfassende Vektorsuche zurück.
    """
    stm_memories = db.query(database.Memory).all()
    ltm_memories = db.query(database.LongTermMemory).all()
    # Wir fügen ein temporäres Attribut hinzu, um die Quelle zu identifizieren.
    for mem in stm_memories:
        mem.source = 'stm'
    for mem in ltm_memories:
        mem.source = 'ltm'
    return stm_memories + ltm_memories
Schritt 2: LTM-Funde befördern und STM-Nutzung signalisieren (LTM-Promotion & STM-Touch)
Jetzt passen wir die zentrale Logik in main.py an. Wir nutzen unsere neue Funktion, um über das gesamte Gedächtnis zu suchen. Wenn wir einen Treffer im LTM haben, befördern wir ihn. Wenn wir Treffer im STM haben, aktualisieren wir deren Zeitstempel.
Anweisung 2: Modifiziere backend/main.py
Suchen Sie in der Funktion handle_chat_request nach dem Kommentar === GOLD STANDARD HYBRID CONTEXT BUILDER ===.
Finden Sie die Zeile:
all_past_facts = [fact for fact in memory_manager.get_all_facts(db) if fact.chat_id != request.chat_id]
Ersetzen Sie diese Zeile durch den folgenden Codeblock. Dieser Block sucht nun über das gesamte Gedächtnis (STM + LTM) und befördert LTM-Treffer sofort zurück ins STM.
code
Python
# In backend/main.py ERSETZEN:

    # 2. Assoziatives Langzeitgedächtnis: Finde die relevantesten "Ankerpunkte" in alten Chats (STM + LTM).
    all_searchable_past_memories = [
        mem for mem in memory_manager.get_all_searchable_memories(db)
        if mem.chat_id != request.chat_id
    ]
    similar_anchor_snippets = vector_service.find_similar_snippets(
        request.prompt, all_searchable_past_memories, top_k=3
    )

    # LTM-Promotion: Wenn Anker aus dem LTM stammen, befördere sie zurück ins STM.
    promoted_snippets = []
    for anchor in similar_anchor_snippets:
        if hasattr(anchor, 'source') and anchor.source == 'ltm':
            logger.info(f"Relevanter Fakt im LTM gefunden: '{anchor.snippet}'. Befördere zu STM.")
            promoted_memory = memory_manager.promote_ltm_to_stm(db, anchor)
            if promoted_memory:
                promoted_snippets.append(promoted_memory)
        else:
            # Es ist bereits im STM, füge es einfach zur Liste hinzu
            promoted_snippets.append(anchor)
    similar_anchor_snippets = promoted_snippets # Überschreibe die Liste mit den jetzt im STM befindlichen Objekten
Finden Sie die Zeile:
if anchor.chat_id not in processed_chat_ids:
Ersetzen Sie diese Zeile und die drei Zeilen danach durch den folgenden, leicht modifizierten Block. Die Änderung ist minimal, stellt aber sicher, dass wir mit den korrekten Objekten arbeiten.
code
Python
# In backend/main.py ERSETZEN:

    for anchor in similar_anchor_snippets:
        # Stellen sicher, dass wir mit einem STM-Objekt arbeiten (nach der Promotion)
        if anchor.chat_id not in processed_chat_ids:
            logger.info(f"Relevanter alter Chat gefunden (ID: {anchor.chat_id}). Lade vollständigen Kontext dieses Chats.")
            full_chat_context = crud.get_memory_by_chat_id(db, anchor.chat_id)
            contextual_cluster_facts.extend(full_chat_context)
            processed_chat_ids.add(anchor.chat_id)
Suchen Sie die Zeile:
logger.info(f"[DEBUG] FINAL HYBRID Memory Context Generated (length: {len(memory_context)}): {memory_context[:1500]}")
Fügen Sie direkt nach dieser Zeile den folgenden Codeblock ein. Dieser "berührt" alle STM-Erinnerungen, die wir für den Kontext verwendet haben, um sie vor der Archivierung zu schützen.
code
Python
# In backend/main.py HINZUFÜGEN:

    # 5. "Touch" all used STM memories to update their last_accessed_at timestamp
    for mem in final_snippets:
        # Wir berühren nur Einträge, die aus dem STM stammen (LTM-Einträge haben keine ID im STM)
        if hasattr(mem, 'id') and isinstance(mem, database.Memory):
             memory_manager.touch_memory_snippet(db, mem.id)
    logger.info(f"Touched {len(final_snippets)} memory snippets to update their relevance.")