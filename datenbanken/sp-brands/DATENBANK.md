---
name: sp-brands
typ: CSV (Tabelle)
zweck: Brand-Adressbuch der Speaking-Kette — je Ziel-Brand eine Zeile; löst Kürzel → brands/-Ordner, Sprache, Brand-Wissensdatenbank (AWMS-Hauptordner) und den customClips-Schalter auf. Ersetzt für diese Kette die Linien-Registry der Singing-Kette (Viktors Entscheid: komplett getrennt).
schreibt: die Session beim Anlegen einer neuen Ziel-Brand (mit Viktor)
liest: das Ripping Sheet (Agent-Dialog + Auftrags-Bau, Spalte quell_brands) · der Trigger (Brand bestimmen) · singing-vsl-dach-lokalisierung (Brand-DB-Pfad) · custom-clips (Schalter)
format: daten.csv mit Kopfzeile; je Brand eine Zeile
---
# Brand-Adressbuch — Speaking

Spalten: `kuerzel` (Text, z. B. ROV) · `brand_ordner` (Ordnername unter `brands/`)
· `sprache` (de/fr/…) · `brand_db` (Pfad der Wissensdatenbank im AWMS-Hauptordner)
· `custom_clips` (true/false) · `quell_brands` (Semikolon-Liste der Sheet-Bibliotheken,
aus denen in diese Brand gerippt werden darf, z. B. `quasi;brand-searcher`; leer = jede
Quell-Brand) · `angelegt` (JJJJ-MM-TT).
Neue Brand = neue Zeile (mit Viktor abgestimmt) — kein Code, kein Deploy.

**Ripping Sheet (seit 02.09.2026, Viktors Entscheid):** Das Sheet liest diese Datei bei
jedem Zugriff und bietet die Brands hier im Rip-Dialog unter dem Agenten „🎙 Eleven Labs"
an (Schlüssel `SP:<KÜRZEL>`); der Auftragstext nennt Projektname, Inbox-Pfad und diese
Zeile. `brand_db` muss auf einen EXISTIERENDEN Ordner zeigen — Areum-Steckbrief und
Referenzbilder liegen in `brand-quasi/Product Reference/`, Orelias in `brand-resilia/`
(Stand 02.09.2026; eigene Ordner brand-areum/brand-orelia gibt es noch nicht).
Die Brand-Stimme wohnt NICHT hier, sondern im Stimmen-Register (datenbanken/stimmen).
