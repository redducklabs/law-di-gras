"""Record the 90-second demo video: Playwright drives localhost, OpenAI TTS narrates.

  cd tools/demo_video
  uv run --with playwright --with openai --with imageio-ffmpeg python record.py [--dry] [--voice ash]

Needs backend :8000 and Vite :5175 running (see docs/demo-script.md). Signs in through the
API with APP_LOGIN_USER/PASSWORD from the main checkout's .env (never printed), so the video
starts on the Cases page. Narration text is the only thing sent to OpenAI. Output: out/demo.mp4.
--dry records with silent placeholders sized by word count (no TTS calls).
"""
import argparse
import os
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import Page, sync_playwright

BASE = "http://localhost:5175"
API = "http://127.0.0.1:8000"
OUT = Path(__file__).parent / "out"
W, H = 1440, 900


def main_env() -> dict:
    root = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                          capture_output=True, text=True, check=True).stdout.strip()
    path = Path(root).parent / ".env"
    if not path.exists():
        path = Path(__file__).resolve().parents[2] / ".env"
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$", line)
        if m:
            env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return env


# ---------- narration ----------
SEGMENTS = [
    ("cases", "A personal-injury file is thousands of pages. Here, every matter is read live from Clio, read-only, "
              "and sorted by what needs you first."),
    ("brief", "Open a case and it reads in ninety seconds: where it stands, what's next, "
              "and a timeline of medical, legal and deadlines."),
    ("source", "Every fact links to its source: the page opens with the exact quote highlighted. "
               "If it isn't in the record, it isn't on screen."),
    ("conflict", "Where the file contradicts itself, like Metro-North's coverage, we show both sides."),
    ("blind", "Blind spots: an agent reads the whole file for what a page-by-page review misses. "
              "The defense says it annexed Metro-North's incident report; our own follow-up says it isn't there."),
    ("audit", "Every run is audited automatically. Anything doubtful is flagged, not stated as fact."),
    ("next", "What's overdue, and a cited follow-up drafted in one click."),
    ("chat", "Ask anything, like when the Pullano deposition is. Answers come only from the record, every sentence cited, "
             "and the links take you straight to the source."),
    ("share", "Providers on a lien get their own view: status, coverage, what we need from them, and their bills. "
              "Never strategy or notes."),
    ("close", "The whole case in ninety seconds, every fact traceable, about two fifty a case."),
]

TTS_INSTRUCTIONS = ("Warm, engaged woman presenting a product she's proud of to a room of trial lawyers. "
                    "Conversational and natural, like talking to a colleague, upbeat but credible. Brisk pace, "
                    "vary intonation, a little smile in the voice, light emphasis on key words, short natural pauses.")


