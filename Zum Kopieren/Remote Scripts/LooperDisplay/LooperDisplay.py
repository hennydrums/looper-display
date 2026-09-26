# -*- coding: utf-8 -*-
"""
LooperDisplay
=============

Ableton Live Remote Script: liefert den Zustand aller Looper des Sets an
das Looper-Display (Browser). Ein KORG nanoKONTROL2 ist optional -- ist
eins angeschlossen, lassen sich die Looper zusaetzlich darueber bedienen.

Bedienung pro Kanalstreifen 1-8 (bezogen auf die aktuelle 8er-Bank):

    R  (CC 64-71)  Record / Weiterschalten -- NICHT geforwardet, sondern
                   in Live auf den Transportknopf des Loopers gemappt, damit
                   dessen eigene Quantisierung greift (siehe README)
    S  (CC 32-39)  Stop -- spielt den Loop zu Ende (siehe STOP_AT_LOOP_END);
                   ein zweiter Druck stoppt schon am naechsten Taktstrich
    M  (CC 48-55)  Loeschen (Clear) -- ebenfalls ueber Lives Mapping


    Marker SET (CC 60)  Spur des zuletzt bedienten Loopers auswaehlen
    Marker <   (CC 61)  eine Spur zurueck
    Marker >   (CC 62)  eine Spur vor
                        Blaettert per Vorgabe nur durch Spuren mit Looper;
                        MARKER_ONLY_LOOPER_TRACKS = False nimmt alle Spuren.

    Fader 1-8 (CC 0-7)  Lautstaerke der Spur des jeweiligen Loopers

    Play  (CC 41)  ALLE Looper starten  -- sofort, unquantisiert
    Stop  (CC 42)  ALLE Looper stoppen  -- sofort, unquantisiert
    Rec   (CC 45)  derzeit ohne Funktion

    Lives Transport wird vom Pult nicht mehr bedient; das liegt am SPD.

    Nicht vom Script bedient, sondern von AbleSet:
    Cycle      (CC 46)      Loop ein / aus
    Track < >  (CC 58, 59)  Song vor / zurueck
    << >>      (CC 43, 44)  Section vor / zurueck

Wichtig: "Clear" ist ueber die Live-API nicht erreichbar. Die M-CCs werden
deshalb bewusst NICHT in build_midi_map() geforwardet, damit sie bei
aktivierter "Remote"-Checkbox an Lives eigenes MIDI-Mapping durchgereicht
werden koennen (siehe README). Die M-LEDs treibt dieses Script trotzdem.

Gemessen: Ein CC gehoert entweder Lives MIDI-Mapping ODER dem Control
Surface, nie beiden. Wird ein CC in build_midi_map() geforwardet, sieht das
Mapping ihn nicht mehr -- und umgekehrt erreicht ein gemappter CC das Script
nicht. Das Script kann den Clear-Druck also grundsaetzlich nicht mitbekommen
und daher auch nicht wissen, ob ein Looper leer ist.

Die LEDs zeigen nicht den Zustand, sondern die jeweils sinnvolle Taste:
Record laesst R, M und S schnell blinken, Overdub dieselben drei langsam;
bei Play blinkt S langsam (stoppen); bei gestopptem Looper leuchten R und M
(aufnehmen oder loeschen).

LED-Rueckmeldung setzt voraus, dass im KORG KONTROL Editor
"LED Mode = External" gesetzt und in den Controller geschrieben wurde.
"""

from __future__ import absolute_import, print_function, unicode_literals

import re
import socket
import struct

import Live
from _Framework.ControlSurface import ControlSurface


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

DEBUG = False             # auf True setzen fuer ausfuehrliche Meldungen im
                          # Live-Log: gefundene Looper samt Parameterliste,
                          # jedes empfangene CC, jeder State-Uebergang.
                          # Log: ~/Library/Preferences/Ableton/Live <Ver>/Log.txt fuer ausfuehrliche Meldungen im
                          # Live-Log: gefundene Looper samt Parameterliste,
                          # jedes empfangene CC, jeder State-Uebergang.
                          # Log: ~/Library/Preferences/Ableton/Live <Ver>/Log.txt

MIDI_CHANNEL = 0          # nanoKONTROL2 Werkseinstellung: MIDI-Kanal 1

NUM_STRIPS = 8

CC_FADER_BASE = 0         # Fader 0..7 -> Lautstaerke der Looper-Spur
CC_SOLO_BASE = 32         # S 32..39  -> Stop am Loop-Ende (sonst Live-Mapping)
CC_MUTE_BASE = 48         # M 48..55  -> NICHT geforwardet (Clear via Live-Mapping)
CC_REC_BASE = 64          # R 64..71  -> NICHT geforwardet (Transport via Live-Mapping)

# Track < > gehen an AbleSet (Song vor/zurueck) und werden NICHT
# geforwardet. Damit hat die Bank-Umschaltung derzeit keine Taste --
# bei mehr als acht Loopern muesste ihr wieder eine zugewiesen werden.
CC_TRACK_LEFT = 58        # Track  <  -> AbleSet
CC_TRACK_RIGHT = 59       # Track  >  -> AbleSet
CC_MARKER_SET = 60        # Marker SET -> zur zuletzt bedienten Looper-Spur
CC_MARKER_LEFT = 61       # Marker <   -> eine Spur zurueck
CC_MARKER_RIGHT = 62      # Marker >   -> eine Spur vor

BANK_DOWN_CCS = ()
BANK_UP_CCS = ()

# Wodurch die Marker-Tasten blaettern:
#   True  -- nur durch Spuren, auf denen ein Looper liegt
#   False -- durch alle Spuren des Sets
MARKER_ONLY_LOOPER_TRACKS = True

