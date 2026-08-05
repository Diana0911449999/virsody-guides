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
POSTER_SOURCE = ROOT / "poster-29-source.jpg"
VOICES = helper.VOICES
SPOKEN = {
    code: {"SDGs": "S D Gs", "SDG": "S D G", "AI": "A I"}
    for code in VOICES
}
JAPANESE_CUES = [
    "高等教育深耕計画成果展へようこそ。このページでは、世代をつなぐ持続可能な健康づくりと介護予防人材育成の成果を紹介します。",
    "台湾の急速な高齢化に対応し、本計画は社会的責任、健康の公平性、利用しやすいケアを柱に、高齢者が地域で健康に尊厳を保って暮らすことを目指します。",
    "持続可能な開発目標の三、四、十、十一、十七に対応し、分野横断型授業、人材育成、スマート福祉機器、デジタルツール、地域連携を組み合わせています。",
    "活動拠点は、大甲の日南、太平の永成、大里、霧峰の北勢などへ広がり、海線地域と屯区のケア資源を利用しやすくしています。",
    "支援員コミュニティーと統合プラットフォームも整備しました。再研修の参加学生は十六人から二十六人に増え、満足度は五点満点中四点八三でした。",
    "二〇二五年度は地域活動を六十回実施し、学生は延べ八百六十人が参加しました。高齢者や支援を必要とする方を延べ千三百十三人支援し、競技会の入賞と二件の特許成果にもつながりました。",
    "学生は実践を通じて専門技術、台湾語での対話、協働力を高め、長期ケアの仕事への理解を深めました。高齢者も健康づくりと世代間交流から活力とつながりを得ています。ご清聴ありがとうございました。",
]


def load_languages():
    html = (ROOT / "29-formal.html").read_text(encoding="utf-8")
    raw = re.search(r"window\.GUIDE_LANGUAGES=(\{.*?\});", html, re.S).group(1)
    return json.loads(raw)


def main():
    OUT.mkdir(exist_ok=True)
    languages = load_languages()
    languages["ja-JP"]["cues"] = JAPANESE_CUES
    for code, item in languages.items():
        text = " ".join(item["cues"])
        spoken = text
        for formal, pronunciation in SPOKEN[code].items():
            spoken = spoken.replace(formal, pronunciation)
        text_path = ROOT / f"narration-29-{code}.txt"
        audio_path = OUT / f"narration-29-{code}.mp3"
        srt_path = ROOT / f"narration-29-{code}.srt"
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

    (OUT / "languages-29.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    shutil.copy2(POSTER_SOURCE, OUT / "poster-29.jpg")
    html = (OUT / "25.html").read_text(encoding="utf-8")
    html = re.sub(r"<title>.*?</title>", f"<title>{languages['zh-TW']['title']} Audio Guide</title>", html, count=1)
    html = re.sub(r'(<figure class="poster"><img src=")[^"]+(" alt=")[^"]+(">)',
                  rf'\1poster-29.jpg?v=1\2{languages["zh-TW"]["title"]}\3', html, count=1)
    html = re.sub(r'(<p id="eyebrow" class="eyebrow">).*?(</p>)', r'\1GUIDE 29\2', html, count=1)
    html = re.sub(r'(<h1 id="title">).*?(</h1>)', rf'\1{languages["zh-TW"]["title"]}\2', html, count=1)
    options = "".join(
        f'<option value="{code}">{item["label"]}</option>'
        for code, item in languages.items()
    )
    html = re.sub(r'(<select id="language">).*?(</select>)', rf'\1{options}\2', html, count=1, flags=re.S)
    html = re.sub(r'languages-25\.js\?v=\d+', "languages-29.js?v=1", html, count=1)
    html = re.sub(r'narration-25-zh-TW\.mp3\?v=\d+', "narration-29-zh-TW.mp3?v=1", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    (OUT / "29.html").write_text(html, encoding="utf-8")
    print(f"Generated 29.html and {len(languages)} audio files; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
