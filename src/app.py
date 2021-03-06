from enum import Enum

from flask_sqlalchemy import SQLAlchemy
from flask import render_template, url_for
from flask import request
import json
from datetime import datetime
from celery import Celery
from flask import Flask,redirect



class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:password@db:5432/speaker_diarisation'
app.debug = True
app.wsgi_app = ReverseProxied(app.wsgi_app)

db = SQLAlchemy(app)


celery_app = Celery('proj',
             broker='pyamqp://rabitmq//',
             backend='rpc://rabitmq//',
             include=['tasks'])


class State(Enum):
    SUBMITTED = 1
    VIDEO_DOWNLOADED = 2
    AUDIO_EXTRACTED = 3
    WAVEFORM_GENERATED = 4
    AUDIO_DATA_ANALYSED = 5
    IMAGE_DATA_ANALYSED = 6
    MFCC_ANALYSED = 7
    FUSION_APPLIED = 8
    DONE = 9
    ERROR = 10


class Job(db.Model):
    video_id = db.Column(db.String(80), primary_key=True)
    number_of_speakers = db.Column(db.Integer, nullable=False)
    state = db.Column(db.Integer, db.ForeignKey('job_state.id'), nullable=False)
    error_log = db.Column(db.Text, nullable=True)
    waveform_width = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Float, nullable=True)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    mapping_face_to_voice = db.Column(db.JSON, nullable=True)


class JobState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    jobs = db.relationship('Job', backref='job_state', lazy=True)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route('/index')
@app.route('/')
def index():
    job_state_done = JobState.query.filter_by(name=State.DONE.name).first()
    jobs = Job.query.filter_by(state=job_state_done.id).all()
    return render_template('index.html', jobs=jobs)


@app.route('/view/<youtube_video_id>', methods=['DELETE'])
def view_delete(youtube_video_id):
    db.session.delete(Job.query.filter_by(video_id=youtube_video_id).first())
    db.session.commit()
    return 'Deleted video with id: %s' % youtube_video_id


@app.route('/view/<youtube_video_id>', methods=['GET'])
def view(youtube_video_id):
    job = Job.query.filter_by(video_id=youtube_video_id).first()
    return render_template('view.html', youtube_video_id=youtube_video_id,
                           waveform_width=job.waveform_width, duration=job.duration,
                           waveform_img=url_for('static', filename='img/waveforms/%s.jpg' % youtube_video_id,
                                                _external=True),
                           audio_lbls=url_for('static', filename='lbls/audio/%s.json' % youtube_video_id,
                                              _external=True),
                           image_lbls=url_for('static', filename='lbls/image/%s.json' % youtube_video_id,
                                              _external=True),
                           fusion_lbls=url_for('static', filename='lbls/fusion/%s.json' % youtube_video_id,
                                              _external=True),
                           mfcc_lbls=url_for('static', filename='lbls/mfcc/%s.json' % youtube_video_id,
                                               _external=True),
                           speakers=job.number_of_speakers,
                           mapping_face_to_voice=job.mapping_face_to_voice
                           )


@app.route('/submit', methods=['POST'])
def submit():
    youtubeurl = request.form['youtubeurl']
    numberofspeakers = int(request.form['numberofspeakers'])

    uploaded_state = JobState.query.filter_by(name=State.SUBMITTED.name).first()
    db.session.add(Job(video_id=youtubeurl, number_of_speakers=numberofspeakers,
                       job_state=uploaded_state, start_time=datetime.utcnow()))
    db.session.commit()

    celery_app.send_task('tasks.x', args=[youtubeurl], queue='lopri')

    return redirect(url_for(".jobs"), code=302)


@app.route('/jobs')
def jobs():
    jobs = Job.query.all()
    return render_template('jobs.html', jobs=jobs)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
