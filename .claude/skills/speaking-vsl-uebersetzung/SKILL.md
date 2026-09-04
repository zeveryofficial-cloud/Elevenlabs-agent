---
name: speaking-vsl-uebersetzung
description: "Ein englisches VSL-Transkript in deutsche Sprech-Copy übersetzen, die in ihre Original-Zeitfenster passt — Budget je Clip in Wörtern pro Sekunde gerechnet, Hook-Mechanik erhalten, Produktnamen unangetastet. Vierter Schritt der Speaking-VSL-Kette zwischen Clip-Karte und DACH-Lokalisierung; auch nutzen, wenn Viktor sagt „übersetz die Copy", „mach die deutsche Fassung", „Sprech-Budgets", „passt das in die Zeit?"."
---

# Speaking VSL Übersetzung — die Zeit ist die Grenze

Anders als bei Text-Copy gibt es hier eine harte Wand: Jede deutsche Zeile muss in
das Zeitfenster ihres Original-Clips passen. Deutsch ist beim Sprechen länger als
Englisch — wer eins zu eins übersetzt, produziert eine Spur, die den Schnitt sprengt
oder die Stimme hetzen lässt. Darum wird nicht satzweise übersetzt, sondern
**fensterweise gegen ein Budget**.

## Eingabe

Alle Pfade vom Projektstamm aus (der Ordner mit `.claude/` und `datenbanken/`).

- Das englische Transkript `<projekte-db>/<projekt>/<slug>-original-<JJJJ-MM-TT>.md`
- Die Clip-Karte aus `singing-vsl-clip-karte` — sie liefert die Fenstergrenzen.
  Fehlt sie, sind die `(M:SS)`-Stempel des Transkripts die Fenster.
- Fehlt eins von beidem: bei Viktor erbitten und stoppen. Nie aus dem Gedächtnis.

## Das Budget

**Deutscher TTS-Sprechfluss trägt 2,2–2,5 Wörter pro Sekunde.** Darunter klingt es
zäh, darüber hetzt die Stimme und die Captions laufen dem Bild davon.

Das Band ist gemessen, nicht geschätzt: Eine deutsche ElevenLabs-Stimme trug in
einem vollen Lauf real 2,3 W/s; wer mit 2,6–3,2 W/s plant, produziert rund 20 %
Überlänge. Andere Stimmen können abweichen: im Zweifel EINEN Block erzeugen, messen,
und das Band für diesen Lauf daraus ableiten — das kostet 20 Sekunden und spart einen
kompletten Neu-Durchgang.

Je Fenster: `Sekunden × 2,3` = Ziel-Wortzahl. Beim Bau grob dagegen zählen, am Ende
exakt. Ein Fenster über 2,5 W/s wird gekürzt — nicht die Sprechgeschwindigkeit erhöht.

**Zahlwörter zählen als Wörter, sprechen sich aber wie Sätze.** „12-Milligramm-Astaxanthin"
ist EIN Wort in der Zählung und sechs Silben im Ohr. Trägt ein Fenster Zahlen, Einheiten
oder Komposita, wird sein Budget um ein Wort je zusammengesetztem Zahlwort gesenkt —
sonst sitzt die Tabelle und die Spur läuft trotzdem über.

