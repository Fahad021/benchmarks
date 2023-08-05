'''
  @file allknn.py
  Class to benchmark the ALLKNN method with dlibml.
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
This class implements the ALLKNN benchmark.
'''
class DLIBML_ALLKNN(object):
  def __init__(self, method_param, run_param):
    # Assemble run command.
    self.cmd = run_param["dlibml_path"] + "dlibml_allknn"
    if "datasets" in method_param:
      dataset = check_dataset(method_param["datasets"], ["csv", "txt"])
      if len(dataset) == 2:
        self.cmd += f" -r {dataset[0]} -q {dataset[1]}"
      elif len(dataset) == 1:
        self.cmd += f" -r {dataset[0]}"
    if "k" in method_param:
      self.cmd += " -k " + str(method_param["k"])
    self.cmd += " -v"

    self.info = f"DLIBML_ALLKNN ({self.cmd})"
    self.timeout = run_param["timeout"]
    self.output = None

  def __str__(self):
    return self.info

  def metric(self):
    try:
      self.output = subprocess.check_output(self.cmd, stderr=subprocess.STDOUT,
        shell=True, timeout=self.timeout)
    except subprocess.TimeoutExpired as e:
      raise Exception("method timeout")
    except Exception as e:
      subprocess_exception(e, self.output)

    metric = {}
    if timer := parse_timer(self.output):
      metric["runtime"] = timer["Nearest_Neighbors"]

    return metric
