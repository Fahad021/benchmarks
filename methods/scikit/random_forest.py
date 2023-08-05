'''
  @file random_forest.py
  @author Marcus Edel

  Random Forest Classifier with scikit.
'''

import os, sys, inspect

# Import the util path, this method even works if the path contains symlinks to
# modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], "../../util")))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from util import *
from sklearn.ensemble import RandomForestClassifier

'''
This class implements the Random Forest Classifier benchmark.
'''
class SCIKIT_RANDOMFOREST(object):
  def __init__(self, method_param, run_param):
    self.info = f"SCIKIT_RANDOMFOREST ({str(method_param)})"

    # Assemble run model parameter.
    self.data = load_dataset(method_param["datasets"], ["csv"])
    self.data_split = split_dataset(self.data[0])

    self.build_opts = {}
    if "num_trees" in method_param:
      self.build_opts["n_estimators"] = int(method_param["num_trees"])
    if "fitness_function" in method_param:
      self.build_opts["criterion"] = str(method_param["fitness_function"])
    if "max_depth" in method_param:
      self.build_opts["max_depth"] = int(method_param["max_depth"])
    if "seed" in method_param:
      self.build_opts["random_state"] = int(method_param["seed"])
    if "minimum_samples_split" in method_param:
      self.build_opts["min_samples_split"] = int(
        method_param["minimum_samples_split"])
    if "minimum_leaf_size" in method_param:
      self.build_opts["min_samples_leaf"] = int(
        method_param["minimum_leaf_size"])
    if "num_jobs" in method_param:
      self.build_opts["n_jobs"] = int(method_param["num_jobs"])

  def __str__(self):
    return self.info

  def metric(self):
    totalTimer = Timer()
    with totalTimer:
      model = RandomForestClassifier(**self.build_opts)
      model.fit(self.data_split[0], self.data_split[1])

      if len(self.data) >= 2:
        predictions = model.predict(self.data[1])

    metric = {"runtime": totalTimer.ElapsedTime()}
    if len(self.data) == 3:
      confusionMatrix = Metrics.ConfusionMatrix(self.data[2], predictions)
      metric['ACC'] = Metrics.AverageAccuracy(confusionMatrix)
      metric['MCC'] = Metrics.MCCMultiClass(confusionMatrix)
      metric['Precision'] = Metrics.AvgPrecision(confusionMatrix)
      metric['Recall'] = Metrics.AvgRecall(confusionMatrix)
      metric['MSE'] = Metrics.SimpleMeanSquaredError(self.data[2], predictions)

    return metric
