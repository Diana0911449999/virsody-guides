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
        "另有二百三十人次參與培訓，一百六十三人報考相關證照，一百三十九人通過，整體通過率同樣為百分之八十五。",
        "另有二百三十人次參與SAP辦公室辦理之培訓課程，其中一百六十三人報考相關證照，一百三十九人通過，整體通過率為百分之八十五。",
    ),
    "en-US": (
        "Another two hundred thirty training participations led to one hundred sixty-three exam candidates and one hundred thirty-nine passes, again reaching eighty-five percent.",
        "Another two hundred thirty participations joined training courses organized by the SAP Office; among them, one hundred sixty-three registered for related certification exams, one hundred thirty-nine passed, and the overall pass rate was eighty-five percent.",
    ),
    "es-ES": (
        "Además, doscientas treinta participaciones en formación produjeron ciento sesenta y tres candidatos y ciento treinta y nueve aprobados.",
        "Además, hubo doscientas treinta participaciones en cursos de formación organizados por la oficina SAP; de ellas, ciento sesenta y tres se presentaron a certificaciones relacionadas, ciento treinta y nueve aprobaron y la tasa global de aprobación fue del ochenta y cinco por ciento.",
    ),
    "fr-FR": (
        "Deux cent trente participations à la formation ont aussi conduit à cent trente-neuf réussites sur cent soixante-trois candidats.",
        "Deux cent trente participations ont été enregistrées aux formations organisées par le bureau SAP; parmi elles, cent soixante-trois personnes se sont présentées aux certifications correspondantes, cent trente-neuf ont réussi et le taux global de réussite a été de quatre-vingt-cinq pour cent.",
    ),
    "de-DE": (
        "Weitere zweihundertdreißig Schulungsteilnahmen führten zu einhundertdreiundsechzig Prüfungen und einhundertneununddreißig Erfolgen.",
        "Weitere zweihundertdreißig Teilnahmen entfielen auf Schulungen des SAP-Büros; davon traten einhundertdreiundsechzig Personen zu entsprechenden Zertifikatsprüfungen an, einhundertneununddreißig bestanden, und die Gesamterfolgsquote lag bei fünfundachtzig Prozent.",
    ),
    "ja-JP": (
        "研修には延べ二百三十人が参加し、百六十三名が関連試験を受け、百三十九名が合格しました。",
        "SAPオフィスが実施した研修には延べ二百三十人が参加し、そのうち百六十三名が関連資格試験を受験、百三十九名が合格し、全体の合格率は八十五パーセントでした。",
    ),
    "ko-KR": (
        "또한 연인원 이백삼십 명이 교육에 참여했고 백육십삼 명이 관련 시험에 응시하여 백삼십구 명이 합격했습니다.",
        "또한 연인원 이백삼십 명이 SAP 사무실에서 운영한 교육 과정에 참여했으며, 이 가운데 백육십삼 명이 관련 자격시험에 응시하고 백삼십구 명이 합격해 전체 합격률은 팔십오 퍼센트였습니다.",
    ),
    "it-IT": (
        "Altre duecentotrenta partecipazioni formative hanno portato a centosessantatré candidati e centotrentanove promossi.",
        "Altre duecentotrenta partecipazioni hanno riguardato i corsi organizzati dall’ufficio SAP; tra queste, centosessantatré persone hanno sostenuto le relative certificazioni, centotrentanove le hanno superate e il tasso complessivo di successo è stato dell’ottantacinque per cento.",
    ),
    "pt-PT": (
        "Outras duzentas e trinta participações em formação resultaram em cento e sessenta e três candidatos e cento e trinta e nove aprovações.",
        "Registaram-se ainda duzentas e trinta participações nos cursos de formação organizados pelo gabinete SAP; destas, cento e sessenta e três pessoas realizaram certificações relacionadas, cento e trinta e nove foram aprovadas e a taxa global de aprovação foi de oitenta e cinco por cento.",
    ),
    "ru-RU": (
        "Ещё двести тридцать участий в обучении привели к ста шестидесяти трём кандидатам и ста тридцати девяти успешным результатам.",
        "Ещё двести тридцать участий пришлось на учебные курсы офиса SAP; из них сто шестьдесят три человека сдавали соответствующие сертификационные экзамены, сто тридцать девять успешно их прошли, а общий процент успешной сдачи составил восемьдесят пять процентов.",
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
            subtitle = " ".join(rows[2:]).strip()
            subtitle = re.sub("sap", "SAP", subtitle, flags=re.IGNORECASE)
            cues.append([seconds(start), seconds(end), subtitle])
    return cues


def main():
    raw = (ROOT / "languages-08.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if set(languages) != set(VOICES) or set(languages) != set(REPLACEMENTS):
        raise RuntimeError("Language set does not match the 10 configured guides")

    for code, item in languages.items():
        old, new = REPLACEMENTS[code]
        display_text = " ".join(cue[2] for cue in item["cues"])
        display_text = re.sub("sap", "SAP", display_text, flags=re.IGNORECASE)
        if old in display_text:
            display_text = display_text.replace(old, new)
        elif new not in display_text:
            raise RuntimeError(f"Expected original or corrected text not found for {code}")

        # Lowercase forces SAP to be pronounced as one word instead of three letters.
        spoken_text = display_text.replace("SAP", "sap")
        text_path = ROOT / f"narration-08-{code}.txt"
        audio_path = ROOT / f"narration-08-{code}.mp3"
        srt_path = ROOT / f"narration-08-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-08.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "08.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-08\.js(?:\?v=\d+)?', "languages-08.js?v=2", html, count=1)
    html = re.sub(r'narration-08-zh-TW\.mp3(?:\?v=\d+)?', "narration-08-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 08 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
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
        "另有二百三十人次參與培訓，一百六十三人報考相關證照，一百三十九人通過，整體通過率同樣為百分之八十五。",
        "另有二百三十人次參與SAP辦公室辦理之培訓課程，其中一百六十三人報考相關證照，一百三十九人通過，整體通過率為百分之八十五。",
    ),
    "en-US": (
        "Another two hundred thirty training participations led to one hundred sixty-three exam candidates and one hundred thirty-nine passes, again reaching eighty-five percent.",
        "Another two hundred thirty participations joined training courses organized by the SAP Office; among them, one hundred sixty-three registered for related certification exams, one hundred thirty-nine passed, and the overall pass rate was eighty-five percent.",
    ),
    "es-ES": (
        "Además, doscientas treinta participaciones en formación produjeron ciento sesenta y tres candidatos y ciento treinta y nueve aprobados.",
        "Además, hubo doscientas treinta participaciones en cursos de formación organizados por la oficina SAP; de ellas, ciento sesenta y tres se presentaron a certificaciones relacionadas, ciento treinta y nueve aprobaron y la tasa global de aprobación fue del ochenta y cinco por ciento.",
    ),
    "fr-FR": (
        "Deux cent trente participations à la formation ont aussi conduit à cent trente-neuf réussites sur cent soixante-trois candidats.",
        "Deux cent trente participations ont été enregistrées aux formations organisées par le bureau SAP; parmi elles, cent soixante-trois personnes se sont présentées aux certifications correspondantes, cent trente-neuf ont réussi et le taux global de réussite a été de quatre-vingt-cinq pour cent.",
    ),
    "de-DE": (
        "Weitere zweihundertdreißig Schulungsteilnahmen führten zu einhundertdreiundsechzig Prüfungen und einhundertneununddreißig Erfolgen.",
        "Weitere zweihundertdreißig Teilnahmen entfielen auf Schulungen des SAP-Büros; davon traten einhundertdreiundsechzig Personen zu entsprechenden Zertifikatsprüfungen an, einhundertneununddreißig bestanden, und die Gesamterfolgsquote lag bei fünfundachtzig Prozent.",
    ),
    "ja-JP": (
        "研修には延べ二百三十人が参加し、百六十三名が関連試験を受け、百三十九名が合格しました。",
        "SAPオフィスが実施した研修には延べ二百三十人が参加し、そのうち百六十三名が関連資格試験を受験、百三十九名が合格し、全体の合格率は八十五パーセントでした。",
    ),
    "ko-KR": (
        "또한 연인원 이백삼십 명이 교육에 참여했고 백육십삼 명이 관련 시험에 응시하여 백삼십구 명이 합격했습니다.",
        "또한 연인원 이백삼십 명이 SAP 사무실에서 운영한 교육 과정에 참여했으며, 이 가운데 백육십삼 명이 관련 자격시험에 응시하고 백삼십구 명이 합격해 전체 합격률은 팔십오 퍼센트였습니다.",
    ),
    "it-IT": (
        "Altre duecentotrenta partecipazioni formative hanno portato a centosessantatré candidati e centotrentanove promossi.",
        "Altre duecentotrenta partecipazioni hanno riguardato i corsi organizzati dall’ufficio SAP; tra queste, centosessantatré persone hanno sostenuto le relative certificazioni, centotrentanove le hanno superate e il tasso complessivo di successo è stato dell’ottantacinque per cento.",
    ),
    "pt-PT": (
        "Outras duzentas e trinta participações em formação resultaram em cento e sessenta e três candidatos e cento e trinta e nove aprovações.",
        "Registaram-se ainda duzentas e trinta participações nos cursos de formação organizados pelo gabinete SAP; destas, cento e sessenta e três pessoas realizaram certificações relacionadas, cento e trinta e nove foram aprovadas e a taxa global de aprovação foi de oitenta e cinco por cento.",
    ),
    "ru-RU": (
        "Ещё двести тридцать участий в обучении привели к ста шестидесяти трём кандидатам и ста тридцати девяти успешным результатам.",
        "Ещё двести тридцать участий пришлось на учебные курсы офиса SAP; из них сто шестьдесят три человека сдавали соответствующие сертификационные экзамены, сто тридцать девять успешно их прошли, а общий процент успешной сдачи составил восемьдесят пять процентов.",
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
            subtitle = " ".join(rows[2:]).strip()
            subtitle = re.sub("sap", "SAP", subtitle, flags=re.IGNORECASE)
            cues.append([seconds(start), seconds(end), subtitle])
    return cues


def main():
    raw = (ROOT / "languages-08.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if set(languages) != set(VOICES) or set(languages) != set(REPLACEMENTS):
        raise RuntimeError("Language set does not match the 10 configured guides")

    for code, item in languages.items():
        old, new = REPLACEMENTS[code]
        display_text = " ".join(cue[2] for cue in item["cues"])
        if old in display_text:
            display_text = display_text.replace(old, new)
        elif new not in display_text:
            raise RuntimeError(f"Expected original or corrected text not found for {code}")

        # Lowercase forces SAP to be pronounced as one word instead of three letters.
        spoken_text = display_text.replace("SAP", "sap")
        text_path = ROOT / f"narration-08-{code}.txt"
        audio_path = ROOT / f"narration-08-{code}.mp3"
        srt_path = ROOT / f"narration-08-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-08.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "08.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-08\.js(?:\?v=\d+)?', "languages-08.js?v=2", html, count=1)
    html = re.sub(r'narration-08-zh-TW\.mp3(?:\?v=\d+)?', "narration-08-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 08 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
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
        "另有二百三十人次參與培訓，一百六十三人報考相關證照，一百三十九人通過，整體通過率同樣為百分之八十五。",
        "另有二百三十人次參與SAP辦公室辦理之培訓課程，其中一百六十三人報考相關證照，一百三十九人通過，整體通過率為百分之八十五。",
    ),
    "en-US": (
        "Another two hundred thirty training participations led to one hundred sixty-three exam candidates and one hundred thirty-nine passes, again reaching eighty-five percent.",
        "Another two hundred thirty participations joined training courses organized by the SAP Office; among them, one hundred sixty-three registered for related certification exams, one hundred thirty-nine passed, and the overall pass rate was eighty-five percent.",
    ),
    "es-ES": (
        "Además, doscientas treinta participaciones en formación produjeron ciento sesenta y tres candidatos y ciento treinta y nueve aprobados.",
        "Además, hubo doscientas treinta participaciones en cursos de formación organizados por la oficina SAP; de ellas, ciento sesenta y tres se presentaron a certificaciones relacionadas, ciento treinta y nueve aprobaron y la tasa global de aprobación fue del ochenta y cinco por ciento.",
    ),
    "fr-FR": (
        "Deux cent trente participations à la formation ont aussi conduit à cent trente-neuf réussites sur cent soixante-trois candidats.",
        "Deux cent trente participations ont été enregistrées aux formations organisées par le bureau SAP; parmi elles, cent soixante-trois personnes se sont présentées aux certifications correspondantes, cent trente-neuf ont réussi et le taux global de réussite a été de quatre-vingt-cinq pour cent.",
    ),
    "de-DE": (
        "Weitere zweihundertdreißig Schulungsteilnahmen führten zu einhundertdreiundsechzig Prüfungen und einhundertneununddreißig Erfolgen.",
        "Weitere zweihundertdreißig Teilnahmen entfielen auf Schulungen des SAP-Büros; davon traten einhundertdreiundsechzig Personen zu entsprechenden Zertifikatsprüfungen an, einhundertneununddreißig bestanden, und die Gesamterfolgsquote lag bei fünfundachtzig Prozent.",
    ),
    "ja-JP": (
        "研修には延べ二百三十人が参加し、百六十三名が関連試験を受け、百三十九名が合格しました。",
        "SAPオフィスが実施した研修には延べ二百三十人が参加し、そのうち百六十三名が関連資格試験を受験、百三十九名が合格し、全体の合格率は八十五パーセントでした。",
    ),
    "ko-KR": (
        "또한 연인원 이백삼십 명이 교육에 참여했고 백육십삼 명이 관련 시험에 응시하여 백삼십구 명이 합격했습니다.",
        "또한 연인원 이백삼십 명이 SAP 사무실에서 운영한 교육 과정에 참여했으며, 이 가운데 백육십삼 명이 관련 자격시험에 응시하고 백삼십구 명이 합격해 전체 합격률은 팔십오 퍼센트였습니다.",
    ),
    "it-IT": (
        "Altre duecentotrenta partecipazioni formative hanno portato a centosessantatré candidati e centotrentanove promossi.",
        "Altre duecentotrenta partecipazioni hanno riguardato i corsi organizzati dall’ufficio SAP; tra queste, centosessantatré persone hanno sostenuto le relative certificazioni, centotrentanove le hanno superate e il tasso complessivo di successo è stato dell’ottantacinque per cento.",
    ),
    "pt-PT": (
        "Outras duzentas e trinta participações em formação resultaram em cento e sessenta e três candidatos e cento e trinta e nove aprovações.",
        "Registaram-se ainda duzentas e trinta participações nos cursos de formação organizados pelo gabinete SAP; destas, cento e sessenta e três pessoas realizaram certificações relacionadas, cento e trinta e nove foram aprovadas e a taxa global de aprovação foi de oitenta e cinco por cento.",
    ),
    "ru-RU": (
        "Ещё двести тридцать участий в обучении привели к ста шестидесяти трём кандидатам и ста тридцати девяти успешным результатам.",
        "Ещё двести тридцать участий пришлось на учебные курсы офиса SAP; из них сто шестьдесят три человека сдавали соответствующие сертификационные экзамены, сто тридцать девять успешно их прошли, а общий процент успешной сдачи составил восемьдесят пять процентов.",
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
            subtitle = " ".join(rows[2:]).strip()
            subtitle = re.sub("sap", "SAP", subtitle, flags=re.IGNORECASE)
            cues.append([seconds(start), seconds(end), subtitle])
    return cues


def main():
    raw = (ROOT / "languages-08.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if set(languages) != set(VOICES) or set(languages) != set(REPLACEMENTS):
        raise RuntimeError("Language set does not match the 10 configured guides")

    for code, item in languages.items():
        old, new = REPLACEMENTS[code]
        display_text = " ".join(cue[2] for cue in item["cues"])
        if old not in display_text:
            raise RuntimeError(f"Expected text not found for {code}: {old}")
        display_text = display_text.replace(old, new)

        # Lowercase forces SAP to be pronounced as one word instead of three letters.
        spoken_text = display_text.replace("SAP", "sap")
        text_path = ROOT / f"narration-08-{code}.txt"
        audio_path = ROOT / f"narration-08-{code}.mp3"
        srt_path = ROOT / f"narration-08-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-08.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "08.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-08\.js(?:\?v=\d+)?', "languages-08.js?v=2", html, count=1)
    html = re.sub(r'narration-08-zh-TW\.mp3(?:\?v=\d+)?', "narration-08-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 08 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
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
        "另有二百三十人次參與培訓，一百六十三人報考相關證照，一百三十九人通過，整體通過率同樣為百分之八十五。",
        "另有二百三十人次參與SAP辦公室辦理之培訓課程，其中一百六十三人報考相關證照，一百三十九人通過，整體通過率為百分之八十五。",
    ),
    "en-US": (
        "Another two hundred thirty training participations led to one hundred sixty-three exam candidates and one hundred thirty-nine passes, again reaching eighty-five percent.",
        "Another two hundred thirty participations joined training courses organized by the SAP Office; among them, one hundred sixty-three registered for related certification exams, one hundred thirty-nine passed, and the overall pass rate was eighty-five percent.",
    ),
    "es-ES": (
        "Además, doscientas treinta participaciones en formación produjeron ciento sesenta y tres candidatos y ciento treinta y nueve aprobados.",
        "Además, hubo doscientas treinta participaciones en cursos de formación organizados por la oficina SAP; de ellas, ciento sesenta y tres se presentaron a certificaciones relacionadas, ciento treinta y nueve aprobaron y la tasa global de aprobación fue del ochenta y cinco por ciento.",
    ),
    "fr-FR": (
        "Deux cent trente participations à la formation ont aussi conduit à cent trente-neuf réussites sur cent soixante-trois candidats.",
        "Deux cent trente participations ont été enregistrées aux formations organisées par le bureau SAP; parmi elles, cent soixante-trois personnes se sont présentées aux certifications correspondantes, cent trente-neuf ont réussi et le taux global de réussite a été de quatre-vingt-cinq pour cent.",
    ),
    "de-DE": (
        "Weitere zweihundertdreißig Schulungsteilnahmen führten zu einhundertdreiundsechzig Prüfungen und einhundertneununddreißig Erfolgen.",
        "Weitere zweihundertdreißig Teilnahmen entfielen auf Schulungen des SAP-Büros; davon traten einhundertdreiundsechzig Personen zu entsprechenden Zertifikatsprüfungen an, einhundertneununddreißig bestanden, und die Gesamterfolgsquote lag bei fünfundachtzig Prozent.",
    ),
    "ja-JP": (
        "研修には延べ二百三十人が参加し、百六十三名が関連試験を受け、百三十九名が合格しました。",
        "SAPオフィスが実施した研修には延べ二百三十人が参加し、そのうち百六十三名が関連資格試験を受験、百三十九名が合格し、全体の合格率は八十五パーセントでした。",
    ),
    "ko-KR": (
        "또한 연인원 이백삼십 명이 교육에 참여했고 백육십삼 명이 관련 시험에 응시하여 백삼십구 명이 합격했습니다.",
        "또한 연인원 이백삼십 명이 SAP 사무실에서 운영한 교육 과정에 참여했으며, 이 가운데 백육십삼 명이 관련 자격시험에 응시하고 백삼십구 명이 합격해 전체 합격률은 팔십오 퍼센트였습니다.",
    ),
    "it-IT": (
        "Altre duecentotrenta partecipazioni formative hanno portato a centosessantatré candidati e centotrentanove promossi.",
        "Altre duecentotrenta partecipazioni hanno riguardato i corsi organizzati dall’ufficio SAP; tra queste, centosessantatré persone hanno sostenuto le relative certificazioni, centotrentanove le hanno superate e il tasso complessivo di successo è stato dell’ottantacinque per cento.",
    ),
    "pt-PT": (
        "Outras duzentas e trinta participações em formação resultaram em cento e sessenta e três candidatos e cento e trinta e nove aprovações.",
        "Registaram-se ainda duzentas e trinta participações nos cursos de formação organizados pelo gabinete SAP; destas, cento e sessenta e três pessoas realizaram certificações relacionadas, cento e trinta e nove foram aprovadas e a taxa global de aprovação foi de oitenta e cinco por cento.",
    ),
    "ru-RU": (
        "Ещё двести тридцать участий в обучении привели к ста шестидесяти трём кандидатам и ста тридцати девяти успешным результатам.",
        "Ещё двести тридцать участий пришлось на учебные курсы офиса SAP; из них сто шестьдесят три человека сдавали соответствующие сертификационные экзамены, сто тридцать девять успешно их прошли, а общий процент успешной сдачи составил восемьдесят пять процентов.",
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
            subtitle = " ".join(rows[2:]).strip()
            subtitle = re.sub(r"(?i)\bsap\b", "SAP", subtitle)
            cues.append([seconds(start), seconds(end), subtitle])
    return cues


def main():
    raw = (ROOT / "languages-08.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if set(languages) != set(VOICES) or set(languages) != set(REPLACEMENTS):
        raise RuntimeError("Language set does not match the 10 configured guides")

    for code, item in languages.items():
        old, new = REPLACEMENTS[code]
        display_text = " ".join(cue[2] for cue in item["cues"])
        if old not in display_text:
            raise RuntimeError(f"Expected text not found for {code}: {old}")
        display_text = display_text.replace(old, new)

        # Lowercase forces SAP to be pronounced as one word instead of three letters.
        spoken_text = display_text.replace("SAP", "sap")
        text_path = ROOT / f"narration-08-{code}.txt"
        audio_path = ROOT / f"narration-08-{code}.mp3"
        srt_path = ROOT / f"narration-08-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-08.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "08.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-08\.js(?:\?v=\d+)?', "languages-08.js?v=2", html, count=1)
    html = re.sub(r'narration-08-zh-TW\.mp3(?:\?v=\d+)?', "narration-08-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 08 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
