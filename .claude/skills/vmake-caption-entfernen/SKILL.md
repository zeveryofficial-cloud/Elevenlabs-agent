---
name: vmake-caption-entfernen
description: "Entfernt eingebrannte Captions/Untertitel/Text aus einem Video per Vmake-API (Task videoscreenclear) — inklusive Schlieren-Kontrolle, Song-Remux und ehrlicher Baubarkeits-Bewertung. Nutzen, wenn Viktor sagt „entferne die Captions/den Text aus dem Video", „die englischen Untertitel müssen weg", „nutze Vmake", oder wenn eine Quell-Ad eingebrannten Text trägt, der die deutschen CapCut-Captions stört."
---

# Vmake: eingebrannten Text aus Video entfernen

Zweck: Eingebrannte Captions aus einem Video tilgen, ohne Timing anzufassen. Der
Song/Ton des Projekts bleibt Master: nach einer Render-Bereinigung wird er
drübergemuxt, nach einer Quell-Bereinigung entsteht er ohnehin frisch im Neu-Render.

Werkzeug (ausführen, immer mit `~/.venvs/sa/bin/python3`, Arbeitsverzeichnis =
`_pipeline/`-Ordner des Projekts — dort landet `vmake_state.json`):
`tools/vmake/vmake_client.py` (Pfad relativ zum Projektstamm — dem Ordner, in dem
`.claude/`, `datenbanken/` und `brands/` nebeneinander liegen)
Subkommandos: `config` · `remove <datei|url>` · `poll <task_id>` · `download <ziel>`.
`remove` nutzt fest den Task `videoscreenclear`; der Task-Katalog steht in der
`config`-Ausgabe (relevant erst, wenn der Client um weitere Tasks erweitert wird).
Keys: `VMAKE_AK` + `VMAKE_SK` in `~/.config/leichtkraut/.env` (Access + Secret,
beide nötig — das Verfahren signiert jeden Request).

## Grenze des Verfahrens: gefüllte Flächen hinterlassen Rückstand

`videoscreenclear` ist für Wasserzeichen und dünne Untertitel gebaut. Ein **gefülltes
Gestaltungs-Element** — ein farbiger Titelbalken, ein Preis-Störer, ein Siegel —
überfordert das Inpainting: Die Buchstaben verschwinden, die FLÄCHE dahinter bleibt als
farbiger Keil stehen. Daraus zwei Regeln:

1. **Immer die ERSTEN Frames prüfen, nicht nur eine Stichprobe aus der Mitte.**
   Hero-Titel stehen in Sekunde 0–4; eine Stichprobe ab Frame 30 sieht sie nie.
   `ffmpeg -i _work/vmake_cleaned.mp4 -vf "select='lt(n,6)',tile=6x1" -vsync 0 /tmp/erste.png`
   und ansehen.
2. **Rückstand unter einem Gestaltungs-Element wird ABGEDECKT, nicht wegretuschiert.**
   Nachträgliches `delogo` über eine große Fläche zerstört mehr, als es rettet (eine
   718x270-Box löschte im Test die halbe Animation). Eine ENGE Box um den Rückstand plus
   leichte Glättung ist die Obergrenze — der Rest verschwindet unter dem deutschen Titel,
   der dort ohnehin hinkommt. Genau deshalb ist „Gestaltungs-Text ersetzen" keine Kür,
   sondern die Lösung für den Rückstand.

Bleibt nach zwei Läufen dasselbe Fenster unberührt (Schritt 4b liefert identische
Zeiten), ist ein dritter Lauf verschwendet: Was Vmake nicht erkennt, erkennt es auch
beim Wiederholen nicht. Dann geht der Rückstand als enge Box in den Schnitt.

## Vor dem Entfernen: Textsorten trennen

Nicht jeder Text im Bild ist ein Untertitel. Vor dem Vmake-Lauf die Stellen sichten und
in zwei Listen schreiben — Ablage `_work/gestaltungs-text.md`, Spalten
Zeitfenster · Originalwortlaut · Position (gemessen, in Pixeln des Quellbilds) ·
Vorschlag in der Zielsprache:

- **Sprech-Untertitel** — klein, unteres Drittel, folgen dem Gesprochenen. Werden
  entfernt; die Fassung in der Zielsprache tritt später an ihre Stelle.
- **Gestaltungs-Text** — Hero-Titel, große farbige Typo, Preis-Störer, Endcard. Wird
  ebenfalls entfernt, aber **er MUSS ersetzt werden** und darf nie einfach fehlen. Ohne
  Ersatz beginnt die Ad mit einem stummen Bild und verliert ihren Hook. Die Liste wandert
  an die Captions und an den Schnitt weiter.

