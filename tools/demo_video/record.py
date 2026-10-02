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
    ("cases", "A personal-injury file is thousands of pages. Every matter here is read live from Clio, read-only, "
              "and sorted by what needs you first."),
    ("brief", "Open a case and it reads in ninety seconds: where it stands, what's next, "
              "and a timeline with medical, legal and deadlines in their own lanes."),
    ("source", "Every fact links to its source. Click it, and the page opens with the exact quote highlighted. "
               "If it isn't in the record, it isn't on screen."),
    ("conflict", "When the file contradicts itself, like Metro-North's coverage, we show both sides and their sources "
                 "instead of guessing."),
    ("blind", "Then the part nobody has time for. An agent reads the whole file for what a page-by-page review misses. "
              "Here, the defense says it annexed Metro-North's incident report, while our own follow-up says it isn't in their response."),
    ("audit", "And every run is audited automatically. Quotes, numbers and overstatements are checked, "
              "and anything doubtful is flagged, not stated as fact."),
    ("next", "What's overdue and who we're waiting on, with a cited follow-up drafted in one click."),
    ("chat", "Ask anything. Answers come only from the record, with sources, and take you to the right place."),
    ("share", "Treating providers on a lien get their own view: status, coverage, what we need from them, and their bills. "
              "No strategy, no notes. The attorney decides what they see."),
    ("close", "The whole case in ninety seconds, every fact traceable, for about two fifty a case."),
]

TTS_INSTRUCTIONS = ("Calm, confident product-demo narrator speaking to trial attorneys. Natural pace, "
                    "clear diction, slight warmth, no hype.")


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
            with client.audio.speech.with_streaming_response.create(
                    model="gpt-4o-mini-tts", voice=voice, input=text, instructions=TTS_INSTRUCTIONS,
                    response_format="wav") as r:
                r.stream_to_file(p)
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
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        self.overlay()

    def scroll_to(self, sel: str):
        self.page.locator(sel).first.scroll_into_view_if_needed()
        time.sleep(0.4)


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
        p.locator("aside[aria-label='Ask the case'] button:has-text('→')").first.wait_for(timeout=45000)
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
    ap.add_argument("--voice", default="ash")
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
        s = Stage(page)
        s.goto(f"{BASE}/cases")
        time.sleep(1.0)
        lead = time.monotonic() - t0  # trimmed from the video
        for key, text in SEGMENTS:
            starts[key] = time.monotonic() - t0
            s.caption(text)
            seg_t = time.monotonic()
            try:
                run_segment(s, key, ctx)
            except Exception as e:  # keep recording; report the broken step
                print(f"[{key}] step failed: {e.__class__.__name__}: {str(e)[:200]}")
                page.screenshot(path=str(OUT / f"fail-{key}.png"))
            left = durs[key] + 0.5 - (time.monotonic() - seg_t)
            if left > 0:
                time.sleep(left)
            elif left < -0.2:
                print(f"[{key}] actions ran {-left:.1f}s past the narration")
        s.caption("")
        time.sleep(1.0)
        end = time.monotonic() - t0
        video = page.video.path()
        ctx.close(); browser.close()

    # Build one narration track: each segment starts where its actions started.
    rate = 24000
    track = bytearray()
    for key, _ in SEGMENTS:
        pos = int((starts[key] - lead) * rate) * 2
        if len(track) < pos:
            track += b"\0" * (pos - len(track))
        with wave.open(str(audio[key])) as w:
            track += w.readframes(w.getnframes())
    narr = OUT / "narration.wav"
    with wave.open(str(narr), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(track))
    final = OUT / ("demo-dry.mp4" if a.dry else "demo.mp4")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", f"{lead:.2f}", "-i", str(video), "-i", str(narr),
                    "-t", f"{end - lead:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", str(final)], check=True)
    print(f"video: {final}  ({end - lead:.1f}s)")
    for k in starts:
        print(f"  {k:9s} @ {starts[k] - lead:5.1f}s  narration {durs[k]:4.1f}s")


if __name__ == "__main__":
    main()
