from lean_backlog_intake_eval import extract_text, parse_json_from_text


def test_extract_text_accepts_list_content_blocks():
    response_body = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"text": "{" "\"status\"" ": " "\"PASS\"" "}"},
                    ]
                }
            }
        ]
    }

    assert extract_text(response_body) == '{"status": "PASS"}'


def test_parse_json_from_text_extracts_json_from_surrounding_text():
    text = 'Result follows:\n```json\n{"status": "PASS"}\n```\nUse this payload.'

    parsed = parse_json_from_text(text)

    assert parsed == {"status": "PASS"}