Die Position misst man, statt sie zu schätzen: einen Frame als `rgb24` dekodieren, die
Farbfläche des Balkens per Schwelle maskieren und die dichten Zeilen/Spalten als Box
ausgeben — das Ergebnis ist die Box, die der Schnitt später abdeckt.

Erst danach läuft `remove`.

## Das Bild nie unnötig neu encodieren

Wird dem bereinigten Video nur eine Tonspur zugefügt, läuft das Video per **`-c:v copy`** —
Stream-Copy, kein Neu-Encode. Jede zusätzliche h264-Generation frisst zuerst die Farbe,
sichtbar an gesättigten Rot- und Orangetönen: Sie sind chroma-unterabgetastet (yuv420p)
und brechen als Erstes in Streifen und Säume auf — genau dort, wo Schmerz-Glow, Blut und
Warnfarben sitzen. Regel: **Ein Ton-Mux ist kein Grund, das Bild anzufassen.** Nur wenn
wirklich in die Pixel gegriffen wird (Overlay, Crop, Skalierung), wird encodiert — dann
mit `-crf 18` oder besser und immer mit den bt709-Tags auf Container-Ebene.

Gegenprobe vor dem Ausliefern: `ffprobe -select_streams v:0 -show_entries stream=nb_frames`
auf Eingabe und Ausgabe. Gleiche Frame-Zahl UND Stream-Copy = das Bild ist bitgleich, es
KANN keine neuen Artefakte tragen. Das beantwortet auch die Rückfrage „kommen die Streifen
von Vmake?" ohne Raterei.

## Vorgehen

1. **Caption-Stellen des Originals festhalten:** Schlieren-Scan (Schritt 4) einmal auf
   dem UNBEREINIGTEN Video laufen lassen — seine Regionen-Liste (Sekunden-Spannen)
   sind die Caption-Stellen für alle späteren Vorher/Nachher-Vergleiche.
2. **Welche Datei bereinigen?** Standard: die QUELLE (`_work/source.mp4`), NICHT der
   fertige Render. Grund (gemessen): Video-Inpainting nutzt Nachbar-Frames; der fertige
   Schnitt hat alle paar Sekunden harte Cuts und liefert schlechten Kontext — auf der
   glatten Quelle rekonstruiert Vmake sichtbar besser. Den Render direkt zu bereinigen
   ist die Ausweich-Route, wenn keine Quelle existiert.
