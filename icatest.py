import csv
import random

import numpy as np
import os

import sampen
from keras.layers import Dense, Dropout
from keras.models import Sequential
from keras.utils.np_utils import to_categorical
from sklearn.decomposition import FastICA

import dataprocessing
from activitydetection import VoiceActivityDetector


def get_data_files(searchdirectory, extension = ".csv"):
    targetfiles = []
    for root, dirs, files in os.walk(searchdirectory):
        for file in files:
            if extension in file:
                targetfiles.append(root+"/"+file)
    return targetfiles


def get_observations(filelist):
    X1 = []
    for file in filelist:
        data = []
        with open(file, 'rb') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in spamreader:
                conv = float(row[0])
                # t =numpy.array([conv])
                # t = [conv]
                data.append(conv)
        data = data[0:len(data)-1]
        data = np.array(data)
        X1.append(data)

    t = X1[0]
    first = True
    for element in X1:
        if first:
            first = False
            continue
        t = np.c_[t, element]
    for index in range(0, len(t)):
        t[index] = np.array(t[index])

    return t


def preprocess_data_array(data):
    returndata = []

    for row in data:
        conv = row
        # t =numpy.array([conv])
        # t = [conv]
        returndata.append(conv)

    returndata = np.array(data)
    return returndata

model = None
#
#
# def initialize_classifier():
#     global model
#     #load truth observationss
#     directory = "testdata/handdata"
#     files = get_data_files(directory)
#     t_observations = get_observations(files)
#     observationsarray = []
#     for observation in t_observations.T:
#         observationsarray.append((observation,np.array([1])))
#
#     #load false observations
#     directory = "testdata/garbagedata"
#     files = get_data_files(directory)
#     f_observations = get_observations(files)
#
#     for observation in f_observations.T:
#        observationsarray.append((observation, np.array([0])))
#
#     #join and mix
#     random.shuffle(observationsarray)
#
#     randomdata = []
#     labels = []
#     for observation in observationsarray:
#         randomdata.append(observation[0])
#         labels.append(observation[1])
#
#
#     n_obs = len(randomdata)
#     n_samples = len(randomdata[0])
#
#     randomdata = np.array(randomdata)
#     labels = np.array(labels)
#
#     randomdata = randomdata.T
#     randomdata /= randomdata.std(axis=0)
#     # Compute ICA
#     ica = FastICA(max_iter=1000)
#     S_ = ica.fit_transform(randomdata)  # Reconstruct signals
#     # A_ = ica.mixing_  # Get estimated mixing matrix
#
#     model = Sequential()
#
#     model.add(Dense(n_obs, input_dim=n_samples, init='uniform', activation='relu'))
#     model.add(Dropout(0.5))
#     model.add(Dense(40, activation='relu'))
#     model.add(Dropout(0.5))
#     model.add(Dense(1, activation='sigmoid'))
#
#     model.compile(loss='binary_crossentropy',
#                   optimizer='rmsprop',
#                   metrics=['accuracy','recall','precision', 'fmeasure'])
#
#     # from sklearn.metrics import confusion_matrix
#     model.fit(S_.T,labels,nb_epoch=40)

def np_treat_array(input):
    signals_processed = []
    for signal in input:
        signals_processed.append(np.array(signal))
    treated = signals_processed[0]
    first = True
    for element in signals_processed:
        if first:
            first = False
            continue
        treated = np.c_[treated, element]
    for index in range(0, len(treated)):
        treated[index] = np.array(treated[index])
    return treated

