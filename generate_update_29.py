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

LANGUAGES = {
    "zh-TW": {
        "label": "繁體中文",
        "title": "跨齡永續健康促進暨預防延緩照護人才培育",
        "eyebrow": "高等教育深耕計畫成果展 · 29",
        "intro": "點選播放按鈕，即可一邊觀看展板，一邊收聽導覽並閱讀同步字幕。",
        "start": "點選下方按鈕開始語音導覽。",
        "hint": "請先點選圓形播放按鈕開始語音。",
        "play": "播放導覽",
        "pause": "暫停導覽",
        "progress": "導覽播放進度",
        "language": "導覽語言",
        "cues": [
            "歡迎來到高等教育深耕計畫成果展。",
            "本頁介紹智慧健康與長照產研辦公室推動的跨齡永續健康促進暨預防延緩照護人才培育成果。",
            "面對臺灣快速高齡化，以及失能與失智照護需求增加，計畫以善盡社會責任、促進公平健康與可近照護為核心，期望長者能在熟悉的社區中健康、有尊嚴地老化。",
            "計畫呼應 SDG 三、四、十、十一與十七，透過跨域課程、專業人才培育、智慧輔具、數位工具與社區夥伴合作，建立在地化、可持續且跨齡共學的健康促進生態系。",
            "實踐場域也從市中心拓展到大甲日南、太平永成、大里及霧峰北勢等社區，提升海線與屯區照護資源的可近性，減少城鄉差距。",
            "辦公室建立協助員社群及跨齡永續銀髮照護整合平台，提供回訓與參訪資訊。",
            "整體滿意度達五分中的四點八三分，並規劃銜接指導員課程，延續服務人力。",
            "一百一十四年度共辦理六十場校外社區活動，八百六十人次學生參與，服務一千三百一十三人次社區長者、失能及失智者。",
            "學生也以智慧照護作品獲得競賽佳績，並取得兩項專利成果。",
            "學生從做中學，提升專業技能、臺語溝通與跨域合作能力，也更理解長照職涯的發展可能。",
            "長者則透過健康促進、數位學習與青銀交流維持活力及社會連結。",
            "以上是跨齡永續健康促進暨預防延緩照護人才培育成果，感謝您的聆聽。",
        ],
    },
    "en-US": {
        "label": "English",
        "title": "Intergenerational Sustainable Health Promotion and Preventive Care Workforce Development",
        "eyebrow": "Higher Education Sprout Project Exhibition · 29",
        "intro": "Select play to view the poster, listen to the guide, and read synchronized subtitles.",
        "start": "Select the button below to begin the audio guide.",
        "hint": "Select the round play button to start.",
        "play": "Play audio guide",
        "pause": "Pause audio guide",
        "progress": "Audio guide progress",
        "language": "Guide language",
        "cues": [
            "Welcome to the Higher Education Sprout Project Achievement Exhibition.",
            "This page presents the intergenerational sustainable health promotion and preventive care workforce program led by the Smart Health and Long-Term Care Industry-Academia Office.",
            "As Taiwan's population ages rapidly and the need for disability and dementia care grows, the program focuses on social responsibility, health equity, and accessible care. Its vision is to help older adults age healthily and with dignity in familiar communities.",
            "Aligned with Sustainable Development Goals three, four, ten, eleven, and seventeen, the program combines interdisciplinary courses, professional training, smart assistive devices, digital tools, and community partnerships to create a local, sustainable, and intergenerational health-promotion ecosystem.",
            "Practice sites have expanded beyond the city center to communities in Dajia Rinan, Taiping Yongcheng, Dali, and Wufeng Beishi. This improves access to care resources in coastal and suburban districts and helps reduce regional inequality.",
            "The office also established an assistant network and an integrated intergenerational eldercare platform for refresher training and visit information.",
            "Overall satisfaction reached four point eight three out of five, and a bridging instructor course is being planned to sustain the service workforce.",
            "In academic year 2025, the program held sixty off-campus community activities. Eight hundred sixty student participations served one thousand three hundred thirteen older adults and people living with disability or dementia.",
            "Student smart-care projects also earned competition honors and produced two patents.",
            "Through learning by doing, students strengthened professional skills, Taiwanese-language communication, and interdisciplinary teamwork while discovering career possibilities in long-term care.",
            "Older adults gained vitality and social connection through health promotion, digital learning, and intergenerational exchange. Thank you for listening.",
        ],
    },
    "ja-JP": {
        "label": "日本語",
        "title": "世代をつなぐ持続可能な健康づくりと介護予防人材育成",
        "eyebrow": "高等教育深耕計画成果展・29",
        "intro": "再生ボタンを押すと、展示パネルを見ながら音声ガイドと同期字幕をご利用いただけます。",
        "start": "下のボタンを押して音声ガイドを開始してください。",
        "hint": "丸い再生ボタンを押して開始してください。",
        "play": "音声ガイドを再生",
        "pause": "一時停止",
        "progress": "音声ガイドの進行状況",
        "language": "ガイド言語",
        "cues": [
            "高等教育深耕計画成果展へようこそ。",
            "このページでは、世代をつなぐ持続可能な健康づくりと介護予防人材育成の成果を紹介します。台湾の急速な高齢化に対応し、本計画は社会的責任、健康の公平性、利用しやすいケアを柱に、高齢者が地域で健康に尊厳を保って暮らすことを目指します。",
            "持続可能な開発目標の三、四、十、十一、十七に対応し、分野横断型授業、人材育成、スマート福祉機器、デジタルツール、地域連携を組み合わせています。",
            "活動拠点は、大甲の日南、太平の永成、大里、霧峰の北勢などへ広がり、海線地域と屯区のケア資源を利用しやすくしています。",
            "支援員コミュニティーと統合プラットフォームを整備し、再研修と見学に関する情報を提供しています。",
            "全体満足度は五点満点中四点八三で、指導員養成につなげる研修を計画し、サービス人材の継続を図ります。",
            "二〇二五年度は地域活動を六十回実施し、学生は延べ八百六十人が参加しました。高齢者や支援を必要とする方を延べ千三百十三人支援し、競技会の入賞と二件の特許成果にもつながりました。",
            "学生は実践を通じて専門技術、台湾語での対話、協働力を高め、長期ケアの仕事への理解を深めました。",
            "高齢者も健康づくりと世代間交流から活力とつながりを得ています。ご清聴ありがとうございました。",
        ],
    },
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
    for code, item in LANGUAGES.items():
        text_path = ROOT / f"narration-29-{code}.txt"
        audio_path = ROOT / f"narration-29-{code}.mp3"
        srt_path = ROOT / f"narration-29-{code}.srt"
        text_path.write_text(" ".join(item["cues"]), encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=3"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-29.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(LANGUAGES, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "29.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-29\.js\?v=\d+', "languages-29.js?v=3", html, count=1)
    html = re.sub(r'narration-29-zh-TW\.mp3\?v=\d+', "narration-29-zh-TW.mp3?v=3", html, count=1)
    duration = LANGUAGES["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 29; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
