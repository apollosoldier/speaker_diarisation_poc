import os
import json
from collections import defaultdict
import operator
from sac.util import Util

def calculate_fusion(audio_lbls, image_lbls):
    pass


def get_highest_probability_class(start_seconds, end_seconds, lbls):
    classes_probability = defaultdict(int)
    for lbl in lbls:
        if lbl.start_seconds >= start_seconds and lbl.end_seconds <= end_seconds:
            classes_probability[lbl.lable] += lbl.end_seconds - lbl.start_seconds

    return max(classes_probability.iteritems(), key=operator.itemgetter(1))[0]



if __name__ == '__main__':

    with open("/Users/nicktgr15/workspace/speaker_diarisation_poc/src/static/lbls/audio/Unamij6z1io.json") as f:
        j = json.load(f)

    calculate_fusion(

        "/Users/nicktgr15/workspace/speaker_diarisation_poc/src/static/lbls/image/Unamij6z1io.json"
    )