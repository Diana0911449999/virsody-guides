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

REPLACEMENTS = {
    "zh-TW": [
        ("整合校長願景", "整合學校願景"),
        ("辦公室位於三民路三段九十一號", "辦公室位於創新育成中心2樓"),
    ],
    "en-US": [
        ("the office at 91, Section 3, Sanmin Road contains", "the office on the second floor of the Innovation and Incubation Center contains"),
    ],
    "es-ES": [
        ("la oficina situada en el número 91 de la sección 3 de la calle Sanmin dispone", "la oficina situada en la segunda planta del Centro de Innovación e Incubación dispone"),
    ],
    "fr-FR": [
        ("le bureau situé au 91, section 3, route Sanmin comprend", "le bureau situé au deuxième étage du Centre d’innovation et d’incubation comprend"),
    ],
    "de-DE": [
        ("Das vom Sprout-Projekt unterstützte Büro in der Sanmin-Straße, Abschnitt drei, Nummer einundneunzig, verfügt", "Das vom Sprout-Projekt unterstützte Büro im zweiten Stock des Innovations- und Gründerzentrums verfügt"),
    ],
    "ja-JP": [
        ("三民路三段九十一号に設置され", "イノベーション育成センター二階に設置され"),
    ],
    "ko-KR": [
        ("산민로 삼단 구십일 번지에 마련된", "창업보육센터 이 층에 마련된"),
    ],
    "it-IT": [
        ("l’ufficio al numero 91 della sezione 3 di via Sanmin comprende", "l’ufficio al secondo piano del Centro di innovazione e incubazione comprende"),
    ],
    "pt-PT": [
        ("o gabinete no número 91 da secção 3 da estrada Sanmin possui", "o gabinete no segundo piso do Centro de Inovação e Incubação possui"),
    ],
    "ru-RU": [
        ("центр по адресу: улица Саньминь, секция 3, дом 91, получил", "центр на втором этаже Центра инноваций и инкубации получил"),
    ],
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
    raw = (ROOT / "languages-09.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    for code, replacements in REPLACEMENTS.items():
        item = languages[code]
        source_text = " ".join(cue[2] for cue in item["cues"])
        for old, new in replacements:
            if old not in source_text:
                raise RuntimeError(f"Expected text not found for {code}: {old}")
            source_text = source_text.replace(old, new)
        text_path = ROOT / f"narration-09-{code}.txt"
        audio_path = ROOT / f"narration-09-{code}.mp3"
        srt_path = ROOT / f"narration-09-{code}.srt"
        text_path.write_text(source_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+20%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-09.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "09.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-09\.js\?v=\d+', "languages-09.js?v=2", html, count=1)
    html = re.sub(r'narration-09-zh-TW\.mp3\?v=\d+', "narration-09-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 09 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
