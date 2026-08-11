import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VOICES = {
    "zh-TW": "zh-TW-HsiaoChenNeural",
    "en-US": "en-US-JennyNeural",
    "ja-JP": "ja-JP-NanamiNeural",
}

REPLACEMENTS = {
    "zh-TW": [("本年度各項學習輔導機制", "114年度各項學習輔導機制")],
    "en-US": [("This year, the learning support mechanisms", "In academic year 2025, the learning support mechanisms")],
    "ja-JP": [("本年度は、各種学習支援制度", "二〇二五年度は、各種学習支援制度")],
}


def seconds(value):
    hours, minutes, secs = value.replace(",", ".").split(":")
    return round(int(hours) * 3600 + int(minutes) * 60 + float(secs), 3)


def read_cues(path):
    cues = []
    for block in re.split(r"\r?\n\r?\n", path.read_text(encoding="utf-8").strip()):
        rows = block.splitlines()
        if len(rows) >= 3:
            start, end = [part.strip() for part in rows[1].split("-->")]
            cues.append([seconds(start), seconds(end), " ".join(rows[2:]).strip()])
    return cues


def main():
    raw = (ROOT / "languages-39.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    for code, item in languages.items():
        spoken_text = " ".join(cue[2] for cue in item["cues"])
        for old, new in REPLACEMENTS[code]:
            if old not in spoken_text:
                raise RuntimeError(f"Expected text not found for {code}: {old}")
            spoken_text = spoken_text.replace(old, new)
        text_path = ROOT / f"narration-39-{code}.txt"
        audio_path = ROOT / f"narration-39-{code}.mp3"
        srt_path = ROOT / f"narration-39-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-39.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "39.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-39\.js(?:\?v=\d+)?', "languages-39.js?v=2", html, count=1)
    html = re.sub(r'narration-39-zh-TW\.mp3(?:\?v=\d+)?', "narration-39-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 39 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
