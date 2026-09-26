# SPD_SX_Pro_Looper

Ableton Live Remote Script, mit dem fünf Pads eines **Roland SPD-SX PRO** die
Looper-Devices eines Sets steuern. Ergänzung zu `LooperDisplay` —
beide Scripts dürfen gleichzeitig laufen und arbeiten auf denselben Loopern.

---

## Installation

Ordner nach

```
~/Music/Ableton/User Library/Remote Scripts/SPD_SX_Pro_Looper
```

kopieren, Live neu starten. Dann in `Einstellungen → Link, Tempo & MIDI` in
einer **freien Zeile**:

| Feld | Wert |
|---|---|
| Bedienoberfläche | `SPD_SX_Pro_Looper` |
| Eingang | `SPD-SX PRO` |
| Ausgang | `IAC-Treiber Bus 1` |

Der Ausgang geht **nicht** an das SPD, sondern in die IAC-Schleife — darüber
laufen die Clear-Befehle (siehe unten). Beim IAC-**Eingang** muss in der
MIDI-Ports-Tabelle **Remote** aktiv und **Track** ausgeschaltet sein.

---

## Preset auf das Gerät laden

Die neun Pads lassen sich statt von Hand über ein fertiges Kit-Preset
einrichten: `KIT-APP_LooperDisplay.TD0`, im LooperDisplay-Paket unter
`Zum Kopieren/SPD-SX Pro Preset/` (dort, wo auch dieser Script-Ordner
herkommt).

1. SPD-SX PRO per USB verbinden, **SPD-SX PRO APP** öffnen (kostenlos von
   Roland, verbindet automatisch mit dem Gerät).
2. Menü `BACKUP → LOAD 1 KIT`.
3. Im Dialog „BACKUP LOAD 1 KIT (FROM FILE)" über `…` die Datei
   `KIT-APP_LooperDisplay.TD0` auswählen, **OK**.
4. Oben rechts auf **WRITE** klicken — schreibt den geladenen Kit auf das
   Gerät.

Die Pad-Belegung des Presets — Note und Kanal müssen zu den
Einstellungen unten im Script passen:

| Pad | Note | Bezeichnung im Preset | Funktion |
|---|---|---|---|
| 1 | 1 | Loop DELETE | Clear |
| 2 | 4 | START ALL Loops | alle Looper starten, sofort |
| 3 | 62 | SONG START/STOP | nicht vom Script — Lives Transport direkt |
| 4 | 2 | Loop STOP | Stop am Loop-Ende |
| 5 | 5 | STOP ALL LOOPER | alle Looper stoppen, gemeinsam am Ende des längsten Loops |
| 6 | 65 | LOOPING Toggle | nicht vom Script — Loop in der Arrangement-Ansicht über AbleSet |
| 7 | 3 | Loop GO | Start / Record / Overdub |
| 8 | 6 | PREV Looper | ◀ vorheriger Looper |
| 9 | 68 | NEXT Looper | nächster Looper ▶ |

---

## Bedienung

Die drei linken Pads wirken immer auf den **gerade gewählten** Looper:

| Pad | Note | Funktion |
|---|---|---|
| links **oben** | 1 | **Clear** — über die IAC-Schleife |
| links **Mitte** | 2 | **Stop am Loop-Ende** — über das LooperDisplay-Script |
| links **unten** | 3 | **Start / Record / Overdub** — über die IAC-Schleife |
| Mitte **oben** | 4 | **alle Looper starten** — sofort, über die API |
| **Mitte** | 5 | **alle Looper stoppen** — gemeinsam am Loop-Ende, über das LooperDisplay-Script |
| Mitte **unten** | 6 | vorheriger Looper |
| rechts **unten** | 68 | nächster Looper |
| rechts **oben** | 62 | Start / Stop von Lives Transport — **nicht** vom Script |
| rechts **Mitte** | 65 | Loop in der Arrangement-Ansicht, über AbleSet — **nicht** vom Script |

Alle auf MIDI-Kanal 1. Die Auswahl läuft **nicht** im Kreis, sondern stößt
an den Enden an — so rutschst du unter Druck nicht versehentlich durch.

Beim Umschalten zeigt Live zusätzlich kurz `SPD-SX: Looper 3 von 8` in der
Statuszeile.