CC_PLAY = 41              # ALLE Looper starten  -- sofort, unquantisiert
CC_STOP = 42              # ALLE Looper stoppen  -- sofort, unquantisiert
CC_RECORD = 45            # derzeit ohne Funktion, LED bleibt aus.
                          # Gemessen: Live laesst pro MIDI-Nachricht nur EIN
                          # Ziel zu -- "alle Looper loeschen" ist vom Pult aus
                          # deshalb nicht moeglich, weil Clear nur ueber Lives
                          # Mapping erreichbar ist und dessen Ausgang hier fuer
                          # die LEDs belegt ist.

# CC_RECORD fehlt hier absichtlich: es gehoert Lives Mapping.
TRANSPORT_CCS = (CC_PLAY, CC_STOP)

LED_ON = 127
LED_OFF = 0

# Looper State-Parameter
STATE_STOP = 0
STATE_RECORD = 1
STATE_PLAY = 2
STATE_OVERDUB = 3

# Weiterschalt-Logik der R-Taste

# Blink-Takt in update_display()-Ticks (ein Tick ~ 100 ms)
BLINK_FAST = 2            # ~200 ms an / 200 ms aus
BLINK_SLOW = 5            # ~500 ms an / 500 ms aus

# Alle LEDs regelmaessig zwangsweise neu senden, auch wenn sich nichts
# geaendert hat. Noetig, weil Live das Script beim nachtraeglichen Zuweisen
# des Output-Ports nicht neu instanziiert: der LED-Cache waere dann mit
# Werten gefuellt, deren MIDI-Nachrichten nie irgendwo angekommen sind.
# Gleiches gilt beim Aus- und wieder Einstecken des Controllers.
FORCE_REFRESH_TICKS = 20  # ~2 s

# --- Leer-Status vom Looper-Display ------------------------------------
# Die Live-API verraet nicht, ob ein Looper Inhalt hat. Der Server des
# Looper-Displays (~/Music/Ableton/Looper-Display) weiss es trotzdem: Er hoert
# die Clear-CCs am nanoKONTROL2 und am IAC-Bus mit und misst Aufnahmen. Er
# schickt /looper/<n>/empty 0|1 per OSC an diesen Port; n ist die
# Looper-Nummer in Spurreihenfolge (1-basiert), wie in der Reihenfolge von
# self._loopers. Bleibt die Nachricht laenger als EMPTY_TIMEOUT_TICKS aus
# (Server aus), gilt der Inhalt wieder als unbekannt und die LEDs verhalten
# sich wie ohne Server.
# Auf demselben Port kommen Transportbefehle des Displays an:
#   /transport/play | /transport/stop | /transport/record | /transport/loop
# (Record und Loop schalten um). Sie wirken auf Lives Transport, nicht auf
# die Looper -- die laufen weiter ueber die IAC-Schleife.
EMPTY_ENABLED = True
EMPTY_PORT = 11005
EMPTY_TIMEOUT_TICKS = 50  # ~5 s

# --- Datenquelle fuer das Looper-Display -------------------------------
# Das Script kennt alle Looper (auch in Racks, auf Return-Spuren und dem
# Master), haengt mit Listenern an ihrem State und laeuft im 100-ms-Takt.
# Es meldet dem Server deshalb selbst per OSC, was der frueher ueber
# AbletonOSC abfragen musste:
#   /nano/count      <anzahl>                            bei Aenderung, alle 2 s
#   /nano/looper     <n> <spurname> <state> <stop wartet> <laenge in beats>
#                    <voreingestellte aufnahmelaenge in takten, 0 = frei>
#                                                        pro Looper, bei Aenderung, alle 2 s
#   /nano/song       <songzeit> <tempo> <laeuft> <zaehler> <aufnahme> <loop>  jeder Tick (~100 ms)
# n ist 1-basiert in der Reihenfolge von self._loopers (Spurreihenfolge,
# dieselbe wie bei den Clear-CCs). Laeuft der Server nicht, verpuffen die
# UDP-Pakete folgenlos.
FEED_ENABLED = True
FEED_HOST = '127.0.0.1'
FEED_PORT = 11006
FEED_FULL_TICKS = 20      # ~2 s: Liste und Zustaende komplett wiederholen

