#!/usr/bin/env python3
"""Sprechspur-Bau — HIER wird ElevenLabs generiert (v3 + Audio-Tags).

Gesetz (gemessen): Eine Copy ist EIN Sprechakt — ganzer Take, dann an den
GEMESSENEN Pausen schneiden und per adelay auf die Zeitmarken legen. Blockweise
Erzeugung klingt roboterhaft (Schlussmelodie in jedem Block). v3 kann kein
previous_text — der Ein-Take-Weg ersetzt es.

CWD = Pipeline-Ordner. Subkommandos:
  stimme <KÜRZEL>                          → Register-Zeile zeigen (Fehler, wenn leer → Casting)
  take --text <take.txt> --kuerzel ROV [--out _work/take.mp3]
        take.txt = die Copy MIT v3-Tags in eckigen Klammern, Blöcke durch Leerzeile
  montage --take _work/take.mp3 --marken <marken.json> [--out _work/sprechspur.wav]
        marken.json = [{"start":0.08,"ende":8.48,"text":"..."}, ...] (SOLL-Fenster je Block)
  woerter --audio _work/sprechspur.wav     → _pipeline/sprech_words.json (Scribe, de)
Tempo-Gesetz der Montage: Überlänge ≤10 % → atempo; 10–15 % nur bei ruhigen
Blöcken; darüber Abbruch mit Kürzungs-Auftrag — nie schneller als 1,15.
"""
import argparse, csv, json, os, re, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

BASIS = os.getcwd()
STAMM = Path(__file__).resolve().parents[2]
REGISTER = STAMM / "datenbanken" / "stimmen" / "daten.csv"

def key():
    for pfad in (Path.home()/".config"/"awms"/".env", Path.home()/".config"/"leichtkraut"/".env"):
        if pfad.exists():
            for z in pfad.read_text().splitlines():
                if z.startswith("ELEVENLABS_API_KEY="): return z.split("=",1)[1].strip()
    sys.exit("ELEVENLABS_API_KEY fehlt — Viktor fragen, nie auf andere Keys ausweichen.")

def stimme(kuerzel):
    with open(REGISTER, encoding="utf-8") as f:
        treffer = [r for r in csv.DictReader(f) if r["marke"].strip().upper() == kuerzel.upper()]
    if len(treffer) > 1:
        sys.exit(f"Stimmen-Register hat {len(treffer)} Zeilen für {kuerzel} — eine Marke, eine "
                 f"Stimme. Erst aufräumen (die ERSTE Casting-Zeile gilt), dann weiter.")
    if treffer: return treffer[0]
    sys.exit(f"Stimmen-Register hat keine Zeile für {kuerzel} — erst Stimm-Casting "
             f"(speaking-vsl-stimm-casting) oder Viktors Stimme eintragen.")

def cmd_take(a):
    if a.voice_id:
        # Experiment-Weg (z. B. Voice-Design-Test): Stimme direkt, Register unangetastet
        r = {"voice_id": a.voice_id, "name": a.voice_name or a.voice_id,
             "modell": "eleven_v3", "stability": "0.5", "similarity_boost": "0.75", "style": "0.0"}
    else:
        r = stimme(a.kuerzel)
    text = Path(a.text).read_text(encoding="utf-8").strip()
    einst = {"stability": float(r["stability"] or 0.5)}
    if r.get("similarity_boost"): einst["similarity_boost"] = float(r["similarity_boost"])
    if r.get("style"): einst["style"] = float(r["style"])
    body = {"text": text, "model_id": r["modell"] or "eleven_v3", "voice_settings": einst}
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{r['voice_id']}?output_format=mp3_44100_192",
        data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": key(), "Content-Type": "application/json"})
    for versuch in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as antwort:
                Path(a.out).write_bytes(antwort.read()); break
        except urllib.error.HTTPError as e:
            fehler = e.read().decode()[:400]
            if versuch == 2: sys.exit(f"ElevenLabs {e.code}: {fehler}")
    d = dauer(a.out)
    print(f"Take OK → {a.out} · {d:.2f}s · Stimme {r['name']} ({r['voice_id']}) · {body['model_id']}")

def dauer(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                                 "-of","csv=p=0",p],capture_output=True,text=True).stdout.strip())

def pausen(p, noise="-32dB", mind=0.18):
    out = subprocess.run(["ffmpeg","-i",p,"-af",f"silencedetect=noise={noise}:d={mind}","-f","null","-"],
                         capture_output=True, text=True).stderr
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start: ([\d.]+)", out)]
    enden  = [float(m.group(1)) for m in re.finditer(r"silence_end: ([\d.]+)", out)]
    return [( s, e ) for s, e in zip(starts, enden)]

