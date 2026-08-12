import json
import re
import subprocess
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VOICE = "zh-TW-HsiaoChenNeural"
RATE = "+10%"
SAMPLE_RATE = 24000


DISPLAY_TO_SPOKEN = {
    "114年度共開設三班，90人次參與證照考試及輔導班，19人取得AI應用規劃師證照":
        "一一四年度共開設三班，九十人次參與證照考試及輔導班，十九人取得AI應用規劃師證照",
    "研習共辦理三場，45人次參與": "研習共辦理三場，四十五人次參與",
    "多益成績達550分以上": "多益成績達五百五十分以上",
}


def run(*args):
    subprocess.run(args, check=True)


def synthesize_mp3(text, output, rate=RATE):
    source = output.with_suffix(".txt")
    source.write_text(text, encoding="utf-8")
    run(sys.executable, "-m", "edge_tts", "-f", str(source), "-v", VOICE,
        f"--rate={rate}", "--write-media", str(output))


def mp3_to_pcm(mp3_path, wav_path):
    run("ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3_path),
        "-ac", "1", "-ar", str(SAMPLE_RATE), "-sample_fmt", "s16", str(wav_path))
    with wave.open(str(wav_path), "rb") as wav:
        return wav.readframes(wav.getnframes())


def synthesize_pcm(text, stem, rate=RATE):
    mp3_path = ROOT / f"{stem}.mp3"
    wav_path = ROOT / f"{stem}.wav"
    synthesize_mp3(text, mp3_path, rate)
    return mp3_to_pcm(mp3_path, wav_path)


def spoken_text(display_text):
    result = display_text
    for display, spoken in DISPLAY_TO_SPOKEN.items():
        result = result.replace(display, spoken)
    # Keep i separate and PAS joined, but let the same Mandarin narrator say
    # the entire sentence in one take so the voice and prosody never change.
    result = result.replace("iPAS", "愛帕斯")
    return result


def build_cue_pcm(text, cue_index):
    source = spoken_text(text)
    return synthesize_pcm(source, f"cue-{cue_index:02d}")


def main():
    languages_path = ROOT / "languages-16.js"
    raw = languages_path.read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    chinese = languages["zh-TW"]

    replacements = {
        "一一四年度共開設三班，九十人次參與證照考試及輔導班，十九人取得AI應用規劃師證照":
            "114年度共開設三班，90人次參與證照考試及輔導班，19人取得AI應用規劃師證照",
        "研習共辦理三場，四十五人次參與": "研習共辦理三場，45人次參與",
        "多益成績達五百五十分以上": "多益成績達550分以上",
    }
    for cue in chinese["cues"]:
        for old, new in replacements.items():
            cue[2] = cue[2].replace(old, new)

    required = ["114年度共開設三班", "45人次參與", "多益成績達550分以上"]
    if not all(any(item in cue[2] for cue in chinese["cues"]) for item in required):
        raise RuntimeError("Expected display subtitle replacements were not found")
    if not any("iPAS" in cue[2] for cue in chinese["cues"]):
        raise RuntimeError("Expected iPAS token was not found")

    all_pcm = bytearray(b"\x00\x00" * int(SAMPLE_RATE * 0.1))
    new_cues = []
    current_seconds = 0.1
    for index, cue in enumerate(chinese["cues"]):
        cue_pcm = build_cue_pcm(cue[2], index)
        duration = len(cue_pcm) / 2 / SAMPLE_RATE
        start = round(current_seconds, 3)
        end = round(current_seconds + duration, 3)
        new_cues.append([start, end, cue[2]])
        all_pcm.extend(cue_pcm)
        current_seconds = end

    wav_output = ROOT / "narration-16-zh-TW-final.wav"
    with wave.open(str(wav_output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(all_pcm))

    audio_output = ROOT / "narration-16-zh-TW.mp3"
    run("ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_output),
        "-codec:a", "libmp3lame", "-b:a", "96k", str(audio_output))
    chinese["audio"] = audio_output.name + "?v=3"
    chinese["cues"] = new_cues

    languages_path.write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "16.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-16\.js(?:\?v=\d+)?', "languages-16.js?v=3", html, count=1)
    html = re.sub(r'narration-16-zh-TW\.mp3(?:\?v=\d+)?', "narration-16-zh-TW.mp3?v=3", html, count=1)
    duration = new_cues[-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Built same-voice 愛帕斯 pronunciation and display-only number subtitles; duration {duration:.1f}s")


if __name__ == "__main__":
    main()