### Pads ändern

Oben im Script als Paare aus MIDI-Kanal (0-basiert) und Notennummer:

```python
PAD_CLEAR = (0, 1)
PAD_STOP  = (0, 2)
PAD_CYCLE = (0, 3)
PAD_PREV  = (0, 6)
PAD_NEXT  = (0, 68)

PAD_ALL_START = (0, 4)    # alle starten, sofort
PAD_ALL_STOP  = (0, 5)    # alle stoppen, am Loop-Ende
```

Alle auf **Kanal 1**. Das Pad rechts unten sendet ab Werk auf Kanal 12 und
wurde am Gerät auf Kanal 1 umgestellt, damit alles zum Looping auf demselben
Kanal liegt.

Das Pad **rechts Mitte** (Note 65, Kanal 12) bleibt unberührt: Es schaltet
über AbleSet den Loop in der Arrangement-Ansicht um und geht das Script
nichts an.

---

## Anzeige über AbleSet

Das Script schickt die Nummer des gewählten Loopers (1-basiert) per OSC an
AbleSets **Shared Variables**:

```
/shared/LooperSPD_SX   →   127.0.0.1:39042
```

Gesendet wird bei jedem Umschalten, beim Laden des Sets und wenn sich die
Zahl der Looper ändert — das Label steht also nie leer.

Im AbleSet-Canvas liest man den Wert mit

```
${shared("LooperSPD_SX")}
```

und blendet pro Looper ein Label über eine Sichtbarkeitsbedingung ein
(`= 1`, `= 2`, …).

### Einstellungen im Script

```python
OSC_ENABLED  = True
OSC_HOST     = '127.0.0.1'
OSC_PORT     = 39042
OSC_VARIABLE = 'LooperSPD_SX'
OSC_AS_INT   = True     # Zahl oder Text — siehe unten, das ist entscheidend
OSC_EXTRA_TARGETS = [('127.0.0.1', 11002)]   # dieselbe Nachricht zusätzlich an das Looper-Display
```

`OSC_EXTRA_TARGETS` bekommt dieselbe Nachricht wie AbleSet. Eingetragen ist
der Server des Looper-Displays (`~/Music/Ableton/Looper-Display/`), der den
gewählten Looper im Browser mit gelbem Rahmen und dem Schild „SPD"
markiert. Läuft der Server nicht, verpuffen die Pakete folgenlos. Der Stand
vor dieser Ergänzung liegt als `SpdSxProLooper.py.bak-vor-looper-display`
daneben.

### Zahl oder Text: hängt davon ab, wie die Canvas liest

AbleSet bietet zwei Wege, und sie brauchen **entgegengesetzte** Typen:

| Zugriff im Canvas | Was zurückkommt | Nötiger Typ |
|---|---|---|
| `osc(":<Verbindung>/shared/LooperSPD_SX")` | das rohe OSC-Argument | **Zahl** (`OSC_AS_INT = True`) |
| `shared("LooperSPD_SX")` | die gespeicherte Shared Variable | **Text** (`OSC_AS_INT = False`) |

Gemessen an AbleSet 3.2.0-beta.3: Ein Integer wird als OSC-Wert angenommen
(`"Updated OSC value"`), aber **nicht** als Shared Variable gespeichert — in
den `Storing variables`-Zeilen des Logs stehen ausschließlich Zeichenketten.
`shared()` liefert dann `undefined`.

Die hier verwendete Canvas nutzt `osc()` mit striktem Vergleich:

```javascript
${osc(":AbletonHenny/shared/LooperSPD_SX") === 3 ? "orange-500" : "gray-700"}
```

`=== 3` trifft nur auf eine Zahl zu, `"3"` wäre dauerhaft falsch. Deshalb
**`OSC_AS_INT = True`**.

### Zweiter Rechner: gleiche AbleSet-Version

Läuft auf einem zweiten Rechner eine andere AbleSet-Fassung, kann dieselbe
Canvas dort abstürzen, während sie auf dem ersten läuft:

```
TypeError: e.includes is not a function.
(In 'e.includes("${")', 'e.includes' is undefined)
```

