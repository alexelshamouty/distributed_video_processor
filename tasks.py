import os
import subprocess
from celery import Celery
import whisper
from celery.schedules import crontab
from celery.app.control import Inspect
from google.cloud import speech

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6388/0')
app.conf.update(worker_concurrency=10,result_expires=3600)

SEGMENT_DIR = 'segments'
TRANSCRIPT_DIR = 'transcripts'
language_model = ""
google_client = ""

@app.on_after_configure.connect
def load_model(sender, **kwargs):
    pass
    global language_model
    language_model = whisper.load_model('large')

@app.on_after_configure.connect
def initiate_client(sender, **kwargs):
    global google_client
    google_client = speech.SpeechClient()
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
def split_to_audio(video_path):
    filename = os.path.basename(video_path)
    base_name, ext = os.path.splitext(filename)
    output = os.path.join(SEGMENT_DIR, f"{base_name}__%03d.wav")

    subprocess.run([
        "ffmpeg", "-i", video_path, "-ac", "1" , "-f", "segment", "-segment_time", "10", output
    ])

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

@app.task
def cloud_transcribe_result(segment_path):
    segment_path = segment_path.strip()
    with open(segment_path,"rb") as f:
        content = f.read().strip()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US",
        model="video",  # Chosen model
    )
    response = google_client.recognize(config=config, audio=audio)
    text = response.results[0].alternatives[0].transcript
    transcription_path = os.path.join(
        TRANSCRIPT_DIR, os.path.basename(segment_path).replace(".wav","_transcription.txt")
    )
    with open(transcription_path,"w") as f:
        f.write(text)
@app.task
def remove_segment_from_database(segment_path):
    #Yeah I know, use sqlite...
    with open("results.txt","w") as f:
        f.write("")
    with open("data_store.txt","w") as f:
        f.write("")