def _take_woerter(take):
    """Scribe-Wortzeiten des Takes (de) — die exakte Schnitt-Grundlage."""
    import tempfile
    roh = tempfile.mktemp(suffix=".json")
    script = STAMM/".claude"/"skills"/"singing-vsl-transkription"/"scripts"/"transcribe.py"
    r = subprocess.run([sys.executable,str(script),take,"--out",roh,"--sprache","de"],
                       capture_output=True,text=True)
    if r.returncode != 0: return None
    d = json.loads(Path(roh).read_text()); os.remove(roh)
    return [{"w":w["text"],"s":w["start"],"e":w["end"]} for w in d["woerter"]]

def _norm_w(s):
    return [w for w in re.sub(r"[^a-zäöüß0-9 ]"," ",s.lower()).split() if w]

def cmd_montage(a):
    marken = json.load(open(a.marken))
    take_d = dauer(a.take)
    paus = pausen(a.take)
    grenzen = None
    tw = _take_woerter(a.take)
    if tw:
        # Präziser Weg: Soll-Wortstrom gegen gehörten Wortstrom alignen (difflib),
        # Blockgrenze = Mitte zwischen letztem Wort des Blocks und erstem des nächsten.
        import difflib
        soll_woerter, soll_grenzidx = [], []
        for m in marken:
            soll_woerter += _norm_w(m["text"]); soll_grenzidx.append(len(soll_woerter))
        hoer = [x for w in tw for x in _norm_w(w["w"])]
        hoer_map = []   # Index im hoer-Strom → tw-Index
        for i,w in enumerate(tw): hoer_map += [i]*len(_norm_w(w["w"]))
        sm = difflib.SequenceMatcher(None, soll_woerter, hoer)
        abb = {}
        for b in sm.get_matching_blocks():
            for k in range(b.size): abb[b.a+k] = b.b+k
        grenzen = [0.0]
        for gi in soll_grenzidx[:-1]:
            links = max((v for s,v in abb.items() if s < gi), default=None)
            rechts = min((v for s,v in abb.items() if s >= gi), default=None)
            if links is None or rechts is None: grenzen = None; break
            t_l = tw[hoer_map[links]]["e"]; t_r = tw[hoer_map[rechts]]["s"]
            grenzen.append((t_l + t_r) / 2)
        if grenzen: grenzen.append(take_d)
    if not grenzen:
        # Ausweichweg: Pause, die dem Zeichenanteil am nächsten liegt
        ges_zeichen = sum(len(m["text"]) for m in marken)
        grenzen = [0.0]; acc = 0
        for m in marken[:-1]:
            acc += len(m["text"])
            soll = take_d * acc / ges_zeichen
            if not paus: sys.exit("Keine Sprechpausen gemessen — Take prüfen (durchgehend Ton?).")
            beste = min(paus, key=lambda p: abs((p[0]+p[1])/2 - soll))
            grenzen.append((beste[0]+beste[1])/2)
        grenzen.append(take_d)
        print("Hinweis: Scribe-Alignment nicht möglich — Zeichen-Anteils-Schnitt benutzt.")
    teile = []
    protokoll = []
    for i, m in enumerate(marken):
        t0, t1 = grenzen[i], grenzen[i+1]
        fenster = m["ende"] - m["start"]
        teil = f"{BASIS}/_work/block_{i:02d}.wav"
        # Rand-Stille wegtrimmen (der Schnitt liegt in Pausen-MITTEN — ohne Trim beginnt
        # jeder Block mit halber Take-Pause und die Marke verfehlt den Stimm-Einsatz)
        trim=("silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,"
              "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.08,areverse")
        subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{t0:.3f}","-to",f"{t1:.3f}",
                        "-i",a.take,"-af",trim,"-ar","44100","-ac","2",teil], check=True)
        blockdauer = dauer(teil)
        # Eskalations-Leiter bei Überlänge: (1) Pausen quetschen — v3 legt mit Tags
        # theatralische Pausen, die Wörter bleiben unberührt; (2) atempo bis 1,10;
        # (3) darüber ist die Copy zu lang → kürzen, nie hetzen.
        if blockdauer > fenster:
            gequetscht = f"{BASIS}/_work/block_{i:02d}_sq.wav"
            subprocess.run(["ffmpeg","-y","-v","error","-i",teil,"-af",
                "silenceremove=stop_periods=-1:stop_duration=0.40:stop_threshold=-35dB:stop_silence=0.32",
                gequetscht], check=True)
            neu_d = dauer(gequetscht)
            if neu_d < blockdauer - 0.05:
                os.replace(gequetscht, teil)
                protokoll.append(f"Block {i}: Pausen {blockdauer:.2f}→{neu_d:.2f}s")
                blockdauer = neu_d
            else:
                os.remove(gequetscht)
        if blockdauer > fenster:
            faktor = blockdauer / fenster
            if faktor > 1.15:
                sys.exit(f"Block {i} ist {blockdauer:.2f}s für ein {fenster:.2f}s-Fenster "
                         f"(x{faktor:.2f}, nach Pausen-Quetsche) — Copy kürzen und neu erzeugen.")
            getempt = f"{BASIS}/_work/block_{i:02d}_at.wav"
            subprocess.run(["ffmpeg","-y","-v","error","-i",teil,"-af",
                            f"atempo={min(faktor,1.15):.4f}",getempt], check=True)
            os.replace(getempt, teil)
            protokoll.append(f"Block {i}: atempo {faktor:.3f}")
        elif i < len(marken)-1 and blockdauer < fenster - 0.6:
            # UNTER-Länge: tote Luft > 0,6 s vor der nächsten Marke — sanft dehnen
            # (Gesetz der Werkstatt: nie beschleunigen, leicht verlangsamen erlaubt),
            # Untergrenze 0,94; der Rest bleibt als natürlicher Absatz-Atem stehen.
            ziel = fenster - 0.5
            faktor = max(blockdauer / ziel, 0.94)
            if faktor < 0.999:
                getempt = f"{BASIS}/_work/block_{i:02d}_at.wav"
                subprocess.run(["ffmpeg","-y","-v","error","-i",teil,"-af",
                                f"atempo={faktor:.4f}",getempt], check=True)
                os.replace(getempt, teil)
                protokoll.append(f"Block {i}: gedehnt {faktor:.3f} (Luft {fenster-blockdauer:.2f}s)")
        teile.append((teil, m["start"]))
    ein = []; filt = []
    for i,(teil, start) in enumerate(teile):
        ein += ["-i", teil]
        filt.append(f"[{i}]adelay={int(start*1000)}|{int(start*1000)}[d{i}]")
    filt.append("".join(f"[d{i}]" for i in range(len(teile))) +
                f"amix=inputs={len(teile)}:normalize=0,loudnorm=I=-16:TP=-1.5[out]")
    subprocess.run(["ffmpeg","-y","-v","error"]+ein+["-filter_complex",";".join(filt),
                    "-map","[out]","-ar","44100",a.out], check=True)
    for t,_ in teile: os.remove(t)
    print(f"Montage OK → {a.out} · {dauer(a.out):.2f}s · Schnitte {[round(g,2) for g in grenzen[1:-1]]}"
          + (" · " + " · ".join(protokoll) if protokoll else ""))

