from gary.discord_text import split_message
from gary.table import format_player_message


def test_short_message_is_untouched():
    assert split_message("The door creaks open.") == ["The door creaks open."]


def test_prefers_paragraph_breaks():
    text = "a" * 15 + "\n\n" + "b" * 15
    assert split_message(text, limit=20) == ["a" * 15, "b" * 15]


def test_falls_back_to_word_breaks():
    chunks = split_message("word " * 10, limit=12)
    assert all(len(c) <= 12 for c in chunks)
    assert " ".join(chunks).split() == ["word"] * 10


def test_hard_cuts_unbroken_text():
    assert split_message("x" * 25, limit=10) == ["x" * 10, "x" * 10, "x" * 5]


def test_player_tag():
    assert format_player_message("Tim", "I open the door") == "[Tim]: I open the door"