# --- Stop am Loop-Ende -------------------------------------------------
# Stop soll den Loop zu Ende spielen, statt am naechsten Taktstrich
# abzubrechen: Bei einem 4-Takter, gestoppt in Takt 1, laeuft er bis Takt 4
# durch. Das Script zaehlt dazu selbst die Takte mit, misst die Loop-Laenge
# und drueckt den Stop-Knopf erst im LETZTEN Takt des Loops -- die
# Quantisierung des Loopers (1 Takt) laesst ihn dann genau am Loop-Ende
# stoppen. Ein zweiter Druck, solange er wartet, stoppt am naechsten
# Taktstrich.
#
# Stop-Wuensche kommen von den S-Tasten, vom SPD-SX-Script und vom Browser
# (per OSC auf EMPTY_PORT: /looper/<n>/stop bzw. /looper/all/stop). "all"
# stoppt alle laufenden Looper GEMEINSAM am Ende des laengsten Loops.
#
# Braucht Live 12 (Live.LooperDevice mit stop()). In aelteren Versionen
# gehen die S-Tasten wie frueher an Lives Mapping.
STOP_AT_LOOP_END = True
STOP_API = hasattr(Live, 'LooperDevice')
STOP_VIA_SCRIPT = STOP_AT_LOOP_END and STOP_API


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
        # Fuer Stop am Loop-Ende, alles in Takten des Script-Zaehlers
        self.seen_state = self.get_state()
        self.rec_start = None     # Takt, in dem die Aufnahme begann
        self.loop_start = None    # Takt, in dem der Loop (neu) anfing
        self.loop_bars = None     # Loop-Laenge in ganzen Takten
        self.stop_at = None       # Takt, an dem der Loop enden soll
        self.stop_sent = False    # Stop-Knopf fuer stop_at schon gedrueckt

    def take_over(self, old):
        """Messwerte eines alten Slots desselben Devices uebernehmen (Rescan)."""
        for name in ('seen_state', 'rec_start', 'loop_start', 'loop_bars',
                     'stop_at', 'stop_sent'):
            setattr(self, name, getattr(old, name))

    def current_bars(self, beats_per_bar):
        """Loop-Laenge in Takten. Bevorzugt Lives eigene Angabe (Live 12,
        loop_length in Beats): die kennt auch Loops, die schon mit dem Set
        geladen wurden, und folgt Laengenaenderungen am Geraet. Sonst die
        eigene Messung bei der Aufnahme."""
        try:
            beats = float(self.device.loop_length)
        except (AttributeError, RuntimeError, TypeError, ValueError):
            beats = 0.0
        if beats > 0:
            return max(1, int(round(beats / beats_per_bar)))
        return self.loop_bars

    def record_bars(self):
        """Am Looper voreingestellte Aufnahmelaenge in Takten (Live 12),
        0 = frei oder unbekannt. Die Liste enthaelt Beschriftungen wie
        "4 Bars"; die erste Zahl darin ist die Taktzahl."""
        try:
            label = self.device.record_length_list[self.device.record_length_index]
        except (AttributeError, RuntimeError, IndexError, TypeError):
            return 0
        match = re.search(r'\d+', str(label))
        return int(match.group()) if match else 0

    @property
    def stop_armed(self):
        return self.stop_at is not None

    def press_stop(self):
        """Stop-Knopf des Loopers druecken -- wartet wie die Maus auf die
        Quantisierung. Ohne Live-12-API bleibt nur der State-Parameter, und
        der stoppt sofort."""
        try:
            self.device.stop()
        except (AttributeError, RuntimeError):
            self.set_state(STATE_STOP)

    @property
    def is_valid(self):
        try:
            return (self.device is not None
                    and self.state_parameter is not None
                    and self.device.canonical_parent is not None)
        except RuntimeError:
            # Device wurde geloescht -> Proxy ist ungueltig
            return False

    def get_state(self):
        if self.state_parameter is None:
            return STATE_STOP
        try:
            return int(round(self.state_parameter.value))
        except RuntimeError:
            return STATE_STOP

    def set_state(self, value):
        if self.state_parameter is None:
            return
        try:
            self.state_parameter.value = float(value)
        except RuntimeError:
            pass


def _osc_message(address, *args):
    """OSC-Nachricht bauen: int -> i, float -> f, bool -> T/F, sonst String."""
    def pad(raw):
        return raw + b'\0' * (4 - len(raw) % 4)
    tags = ','
    body = b''
    for value in args:
        if isinstance(value, bool):
            tags += 'T' if value else 'F'
        elif isinstance(value, int):
            tags += 'i'
            body += struct.pack('>i', value)
        elif isinstance(value, float):
            tags += 'f'
            body += struct.pack('>f', value)
        else:
            tags += 's'
            body += pad(str(value).encode('utf-8'))
    return pad(address.encode('ascii')) + pad(tags.encode('ascii')) + body


def _parse_osc(data):
    """Kleiner OSC-Parser: liefert (adresse, [argumente]) oder None.

    Versteht die Typen i, f, s, T, F -- mehr schickt der Server nicht.
    """
    try:
        end = data.index(b'\0')
        address = data[:end].decode('ascii')
        pos = (end + 4) & ~3                  # Adresse ist auf 4 Byte aufgefuellt
        args = []
        if pos < len(data) and data[pos:pos + 1] == b',':
            tag_end = data.index(b'\0', pos)
            tags = data[pos + 1:tag_end].decode('ascii')
            pos = (tag_end + 4) & ~3
            for tag in tags:
                if tag == 'i':
                    args.append(struct.unpack('>i', data[pos:pos + 4])[0])
                    pos += 4
                elif tag == 'f':
                    args.append(struct.unpack('>f', data[pos:pos + 4])[0])
                    pos += 4
                elif tag == 's':
                    s_end = data.index(b'\0', pos)
                    args.append(data[pos:s_end].decode('utf-8'))
                    pos = (s_end + 4) & ~3
                elif tag == 'T':
                    args.append(True)
                elif tag == 'F':
                    args.append(False)
                else:
                    return None
        return address, args
    except (ValueError, IndexError, struct.error, UnicodeDecodeError):
        return None


def _parse_osc_empty(data):
    """/looper/<n>/empty <Zahl> -> (n, wert) oder None."""
    parsed = _parse_osc(data)
    if parsed is None:
        return None
    address, args = parsed
    parts = address.split('/')
    if len(parts) != 4 or parts[1] != 'looper' or parts[3] != 'empty' or not args:
        return None
    try:
        return int(parts[2]), args[0]
    except (ValueError, TypeError):
        return None


