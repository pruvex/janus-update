from pathlib import Path

from backend.tools import pdf_generator


def _pdf_execution_time_ms(result) -> float:
    meta = getattr(result, "metadata", None) or {}
    return meta.get("execution_time_ms")


def _mock_user_home(monkeypatch, tmp_path: Path) -> Path:
    fake_home = tmp_path / "fake_home"
    (fake_home / "Documents").mkdir(parents=True, exist_ok=True)
    (fake_home / "Desktop").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(pdf_generator.os.path, "expanduser", lambda _path: str(fake_home))
    return fake_home


def test_create_pdf_success(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    fake_home = _mock_user_home(monkeypatch, tmp_path)

    result = pdf_generator.create_pdf(
        content="# Test\n\nPDF Inhalt.",
        filename="success.pdf",
        location="Documents",
        dry_run=False,
    )

    assert result.status == "ok"
    assert result.error is None
    file_path = Path(result.data["file_path"])
    assert file_path.exists()
    assert file_path.parent == fake_home / "Documents"
    assert file_path.name == "success.pdf"
    assert isinstance(_pdf_execution_time_ms(result), float)


def test_create_pdf_dry_run(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    result = pdf_generator.create_pdf(
        content="# Vorschau\n\nNur Dry Run.",
        filename="preview.pdf",
        location="Documents",
        dry_run=True,
    )

    assert result.status == "dry_run_success"
    assert result.error is None
    assert str(result.data.get("preview_url", "")).startswith("data:application/pdf;base64,")
    assert not (tmp_path / "preview.pdf").exists()
    assert isinstance(_pdf_execution_time_ms(result), float)


def test_create_pdf_write_error(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    def _raise_permission_error(*_args, **_kwargs):
        raise PermissionError("blocked")

    monkeypatch.setattr(pdf_generator.PDF, "output", _raise_permission_error)

    result = pdf_generator.create_pdf(
        content="# Test\n\nWrite Error.",
        filename="denied.pdf",
        location="Documents",
        dry_run=False,
    )

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "WRITE_PERMISSION_DENIED"


def test_create_pdf_writes_output_when_fpdf_returns_string_without_creating_file(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    fake_home = _mock_user_home(monkeypatch, tmp_path)

    def _fake_output(self, path, *_args, **_kwargs):
        return "%PDF-1.4 fake pdf bytes"

    monkeypatch.setattr(pdf_generator.PDF, "output", _fake_output)

    result = pdf_generator.create_pdf(
        content="# Test\n\nPDF Inhalt.",
        filename="fallback_write.pdf",
        location="Documents",
        dry_run=False,
    )

    assert result.status == "ok"
    file_path = Path(result.data["file_path"])
    assert file_path == fake_home / "Documents" / "fallback_write.pdf"
    assert file_path.exists()
    assert file_path.read_bytes().startswith(b"%PDF-1.4")


def test_normalize_pdf_content_removes_agent_signature_line():
    normalized = pdf_generator._normalize_pdf_content(
        "# Spanien\n\n- Hauptstadt: Madrid\n\nErstellt vom SpainPDFCreator Spezial-Agenten.",
        "spanien.pdf",
    )

    assert "Spezial-Agenten" not in normalized
    assert "Hauptstadt: Madrid" in normalized


def test_normalize_pdf_content_converts_plain_fact_blob_to_markdown():
    normalized = pdf_generator._normalize_pdf_content(
        "Fakten: Hauptstadt von Norwegen ist Oslo. Einwohnerzahl: ca. 5,5 Millionen. Entfernung Berlin nach Oslo: 1347 km.",
        "norwegen.pdf",
    )

    assert normalized.startswith("# Norwegen")
    assert "## Fakten" in normalized
    assert "- Hauptstadt von Norwegen ist Oslo." in normalized
    assert "- Einwohnerzahl: ca. 5,5 Millionen." in normalized


def test_extract_first_image_path_and_clean_content_resolves_user_images(tmp_path, monkeypatch):
    images_root = tmp_path / "images"
    images_root.mkdir(parents=True, exist_ok=True)
    image_file = images_root / "affe.png"
    image_file.write_bytes(b"fake-image")

    monkeypatch.setattr(pdf_generator, "get_images_dir", lambda: str(images_root))

    image_path, cleaned = pdf_generator._extract_first_image_path_and_clean_content(
        "# Bericht\n\n![Affe](/user_images/affe.png)\n\nKurze Beschreibung."
    )

    assert image_path == str(image_file)
    assert "![Affe]" not in cleaned
    assert "Kurze Beschreibung." in cleaned


def test_create_pdf_resolves_explicit_user_images_image_path(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    images_root = tmp_path / "images"
    images_root.mkdir(parents=True, exist_ok=True)
    image_file = images_root / "affe.png"
    image_file.write_bytes(b"fake-image")

    monkeypatch.setattr(pdf_generator, "get_images_dir", lambda: str(images_root))

    called = {}

    def _fake_image(self, image_path, *args, **kwargs):
        called["image_path"] = image_path

    monkeypatch.setattr(pdf_generator.PDF, "image", _fake_image)
    monkeypatch.setattr(pdf_generator.PDF, "output", lambda self, *_args, **_kwargs: "%PDF-1.4 image")

    result = pdf_generator.create_pdf(
        content="# Bericht\n\nTextinhalt.",
        filename="with_image.pdf",
        location="Documents",
        image_path="/user_images/affe.png",
        dry_run=False,
    )

    assert result.status == "ok"
    assert called.get("image_path") == str(image_file)


def test_create_pdf_renders_multiple_inline_markdown_images_with_width(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    images_root = tmp_path / "images"
    images_root.mkdir(parents=True, exist_ok=True)
    image_one = images_root / "scene1.png"
    image_two = images_root / "scene2.png"
    image_one.write_bytes(b"fake-image-1")
    image_two.write_bytes(b"fake-image-2")

    monkeypatch.setattr(pdf_generator, "get_images_dir", lambda: str(images_root))

    calls = []

    def _fake_image(self, image_path, *args, **kwargs):
        calls.append((image_path, kwargs.get("w")))

    monkeypatch.setattr(pdf_generator.PDF, "image", _fake_image)
    monkeypatch.setattr(pdf_generator.PDF, "output", lambda self, *_args, **_kwargs: "%PDF-1.4 inline")

    result = pdf_generator.create_pdf(
        content=(
            "# Der kleine Hase\n\n"
            "Erste Szene.\n\n"
            "![Szene 1](/user_images/scene1.png)\n\n"
            "Zweite Szene.\n\n"
            "![Szene 2](/user_images/scene2.png)"
        ),
        filename="der_kleine_hase.pdf",
        location="Documents",
        image_width=79,
        dry_run=False,
    )

    assert result.status == "ok"
    assert [call[0] for call in calls] == [str(image_one), str(image_two)]
    assert all(call[1] == 79 for call in calls)


def test_resolve_layout_profile_auto_prefers_bilderbuch_for_kids_story():
    profile = pdf_generator._resolve_layout_profile(
        layout_profile="auto",
        source_prompt="Schreibe eine Kindergeschichte als Bilderbuch mit Illustrationen.",
        content="# Der kleine Hase\n\nEine kurze Geschichte für Kinder.",
    )
    assert profile == "bilderbuch"


def test_create_pdf_passes_selected_layout_and_body_font_size(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    captured = {}

    def _capture_add_markdown(self, markdown_text, font_size, image_width=0, layout_profile="bericht"):
        captured["font_size"] = font_size
        captured["layout_profile"] = layout_profile

    monkeypatch.setattr(pdf_generator.PDF, "add_markdown_text", _capture_add_markdown)
    monkeypatch.setattr(pdf_generator.PDF, "output", lambda self, *_args, **_kwargs: "%PDF-1.4 layout")

    result = pdf_generator.create_pdf(
        content="# Titel\n\nText.",
        filename="layout_auto.pdf",
        location="Documents",
        layout_profile="auto",
        source_prompt="Bitte als Bilderbuch für Kinder setzen.",
        dry_run=False,
    )

    assert result.status == "ok"
    assert captured["layout_profile"] == "bilderbuch"
    assert captured["font_size"] == pdf_generator._LAYOUT_PROFILES["bilderbuch"].base_font_size


def test_bilderbuch_layout_uses_title_page_and_chapter_breaks(monkeypatch):
    pdf = pdf_generator.PDF()
    pdf.add_font = lambda *args, **kwargs: None
    pdf.set_font = lambda *args, **kwargs: None
    calls = []

    monkeypatch.setattr(pdf, "multi_cell", lambda *args, **kwargs: calls.append(("multi_cell", args, kwargs)))
    monkeypatch.setattr(pdf, "ln", lambda *args, **kwargs: calls.append(("ln", args, kwargs)))
    monkeypatch.setattr(pdf, "cell", lambda *args, **kwargs: calls.append(("cell", args, kwargs)))
    monkeypatch.setattr(pdf, "set_y", lambda *args, **kwargs: calls.append(("set_y", args, kwargs)))
    y_values = iter([20, 60])

    def _fake_get_y():
        try:
            return next(y_values)
        except StopIteration:
            return 60

    monkeypatch.setattr(pdf, "get_y", _fake_get_y)
    monkeypatch.setattr(pdf, "add_page", lambda *args, **kwargs: calls.append(("add_page", args, kwargs)))

    pdf.add_markdown_text(
        "# Der kleine Hase\n\n## Kapitel 1\nText 1\n\n## Kapitel 2\nText 2",
        font_size=14,
        layout_profile="bilderbuch",
    )

    page_break_calls = [entry for entry in calls if entry[0] == "add_page"]
    title_cells = [entry for entry in calls if entry[0] == "multi_cell" and len(entry[1]) >= 3 and entry[1][2] == "Ein Bilderbuch"]
    centered_heading_calls = [entry for entry in calls if entry[0] == "multi_cell" and len(entry[1]) >= 5 and entry[1][4] == "C"]

    assert len(page_break_calls) >= 1
    assert title_cells
    assert centered_heading_calls


def test_rebalance_storybook_block_moves_more_text_above_when_height_is_tight():
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    block = pdf_generator.StoryChapterBlock(
        chapter_title="Kapitel 2",
        text_above="Am späten Vormittag entdeckten Pippel und Stachel eine bunte Karte im Laub.",
        image_paths=["fake.png"],
        text_below=(
            "Die Karte zeigte den Weg zu einem geheimen Garten voller schimmernder Blumen. "
            "Unterwegs trafen sie einen müden Vogel, der nicht weiterfliegen konnte. "
            "Die beiden halfen dem Vogel und suchten einen sicheren Platz, bis er sich ausruhen konnte."
        ),
    )

    original_above_sentence_count = len(pdf_generator._split_storybook_sentences(block.text_above))
    rebalanced = pdf_generator._rebalance_storybook_block_for_height(
        block,
        style,
        font_size=18,
        image_width=120,
        available_height=160,
    )

    assert len(pdf_generator._split_storybook_sentences(rebalanced.text_above)) >= original_above_sentence_count
    assert rebalanced.chapter_title == block.chapter_title
    assert rebalanced.image_paths == block.image_paths


def test_build_storybook_layout_plan_splits_long_below_text_into_multiple_pages(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(pdf_generator, "_estimate_image_height", lambda *_args, **_kwargs: 110)

    chapters = [
        pdf_generator.StoryChapterBlock(
            chapter_title="Kapitel 1",
            text_above="Oben steht ein kurzer Einstieg.",
            image_paths=["fake.png"],
            text_below=(
                "Der erste lange Satz beschreibt ausführlich den Weg durch die sonnige Wiese und braucht deutlich Platz. "
                "Der zweite lange Satz erzählt ebenfalls detailliert von den Blumen, dem Wind und den Farben am Wegesrand. "
                "Der dritte lange Satz erklärt, wie die Freunde weitergingen und dabei neue kleine Hinweise entdeckten. "
                "Der vierte lange Satz rundet die Szene ab und sorgt dafür, dass eine zweite Fortsetzungsseite nötig wird."
            ),
        )
    ]

    plan = pdf_generator._build_storybook_layout_plan(
        title="Der kleine Hase",
        chapters=chapters,
        style=style,
        font_size=18,
        page_width=160,
        page_height=120,
    )

    chapter_plans = plan["chapters"]
    assert len(chapter_plans) == 1
    assert len(chapter_plans[0]) >= 2
    assert chapter_plans[0][0].title_on_page is True
    assert chapter_plans[0][1].title_on_page is False
    assert chapter_plans[0][0].image_path == "fake.png"
    assert chapter_plans[0][1].image_path is None


def test_select_storybook_image_width_shrinks_tall_image_for_better_balance(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(pdf_generator, "_estimate_image_height", lambda _path, width: width * 1.4)

    selected_width = pdf_generator._select_storybook_image_width(
        "fake.png",
        requested_width=160,
        style=style,
        page_height=180,
        reserved_text_height=55,
    )

    assert selected_width is not None
    assert selected_width < 160
    assert selected_width >= 60


def test_classify_storybook_scene_detects_hero_and_calm_scenes():
    hero_block = pdf_generator.StoryChapterBlock(
        chapter_title="Das geheime Leuchten",
        text_above="Plötzlich erschien ein funkelnder Regenbogen über dem Wald.",
        image_paths=["fake.png"],
        text_below="Alle staunten über das Wunder.",
    )
    calm_block = pdf_generator.StoryChapterBlock(
        chapter_title="Am Abend",
        text_above="Leise kuschelten sich beide Freunde ins warme Gras.",
        image_paths=["fake.png"],
        text_below="Sanft flüsterte der Wind durch die Blätter.",
    )

    assert pdf_generator._classify_storybook_scene(hero_block) == "hero"
    assert pdf_generator._classify_storybook_scene(calm_block) == "calm"


def test_determine_storybook_page_style_assigns_hero_and_soft_continuation():
    assert pdf_generator._determine_storybook_page_style("hero", True, True, False) == "hero"
    assert pdf_generator._determine_storybook_page_style("calm", False, False, True) == "continuation-soft"
    assert pdf_generator._determine_storybook_page_style("adventure", True, True, False) == "chapter-opening"


def test_build_storybook_page_plan_marks_hero_opening_and_continuation(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(pdf_generator, "_estimate_image_height", lambda _path, width: max(60, width * 0.65))

    block = pdf_generator.StoryChapterBlock(
        chapter_title="Der Regenbogenpfad",
        text_above="Plötzlich öffnete sich ein geheimes Tor aus Licht.",
        image_paths=["fake.png"],
        text_below=(
            "Die Freunde staunten über das funkelnde Wunder am Himmel. "
            "Behutsam setzten sie einen Schritt nach dem anderen auf den schimmernden Pfad. "
            "Dabei leuchteten Sterne wie kleine Laternen um sie herum. "
            "Ganz hinten wartete ein stilles Schloss aus goldenem Nebel."
        ),
    )

    plans = pdf_generator._build_storybook_page_plan_for_block(
        block,
        style,
        font_size=18,
        page_width=160,
        page_height=140,
    )

    assert plans[0].scene_class == "hero"
    assert plans[0].page_style == "hero"
    if len(plans) > 1:
        assert plans[1].page_style == "continuation"


def test_build_storybook_page_plan_rebalances_text_from_continuation_back_to_first_page(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(pdf_generator, "_estimate_image_height", lambda _path, width: max(40, width * 0.75))

    block = pdf_generator.StoryChapterBlock(
        chapter_title="Kapitel 1",
        text_above="Kurzer Auftakt.",
        image_paths=["fake.png"],
        text_below=(
            "Der erste Satz beschreibt ruhig die Lichtung und die Farben der Blumen. "
            "Der zweite Satz erzählt ausführlich vom Picknickkorb und den vielen Beeren darin. "
            "Der dritte Satz schildert, wie beide Freunde lachend Beeren miteinander teilen. "
            "Der vierte Satz beschreibt, wie sie sich dabei noch enger zusammenkuscheln. "
            "Der fünfte Satz rundet die Szene sanft ab und verlängert die Fortsetzung."
        ),
    )

    plans = pdf_generator._build_storybook_page_plan_for_block(
        block,
        style,
        font_size=18,
        page_width=160,
        page_height=150,
    )

    assert len(plans) >= 1
    first_sentences = pdf_generator._split_storybook_sentences(plans[0].text_below)
    assert len(first_sentences) >= 1
    if len(plans) > 1:
        second_sentences = pdf_generator._split_storybook_sentences(plans[1].text_below)
        assert len(second_sentences) >= 2


def test_compute_storybook_vertical_offset_prefers_gentle_centering():
    image_offset = pdf_generator._compute_storybook_vertical_offset(plan_height=110, page_height=180, has_image=True)
    text_offset = pdf_generator._compute_storybook_vertical_offset(plan_height=90, page_height=180, has_image=False)

    assert image_offset > 0
    assert text_offset > image_offset
    assert text_offset <= 26


def test_rebalance_storybook_continuation_chain_merges_one_sentence_tail_page(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(
        pdf_generator,
        "_estimate_wrapped_text_height",
        lambda text, _style, _chars: 12 * max(1, len(pdf_generator._split_storybook_sentences(text))),
    )

    plans = [
        pdf_generator.StorybookPagePlan(
            chapter_title="Kapitel 2",
            text_above="Ein kurzer Einstieg.",
            image_path="fake.png",
            text_below="Ein ordentlicher Abschlusssatz auf der Bildseite.",
            title_on_page=True,
            image_width=120,
        ),
        pdf_generator.StorybookPagePlan(
            chapter_title="Kapitel 2",
            text_above="",
            image_path=None,
            text_below="Der erste Fortsetzungssatz. Der zweite Fortsetzungssatz.",
            title_on_page=False,
            image_width=None,
        ),
        pdf_generator.StorybookPagePlan(
            chapter_title="Kapitel 2",
            text_above="",
            image_path=None,
            text_below="Der letzte Satz sollte nicht allein stehen.",
            title_on_page=False,
            image_width=None,
        ),
    ]

    rebalanced = pdf_generator._rebalance_storybook_continuation_chain(plans, style, font_size=18, page_height=90)

    assert len(rebalanced) == 2
    assert "Der letzte Satz sollte nicht allein stehen." in rebalanced[1].text_below


def test_rebalance_storybook_plans_merges_short_first_continuation_back_to_image_page(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(pdf_generator, "_estimate_image_height", lambda _path, width: width * 0.45)
    monkeypatch.setattr(
        pdf_generator,
        "_estimate_wrapped_text_height",
        lambda text, _style, _chars: 10 * max(1, len(pdf_generator._split_storybook_sentences(text))),
    )

    first_plan = pdf_generator.StorybookPagePlan(
        chapter_title="Kapitel 2",
        text_above="Kurzer Einstieg.",
        image_path="fake.png",
        text_below="Ein Satz auf der Bildseite.",
        title_on_page=True,
        image_width=120,
        scene_class="standard",
        page_style="chapter-opening",
    )
    second_plan = pdf_generator.StorybookPagePlan(
        chapter_title="Kapitel 2",
        text_above="",
        image_path=None,
        text_below="Ein kurzer Nachsatz bleibt sonst allein auf der Folgeseite.",
        title_on_page=False,
        image_width=None,
        scene_class="standard",
        page_style="continuation-soft",
    )

    rebalanced = pdf_generator._rebalance_storybook_plans([first_plan, second_plan], style, page_height=120)

    assert len(rebalanced) == 1
    assert "Ein kurzer Nachsatz bleibt sonst allein auf der Folgeseite." in rebalanced[0].text_below


def test_build_storybook_page_plan_avoids_tiny_continuation_page_after_image(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(pdf_generator, "_estimate_image_height", lambda _path, width: 74)
    monkeypatch.setattr(
        pdf_generator,
        "_estimate_wrapped_text_height",
        lambda text, _style, _chars: 10 * max(1, len(text.splitlines()) + max(1, len(text) // 95)),
    )

    block = pdf_generator.StoryChapterBlock(
        chapter_title="Kapitel 1",
        text_above=(
            "Es war ein sonniger Frühlingstag, an dem das Häschen fröhlich durch das Gras hoppelte. "
            "Es roch die bunten Blumen und hörte das Zwitschern der Vögel."
        ),
        image_paths=["fake.png"],
        text_below=(
            "Plötzlich entdeckte es einen Igel, der sich hinter einem Pilz versteckte und neugierig lugte. "
            "Das Häschen und der Igel begrüßten sich mit einem vorsichtigen Schnuppern und lernten, dass Neugier Freundschaft beginnen kann. "
            "Sie beschlossen, gemeinsam die Wiese zu erkunden."
        ),
    )

    plans = pdf_generator._build_storybook_page_plan_for_block(
        block,
        style,
        font_size=18,
        page_width=160,
        page_height=150,
    )

    assert len(plans) >= 1
    if len(plans) > 1:
        continuation_height = pdf_generator._estimate_storybook_page_plan_height(plans[1], style, 18)
        assert continuation_height >= 40


def test_rebalance_storybook_plans_merges_single_sentence_tail_from_image_page(monkeypatch):
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    monkeypatch.setattr(pdf_generator, "_estimate_image_height", lambda _path, width: width * 0.7)
    monkeypatch.setattr(
        pdf_generator,
        "_estimate_wrapped_text_height",
        lambda text, _style, _chars: 9 * max(1, len(pdf_generator._split_storybook_sentences(text))),
    )

    first_plan = pdf_generator.StorybookPagePlan(
        chapter_title="Kapitel 3",
        text_above="Am Abend des dritten Tages laden Mia und Iggi ihre Freunde zu einem kleinen Fest ein.",
        image_path="fake.png",
        text_below=(
            "Alle erzählen sich Geschichten, lachen, singen Lieder und genießen gemeinsam die Beeren und Nüsse. "
            "Die Freunde merken, wie schön es ist, zusammen zu lachen und zu teilen. "
            "Mia und Iggi umarmen sich glücklich und wissen, dass echte Freundschaft im Herzen beginnt. "
            "Am Ende des Festes schauen sie zufrieden zu den Sternen und flüstern:"
        ),
        title_on_page=True,
        image_width=120,
        scene_class="calm",
        page_style="chapter-opening",
    )
    second_plan = pdf_generator.StorybookPagePlan(
        chapter_title="Kapitel 3",
        text_above="",
        image_path=None,
        text_below="Wir bleiben Freunde für immer.",
        title_on_page=False,
        image_width=None,
        scene_class="calm",
        page_style="continuation-soft",
    )

    rebalanced = pdf_generator._rebalance_storybook_plans([first_plan, second_plan], style, page_height=150)

    assert len(rebalanced) == 1
    assert "Wir bleiben Freunde für immer." in rebalanced[0].text_below


def test_render_storybook_page_plan_uses_hero_heading_scale_and_continuation_body_size(monkeypatch):
    pdf = pdf_generator.PDF()
    calls = []

    monkeypatch.setattr(pdf, "set_y", lambda value: calls.append(("set_y", value)))
    monkeypatch.setattr(pdf, "get_y", lambda: 25)
    monkeypatch.setattr(pdf, "set_text_color", lambda *args, **kwargs: None)
    monkeypatch.setattr(pdf, "multi_cell", lambda *args, **kwargs: calls.append(("multi_cell", args, kwargs)))
    monkeypatch.setattr(pdf, "ln", lambda *args, **kwargs: calls.append(("ln", args, kwargs)))
    monkeypatch.setattr(pdf, "image", lambda *args, **kwargs: calls.append(("image", args, kwargs)))
    monkeypatch.setattr(pdf, "set_font", lambda family, style_name, size: calls.append(("set_font", family, style_name, size)))
    monkeypatch.setattr(pdf_generator.os.path, "exists", lambda _path: True)
    pdf.w = 210
    pdf.l_margin = 25

    hero_plan = pdf_generator.StorybookPagePlan(
        chapter_title="Das Wunder",
        text_above="Plötzlich wurde alles hell.",
        image_path="fake.png",
        text_below="Alle sahen staunend nach oben.",
        title_on_page=True,
        image_width=120,
        vertical_offset=8,
        scene_class="hero",
        page_style="hero",
    )
    continuation_plan = pdf_generator.StorybookPagePlan(
        chapter_title="Das Wunder",
        text_above="",
        image_path=None,
        text_below="Dann gingen sie langsam weiter.",
        title_on_page=False,
        image_width=None,
        vertical_offset=0,
        scene_class="calm",
        page_style="continuation-soft",
    )

    pdf._render_storybook_page_plan(hero_plan, pdf_generator._LAYOUT_PROFILES["bilderbuch"], font_size=18)
    pdf._render_storybook_page_plan(continuation_plan, pdf_generator._LAYOUT_PROFILES["bilderbuch"], font_size=18)

    font_calls = [entry for entry in calls if entry[0] == "set_font"]
    assert any(entry[2] == "B" and entry[3] > 32 for entry in font_calls)
    assert any(entry[2] == "" and entry[3] < 18 for entry in font_calls)


def test_render_storybook_markdown_uses_planned_pages(monkeypatch):
    pdf = pdf_generator.PDF()
    pdf.set_font = lambda *args, **kwargs: None
    pdf.set_text_color = lambda *args, **kwargs: None
    pdf.w = 210
    pdf.h = 297
    pdf.l_margin = 25
    pdf.t_margin = 25
    pdf.b_margin = 25
    pdf.page_break_trigger = 272

    calls = []

    monkeypatch.setattr(pdf, "multi_cell", lambda *args, **kwargs: calls.append(("multi_cell", args, kwargs)))
    monkeypatch.setattr(pdf, "ln", lambda *args, **kwargs: calls.append(("ln", args, kwargs)))
    monkeypatch.setattr(pdf, "cell", lambda *args, **kwargs: calls.append(("cell", args, kwargs)))
    monkeypatch.setattr(pdf, "set_y", lambda *args, **kwargs: calls.append(("set_y", args, kwargs)))
    monkeypatch.setattr(pdf, "get_y", lambda: 25)
    monkeypatch.setattr(pdf, "add_page", lambda *args, **kwargs: calls.append(("add_page", args, kwargs)))
    monkeypatch.setattr(pdf, "image", lambda *args, **kwargs: calls.append(("image", args, kwargs)))
    monkeypatch.setattr(pdf_generator.os.path, "exists", lambda _path: True)

    planned_pages = [
        [
            pdf_generator.StorybookPagePlan(
                chapter_title="Kapitel 1",
                text_above="Oben 1",
                image_path="fake.png",
                text_below="Unten 1",
                title_on_page=True,
                image_width=120,
                vertical_offset=10,
            ),
            pdf_generator.StorybookPagePlan(
                chapter_title="Kapitel 1",
                text_above="",
                image_path=None,
                text_below="Fortsetzung",
                title_on_page=False,
                image_width=None,
                vertical_offset=0,
            ),
        ]
    ]

    monkeypatch.setattr(
        pdf_generator,
        "_build_storybook_layout_plan",
        lambda *args, **kwargs: {"title": "Der kleine Hase", "chapters": planned_pages},
    )

    pdf._render_storybook_markdown(
        "# Der kleine Hase\n\n## Kapitel 1\nText",
        pdf_generator._LAYOUT_PROFILES["bilderbuch"],
        font_size=18,
    )

    add_page_calls = [entry for entry in calls if entry[0] == "add_page"]
    image_calls = [entry for entry in calls if entry[0] == "image"]
    text_calls = [entry for entry in calls if entry[0] == "multi_cell"]

    assert len(add_page_calls) >= 2
    assert image_calls
    assert any(len(entry[1]) >= 3 and entry[1][2] == "Fortsetzung" for entry in text_calls)


def test_storybook_planned_pages_do_not_repeat_heading_on_continuation(monkeypatch):
    pdf = pdf_generator.PDF()
    pdf.set_font = lambda *args, **kwargs: None
    pdf.set_text_color = lambda *args, **kwargs: None
    pdf.w = 210
    pdf.h = 297
    pdf.l_margin = 25
    pdf.t_margin = 25
    pdf.b_margin = 25
    pdf.page_break_trigger = 220

    calls = []

    monkeypatch.setattr(pdf, "get_y", lambda: 25)
    monkeypatch.setattr(pdf, "set_y", lambda value: calls.append(("set_y", value)))
    monkeypatch.setattr(pdf, "ln", lambda amount=0: calls.append(("ln", amount)))
    monkeypatch.setattr(pdf, "multi_cell", lambda _w, _h, txt, *_args, **_kwargs: calls.append(("multi_cell", txt)))
    monkeypatch.setattr(pdf, "image", lambda image_path, *args, **kwargs: calls.append(("image", image_path, kwargs.get("w"))))
    monkeypatch.setattr(pdf, "add_page", lambda *args, **kwargs: calls.append(("add_page", None)))
    monkeypatch.setattr(pdf_generator.os.path, "exists", lambda _path: True)

    block = pdf_generator.StoryChapterBlock(
        chapter_title="Kapitel 2",
        text_above=(
            "Am späten Vormittag entdeckten Pippel und Stachel eine bunte Karte im Laub. "
            "Die Karte zeigte den Weg zu einem geheimen Garten voller schimmernder Blumen."
        ),
        image_paths=["fake.png"],
        text_below=(
            "Unterwegs trafen sie einen müden Vogel, der nicht weiterfliegen konnte. "
            "Die beiden halfen dem Vogel und suchten einen sicheren Platz, bis er sich ausruhen konnte."
        ),
    )

    chapter_pages = pdf_generator._build_storybook_page_plan_for_block(
        block,
        pdf_generator._LAYOUT_PROFILES["bilderbuch"],
        font_size=18,
        page_width=160,
        page_height=120,
    )

    for page_index, plan in enumerate(chapter_pages):
        if page_index > 0:
            pdf.add_page()
        pdf._render_storybook_page_plan(plan, pdf_generator._LAYOUT_PROFILES["bilderbuch"], font_size=18)

    chapter_titles = [entry for entry in calls if entry[0] == "multi_cell" and entry[1] == "Kapitel 2"]
    assert len(chapter_titles) == 1


def test_storybook_first_chapter_does_not_force_blank_page_after_title(monkeypatch):
    pdf = pdf_generator.PDF()
    pdf.set_font = lambda *args, **kwargs: None
    pdf.set_text_color = lambda *args, **kwargs: None
    pdf.page_break_trigger = 260
    pdf.w = 210
    pdf.h = 297
    pdf.l_margin = 25
    pdf.t_margin = 25
    pdf.b_margin = 25

    calls = []
    current_y = {"value": 25}

    def _fake_get_y():
        return current_y["value"]

    def _fake_add_page(*_args, **_kwargs):
        current_y["value"] = 25
        calls.append(("add_page", None))

    def _fake_multi_cell(_w, h, txt, *_args, **_kwargs):
        current_y["value"] += h
        calls.append(("multi_cell", txt))

    monkeypatch.setattr(pdf, "get_y", _fake_get_y)
    monkeypatch.setattr(pdf, "add_page", _fake_add_page)
    monkeypatch.setattr(pdf, "multi_cell", _fake_multi_cell)
    monkeypatch.setattr(pdf, "ln", lambda amount=0: calls.append(("ln", amount)))
    monkeypatch.setattr(pdf, "set_y", lambda value: calls.append(("set_y", value)))

    pdf._render_storybook_title_page("Der kleine Hase", pdf_generator._LAYOUT_PROFILES["bilderbuch"], 18)
    plan = pdf_generator.StorybookPagePlan(
        chapter_title="Kapitel 1",
        text_above="Ein erster Abschnitt.",
        image_path=None,
        text_below="Noch etwas Text.",
        title_on_page=True,
        image_width=None,
        vertical_offset=0,
    )
    pdf._render_storybook_page_plan(plan, pdf_generator._LAYOUT_PROFILES["bilderbuch"], font_size=18)

    add_page_calls = [entry for entry in calls if entry[0] == "add_page"]
    assert len(add_page_calls) == 1


def test_split_storybook_text_to_fit_height_avoids_single_sentence_remainder():
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    text = (
        "Der erste Satz ist bewusst etwas länger, damit er realistisch Zeilenhöhe verbraucht. "
        "Der zweite Satz ist ebenfalls deutlich länger formuliert und braucht ebenfalls merklich Platz. "
        "Der dritte Satz ist noch einmal ausführlich beschrieben, damit die Höhenmessung sauber greift. "
        "Der vierte Satz bleibt als potentieller Rest übrig und soll nicht allein stehen."
    )
    chars_per_line = pdf_generator._get_storybook_chars_per_line(style)
    height_for_three = pdf_generator._estimate_wrapped_text_height(
        (
            "Der erste Satz ist bewusst etwas länger, damit er realistisch Zeilenhöhe verbraucht. "
            "Der zweite Satz ist ebenfalls deutlich länger formuliert und braucht ebenfalls merklich Platz. "
            "Der dritte Satz ist noch einmal ausführlich beschrieben, damit die Höhenmessung sauber greift."
        ),
        style,
        chars_per_line,
    )

    fitting, overflow = pdf_generator._split_storybook_text_to_fit_height(
        text,
        style,
        available_height=height_for_three,
    )

    assert fitting == (
        "Der erste Satz ist bewusst etwas länger, damit er realistisch Zeilenhöhe verbraucht. "
        "Der zweite Satz ist ebenfalls deutlich länger formuliert und braucht ebenfalls merklich Platz."
    )
    assert overflow == (
        "Der dritte Satz ist noch einmal ausführlich beschrieben, damit die Höhenmessung sauber greift. "
        "Der vierte Satz bleibt als potentieller Rest übrig und soll nicht allein stehen."
    )


def test_storybook_chars_per_line_targets_book_like_line_length():
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]

    assert pdf_generator._get_storybook_chars_per_line(style) == 68


def test_has_too_short_last_line_detects_short_tail_in_storybook():
    style = pdf_generator._LAYOUT_PROFILES["bilderbuch"]
    chars_per_line = pdf_generator._get_storybook_chars_per_line(style)
    repeated_words = " ".join(["Wort"] * 14)
    text = f"{repeated_words} mini"

    assert pdf_generator._has_too_short_last_line(text, chars_per_line) is True


def test_create_pdf_denies_forbidden_absolute_windows_path(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    result = pdf_generator.create_pdf(
        content="# Test\n\nHack.",
        filename="hack.pdf",
        location="C:\\Windows",
        dry_run=False,
    )

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "WRITE_PERMISSION_DENIED"


def test_create_pdf_markdown_error(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    def _raise_markdown_error(_content):
        raise pdf_generator.MarkdownSyntaxError("bad markdown")

    monkeypatch.setattr(pdf_generator, "_validate_markdown_syntax", _raise_markdown_error)

    result = pdf_generator.create_pdf(
        content="# Broken [",
        filename="broken.pdf",
        location="Documents",
        dry_run=False,
    )

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "MARKDOWN_PARSE_ERROR"


def test_create_pdf_denies_path_traversal_outside_storage_root(tmp_path, monkeypatch):
    monkeypatch.setenv("JANUS_STORAGE_ROOT", str(tmp_path))
    _mock_user_home(monkeypatch, tmp_path)

    result = pdf_generator.create_pdf(
        content="# Test\n\nTraversal.",
        filename="blocked.pdf",
        location="..\\..\\Desktop",
        dry_run=False,
    )

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "WRITE_PERMISSION_DENIED"
