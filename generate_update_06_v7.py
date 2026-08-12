import json
import re
import subprocess
import sys
import wave
from array import array
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VOICE = "zh-TW-HsiaoChenNeural"
RATE = "+10%"
LETTER_RATE = "+20%"
SAMPLE_RATE = 24000
LETTER_GAP_MS = 0


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


def trim_edge_silence(pcm, threshold=180, keep_ms=8):
    """Remove TTS padding while retaining a tiny natural consonant margin."""
    samples = array("h")
    samples.frombytes(pcm)
    audible = [i for i, sample in enumerate(samples) if abs(sample) >= threshold]
    if not audible:
        return pcm
    keep = int(SAMPLE_RATE * keep_ms / 1000)
    start = max(0, audible[0] - keep)
    end = min(len(samples), audible[-1] + keep + 1)
    return samples[start:end].tobytes()


def build_canonical_emi_pcm():
    """Build E M I once so every occurrence uses the exact same waveform."""
    pcm = bytearray()
    for letter in ("E", "M", "I"):
        letter_pcm = synthesize_pcm(letter, f"canonical-{letter}", LETTER_RATE)
        pcm.extend(trim_edge_silence(letter_pcm))
    return bytes(pcm)


def build_cue_pcm(text, cue_index, canonical_emi_pcm):
    parts = re.split(r"(EMI)", text)
    pcm = bytearray()
    for part_index, part in enumerate(parts):
        if not part:
            continue
        if part != "EMI":
            spoken = part.replace("累積158人次參與", "累積一百五十八人次參與")
            spoken_pcm = synthesize_pcm(spoken, f"cue-{cue_index:02d}-{part_index:02d}")
            # Remove the padding at either side of an EMI boundary. This
            # prevents a pause before E or after I while leaving ordinary
            # sentence timing untouched.
            touches_emi = (
                (part_index > 0 and parts[part_index - 1] == "EMI")
                or (part_index + 1 < len(parts) and parts[part_index + 1] == "EMI")
            )
            pcm.extend(trim_edge_silence(spoken_pcm) if touches_emi else spoken_pcm)
            continue

        # Reuse one canonical E M I waveform everywhere, guaranteeing that
        # later pronunciations sound exactly the same as the first one.
        pcm.extend(canonical_emi_pcm)
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
    canonical_emi_pcm = build_canonical_emi_pcm()
    current_seconds = 0.1
    all_pcm.extend(b"\x00\x00" * int(SAMPLE_RATE * current_seconds))
    for index, cue in enumerate(chinese["cues"]):
        cue_pcm = build_cue_pcm(cue[2], index, canonical_emi_pcm)
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
    chinese["audio"] = audio_output.name + "?v=9"
    chinese["cues"] = new_cues

    languages_path.write_text(
        "window.GUIDE_LANGUAGES=" + json.dumps(languages, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    html_path = ROOT / "06.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r'languages-06\.js(?:\?v=\d+)?', "languages-06.js?v=9", html, count=1)
    html = re.sub(r'narration-06-zh-TW\.mp3(?:\?v=\d+)?', "narration-06-zh-TW.mp3?v=9", html, count=1)
    duration = new_cues[-1][1]
    html = re.sub(r'max="[0-9.]+"', f'max="{duration}"', html, count=1)
    html = re.sub(r'id="total">\d+:\d+', f'id="total">{int(duration // 60)}:{int(duration % 60):02d}', html, count=1)
    html_path.write_text(html, encoding="utf-8")
    print(f"Built one canonical E M I waveform and removed boundary pauses; duration {duration:.1f}s")


if __name__ == "__main__":
    main()
