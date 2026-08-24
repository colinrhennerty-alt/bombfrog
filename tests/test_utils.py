from game.utils import clamp, env_flag


def test_clamp_within_range():
    assert clamp(5, 0, 10) == 5


def test_clamp_below_min():
    assert clamp(-5, 0, 10) == 0


def test_clamp_above_max():
    assert clamp(15, 0, 10) == 10


def test_env_flag_defaults_to_false_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_FLAG", raising=False)
    assert env_flag("SOME_FLAG") is False


def test_env_flag_respects_a_custom_default_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_FLAG", raising=False)
    assert env_flag("SOME_FLAG", default=True) is True


def test_env_flag_true_for_common_truthy_strings(monkeypatch):
    for value in ("1", "true", "True", "YES", "on", "  yes  "):
        monkeypatch.setenv("SOME_FLAG", value)
        assert env_flag("SOME_FLAG") is True, value


def test_env_flag_false_for_falsy_or_unrecognized_strings(monkeypatch):
    for value in ("0", "false", "no", "off", "", "garbage"):
        monkeypatch.setenv("SOME_FLAG", value)
        assert env_flag("SOME_FLAG") is False, value
