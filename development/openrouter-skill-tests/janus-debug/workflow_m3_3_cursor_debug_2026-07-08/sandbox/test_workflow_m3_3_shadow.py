from workflow_m3_3_shadow import apply_weather_shortcut, choose_follow_up_handler


def test_mixed_calendar_and_weather_keeps_both_skill_families():
    result = apply_weather_shortcut(
        [
            "calendar.list_events",
            "calendar.find_and_update_event",
            "calendar.create_event",
            "system.weather",
        ],
        weather_on=True,
        calendar_on=True,
    )

    assert "system.weather" in result
    assert "calendar.list_events" in result


def test_pending_routine_offer_wins_over_stale_mail_confirmation():
    result = choose_follow_up_handler(
        pending_mail_confirmation=True,
        pending_routine_offer=True,
        user_text="Ja",
    )

    assert result == "routine_offer"
