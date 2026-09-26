# Looper Display

> **Download:** [`LooperDisplay-….zip` unter Releases](https://github.com/hennydrums/looper-display/releases/latest)
> — nicht „Source code", dem fehlt die App.
>
> **Schöner zu lesen:** die [Anleitung als Webseite](https://hennydrums.github.io/looper-display/install.html)
> (DE/EN), liegt auch im Zip als `Anleitung - Guide.html`. Dieses Dokument
> hier ist die reine Textversion zum Nachschlagen.

Zeigt den Zustand aller Looper eines Ableton-Live-Sets als drehende Ringe im
Browser: auf dem Mac, auf einem zweiten Monitor oder auf jedem Tablet im
selben Netz. Kein Max for Live, kein AbletonOSC, keine bestimmte Hardware
nötig.

**Voraussetzungen:** Mac mit Apple-Chip (M1 oder neuer), macOS 12 oder
neuer, Ableton Live 11 oder 12. **Empfohlen ist Live 12** — nur damit spielt
Stop den Loop zu Ende, kennt die Anzeige die Länge von Loops, die mit dem Set
geladen wurden, und zeigt bei leeren Loopern die voreingestellte
Aufnahmelänge. Unter Live 11 läuft alles andere wie gewohnt.

## Was du bekommst

```
LooperDisplay.app                     Doppelklick startet sie
Anleitung - Guide.html                die Anleitung als Webseite
LooperDisplay.als                     Beispielprojekt mit acht Loopern

Zum Kopieren/                         einmalig an den Zielort kopieren
├── Remote Scripts/
│   ├── LooperDisplay/                Pflicht: liefert die Daten an die Anzeige
│   └── SPD_SX_Pro_Looper/            optional: nur mit einem Roland SPD-SX
└── SPD-SX Pro Preset/                optional: fertiges Kit zum Import auf das SPD-SX
```

Die App ist ein fertiges Programm für Apple-Silicon-Macs. Kein Node.js,
kein `npm install`, kein Terminal nötig.

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
3. `LooperDisplay.app` in den Ordner „Programme" ziehen und doppelklicken.
   Beim ersten Mal meldet macOS, dass es die App nicht prüfen kann — mit
   „Fertig" schließen, dann **Systemeinstellungen → Datenschutz &
   Sicherheit** ganz nach unten scrollen und **„Trotzdem öffnen"** wählen.
   Das ist nur einmal nötig.
4. Die Anzeige öffnet sich automatisch im Browser. Die Adresse fürs Tablet
   (selbes WLAN) steht in der Anzeige oben rechts unter **📱 Tablet**.
   Taste `F` schaltet Vollbild.

## Wie beendest du es wieder?

**⏻ Quit server** oben rechts in der Anzeige. Nur den Browser-Tab zu
schließen beendet die App nicht, sie läuft im Hintergrund weiter — meist
gewollt, falls ein Tablet die Seite dauerhaft offen halten soll. Ein
erneuter Doppelklick auf die App öffnet die Anzeige wieder.

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
   - Den Stop-Knopf **nicht** mappen (ab Live 12): STOP läuft übers Script und
     spielt den Loop zu Ende; eine Stop-Zuweisung hätte Vorrang und stoppt am
     nächsten Takt.
   - Clear-Button des Loopers anklicken, im Browser die Mülleimer-Ecke (🗑) tippen.
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
