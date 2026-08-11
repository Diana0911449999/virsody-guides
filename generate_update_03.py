import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VOICES = {
    "zh-TW": "zh-TW-HsiaoChenNeural",
    "en-US": "en-US-JennyNeural",
    "es-ES": "es-ES-ElviraNeural",
    "fr-FR": "fr-FR-DeniseNeural",
    "de-DE": "de-DE-KatjaNeural",
    "ja-JP": "ja-JP-NanamiNeural",
    "ko-KR": "ko-KR-SunHiNeural",
    "it-IT": "it-IT-ElsaNeural",
    "pt-PT": "pt-PT-RaquelNeural",
    "ru-RU": "ru-RU-SvetlanaNeural",
}

IPAS_SPOKEN = {
    "zh-TW": "I pass",
    "en-US": "I pass",
    "es-ES": "I pass",
    "fr-FR": "I pass",
    "de-DE": "I pass",
    "ja-JP": "アイ パス",
    "ko-KR": "아이 패스",
    "it-IT": "I pass",
    "pt-PT": "I pass",
    "ru-RU": "ай пас",
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
    raw = (ROOT / "languages-03.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    for code, item in languages.items():
        display_text = " ".join(cue[2] for cue in item["cues"])
        if "iPAS" not in display_text:
            raise RuntimeError(f"iPAS not found for {code}")
        pronunciation = IPAS_SPOKEN[code]
        spoken_text = display_text.replace("iPAS", pronunciation)
        text_path = ROOT / f"narration-03-{code}.txt"
        audio_path = ROOT / f"narration-03-{code}.mp3"
        srt_path = ROOT / f"narration-03-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+20%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        cues = read_cues(srt_path)
        for cue in cues:
            cue[2] = cue[2].replace(pronunciation, "iPAS")
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = cues

    (ROOT / "languages-03.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "03.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-03\.js(?:\?v=\d+)?', "languages-03.js?v=2", html, count=1)
    html = re.sub(r'narration-03-zh-TW\.mp3(?:\?v=\d+)?', "narration-03-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated iPAS pronunciation in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
