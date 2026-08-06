import json
import os
import re
import subprocess
import sys
from pathlib import Path

import generate_multilang_26 as helper

ROOT = Path(__file__).resolve().parent
OUT = ROOT if os.environ.get("GITHUB_ACTIONS") == "true" else ROOT / "github-pages"
VOICES = {code: helper.VOICES[code] for code in ("zh-TW", "en-US", "ja-JP")}


def load_languages():
    script = (ROOT / "languages-41.js").read_text(encoding="utf-8")
    languages = json.loads(re.search(r"window\.GUIDE_LANGUAGES=(\{.*\});", script, re.S).group(1))
    languages["en-US"]["cues"] = [
        "Welcome to the Higher Education Sprout Project Achievement Exhibition. This guide presents learning and daily-life support for Indigenous students at National Taichung University of Science and Technology, organized by the Indigenous Student Resource Center.",
        "Indigenous language certificate classes strengthen language proficiency while deepening cultural identity and belonging. Study groups and Seediq language instruction help students reconnect language learning with community memory.",
        "Learning also takes place through Indigenous Culture Week, traditional Tsou bamboo-cup workshops, community visits, and field studies in the Qingliu and Saisiyat communities. Exploration of Paiwan spiritual traditions encourages respectful understanding of diverse Indigenous cultures.",
        "These activities connect academic guidance, daily-life support, cultural transmission, and community engagement. Students build confidence, strengthen peer connections, and turn cultural knowledge into meaningful action.",
        "Participation grew from nine hundred and sixty-four attendances in 2024 to one thousand six hundred and forty-five in 2025, with forty activities held. The center will continue providing steady support so every student can value their roots and move confidently toward the future. Thank you for listening."
    ]
    languages["ja-JP"]["cues"] = [
        "高等教育深耕計画成果展へようこそ。この展示では、国立台中科技大学の先住民族学生に対する学習・生活支援を紹介します。担当は、キャリア・カウンセリングセンターの先住民族学生資源センターです。",
        "先住民族語の検定対策講座や学習会を設け、語学力の向上とともに、文化への誇り、アイデンティティー、仲間とのつながりを育んでいます。セデック語の授業も、言葉と地域の記憶を結び付けます。",
        "さらに、先住民族文化週間、ツォウ族の竹コップ作り、清流集落やサイシャット族集落でのフィールドワーク、パイワン族の精神文化を学ぶ活動など、多彩な体験を行っています。",
        "こうした活動は、学習支援と生活支援、文化継承、地域交流を結び、学生の自信と相互理解を高めます。参加者は二〇二四年の延べ九百六十四人から、二〇二五年には延べ千六百四十五人へ増加し、合計四十回の活動を実施しました。",
        "今後も、一人ひとりが自らのルーツを大切にし、安心して学び、未来へ進めるよう支援を続けます。以上でご案内を終わります。ご清聴ありがとうございました。"
    ]
    return languages


def main():
    OUT.mkdir(exist_ok=True)
    languages = load_languages()
    for code, item in languages.items():
        spoken = " ".join(cue[2] if isinstance(cue, list) else cue for cue in item["cues"])
        text_path = ROOT / f"narration-41-{code}.txt"
        audio_path = OUT / f"narration-41-{code}.mp3"
        srt_path = ROOT / f"narration-41-{code}.srt"
        text_path.write_text(spoken, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / ".vendor")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+15%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path)
        ], check=True, env=env)
        item["audio"] = audio_path.name + "?v=1"
        item["cues"] = helper.read_cues(srt_path)

    (OUT / "languages-41.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    html = (OUT / "41.html").read_text(encoding="utf-8")
    html = re.sub(r"<title>.*?</title>", f"<title>{languages['zh-TW']['title']}｜Audio Guide</title>", html, count=1)
    html = re.sub(
        r'(<figure class="poster"><img src=")[^"]+(" alt=")[^"]+(">)',
        lambda match: match.group(1) + "poster-41.jpg?v=1" + match.group(2)
        + languages["zh-TW"]["title"] + match.group(3),
        html,
        count=1,
    )
    html = re.sub(r'(<p id="eyebrow" class="eyebrow">).*?(</p>)', r'\1GUIDE 41\2', html, count=1)
    html = re.sub(
        r'(<h1 id="title">).*?(</h1>)',
        lambda match: match.group(1) + languages["zh-TW"]["title"] + match.group(2),
        html,
        count=1,
    )
    options = "".join(f'<option value="{code}">{item["label"]}</option>' for code, item in languages.items())
    html = re.sub(r'(<select id="language">).*?(</select>)', rf'\1{options}\2', html, count=1, flags=re.S)
    html = re.sub(r'languages-40\.js\?v=\d+', "languages-41.js?v=1", html, count=1)
    html = re.sub(r'narration-40-zh-TW\.mp3\?v=\d+', "narration-41-zh-TW.mp3?v=1", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    (OUT / "41.html").write_text(html, encoding="utf-8")
    print(f"Generated 41.html and {len(languages)} audio files; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