Gekürzt wird in dieser Reihenfolge:
1. **Füllwörter und Doppelungen** („ganz", „wirklich", „auch")
2. **Relativsätze zu Nominalphrasen** („das Taubheitsgefühl, das dich kaum laufen
   lässt" → „das Taubheitsgefühl beim Laufen") — spart am meisten, kostet am wenigsten
3. **Kurzformen** („Operation" → „OP", spart zwei Silben)
4. **Erst zuletzt** ein Nebenargument streichen — und das im Anmerkungs-Teil ausweisen

## Das erste Gesetz: natürlich fließen schlägt Strukturtreue

Die Singing-Linie übersetzt strukturgleich am englischen Satzbau entlang (1:1-Optik,
damit die Clips hart am Original geschnitten werden können). **Diese Regel gilt hier
NICHT.** In der Speaking-Kette ist die Stimme formbar (Clip vor Audio — die Sprechspur
passt sich den Clips an), also entscheidet der deutsche SPRACHFLUSS: Sätze so bauen,
wie ein Muttersprachler sie sagen würde, nicht wie das Englische sie gebaut hat.
Wörtlichkeit ist nur Mittel, nie Ziel.

Referenzpaar (aus echtem Gate-Befund — die linke Fassung fiel durch):
- ✗ strukturnah: „Deine Nieren warnen nie. Melden sie sich, ist es zu spät."
- ✓ natürlich: „Deine Nieren geben dir nie Warnsignale. Aber wenn sie es tun,
  dann ist es zu spät."

Prüf-Frage je Zeile: Würde eine deutsche Sprecherin das GENAU SO sagen? Klingt eine
Zeile nach Übersetzung, wird sie umgebaut — das Budget wird danach geprüft, nicht
als Ausrede fürs Verknappen auf Kosten des Flusses benutzt.

## Die vier Gesetze

1. **Hook-Mechanik schlägt Wörtlichkeit.** Ein Negations-Hook („Do not try X if you
   have Y") ist eine getarnte Empfehlung. Wörtlich übersetzt kippt er ins echte
   Abraten. Übersetzt wird die MECHANIK, nicht der Satz.
2. **Produkt- und Markennamen bleiben unangetastet.** Der Tausch ist Sache der
   Lokalisierung — hier steht noch der Name der Quelle.
3. **Beträge bleiben in der Quellwährung.** Die Euro-Umstellung ist eine stehende
   Entscheidung der Lokalisierung, keine Übersetzungs-Aufgabe.
4. **Fachbegriffe nach Sprechbarkeit wählen, nicht nach Präzision.** „rehydrate your
   discs" → „befeuchtet die Bandscheiben"; „rehydrieren" ist näher, klingt aber
   gesprochen nach Beipackzettel.

Anrede ist **Du** — Gattung ist „Frau erzählt Frau". Figuren innerhalb der Story
behalten das Register ihrer Szene.

## Ausgabe

`<projekte-db>/<projekt>/<slug>-uebersetzung-<JJJJ-MM-TT>.md`, und vollständig im Chat
zeigen. Aufbau:

1. **Kopfzeile** — Vorlage, Sprache-Budget gesamt, Stand
2. **Die Copy als ZWEI BLÖCKE, nie verschachtelt:** zuerst ein Block mit allen
   englischen Original-Zeilen (Überschrift `## Original (EN)`), darunter ein Block mit
   allen deutschen Zeilen (Überschrift `## Deutsch (Sprech-Copy)`). Beide Blöcke tragen
   dieselben `(M:SS)`-Stempel in derselben Reihenfolge — so findet das Auge jede Zeile
   im anderen Block über den Stempel. Nur die deutschen Zeilen beginnen mit `(`, damit
   der Längen-Check sie zählt; die englischen stehen unter ihrer eigenen Überschrift.
   Grund: Viktor vergleicht am Gate Original und Übersetzung — eine deutsche Copy allein
   ist für ihn nicht prüfbar, und zeilenweise verschachtelte EN/DE-Paare werden bei zwölf
   Blöcken zu einer unlesbaren Wand. Dasselbe Zwei-Block-Format gilt für jede Copy-Anzeige
   im Chat bis zur Audio-Prüfung (dort als zwei Code-Blöcke).
   Die Clip-Bindung (`Cxxx-Cyyy` je Block) steht als eigene Zeile unter den Blöcken, nicht
   in den Copy-Zeilen.
3. **Budget-Kontrolle** — Tabelle je Clip: Fenster · Sekunden · EN-Wörter ·
   DE-Wörter · W/s · sitzt ja/nein. Ein Fenster am Rand bekommt eine konkrete
   Kürzungs-Alternative als Fließtext darunter, keine vage Warnung.
4. **Übersetzer-Entscheidungen** — je Entscheidung ein Stichpunkt mit Begründung.
   Hier gehören Hook-Mechanik, Kurzformen, Fachbegriff-Wahl und alles hinein, was
   ein späterer Leser sonst für einen Fehler halten würde.
5. **Anmerkungen an die Lokalisierung** (optional) — was dort geprüft werden muss:
   kulturelle Anker, Zahlen mit Marktbezug, Produktfakten ohne Beleg. Die
   Lokalisierung liest diesen Abschnitt als Pflicht-Input.

Danach übernimmt `singing-vsl-dach-lokalisierung`.

## Fallen aus echten Läufen

- **Kurze Fenster sind gefährlicher als lange.** Ein 4-Sekunden-Fenster verzeiht kein
  einziges Wort zu viel; ein 10-Sekunden-Fenster schluckt zwei. Zuerst die kurzen bauen.
- **Aufzählungen sind der beste Kürzungs-Hebel.** „bei ausstrahlenden Beinschmerzen,
  bei steifem unterem Rücken, und bei diesem Taubheitsgefühl" → „bei Beinschmerzen,
  steifem Rücken, diesem Taubheitsgefühl": dreimal die Präposition gespart, Inhalt
  vollständig erhalten.
- **Der Gesamtschnitt lügt.** 2,9 W/s über die ganze Ad kann ein Fenster mit 3,6
  verstecken. Immer je Fenster prüfen, nie nur gesamt.
