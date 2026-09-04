---
name: sprech-watch
description: "Erzeugt die deutsche Sprechspur einer Speaking-VSL und prüft sie gegen die Zeitfenster — ein durchgehender Take statt isolierter Blöcke, danach an den Sprechpausen geschnitten. Nutzen nach der Lokalisierung, wenn „Sprechspur", „Voiceover", „TTS", „Stimme bauen" fällt."
---

# sprech-watch — die Sprechspur und ihr Prüfer-Loop

## Das Grundgesetz: EIN Take, danach schneiden

**Die ganze Copy wird in EINEM Stück erzeugt — nie Block für Block.**

Warum: Ein TTS-Modell hört nur den Text, den es bekommt. Erzeugt man Block 3 isoliert,
weiß es nichts von Block 2 und 4 — es setzt an, schließt ab, und legt in jeden Block
eine Anfangs- und Schlussmelodie. Das Ergebnis klingt abgehackt: **die Stimme hört
mitten im Gedanken auf, obwohl dort kein Punkt steht.** Genau daran erkennt ein
Muttersprachler sofort die Maschine.

Der Ablauf:
1. **Ein Take** der vollständigen Copy erzeugen. Der Sprechfluss läuft durch, die
   Betonung trägt über Satzgrenzen hinweg.
2. **Sprechpausen messen**, nicht schätzen:
   `ffmpeg -i ganz.mp3 -af silencedetect=noise=-32dB:d=0.18 -f null -`
3. **An den Blockgrenzen schneiden** — die gemessene Pause, die dem erwarteten
   Zeichenanteil am nächsten liegt (Zeichen des Blocks ÷ Zeichen gesamt × Gesamtdauer).
4. **Auf die Zeitmarken legen** (`adelay`). Innerhalb eines Blocks wird der Ton NIE
   angefasst — nur die Stille dazwischen wird gedehnt oder gekürzt.

**Gemessen im QUA-001-Lauf:** Blockweise Erzeugung ergab Viktors Befund „klingt
roboterhaft, hört mitten im Satz auf, man merkt sofort das ist eine KI-Stimme". Der
durchgehende Take derselben Copy mit derselben Stimme klang zusammenhängend.

## Modell zuerst nachsehen, nie annehmen

Vor dem ersten Take die Modell-Liste des Kontos abfragen:
`GET https://api.elevenlabs.io/v1/models` (Header `xi-api-key`) und das neueste
deutschfähige nehmen. Im QUA-001-Lauf lief zuerst `eleven_multilingual_v2`, obwohl
`eleven_v3` im Konto lag — eine ganze Modellgeneration verschenkt, aus reiner Annahme.

Achtung: `eleven_v3` unterstützt `previous_text`/`next_text` **nicht** (HTTP 400,
`unsupported_model`). Das ist kein Problem, weil der EIN-Take-Weg den Kontext
ohnehin von selbst mitbringt — er ist dem Kontextfeld sogar überlegen.

## Der Prüfer-Loop: jeder Block gegen sein Fenster

Je Block Dauer messen und gegen sein Zeitfenster halten. Toleranz 0,25 s.
Die Montage schneidet an den ECHTEN Wortzeiten (Scribe auf dem Take, Grenze =
Mitte der Pause zwischen den Blöcken) — der Zeichen-Anteil ist nur Notbehelf.

Die Montage trimmt jeden Block an den Rändern von Stille (der Schnitt liegt in
Pausen-Mitten — ungetrimmt beginnt jeder Block mit halber Take-Pause und der
Stimm-Einsatz verfehlt seine Marke; gemessen: bis 1,2 s tote Luft an Blockgrenzen).

