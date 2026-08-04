import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import generate_multilang_24 as base
except ModuleNotFoundError:
    base = None


ROOT = Path(__file__).resolve().parent
OUT = ROOT if os.environ.get("GITHUB_ACTIONS") == "true" else ROOT / "github-pages"
EDGE_TTS = ROOT / ".vendor" / "bin" / "edge-tts.exe"
POSTER_SOURCE = Path(r"D:\00 珮丞\2.網路後端平台\4.線上成果展\114年度\更新版規劃(黑色背景)\圖片\26.(一).1-圖書館Journals 學術期刊資料庫等-5種電子資源使用 & 學生專業實務技術能力推動成效.jpg")
VOICES = base.VOICES if base else {
    "zh-TW": "zh-TW-HsiaoChenNeural", "en-US": "en-US-JennyNeural",
    "es-ES": "es-ES-ElviraNeural", "fr-FR": "fr-FR-DeniseNeural",
    "de-DE": "de-DE-KatjaNeural", "ja-JP": "ja-JP-NanamiNeural",
    "ko-KR": "ko-KR-SunHiNeural", "it-IT": "it-IT-ElsaNeural",
    "pt-PT": "pt-PT-RaquelNeural", "ru-RU": "ru-RU-SvetlanaNeural",
}

TITLES = {
    "zh-TW": "圖書館電子資源使用與學生專業實務技術能力推動成效",
    "en-US": "Library E-Resources and Student Professional Practice Development",
    "es-ES": "Recursos electrónicos de la biblioteca y desarrollo de competencias profesionales",
    "fr-FR": "Ressources électroniques de la bibliothèque et développement des compétences professionnelles",
    "de-DE": "Elektronische Bibliotheksressourcen und Förderung berufspraktischer Kompetenzen",
    "ja-JP": "図書館電子資料の活用と学生の専門実務能力向上",
    "ko-KR": "도서관 전자자료 활용과 학생 전문 실무 역량 강화",
    "it-IT": "Risorse elettroniche della biblioteca e sviluppo delle competenze professionali",
    "pt-PT": "Recursos eletrónicos da biblioteca e desenvolvimento de competências profissionais",
    "ru-RU": "Электронные ресурсы библиотеки и развитие профессиональных практических навыков",
}

