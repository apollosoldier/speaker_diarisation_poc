from celery import Celery

import os
import subprocess
import librosa
import librosa.display
import numpy as np
from PIL import Image
from sac.util import Util

from app import db, JobState, Job, State
from steps.audio_based_segmentation import generate_audio_based_segmentation
from steps.face_based_segmentation import extract_images_from_video, generate_face_based_segmentation
from datetime import datetime

from steps.fusion import calculate_fusion

celery_app = Celery('tasks', backend='rpc://rabitmq//', broker='pyamqp://rabitmq//')


def set_state(state, db, job, error=""):
    video_downloaded_state = JobState.query.filter_by(name=state.name).first()
    job.job_state = video_downloaded_state
    job.error_log = error
    db.session.commit()


@celery_app.task
def x(youtube_video_id):
    job = Job.query.filter_by(video_id=youtube_video_id).first()
    if job is not None:
        try:
            job.start_time = datetime.utcnow()
            subprocess.check_call(['youtube-dl', '-f', '18', '-o', 'videos/%(id)s.%(ext)s',
                                   'https://www.youtube.com/watch?v=%s' % youtube_video_id])
            set_state(State.VIDEO_DOWNLOADED, db, job)

            subprocess.check_call(['ffmpeg', '-y', '-i', 'videos/%s.mp4' % youtube_video_id, '-ar', '16000', '-ac', '1',
                                   'audios/%s.wav' % youtube_video_id])
            set_state(State.AUDIO_EXTRACTED, db, job)

            y, sr = librosa.load("audios/%s.wav" % youtube_video_id, sr=16000)
            D = librosa.amplitude_to_db(librosa.stft(y), ref=np.max)
            D = np.flipud(D)
            D8 = (((D - D.min()) / (D.max() - D.min())) * 255.9).astype(np.uint8)
            img = Image.fromarray(D8)
            img = img.resize((D.shape[1], 128))
            img.save("static/img/waveforms/%s.jpg" % youtube_video_id)
            duration = librosa.get_duration(y=y, sr=sr)
            job.waveform_width = D.shape[1]
            job.duration = duration
            set_state(State.WAVEFORM_GENERATED, db, job)

            # audio based segmentation

            generate_audio_based_segmentation(
                os.path.abspath('audios/%s.wav' % youtube_video_id), 15, 20, 256, 128, 0.2,
                os.path.abspath('models/weights.h5'),
                os.path.abspath('models/scaler.pickle'),
                1024, 3, 1024, youtube_video_id,
                os.path.abspath('static/lbls/audio')
            )
            set_state(State.AUDIO_DATA_ANALYSED, db, job)

            # face based segmentation
            extract_images_from_video(
                os.path.abspath('videos/%s.mp4' % youtube_video_id),
                os.path.abspath('video_frames')
            )
            generate_face_based_segmentation(
                youtube_video_id,
                os.path.abspath('video_frames/%s' % youtube_video_id),
                os.path.abspath('static/lbls/image'),
                4,
                os.path.abspath('models/shape_predictor_68_face_landmarks.dat'),
                os.path.abspath('models/dlib_face_recognition_resnet_model_v1.dat')
            )
            set_state(State.IMAGE_DATA_ANALYSED, db, job)

            # fusion
            calculate_fusion(
                youtube_video_id,
                os.path.abspath('static/lbls/fusion'),
                Util.read_audacity_labels(
                    os.path.abspath('static/lbls/audio/%s.txt' % youtube_video_id)
                ),
                Util.read_audacity_labels(
                    os.path.abspath('static/lbls/image/%s.txt' % youtube_video_id)
                ),
                duration
            )
            set_state(State.FUSION_APPLIED, db, job)

            job.end_time = datetime.utcnow()
            set_state(State.DONE, db, job)

        except Exception as e:
            print(e)
            job.end_time = datetime.utcnow()
            set_state(State.ERROR, db, job, str(e))