Längen-Leiter (in dieser Reihenfolge, die Montage fährt sie selbst):
| Fall | Mittel |
|---|---|
| Überlänge 1 | **Pausen quetschen** — Stille > 0,4 s auf 0,32 s (silenceremove); v3 legt mit Tags theatralische Pausen, die Wörter bleiben unberührt |
| Überlänge 2 | `atempo` bis 1,10 — hört niemand; bis 1,15 nur bei ruhigen Blöcken |
| Überlänge 3 | **Copy kürzen und neu erzeugen** — Tempo darüber klingt gehetzt |
| UNTER-Länge (> 0,6 s Luft vor der nächsten Marke) | **sanft dehnen** bis atempo 0,94 (nie beschleunigen, leicht verlangsamen ist das Werkstatt-Gesetz); ~0,5 s bleiben als Absatz-Atem |

Der Prüfer hört zusätzlich auf SPUR-Ebene: tote Luft > 0,8 s zwischen den Blöcken,
Stimm-Einsatz ± 0,3 s neben seiner Marke, und Stimm-Identität über die ganze Spur
(Gemini-Ohr: same_speaker + Wechsel-Sekunde) — Block-GRÜN allein ist kein FERTIG.

Betonungs-Regel dazu: GROSSSCHREIBUNG lässt v3 jede Stelle zelebrieren und kostet
messbar Zeit — höchstens 1–2 Wörter je Copy in Caps, den Rest trägt die
Emotions-Delivery der Tags.

## Abschluss-Prüfung

- Jeder Block startet exakt auf seiner Zeitmarke (durch `adelay` garantiert, nicht
  nachträglich zu messen).
- Gesamtpegel `loudnorm=I=-16:TP=-1.5` — Social-Plattformen normalisieren sonst selbst.
- Keine Überlappung: Blockende + Startmarke des nächsten prüfen.

## Werkzeug und Emotions-Tags

Die Ausführung läuft über `tools/sp/sprechspur.py` (CWD = Pipeline-Ordner):
`stimme <KÜRZEL>` holt die Brand-Stimme aus dem Register (leer → erst Casting),
`take` erzeugt den EINEN Take, `montage` schneidet an den gemessenen Pausen und
legt die Blöcke per adelay auf ihre Marken, `woerter` schreibt den Wort-Cache
für die Captions (Scribe, de).

Der Take-Text entsteht aus der finalen Copy PLUS den v3-Audio-Tags aus
`_pipeline/emotions_karte.json` (`.claude/skills/speaking-vsl-emotionskarte/SKILL.md`):
Standard ist KEIN Tag — höchstens 1–2 in der GANZEN Copy, nur an Stellen, an denen
die Karte `emotionsstaerke = stark` misst (typisch Hook/CTA); Betonung per
GROSSSCHREIBUNG ebenso sparsam (1–2 Wörter je Copy). Die final-Datei im
Projekt-Ordner bleibt tag-frei — Tags leben nur im Take-Text (`_work/take_text.txt`).

## Der Prüfer ist ein Werkzeug, danach steht ein Gate

`tools/sp/pruefer.py --audio _work/sprechspur.wav --marken <marken.json>` hört
maschinell ab: Rück-Transkription gegen die Soll-Copy (Versprecher, Doppelwörter,
Auslassungen), Pausen > 0,8 s mitten im Block, Fensterzeiten, dazu das
Anker-kalibrierte Gemini-Ohr (Aussprache, Artefakte, Roboter-Stellen). Exit 1 =
rote Zeile → NUR diese Stelle neu erzeugen (Take-Würfel mit gleichem Text und
Tags, an den Pausen der Nachbarblöcke einsetzen), höchstens 3 Versuche, dann
Befund an Viktor.

Nach GRÜN stoppt der Lauf am **Übergangs-Gate Sprechspur-Abnahme**: die Blöcke
als bildboard-Links im Chat zeigen (je Block ein Link + die Prüfer-Zeile),
Viktor hört und sagt „passt" oder gibt Befund je Block. Jeder Befund läuft als
/feedback in den Prüfer oder die Bausteine davor — das Gate trainiert den
Prüfer und fällt weg, sobald mehrere Läufe in Folge ohne Viktor-Befund
durchgehen. Bis dahin geht KEIN Lauf ohne dieses Gate in den Schnitt.
