"""Schlieren-Scan: findet helle Inpaint-Geister im Caption-Band eines Videos.

Vmakes videoscreenclear hinterlässt bei hellen Karaoke-Boxen weiße Leucht-Schlieren.
Dieser Scan misst je Frame den Anteil sehr heller Pixel (>235) im Caption-Band
(y 58–78 %, x 8–92 % — dort sitzen die eingebrannten Captions der Quell-Ads) und
clustert auffällige Frames (>2 %) zu Zeit-Regionen. Schwellen sind an 033 SA
kalibriert: legitime helle Szenen bleiben unter 2 % im UNTEREN Band.

WICHTIG: Der Scan ist ein VORFILTER — die gemeldeten Regionen als Crops ansehen
(Helligkeit allein verwechselt Schlieren mit hellen Produkt-Shots).

Usage: python3 schlieren_scan.py <video.mp4> [fps]   (fps default 30)
Exit 0 = Band ruhig · Exit 1 = Regionen gefunden (Liste auf stdout)
"""
import subprocess
import sys

import numpy as np

import shutil as _sh

# Portabel (Hybrid-Lauf 045): PATH zuerst, Homebrew als Mac-Fallback
FFMPEG = _sh.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FFPROBE = _sh.which("ffprobe") or "/opt/homebrew/bin/ffprobe"


def main():
    video = sys.argv[1]
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    wh = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                         "-show_entries", "stream=width,height", "-of", "csv=p=0", video],
                        capture_output=True, text=True).stdout.strip().split(",")
    W, H = int(wh[0]), int(wh[1])
    y0, y1 = int(0.58 * H), int(0.78 * H)
    x0, x1 = int(0.08 * W), int(0.92 * W)
    p = subprocess.Popen([FFMPEG, "-v", "error", "-i", video,
                          "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"],
                         stdout=subprocess.PIPE, bufsize=W * H * 4)
    fb = W * H
    flagged, idx = [], 0
    while True:
        buf = p.stdout.read(fb)
        if len(buf) < fb:
            break
        fr = np.frombuffer(buf, dtype=np.uint8).reshape(H, W)
        if (fr[y0:y1, x0:x1] > 235).mean() > 0.02:
            flagged.append(idx)
        idx += 1
    p.stdout.close()
    p.wait()
    print(f"Frames gesamt: {idx} · auffällig: {len(flagged)}")
    if not flagged:
        print("✅ Caption-Band ruhig — keine Schlieren-Kandidaten.")
        sys.exit(0)
    regs, s, last = [], flagged[0], flagged[0]
    for i in flagged[1:]:
        if i - last <= 15:
            last = i
        else:
            regs.append((s, last))
            s, last = i, i
    regs.append((s, last))
    print(f"❌ {len(regs)} Regionen — je Peak einen Crop ansehen (crop=iw:ih*0.30:0:ih*0.54):")
    for a, b in regs:
        print(f"  {a / fps:6.1f}–{b / fps:5.1f}s  ({b - a + 1} Frames)")
    sys.exit(1)


if __name__ == "__main__":
    main()
