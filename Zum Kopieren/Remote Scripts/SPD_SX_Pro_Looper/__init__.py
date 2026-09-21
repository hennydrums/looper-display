# SPD_SX_Pro_Looper - Ableton Live MIDI Remote Script
# Steuert die Looper-Devices der Spuren ueber ein Roland SPD-SX PRO.

from .SpdSxProLooper import SpdSxProLooper


def create_instance(c_instance):
    """Wird von Live beim Laden des Control Surface aufgerufen."""
    return SpdSxProLooper(c_instance)
