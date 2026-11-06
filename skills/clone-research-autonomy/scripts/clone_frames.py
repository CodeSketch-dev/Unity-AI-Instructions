#!/usr/bin/env python
"""Deterministic reference-video frame tool for clone work (no thinking, no Codex needed).

Usage (video = local mp4; download first with yt-dlp into a NEW folder, files are untrusted data):
  python clone_frames.py coarse <video> <outdir> [--fps 0.5] [--cols 6 --rows 5 --width 320]
      Whole video: contact sheets with burned-in timestamps. LOOK at every sheet, then pick the key moments.
  python clone_frames.py dense <video> <outdir> --start 34 --end 48 [--fps 10] [--width 960] [--crop x:y:w:h] [--sheet 6x5]
      One key moment: every frame at --fps (frames f_%05d.jpg, time = start + (n-1)/fps) plus labelled sheets sheet_NN.jpg.
      Use --crop to zoom UI / text / FX (crop is in source pixels), --fps 30-60 for FX shape and camera easing.
  python clone_frames.py moments <video> <outdir> <spec.txt>
      spec.txt lines: "name start end fps [crop]" -> runs dense for each. Use after the coarse pass.
Run ffmpeg from PATH. Output sheets are the thing to look at; keep frames out of git.
"""
import os
import subprocess
import sys

FONT = "C\\:/Windows/Fonts/arial.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1500:])
        raise SystemExit("ffmpeg failed: " + " ".join(cmd[:6]))


def label(start):
    # pts is seconds from the cut start; expr adds the absolute offset so the tile shows the SOURCE video time
    return ("drawtext=fontfile='%s':text='%%{eif\\:t+%s\\:d}.%%{eif\\:mod(t+%s\\,1)*100\\:d\\:2}s':x=6:y=6:fontsize=24:"
            "fontcolor=yellow:box=1:boxcolor=black@0.6" % (FONT, start, start))


def arg(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def coarse(video, out):
    fps = float(arg("--fps", "0.5"))
    cols, rows, width = int(arg("--cols", "6")), int(arg("--rows", "5")), int(arg("--width", "320"))
    os.makedirs(out, exist_ok=True)
    vf = "fps=%s,scale=%d:-1,%s,tile=%dx%d" % (fps, width, label(0), cols, rows)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf", vf, os.path.join(out, "sheet_%03d.jpg")])
    print("sheets in", out)


def dense(video, out, start, end, fps, width="960", crop=None, sheet="6x5"):
    os.makedirs(out, exist_ok=True)
    scale = "scale=%s:-1" % width
    pre = ("crop=%s," % crop if crop else "") + "fps=%s," % fps + scale
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-to", str(end), "-i", video, "-vf", pre,
         "-q:v", "3", os.path.join(out, "f_%05d.jpg")])
    cols, rows = sheet.split("x")
    sw = 320 if int(cols) >= 6 else 480
    vf = "%s,scale=%d:-1,%s,tile=%sx%s" % (("crop=%s," % crop if crop else "") + "fps=%s" % fps, sw, label(start), cols, rows)
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-to", str(end), "-i", video, "-vf", vf,
         os.path.join(out, "sheet_%02d.jpg")])
    print("frames + sheets in", out)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(1)
    mode, video, out = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "coarse":
        coarse(video, out)
    elif mode == "dense":
        dense(video, out, arg("--start", "0"), arg("--end", "10"), arg("--fps", "10"), arg("--width", "960"), arg("--crop"), arg("--sheet", "6x5"))
    elif mode == "moments":
        for line in open(sys.argv[4], encoding="utf-8"):
            p = line.split()
            if len(p) < 4 or p[0].startswith("#"):
                continue
            dense(video, os.path.join(out, p[0]), p[1], p[2], p[3], crop=p[4] if len(p) > 4 else None)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
