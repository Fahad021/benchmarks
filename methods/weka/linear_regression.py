'''
  @file linear_regression.py
  @author Marcus Edel

  Class to benchmark the weka Linear Regression method.
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
This class implements the Linear Regression benchmark.
'''
class WEKA_LINEARREGRESSION(object):
  def __init__(self, method_param, run_param):
    # Assemble run command.
    dataset = check_dataset(method_param["datasets"], ["arff"])

    if len(dataset) >= 2:
      self.cmd = shlex.split("java -classpath " + run_param["weka_path"] +
        "/weka.jar" + ":methods/weka" + " LinearRegression -i " + dataset[0] +
        " -t " + dataset[1])
    else:
      self.cmd = shlex.split("java -classpath " + run_param["weka_path"] +
        "/weka.jar" + ":methods/weka" + " LinearRegression -i " + dataset[0])

    self.info = f"WEKA_LINEARREGRESSION ({str(self.cmd)})"
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

    return metric