TEXTS = {
    "zh-TW": """歡迎來到高等教育深耕計畫成果展。這張展板呈現圖書館電子資源，以及學生專業實務技術能力的推動成果。首先，圖書館透過資料庫、論文比對系統、利用課程與推廣活動，強化學生的資訊素養，讓電子資源成為教學與研究的重要後盾。114年度，Journals學術期刊資料庫全文下載五萬二千九百一十五次，Theses學位論文資料庫八千四百五十次，JSTOR全文下載四千三百七十一次；Symskan文獻比對四百零三篇，Turnitin英文AI寫作偵測二百八十一次，接近預期值的三倍。資料庫課程共五十八小時，涵蓋三十七個班級、八百七十六人參與。圖書館也以主動服務與學科館員轉型，獲得全國大專校院圖書館精進與創新競賽佳作。第二部分聚焦學生職涯與實務能力。學校透過校外實習、業界導師、職涯會談、專業講座與學習歷程，協助學生縮短學用落差。114年度共有一千五百七十九人次參與實習；聘請二十九位業界導師，輔導一千三百八十五人次；二十三位職涯輔導老師提供七百四十一人次會談，另完成七場輔導研習、五場專業講座與工作坊，以及二百二十五人次職涯諮詢。學生學習歷程EP平台使用率達百分之八十八點六一。這些成果讓知識檢索、專業實作與職涯準備相互連結，陪伴學生更有信心地走向未來。感謝您的聆聽。""",
    "en-US": """Welcome to the Higher Education Sprout Project Achievement Exhibition. This panel presents the use of library e-resources and the development of students’ professional practice skills. The library strengthens information literacy through databases, originality-checking systems, training courses, and outreach. In year 114, the Journals database recorded 52,915 full-text downloads, Theses recorded 8,450, and JSTOR recorded 4,371. Symskan processed 403 similarity checks, while Turnitin’s English AI-writing detector processed 281, nearly three times the expected target. Database training totaled 58 hours, reaching 876 participants in 37 classes. The library’s shift toward proactive subject-librarian services also earned recognition in a national innovation competition for university libraries. The second section focuses on career readiness and practical skills. Through off-campus internships, industry mentors, career interviews, professional workshops, and learning portfolios, the university helps students connect academic learning with the workplace. In year 114, internships involved 1,579 student participations. Twenty-nine industry mentors supported 1,385 participations, while 23 career advisers provided 741 individual consultations. The university also held seven adviser-training sessions, five professional lectures and workshops, and delivered 225 career consultations. Use of the student e-portfolio platform reached 88.61 percent. Together, these initiatives connect reliable research, professional practice, and career planning, helping students move toward the future with greater confidence. Thank you for listening.""",
    "es-ES": """Bienvenidos a la Exposición de Logros del Proyecto Sprout de Educación Superior. Este panel presenta el uso de los recursos electrónicos de la biblioteca y el desarrollo de las competencias profesionales del alumnado. La biblioteca fortalece la alfabetización informacional mediante bases de datos, sistemas de comparación de textos, cursos y actividades de difusión. En el año 114, Journals registró 52.915 descargas de texto completo, Theses 8.450 y JSTOR 4.371. Symskan realizó 403 comparaciones y el detector de escritura con inteligencia artificial en inglés de Turnitin alcanzó 281 usos, casi tres veces la meta prevista. La formación sobre bases de datos sumó 58 horas y llegó a 876 participantes de 37 clases. La transformación hacia servicios bibliotecarios más activos también recibió un reconocimiento nacional a la innovación. La segunda parte se centra en la preparación profesional. Mediante prácticas externas, mentores del sector, entrevistas de orientación, talleres y portafolios de aprendizaje, la universidad reduce la distancia entre el estudio y el empleo. En el año 114 hubo 1.579 participaciones en prácticas. Veintinueve mentores atendieron 1.385 participaciones, y 23 orientadores ofrecieron 741 entrevistas. También se realizaron siete jornadas de formación, cinco conferencias y talleres profesionales, y 225 consultas de carrera. El uso de la plataforma de portafolio electrónico alcanzó el 88,61 por ciento. Estas iniciativas conectan investigación, práctica y planificación profesional para que los estudiantes avancen con mayor confianza. Gracias por su atención.""",
    "fr-FR": """Bienvenue à l’exposition des réalisations du Projet Sprout pour l’enseignement supérieur. Ce panneau présente l’utilisation des ressources électroniques de la bibliothèque et le développement des compétences professionnelles des étudiants. La bibliothèque renforce la maîtrise de l’information grâce aux bases de données, aux outils de comparaison de textes, aux formations et aux actions de sensibilisation. En année 114, Journals a enregistré 52 915 téléchargements en texte intégral, Theses 8 450 et JSTOR 4 371. Symskan a traité 403 vérifications de similarité, tandis que le détecteur d’écriture en anglais par intelligence artificielle de Turnitin a atteint 281 utilisations, soit près de trois fois l’objectif. Les formations aux bases de données ont totalisé 58 heures et réuni 876 participants dans 37 classes. La transition vers un service actif de bibliothécaires disciplinaires a aussi reçu une distinction nationale. La seconde partie concerne l’insertion professionnelle. Les stages, les mentors issus de l’industrie, les entretiens de carrière, les ateliers et les portfolios rapprochent les apprentissages du monde du travail. En année 114, 1 579 participations à des stages ont été enregistrées. Vingt-neuf mentors ont accompagné 1 385 participations et 23 conseillers ont assuré 741 entretiens. Sept formations, cinq conférences et ateliers professionnels, ainsi que 225 consultations de carrière ont également été proposés. Le taux d’utilisation de la plateforme de portfolio électronique a atteint 88,61 pour cent. Ces actions relient recherche, pratique et projet professionnel afin d’aider les étudiants à avancer avec confiance. Merci de votre écoute.""",
    "de-DE": """Willkommen zur Ergebnisausstellung des Higher Education Sprout Project. Diese Tafel zeigt die Nutzung elektronischer Bibliotheksressourcen und die Förderung berufspraktischer Kompetenzen. Die Bibliothek stärkt Informationskompetenz durch Datenbanken, Textvergleichssysteme, Schulungen und Öffentlichkeitsarbeit. Im Jahr 114 verzeichnete Journals 52.915 Volltextdownloads, Theses 8.450 und JSTOR 4.371. Mit Symskan wurden 403 Ähnlichkeitsprüfungen durchgeführt. Turnitins Erkennung englischer Texte mit künstlicher Intelligenz erreichte 281 Nutzungen und damit fast das Dreifache des Zielwerts. Die Datenbankschulungen umfassten 58 Stunden und erreichten 876 Teilnehmende in 37 Klassen. Der Wandel zu einem aktiven Fachreferentenservice wurde außerdem in einem nationalen Innovationswettbewerb ausgezeichnet. Der zweite Teil konzentriert sich auf Berufsorientierung und praktische Fähigkeiten. Praktika, Mentoren aus der Wirtschaft, Beratungsgespräche, Workshops und Lernportfolios verbinden Studium und Arbeitswelt. Im Jahr 114 wurden 1.579 Praktikumsteilnahmen erfasst. Neunundzwanzig Mentoren begleiteten 1.385 Teilnahmen, und 23 Laufbahnberater führten 741 Gespräche. Hinzu kamen sieben Fortbildungen, fünf Fachvorträge und Workshops sowie 225 Laufbahnberatungen. Die Nutzung der elektronischen Portfolio-Plattform erreichte 88,61 Prozent. So werden verlässliche Recherche, berufliche Praxis und Karriereplanung miteinander verbunden und Studierende auf ihrem Weg in die Zukunft gestärkt. Vielen Dank fürs Zuhören.""",
    "ja-JP": """高等教育深耕計画成果展へようこそ。このパネルでは、図書館の電子資料活用と、学生の専門実務能力を高める取り組みを紹介します。図書館は、データベース、文章類似度判定システム、利用講習、広報活動を通して、学生の情報リテラシーを支えています。114年度の全文ダウンロード数は、Journalsが5万2,915回、Thesesが8,450回、JSTORが4,371回でした。Symskanの文献比較は403件、Turnitinの英語AI文章検出は281件で、目標の約3倍となりました。データベース講習は合計58時間、37クラス、876人が参加しました。さらに、受け身のサービスから学科担当司書による積極的支援へ転換した取り組みが、全国の大学図書館革新コンテストで評価されました。後半は、学生のキャリアと実務能力です。学外実習、企業メンター、キャリア面談、専門講座、学習ポートフォリオを通して、学びと仕事の距離を縮めています。114年度の実習参加は1,579人回でした。29人の企業メンターが1,385人回を支援し、23人のキャリア担当教員が741人回の面談を行いました。さらに、研修7回、専門講座とワークショップ5回、キャリア相談225人回を実施し、EP学習履歴プラットフォームの利用率は88.61パーセントに達しました。調査、実践、進路支援を結び、学生が自信を持って未来へ進める環境を整えています。ご清聴ありがとうございました。""",
    "ko-KR": """고등교육 심화 프로젝트 성과전에 오신 것을 환영합니다. 이 전시물은 도서관 전자자료 활용과 학생 전문 실무 역량 강화 성과를 소개합니다. 도서관은 데이터베이스, 문서 유사도 검사 시스템, 이용 교육과 홍보를 통해 학생의 정보 활용 능력을 높이고 있습니다. 114년도 전문 원문 다운로드는 Journals 5만 2천915회, Theses 8천450회, JSTOR 4천371회였습니다. Symskan 문헌 검사는 403건, Turnitin 영어 AI 글쓰기 탐지는 281건으로 목표치의 약 세 배에 달했습니다. 데이터베이스 교육은 총 58시간 동안 37개 학급, 876명이 참여했습니다. 또한 학과 담당 사서를 중심으로 한 능동적 서비스 전환은 전국 대학도서관 혁신 경진대회에서 좋은 평가를 받았습니다. 후반부는 학생의 진로 준비와 실무 능력입니다. 교외 실습, 산업체 멘토, 진로 상담, 전문 워크숍과 학습 포트폴리오를 통해 배움과 직업 현장을 연결합니다. 114년도 실습 참여는 1천579인회였습니다. 산업체 멘토 29명이 1천385인회를 지원했고, 진로 지도교수 23명이 741인회의 상담을 제공했습니다. 이와 함께 지도 역량 연수 7회, 전문 강연과 워크숍 5회, 진로 상담 225인회를 운영했습니다. 학생 EP 학습이력 플랫폼 이용률은 88.61퍼센트에 이르렀습니다. 이러한 노력은 신뢰할 수 있는 연구, 전문 실습과 진로 설계를 연결하여 학생들이 더 큰 자신감으로 미래를 준비하도록 돕습니다. 경청해 주셔서 감사합니다.""",
    "it-IT": """Benvenuti alla mostra dei risultati del Progetto Sprout per l’istruzione superiore. Questo pannello presenta l’uso delle risorse elettroniche della biblioteca e lo sviluppo delle competenze professionali degli studenti. La biblioteca rafforza l’alfabetizzazione informativa attraverso banche dati, sistemi di confronto dei testi, corsi e attività di promozione. Nell’anno 114, Journals ha registrato 52.915 download di testi completi, Theses 8.450 e JSTOR 4.371. Symskan ha elaborato 403 controlli di similarità, mentre il rilevatore di scrittura inglese con intelligenza artificiale di Turnitin ha raggiunto 281 utilizzi, quasi tre volte l’obiettivo previsto. La formazione sulle banche dati ha totalizzato 58 ore e coinvolto 876 partecipanti di 37 classi. Il passaggio a servizi bibliotecari più attivi ha inoltre ricevuto un riconoscimento nazionale per l’innovazione. La seconda parte riguarda la preparazione professionale. Tirocini esterni, mentori dell’industria, colloqui di orientamento, laboratori e portfolio collegano lo studio al mondo del lavoro. Nell’anno 114 sono state registrate 1.579 partecipazioni ai tirocini. Ventinove mentori hanno seguito 1.385 partecipazioni e 23 consulenti hanno offerto 741 colloqui. Sono stati inoltre organizzati sette corsi di formazione, cinque conferenze e laboratori professionali, e 225 consulenze di carriera. L’uso della piattaforma di portfolio elettronico ha raggiunto l’88,61 per cento. Queste iniziative uniscono ricerca, pratica e pianificazione professionale, aiutando gli studenti ad affrontare il futuro con maggiore fiducia. Grazie per l’ascolto.""",
    "pt-PT": """Bem-vindos à Exposição de Resultados do Projeto Sprout para o Ensino Superior. Este painel apresenta a utilização dos recursos eletrónicos da biblioteca e o desenvolvimento das competências profissionais dos estudantes. A biblioteca reforça a literacia da informação através de bases de dados, sistemas de comparação de textos, formação e divulgação. No ano 114, Journals registou 52.915 descarregamentos de texto integral, Theses 8.450 e JSTOR 4.371. Symskan realizou 403 verificações de semelhança, enquanto o detetor de escrita inglesa com inteligência artificial do Turnitin atingiu 281 utilizações, quase três vezes a meta prevista. A formação sobre bases de dados totalizou 58 horas e envolveu 876 participantes de 37 turmas. A transição para serviços mais ativos de bibliotecários especializados também recebeu um reconhecimento nacional de inovação. A segunda parte centra-se na preparação profissional. Estágios externos, mentores da indústria, entrevistas de carreira, workshops e portefólios aproximam a aprendizagem do mercado de trabalho. No ano 114 registaram-se 1.579 participações em estágios. Vinte e nove mentores acompanharam 1.385 participações e 23 orientadores realizaram 741 entrevistas. Foram ainda promovidas sete formações, cinco palestras e workshops profissionais, e 225 consultas de carreira. A utilização da plataforma de portefólio eletrónico atingiu 88,61 por cento. Estas iniciativas ligam investigação, prática e planeamento profissional, ajudando os estudantes a avançar com maior confiança. Obrigado pela atenção.""",
    "ru-RU": """Добро пожаловать на выставку достижений проекта развития высшего образования. Этот стенд посвящён электронным ресурсам библиотеки и развитию профессиональных практических навыков студентов. Библиотека повышает информационную грамотность с помощью баз данных, систем проверки сходства текстов, учебных занятий и информационных мероприятий. В 114 году база Journals зарегистрировала 52 915 полнотекстовых загрузок, Theses — 8 450, а JSTOR — 4 371. В Symskan было выполнено 403 проверки, а функция выявления английских текстов с искусственным интеллектом в Turnitin использовалась 281 раз — почти втрое больше ожидаемого показателя. Обучение работе с базами данных составило 58 часов и охватило 876 участников из 37 групп. Переход к активной работе предметных библиотекарей также получил национальную награду за инновации. Вторая часть посвящена готовности к карьере. Стажировки, отраслевые наставники, консультации, семинары и электронные портфолио помогают связать обучение с работой. В 114 году было зарегистрировано 1 579 участий в стажировках. Двадцать девять наставников поддержали 1 385 участий, а 23 консультанта провели 741 встречу. Также состоялись семь обучающих мероприятий, пять профессиональных лекций и семинаров и 225 карьерных консультаций. Платформой электронного портфолио воспользовались 88,61 процента студентов. Эти меры объединяют качественный поиск информации, практику и планирование карьеры, помогая студентам увереннее двигаться в будущее. Благодарим за внимание.""",
}

