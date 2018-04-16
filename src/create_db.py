from app import db
import time
from app import JobState, Job

db.drop_all(bind=None)
db.create_all()


db.session.add(JobState(name='submitted'))
db.session.add(JobState(name='video_downloaded'))
db.session.add(JobState(name='audio_extracted'))
db.session.add(JobState(name='speakers_detected'))
db.session.add(JobState(name='done'))
db.session.add(JobState(name='error'))

db.session.commit()