class LooperDisplay(ControlSurface):

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self._loopers = []
        self._bank_offset = 0
        self._blink_tick = 0
        self._led_cache = {}
        self._last_touched = None   # Index in self._loopers, fuer Marker SET
        self._last_states = []      # Momentaufnahme, um Aenderungen zuzuordnen
        self._state_listeners = []       # (parameter, callback)
        self._rescan_scheduled = False
        self._empty = {}                 # Looper-Nummer (1-basiert) -> True/False
        self._empty_tick = -EMPTY_TIMEOUT_TICKS   # Tick der letzten Nachricht
        self._empty_socket = None
        self._feed_socket = None
        # Fortlaufender Taktzaehler: zaehlt jeden Taktwechsel der Songposition
        # einmal, auch wenn sie springt (Arrangement-Loop, Locator).
        self._bar_count = 0
        self._bar_index = None
        if FEED_ENABLED:
            try:
                self._feed_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception as error:
                self.log_message('Display-Feed: Socket nicht nutzbar (%r)' % (error,))
        if EMPTY_ENABLED:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(False)
                sock.bind(('127.0.0.1', EMPTY_PORT))
                self._empty_socket = sock
            except Exception as error:
                self.log_message('Leer-Status: Port %d nicht nutzbar (%r), '
                                 'LEDs wie ohne Server' % (EMPTY_PORT, error))

        with self.component_guard():
            self._setup_structure_listeners()
            self._rescan_loopers()

        self.log_message('LooperDisplay geladen - %d Looper gefunden'
                         % len(self._loopers))
        if self._loopers:
            try:
                device = self._loopers[0].device
                self.log_message('Aufnahmelaengen laut Live: %s (gewaehlt: %s)'
                                 % (list(device.record_length_list),
                                    device.record_length_index))
            except (AttributeError, RuntimeError):
                pass
        if DEBUG:
            for i, slot in enumerate(self._loopers):
                try:
                    self.log_message('  Streifen %d: Spur "%s", State=%d'
                                     % (i + 1, slot.track.name, slot.get_state()))
                except Exception as error:
                    self.log_message('  Streifen %d: %r' % (i + 1, error))
            if self._loopers:
                device = self._loopers[0].device
                self.log_message('  Parameter von Looper 1 (is_active=%s):'
                                 % getattr(device, 'is_active', '?'))
                for parameter in device.parameters:
                    self.log_message('    %-18s = %-8s (min=%s max=%s)'
                                     % (parameter.name, parameter.value,
                                        parameter.min, parameter.max))
        self.schedule_message(1, self._refresh_all_leds)

    # ------------------------------------------------------------------
    # MIDI-Map: nur die CCs forwarden, die das Script selbst auswertet.
    # R und M fehlen hier absichtlich -> gehen an Lives MIDI-Mapping, S nur
    # ohne Stop am Loop-Ende. Regler und Transport bleiben frei fuer Live.
    # ------------------------------------------------------------------
    def build_midi_map(self, midi_map_handle):
        ControlSurface.build_midi_map(self, midi_map_handle)
        script_handle = self._c_instance.handle()
        forwarded = []
        for index in range(NUM_STRIPS):
            # R und M fehlen hier absichtlich: Sie gehen an Lives
            # MIDI-Mapping, das die echten Knoepfe des Loopers drueckt.
            # Nur so greift dessen eigene Quantisierung.
            forwarded.append(CC_FADER_BASE + index)
            if STOP_VIA_SCRIPT:
                forwarded.append(CC_SOLO_BASE + index)
        forwarded.extend(BANK_DOWN_CCS)
        forwarded.extend(BANK_UP_CCS)
        forwarded.append(CC_MARKER_SET)
        forwarded.append(CC_MARKER_LEFT)
        forwarded.append(CC_MARKER_RIGHT)
        forwarded.extend(TRANSPORT_CCS)
        for cc in forwarded:
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle,
                                         MIDI_CHANNEL, cc)
        if DEBUG:
            self.log_message('build_midi_map: forwarde Kanal %d, CCs %s'
                             % (MIDI_CHANNEL + 1, forwarded))

    # ------------------------------------------------------------------
    # Rohes MIDI-Handling
    # ------------------------------------------------------------------
    def receive_midi(self, midi_bytes):
        if DEBUG:
            self.log_message('receive_midi: %s' % (tuple(midi_bytes),))
        if len(midi_bytes) != 3:
            return
        status, cc, value = midi_bytes[0], midi_bytes[1], midi_bytes[2]
        if status != (0xB0 | MIDI_CHANNEL):
            return

        # Fader zuerst: bei ihnen ist der Wert 0 gueltig (Regler ganz unten)
        if CC_FADER_BASE <= cc < CC_FADER_BASE + NUM_STRIPS:
            self._on_fader(cc - CC_FADER_BASE, value)
            return

        if value == 0:
            # bei Tasten nur den Druck auswerten, das Loslassen ignorieren
            return

        if CC_SOLO_BASE <= cc < CC_SOLO_BASE + NUM_STRIPS:
            slot = self._slot_for_index(cc - CC_SOLO_BASE)
            if slot is not None:
                self._request_stop([slot])
        elif cc == CC_PLAY:
            self._set_all_loopers(STATE_PLAY, 'gestartet')
        elif cc == CC_STOP:
            self._set_all_loopers(STATE_STOP, 'gestoppt')
        elif cc in BANK_DOWN_CCS:
            self._change_bank(-NUM_STRIPS)
        elif cc in BANK_UP_CCS:
            self._change_bank(NUM_STRIPS)
        elif cc == CC_MARKER_LEFT:
            self._step_track(-1)
        elif cc == CC_MARKER_RIGHT:
            self._step_track(1)
        elif cc == CC_MARKER_SET:
            self._select_last_touched()
        elif DEBUG:
            self.log_message('CC %d wird nicht ausgewertet' % cc)

    def _set_all_loopers(self, target, was):
        """Play- und Stop-Taste: alle Looper auf einmal schalten.

        Bewusst direkt ueber den State-Parameter, also SOFORT und
        unquantisiert. Am Stueckende soll nicht noch ein Takt auslaufen, und
        beim Einsatz sollen alle gemeinsam losgehen. Fuer musikalische
        Uebergaenge die einzelnen Tasten benutzen -- die laufen ueber Lives
        Mapping und sind quantisiert.
        """
        count = 0
        for slot in self._loopers:
            if slot.is_valid and slot.get_state() != target:
                slot.set_state(target)
                count += 1
        self.show_message('Alle Looper %s (%d)' % (was, count))
        if DEBUG:
            self.log_message('Sammelbefehl %s: %d Looper' % (was, count))
        self._update_leds()

    def _on_fader(self, index, value):
        """Fader: Lautstaerke der Spur, auf der der Looper liegt."""
        slot = self._slot_for_index(index)
        if slot is None:
            return
        try:
            parameter = slot.track.mixer_device.volume
            parameter.value = (parameter.min
                               + (parameter.max - parameter.min) * value / 127.0)
        except (RuntimeError, AttributeError):
            pass

    def _slot_for_index(self, index):
        absolute = self._bank_offset + index
        if 0 <= absolute < len(self._loopers):
            slot = self._loopers[absolute]
            if slot.is_valid:
                return slot
        return None

    # ------------------------------------------------------------------
    # Marker-Tasten: durch Lives Spuren blaettern
    # ------------------------------------------------------------------
    def _scrollable_tracks(self):
        """Die Spuren, durch die geblaettert wird -- in Reihenfolge des Sets."""
        song = self.song()
        if not MARKER_ONLY_LOOPER_TRACKS:
            return list(song.tracks)
        tracks = []
        for slot in self._loopers:
            if not slot.is_valid:
                continue
            if slot.track not in tracks:
                tracks.append(slot.track)
        return tracks

    def _step_track(self, delta):
        tracks = self._scrollable_tracks()
        if not tracks:
            return
        song = self.song()
        try:
            index = tracks.index(song.view.selected_track)
        except ValueError:
            # Aktuelle Auswahl gehoert nicht dazu -- am Anfang beginnen.
            index = 0 if delta > 0 else len(tracks) - 1
        else:
            index = max(0, min(len(tracks) - 1, index + delta))
        self._select_track(tracks[index], index + 1, len(tracks))

    def _select_last_touched(self):
        """Marker SET: zur Spur des zuletzt bedienten Loopers springen."""
        if self._last_touched is None:
            self.show_message('Noch kein Looper bedient')
            return
        if not (0 <= self._last_touched < len(self._loopers)):
            self.show_message('Zuletzt bedienter Looper existiert nicht mehr')
            return
        slot = self._loopers[self._last_touched]
        if not slot.is_valid:
            return
        self._select_track(slot.track, self._last_touched + 1, len(self._loopers))

    def _select_track(self, track, position, total):
        try:
            self.song().view.selected_track = track
            self.show_message('%s  (%d von %d)' % (track.name, position, total))
            if DEBUG:
                self.log_message('Spur gewaehlt: %s' % track.name)
        except (RuntimeError, AttributeError) as error:
            if DEBUG:
                self.log_message('Spurauswahl fehlgeschlagen: %r' % (error,))

    def _change_bank(self, delta):
        if not self._loopers:
            return
        max_offset = max(0, ((len(self._loopers) - 1) // NUM_STRIPS) * NUM_STRIPS)
        new_offset = max(0, min(max_offset, self._bank_offset + delta))
        if new_offset != self._bank_offset:
            self._bank_offset = new_offset
            self.show_message('Looper-Bank %d-%d von %d'
                              % (self._bank_offset + 1,
                                 min(self._bank_offset + NUM_STRIPS,
                                     len(self._loopers)),
                                 len(self._loopers)))
            self._refresh_all_leds()

    # ------------------------------------------------------------------
    # Looper suchen (auch in Racks, rekursiv)
    # ------------------------------------------------------------------
    def _rescan_loopers(self):
        self._remove_state_listeners()
        previous = [slot for slot in self._loopers if slot.is_valid]
        self._loopers = []
        song = self.song()
        tracks = list(song.tracks) + list(song.return_tracks) + [song.master_track]
        for track in tracks:
            self._collect_loopers(track.devices, track)
        # Gemessene Loops nicht vergessen, nur weil eine Spur dazukam.
        for slot in self._loopers:
            for old in previous:
                if old.device == slot.device:
                    slot.take_over(old)
                    break

        max_offset = max(0, ((max(1, len(self._loopers)) - 1) // NUM_STRIPS) * NUM_STRIPS)
        self._bank_offset = min(self._bank_offset, max_offset)
        self._add_state_listeners()
        self._refresh_all_leds()
        self._feed_loopers()

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

    # ------------------------------------------------------------------
    # Listener
    # ------------------------------------------------------------------
    def _setup_structure_listeners(self):
        song = self.song()
        song.add_tracks_listener(self._on_structure_changed)
        song.add_return_tracks_listener(self._on_structure_changed)

    def _on_structure_changed(self):
        # Erst im naechsten Tick rescannen: waehrend der Aenderung sind die
        # Device-Listen noch nicht konsistent.
        if not self._rescan_scheduled:
            self._rescan_scheduled = True
            self.schedule_message(1, self._deferred_rescan)

    def _deferred_rescan(self):
        self._rescan_scheduled = False
        self._rescan_loopers()

    def _add_state_listeners(self):
        for slot in self._loopers:
            parameter = slot.state_parameter
            try:
                if not parameter.value_has_listener(self._on_state_changed):
                    parameter.add_value_listener(self._on_state_changed)
                    self._state_listeners.append(parameter)
            except RuntimeError:
                pass
        # Device-Listen der Tracks beobachten, damit neu eingefuegte oder
        # geloeschte Looper erkannt werden.
        for track in list(self.song().tracks) + list(self.song().return_tracks) \
                + [self.song().master_track]:
            try:
                if not track.devices_has_listener(self._on_structure_changed):
                    track.add_devices_listener(self._on_structure_changed)
            except RuntimeError:
                pass

    def _remove_state_listeners(self):
        for parameter in self._state_listeners:
            try:
                if parameter.value_has_listener(self._on_state_changed):
                    parameter.remove_value_listener(self._on_state_changed)
            except (RuntimeError, AttributeError):
                pass
        self._state_listeners = []

    def _remove_device_listeners(self):
        song = self.song()
        for track in list(song.tracks) + list(song.return_tracks) + [song.master_track]:
            try:
                if track.devices_has_listener(self._on_structure_changed):
                    track.remove_devices_listener(self._on_structure_changed)
            except (RuntimeError, AttributeError):
                pass

    def _note_last_touched(self):
        """Merkt sich, welcher Looper zuletzt seinen Zustand geaendert hat.

        Seit R, S und M ueber Lives Mapping laufen, sieht das Script die
        Tastendruecke nicht mehr. Der Wertelistener bleibt aber -- und der
        erwischt jede Aenderung, auch die per Maus.
        """
        states = []
        for slot in self._loopers:
            states.append(slot.get_state() if slot.is_valid else -1)
        if len(states) == len(self._last_states):
            for index, (before, now) in enumerate(zip(self._last_states, states)):
                if before != now:
                    self._last_touched = index
                    break
        self._last_states = states

    def _on_state_changed(self):
        self._note_last_touched()
        self._track_loops()
        self._feed_loopers()
        if DEBUG:
            states = [slot.get_state() for slot in self._loopers if slot.is_valid]
            self.log_message('State-Listener: %s, Transport laeuft=%s'
                             % (states, self.song().is_playing))
        self._update_leds()

    # ------------------------------------------------------------------
    # Stop am Loop-Ende
    # ------------------------------------------------------------------
    def _bars_now(self):
        """Stand des Taktzaehlers, mit Bruchteil im laufenden Takt."""
        song = self.song()
        try:
            bpb = float(song.signature_numerator) or 4.0
            beats = float(song.current_song_time)
        except Exception:
            return float(self._bar_count)
        index = int(beats // bpb)
        if self._bar_index is None:
            self._bar_index = index
        elif index != self._bar_index:
            delta = index - self._bar_index
            # Normal ein Takt weiter; ein Sprung der Songposition zaehlt als
            # genau ein Taktwechsel, der Looper selbst springt ja nicht mit.
            self._bar_count += delta if 0 < delta <= 2 else 1
            self._bar_index = index
        return self._bar_count + (beats % bpb) / bpb

    def _track_loops(self):
        """Zustandswechsel auswerten: Aufnahmen messen, Loop-Anfang merken."""
        now = None
        disarmed = False
        for number, slot in enumerate(self._loopers, 1):
            if not slot.is_valid:
                continue
            state = slot.get_state()
            prev = slot.seen_state
            if state == prev:
                continue
            slot.seen_state = state
            if now is None:
                now = self._bars_now()
            # Der Looper schaltet quantisiert, also auf einem Taktstrich.
            bar = int(round(now))
            if state == STATE_RECORD:
                slot.rec_start = bar
            elif state in (STATE_PLAY, STATE_OVERDUB):
                if prev == STATE_RECORD and slot.rec_start is not None:
                    bars = bar - slot.rec_start
                    # Kuerzer als ein Takt: Live hat Record gar nicht ausgefuehrt.
                    if bars >= 1:
                        slot.loop_bars = bars
                        slot.loop_start = bar
                        self._log_loop(number, slot)
                elif prev == STATE_STOP:
                    slot.loop_start = bar          # Loop faengt vorn an
            if state in (STATE_STOP, STATE_RECORD) and slot.stop_armed:
                slot.stop_at = None
                slot.stop_sent = False
                disarmed = True
        if disarmed:
            self._update_leds()

    def _log_loop(self, number, slot):
        try:
            api_length = slot.device.loop_length
        except (AttributeError, RuntimeError):
            api_length = '-'
        self.log_message('Looper %d: Loop %d Takte (loop_length laut Live: %s)'
                         % (number, slot.loop_bars, api_length))

    def _next_loop_end(self, slot, now):
        """Takt, an dem der laufende Durchgang des Loops endet, oder None."""
        try:
            bpb = float(self.song().signature_numerator) or 4.0
        except Exception:
            bpb = 4.0
        bars = slot.current_bars(bpb)
        if bars is None or slot.loop_start is None:
            return None
        done = now - slot.loop_start
        if done < 0:
            return None
        return slot.loop_start + (int(done // bars) + 1) * bars

    def _stop_command(self, which):
        """Stop-Wunsch per OSC (Browser, SPD-SX): Nummer oder 'all'."""
        valid = [slot for slot in self._loopers if slot.is_valid]
        if which == 'all':
            self._request_stop(valid, together=True)
            return
        try:
            number = int(which)
        except ValueError:
            return
        if 1 <= number <= len(valid):
            self._request_stop([valid[number - 1]])

    def _request_stop(self, slots, together=False):
        """Stop fuer einen oder mehrere Looper: am Ende des Loops, bei
        together gemeinsam am Ende des laengsten. Wartet schon einer, stoppt
        der zweite Druck am naechsten Taktstrich."""
        slots = [slot for slot in slots if slot.is_valid]
        for slot in slots:
            if slot.get_state() == STATE_RECORD:
                slot.press_stop()                  # Aufnahme: wie bisher
        running = [slot for slot in slots
                   if slot.get_state() in (STATE_PLAY, STATE_OVERDUB)]
        if not running:
            return
        now = self._bars_now()
        waiting = [slot for slot in running if slot.stop_armed and not slot.stop_sent]
        fresh = [slot for slot in running if not slot.stop_armed]
        if waiting or not STOP_VIA_SCRIPT:
            for slot in (waiting or fresh):
                slot.stop_at = int(now) + 1
                slot.stop_sent = True
                slot.press_stop()
            self.show_message('Stop am naechsten Takt')
        elif fresh:
            ends = dict((slot, self._next_loop_end(slot, now)) for slot in fresh)
            if together:
                known = [end for end in ends.values() if end is not None]
                last = max(known) if known else None
                ends = dict((slot, last) for slot in fresh)
            for slot, end in ends.items():
                if end is None:                    # Loop unbekannt: naechster Takt
                    slot.stop_at = int(now) + 1
                    slot.stop_sent = True
                    slot.press_stop()
                else:
                    slot.stop_at = end
                    slot.stop_sent = False
            known = [end for end in ends.values() if end is not None]
            if known:
                left = max(1, max(known) - int(now))
                self.show_message('Stop am Loop-Ende (noch %d %s)'
                                  % (left, 'Takt' if left == 1 else 'Takte'))
            self._service_stops(now)
        self._feed_loopers()
        self._update_leds()

    def _service_stops(self, now=None):
        """Jeden Tick: Taktzaehler fortschreiben, faellige Stops ausloesen."""
        if now is None:
            now = self._bars_now()
        changed = False
        try:
            playing = self.song().is_playing
        except Exception:
            playing = True
        for slot in self._loopers:
            if not slot.stop_armed or not slot.is_valid:
                continue
            if not slot.stop_sent and (now >= slot.stop_at - 1 or not playing):
                # Im letzten Takt des Loops druecken: die Quantisierung des
                # Loopers laesst ihn dann genau am Loop-Ende stoppen.
                slot.press_stop()
                slot.stop_sent = True
                changed = True
            elif slot.stop_sent and now >= slot.stop_at + 1:
                # Laeuft trotzdem noch -- nicht ewig als wartend anzeigen.
                slot.stop_at = None
                slot.stop_sent = False
                changed = True
        if changed:
            self._feed_loopers()

    # ------------------------------------------------------------------
    # LEDs
    # ------------------------------------------------------------------
    def update_display(self):
        # Wird von Live etwa alle 100 ms aufgerufen -> Blink-Takt.
        ControlSurface.update_display(self)
        self._blink_tick += 1
        if self._blink_tick % FORCE_REFRESH_TICKS == 0:
            self._led_cache = {}
        self._poll_empty()
        self._service_stops()
        self._update_leds()
        self._feed_song()
        if self._blink_tick % FEED_FULL_TICKS == 0:
            self._feed_loopers()

    # ------------------------------------------------------------------
    # Datenquelle fuer das Looper-Display
    # ------------------------------------------------------------------
    def _feed_send(self, data):
        if self._feed_socket is None:
            return
        try:
            self._feed_socket.sendto(data, (FEED_HOST, FEED_PORT))
        except Exception:
            pass

    def _feed_loopers(self):
        """Looper-Liste mit Namen und Zustaenden an den Server."""
        if self._feed_socket is None:
            return
        valid = [slot for slot in self._loopers if slot.is_valid]
        self._feed_send(_osc_message('/nano/count', len(valid)))
        for number, slot in enumerate(valid, 1):
            try:
                name = slot.track.name
                state = int(slot.get_state())
            except Exception:
                continue
            # Loop-Laenge laut Live in Beats (Live 12), 0 = unbekannt. Damit
            # zeigt die Anzeige auch Loops an, die mit dem Set geladen wurden.
            try:
                length = float(slot.device.loop_length)
            except (AttributeError, RuntimeError, TypeError, ValueError):
                length = 0.0
            self._feed_send(_osc_message('/nano/looper', number, name, state,
                                         1 if slot.stop_armed else 0, length,
                                         slot.record_bars()))

    def _feed_song(self):
        if self._feed_socket is None:
            return
        try:
            song = self.song()
            self._feed_send(_osc_message('/nano/song',
                                         float(song.current_song_time),
                                         float(song.tempo),
                                         bool(song.is_playing),
                                         int(song.signature_numerator),
                                         bool(song.record_mode),
                                         bool(song.loop)))
        except Exception:
            pass

    def _poll_empty(self):
        """Leer-Meldungen des Looper-Displays einlesen (nicht blockierend)."""
        if self._empty_socket is None:
            return
        for _ in range(64):
            try:
                data, _addr = self._empty_socket.recvfrom(512)
            except (socket.error, OSError):
                break
            parsed = _parse_osc(data)
            if parsed is None:
                continue
            address, args = parsed
            if address.startswith('/transport/'):
                self._transport_command(address[len('/transport/'):])
                continue
            parts = address.split('/')
            if len(parts) == 4 and parts[1] == 'looper' and parts[3] == 'stop':
                if not (args and args[0] == 0):     # 0 = Taste losgelassen
                    self._stop_command(parts[2])
                continue
            empty = _parse_osc_empty(data)
            if empty is None:
                continue
            number, value = empty
            self._empty[number] = bool(value)
            self._empty_tick = self._blink_tick
        if self._empty and self._blink_tick - self._empty_tick > EMPTY_TIMEOUT_TICKS:
            self._empty = {}            # Server schweigt: Inhalt unbekannt

    def _transport_command(self, command):
        """Transportbefehl des Displays auf Lives Transport anwenden."""
        song = self.song()
        try:
            if command == 'play':
                song.start_playing()
            elif command == 'stop':
                song.stop_playing()
            elif command == 'record':
                song.record_mode = not song.record_mode
            elif command == 'loop':
                song.loop = not song.loop
            else:
                return
            if DEBUG:
                self.log_message('Display: Transport %s' % command)
            self._feed_song()
        except Exception as error:
            self.log_message('Display: Transport %s fehlgeschlagen: %r' % (command, error))

    def _is_empty(self, slot):
        """True nur, wenn der Server den Looper ausdruecklich als leer meldet."""
        try:
            number = self._loopers.index(slot) + 1
        except ValueError:
            return False
        return self._empty.get(number, False)

    def _blink(self, period):
        return (self._blink_tick // period) % 2 == 0

    def _update_leds(self):
        """LEDs zeigen, welche Taste gerade sinnvoll ist:

            Record     R, M und S blinken schnell
            Overdub    R, M und S blinken langsam
            Play       S blinkt langsam  -- stoppen
            Stop wartet aufs Loop-Ende: S blinkt schnell
            gestoppt   R und M an        -- aufnehmen oder loeschen
            LEER (laut Looper-Display), gestoppt oder nach Sammelstart im Play
                       nur R an          -- nichts zu stoppen oder zu loeschen
        """
        for index in range(NUM_STRIPS):
            slot = self._slot_for_index(index)
            rec_led = mute_led = solo_led = LED_OFF
            if slot is not None:
                state = slot.get_state()
                # Leerer Looper (laut Looper-Display) in Play/Overdub: nach einem
                # Sammelstart formal "laufend", aber ohne Inhalt. Nichts zu stoppen,
                # nichts zu loeschen -- nur R (dort heisst der Transportknopf Record).
                if state in (STATE_PLAY, STATE_OVERDUB) and self._is_empty(slot):
                    state = STATE_STOP
                if state == STATE_RECORD:
                    blink = LED_ON if self._blink(BLINK_FAST) else LED_OFF
                    rec_led = mute_led = solo_led = blink
                elif state == STATE_OVERDUB:
                    blink = LED_ON if self._blink(BLINK_SLOW) else LED_OFF
                    rec_led = mute_led = solo_led = blink
                elif state == STATE_PLAY:
                    solo_led = LED_ON if self._blink(BLINK_SLOW) else LED_OFF
                if state in (STATE_PLAY, STATE_OVERDUB) and slot.stop_armed:
                    solo_led = LED_ON if self._blink(BLINK_FAST) else LED_OFF
                else:
                    rec_led = LED_ON
                    mute_led = LED_OFF if self._is_empty(slot) else LED_ON
            self._send_led(CC_REC_BASE + index, rec_led)
            self._send_led(CC_MUTE_BASE + index, mute_led)
            self._send_led(CC_SOLO_BASE + index, solo_led)
        self._update_transport_leds()

    def _update_transport_leds(self):
        """Der Transportblock bedient die Looper, nicht mehr Lives Wiedergabe.

        Jede LED leuchtet, solange ihre Taste etwas zu tun hat.
        """
        try:
            states = [slot.get_state() for slot in self._loopers if slot.is_valid]
            running = any(state != STATE_STOP for state in states)
            stopped = any(state == STATE_STOP for state in states)
            self._send_led(CC_PLAY, LED_ON if stopped else LED_OFF)
            self._send_led(CC_STOP, LED_ON if running else LED_OFF)
            self._send_led(CC_RECORD, LED_OFF)   # ohne Funktion
        except RuntimeError:
            pass

    def _send_led(self, cc, value):
        if self._led_cache.get(cc) == value:
            return
        self._led_cache[cc] = value
        # Ohne angeschlossenes Geraet (Output = "Kein") laesst sich nicht senden.
        # Das Script wird auch ohne nanoKONTROL2 verwendet -- fuer den Server ist
        # es dann nur Datenquelle, die LEDs bleiben einfach ohne Wirkung.
        try:
            self._send_midi((0xB0 | MIDI_CHANNEL, cc, value))
        except RuntimeError:
            pass

    def _refresh_all_leds(self):
        self._led_cache = {}
        self._update_leds()

    def _all_leds_off(self):
        try:
            for base in (CC_SOLO_BASE, CC_MUTE_BASE, CC_REC_BASE):
                for index in range(NUM_STRIPS):
                    self._send_midi((0xB0 | MIDI_CHANNEL, base + index, LED_OFF))
            for cc in TRANSPORT_CCS:
                self._send_midi((0xB0 | MIDI_CHANNEL, cc, LED_OFF))
        except RuntimeError:
            pass

    # ------------------------------------------------------------------
    # Lebenszyklus
    # ------------------------------------------------------------------
    def refresh_state(self):
        ControlSurface.refresh_state(self)
        self._refresh_all_leds()

    def disconnect(self):
        self._remove_state_listeners()
        self._remove_device_listeners()
        song = self.song()
        try:
            if song.tracks_has_listener(self._on_structure_changed):
                song.remove_tracks_listener(self._on_structure_changed)
            if song.return_tracks_has_listener(self._on_structure_changed):
                song.remove_return_tracks_listener(self._on_structure_changed)
        except (RuntimeError, AttributeError):
            pass
        self._all_leds_off()
        if self._empty_socket is not None:
            try:
                self._empty_socket.close()
            except Exception:
                pass
            self._empty_socket = None
        if self._feed_socket is not None:
            try:
                self._feed_socket.close()
            except Exception:
                pass
            self._feed_socket = None
        ControlSurface.disconnect(self)
