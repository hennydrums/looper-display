# LooperDisplay

Ableton Live Remote Script, das den Zustand aller **Looper-Devices** eines
Sets an das Looper Display (Browser) liefert. Ein **KORG nanoKONTROL2**
ist optional und kann zusätzlich zur Fernsteuerung der Looper genutzt
werden.

> **Auch ohne den Controller nützlich.** Looper-Suche, Zustände und
> Songposition laufen unabhängig von Ein- und Ausgang. Fehlt das Gerät,
> bleiben Fader, Marker und LEDs einfach ohne Wirkung — Live lädt das
> Script trotzdem klaglos, Ein- und Ausgang können auf „Kein" stehen.
> Siehe Abschnitt 5.

---

## 1. Installation

### Installationspfad

Den kompletten Ordner `LooperDisplay` (mit `__init__.py` und
`LooperDisplay.py`) hierhin kopieren:

**macOS**

```
/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/LooperDisplay
```

(Rechtsklick auf Live.app → „Paketinhalt zeigen" → `Contents/App-Resources/MIDI Remote Scripts/`)

Alternativ, updatesicher, ab Live 11:

```
~/Music/Ableton/User Library/Remote Scripts/LooperDisplay
```

**Windows**

```
C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\LooperDisplay
```

oder

```
...\Documents\Ableton\User Library\Remote Scripts\LooperDisplay
```

Danach **Live neu starten**.

### In Live aktivieren

`Einstellungen → Link/Tempo/MIDI` (bzw. `Link/MIDI`):

| Feld | Wert |
|---|---|
| Control Surface | `LooperDisplay` |
| Input | `nanoKONTROL2 SLIDER/KNOB` |
| Output | `nanoKONTROL2 CTRL` |

**Achtung, die Ports heissen unterschiedlich.** Der nanoKONTROL2 meldet unter
macOS genau einen Eingang (`SLIDER/KNOB`) und genau einen Ausgang (`CTRL`).
Einen Ausgang namens `SLIDER/KNOB` gibt es nicht — die LEDs laufen ueber
`nanoKONTROL2 CTRL`. Ohne gesetzten Output laedt das Script zwar (die
Meldung steht im Log), aber es leuchtet nichts.

In der MIDI-Ports-Tabelle darunter beim **Input**-Port des nanoKONTROL2
zusätzlich **Remote = An** setzen. Das ist Voraussetzung für das
Clear-Mapping (siehe Abschnitt 4).

### LEDs: KORG KONTROL Editor

Die LED-Rückmeldung funktioniert **nur**, wenn der Controller im externen
LED-Modus läuft:

1. KORG KONTROL Editor öffnen, nanoKONTROL2 verbinden.
2. **`LED Mode` = `External`** setzen.
3. `Communication → Write Scene Data` — die Einstellung muss in den
   Controller geschrieben werden, sonst ist sie nach dem Trennen weg.

> **Achtung, macOS-Version des Editors.** In der Mac-Fassung des KORG
> KONTROL Editor sind die `Communication`-Menüpunkte (`Write Scene Data`,
> `Receive Scene Data`) praktisch nicht erreichbar — im Programm angelegt,
> aber nicht bedienbar. Getestet mit macOS 26 auf Apple Silicon.
> **Lösung: die Einstellung einmalig auf einem Windows-Rechner schreiben.**
> Dort funktioniert derselbe Editor normal. Danach steckt `LED Mode =
> External` dauerhaft im Controller, und der Mac braucht den Editor nie
> wieder.

Ohne diesen Schritt schalten die Tasten ihre LEDs nur lokal beim Drücken
und zeigen den Looper-Status nicht an.

---

## 2. Bedienung

Pro Kanalstreifen 1–8 (bezogen auf die aktuelle 8er-Bank):

| Taste | CC | Funktion |
|---|---|---|
| **R** | 64–71 | Record / Weiterschalten — via Live-MIDI-Mapping, siehe Abschnitt 4 |
| **S** | 32–39 | **Stop am Loop-Ende** — vom Script, siehe „Stop am Loop-Ende“; zweiter Druck: nächster Takt |
| **M** | 48–55 | Löschen (Clear) — via Live-MIDI-Mapping, siehe Abschnitt 4 |
| **Fader** | 0–7 | Lautstärke der Spur, auf der der jeweilige Looper sitzt |

| Taste | CC | Funktion |
|---|---|---|
| **Marker SET** | 60 | Spur des zuletzt bedienten Loopers auswählen |
| **Marker ◀ ▶** | 61, 62 | eine Spur zurück / vor |
| **Play** | 41 | **alle Looper starten** — sofort, unquantisiert |
| **Stop** | 42 | **alle Looper stoppen** — sofort, unquantisiert |
| **Rec** | 45 | derzeit ohne Funktion |

Beim Bankwechsel zeigt Live kurz an, welcher Looper-Bereich aktiv ist
(z. B. „Looper-Bank 9-14 von 14").

> **Stolperstelle: R auf einem bereits gefüllten Looper.**
> `Record` ist in Live nur für einen **leeren** Looper eine gültige Aktion.
> Steht der Looper auf Stop und enthält bereits Material, setzt das Script
> zwar `State = 1`, das Gerät führt es aber nicht aus — die R-LED blinkt
> dann, ohne dass etwas passiert. Ob ein Looper Material enthält, gibt die
> Live-API nicht preis, das Script kann es also nicht selbst erkennen.
> In dem Fall R ein zweites Mal drücken: das schaltet auf `Play`.
> Ebenso gilt: zum Aufnehmen muss die Spur scharfgeschaltet und der
> Monitor passend gesetzt sein — sonst nimmt der Looper Stille auf.

### Von AbleSet bedient, nicht vom Script

Diese Tasten forwardet das Script **nicht**. AbleSet liest den Controller
unabhängig von Live mit und wertet sie selbst aus:

| Taste | CC | Funktion in AbleSet |
|---|---|---|
| **Cycle** | 46 | Loop ein / aus |
| **Track ◀ ▶** | 58, 59 | Song vor / zurück |
| **◀◀ ▶▶** | 43, 44 | Section vor / zurück |

> **Die Bank-Umschaltung hat dadurch keine Taste mehr.** Sie lag auf
> Track ◀ ▶. Bei bis zu acht Loopern spielt das keine Rolle — alles liegt in
> einer Bank. Ab dem neunten müsste ihr wieder ein Bedienelement zugewiesen
> werden; die Funktion ist im Script erhalten.

### Der Transportblock bedient die Looper

**Play** startet alle Looper, **Stop** hält alle an — beides sofort und
unquantisiert über den State-Parameter. Lives eigener Transport wird vom
Pult **nicht** mehr bedient; dafür gibt es das SPD-Pad rechts oben.

Damit gibt es zwei klar getrennte Werkzeuge:

| | Wirkung | Timing |
|---|---|---|
| **R 1–8** | einzelner Looper | quantisiert, über Lives Mapping |
| **S 1–8** | einzelner Looper | am Ende des Loops, vom Script |
| **Play, Stop** | alle Looper | sofort, über die API |

Für musikalische Übergänge die Streifentasten, fürs Stückende den
Transportblock. Der unquantisierte Weg ist dort kein Kompromiss: Am Ende
soll nicht noch ein Takt auslaufen.

> **Die Rec-Taste ist stillgelegt.** Sie sollte „alle Looper löschen"
> bekommen — das geht aber nicht: `Clear` ist nur über Lives MIDI-Mapping
> erreichbar, und **Live lässt pro MIDI-Nachricht nur ein Ziel zu**
> (gemessen). Eine Taste auf acht Clear-Knöpfe zu legen ist damit
> unmöglich, und selbst senden kann das Script die acht CCs nicht, weil sein
> Ausgang für die LEDs belegt ist. Zum Löschen bleiben die M-Tasten je
> Looper — oder ein SPD-Pad, das über die IAC-Schleife senden kann.

### Stop am Loop-Ende

Stop spielt den Loop zu Ende, statt am nächsten Taktstrich abzubrechen: Ein
4-Takter, gestoppt in Takt 1, läuft bis Takt 4 durch. Das Script zählt dazu
selbst die Takte mit, misst die Loop-Länge bei der Aufnahme und drückt den
Stop-Knopf des Loopers (`LooperDevice.stop()`) erst im **letzten Takt** des
Loops — die Quantisierung des Loopers (1 Takt) lässt ihn dann genau am
Loop-Ende stoppen. Solange er wartet, blinkt S schnell.

| Auslöser | Wirkung |
|---|---|
| S-Taste | dieser Looper stoppt am Ende seines Loops |
| S-Taste, zweiter Druck | stoppt doch schon am nächsten Taktstrich |
| OSC `/looper/<n>/stop` auf Port 11005 | wie die S-Taste — so kommen das SPD-Stop-Pad und die STOP-Taste des Browsers an |
| OSC `/looper/all/stop` | alle laufenden Looper **gemeinsam** am Ende des längsten Loops (SPD „Stop all“) |
| Stop im Transportblock (CC 42) | unverändert: alle sofort |

Die Länge kommt von Live selbst (`LooperDevice.loop_length`, in Beats) — so
kennt das Script auch Loops, die mit dem Set geladen wurden; ohne diese
Angabe nimmt es die eigene Messung. Den Loop-Anfang merkt es sich beim Start
des Loopers (Stop → Play). Läuft ein Looper schon, während das Script lädt,
stoppt der erste Stop wie früher am nächsten Taktstrich. Braucht Live 12; unter Live 11
bleiben die S-Tasten beim Live-Mapping. Abschalten: `STOP_AT_LOOP_END = False`.

### Marker-Tasten: durch Lives Spuren blättern

| Taste | CC | Funktion |
|---|---|---|
| **Marker SET** | 60 | Spur des **zuletzt bedienten** Loopers auswählen |
| **Marker ◀** | 61 | eine Spur zurück |
| **Marker ▶** | 62 | eine Spur vor |

Live zeigt dabei den Spurnamen und die Position, etwa `LOOPER3 (3 von 8)`,
und scrollt die Ansicht mit. Die Auswahl läuft nicht im Kreis, sondern stößt
an den Enden an.

Geblättert wird per Vorgabe **nur durch Spuren mit Looper**. Oben im Script:

```python
MARKER_ONLY_LOOPER_TRACKS = False   # dann durch alle Spuren des Sets
```

„Zuletzt bedient" heißt: der Looper, dessen **Zustand** sich zuletzt
geändert hat. Da R, S und M über Lives Mapping laufen, sieht das Script die
Tastendrücke nicht — es wertet stattdessen den Wertelistener aus. Der
erwischt jede Änderung, auch die per Maus.

### Fader

Fader 1–8 steuern die Lautstärke der Spur, auf der der Looper des jeweiligen
Streifens liegt — also dieselbe Zuordnung wie R/M/S, und ebenso
bankabhängig.

Die Fader arbeiten **absolut, ohne Abholmodus**: Nach einem Bankwechsel
stimmt die physische Faderstellung nicht mehr mit der Lautstärke der neu
zugewiesenen Spur überein. Die erste Bewegung springt dann auf den
Faderwert. Bei bis zu acht Loopern, also einer einzigen Bank, spielt das
keine Rolle.

### LED-Anzeige

Die LEDs zeigen **nicht den Zustand, sondern die jeweils sinnvolle Taste**:

| Looper | R | M | S |
|---|---|---|---|
| **Record** | blinkt schnell | blinkt schnell | blinkt schnell |
| **Overdub** | blinkt langsam | blinkt langsam | blinkt langsam |
| **Play** | aus | aus | blinkt langsam |
| **gestoppt, mit Inhalt** | **an** | **an** | aus |
| **leer** (gestoppt oder nach Sammelstart im Play) | **an** | aus | aus |

Bei gestopptem Looper mit Inhalt leuchten R und M gemeinsam: Du kannst ihn
entweder bespielen oder löschen. Bei Play blinkt S — die Taste, die ihn
stoppt. Ist auf einem Streifen gar kein Looper, bleiben alle drei LEDs
dunkel.

Ob ein Looper leer ist, weiß die Live-API nicht. Das Script bekommt die
Information vom Server des Looper-Displays (Abschnitt 5). Ohne Server
verschwindet die Leer-Zeile nach fünf Sekunden von selbst, und R und M
leuchten bei jedem gestoppten Looper wie früher. Ein leerer Looper, den ein
Sammelstart formal auf Play gesetzt hat, wird wie ein gestoppter leerer
behandelt: nur R, denn dort bedeutet der Transportknopf Record.

| Transport-LED | Bedeutung |
|---|---|
| **Play** an | mindestens ein Looper **steht** — es gibt etwas zu starten |
| **Stop** an | mindestens ein Looper **läuft** — es gibt etwas zu stoppen |
| **Rec** | immer aus, die Taste hat keine Funktion |

## 3. Welche Looper werden gefunden?

Das Script scannt beim Laden — und bei jeder Änderung der Spur- oder
Device-Struktur — **alle** Audio-/MIDI-Spuren, Return-Spuren und den Master
nach Devices der Klasse `Looper`, **auch innerhalb von Racks** (Instrument-,
Audio-Effekt- und Drum-Racks, rekursiv über alle Chains).

Die gefundenen Looper werden in Reihenfolge der Spuren durchnummeriert und
in 8er-Bänken auf die Streifen gelegt.

---

## 4. Transport und Clear einmalig mappen

> **Nur für Live 11.** Mit Live 12 bedient das Script R, M und S selbst über
> die Looper-API (`record()`, `play()`, `overdub()`, `stop()`, `clear()`) —
> keine Zuweisungen, kein IAC-Treiber. Vorhandene Zuweisungen für R und M
> schaden nicht; eine Stop-Zuweisung bitte löschen (siehe unten). Die
> Rec-Taste löscht mit Live 12 bei zweimaligem Druck **alle** Looper.

R und M laufen über Lives eigenes MIDI-Mapping — weil nur so die
Quantisierung des Loopers greift:

| Bedienelement | CC | Ziel im Looper |
|---|---|---|
| **R 1–8** | 64–71 | der große **Transportknopf** |
| **S 1–8** | 32–39 | **nicht mappen** (nur unter Live 11: **Stop**) |
| **M 1–8** | 48–55 | **Clear** |

Das Script forwardet R und M **absichtlich nicht**, damit Live sie sieht.

> **Stop ab Live 12 nicht mappen.** Die S-Tasten wertet das Script selbst aus
> (Stop am Loop-Ende). Eine eigene Zuweisung in Live hat aber **Vorrang** vor
> dem Script: Ist der Stop-Knopf auf CC 32–39 gemappt, drückt S ihn direkt,
> und der Looper stoppt am nächsten Taktstrich. Vorhandene Stop-Zuweisungen
> im Map-Modus anklicken und mit `Entf` löschen.

### Warum das nicht über die API läuft

Der `State`-Parameter lässt sich zwar setzen — aber **das umgeht die
Quantisierung des Loopers**. Gemessen: Bei laufendem Transport und
`Quantization = 1 Bar` wartet ein Mausklick auf den nächsten Takt, ein
geschriebener Parameterwert nicht; die Aufnahme startet sofort.

Lives MIDI-Mapping drückt dagegen den **echten Knopf**. Der Looper
quantisiert dann selbst, sample-genau. Eine Nachbildung im Script wäre an
den 100-ms-Takt von `update_display` gebunden gewesen — für einen Looper
unbrauchbar.

`Clear` ist über die API gar nicht erst erreichbar, weder als Parameter noch
als Funktion. Auch Max for Live hilft nicht, es benutzt dasselbe Object
Model.

### Anleitung

Einmalig, danach im Set gespeichert:

1. `Cmd + M` (MIDI-Map-Modus).
2. Den **großen Transportknopf** von Looper 1 anklicken, **R1** drücken →
   `CC 64`.
3. Den **Clear**-Button von Looper 1 anklicken, **M1** drücken → `CC 48`.
4. Für Looper 2 dasselbe mit **R2** und **M2** — und so weiter bis Looper 8.
5. `Cmd + M` verlassen, **Set speichern**.

Nur unter Live 11 zusätzlich den **Stop**-Knopf mit **S1**–**S8** (`CC 32`–`39`) mappen.

Vierundzwanzig Zuweisungen insgesamt. Am besten im Standard-Set ablegen:
`Einstellungen → File/Folder → Standard-Set speichern`.

> **Vorsicht im Map-Modus.** Solange `Cmd + M` aktiv ist und ein Element
> ausgewählt, legt *jede* eingehende MIDI-Nachricht eine Zuweisung an und
> überschreibt die vorhandene.

### Dieselben Zuweisungen bedienen auch das SPD-SX

Lives Zuweisungen hängen **an der Nachricht, nicht am Port**. Das
SPD-Script sendet dieselben CCs über den IAC-Treiber und trifft damit
dieselben sechzehn Einträge — ein zweiter Satz ist nicht nötig. Siehe
`SPD_SX_Pro_Looper/README.md`.

### Hinweis zu den Bänken

Lives MIDI-Mapping ist statisch und folgt den Bank-Tasten **nicht**. R1, S1
und M1 gehören fest zu Looper 1. Bei bis zu acht Loopern spielt das keine
Rolle; darüber hinaus erreichen die drei Tastenreihen nur die ersten acht.
Die **Fader** folgen der Bank weiterhin.


### Was das Script forwardet — und was nicht

| Bedienelement | CC | Vom Script belegt? |
|---|---|---|
| R-Tasten | 64–71 | **nein** → frei für Live-Mapping (Transportknopf) |
| M-Tasten | 48–55 | **nein** → frei für Live-Mapping (Clear); LEDs treibt das Script |
| Track ◀ ▶ | 58, 59 | **nein** → AbleSet (Song vor/zurück) |
| S-Tasten | 32–39 | **ja** (Stop am Loop-Ende; unter Live 11 nein → Live-Mapping) |
| Fader | 0–7 | **ja** |
| Regler | 16–23 | nein → frei für Live-Mapping |
| Transport Play/Stop/Rec | 41, 42, 45 | **ja** |
| Marker SET, ◀ ▶ | 60, 61, 62 | **ja** (Spurauswahl) |
| Cycle, ◀◀ ▶▶ | 46, 43, 44 | **nein** → AbleSet (Loop, Section) |

---

## 5. Zusammenspiel mit dem Looper-Display

Das Script ist die Datenquelle des Looper-Displays
(`~/Music/Ableton/Looper-Display/`, eigene `README.md`) und bekommt von
dessen Server eine Information zurück, die es selbst nicht hat. Beides läuft
über OSC auf `127.0.0.1`, ohne Live anzufassen.

**Was das Script sendet** (Port `FEED_PORT`, Standard 11006):

| Adresse | Wann | Inhalt |
|---|---|---|
| `/nano/count` | bei Änderung, alle 2 s | Anzahl der gefundenen Looper |
| `/nano/looper` | bei jedem State-Wechsel, alle 2 s | Nummer (1-basiert, Reihenfolge von `_loopers`), Spurname, State |
| `/nano/song` | jeder `update_display`-Tick (~100 ms) | Songzeit in Beats, Tempo, Transport läuft, Taktzähler, Aufnahme scharf, Loop an |

Die Nummern sind dieselben wie bei den Clear-CCs: Looper 1 ist CC 48, wie
in Lives Zuweisungen. Weil das Script auch Looper in Racks, auf Return-Spuren
und dem Master findet, sieht das Display sie ebenfalls — AbletonOSC konnte
das nicht und wird deshalb nicht mehr gebraucht.

**Was das Script empfängt** (Port `EMPTY_PORT`, Standard 11005):
`/looper/<n>/empty 0|1` und `/transport/play|stop|record|loop` — die vier
Transporttasten des Looper-Displays. Sie rufen `start_playing()`,
`stop_playing()` und die umschaltenden Eigenschaften `record_mode` und
`loop` der Live-API auf, unabhängig von den Loopern. Der Server weiß das, weil er außerhalb von Live
die Clear-CCs am nanoKONTROL2 und am IAC-Bus mithört und jede Aufnahme
sieht. Das Script liest den Port nicht blockierend in `update_display`.
Kommt `EMPTY_TIMEOUT_TICKS` (~5 s) lang nichts, gilt jeder Looper wieder als
„unbekannt".

Einstellungen oben im Script: `FEED_ENABLED`, `FEED_HOST`, `FEED_PORT`,
`FEED_FULL_TICKS`, `EMPTY_ENABLED`, `EMPTY_PORT`, `EMPTY_TIMEOUT_TICKS`.
Der Stand vor dem Display liegt als
`NanoKontrol2Looper.py.bak-vor-looper-display` daneben.

## 6. Fehlersuche

**Die LEDs bleiben dunkel.**
Steht der **Output** der Control-Surface-Zeile auf `nanoKONTROL2 CTRL`?
Das ist der haeufigste Fehler — `None` ist die Voreinstellung, und das
Script laedt auch ohne Output klaglos. Zweitens: `LED Mode = External` im
KORG KONTROL Editor gesetzt *und* mit „Write Scene Data" in den Controller
geschrieben?

**Die M-Tasten lassen sich nicht mappen.**
Beim Input-Port muss **Remote** aktiviert sein. Steht der Controller nicht
auf den Werks-CCs (S = 32–39), zuerst im KORG KONTROL Editor zurücksetzen.

**Prüfen, ob der Controller LEDs überhaupt annimmt.**
Ein Test an Live vorbei: ein kleines Programm schickt direkt CC 32-39 mit
Wert 127 an den Port `nanoKONTROL2 CTRL`. Leuchtet die S-Reihe daraufhin
nicht, steht `LED Mode` noch auf `Internal` — dann hilft nur der Editor
(siehe oben), kein Remote Script der Welt.

**Es passiert gar nichts.**
Der Controller muss auf **MIDI-Kanal 1** senden (Werkseinstellung). Prüfen,
ob Live überhaupt Daten sieht (MIDI-Indikator oben rechts). Meldungen des
Scripts stehen im Live-Log:
`~/Library/Preferences/Ableton/Live <Version>/Log.txt`
(Windows: `%APPDATA%\Ableton\Live <Version>\Preferences\Log.txt`) —
dort steht beim Start `LooperDisplay geladen - N Looper gefunden`.

**Ein neu eingefügter Looper taucht nicht auf.**
Das Script scannt bei Struktur-Änderungen automatisch neu. Falls nicht,
Control Surface in den Einstellungen kurz ab- und wieder anwählen.

**Das Looper-Display zeigt „Live antwortet nicht" oder gar nichts.**
Das Script sendet nicht. Live nach dem Kopieren der neuen Fassung neu
gestartet? `FEED_ENABLED = True`? Das Terminal des Servers muss
`Quelle: nanoKONTROL2-Script meldet sich` zeigen.

**Die M-LED bleibt bei einem leeren Looper an.**
Der Server des Displays läuft nicht oder hat den Clear nicht gesehen. Im
Live-Log steht beim Start, falls Port 11005 nicht zu öffnen war:
`Leer-Status: Port 11005 nicht nutzbar`.
