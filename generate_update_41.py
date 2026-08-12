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
    "zh-TW": (
        "計畫以族語學習、文化認同與生活支持為核心，設立原住民族語證照班，鼓勵學生準備並考取族語認證。",
        "計畫以族語學習、促成全民原教與生活支持為核心，設立原住民族語證照班，鼓勵學生準備並考取族語認證。",
    ),
    "en-US": (
        "Indigenous language certificate classes strengthen language proficiency while deepening cultural identity and belonging.",
        "The project centers on Indigenous language learning, advancing Indigenous education for all, and daily-life support. It provides Indigenous language certificate classes and encourages students to prepare for and earn language certification.",
    ),
    "ja-JP": (
        "先住民族語の検定対策講座や学習会を設け、語学力の向上とともに、文化への誇り、アイデンティティー、仲間とのつながりを育んでいます。",
        "本計画は、先住民族語の学習、すべての人に向けた先住民族教育の推進、生活支援を柱とし、先住民族語の検定対策講座を設け、学生の受験と資格取得を後押ししています。",
    ),
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
    raw = (ROOT / "languages-41.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if set(languages) != set(VOICES) or set(languages) != set(REPLACEMENTS):
        raise RuntimeError("Language set does not match the three configured guides")

    for code, item in languages.items():
        old, new = REPLACEMENTS[code]
        spoken_text = " ".join(cue[2] for cue in item["cues"])
        if old not in spoken_text:
            raise RuntimeError(f"Expected text not found for {code}: {old}")
        spoken_text = spoken_text.replace(old, new)
        text_path = ROOT / f"narration-41-{code}.txt"
        audio_path = ROOT / f"narration-41-{code}.mp3"
        srt_path = ROOT / f"narration-41-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-41.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "41.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-41\.js(?:\?v=\d+)?', "languages-41.js?v=2", html, count=1)
    html = re.sub(r'narration-41-zh-TW\.mp3(?:\?v=\d+)?', "narration-41-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 41 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
