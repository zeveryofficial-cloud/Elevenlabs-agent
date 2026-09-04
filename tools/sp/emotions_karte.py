#!/usr/bin/env python3
"""Emotions-Karte: die Delivery der ORIGINAL-Stimme je Copy-Zeile reverse-engineeren.

Warum: ElevenLabs v3 ohne Vorgabe wiederholt oder würfelt Emotionen. Also wird
zuerst gemessen, WIE das Original jede Zeile spricht (Emotion, Ton, Tempo,
betonte Wörter, Pausen), und daraus je Zeile ein v3-Audio-Tag-Vorschlag gebaut.
Ohr ist gemini-2.5-flash via kie.ai — das Modell, das den Audio-Anker bestand
(Anker-Regel: nur Anker-bestandene Modelle dürfen urteilen; pro reicht kein
Audio durch).

CWD = Pipeline-Ordner. Aufruf:
  python3 emotions_karte.py --bloecke <bloecke.json>
bloecke.json: [{"t0":0.08,"t1":8.48,"en":"Your kidneys ..."} , ...]
Ausgabe: _pipeline/emotions_karte.json (je Zeile Analyse + v3_tags).
Exit 1, wenn eine Zeile kein gültiges JSON liefert (Rest wird trotzdem gespeichert).
"""
import argparse, base64, json, os, subprocess, sys, time
from pathlib import Path

BASIS = os.getcwd()
GURL = "https://api.kie.ai/gemini-2.5-flash/v1/chat/completions"
TAGS = ["whispers","sighs","excited","angry","stern","serious","warm","reassuring",
        "urgent","sarcastic","curious","confident","calm","dramatic","emphatic"]

def key():
    for z in (Path.home()/".config"/"awms"/".env").read_text().splitlines():
        if z.startswith("KIE_API_KEY="): return z.split("=",1)[1].strip()
    sys.exit("KIE_API_KEY fehlt in ~/.config/awms/.env")

PROMPT = ("You hear one line from an English direct-response health ad, spoken by its narrator. "
 "Judge ONLY the vocal delivery of this audio (not the content). Line text: «{en}». "
 "Most ad narration is professionally NEUTRAL — flag emotion only when the delivery "
 "clearly departs from neutral narration. Answer STRICT JSON, nothing else: "
 '{{"emotion":"<primary emotion, 1-3 words>","ton":"<tone of voice, 1-3 words>",'
 '"emotionsstaerke":"neutral/leicht/stark",'
 '"tempo":"slow/medium/fast","betonte_woerter":["<words the voice stresses>"],'
 '"pausen":"<none or where the voice pauses, max 8 words>",'
 '"v3_tags":[<tags ONLY if emotionsstaerke is stark, max 1, from: {tags}; else empty>],'
 '"note":"<max 12 words>"}}')

def ask(mp3, en, k):
    b64 = base64.b64encode(open(mp3,"rb").read()).decode()
    payload = {"model":"gemini-2.5-flash","temperature":0.1,"messages":[{"role":"user","content":[
        {"type":"text","text":PROMPT.format(en=en, tags=", ".join(TAGS))},
        {"type":"input_audio","input_audio":{"data":b64,"format":"mp3"}}]}]}
    for w in (0, 20, 40):
        if w: time.sleep(w)
        out = subprocess.run(["curl","-s","-X","POST","-H",f"Authorization: Bearer {k}",
                              "-H","Content-Type: application/json","--data-binary","@-",GURL],
                             input=json.dumps(payload), capture_output=True, text=True, timeout=180).stdout
        try:
            txt = json.loads(out)["choices"][0]["message"]["content"]
            txt = txt.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            d = json.loads(txt)
            d["v3_tags"] = [t for t in d.get("v3_tags",[]) if t in TAGS]
            return d
        except Exception:
            if '"code":500' not in out: return {"fehler": out[:300]}
    return {"fehler": out[:300]}

ap = argparse.ArgumentParser(); ap.add_argument("--bloecke", required=True)
a = ap.parse_args()
bloecke = json.load(open(a.bloecke))
SRC = f"{BASIS}/_work/source_original.mp4"
if not os.path.exists(SRC): SRC = f"{BASIS}/_work/source.mp4"
k = key(); rows = []; kaputt = 0
for i, b in enumerate(bloecke):
    snip = f"{BASIS}/_work/emo_{i:02d}.mp3"
    subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{b['t0']:.2f}","-to",f"{b['t1']:.2f}",
                    "-i",SRC,"-vn","-c:a","libmp3lame","-b:a","160k",snip], check=True)
    r = ask(snip, b["en"], k)
    os.remove(snip)
    rows.append({"zeile": i, "t0": b["t0"], "t1": b["t1"], "en": b["en"], **r})
    if "fehler" in r: kaputt += 1
    print(f"Zeile {i}: {r.get('emotion','FEHLER')} · Ton {r.get('ton','—')} · Tags {r.get('v3_tags','—')}")
json.dump(rows, open(f"{BASIS}/_pipeline/emotions_karte.json","w"), ensure_ascii=False, indent=1)
print(f"emotions_karte.json: {len(rows)} Zeilen, {kaputt} Fehler")
sys.exit(1 if kaputt else 0)
