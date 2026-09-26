# -*- coding: utf-8 -*-
"""
SPD_SX_Pro_Looper
=================

Ableton Live Remote Script, das die Looper-Devices des Sets ueber fuenf Pads
eines Roland SPD-SX PRO steuert. Ergaenzung zu "LooperDisplay" --
beide duerfen gleichzeitig laufen, sie arbeiten auf denselben Loopern.

Bedienung:

    linke Spalte oben    Clear  (ueber die IAC-Schleife, siehe unten)
    linke Spalte Mitte   Stop -- spielt den Loop zu Ende (STOP_AT_LOOP_END),
                         zweiter Druck: naechster Taktstrich
    linke Spalte unten   Start / Record / Overdub -- druckt ueber die
                         IAC-Schleife den Transportknopf des Loopers, damit
                         dessen eigene Quantisierung greift

    Mitte links          vorheriger Looper
    Mitte unten          naechster Looper

    Mitte oben           ALLE Looper starten -- sofort, siehe _start_all
    Mitte                ALLE Looper stoppen -- gemeinsam am Ende des
                         laengsten Loops, zweiter Druck: naechster Taktstrich

Die drei linken Pads wirken immer auf den GERADE GEWAEHLTEN Looper. Welcher
das ist, meldet das Script per OSC an AbleSet; dort blendet ein Canvas-Label
die passende Markierung ein.

Clear laeuft ueber einen Umweg: Der Button ist ueber die Live-API nicht
erreichbar, nur ueber Lives eigenes MIDI-Mapping -- und das ist statisch,
folgt der Durchschaltung also nicht. Deshalb sendet das Script pro Looper
einen eigenen CC in den IAC-Treiber, der in Live als Fernsteuerungs-Eingang
wieder ankommt und dort den gemappten Clear-Button ausloest.
"""

from __future__ import absolute_import, print_function, unicode_literals

import socket
import struct

import Live
from _Framework.ControlSurface import ControlSurface



DEBUG = False             # auf True setzen fuer Meldungen im Live-Log

# --- Pads: (MIDI-Kanal 0-basiert, Notennummer) ------------------------
# Am Geraet gemessen. Schickt dein Kit andere Notes, hier anpassen.
PAD_CLEAR = (0, 1)        # links oben    -- "Loop DELETE"
PAD_STOP = (0, 2)         # links Mitte   -- "Loop STOP"
PAD_CYCLE = (0, 3)        # links unten   -- "Loop GO", Start/Record/Overdub

PAD_ALL_START = (0, 4)    # Mitte oben    -- "START ALL Loops", sofort
PAD_ALL_STOP = (0, 5)     # Mitte Mitte   -- "STOP ALL Loops QUANT"
PAD_PREV = (0, 6)         # Mitte unten   -- "Looper -"
PAD_NEXT = (0, 68)        # rechts unten  -- "Looper +"
                          # Dieses Pad sendet ab Werk auf Kanal 12 und
                          # wurde am Geraet auf Kanal 1 umgestellt.

# Nicht vom Script ausgewertet:
#   rechts oben  (Note 62)  "START/STOP Ableton"
#   rechts Mitte (Note 65)  "LOOPER TOGGLE" -- Loop in der Arrangement-
#                           Ansicht, ueber AbleSet

ALL_PADS = (PAD_CLEAR, PAD_STOP, PAD_CYCLE, PAD_PREV, PAD_NEXT,
            PAD_ALL_START, PAD_ALL_STOP)

# --- Clear ueber die IAC-Schleife -------------------------------------
# "Clear" ist ueber die Live-API nicht erreichbar, nur ueber Lives eigenes
# MIDI-Mapping. Damit das trotzdem der Durchschaltung folgen kann, sendet
# das Script pro Looper einen eigenen CC an den IAC-Treiber. IAC ist eine
# Schleife: Was hinausgeht, kommt in Live als Fernsteuerungs-Eingang wieder
# an und loest dort den gemappten Clear-Button aus.
#
# Voraussetzung: In Live steht der AUSGANG dieser Bedienoberflaeche auf
# "IAC-Treiber Bus 1", und beim IAC-EINGANG ist "Remote" aktiviert.
CLEAR_ENABLED = True
CLEAR_CHANNEL = 0         # 0-basiert, entspricht MIDI-Kanal 1
CLEAR_CC_BASE = 48        # Looper 1 -> CC 48, Looper 2 -> CC 49, ...

