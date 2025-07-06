from faster_whisper import WhisperModel

model_size = "distil-large-v3"
# model_size = "small"

audio_model = WhisperModel(model_size, device="cpu", compute_type="int8")

def extract_text(audio_file_path):
    try:
        segments, info = audio_model.transcribe(
            audio_file_path,
            beam_size=1,         # Greedy decoding for maximum speed
            language="en",       # Force English language
            word_timestamps=False, # Skip word-level timestamps (faster)
            temperature=0,
            suppress_tokens=None,
        )

        transcript_segments = []
        for segment in segments:
            entry = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            transcript_segments.append(entry)

        full_text = " ".join(segment["text"] for segment in transcript_segments)

        return True, transcript_segments, full_text, "Success"
    except Exception as e:
        return False, None, None, f"Error: {e}"