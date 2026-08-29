"""
The official NASA C-MAPSS scoring function.

Unlike RMSE, this is asymmetric: predicting a LATE failure (predicted RUL
> actual RUL, i.e. the model was overconfident that the engine still had
life left) is penalized far more heavily than predicting an EARLY failure
(overly cautious). This mirrors reality -- an engine that fails before
your model warned you about it is a safety incident; an engine you
flagged too early just costs some unnecessary maintenance.

Reference: Saxena & Goebel, "Turbofan Engine Degradation Simulation
Data Set", NASA Ames Prognostics Data Repository.
"""
import numpy as np


def nasa_score(y_true, y_pred):
    d = np.asarray(y_pred) - np.asarray(y_true)
    score = np.where(d < 0, np.exp(-d / 13) - 1, np.exp(d / 10) - 1)
    return float(np.sum(score))


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def mae(y_true, y_pred):
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))
