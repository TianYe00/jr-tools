import numpy as np
from nose.tools import assert_true
from ..classifiers import (PolarRegression, AngularRegression,
                           SVR_polar, SVR_angle)

def make_circular_data():
    from jr.meg import mat2mne
    # Toy circular data
    n_trial, n_chan, n_time = 198, 100, 4
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]  # equidistant angles

    # ---- template topography for each angle
    X0 = np.linspace(0, 2, np.sqrt(n_chan)) - 1
    coefs = list()
    for a, angle in enumerate(angles):
        Xm, Ym = np.meshgrid(X0, X0)
        Xm += np.cos(angle)
        Ym += np.sin(angle)
        coefs.append(np.exp(-((Xm ** 2) + (Ym ** 2))))

    # ---- add noisy topo to each trial at time=1, pi shift at time=2
    snr = 10.
    X = np.random.randn(n_trial, n_chan, n_time) / snr
    y = np.arange(n_trial) % len(angles)
    for trial in range(n_trial):
        X[trial, :, 1] += coefs[y[trial]].flatten()
        X[trial, :, 2] += coefs[y[(trial + len(angles)/2) % len(angles)]].flatten()

    # ---- export in mne structure
    events = np.array(y * 10, int)  # need integers, and avoid duplicate
    epochs = mat2mne(X, events=events)
    return epochs, y

def show_circular_data():
    import matplotlib.pyplot as plt
    epochs, angles = make_circular_data()
    coefs = list()
    sel_time = 1 # select only one time point
    for ii in np.unique(angles):
        # select each trial
        sel_y = np.where(angles==ii)[0]
        # get mean effect
        coef = np.mean(epochs._data[sel_y, :, sel_time], axis=0)
        # square image
        coef = np.reshape(coef, [np.sqrt(len(coef))] * 2)
        coefs.append()
    for coef in coefs:
        plt.matshow(coef[:, 1])
    plt.show()

def test_circular_classifiers():
    from mne.decoding import GeneralizationAcrossTime
    import matplotlib.pyplot as plt
    from ..scorers import scorer_angle
    epochs, angles = make_circular_data()
    clf_list = [PolarRegression(random_state=0),
                AngularRegression(random_state=0),
                SVR_polar(random_state=0),  # to be deprecated
                SVR_angle(random_state=0)]  # to be deprecated
    for clf in clf_list:
        gat = GeneralizationAcrossTime(clf=clf, scorer=scorer_angle)
        gat.fit(epochs, y=angles)
        gat.predict(epochs)
        gat.score(y=angles)
        assert_true(np.abs(gat.scores_[0][0]) < .1)  # chance level
        assert_true(gat.scores_[1][1] > 1.)  # decode
        assert_true(gat.scores_[2][2] > 1.)  # decode
        assert_true(gat.scores_[1][2] < -1.)  # anti-generalize
