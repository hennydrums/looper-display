# Looper Display

> **Schöner zu lesen:** Doppelklick auf [`install.html`](install.html)
> öffnet dieselbe Anleitung als gestaltete Webseite mit
> Schritt-für-Schritt-Zahlen, Bedienungsteil und Sprachumschalter
> (DE/EN) oben rechts. Dieses Dokument hier ist die reine Textversion
> zum Nachschlagen.

Zeigt den Zustand aller Looper eines Ableton-Live-Sets als drehende Ringe im
Browser: auf dem Mac, auf einem zweiten Monitor oder auf jedem Tablet im
selben Netz. Kein Max for Live, kein AbletonOSC, keine bestimmte Hardware
nötig.

## Was du bekommst

```
Looper-Display starten.command        Doppelklick startet sie
Looper-Display beenden.command        Doppelklick beendet sie wieder

Zum Kopieren/                         einmalig an den Zielort kopieren
├── Remote Scripts/
│   ├── LooperDisplay/                Pflicht: liefert die Daten an die Anzeige
│   └── SPD_SX_Pro_Looper/            optional: nur mit einem Roland SPD-SX
└── SPD-SX Pro Preset/                optional: fertiges Kit zum Import auf das SPD-SX

Programm (nicht anfassen)/            die App selbst
├── looper-display
└── node_modules/
```

Die App selbst ist eine fertige Programmdatei für Apple-Silicon-Macs. Kein
Node.js, kein `npm install`, kein Terminal-Wissen nötig. Der Ordner
`Programm (nicht anfassen)` muss dabei so bleiben, wie er ist.

## Installation

1. Den Ordner `Zum Kopieren/Remote Scripts/LooperDisplay` nach
   `~/Music/Ableton/User Library/Remote Scripts/` kopieren. Bei einem
   Roland SPD-SX PRO im Rig auch `Zum Kopieren/Remote Scripts/SPD_SX_Pro_Looper`
   dorthin kopieren -- das passende Kit-Preset dafür liegt in
   `Zum Kopieren/SPD-SX Pro Preset/`.
2. Live starten. `Einstellungen → Link, Tempo & MIDI`: in einer freien Zeile
   der Bedienoberflächen `LooperDisplay` auswählen. **Ohne eigene
   Hardware bleiben Eingang und Ausgang auf „Kein"** — ein KORG
   nanoKONTROL2 ist optional, auch ohne angeschlossenes Gerät liefert das
   Script alle Daten für die Anzeige. Hast du ein **echtes KORG
   nanoKONTROL2** im Rig, dort stattdessen Eingang `nanoKONTROL2
   (SLIDER/KNOB)` und Ausgang `nanoKONTROL2 (CTRL)` einstellen, sonst
   bleiben Tasten und LEDs am Gerät ohne Wirkung.
3. Doppelklick auf `Looper-Display starten.command`. Beim ersten Mal fragt
   macOS, ob die Datei geöffnet werden darf — Rechtsklick auf die Datei,
   dann „Öffnen" wählen und bestätigen, das genügt einmalig.
4. Das Terminalfenster zeigt zwei Adressen:

   ```
   Anzeige: http://localhost:8080
            http://192.168.0.XXX:8080  (fuer Tablet/Handy)
   ```

   Die erste im eigenen Browser öffnen, die zweite auf einem Tablet im
   selben WLAN. Taste `F` schaltet Vollbild, Fenster einfach offen lassen.

## Wie beendest du es wieder?

Solange das Terminalfenster aus Schritt 3 offen ist, läuft die App. Drei
gleichwertige Wege, sie zu beenden:

- **Ctrl + C** im Terminalfenster drücken, während es im Vordergrund ist.
- Das **Terminalfenster schließen** — macOS fragt nach, ob der laufende
  Vorgang beendet werden soll, das bestätigen.
- Doppelklick auf **`Looper-Display beenden.command`** — findet und beendet
  die App auch dann, wenn das Terminalfenster schon zu ist.

Nur den Browser-Tab zu schließen beendet die App nicht, sie läuft im
Hintergrund weiter — meist gewollt, falls ein Tablet die Seite dauerhaft
offen halten soll.

## Was sofort funktioniert

- Alle Looper im Set, auch in Racks, auf Return-Spuren und dem Master.
- Zustand (Record, Play, Overdub, Stop), Loop-Länge in Takten, laufender
  Takt — alles live, ohne dass du etwas einstellen musst.
- Vier Tasten oben in der Anzeige für Lives Transport: **Play, Stop, Record,
  Loop**. Die wirken direkt über die Live-API, brauchen kein zusätzliches
  Setup.

## Bedienung einzelner Looper aus dem Browser (optional, mit Einrichtung)

Jeder Ring lässt sich antippen (Transportknopf), dazu gibt es zwei Tasten
für Stop und Clear. Das braucht — anders als die vier Transporttasten oben —
eine kleine einmalige Einrichtung, weil Ableton Loopern keinen direkten
„stoppe quantisiert" oder „lösche" Befehl über die API erlaubt. Der Weg
dahin: ein virtueller MIDI-Bus, den die App bedient, und eine ganz normale
MIDI-Zuweisung in Live, wie du sie auch mit jedem Controller machen würdest.

1. **Audio-MIDI-Setup** öffnen (Spotlight → „Audio-MIDI-Setup"), Fenster
   „MIDI-Studio" einblenden, doppelt auf „IAC-Treiber" klicken, **„Gerät
   ist online"** anhaken. Ein Bus reicht.
2. In Live, `Einstellungen → Link, Tempo & MIDI`, bei den MIDI-Ports:
   Eingang `IAC-Treiber (Bus 1)` — **Remote an**, **Track aus**.
3. `Cmd+M` in Live (Map-Modus). Für jeden Looper:
   - großen Transportknopf anklicken, kurz im Browser auf den Ring tippen
     → Zuweisung entsteht automatisch.
   - Stop-Knopf des Loopers anklicken, im Browser die STOP-Ecke tippen.
   - Clear-Button des Loopers anklicken, im Browser die CLEAR-Ecke tippen.
4. `Cmd+M` verlassen, **Set speichern**.

Live quantisiert danach selbst, genau wie bei einem echten Controller —
ein Tipp auf „Play" wartet auf den nächsten Takt, wenn der Looper darauf
eingestellt ist.

## Grenzen

- Ob ein Looper leer oder gefüllt ist, verrät die Live-API nicht. Diese
  Anzeige zeigt es deshalb nur, wenn du selbst per Klick auf den Ring die
  Taktzahl gesetzt hast oder eine neue Aufnahme messen konnte.
- Die App muss auf demselben Rechner wie Live laufen (oder im selben Netz,
  mit einer Umgebungsvariable für die Adresse) — sie hört per UDP mit,
  das geht nicht über das Internet.
- Getestet auf Apple-Silicon-Macs (M-Prozessoren). Für Intel-Macs oder
  Windows bitte melden.

---

*Diese Anzeige ist für den persönlichen, nicht-kommerziellen Gebrauch
gedacht. Weitergabe an Freunde und Bandkollegen ausdrücklich erwünscht,
Weiterverkauf oder Veröffentlichung als eigenes Produkt bitte nicht ohne
Rücksprache.*