Die Meldung ist irreführend — sie sieht nach einem falschen Wert-Typ oder
einem fehlenden OSC-Wert aus, obwohl nur die Version nicht passt. **Bei
diesem Fehler zuerst die Versionen vergleichen.** Sie steht im Dateinamen
des Logs:

```
~/Library/Application Support/ableset/logs/ableset-<Version>-….log
```

Gleiche Version auf beiden Rechnern ist ohnehin richtig, wenn beide dasselbe
Projekt fahren.

### Das Präfix der OSC-Verbindung

`:AbletonHenny` ist der Name der OSC-Verbindung in AbleSet, nicht Teil der
gesendeten Adresse. Das Script sendet schlicht an `/shared/LooperSPD_SX`;
AbleSet stellt den Verbindungsnamen davor.

Definiert ist er in

```
~/Library/Application Support/ableset/osc-connections.json
```

```json
{"connections":[{"id":"…","name":"AbletonHenny","listenPort":39042}]}
```

> **Diese Datei gehört nicht zum Ableton-Projekt.** Sie liegt in AbleSets
> Programmordner und wandert nicht mit. Auf einem zweiten Rechner muss die
> Verbindung **denselben Namen** tragen, sonst liefert jedes
> `osc(":AbletonHenny/…")` dort `undefined` — und die Canvas stirbt beim
> Auswerten mit
>
> ```
> TypeError: e.includes is not a function.
> (In 'e.includes("${")', 'e.includes' is undefined)
> ```
>
> Der Fehler tritt bei **jedem** `undefined` in einem `${…}` auf und sagt
> nichts darüber, welcher Ausdruck ihn ausgelöst hat.

---

## Was nicht geht, und warum

### Sammelbefehle

**Stoppen (Mitte)** schickt einen Stop-Wunsch an das Script LooperDisplay
(OSC `/looper/all/stop` auf Port 11005). Das zählt die Takte mit und lässt
alle Looper **gemeinsam am Ende des längsten Loops** stoppen; ein zweiter
Druck stoppt am nächsten Taktstrich. Das einzelne Stop-Pad geht denselben
Weg (`/looper/<n>/stop`). Ohne Live 12 fällt das Script auf den alten Weg
zurück: Stop-CC über die IAC-Schleife, quantisiert auf den nächsten Takt.

**Starten (Mitte oben)** geht bewusst den anderen Weg, nämlich direkt über
den State-Parameter und damit **unquantisiert**:

> Der große Transportknopf schaltet weiter, und bei einem **leeren** Looper
> bedeutet er `Record`. Da die Live-API den Loop-Inhalt nicht preisgibt,
> kann das Script leer und gefüllt nicht unterscheiden — ein quantisierter
> Sammelstart würde auf der Bühne ungewollt Aufnahmen starten. Über den
> State-Parameter bleibt `Play` auf einem leeren Looper dagegen folgenlos.

> **Nebenwirkung, die bleibt:** Nach dem Sammelstart stehen auch leere
> Looper auf `Play`. Die LEDs am Pult zeigen sie damit als laufend, und man
> sieht nicht mehr, welche leer sind. Diese Information hat nur das
> Max-Device, das die Loop-Länge misst — sichtbar zu machen wäre sie in der
> AbleSet-Canvas.

### Transport und Clear laufen über die IAC-Schleife

Zwei Dinge erreicht die Live-API nicht — und beide gehen deshalb denselben
Weg: Das Script sendet einen CC in den IAC-Treiber, Live sieht ihn als
Fernsteuerungs-Eingang und drückt den echten Knopf im Device.

| Pad | gesendeter CC | Ziel im Looper |
|---|---|---|
| links unten | `64 + Nummer des Loopers` | der große **Transportknopf** |
| links Mitte | `32 + Nummer des Loopers` | **Stop** |
| links oben | `48 + Nummer des Loopers` | **Clear** |

Alle auf **Kanal 1** — dieselben Nachrichten, die auch die R-, S- und
M-Tasten des nanoKONTROL2 senden. Es genügt also **ein** Satz von
vierundzwanzig Zuweisungen für beide Geräte.

#### Warum das nicht über den State-Parameter läuft