# Bewusst dieselben Nachrichten wie die M-Tasten des nanoKONTROL2 (CC 48-55
# auf Kanal 1): Lives Zuweisungen haengen an der Nachricht, nicht am Port.
# Beide Geraete loesen damit dieselbe Zuweisung aus, und es genuegt EIN Satz
# von acht Clear-Zuweisungen fuer beide Wege.

# --- OSC an AbleSet ---------------------------------------------------
# AbleSet liest "Shared Variables": /shared/<name>. Im Canvas steht als Wert
# ${shared("<name>")}, eine Sichtbarkeitsbedingung vergleicht ihn mit der
# Nummer des Loopers.
OSC_ENABLED = True
OSC_HOST = '127.0.0.1'
OSC_PORT = 39042
# Dieselbe Nachricht geht zusaetzlich an diese Empfaenger. Eingetragen ist das
# Looper-Display (~/Music/Ableton/Looper-Display, server.js lauscht auf 11002).
OSC_EXTRA_TARGETS = [('127.0.0.1', 11002)]
OSC_VARIABLE = 'LooperSPD_SX'
OSC_AS_INT = True         # Als ZAHL senden. Die Canvas liest den Wert mit
                          # osc(":<Verbindung>/shared/LooperSPD_SX") und
                          # vergleicht strikt: === 3. osc() liefert das rohe
                          # OSC-Argument, also 3 bei einem Integer und "3"
                          # bei einem String -- ein String macht alle
                          # Vergleiche dauerhaft falsch.
                          # Achtung: Wer statt osc() die Funktion shared()
                          # benutzt, braucht das Gegenteil. Shared Variables
                          # legt AbleSet nur aus String-Argumenten an.

# --- Transportknopf ueber die IAC-Schleife -----------------------------
# Der State-Parameter laesst sich zwar setzen, umgeht dabei aber die
# Quantisierung des Loopers -- gemessen: die Maus wartet auf den Takt, ein
# geschriebener Parameterwert nicht. Deshalb geht auch das Weiterschalten
# ueber Lives MIDI-Mapping: Das Script sendet einen CC in den IAC-Treiber,
# Live drueckt daraufhin den echten Transportknopf, und der Looper
# quantisiert selbst.
#
# Dieselben Nachrichten wie die R-Tasten des nanoKONTROL2 (CC 64-71,
# Kanal 1), also genuegt EIN Satz von acht Zuweisungen fuer beide Geraete.
TRANSPORT_CHANNEL = 0     # 0-basiert, entspricht MIDI-Kanal 1
TRANSPORT_CC_BASE = 64    # Looper 1 -> CC 64, wie R1 am nanoKONTROL2
STOP_CC_BASE = 32         # Looper 1 -> CC 32, wie S1 am nanoKONTROL2

# --- Stop am Loop-Ende ------------------------------------------------
# Die Stop-Pads spielen den Loop zu Ende. Das Mitzaehlen der Takte macht das
# Script "LooperDisplay"; dieses Script schickt ihm nur den Wunsch per OSC:
# /looper/<n>/stop bzw. /looper/all/stop (alle gemeinsam am Ende des
# laengsten Loops). Ohne Live 12 (Live.LooperDevice) wie frueher ueber die
# IAC-Schleife, also am naechsten Taktstrich.
STOP_AT_LOOP_END = hasattr(Live, 'LooperDevice')
STOP_TARGET = ('127.0.0.1', 11005)   # EMPTY_PORT des LooperDisplay-Scripts

STATE_STOP = 0
STATE_RECORD = 1
STATE_PLAY = 2
STATE_OVERDUB = 3



def osc_message(address, value, as_int):
    """Minimale OSC-Nachricht mit genau einem Argument."""
    def pad(data):
        data += b'\x00'
        while len(data) % 4:
            data += b'\x00'
        return data

    out = pad(address.encode('utf-8'))
    if as_int:
        out += pad(b',i') + struct.pack('>i', int(value))
    else:
        out += pad(b',s') + pad(str(value).encode('utf-8'))
    return out


