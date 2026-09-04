# Speaking-Kette — Learnings (Konzentrat)

1. **Eine Copy ist EIN Sprechakt.** Ganze Copy in einem Take, an GEMESSENEN Pausen
   schneiden, per adelay auf die Marken — nie blockweise erzeugen (klingt roboterhaft,
   Stimme hört mitten im Satz auf). Beleg: feedback_log 20.08.2026 #5.
2. **Deutscher TTS-Fluss trägt ~2,3 W/s** (Band 2,2–2,5). Budget je Fenster = Sekunden × 2,3;
   Zahl-Komposita kosten extra. Beleg: feedback_log Nebenbefund + Übersetzungs-Skill.
3. **Nur deutsche Muttersprachler-Stimmen** aus der öffentlichen Bibliothek; Wahl wird
   GEMESSEN (Tonhöhen-Variation 25–35 %). Konto-Standardstimmen sind amerikanisch,
   auch wenn „DE verifiziert". Beleg: feedback_log #7.
4. **Emotionen werden reverse-engineert, nie erfunden.** v3 ohne Vorgabe wiederholt
   oder würfelt Emotionen — erst die Original-Delivery je Zeile messen (Emotions-Karte),
   dann als v3-Tags auf die deutschen Zeilen.
5. **ElevenLabs one-shottet nie fehlerfrei.** Prüfer-Loop Pflicht (Rück-Transkription +
   Pausen-Messung + Gemini-Ohr); rote Zeile → nur diese Stelle neu, max. 3 Versuche.
6. **Modell-Liste des Kontos abfragen, nie annehmen** (eleven_v3 lag brach, weil
   multilingual_v2 angenommen wurde). v3 kann kein previous_text — der Ein-Take-Weg
   ersetzt es. Beleg: feedback_log #5.
7. **Ton-Mux ist kein Grund, das Bild anzufassen** — -c:v copy, Frame-Zahl beweist
   Bitgleichheit; Box-Overlay = einzige Encode-Ausnahme (crf 18 + bt709). Beleg: #1/#6.
8. **Copy am Gate immer als EN/DE-Zeilenpaar.** Viktor prüft die deutsche Zeile nur gegen
   das englische Original — eine Copy allein ist „nichts zum Vergleichen". Beleg:
   feedback_log 04.09.2026 #1 (ARE 002 EL).
9. **Szenenerkennung 0,30 ist auf einfarbigen Ads blind.** Auf der rosa Quasi-Ad fehlten
   11 harte Schnitte; Produkt-Fenster per Frame-Differenz (Diff > 18 auf 90×160 Grau)
   nachziehen, sonst bekommt ein Custom-Clip den falschen Start-Frame. Beleg: ARE 002 EL.
10. **Custom-Clips erst NACH der Audio-Prüfung starten.** 14 Clips vor dem Gate kosteten
    ~30 min Wartezeit für Viktor; das Gate braucht nur die Stimmen. Beleg: feedback_log
    04.09.2026 #2.
11. **Einbau frame-genau per Pipe, nicht per trim/concat.** Die Quelle lief 29,93 fps (VFR);
    der ffmpeg-Schnittgraph lieferte 4 Frames zu viel. `_pipeline/custom_einbau.py`
    (ARE 002 EL) reicht die Quelle Frame für Frame durch und tauscht nur die Fenster.
12. **Eingebackene $-Texte in 3D-Szenen im Frame-Edit mitübersetzen** („$210" → „210 €",
    „70% OFF" → „70 % RABATT") — der Edit-Schritt kann Typo; was erst später im Shot
    auftaucht (glühendes „FREE"), wird fette CapCut-Caption. Beleg: ARE 002 EL C02/C06/C11/C27.
