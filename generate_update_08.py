import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main():
    languages_path = ROOT / "languages-08.js"
    raw = languages_path.read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    if len(languages) != 10:
        raise RuntimeError(f"Expected 10 languages, found {len(languages)}")

    corrected = (
        "另有二百三十人次參與SAP辦公室辦理之培訓課程，其中一百六十三人報考相關證照，"
        "一百三十九人通過，整體通過率為百分之八十五。"
    )
    for code, item in languages.items():
        for cue in item["cues"]:
            cue[2] = re.sub("sap", "SAP", cue[2], flags=re.IGNORECASE)
        item["audio"] = re.sub(r"\?v=\d+$", "?v=3", item["audio"])

    if corrected not in " ".join(cue[2] for cue in languages["zh-TW"]["cues"]):
        raise RuntimeError("Corrected Chinese sentence is missing")

    languages_path.write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "08.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-08\.js(?:\?v=\d+)?', "languages-08.js?v=3", html, count=1)
    html = re.sub(r'narration-08-zh-TW\.mp3(?:\?v=\d+)?', "narration-08-zh-TW.mp3?v=3", html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print("Finalized guide 08 cache versions for 10 languages")


if __name__ == "__main__":
    main()
