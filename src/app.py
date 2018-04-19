from enum import Enum

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from flask import request
from kafka import KafkaProducer
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:password@db:5432/speaker_diarisation'
app.debug = True

db = SQLAlchemy(app)


class State(Enum):
    SUBMITTED = 1
    VIDEO_DOWNLOADED = 2
    AUDIO_EXTRACTED = 3
    WAVEFORM_GENERATED = 4
    AUDIO_DATA_ANALYSED = 5
    IMAGE_DATA_ANALYSED = 6
    DONE = 7
    ERROR = 8


class Job(db.Model):
    video_id = db.Column(db.String(80), primary_key=True)
    number_of_speakers = db.Column(db.Integer, nullable=False)
    state = db.Column(db.Integer, db.ForeignKey('job_state.id'), nullable=False)
    error_log = db.Column(db.Text, nullable=True)
    waveform_width = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Float, nullable=True)


class JobState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    jobs = db.relationship('Job', backref='job_state', lazy=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/view/<youtube_video_id>', methods=['DELETE'])
def view_delete(youtube_video_id):
    db.session.delete(Job.query.filter_by(video_id=youtube_video_id).first())
    db.session.commit()
    return 'Deleted video with id: %s' % youtube_video_id


@app.route('/view/<youtube_video_id>', methods=['GET'])
def view(youtube_video_id):
    job = Job.query.filter_by(video_id=youtube_video_id).first()
    return render_template('view.html', youtube_video_id=youtube_video_id,
                           waveform_width=job.waveform_width, duration=job.duration)


@app.route('/submit', methods=['POST'])
def submit():
    youtubeurl = request.form['youtubeurl']
    numberofspeakers = int(request.form['numberofspeakers'])

    producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda m: json.dumps(m).encode('utf-8'),
        api_version=(1, 0, 1))

    uploaded_state = JobState.query.filter_by(name=State.SUBMITTED.name).first()
    db.session.add(Job(video_id=youtubeurl, number_of_speakers=numberofspeakers, job_state=uploaded_state))
    db.session.commit()

    msg = {
        "youtubeurl": youtubeurl
    }
    producer.send('foobar', msg)
    producer.flush()

    return render_template('submit.html', youtubeurl=youtubeurl)


@app.route('/jobs')
def jobs():
    jobs = Job.query.all()
    return render_template('jobs.html', jobs=jobs)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