Der `State`-Parameter ließe sich setzen — aber das **umgeht die
Quantisierung des Loopers**. Gemessen: Bei laufendem Transport und
`Quantization = 1 Bar` wartet ein Mausklick auf den nächsten Takt, ein
geschriebener Parameterwert nicht. Lives Mapping drückt dagegen den echten
Knopf, und der Looper quantisiert selbst — sample-genau.

Eine Nachbildung im Script wurde gebaut und wieder verworfen: Sie hing am
100-ms-Takt von `update_display` und war damit für einen Looper zu träge.

#### Und Clear

`Clear` ist über die Live-API **nicht** erreichbar — nur über Lives eigenes
MIDI-Mapping. Das wiederum ist statisch: Es hängt am konkreten Looper und
würde der Durchschaltung nicht folgen. Und ein MIDI-Ereignis gehört immer
entweder Lives Mapping **oder** dem Control Surface, nie beiden (am Gerät
gemessen).

Der Ausweg nutzt den **IAC-Treiber** als Schleife:

1. Der Ausgang des Scripts steht auf `IAC-Treiber Bus 1`.
2. Je nach Pad sendet das Script `CC 48 + Nummer` (Clear),
   `CC 32 + Nummer` (Stop) oder `CC 64 + Nummer` (Transport) auf
   **MIDI-Kanal 1** — Looper 1 → CC 48, 32 beziehungsweise 64.
   Das sind **genau dieselben Nachrichten wie die M-, S- und R-Tasten des
   nanoKONTROL2**: Lives Zuweisungen hängen an der Nachricht, nicht am Port,
   also lösen beide Geräte dieselbe Zuweisung aus. Es genügt **ein** Satz von
   vierundzwanzig Zuweisungen für beide Wege.
3. Der CC kommt über IAC als Fernsteuerungs-Eingang in Live zurück und löst
   dort den gemappten Clear-Button aus.

Dadurch **folgen alle drei der Durchschaltung**, obwohl Lives
Mapping statisch ist: Für jeden Looper existiert eine eigene, fest
zugewiesene CC-Nummer, und das Script wählt aus, welche es sendet.

Bestätigt: Live nimmt seinen eigenen IAC-Rückweg als Fernsteuerung an.

#### Die Zuweisungen anlegen

Einmalig, danach im Set gespeichert:

1. `Cmd + M` (MIDI-Map-Modus).
2. Den **großen Transportknopf** von Looper 1 anklicken, **R1** drücken →
   `CC 64`.
3. Den **Stop**-Knopf von Looper 1 anklicken, **S1** drücken → `CC 32`.
4. Den **Clear**-Button von Looper 1 anklicken, **M1** drücken → `CC 48`.
5. Für Looper 2 dasselbe mit **R2**, **S2**, **M2** — und so weiter bis
   Looper 8.
6. `Cmd + M` verlassen, Set speichern.

Ein separates Mapping für das SPD ist **nicht** nötig — es sendet dieselben
CCs.

Einstellungen im Script:

```python
CLEAR_ENABLED     = True
CLEAR_CHANNEL     = 0    # 0-basiert, entspricht MIDI-Kanal 1
CLEAR_CC_BASE     = 48   # Looper 1 -> CC 48, wie M1 am nanoKONTROL2
TRANSPORT_CHANNEL = 0
TRANSPORT_CC_BASE = 64   # Looper 1 -> CC 64, wie R1 am nanoKONTROL2
STOP_CC_BASE      = 32   # Looper 1 -> CC 32, wie S1 am nanoKONTROL2
```

### Keine LED-Rückmeldung an den Pads

Technisch ginge ein Pulsieren: Das SPD lässt ein Pad aufleuchten, wenn es
eine Note dafür empfängt, und die Helligkeit hängt nicht an der Velocity.
Ein Dauerleuchten ist aber nicht möglich, und der nötige Dauerstrom an Notes
löst laufend die Pad-Samples mit aus. Diese Variante wurde erprobt und
wieder verworfen — die Anzeige übernimmt AbleSet.

Den Looper-Zustand selbst zeigen weiterhin die LEDs des nanoKONTROL2. Die
hängen am State-Parameter und nicht daran, wer ihn verändert hat. Welcher
Looper gerade am SPD gewählt ist, zeigt außerdem das Looper-Display im
Browser (`LOOPER-SETUP.md`, Abschnitt 5).
