import os
import subprocess
from celery import Celery
import whisper
from celery.schedules import crontab
from celery.app.control import Inspect

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6388/0')
app.conf.update(worker_concurrency=2,result_expires=3600)

SEGMENT_DIR = 'segments'
TRANSCRIPT_DIR = 'transcripts'
language_model = ""

@app.on_after_configure.connect
def load_model(sender, **kwargs):
    global language_model
    language_model = whisper.load_model('large')

@app.task
def split_video(video_path):
    filename = os.path.basename(video_path)
    base_name, ext = os.path.splitext(filename)
    output = os.path.join(SEGMENT_DIR, f"{base_name}__%03d{ext}")

    subprocess.run(
        [
            "ffmpeg", "-i", video_path, "-c", "copy", "-f", "segment", "-segment_time", "500", output
        ]
    )

    return [os.path.join(SEGMENT_DIR, f) for f in os.listdir(SEGMENT_DIR) if f.startswith(base_name)]

@app.task
def print_results(results):
    with open("results.txt","a+") as f:
        for segments in results:
            f.write(f"{segments}\n")
    return results

@app.task
def transcribe_result(segment_path):
    segment_path = os.path.abspath(segment_path).strip()
    if not os.path.exists(segment_path):
        print("File does not exist")
        exit
    result = language_model.transcribe(segment_path)
    transcription = result.get("text", "").strip()
    transcription_path = os.path.join(
        TRANSCRIPT_DIR, os.path.basename(segment_path).replace(".mp4","_transcription.txt")
    )
    with open(transcription_path,"w") as f:
        f.write(transcription)
    
    return transcription_path