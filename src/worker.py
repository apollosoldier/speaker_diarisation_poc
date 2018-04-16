from kafka import KafkaConsumer
import json
import subprocess
import librosa
import librosa.display
import numpy as np
from PIL import Image

from app import db, JobState, Job, State


def set_state(state, db, job):
    video_downloaded_state = JobState.query.filter_by(name=state.name).first()
    job.job_state = video_downloaded_state
    db.session.commit()


def main():
    consumer = KafkaConsumer('foobar',
                             value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                             bootstrap_servers='kafka:9092',
                             group_id='my-group',
                             api_version=(1, 0, 1)
                             )

    for msg in consumer:
        youtube_video_id = msg.value['youtubeurl']

        job = Job.query.filter_by(video_id=youtube_video_id).first()
        print(job)

        if job is not None:
            try:
                subprocess.check_call(['youtube-dl', '-f', '18', '-o', '%(id)s.%(ext)s',
                                       'https://www.youtube.com/watch?v=%s' % youtube_video_id])
                set_state(State.VIDEO_DOWNLOADED, db, job)

                subprocess.check_call(['ffmpeg', '-y', '-i', '%s.mp4' % youtube_video_id, '-ar', '16000', '-ac', '1',
                                       '%s.wav' % youtube_video_id])
                set_state(State.AUDIO_EXTRACTED, db, job)

                y, sr = librosa.load("%s.wav" % youtube_video_id, sr=16000)
                D = librosa.amplitude_to_db(librosa.stft(y), ref=np.max)
                D = np.fliplr(D)
                D = np.flipud(D)
                D8 = (((D - D.min()) / (D.max() - D.min())) * 255.9).astype(np.uint8)
                img = Image.fromarray(D8)
                img.save("static/img/waveforms/%s.jpg" % youtube_video_id)
                set_state(State.WAVEFORM_GENERATED, db, job)

                set_state(State.DONE, db, job)

            except Exception as e:
                print(e)
                set_state(State.ERROR, db, job)


if __name__ == '__main__':
    main()
