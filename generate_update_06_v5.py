import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VOICE = "zh-TW-HsiaoChenNeural"
SPOKEN_EMI = "伊欸姆愛"


def seconds(value):
    hours, minutes, secs = value.replace(",", ".").split(":")
    return round(int(hours) * 3600 + int(minutes) * 60 + float(secs), 3)


def read_cues(path):
    cues = []
    for block in re.split(r"\r?\n\r?\n", path.read_text(encoding="utf-8").strip()):
        rows = block.splitlines()
        if len(rows) >= 3:
            start, end = [part.strip() for part in rows[1].split("-->")]
            subtitle = " ".join(rows[2:]).strip().replace(SPOKEN_EMI, "EMI")
            subtitle = subtitle.replace("累計一百五十八人次參與", "累積158人次參與")
            cues.append([seconds(start), seconds(end), subtitle])
    return cues


def main():
    languages_path = ROOT / "languages-06.js"
    raw = languages_path.read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if "zh-TW" not in languages or len(languages) != 10:
        raise RuntimeError("Expected the 10-language guide with Traditional Chinese")

    chinese = languages["zh-TW"]
    display_text = " ".join(cue[2] for cue in chinese["cues"])
    if "EMI" not in display_text:
        raise RuntimeError("Expected EMI text was not found")
    if "累計一百五十八人次參與" not in display_text:
        raise RuntimeError("Expected spoken participation phrase was not found")

    # Keep the spoken participation phrase unchanged. Only EMI receives a
    # continuous phonetic prompt; generated subtitles are restored below.
    spoken_text = display_text.replace("EMI", SPOKEN_EMI)
    text_path = ROOT / "narration-06-zh-TW.txt"
    audio_path = ROOT / "narration-06-zh-TW.mp3"
    srt_path = ROOT / "narration-06-zh-TW.srt"
    text_path.write_text(spoken_text, encoding="utf-8")
    subprocess.run([
        sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICE,
        "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
    ], check=True)
    chinese["audio"] = audio_path.name + "?v=5"
    chinese["cues"] = read_cues(srt_path)

    subtitle_text = " ".join(cue[2] for cue in chinese["cues"])
    if "累積158人次參與" not in subtitle_text or SPOKEN_EMI in subtitle_text:
        raise RuntimeError("Subtitle restoration failed")

    languages_path.write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "06.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-06\.js(?:\?v=\d+)?', "languages-06.js?v=5", html, count=1)
    html = re.sub(r'narration-06-zh-TW\.mp3(?:\?v=\d+)?', "narration-06-zh-TW.mp3?v=5", html, count=1)
    duration = chinese["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 06 Chinese EMI pronunciation; duration {duration:.1f}s")


if __name__ == "__main__":
    main()
