from kafka import KafkaConsumer
from app import Job
from app import db
import json

consumer = KafkaConsumer('foobar',
                         value_deserializer=lambda m: json.loads(m),
                         bootstrap_servers='kafka:9092',
                         group_id='my-group',
                         api_version=(1, 0, 1)
                         )
for msg in consumer:
    print(msg)
    job = Job.query.filter_by(video_id=msg.value['youtubeurl']).first()
    job.processed = True
    db.session.commit()
