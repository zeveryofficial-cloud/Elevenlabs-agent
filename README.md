# Elevenlabs agent

Der **Eleven Labs Ripping Agent**: ein AWMS-Workflow, der aus einer gesprochenen Longform-VSL
eine deutsche Fassung mit ElevenLabs-Sprechstimme baut — Transkript, Clip-Karte, Übersetzung in
Sprech-Budgets, DACH-Lokalisierung, Sprechspur (ein Take, an gemessenen Pausen geschnitten),
Prüfer-Loop, Musikbett per Demucs aus dem Original, Custom Clips mit dem eigenen Produkt,
Abnahme mit Zahlen, Captions-Paket für CapCut.

Die Workflow-Datei ist die Arbeitsanweisung: `workflows/eleven-labs-ripping-agent.json`
(Knoten = Skills, Tools, Datenbanken, Gates; Kanten = Reihenfolge und Lese-/Schreibzugriffe).
Eine KI arbeitet sie Knoten für Knoten ab, stoppt an den Mensch-Gates (Audio-Prüfung,
CapCut-Sichtung) und liest/schreibt die Datenbanken laut Kanten.

| Ordner | Inhalt |
|---|---|
| `workflows/` | die Workflow-Datei |
| `.claude/skills/` | die Skills der Kette (Prozeduren als SKILL.md, teils mit Scripts) |
| `tools/sp/` | Werkzeugkasten der Sprech-Kette: Bootstrap, Clip-Karte, Emotions-Karte, Sprechspur, Prüfer, Render, Abnahme, CapCut-Paket |
| `tools/vmake/` | Caption-Entfernung (Vmake-API) + Schlieren-Scan |
| `datenbanken/` | die Verträge der Datenbanken (`DATENBANK.md`) und CSV-Kopfzeilen — ohne Daten |

Nicht enthalten: Projekte, Brand-Wissen, Schlüssel (`~/.config/awms/.env`), das Ripping Sheet
und der Meta-Uploader (eigene Software im AWMS-Hauptprojekt).

Voraussetzungen: Python-Umgebung `~/.venvs/sa` (ffmpeg, demucs, numpy, soundfile); Dienste
ElevenLabs (TTS + Scribe), Vmake, kie.ai (Gemini-Ohr), Kling-CLI (Custom Clips).
