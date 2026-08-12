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
    "zh-TW": (
        "茂順與信岳相關產業各有十名學生實習，比例均為百分之十四。",
        "茂順、信岳與其他相關產業各有十名學生實習，比例均為百分之十四。",
    ),
    "en-US": (
        "Ten students entered related internships connected with Nak and ten with Hsin Yueh, each representing fourteen percent.",
        "Ten students interned with Nak, ten with Hsin Yueh, and ten in other related industries; each group represented fourteen percent.",
    ),
    "es-ES": (
        "Treinta y tres estudiantes se inscribieron en la sesión de Nak, y diez realizaron prácticas relacionadas con cada una de las empresas Nak y Hsin Yueh.",
        "Treinta y tres estudiantes se inscribieron en la sesión de Nak; diez realizaron prácticas en Nak, diez en Hsin Yueh y diez en otras industrias relacionadas, y cada grupo representó el catorce por ciento.",
    ),
    "fr-FR": (
        "Trente-trois étudiants se sont inscrits à la présentation de Nak, et dix ont effectué un stage lié à chacune des entreprises Nak et Hsin Yueh.",
        "Trente-trois étudiants se sont inscrits à la présentation de Nak; dix ont effectué un stage chez Nak, dix chez Hsin Yueh et dix dans d’autres secteurs connexes, chaque groupe représentant quatorze pour cent.",
    ),
    "de-DE": (
        "Je zehn absolvierten einschlägige Praktika im Umfeld von Nak und Hsin Yueh.",
        "Je zehn Studierende absolvierten Praktika bei Nak, bei Hsin Yueh und in anderen verwandten Branchen; jede Gruppe entsprach vierzehn Prozent.",
    ),
    "ja-JP": (
        "ナックの説明会には三十三名が登録し、ナックとシンユエの関連分野では、それぞれ十名が実習しました。",
        "ナックの説明会には三十三名が登録し、ナック、シンユエ、その他の関連産業で、それぞれ十名の学生が実習し、各割合は十四パーセントでした。",
    ),
    "ko-KR": (
        "낙 설명회에는 서른세 명이 등록했으며, 낙과 신웨 관련 분야에서 각각 열 명이 실습했습니다.",
        "낙 설명회에는 서른세 명이 등록했으며, 낙, 신웨, 기타 관련 산업에서 각각 열 명의 학생이 실습했고 각 비율은 십사 퍼센트였습니다.",
    ),
    "it-IT": (
        "Trentatré studenti si sono iscritti alla presentazione di Nak; dieci hanno svolto tirocini collegati a Nak e dieci a Hsin Yueh.",
        "Trentatré studenti si sono iscritti alla presentazione di Nak; dieci hanno svolto tirocini presso Nak, dieci presso Hsin Yueh e dieci in altri settori collegati, con il quattordici per cento per ciascun gruppo.",
    ),
    "pt-PT": (
        "Trinta e três estudantes inscreveram-se na sessão da Nak; dez realizaram estágios ligados à Nak e dez à Hsin Yueh.",
        "Trinta e três estudantes inscreveram-se na sessão da Nak; dez realizaram estágios na Nak, dez na Hsin Yueh e dez noutras indústrias relacionadas, correspondendo cada grupo a catorze por cento.",
    ),
    "ru-RU": (
        "На встречу Nak записались тридцать три студента; по десять человек прошли профильную практику, связанную с Nak и Hsin Yueh.",
        "На встречу Nak записались тридцать три студента; по десять человек прошли практику в Nak, в Hsin Yueh и в других смежных отраслях, причём каждая группа составила четырнадцать процентов.",
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
    raw = (ROOT / "languages-19.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if set(languages) != set(VOICES) or set(languages) != set(REPLACEMENTS):
        raise RuntimeError("Language set does not match the 10 configured guides")

    for code, item in languages.items():
        old, new = REPLACEMENTS[code]
        spoken_text = " ".join(cue[2] for cue in item["cues"])
        if old not in spoken_text:
            raise RuntimeError(f"Expected text not found for {code}: {old}")
        spoken_text = spoken_text.replace(old, new)
        text_path = ROOT / f"narration-19-{code}.txt"
        audio_path = ROOT / f"narration-19-{code}.mp3"
        srt_path = ROOT / f"narration-19-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-19.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "19.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-19\.js(?:\?v=\d+)?', "languages-19.js?v=2", html, count=1)
    html = re.sub(r'narration-19-zh-TW\.mp3(?:\?v=\d+)?', "narration-19-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 19 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
