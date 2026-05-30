"""Recorder classifier — maps raw pynput keys to capture-contract event types.

Skipped automatically if pynput isn't installed (e.g. on CI), since the
classifier's input types come from the pynput module itself.
"""
import pytest

pynput = pytest.importorskip("pynput")

from auditor.adapters.human_control_recorder import _classify


def test_backspace_classified_as_backspace():
    assert _classify(pynput.keyboard.Key.backspace) == "backspace"


def test_delete_classified_as_delete():
    assert _classify(pynput.keyboard.Key.delete) == "delete"


def test_printable_char_classified_as_keystroke():
    # KeyCode.from_char is pynput's documented way to fabricate a printable key.
    assert _classify(pynput.keyboard.KeyCode.from_char("a")) == "keystroke"


def test_modifier_key_classified_as_keystroke():
    # Shift/ctrl/etc. count as typed actions in the capture contract.
    assert _classify(pynput.keyboard.Key.shift) == "keystroke"
