from app import db, JobState, State

db.drop_all(bind=None)
db.create_all()

for x in list(State):
    db.session.add(JobState(name=x.name))

db.session.commit()
