# LooperDisplay - Ableton Live MIDI Remote Script
# Liefert den Zustand aller Looper an das Looper-Display (Browser); ein
# KORG nanoKONTROL2 ist optional und wird nur bedient, wenn eins da ist.

from .LooperDisplay import LooperDisplay


def create_instance(c_instance):
    """Wird von Live beim Laden des Control Surface aufgerufen."""
    return LooperDisplay(c_instance)
