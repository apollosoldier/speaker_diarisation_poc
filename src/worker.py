from kafka import KafkaConsumer
from app import Job, JobState
from app import db
import json
import subprocess
from tenacity import retry, stop_after_attempt, wait_fixed


def main():
    consumer = KafkaConsumer('foobar',
                             value_deserializer=lambda m: json.loads(m),
                             bootstrap_servers='kafka:9092',
                             group_id='my-group',
                             api_version=(1, 0, 1)
                             )

    for msg in consumer:
        print(msg)
        youtube_video_id = msg.value['youtubeurl']

        job = Job.query.filter_by(video_id=youtube_video_id).first()
        print(job)

        if job is not None:
            print(job)
            try:
                subprocess.check_call(['youtube-dl', '-f', '18', 'https://www.youtube.com/watch?v=%s' % youtube_video_id])
                video_downloaded_state = JobState.query.filter_by(name='video_downloaded').first()
                job.job_state = video_downloaded_state
            except:
                failed_state = JobState.query.filter_by(name='failed').first()
                job.job_state = failed_state

            db.session.commit()


if __name__ == '__main__':
    main()
