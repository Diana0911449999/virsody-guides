import json
import re
import subprocess
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VOICE = "zh-TW-HsiaoChenNeural"
RATE = "+10%"
LETTER_RATE = "+20%"
SAMPLE_RATE = 24000
LETTER_GAP_MS = 45


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


def build_cue_pcm(text, cue_index):
    parts = re.split(r"(EMI)", text)
    pcm = bytearray()
    for part_index, part in enumerate(parts):
        if not part:
            continue
        if part != "EMI":
            spoken = part.replace("累積158人次參與", "累積一百五十八人次參與")
            pcm.extend(synthesize_pcm(spoken, f"cue-{cue_index:02d}-{part_index:02d}"))
            continue

        # Generate literal English letters as three independent clips. This
        # guarantees E, M and I are articulated separately. Only a 45 ms gap
        # is inserted, so the sequence remains smooth without a long pause.
        for letter_index, letter in enumerate(("E", "M", "I")):
            pcm.extend(synthesize_pcm(letter, f"cue-{cue_index:02d}-{part_index:02d}-{letter}", LETTER_RATE))
            if letter_index < 2:
                pcm.extend(b"\x00\x00" * int(SAMPLE_RATE * LETTER_GAP_MS / 1000))
    return bytes(pcm)


def main():
    languages_path = ROOT / "languages-06.js"
    raw = languages_path.read_text(encoding="utf-8").strip()
    languages = json.loads(re.match(r"window\.GUIDE_LANGUAGES=(.*);$", raw, re.S).group(1))
    chinese = languages["zh-TW"]
    if not any("EMI" in cue[2] for cue in chinese["cues"]):
        raise RuntimeError("Expected EMI subtitles were not found")
    if not any("累積158人次參與" in cue[2] for cue in chinese["cues"]):
        raise RuntimeError("Expected 158 subtitle was not found")

    all_pcm = bytearray()
    new_cues = []
    current_seconds = 0.1
    all_pcm.extend(b"\x00\x00" * int(SAMPLE_RATE * current_seconds))
    for index, cue in enumerate(chinese["cues"]):
        cue_pcm = build_cue_pcm(cue[2], index)
        duration = len(cue_pcm) / 2 / SAMPLE_RATE
        start = round(current_seconds, 3)
        end = round(current_seconds + duration, 3)
        new_cues.append([start, end, cue[2]])
        all_pcm.extend(cue_pcm)
        current_seconds = end

    wav_output = ROOT / "narration-06-zh-TW-final.wav"
    with wave.open(str(wav_output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(all_pcm))

    audio_output = ROOT / "narration-06-zh-TW.mp3"
    run("ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_output),
        "-codec:a", "libmp3lame", "-b:a", "96k", str(audio_output))
    chinese["audio"] = audio_output.name + "?v=7"
    chinese["cues"] = new_cues

    languages_path.write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "06.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-06\.js(?:\?v=\d+)?', "languages-06.js?v=7", html, count=1)
    html = re.sub(r'narration-06-zh-TW\.mp3(?:\?v=\d+)?', "narration-06-zh-TW.mp3?v=7", html, count=1)
    duration = new_cues[-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Built literal E M I clips with {LETTER_GAP_MS} ms gaps; duration {duration:.1f}s")


if __name__ == "__main__":
    main()
