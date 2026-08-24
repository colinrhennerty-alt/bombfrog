from game.simulation.debug_log import log


def test_log_prints_with_a_debug_prefix(capsys):
    log("something happened")
    captured = capsys.readouterr()
    assert captured.out == "[debug] something happened\n"
