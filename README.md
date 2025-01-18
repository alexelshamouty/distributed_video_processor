# Distributed Video Segmentation and Transcription

1. Put your videos in videos/
2. Create a segments and transcripts directory
3. Cofngiure concurrency in worker.py
4. Make sure you have two redis instances running. One is the broker and the other is for the results backend
```
docker run -it -p 6379:6379 redis
docker run -it -p 6388:6379 redis
```
5. Expose your brokers and your result backend externally or via a VPN for your remote workers
6. Make sure you have shared storage ( ie: Mount videos/ segments/ transcripts from the master node, the one you'll be running main from


* Because of slowness I decided to offload the analysis to google cloud, so make sure you adjust your workflow accordingly
If you decide on using google cloud make sure you have the following ready before you start

```
gcloud init     
gcloud auth application-default login
```