def cmd_woerter(a):
    script = STAMM/".claude"/"skills"/"singing-vsl-transkription"/"scripts"/"transcribe.py"
    r = subprocess.run([sys.executable, str(script), a.audio, "--out",
                        f"{BASIS}/_pipeline/sprech_words_roh.json", "--sprache","de"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Scribe-Wortcache scheiterte:\n{r.stderr[-400:]}")
    d = json.loads(open(f"{BASIS}/_pipeline/sprech_words_roh.json").read())
    words=[{"w":w["text"],"s":round(w["start"],2),"e":round(w["end"],2)} for w in d["woerter"]]
    json.dump({"language":"de","words":words}, open(f"{BASIS}/_pipeline/sprech_words.json","w"),
              ensure_ascii=False)
    print(f"Wort-Cache: {len(words)} Wörter → _pipeline/sprech_words.json")

ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("stimme"); s.add_argument("kuerzel")
t = sub.add_parser("take"); t.add_argument("--text",required=True); t.add_argument("--kuerzel",required=True); t.add_argument("--out",default="_work/take.mp3"); t.add_argument("--voice-id"); t.add_argument("--voice-name")
m = sub.add_parser("montage"); m.add_argument("--take",default="_work/take.mp3"); m.add_argument("--marken",required=True); m.add_argument("--out",default="_work/sprechspur.wav")
w = sub.add_parser("woerter"); w.add_argument("--audio",default="_work/sprechspur.wav")
a = ap.parse_args()
if a.cmd=="stimme": print(json.dumps(stimme(a.kuerzel), ensure_ascii=False, indent=1))
elif a.cmd=="take": cmd_take(a)
elif a.cmd=="montage": cmd_montage(a)
elif a.cmd=="woerter": cmd_woerter(a)