def initialize_classifier_multi():
    global model
    #load truth observationss
    directory = "testdata/joineddata"
    files = get_data_files(directory, extension=".txt")
    observationsarray = []
    garbagearray = []
    global_S_ = []
    global_labels = []

    for index, file in enumerate(files):
        print "In", index, file
        currentobservationsarray = []
        currentgarbagearray = []
        signals, blanks = dataprocessing.find_signals_improved(file)
        signals_processed = np_treat_array(signals)
        blanks_processed = np_treat_array(blanks)
        for observation in signals_processed.T:
            observationsarray.append((observation, np.array([index])))
            currentobservationsarray.append((observation, np.array([index+1])))
        for observation in blanks_processed.T:
            garbagearray.append((observation, np.array([index])))
            currentgarbagearray.append((observation, np.array([0])))

        randomdata = []
        labels = []
        S_ = []
        for obsindex, observation in enumerate(currentobservationsarray):
            if len(S_) == 0:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = ica.fit_transform(randomdata)  # Reconstruct signals
            else:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = np.c_[ica.fit_transform(randomdata), S_]  # Reconstruct signals
            labels.append(observation[1])
        for obsindex, observation in enumerate(currentgarbagearray):
            if len(S_) == 0:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = ica.fit_transform(randomdata)  # Reconstruct signals
            else:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = np.c_[ica.fit_transform(randomdata), S_]  # Reconstruct signals
            labels.append(observation[1])

        # randomdata = np.array(randomdata)
        labels = np.array(labels)
        if len(global_S_) == 0:
            global_S_ = S_
        else:
            global_S_ = np.c_[global_S_, S_]

        if len(global_labels) == 0:
            global_labels = labels
        else:
            global_labels = np.append(global_labels,labels)
    glabels = []
    for label in global_labels:
        glabels.append(np.array([label]))
    global_labels = np.array(glabels)
    n_obs = len(global_S_[0])
    n_samples = len(global_S_)
    # COnvert labels to correct format
    global_labels = to_categorical(global_labels, 6)

    model = Sequential()

    model.add(Dense(185, input_dim=n_samples, init='uniform', activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(23, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(6, activation='sigmoid'))

    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy','recall','precision', 'fmeasure','fbeta_score','categorical_accuracy'])

    # from sklearn.metrics import confusion_matrix
    model.fit(global_S_.T,global_labels,nb_epoch=40)

    #load truth observationss
    directory = "testdata/newvoweldata"
    files = get_data_files(directory, extension=".txt")
    observationsarray = []
    garbagearray = []
    global_S_ = []
    global_labels = []

    for index, file in enumerate(files):
        print "In", index, file
        currentobservationsarray = []
        currentgarbagearray = []
        signals, blanks = dataprocessing.find_signals_improved(file)
        signals_processed = np_treat_array(signals)
        if len(blanks) != 0:
            blanks_processed = np_treat_array(blanks)
            for observation in blanks_processed.T:
                garbagearray.append((observation, np.array([index])))
                currentgarbagearray.append((observation, np.array([0])))

        for observation in signals_processed.T:
            observationsarray.append((observation, np.array([index])))
            currentobservationsarray.append((observation, np.array([index+1])))

        randomdata = []
        labels = []
        S_ = []
        for obsindex, observation in enumerate(currentobservationsarray):
            if len(S_) == 0:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = ica.fit_transform(randomdata)  # Reconstruct signals
            else:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = np.c_[ica.fit_transform(randomdata), S_]  # Reconstruct signals
            labels.append(observation[1])
        for obsindex, observation in enumerate(currentgarbagearray):
            if len(S_) == 0:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = ica.fit_transform(randomdata)  # Reconstruct signals
            else:
                randomdata = []
                for item in observation[0].T:
                    randomdata.append(np.array([item]))
                randomdata = np.array(randomdata)
                randomdata /= randomdata.std(axis=0)
                # Compute ICA
                ica = FastICA(max_iter=4000)
                S_ = np.c_[ica.fit_transform(randomdata), S_]  # Reconstruct signals
            labels.append(observation[1])

        # randomdata = np.array(randomdata)
        labels = np.array(labels)
        if len(global_S_) == 0:
            global_S_ = S_
        else:
            global_S_ = np.c_[global_S_, S_]

        if len(global_labels) == 0:
            global_labels = labels
        else:
            global_labels = np.append(global_labels,labels)
    glabels = []
    for label in global_labels:
        glabels.append(np.array([label]))
    global_labels = np.array(glabels)
    n_obs = len(global_S_[0])
    n_samples = len(global_S_)
    # COnvert labels to correct format
    origlables = global_labels
    global_labels = to_categorical(global_labels, 6)

    print "Evaluating"
    print model.metrics_names
    print model.evaluate(global_S_.T,global_labels)
    pred = model.predict_classes(global_S_.T)
    print pred
    # # global_labels
    from sklearn.metrics import confusion_matrix
    print "COnf matrix"
    print confusion_matrix(origlables,pred)
    from sklearn.metrics import classification_report
    print "CR"
    print classification_report(origlables,pred)


ica = None
def classify(preprocesseddataarray):
    global ica
    if ica is None:
        ica = FastICA()
    processedarray = []
    for index, element in enumerate(preprocesseddataarray[0]):
        processedarray.append(np.array([element]))
        # preprocesseddataarray[index] /= preprocesseddataarray[index].std(axis=0)
    t = np.array(processedarray)

    t /= t.std(axis=0)
    S_ = ica.fit_transform(t)
    # S_ = S_[0:150]
    res2 = model.predict(S_.T)
    print "Results"
    print res2
    print model.predict_classes(S_.T)
    print model.predict_proba(S_.T)

    return res2


if __name__ == '__main__':
    # initialize_classifier()
    initialize_classifier_multi()
    # load test observationss
    file = "/home/pedro/Documents/git/telepathicspeech/testdata/aeoutput.txt"
    #
    sigs, blanks = dataprocessing.find_signals_improved(file)
    for sig in sigs:
        prepross = np_treat_array(sig)
        res = classify(prepross)
        print res
    # print classify(t_observations)
    # evalables = np.array([np.array([0]),np.array([0]),np.array([0]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1]),np.array([1])])
    #
    # res = model.evaluate(S_.T, evalables)

    # print "conf"
    # print confusion_matrix(evalables[:1,],res2)
    # print "end"
    # print res
    # print model.metrics_names
