---
name: speaking-vsl-musikbett
description: "Das Instrumental-Bett einer Speaking-VSL aus dem Original gewinnen: Demucs trennt die Original-Tonspur in Stimme und Musik, das Musikbett läuft unter die neue deutsche Sprechspur. Nutzen beim Schnitt der Speaking-Kette oder wenn „Musikbett", „Hintergrundmusik", „die Musik fehlt" fällt."
---

# Musikbett — das Original liefert die Musik

Die bewiesene Ad hat ihre Musik schon: Sie liegt unter der Original-Stimme.
Statt neue Musik zu erzeugen, wird die Original-Tonspur getrennt und das
Instrumental behalten — die Musik-Identität der Vorlage bleibt, nichts muss
komponiert oder lizenziert-geraten werden. In dieser Kette wird KEINE Musik
generiert (kein Suno).

## Ablauf

CWD = Pipeline-Ordner (`brands/<Brand>/<NNN> EL/` — Läufe vor dem 02.09.2026: `<NNN> SP`).

1. **Tonspur ziehen:**
   `ffmpeg -y -v error -i _work/source.mp4 -vn -ar 44100 _work/original_ton.wav`
2. **Trennen (lokal, kein Dienst):**
   `~/.venvs/sa/bin/python3 -m demucs --two-stems=vocals -n htdemucs -o _work/demucs_out _work/original_ton.wav`
   → `_work/demucs_out/htdemucs/original_ton/no_vocals.wav` ist das Bett.
   Bricht Demucs ab (ImportError): Paket im venv `~/.venvs/sa` nachinstallieren.
3. **Als Bett ablegen:** `cp .../no_vocals.wav _work/musikbett.wav`
4. **Rest-Stimme gegenhören (Pflicht):** An 2–3 Stellen, an denen das Original
   spricht, einen Schnipsel des Betts anhören (bildboard-Link) bzw. messen:
   bleibt dort hörbar Original-Sprache stehen, taugt das Bett nicht —
   dann Bett leiser fahren (weiter unter die Sprechspur) oder auf Bett
   verzichten und das im Chat sagen. Ein Bett mit durchscheinender
   US-Stimme ist schlimmer als gar keins.
5. **Pegel:** Das Bett mischt `tools/sp/render.py` mit `--bett-db` unter die
   Sprechspur (Startwert −10 dB). Der richtige Wert wird im Lauf GEGENGEHÖRT
   und der gemessene Wert im Projekt notiert — Sprechverständlichkeit schlägt
   Musik-Präsenz.

## Ausgabe

`_work/musikbett.wav` — Eingabe für `tools/sp/render.py`.
