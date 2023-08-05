'''
  @file logistic_regression.py
  @author Anand Soni

  Logistic Regression with scikit.
'''

import os, sys, inspect

# Import the util path, this method even works if the path contains symlinks to
# modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], "../../util")))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from util import *
from sklearn.linear_model import LogisticRegression as SLogisticRegression

'''
This class implements the Logistic Regression benchmark.
'''
class SCIKIT_LOGISTICREGRESSION(object):
  def __init__(self, method_param, run_param):
    self.info = f"SCIKIT_LOGISTICREGRESSION ({str(method_param)})"

    # Assemble run model parameter.
    self.data = load_dataset(method_param["datasets"], ["csv"])
    self.data_split = split_dataset(self.data[0])

    self.build_opts = {}
    if "algorithm" in method_param:
      self.build_opts["solver"] = str(method_param["algorithm"])
    if "epsilon" in method_param:
      self.build_opts["epsilon"] = float(method_param["epsilon"])
    if "max_iterations" in method_param:
      self.build_opts["max_iter"] = int(method_param["max_iterations"])

  def __str__(self):
    return self.info

  def metric(self):
    totalTimer = Timer()
    with totalTimer:
      model = SLogisticRegression(**self.build_opts)
      model.fit(self.data_split[0], self.data_split[1])

      if len(self.data) >= 2:
        predictions = model.predict(self.data[1])
        b = model.coef_

    metric = {"runtime": totalTimer.ElapsedTime()}
    if len(self.data) == 3:
      confusionMatrix = Metrics.ConfusionMatrix(self.data[2], predictions)
      metric['ACC'] = Metrics.AverageAccuracy(confusionMatrix)
      metric['MCC'] = Metrics.MCCMultiClass(confusionMatrix)
      metric['Precision'] = Metrics.AvgPrecision(confusionMatrix)
      metric['Recall'] = Metrics.AvgRecall(confusionMatrix)
      metric['MSE'] = Metrics.SimpleMeanSquaredError(self.data[2], predictions)

    return metric
