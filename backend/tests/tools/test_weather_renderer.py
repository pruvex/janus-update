from backend.renderers.implementations.weather_renderer import WeatherRenderer


def test_weather_renderer_prefers_structured_uniform_shape():
    renderer = WeatherRenderer()
    out = renderer.render(
        {
            "city": "Koeln",
            "date": "heute",
            "weather_description": "Bedeckt",
            "temp_max": 32.1,
            "temp_min": 18.5,
            "precipitation_probability": 0,
            "wind_speed_max": 7.9,
            "source": "open-meteo",
            "forecast": "Freier Alttext, der ignoriert werden soll.",
        }
    )
    assert "Das Wetter fuer Koeln (heute) im Ueberblick:" in out
    assert "* Zustand: Bedeckt" in out
    assert "* Temperaturen: Hoechstwerte bis zu 32.1 C, Tiefstwerte bei 18.5 C" in out
    assert "* Regen: Die Niederschlagswahrscheinlichkeit liegt bei 0 %" in out
    assert "* Wind: Leichte Brisen mit Boeen bis zu 7.9 km/h" in out
    assert "Quelle: Open-Meteo" in out


def test_weather_renderer_fallback_forecast_keeps_single_source_line():
    renderer = WeatherRenderer()
    out = renderer.render(
        {
            "city": "Koeln",
            "forecast": "Wetter fuer Koeln: sonnig.\nQuelle: wttr.in",
            "source": "wttr.in",
        }
    )
    assert "Wetter in Koeln:" in out
    assert out.count("Quelle:") == 1
