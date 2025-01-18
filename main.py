import os
from tasks import split_video,print_results,transcribe_result
from celery import chain
from time import sleep
from tasks import app

VIDEOS_DIR = "videos"

if __name__ == "__main__":
    tasks = []
    for video_file in os.listdir(VIDEOS_DIR):
        video_path = os.path.join(VIDEOS_DIR, video_file)

        result = chain(
            split_video.s(video_path),
            print_results.s(),
        ).apply_async()

        with open("data_store.txt","+a") as data_store:
            data_store.write(f"{video_file} {result.id}\n")
        tasks.append(result.id)
    
    print("Starting to watch tasks now")
    while not len(tasks) == 0:
        for task_id in tasks:
            result = app.AsyncResult(task_id)
            if result.ready():
                print(f"Task {task_id} is finished")
                tasks.remove(task_id)
        print("Tasks are still not finished")
        sleep(1)
    
    print("Segmentation is done, now we read the results and transcribe it")

    transcribe_tasks = []
    with open("results.txt") as f:
        results = f.readlines()
        for result in results:
            result = transcribe_result.delay(result.split(" ")[0])
            transcribe_tasks.append(result.id)
    
    while not len(transcribe_tasks) == 0:
        for task in transcribe_tasks:
            result = app.AsyncResult(task)
            if result.ready():
                print(f"Transcription task {task} is finished")
                transcribe_tasks.remove(task)
        print("Transcriping")
        sleep(1)