def tts(env: dict, voice: str, dry: bool) -> dict[str, Path]:
    OUT.mkdir(exist_ok=True)
    files = {}
    if not dry:
        from openai import OpenAI
        client = OpenAI(api_key=env["OPENAI_API_KEY"])
    for key, text in SEGMENTS:
        p = OUT / f"{key}.wav"
        if dry:
            n = int(24000 * (len(text.split()) / 2.6))  # ~156 wpm placeholder
            with wave.open(str(p), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(b"\0\0" * n)
        elif not p.exists() or p.stat().st_mtime < Path(__file__).stat().st_mtime:
            for attempt in range(4):  # raw 24 kHz 16-bit mono PCM -> our own WAV header
                try:
                    pcm = client.audio.speech.create(model="gpt-4o-mini-tts", voice=voice, input=text,
                                                     instructions=TTS_INSTRUCTIONS, response_format="pcm").content
                    break
                except Exception as e:
                    print(f"tts {key} retry {attempt + 1}: {e.__class__.__name__}")
                    time.sleep(2 + 2 * attempt)
            else:
                sys.exit(f"TTS failed for {key}")
            with wave.open(str(p), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
        files[key] = p
    return files


def wav_seconds(p: Path) -> float:
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


# ---------- on-screen helpers ----------
OVERLAY_JS = """
() => {
  if (document.getElementById('__cursor')) return;
  const c = document.createElement('div'); c.id = '__cursor';
  c.style.cssText = 'position:fixed;left:720px;top:450px;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;' +
    'background:rgba(79,70,229,.35);border:2px solid rgba(79,70,229,.9);z-index:2147483647;pointer-events:none;' +
    'transition:left .55s ease, top .55s ease, transform .15s ease;';
  document.body.appendChild(c);
  const cap = document.createElement('div'); cap.id = '__caption';
  cap.style.cssText = 'position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:1100px;padding:10px 18px;' +
    'border-radius:12px;background:rgba(15,23,42,.82);color:#fff;font:500 17px/1.4 Inter,system-ui,sans-serif;' +
    'text-align:center;z-index:2147483646;pointer-events:none;transition:opacity .25s;opacity:0';
  document.body.appendChild(cap);
}
"""


class Stage:
    def __init__(self, page: Page):
        self.page = page
        self.caption_text = ""

    def overlay(self):
        self.page.evaluate(OVERLAY_JS)
        if self.caption_text:
            self.caption(self.caption_text)

    def caption(self, text: str):
        self.caption_text = text
        self.page.evaluate("""t => { const c = document.getElementById('__caption'); if (c) { c.textContent = t; c.style.opacity = t ? 1 : 0 } }""", text)

    def move(self, loc, click=False, pause=0.35):
        loc.scroll_into_view_if_needed(timeout=8000)
        loc.evaluate("e => { const r = e.getBoundingClientRect(); if (r.top < 90 || r.bottom > innerHeight - 170) e.scrollIntoView({block: 'center', behavior: 'smooth'}) }")
        time.sleep(0.45)
        b = loc.bounding_box()
        if not b:
            return
        x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        self.overlay()
        self.page.evaluate("""([x,y]) => { const c = document.getElementById('__cursor'); c.style.left = x+'px'; c.style.top = y+'px' }""", [x, y])
        self.page.mouse.move(x, y, steps=8)
        time.sleep(0.6)
        if click:
            self.page.evaluate("() => { const c = document.getElementById('__cursor'); c.style.transform='scale(.7)'; setTimeout(()=>c.style.transform='', 160) }")
            loc.click(timeout=8000)
            time.sleep(pause)
            self.overlay()

    def goto(self, url: str):
        self.page.goto(url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=4000)  # polling pages never go idle
        except Exception:
            pass
        self.overlay()

    def scroll_to(self, sel: str):
        self.page.locator(sel).first.scroll_into_view_if_needed()
        time.sleep(0.4)


# Dead time to cut from the final video, as (start, end) in seconds since t0.
CUTS: list[tuple[float, float]] = []
T0 = [0.0]


# ---------- the demo path ----------
def close_all(s: Stage):
    """Close any open drawer / chat panel (visible Close buttons only)."""
    for _ in range(3):
        btns = [b for b in s.page.get_by_role("button", name="Close").all() if b.is_visible()]
        if not btns:
            return
        try:
            s.move(btns[0], click=True, pause=0.4)
        except Exception:
            s.page.keyboard.press("Escape")


def run_segment(s: Stage, key: str, ctx) -> None:
    p = s.page
    if key == "cases":
        s.goto(f"{BASE}/cases")
        rows = p.locator("[role=link]")
        s.move(rows.first)
        time.sleep(1.2)
        s.move(p.get_by_text(re.compile("overdue", re.I)).first)
    elif key == "brief":
        s.move(p.locator("[role=link]").first, click=True, pause=1.0)
        p.wait_for_selector("#timeline", timeout=20000)
        s.overlay()
        s.move(p.locator("#timeline").first)
        dots = p.locator("#timeline [aria-label]")
        if dots.count() > 4:
            s.move(dots.nth(3))
    elif key == "source":
        chip = p.locator("#status button[title]").first
        s.move(chip, click=True, pause=1.5)
        p.wait_for_timeout(2500)
    elif key == "conflict":
        close_all(s)
        hit = p.locator("#status li", has_text="Conflict").first
        if hit.count():
            s.move(hit)
    elif key == "blind":
        bar = p.locator("#blind-spots button[aria-expanded]").first
        s.move(bar, click=True, pause=1.0)
        chip = p.locator("#blind-spots ol li").first.locator("button[title]").first
        if chip.count():
            s.move(chip, click=True, pause=1.5)
            p.wait_for_timeout(2000)
    elif key == "audit":
        close_all(s)
        badge = p.get_by_text(re.compile(r"Audited|Audit running", re.I)).first
        if badge.count():
            s.page.evaluate("window.scrollTo({top:0,behavior:'smooth'})"); time.sleep(0.6)
            s.move(badge)
        flag = p.locator("[aria-label='Audit flag']").first
        if flag.count():
            s.move(flag)
    elif key == "next":
        s.scroll_to("#next-steps")
        btn = p.locator("#next-steps").get_by_role("button", name=re.compile("Draft", re.I)).first
        s.move(btn, click=True, pause=1.2)
        p.wait_for_timeout(1500)
    elif key == "chat":
        close_all(s)
        s.move(p.get_by_role("button", name="Ask the case"), click=True, pause=0.6)
        box = p.get_by_placeholder(re.compile("Ask about this case"))
        s.move(box, click=True)
        box.type("When is the Pullano deposition?", delay=35)
        s.move(p.get_by_role("button", name="Send"), click=True)
        t_send = time.monotonic() - T0[0] + 1.5  # keep the "Reading the record…" beat
        p.locator("aside[aria-label='Ask the case'] button:has-text('→')").first.wait_for(timeout=60000)
        t_ans = time.monotonic() - T0[0] - 0.2
        if t_ans - t_send > 1.0:
            CUTS.append((t_send, t_ans))
        time.sleep(1.0)
        link = p.locator("aside[aria-label='Ask the case'] button:has-text('→')").first
        s.move(link, click=True, pause=1.2)
    elif key == "share":
        close_all(s)
        p.evaluate("window.scrollTo({top:0,behavior:'smooth'})"); time.sleep(0.6)
        s.move(p.get_by_role("button", name="Share with provider").first, click=True, pause=1.5)
        link = p.locator("[aria-label='Share with provider'] a[href*='/p/']").first
        link.wait_for(timeout=15000)
        s.move(link)
        href = link.get_attribute("href")
        time.sleep(1.0)
        s.goto(href if href.startswith("http") else BASE + href)
        time.sleep(1.0)
        p.mouse.wheel(0, 500); time.sleep(1.2)
    elif key == "close":
        s.goto(f"{BASE}/cases")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--voice", default="nova")
    ap.add_argument("--headed", action="store_true")
    a = ap.parse_args()
    env = main_env()
    audio = tts(env, a.voice, a.dry)
    durs = {k: wav_seconds(p) for k, p in audio.items()}
    print("narration seconds:", round(sum(durs.values()), 1))

    OUT.mkdir(exist_ok=True)
    starts: dict[str, float] = {}
    with sync_playwright() as pw:
        exe = next(iter(sorted(Path(os.environ.get("LOCALAPPDATA", "")).glob("ms-playwright/chromium-*/chrome-win64/chrome.exe"))), None)
        browser = pw.chromium.launch(headless=not a.headed, executable_path=str(exe) if exe else None)
        ctx = browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(OUT / "raw"),
                                  record_video_size={"width": W, "height": H}, base_url=BASE)
        r = ctx.request.post(f"{BASE}/api/auth/login",
                             data={"username": env["APP_LOGIN_USER"], "password": env["APP_LOGIN_PASSWORD"]})
        if not r.ok:
            sys.exit(f"login failed: {r.status}")
        page = ctx.new_page()
        t0 = time.monotonic()
        T0[0] = t0
        s = Stage(page)
        s.goto(f"{BASE}/cases")
        time.sleep(1.0)
        lead = time.monotonic() - t0  # trimmed from the video
        for key, text in SEGMENTS:
            starts[key] = time.monotonic() - t0
            s.caption(text)
            seg_t = time.monotonic()
            cut_before = sum(b - a for a, b in CUTS)
            try:
                run_segment(s, key, ctx)
            except Exception as e:  # keep recording; report the broken step
                print(f"[{key}] step failed: {e.__class__.__name__}: {str(e)[:200]}")
                page.screenshot(path=str(OUT / f"fail-{key}.png"))
            cut_here = sum(b - a for a, b in CUTS) - cut_before
            left = durs[key] + 0.5 - (time.monotonic() - seg_t - cut_here)
            if left > 0:
                time.sleep(left)
            elif left < -0.2:
                print(f"[{key}] actions ran {-left:.1f}s past the narration")
        s.caption("")
        time.sleep(1.0)
        end = time.monotonic() - t0
        video = page.video.path()
        ctx.close(); browser.close()

    # Map recording time -> final-video time (lead trimmed, CUTS removed).
    def vt(t: float) -> float:
        return t - lead - sum(min(b, t) - a for a, b in CUTS if a < t)

    rate = 24000
    track = bytearray()
    for key, _ in SEGMENTS:
        pos = int(vt(starts[key]) * rate) * 2
        if len(track) < pos:
            track += b"\0" * (pos - len(track))
        with wave.open(str(audio[key])) as w:
            track += w.readframes(w.getnframes())
    narr = OUT / "narration.wav"
    with wave.open(str(narr), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(track))
    final = OUT / ("demo-dry.mp4" if a.dry else "demo.mp4")
    keep, at = [], lead
    for a_, b_ in sorted(CUTS):
        keep.append((at, a_)); at = b_
    keep.append((at, end))
    parts = "".join(f"[0:v]trim=start={x:.3f}:end={y:.3f},setpts=PTS-STARTPTS[v{i}];" for i, (x, y) in enumerate(keep))
    graph = parts + "".join(f"[v{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=1:a=0[v]"
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(video), "-i", str(narr), "-filter_complex", graph,
                    "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-r", "25", "-c:a", "aac", "-b:a", "160k", str(final)], check=True)
    total = vt(end)
    print(f"video: {final}  ({total:.1f}s; cut {sum(b - a for a, b in CUTS):.1f}s of waiting)")
    for k in starts:
        print(f"  {k:9s} @ {vt(starts[k]):5.1f}s  narration {durs[k]:4.1f}s")


if __name__ == "__main__":
    main()
