---
name: speaking-vsl-emotionskarte
description: "Die Delivery der Original-Stimme einer Speaking-VSL je Copy-Zeile reverse-engineeren (Emotion, Ton, Tempo, betonte Wörter, Pausen) und daraus ElevenLabs-v3-Audio-Tags für die deutschen Zeilen bauen — Schritt der Speaking-Kette zwischen Clip-Karte und Übersetzung. Nutzen, wenn „Emotionen", „Emotions-Karte", „wie spricht das Original", „die Stimme klingt langweilig/emotionslos" fällt."
---

# Emotions-Karte — die Delivery wird gemessen, nie erfunden

ElevenLabs v3 ohne Emotions-Vorgabe hat zwei Ausfallarten: Es wiederholt eine
Emotion über die ganze Spur, oder es würfelt unpassende. Beides klingt sofort
nach Maschine. Der Ausweg ist Reverse-Engineering: Das Original hat jede Zeile
schon einmal richtig gesprochen — diese Delivery wird gemessen und auf die
deutsche Fassung übertragen. Die KI erfindet keine Emotionen, sie überträgt
belegte.

## Eingabe

Alle Pfade vom Pipeline-Ordner des Projekts aus (`brands/<Brand>/<NNN> EL/` — Läufe vor dem 02.09.2026 heißen `<NNN> SP`).

- `_work/source_original.mp4` (oder `source.mp4`) — die Tonspur des Originals.
- Die Copy-Zeilen mit Zeitfenstern: aus dem EN-Transkript des Projekts die
  Blöcke als `_pipeline/emo_bloecke.json` schreiben:
  `[{"t0": 0.08, "t1": 8.48, "en": "Your kidneys never ..."}, ...]`
  (t0 = Start des ersten Worts, t1 = Start des Folgeblocks; Quelle ist das
  Scribe-Roh-JSON).

## Ablauf

1. **Messen:** `~/.venvs/sa/bin/python3 <projektstamm>/tools/sp/emotions_karte.py
   --bloecke _pipeline/emo_bloecke.json` — je Zeile hört das Gemini-Ohr
   (gemini-2.5-flash via kie.ai; Anker-Regel: nur Anker-bestandene Modelle
   dürfen urteilen) den Original-Schnipsel ab und liefert STRICT JSON:
   Emotion, Ton, Tempo, betonte Wörter, Pausen, v3-Tag-Vorschlag aus der
   festen Tag-Liste des Scripts. Exit 1 = mindestens eine Zeile ohne gültiges
   Urteil → diese Zeilen einzeln nachfahren; bleibt es leer, die Zeile ohne
   Tags weitergeben und das im Chat sagen (nie selbst raten).
2. **Plausibilität mit eigenen Augen:** Die Karte gegen die Clip-Karte halten —
   ein „excited" auf einem Angst-Bild (kaputte Niere) ist ein Widerspruch:
   dann gewinnt das, was Bild UND Text stützen, und die Abweichung wird in der
   Karte als `korrektur` notiert.
3. **Auf Deutsch übertragen:** Nach der Übersetzung die Tags den DEUTSCHEN
   Zeilen zuordnen (gleiche Block-Nummer) und betonte Wörter auf ihre
   deutschen Entsprechungen mappen. Ergebnis in
   `_pipeline/emotions_karte.json` ergänzen (Feld `de` + `de_betonung`).
4. **Tags setzen — Standard ist KEIN Tag.** Ein einziges v3-Tag färbt die ganze
   Passage fett („bei v3, wenn du da ein Label reinmachst, ist das fett
   emotional"). Darum bekommt eine Zeile nur dann ein Tag, wenn das Original
   dort WIRKLICH hörbar emotional abweicht (Karte: `emotionsstaerke = stark`) —
   typisch Hook und CTA, fast nie die Erklär-Mitte. Höchstens 1–2 Tags in der
   GANZEN Copy. Alles andere regeln Dynamik und Timing: Tempo, Pausen und
   Fenster-Füllung macht die Montage über die Timestamps, nicht ein Label.
   Betonung einzelner Wörter über GROSSSCHREIBUNG — auch die sparsam
   (höchstens 1–2 Wörter je Copy, Caps kosten messbar Sprechzeit).

## Ausgabe

`_pipeline/emotions_karte.json` — je Zeile: `t0, t1, en, emotion, ton, tempo,
betonte_woerter, pausen, v3_tags, note` (+ nach Schritt 3: `de, de_betonung`,
ggf. `korrektur`). Die FINALE Copy im Projekt-Ordner bleibt tag-frei — Viktors
Gate liest saubere Copy; die Tags konsumiert ausschließlich der Take-Text des
Sprechspur-Baus.

## Fallen

- **Tags gehören in den Take-Text, nie in die final-Datei** — sonst liest die
  Lokalisierung Tags als Copy und der Längen-Check zählt sie als Wörter.
- **Ein Tag wirkt auf das, was NACH ihm kommt.** Tag ans Zeilenende ist wirkungslos.
- **Karaoke-Wortfarben des Originals sind KEIN Emotions-Signal** — die Farben
  wechseln mechanisch je Wort. Nur das Ohr zählt.
