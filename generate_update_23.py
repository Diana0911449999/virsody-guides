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

UPDATES = {
    "zh-TW": {
        "title": "TronClass創新教學平台與首次申請教學實踐研究計畫補助及鼓勵教師參與教學實踐研究計畫",
        "overview": "本展板介紹 TronClass 創新教學平台，以及首次申請教學實踐研究計畫補助及鼓勵教師參與教學實踐研究計畫的推動成果。",
        "transition_index": 6,
        "transition": "第二項成果是首次申請教學實踐研究計畫補助及鼓勵教師參與教學實踐研究計畫。",
    },
    "en-US": {
        "title": "TronClass Innovative Learning Platform, First-Time Teaching Practice Research Grants, and Faculty Participation Incentives",
        "overview": "This panel presents the TronClass innovative learning platform, grants for first-time applicants to the Teaching Practice Research Program, and incentives encouraging faculty participation in teaching practice research.",
        "transition_index": 7,
        "transition": "The second achievement combines grants for first-time Teaching Practice Research Program applicants with incentives encouraging faculty participation in teaching practice research.",
    },
    "es-ES": {
        "title": "Plataforma innovadora TronClass, ayudas para primeras solicitudes e incentivos a la investigación docente",
        "overview": "Este panel presenta la plataforma innovadora TronClass, las ayudas para la primera solicitud al Programa de Investigación de la Práctica Docente y los incentivos para fomentar la participación del profesorado.",
        "transition_index": 5,
        "transition": "La segunda iniciativa combina ayudas para primeras solicitudes con incentivos que animan al profesorado a participar en la investigación de la práctica docente.",
    },
    "fr-FR": {
        "title": "Plateforme TronClass, aide aux premières demandes et encouragement à la recherche pédagogique",
        "overview": "Ce panneau présente la plateforme innovante TronClass, l’aide aux premières demandes de projets de recherche sur les pratiques pédagogiques et les mesures encourageant la participation des enseignants.",
        "transition_index": 5,
        "transition": "Le second dispositif associe l’aide aux premières demandes et les mesures encourageant les enseignants à participer à la recherche sur les pratiques pédagogiques.",
    },
    "de-DE": {
        "title": "TronClass-Lernplattform, Förderung von Erstanträgen und Teilnahme an Lehrpraxisforschung",
        "overview": "Diese Tafel stellt die innovative Lernplattform TronClass, die Förderung von Erstanträgen und Anreize zur Teilnahme von Lehrkräften an der Lehrpraxisforschung vor.",
        "transition_index": 6,
        "transition": "Das zweite Vorhaben verbindet die Förderung von Erstanträgen mit Anreizen für Lehrkräfte, sich an der Lehrpraxisforschung zu beteiligen.",
    },
    "ja-JP": {
        "title": "TronClass革新的教育プラットフォーム、教育実践研究の初回申請補助と参加奨励",
        "overview": "この展示では、TronClass革新的教育プラットフォーム、教育実践研究計画の初回申請補助、そして教員の教育実践研究への参加を奨励する取り組みを紹介します。",
        "transition_index": 6,
        "transition": "第二の成果は、教育実践研究計画の初回申請補助と、教員の教育実践研究への参加奨励です。",
    },
    "ko-KR": {
        "title": "TronClass 혁신 교육 플랫폼, 교수실천 연구 첫 신청 지원과 참여 장려",
        "overview": "이 전시는 TronClass 혁신 교육 플랫폼, 교수실천 연구계획 첫 신청 지원, 그리고 교원의 교수실천 연구 참여를 장려하는 사업 성과를 소개합니다.",
        "transition_index": 6,
        "transition": "두 번째 성과는 교수실천 연구계획 첫 신청 지원과 교원의 교수실천 연구 참여 장려입니다.",
    },
    "it-IT": {
        "title": "Piattaforma TronClass, sostegno alle prime domande e partecipazione alla ricerca didattica",
        "overview": "Il pannello presenta la piattaforma innovativa TronClass, il sostegno ai docenti che presentano per la prima volta un progetto di ricerca sulla pratica didattica e gli incentivi alla partecipazione dei docenti.",
        "transition_index": 5,
        "transition": "La seconda iniziativa unisce il sostegno alle prime domande e gli incentivi che incoraggiano i docenti a partecipare alla ricerca sulla pratica didattica.",
    },
    "pt-PT": {
        "title": "Plataforma TronClass, apoio a primeiras candidaturas e participação na investigação pedagógica",
        "overview": "Este painel apresenta a plataforma inovadora TronClass, o apoio à primeira candidatura de projetos de investigação da prática pedagógica e os incentivos à participação dos docentes.",
        "transition_index": 5,
        "transition": "A segunda iniciativa reúne o apoio às primeiras candidaturas e os incentivos que encorajam os docentes a participar na investigação da prática pedagógica.",
    },
    "ru-RU": {
        "title": "Платформа TronClass, поддержка первых заявок и участие в исследованиях преподавательской практики",
        "overview": "Этот стенд представляет инновационную платформу TronClass, поддержку первых заявок на исследования преподавательской практики и меры, поощряющие участие преподавателей.",
        "transition_index": 6,
        "transition": "Второе направление объединяет поддержку первых заявок и меры, поощряющие преподавателей участвовать в исследованиях преподавательской практики.",
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
    raw = (ROOT / "languages-23.js").read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if set(languages) != set(VOICES) or set(languages) != set(UPDATES):
        raise RuntimeError("Language set does not match the 10 configured guides")

    for code, item in languages.items():
        update = UPDATES[code]
        item["title"] = update["title"]
        item["cues"][1][2] = update["overview"]
        item["cues"][update["transition_index"]][2] = update["transition"]
        spoken_text = " ".join(cue[2] for cue in item["cues"])
        text_path = ROOT / f"narration-23-{code}.txt"
        audio_path = ROOT / f"narration-23-{code}.mp3"
        srt_path = ROOT / f"narration-23-{code}.srt"
        text_path.write_text(spoken_text, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code],
            "--rate=+10%", "--write-media", str(audio_path), "--write-subtitles", str(srt_path),
        ], check=True)
        item["audio"] = audio_path.name + "?v=2"
        item["cues"] = read_cues(srt_path)

    (ROOT / "languages-23.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    title = UPDATES["zh-TW"]["title"]
    html_path = ROOT / "23.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r"<title>.*?</title>", f"<title>{title}｜Audio Guide</title>", html, count=1)
    html = re.sub(r'<h1 id="title">.*?</h1>', f'<h1 id="title">{title}</h1>', html, count=1)
    html = re.sub(r'alt="[^"]*"', f'alt="{title}海報"', html, count=1)
    html = re.sub(r'poster-23\.jpg(?:\?v=\d+)?', "poster-23.jpg?v=2", html, count=1)
    html = re.sub(r'languages-23\.js(?:\?v=\d+)?', "languages-23.js?v=2", html, count=1)
    html = re.sub(r'narration-23-zh-TW\.mp3(?:\?v=\d+)?', "narration-23-zh-TW.mp3?v=2", html, count=1)
    duration = languages["zh-TW"]["cues"][-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Updated guide 23 in {len(languages)} languages; Chinese duration {duration:.1f}s")


if __name__ == "__main__":
    main()
