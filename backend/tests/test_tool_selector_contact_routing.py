from backend.services.chat.tool_selector import ToolSelector


def test_retrieve_candidates_adds_contact_extraction_for_residence_statement():
    candidates = ToolSelector.retrieve_candidates("Oliver Schwab wohnt in Köln-Stammheim")
    candidate_names = {candidate["tool_name"] for candidate in candidates}

    assert "contacts.extract_from_text" in candidate_names


def test_select_tools_includes_contact_extraction_for_contact_fact_statement():
    tools = ToolSelector.select_tools("Oliver Schwab wohnt in Köln-Stammheim")
    tool_names = {tool.get("function", {}).get("name") for tool in tools}

    assert (
        "extract_and_save_contact_from_text" in tool_names
        or "contacts.extract_from_text" in tool_names
        or "contacts_extract_from_text" in tool_names
    )


def test_retrieve_candidates_adds_contact_extraction_for_pet_follow_up_statement():
    candidates = ToolSelector.retrieve_candidates("und er hat einen hund")
    candidate_names = {candidate["tool_name"] for candidate in candidates}

    assert "contacts.extract_from_text" in candidate_names


def test_retrieve_candidates_adds_contact_extraction_for_pet_follow_up_with_besitzt():
    candidates = ToolSelector.retrieve_candidates("und er besitzt einen hund")
    candidate_names = {candidate["tool_name"] for candidate in candidates}

    assert "contacts.extract_from_text" in candidate_names


def test_retrieve_candidates_adds_contact_extraction_for_named_pet_attribute_statement():
    candidates = ToolSelector.retrieve_candidates("olis hund tasso ist ein podenco")
    candidate_names = {candidate["tool_name"] for candidate in candidates}

    assert "contacts.extract_from_text" in candidate_names