SPOKEN = {
    "zh-TW": {"AI": "A I", "EP": "E P"},
    "en-US": {"AI": "A I", "EP": "E P"},
    "es-ES": {"AI": "A I", "EP": "E P"},
    "fr-FR": {"AI": "A I", "EP": "E P"},
    "de-DE": {"AI": "A I", "EP": "E P"},
    "ja-JP": {"AI": "エー アイ", "EP": "イー ピー"},
    "ko-KR": {"AI": "에이 아이", "EP": "이 피"},
    "it-IT": {"AI": "A I", "EP": "E P"},
    "pt-PT": {"AI": "A I", "EP": "E P"},
    "ru-RU": {"AI": "эй ай", "EP": "и пи"},
}


def seconds(value):
    hours, minutes, secs = value.replace(",", ".").split(":")
    return round(int(hours) * 3600 + int(minutes) * 60 + float(secs), 3)


def read_cues(path):
    if base:
        return base.read_cues(path)
    cues = []
    for block in re.split(r"\r?\n\r?\n", path.read_text(encoding="utf-8").strip()):
        rows = block.splitlines()
        if len(rows) >= 3:
            start, end = [part.strip() for part in rows[1].split("-->")]
            cues.append([seconds(start), seconds(end), " ".join(rows[2:]).strip()])
    return cues


