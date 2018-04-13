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
    # id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(80), primary_key=True)
    processed = db.Column(db.Boolean, default=False)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    youtubeurl = request.form['youtubeurl']

    producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda m: json.dumps(m).encode('utf-8'),
        api_version=(1, 0, 1))

    msg = {
        "youtubeurl": youtubeurl
    }
    producer.send('foobar', msg)

    db.session.add(Job(video_id=youtubeurl))
    db.session.commit()

    return render_template('submit.html', youtubeurl=youtubeurl)

@app.route('/jobs')
def jobs():
    jobs = Job.query.all()
    return render_template('jobs.html', jobs=jobs)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
