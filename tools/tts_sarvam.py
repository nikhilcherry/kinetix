"""Voice lines for a reel via Sarvam's bulbul TTS (strong for Indian languages and Hinglish).

    SARVAM_API_KEY=... python3 tools/tts_sarvam.py "Arre! Yeh kiski gaadi hai yaar?!" assets/line1.wav --speaker aditya --lang hi-IN --pace 1.15

Speakers seen working with bulbul:v3: aditya, kabir, ritu. Any other TTS works too; Kinetix only needs a WAV.
"""
import argparse
import base64
import json
import os
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("text"); ap.add_argument("out")
ap.add_argument("--speaker", default="ritu"); ap.add_argument("--lang", default="en-IN")
ap.add_argument("--pace", type=float, default=1.0); ap.add_argument("--model", default="bulbul:v3")
a = ap.parse_args()
key = os.environ.get("SARVAM_API_KEY") or exit("set SARVAM_API_KEY")
body = {"text": a.text, "target_language_code": a.lang, "model": a.model, "speaker": a.speaker, "pace": a.pace, "speech_sample_rate": 44100}
req = urllib.request.Request("https://api.sarvam.ai/text-to-speech", data=json.dumps(body).encode(), method="POST",
                             headers={"api-subscription-key": key, "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as r:
    audio = json.load(r)["audios"][0]
open(a.out, "wb").write(base64.b64decode(audio))
print(a.out)