def main(generate_audio):
    for code, text in TEXTS.items():
        (ROOT / f"narration-26-{code}.txt").write_text(text, encoding="utf-8")
    if not generate_audio:
        if POSTER_SOURCE.exists():
            shutil.copy2(POSTER_SOURCE, ROOT / "github-pages" / "poster-26.jpg")
        print("Draft texts for guide 26 are ready. Audio generation was not started.")
        return

    raw = (OUT / "languages-25.js").read_text(encoding="utf-8").strip()
    previous = json.loads(raw.removeprefix("window.GUIDE_LANGUAGES=").removesuffix(";"))
    languages = {}
    for code, ui in previous.items():
        item = {key: value for key, value in ui.items() if key not in ("audio", "cues")}
        item["title"] = TITLES[code]
        item["eyebrow"] = re.sub(r"\d+\s*$", "26", ui["eyebrow"])
        spoken = TEXTS[code]
        for formal, pronunciation in SPOKEN[code].items():
            spoken = spoken.replace(formal, pronunciation)
        text_path = ROOT / f"narration-26-{code}.txt"
        audio_path = OUT / f"narration-26-{code}.mp3"
        srt_path = ROOT / f"narration-26-{code}.srt"
        text_path.write_text(spoken, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / ".vendor")
        subprocess.run([
            sys.executable, "-m", "edge_tts", "-f", str(text_path), "-v", VOICES[code], "--rate=+20%",
            "--write-media", str(audio_path), "--write-subtitles", str(srt_path)
        ], check=True, env=env)
        cues = read_cues(srt_path)
        for cue in cues:
            for formal, pronunciation in SPOKEN[code].items():
                cue[2] = cue[2].replace(pronunciation, formal)
        item["audio"] = audio_path.name + "?v=1"
        item["cues"] = cues
        languages[code] = item

    (OUT / "languages-26.js").write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    if POSTER_SOURCE.exists() and OUT != ROOT:
        shutil.copy2(POSTER_SOURCE, OUT / "poster-26.jpg")
    duration = languages["zh-TW"]["cues"][-1][1]
    mins, secs = int(duration // 60), int(duration % 60)
    html = (OUT / "25.html").read_text(encoding="utf-8")
    html = re.sub(r"<title>.*?</title>", f"<title>{TITLES['zh-TW']}｜Audio Guide</title>", html, count=1)
    html = re.sub(
        r'(<figure class="poster"><img src=")[^"]+(" alt=")[^"]+(\">)',
        rf'\1poster-26.jpg?v=1\2{TITLES["zh-TW"]}海報\3', html, count=1)
    html = re.sub(r'(<p id="eyebrow" class="eyebrow">).*?(</p>)', r'\1高等教育深耕計畫成果展 · 26\2', html, count=1)
    html = re.sub(r'(<h1 id="title">).*?(</h1>)', rf'\1{TITLES["zh-TW"]}\2', html, count=1)
    html = re.sub(r'languages-25\.js\?v=\d+', "languages-26.js?v=1", html, count=1)
    html = re.sub(r'narration-25-zh-TW\.mp3\?v=\d+', "narration-26-zh-TW.mp3?v=1", html, count=1)
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{mins}:{secs:02d}', html, count=1)
    (OUT / "26.html").write_text(html, encoding="utf-8")
    print(json.dumps({code: {"duration": data["cues"][-1][1], "ending": data["cues"][-1][2]}
                      for code, data in languages.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-audio", action="store_true")
    args = parser.parse_args()
    main(args.generate_audio)
