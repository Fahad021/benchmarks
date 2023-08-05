'''
  @file qda.py
  Class to benchmark the matlab qda method.
'''

import os, sys, inspect, shlex, subprocess

# Import the util path, this method even works if the path contains symlinks to
# modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], "../../util")))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from util import *

'''
This class implements the QDA benchmark.
'''
class MATLAB_QDA(object):
  def __init__(self, method_param, run_param):
    # Assemble run command.
    self.dataset = method_param["datasets"]

    inputCmd = f"-t {self.dataset[0]} -T {self.dataset[1]}"
    # Split the command using shell-like syntax.
    self.cmd = shlex.split(run_param["matlab_path"] +
      "matlab -nodisplay -nosplash -r \"try, QDA('" + inputCmd +
      "'), catch, exit(1), end, exit(0)\"")

    self.info = f"MATLAB_QDA ({str(self.cmd)})"
    self.timeout = run_param["timeout"]
    self.output = None

  def __str__(self):
    return self.info

  def metric(self):
    try:
      self.output = subprocess.check_output(self.cmd, stderr=subprocess.STDOUT,
        shell=False, timeout=self.timeout)
    except subprocess.TimeoutExpired as e:
      raise Exception("method timeout")
    except Exception as e:
      subprocess_exception(e, self.output)

    metric = {}
    if timer := parse_timer(self.output):
      metric["runtime"] = timer["total_time"]

      if len(self.dataset) > 2:
        predictions = load_dataset("predictions.csv", ["csv"])[0]
        true_labels = load_dataset(self.dataset[2], ["csv"])[0]

        confusionMatrix = Metrics.ConfusionMatrix(true_labels, predictions)
        metric['ACC'] = Metrics.AverageAccuracy(confusionMatrix)
        metric['MCC'] = Metrics.MCCMultiClass(confusionMatrix)
        metric['Precision'] = Metrics.AvgPrecision(confusionMatrix)
        metric['Recall'] = Metrics.AvgRecall(confusionMatrix)
        metric['MSE'] = Metrics.SimpleMeanSquaredError(true_labels, predictions)

    return metric
