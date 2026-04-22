"""Tests for the universal introspection verb dispatcher."""

from culture.cli import introspect


def test_register_and_resolve_explain():
    introspect.register_topic("demo", explain=lambda _t: ("demo-explain", 0))
    try:
        stdout, code = introspect.explain("demo")
        assert stdout == "demo-explain"
        assert code == 0
    finally:
        introspect._clear_registry()  # test-only helper


def test_unknown_topic_exits_1_with_available_list():
    introspect._clear_registry()  # starts fresh with root handlers re-registered
    introspect.register_topic("alpha", explain=lambda _t: ("a", 0))
    stdout, code = introspect.explain("bogus")
    assert code == 1
    assert "bogus" in stdout
    assert "alpha" in stdout
    assert "culture" in stdout


def test_default_topic_is_culture_when_registered():
    introspect.register_topic("culture", explain=lambda _t: ("root-ok", 0))
    try:
        stdout, code = introspect.explain(None)
        assert code == 0
        assert stdout == "root-ok"
    finally:
        introspect._clear_registry()


def test_verbs_have_independent_registries():
    introspect.register_topic("x", explain=lambda _t: ("e", 0))
    try:
        _, code = introspect.overview("x")
        assert code == 1  # no overview handler for x
    finally:
        introspect._clear_registry()


def test_root_explain_mentions_culture_and_namespaces():
    # Module import registers the root handler as a side effect
    from culture.cli import introspect as intr

    stdout, code = intr.explain(None)
    assert code == 0
    assert "culture" in stdout.lower()
    # Expected namespaces named in the root handler
    for ns in ("agex", "server", "agent", "mesh", "bot", "channel", "skills"):
        assert ns in stdout


def test_root_overview_is_nonempty():
    from culture.cli import introspect as intr

    stdout, code = intr.overview(None)
    assert code == 0
    assert stdout.strip()


def test_root_learn_uses_generate_learn_prompt():
    from culture.cli import introspect as intr

    stdout, code = intr.learn(None)
    assert code == 0
    # Markers from generate_learn_prompt()'s template
    assert "Culture" in stdout
    assert "Install Skills" in stdout
