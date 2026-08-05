import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import generate_multilang_26 as helper

ROOT = Path(__file__).resolve().parent
OUT = ROOT if os.environ.get("GITHUB_ACTIONS") == "true" else ROOT / "github-pages"
POSTER_SOURCE = ROOT / "poster-31-source.jpg"
VOICES = {code: helper.VOICES[code] for code in ("zh-TW", "en-US", "ja-JP")}
SPOKEN = {code: {"USR": "U S R", "CSR": "C S R", "SDGs": "S D Gs"} for code in VOICES}


def load_languages():
    html = (ROOT / "31-formal.html").read_text(encoding="utf-8")
    raw = re.search(r"window\.GUIDE_LANGUAGES=(\{.*?\});", html, re.S).group(1)
    return json.loads(raw)


def main():
    OUT.mkdir(exist_ok=True)
    languages = load_languages()
    for code, item in languages.items():
        spoken = " ".join(item["cues"])
        for formal, pronunciation in SPOKEN[code].items():
            spoken = spoken.replace(formal, pronunciation)
        text_path = ROOT / f"narration-31-{code}.txt"
        audio_path = OUT / f"narration-31-{code}.mp3"
        srt_path = ROOT / f"narration-31-{code}.srt"
        text_path.write_text(spoken, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / ".vendor")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path)
        ], check=True, env=env)
        cues = helper.read_cues(srt_path)
        for cue in cues:
            for formal, pronunciation in SPOKEN[code].items():
                cue[2] = cue[2].replace(pronunciation, formal)
        item["audio"] = audio_path.name + "?v=1"
        item["cues"] = cues

    (OUT / "languages-31.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    shutil.copy2(POSTER_SOURCE, OUT / "poster-31.jpg")
    html = (OUT / "30.html").read_text(encoding="utf-8")
    html = re.sub(r"<title>.*?</title>", f"<title>{languages['zh-TW']['title']}｜Audio Guide</title>", html, count=1)
    html = re.sub(r'(<figure class="poster"><img src=")[^"]+(" alt=")[^"]+(">)',
                  rf'\1poster-31.jpg?v=1\2{languages["zh-TW"]["title"]}\3', html, count=1)
    html = re.sub(r'(<p id="eyebrow" class="eyebrow">).*?(</p>)', r'\1GUIDE 31\2', html, count=1)
    html = re.sub(r'(<h1 id="title">).*?(</h1>)', rf'\1{languages["zh-TW"]["title"]}\2', html, count=1)
    options = "".join(f'<option value="{code}">{item["label"]}</option>' for code, item in languages.items())
    html = re.sub(r'(<select id="language">).*?(</select>)', rf'\1{options}\2', html, count=1, flags=re.S)
    html = re.sub(r'languages-30\.js\?v=\d+', "languages-31.js?v=1", html, count=1)
    html = re.sub(r'narration-30-zh-TW\.mp3\?v=\d+', "narration-31-zh-TW.mp3?v=1", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    (OUT / "31.html").write_text(html, encoding="utf-8")
    print(f"Generated 31.html and {len(languages)} audio files; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
