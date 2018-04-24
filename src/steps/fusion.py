import os
import json
from collections import defaultdict
import operator
from sac.util import Util


class Item:
    def __init__(self, start_seconds, end_seconds, image_class, audio_class):
        self.start_seconds = start_seconds
        self.end_seconds = end_seconds
        self.image_class = image_class
        self.audio_class = audio_class

    def __repr__(self):
        return "[%s %s %s %s]" % (self.start_seconds, self.end_seconds, self.image_class, self.audio_class)


def calculate_fusion(audio_lbls, image_lbls, duration):

    mapping_face_to_voice = {}

    step = 0.2  # 100 ms

    pairs = []

    i = 0
    while i < duration:

        image_lbl_code = None
        audio_lbl_code = None

        for image_lbl in image_lbls:

            if image_lbl.end_seconds >= i:
                # print("%s >= %s" % (image_lbl.start_seconds, i) )
                image_lbl_code = image_lbl.label
                break

        for audio_lbl in audio_lbls:
            if audio_lbl.end_seconds >= i:
                audio_lbl_code = audio_lbl.label
                break

        pairs.append(Item(i, i+step, image_lbl_code, audio_lbl_code))

        i += step

    print(pairs)

    ## find correlation
    correlation_pairs = []
    for p in pairs:
        if p.image_class is not None and p.audio_class is not None and p.audio_class != 'non_speech':
            classes = p.image_class.split(",")
            if len(classes) == 1:
                c = classes[0]
                if c != "non_speech":
                    # print(p)
                    correlation_pairs.append(p)

    print(correlation_pairs)

    classes_set = list(set([i.image_class for i in correlation_pairs]))
    print(classes_set)
    for c in classes_set:
        classes_probability = defaultdict(int)
        for p in correlation_pairs:
            if p.image_class == c:
                classes_probability[p.audio_class] += 1

        mapping_face_to_voice[c] = max(classes_probability.items(), key=operator.itemgetter(1))[0]

    print(mapping_face_to_voice)

    for p in pairs:
        if p.image_class is not None:
            classes = p.image_class.split(",")
            if len(classes) == 1:
                c = classes[0]
                p.image_class = mapping_face_to_voice[c]

    print(pairs)

    # detect asymfwnia

    # for ka8e asymfwnia find 6 nearest neighbours (excluding non_speech)




def get_highest_probability_class(start_seconds, end_seconds, lbls):
    print("%s %s" % (start_seconds, end_seconds))
    classes_probability = defaultdict(int)
    for lbl in lbls:
        if lbl.start_seconds >= start_seconds and lbl.end_seconds <= end_seconds:
            classes_probability[lbl.label] += lbl.end_seconds - lbl.start_seconds

    print(classes_probability.keys())

    return max(classes_probability.items(), key=operator.itemgetter(1))[0]


if __name__ == '__main__':

    audio_lbls = Util.read_audacity_labels(
        "/Users/nikolaostsipas/p_workspace/speaker_diarisation_poc/src/static/lbls/audio/Unamij6z1io.txt")
    image_lbls = Util.read_audacity_labels(
        "/Users/nikolaostsipas/p_workspace/speaker_diarisation_poc/src/static/lbls/image/Unamij6z1io.txt")

    calculate_fusion(audio_lbls, image_lbls, 443.129625)
