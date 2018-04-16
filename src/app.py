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


class Job(db.Model):
    video_id = db.Column(db.String(80), primary_key=True)
    number_of_speakers = db.Column(db.Integer, nullable=False)
    state = db.Column(db.Integer, db.ForeignKey('job_state.id'), nullable=False)


class JobState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    jobs = db.relationship('Job', backref='job_state', lazy=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/view/<youtube_video_id>', methods=['GET'])
def view(youtube_video_id):
    return render_template('view.html', youtube_video_id=youtube_video_id)


@app.route('/submit', methods=['POST'])
def submit():
    youtubeurl = request.form['youtubeurl']
    numberofspeakers = int(request.form['numberofspeakers'])

    producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda m: json.dumps(m).encode('utf-8'),
        api_version=(1, 0, 1))

    uploaded_state = JobState.query.filter_by(name='submitted').first()
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
