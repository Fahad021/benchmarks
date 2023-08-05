'''
  @file dtc.py
  Class to benchmark the weka Decision Tree Classifier method.
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
This class implements the Decision Tree Classifier benchmark.
'''
class WEKA_DTC(object):
  def __init__(self, method_param, run_param):
    # Assemble run command.
    self.dataset = check_dataset(method_param["datasets"], ["arff"])

    opts = {"minimum_leaf_size": 2}
    if "minimum_leaf_size" in method_param:
      opts["minimum_leaf_size"] = int(method_param["minimum_leaf_size"])

    self.cmd = shlex.split("java -classpath " + run_param["weka_path"] +
      "/weka.jar" + ":methods/weka" + " DTC -t " + self.dataset[0] + " -T " +
      self.dataset[1] + " -M " + str(opts["minimum_leaf_size"]))

    self.info = f"WEKA_DTC ({str(self.cmd)})"
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
      metric['runtime'] = timer["total_time"]

    if len(self.dataset) >= 3:
        predictions = load_dataset("weka_predicted.csv", ["csv"])[0]
        true_labels = load_dataset(self.dataset[2], ["csv"])[0]

        metric['MSE'] = Metrics.SimpleMeanSquaredError(
          true_labels, predictions)

    return metric