class LooperSlot(object):
    """Ein gefundenes Looper-Device samt seines State-Parameters."""

    def __init__(self, device, track):
        self.device = device
        self.track = track
        self.state_parameter = None
        for parameter in device.parameters:
            if parameter.name == 'State':
                self.state_parameter = parameter
                break

    @property
    def is_valid(self):
        try:
            return (self.device is not None
                    and self.state_parameter is not None
                    and self.device.canonical_parent is not None)
        except RuntimeError:
            return False

    def get_state(self):
        try:
            return int(round(self.state_parameter.value))
        except (RuntimeError, AttributeError):
            return STATE_STOP

    def set_state(self, value):
        try:
            self.state_parameter.value = float(value)
        except (RuntimeError, AttributeError):
            pass


class SpdSxProLooper(ControlSurface):

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self._loopers = []
        self._selected = 0
        self._rescan_scheduled = False
        self._socket = None

        if OSC_ENABLED:
            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception as error:
                self.log_message('OSC-Socket konnte nicht geoeffnet werden: %r'
                                 % (error,))

        with self.component_guard():
            song = self.song()
            song.add_tracks_listener(self._on_structure_changed)
            song.add_return_tracks_listener(self._on_structure_changed)
            self._rescan_loopers()

        self.log_message('SPD_SX_Pro_Looper geladen - %d Looper gefunden'
                         % len(self._loopers))
        # Beim Laden einmal senden, damit das Label nie leer steht.
        self.schedule_message(2, self._send_selection)

    # ------------------------------------------------------------------
    # MIDI-Map
    # ------------------------------------------------------------------
    def build_midi_map(self, midi_map_handle):
        ControlSurface.build_midi_map(self, midi_map_handle)
        script_handle = self._c_instance.handle()
        for channel, note in ALL_PADS:
            Live.MidiMap.forward_midi_note(script_handle, midi_map_handle,
                                           channel, note)
        if DEBUG:
            self.log_message('build_midi_map: forwarde Pads %s' % (ALL_PADS,))

    # ------------------------------------------------------------------
    # MIDI-Auswertung
    # ------------------------------------------------------------------
    def receive_midi(self, midi_bytes):
        if len(midi_bytes) != 3:
            return
        status, note, velocity = midi_bytes[0], midi_bytes[1], midi_bytes[2]
        if (status & 0xF0) != 0x90 or velocity == 0:
            return                      # Note Off ignorieren
        pad = (status & 0x0F, note)
        if DEBUG:
            self.log_message('Pad %s, Velocity %d' % (pad, velocity))

        if pad == PAD_PREV:
            self._change_selection(-1)
        elif pad == PAD_NEXT:
            self._change_selection(1)
        elif pad == PAD_CYCLE:
            self._on_cycle()
        elif pad == PAD_STOP:
            self._on_stop()
        elif pad == PAD_CLEAR:
            self._on_clear()
        elif pad == PAD_ALL_STOP:
            if STOP_AT_LOOP_END:
                self._send_stop_request('all')
            else:
                self._on_all(STOP_CC_BASE, 'Stop')
        elif pad == PAD_ALL_START:
            self._start_all()

    def _current_slot(self):
        if 0 <= self._selected < len(self._loopers):
            slot = self._loopers[self._selected]
            if slot.is_valid:
                return slot
        return None

    def _on_stop(self):
        """Mittleres linkes Pad: Stop-Knopf des gewaehlten Loopers druecken.

        Mit Live 12 stoppt er am Loop-Ende (siehe STOP_AT_LOOP_END), sonst
        wie beim Transportknopf ueber Lives Mapping, damit die Quantisierung
        des Loopers greift -- ein gesetzter State-Parameter stoppt sofort.
        """
        if STOP_AT_LOOP_END:
            if self._loopers:
                self._send_stop_request(str(self._selected + 1))
        else:
            self._send_looper_cc(STOP_CC_BASE, 'Stop')

    def _send_stop_request(self, which):
        """Stop-Wunsch an das LooperDisplay-Script: Looper-Nummer oder 'all'."""
        if self._socket is None:
            return
        try:
            data = osc_message('/looper/%s/stop' % which, 1, True)
            self._socket.sendto(data, STOP_TARGET)
        except Exception as error:
            self.log_message('Stop-Wunsch nicht gesendet: %r' % (error,))
            return
        if DEBUG:
            self.log_message('Stop-Wunsch: Looper %s' % which)

    def _start_all(self):
        """Mitte oben: alle Looper starten -- sofort, ueber den State-Parameter.

        Bewusst NICHT ueber den Transportknopf, obwohl das quantisiert waere:
        Der Knopf schaltet weiter, und bei einem LEEREN Looper bedeutet er
        Record. Das Script kann leer und gefuellt nicht unterscheiden -- die
        Live-API gibt den Loop-Inhalt nicht preis -- und wuerde deshalb auf
        der Buehne ungewollt Aufnahmen starten.

        Der State-Parameter ist hier der sichere Weg: Auf einem leeren Looper
        bleibt "Play" folgenlos. Der Preis ist, dass der Start nicht
        quantisiert ist.
        """
        count = 0
        for slot in self._loopers:
            if slot.is_valid and slot.get_state() != STATE_PLAY:
                slot.set_state(STATE_PLAY)
                count += 1
        self.show_message('Alle Looper gestartet (%d)' % count)
        if DEBUG:
            self.log_message('Sammelstart: %d Looper' % count)

    def _on_all(self, base, was):
        """Sammelbefehl: denselben CC fuer JEDEN Looper senden.

        Auch hier ueber Lives Mapping statt ueber den State-Parameter --
        damit stoppen alle Looper gemeinsam am naechsten Taktstrich, statt
        mitten im Takt abzureissen.
        """
        if not self._loopers:
            return
        sent = []
        for index in range(len(self._loopers)):
            cc = base + index
            if cc > 127:
                break
            self._send_midi((0xB0 | TRANSPORT_CHANNEL, cc, 127))
            sent.append(cc)
        if not sent:
            return
        # Loslassen gesammelt im naechsten Tick nachreichen.
        self.schedule_message(1, self._release_all, sent)
        self.show_message('%s: alle %d Looper' % (was, len(sent)))
        if DEBUG:
            self.log_message('%s fuer alle: CCs %s auf Kanal %d'
                             % (was, sent, TRANSPORT_CHANNEL + 1))

    def _release_all(self, ccs):
        for cc in ccs:
            self._send_midi((0xB0 | TRANSPORT_CHANNEL, cc, 0))

    def _send_looper_cc(self, base, was):
        """CC fuer den gewaehlten Looper in die IAC-Schleife schicken."""
        if not self._loopers:
            return
        cc = base + self._selected
        if cc > 127:
            self.log_message('%s: CC %d liegt ausserhalb des gueltigen '
                             'Bereichs' % (was, cc))
            return
        self._send_midi((0xB0 | TRANSPORT_CHANNEL, cc, 127))
        self.schedule_message(1, self._send_transport_release, cc)
        if DEBUG:
            self.log_message('%s: CC %d auf Kanal %d gesendet (Looper %d)'
                             % (was, cc, TRANSPORT_CHANNEL + 1,
                                self._selected + 1))

    def _on_cycle(self):
        """Unteres linkes Pad: Transportknopf des gewaehlten Loopers druecken.

        Laeuft ueber Lives MIDI-Mapping, nicht ueber den State-Parameter --
        nur so greift die Quantisierung des Loopers. Der Knopf schaltet dann
        von selbst weiter: Record -> Play -> Overdub -> Play -> ...
        """
        self._send_looper_cc(TRANSPORT_CC_BASE, 'Transport')

    def _send_transport_release(self, cc):
        self._send_midi((0xB0 | TRANSPORT_CHANNEL, cc, 0))

    def _on_clear(self):
        """Oberes Pad: CC fuer den gewaehlten Looper in die IAC-Schleife."""
        if not CLEAR_ENABLED or not self._loopers:
            return
        cc = CLEAR_CC_BASE + self._selected
        if cc > 127:
            self.log_message('Clear: CC %d liegt ausserhalb des gueltigen '
                             'Bereichs -- CLEAR_CC_BASE senken' % cc)
            return
        self._send_midi((0xB0 | CLEAR_CHANNEL, cc, 127))
        # Loslassen nachreichen, damit Live einen sauberen Tastendruck sieht.
        self.schedule_message(1, self._send_clear_release, cc)
        if DEBUG:
            self.log_message('Clear: CC %d auf Kanal %d gesendet (Looper %d)'
                             % (cc, CLEAR_CHANNEL + 1, self._selected + 1))

    def _send_clear_release(self, cc):
        self._send_midi((0xB0 | CLEAR_CHANNEL, cc, 0))

    # ------------------------------------------------------------------
    # Auswahl und Anzeige
    # ------------------------------------------------------------------
    def _change_selection(self, delta):
        if not self._loopers:
            return
        new = max(0, min(len(self._loopers) - 1, self._selected + delta))
        if new != self._selected:
            self._selected = new
            self._send_selection()
        self.show_message('SPD-SX: Looper %d von %d'
                          % (self._selected + 1, len(self._loopers)))

    def _send_selection(self):
        """Nummer des gewaehlten Loopers (1-basiert) an AbleSet schicken."""
        if not OSC_ENABLED or self._socket is None:
            return
        value = self._selected + 1 if self._loopers else 0
        try:
            data = osc_message('/shared/' + OSC_VARIABLE, value, OSC_AS_INT)
            self._socket.sendto(data, (OSC_HOST, OSC_PORT))
            for target in OSC_EXTRA_TARGETS:
                try:
                    self._socket.sendto(data, target)
                except Exception:
                    pass
            if DEBUG:
                self.log_message('OSC: /shared/%s = %s' % (OSC_VARIABLE, value))
        except Exception as error:
            self.log_message('OSC-Versand fehlgeschlagen: %r' % (error,))

    # ------------------------------------------------------------------
    # Looper suchen
    # ------------------------------------------------------------------
    def _rescan_loopers(self):
        previous_count = len(self._loopers)
        self._loopers = []
        song = self.song()
        tracks = list(song.tracks) + list(song.return_tracks) + [song.master_track]
        for track in tracks:
            self._collect_loopers(track.devices, track)
        for track in tracks:
            try:
                if not track.devices_has_listener(self._on_structure_changed):
                    track.add_devices_listener(self._on_structure_changed)
            except RuntimeError:
                pass
        self._selected = max(0, min(self._selected, len(self._loopers) - 1))
        if len(self._loopers) != previous_count:
            self._send_selection()

    def _collect_loopers(self, devices, track):
        for device in devices:
            try:
                class_name = device.class_name
            except RuntimeError:
                continue
            if class_name == 'Looper':
                slot = LooperSlot(device, track)
                if slot.state_parameter is not None:
                    self._loopers.append(slot)
            if getattr(device, 'can_have_chains', False):
                for chain in device.chains:
                    self._collect_loopers(chain.devices, track)
                if getattr(device, 'can_have_drum_pads', False):
                    for chain in device.return_chains:
                        self._collect_loopers(chain.devices, track)

    def _on_structure_changed(self):
        if not self._rescan_scheduled:
            self._rescan_scheduled = True
            self.schedule_message(1, self._deferred_rescan)

    def _deferred_rescan(self):
        self._rescan_scheduled = False
        self._rescan_loopers()

    # ------------------------------------------------------------------
    def disconnect(self):
        song = self.song()
        for track in list(song.tracks) + list(song.return_tracks) \
                + [song.master_track]:
            try:
                if track.devices_has_listener(self._on_structure_changed):
                    track.remove_devices_listener(self._on_structure_changed)
            except (RuntimeError, AttributeError):
                pass
        try:
            if song.tracks_has_listener(self._on_structure_changed):
                song.remove_tracks_listener(self._on_structure_changed)
            if song.return_tracks_has_listener(self._on_structure_changed):
                song.remove_return_tracks_listener(self._on_structure_changed)
        except (RuntimeError, AttributeError):
            pass
        if self._socket is not None:
            try:
                self._socket.close()
            except Exception:
                pass
        ControlSurface.disconnect(self)