3. **Entfernen:** `remove <datei>` — lädt selbst zu Vmakes OSS hoch (fremde Hosts wie
   litterbox erreichen deren China-Server NICHT: „Video Download Error") und startet
   den Task. `poll <task_id>` wiederholen, bis FERTIG oder FEHLGESCHLAGEN gedruckt
   wird — die gemeldete `predict_elapsed`-Schätzung ist viel zu optimistisch (~84 s
   gemeldet, >10 min real bei ~5-min-Videos). Nach 45 min ohne Terminal-Status oder
   bei FEHLGESCHLAGEN: einmal neu einreichen; scheitert auch das, Viktor mit der
   Fehlermeldung stoppen (häufig: Quota leer — steht in der CONSUME-Antwort).
   Ergebnis: `download _work/vmake_cleaned.mp4`.
4. **Schlieren-Scan + Sichtung (Pflicht):** Vmakes bekannte Schwäche sind helle
   Karaoke-Highlight-Boxen — dort hinterlässt das Inpainting weiße Leucht-Schlieren.
   Der Scan dekodiert das ganze Video und läuft mit dem Rechen-venv:
   `~/.venvs/sa/bin/python3 tools/vmake/schlieren_scan.py <video.mp4> 30`
   (Exit 0 = Band ruhig, Exit 1 = Regionen-Liste als `a–b s`-Zeilen; ImportError =
   fehlendes Paket im venv nachinstallieren). Der Scan ist ein VORFILTER: Er misst
   Helligkeit und verwechselt darum helle Produkt-Shots mit Schlieren — die gemeldeten
   Regionen werden angesehen, nicht geglaubt. Dann ANSEHEN — je auffälliger Region UND
   je 2–3 Original-Caption-Stellen aus Schritt 1:
   `ffmpeg -ss <Sekunde> -i _work/vmake_cleaned.mp4 -frames:v 1 -vf "crop=iw:ih*0.30:0:ih*0.54,scale=iw*2:ih*2" /tmp/check_<Sekunde>.png`
   und die PNGs mit dem Read-Werkzeug öffnen. So beantwortet EIN Blick beides:
   Text weg? Schlieren da?

4b. **Rest-Karten messen statt schätzen.** Ob wirklich alles weg ist, entscheidet nicht
   der Blick auf drei Stichproben, sondern der Vergleich Frame für Frame: Wo Vmake
   gearbeitet hat, unterscheidet sich das Caption-Band vom Original; wo es NICHTS getan
   hat, ist der Unterschied null — und dort steht das englische Wort noch. Beide Videos
   klein dekodieren (`scale=180:320`, `-pix_fmt gray`), je Frame den mittleren Betrag der
   Differenz im Band y 64–86 % rechnen und die Frames mit Differenz < 0,6 zu Zeit-Fenstern
   clustern. Ausgabe: Zahl der unberührten Frames + die Fenster in Sekunden. Diese Fenster
   sind der Befund für Schritt 5 — mit Sekunden, nicht mit „sieht sauber aus".

5. **Befund ehrlich bewerten:** Text weg + Band ruhig → sauber, weiter. Text weg, aber
   Leucht-Schlieren → Viktor die Wahl zeigen (überdecken lassen / Quelle-zuerst-Weg /
   lokale Nachbearbeitung, als A/B-Varianten) — nicht still durchwinken. Text NICHT
   weg → Task einmal neu einreichen; liefert Schritt 4b danach dieselben unberührten
   Fenster, ist es kein Zufall — Befund mit Crops UND Sekunden an Viktor, und der
   Rückstand geht als enge Box in den Schnitt statt in einen dritten Vmake-Lauf.
6. **Weiterverarbeiten je Zweig:**
   - **Quelle bereinigt:** Original sichern als `_work/source_original.mp4`, dann
     `vmake_cleaned.mp4` → `_work/source.mp4`. Frame-Zahl muss stimmen:
     `ffprobe -count_frames -select_streams v:0 -show_entries stream=nb_read_frames`
     gegen Feld `frames` in `_pipeline/sa_config.json` (legt der Bootstrap an).
     Dann den Renderer des Projekts neu laufen lassen: `_pipeline/render<NNN>.py`
     (der Frame-Map-Renderer; liest `_pipeline/cutlist<NNN>.json` — die bleibt gültig,
     weil Frames/fps identisch sind — und schreibt die finale MP4 samt Song-Ton und
     Farb-Tags selbst). Er rechnet auf dem Hetzner-Worker: seine Eingaben
     (`render<NNN>.py`, `cutlist<NNN>.json`, `sa_config.json`, `_work/source.mp4`,
     `../song/song<NNN>.wav`) mit gespiegelter Ordnerstruktur nach
     `/work/kollege/<slug>/` syncen, dort laufen lassen, die finale MP4 sofort
     zurücksyncen (Muster + Erfolgskriterien:
     `.claude/skills/sa-resync-singing-ad/SKILL.md` §Rechenort); meldet das Log
     dort eine fehlende Datei, den genannten Pfad nachsyncen und erneut starten.
   - **Render bereinigt:** Song-Master (`../song/song<NNN>.wav`) als einzige Tonspur
     drübermuxen: `ffmpeg -i _work/vmake_cleaned.mp4 -i ../song/song<NNN>.wav -map 0:v
     -map 1:a -c:v copy -c:a aac -b:a 192k -color_primaries bt709 -color_trc bt709
     -colorspace bt709 -color_range tv -movflags +faststart -shortest <final.mp4>`.
     Der `-shortest`-Mux darf genau 1 Endframe kosten (liegt im Fade-out) — mehr ist
     ein Befund. Farb-Tags dabei NUR auf Container-Ebene (wie im Kommando); den
     Bitstream-Filter `h264_metadata` auf Vmake-Ausgaben NIE anwenden — er scheitert
     an deren SEI-Einheiten und wirft still Pakete weg (gemessen: 6751 statt 8838
     Frames, Datei unbrauchbar).
7. **Abschluss-Beweis:** Frame-Zahl + Dauer per ffprobe; beim Remux-Zweig zusätzlich
   A/V-Sync per Kreuzkorrelation Song↔Mux-Audio an ≥3 Zeitpunkten (soundfile +
   numpy.correlate auf 2-s-Fenstern; Offset ~0 ms erwartet); /watch-Stichprobe an den
   Caption-Stellen aus Schritt 1. Verbrauch buchen: eine Zeile an
   `/root/AWMS/.usage/direkt.jsonl` anhängen, Format:
   `{"ts":"<ISO-Zeit>","workflow":"<Workflow-Name>","anbieter":"vmake","menge":<Anzahl Tasks>,"notiz":"<Kurzbeschreibung>"}`.

## Gotchas

- `remove` mit http(s)-URL überspringt den OSS-Upload — funktioniert nur mit URLs, die
  aus China erreichbar sind. Im Zweifel lokalen Pfad geben.
- Vmake re-encodiert das Video (Dateigröße/Bitrate ändern sich, Frames/fps bleiben) —
  deshalb dem Vmake-Ton nie trauen; der Ton kommt immer aus dem Song-Master.
- Der Scan ist ein VORFILTER: Helligkeit verwechselt Schlieren mit legitim hellen
  Szenen (Produkt-Shots, Fenster) — entscheiden tun die Crops, nie die Zahl allein.
