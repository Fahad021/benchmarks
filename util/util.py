'''
  @file sqlite.py
  @author Marcus Edel
  @author Anand Soni
  @contributor Rukmangadh Sai Myana

  Utility functions.
'''

import timeout_decorator
import time
import numpy as np
import sys
import math
import os
import imp
import copy
import shlex

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess

'''
This class contains a function to import modules and scripts.
'''
class Loader(object):

  '''
  Import a module from a path.

  @param path - The path to the module.
  @return The name of the module.
  '''
  @staticmethod
  def ImportModuleFromPath(path):
    destinationPath = os.path.dirname(path)

    if destinationPath == "":
      destinationPath = '.'

    # Remove the .py suffix.
    scriptName = os.path.basename(path)

    modName = scriptName[:-3] if scriptName.endswith(".py") else scriptName
    fileHandle = None
    try:
      tup = imp.find_module(modName, [destinationPath])
      module = imp.load_module(modName, *tup)
      fileHandle = tup[0]
    finally:
      if fileHandle is not None:
        fileHandle.close()

    # Return the name of the module.
    return module

'''
This class contains a function to mesure the time.
'''
class Timer(object):

  '''
  Start the timer.
  '''
  def __enter__(self):
    self.__start = time.time()

  '''
  Stop the timer.
  '''
  def __exit__(self, type, value, traceback):
    self.__finish = time.time()

  '''
  Return the elapsed time of the timer.
  '''
  def ElapsedTime(self):
    return self.__finish - self.__start

'''
Parse the mlpack timer from the given data.
'''
def parse_mlpack_timer(data):
  timer_start = False
  timer = {}
  for line in data.splitlines():
    if "Program timers:" in line:
      timer_start = True
      continue

    if timer_start == True and line.endswith("s"):
      splits = line.split(" ")
      if len(splits) >= 2:
        timer_name = splits[len(splits) - 2][:-1]
        timer_value = splits[len(splits) - 1][:-1]
        if "," in timer_value:
          timer_value.replace(',', '.')

        timer[timer_name] = float(timer_value)

  return timer

'''
Parse the weka timer from the given data.
'''
def parse_weka_timer(data):
  timer_start = False
  timer = {}
  for line in data.splitlines():
    if "weka" in line:
      timer_start = True
      continue

    if timer_start == True and line.endswith("s"):
      splits = line.split(" ")
      if len(splits) >= 2:
        timer_name = splits[len(splits) - 2][:-1]
        timer_value = splits[len(splits) - 1][:-1]
        if "," in timer_value:
          timer_value.replace(',', '.')

        timer[timer_name] = float(timer_value)

  return timer

'''
Parse the matlab timer from the given data.
'''
def parse_matlab_timer(data):
  timer = {}
  for line in data.splitlines():
    if "INFO" in line:
      splits = line.split(" ")
      if len(splits) >= 2:
        timer_name = splits[len(splits) - 2][:-1]
        timer_value = splits[len(splits) - 1][:-1]
        timer[timer_name] = float(timer_value)

  return timer

'''
Parse the timer from the given data.
'''
def parse_timer(data):
  data = data.decode("utf-8")

  if "www.mathworks.com" in data:
    return parse_matlab_timer(data)
  elif "weka" in data:
    return parse_weka_timer(data)
  else:
    return parse_mlpack_timer(data)

'''
Add arff header to the given data.s
'''
def add_arff_header(data, new_data):
  # Extract the dataset name.
  relationName = os.path.splitext(os.path.basename(data))[0].split('_')[0]

  with open(data) as fid:
    head = [next(fid) for _ in range(1)]
  # We can convert files with ' ' and ',' as seperator.
  count = max(head[0].count(","), head[0].count(" ")) + 1

  with open(new_data, "a") as nfid:
    nfid.write(f"@relation {relationName}" + "\n\n")
    for i in range(count):
      nfid.write(f"@attribute {data}_dim{str(i)}" + " NUMERIC\n")
    nfid.write("\n@data\n")

    with open(data, "r") as fid:
      while True:
        if line := fid.read(65536):
          nfid.write(line)
        else:
          break

'''
Pretty subprocess exception output.
'''
def subprocess_exception(e, output):
  if output:
    raise Exception(f"{str(e)} -- " + output.decode("utf-8"))
  else:
    raise Exception(str(e))

'''
Extend the given param if the sweep option is set.
'''
def param_extension(param):
  def frange(x, y, jump):
    while x < y:
      yield x
      x += jump

  options = []
  for option in param:
    sweep = False
    for key, value in option.items():

      if "sweep" in str(value):
        sweep_option = str(value)
        sweep_option = sweep_option.replace("sweep(", "")[:-1]
        sweep_option = sweep_option.split(",")

        for value in frange(float(sweep_option[0]), float(sweep_option[1]),
          float(sweep_option[2])):
          new_option = copy.deepcopy(option)
          new_option[key] = value
          options.append(new_option)

        sweep = True
    if not sweep:
      options.append(option)

  return options

'''
Load the given datasets if supported.
'''
def load_dataset(datasets, support):
  datasets = check_dataset(datasets, support)
  # if isinstance(datasets, str):
  #   datasets = [datasets]

  if len(datasets) == 1 and "csv" in support:
      return (np.genfromtxt(datasets[0], delimiter=','),)
  if len(datasets) == 2 and "csv" in support:
    return np.genfromtxt(datasets[0],
                         delimiter=','), np.genfromtxt(datasets[1],
                                                       delimiter=',')
  if len(datasets) == 3 and "csv" in support:
    return (
        np.genfromtxt(datasets[0], delimiter=','),
        np.genfromtxt(datasets[1], delimiter=','),
        np.genfromtxt(datasets[2], delimiter=','),
    )

'''
Check if the specified dataset exists.
'''
def check_dataset(datasets, support):
  if isinstance(datasets, str):
    datasets = [datasets]

  for d_idx, d in enumerate(datasets):
    if not os.path.exists(d):
      raise Exception(f"file  {str(d)} not found.")
    extension = os.path.splitext(d)[1][1:]

    check = False
    for s in support:
      data_supported = d[:len(d) - len(extension)] + s
      ex = s
      if os.path.isfile(data_supported):
        check = True
        break

    if (not check and ex != "arff" and os.path.isfile(data_supported)
        or check and datasets[d_idx] not in data_supported):
      datasets[d_idx] = data_supported
    elif not check and ex != "arff" and not os.path.isfile(data_supported):
      raise Exception("No conversion possible.")

    elif not check:
      add_arff_header(d, data_supported)
      datasets[d_idx] = data_supported
  return datasets


'''
Split the train labels from the given train dataset.
'''
def split_dataset(dataset):
  if isinstance(dataset, (list, tuple)):
    dataset = dataset[0]

  return (dataset[:,:-1], dataset[:, (dataset.shape[1] - 1)])

'''
Encodes the classification labels.

@type train_labels - numpy.ndarray
@param train_labels - Numpy array of labels.
@type label_type - str
@param label_type - The type of the label.
@type convention - str
@param convention - The convention to be followed while encoding.
@rtype - tuple
@returns - The encoded labels and the label map encoding.

Notes
-----
This function is required by Shogun for multiclass classification because
Shogun requires that the multiclass classifiction labels are in the format {0,
1,....., num_classes-1} while training

This function is also required by Shogun for binary classification because
Shogun requires that the binary classification labels are in the format {-1,1}
while training.
'''
def label_encoder(train_labels, label_type="multiclass", convention="Shogun"):
  if convention == "Shogun":

    if label_type == "multiclass":
      distinct_labels = set(train_labels)
      num_labels = len(set(train_labels))
      classes = np.linspace(0, num_labels, num_labels, endpoint=False)
      label_map = dict(zip(distinct_labels, classes))
      train_labels = np.array([label_map[label] for label in train_labels])
      return train_labels, label_map

    elif label_type == "binary":
      distinct_labels = set(train_labels)
      num_labels = len(set(train_labels))
      assert num_labels==2, "Provided train_labels are not binary labels"
      classes = np.array([-1,1])
      label_map = dict(zip(distinct_labels, classes))
      train_labels = np.array([label_map[label] for label in train_labels])
      return train_labels, label_map

'''
Decodes the encoded label into original labels.

@type predicted_labels - numpy.ndarray
@param predicted_labels - Numpy array of labels
@type label_map - dict
@param label_map - The label encoding
@rtype - numpy.ndarray
@returns - Original labels

Notes
-----
This function is required by Shogun for multiclass classification because
Shogun requires that the multiclass classifiction labels are in the format {0,
1,....., num_classes-1} while training. This function is to be used only after 
the label_map is generated using above function.

This function is also required by Shogun for binary classification because
Shogun requires that the binary classification labels are in the format {-1,1}
while training. This function is to be used only after the label_map is 
generated using above function.
'''
def label_decoder(predicted_labels, label_map):
  reverse_map = {value:key for key,value in label_map.items()}
  predicted_labels = np.array(
    [reverse_map[label] for label in predicted_labels])
  return predicted_labels

'''
Implementation of various metrics common to all classifiers.
'''
class Metrics(object):

  '''
  @param labels - File containing true labels
  @param prediction - File containing predicted labels
  Create the confusion matrix from the two arrays containing the true labels and
  the predicted labels. The confusion matrix contains all information about the
  number of true and false positives and negatives for all the classes in
  consideration.
  '''
  @staticmethod
  def ConfusionMatrix(labels, prediction):
    from sklearn.metrics import confusion_matrix
    return confusion_matrix(labels, prediction)

  '''
  @param CM - The confusion matrix
  This function is a great and simple one that can be used as a debugging tool
  for metrics involving true/false positives/negatives. Uncomment the call to
  this function in RunMetrics(..) to see the Confusion Matrix visually!
  '''
  @staticmethod
  def VisualizeConfusionMatrix(CM):
    import pylab as pl
    print(CM)
    pl.matshow(CM)
    pl.title('Confusion Matrix')
    pl.colorbar()
    pl.ylabel('True Label')
    pl.xlabel('Predicted Label')
    pl.show()

  '''
  @param CM - The confusion matrix
  Average accuracy measure. The average accuracy is defined as the average/mean
  of accuracies of prediction obtained for each class in consideration. We use
  the confusion matrix as the parameter to this function.
  '''
  @staticmethod
  def AverageAccuracy(CM):
    acc=0.0
    Sum=0
    l=len(CM)
    for i in range(l):
        for j in range(l):
            Sum+=CM[i][j]
        acc = acc + (float(CM[i][i])/float(Sum))*100.0
        Sum=0
    acc = acc/l
    return acc/100.0


  '''
  @param class_i - Index of the class in the confusion matrix
  @param CM - The confusion matrix
  Precision measure for a single class. Arguments provided to this method are the
  confusion matrix and the class index in the confusion matrix (class_i). It is not
  the actual label for the class.
  '''
  @staticmethod
  def PrecisionForAClass(class_i,CM):
    l=len(CM)
    truePositives = CM[class_i][class_i]
    falsePositives = sum(CM[j][class_i] for j in range(l))
    falsePositives-=truePositives
    totalPositives = truePositives + falsePositives
    return truePositives/totalPositives if totalPositives != 0 else 1

  '''
  @param class_i - Index of the class in the confusion matrix
  @param CM - The confusion matrix
  Recall measure for a single class. Arguments provided to this method are the
  confusion matrix and the class index in the confusion matrix (class_i). It is not
  the actual label for the class.
  '''
  @staticmethod
  def RecallForAClass(class_i,CM):
    l=len(CM)
    truePositives = CM[class_i][class_i]
    falseNegatives = sum(CM[class_i][j] for j in range(l))
    falseNegatives-=truePositives
    total = truePositives + falseNegatives
    return truePositives/total

  '''
  @param CM - The confusion matrix
  AvgPrecision(AvgRecall) represents the average of precisions(recall) obtained from each
  classifier. Since precision and recall are defined for binary classifiers, we
  can only calculate these measures for all the classes individually. AvgPrecision
  (AvgRecall) can be thought of as a new measure of performance for a multi-class
  classifier (One vs All approach).
  '''
  @staticmethod
  def AvgPrecision(CM):
    l=len(CM)
    avgPrecision = sum(Metrics.PrecisionForAClass(i,CM) for i in range(l))
    avgPrecision = avgPrecision/l
    return avgPrecision

  @staticmethod
  def AvgRecall(CM):
    l=len(CM)
    avgRecall = sum(Metrics.RecallForAClass(i,CM) for i in range(l))
    avgRecall = avgRecall/l
    return avgRecall

  '''
  @param class_i - Index of the class in the confusion matrix
  @param CM - The confusion matrix
  FMeasure for a class is defined as the harmonic mean of precision and recall.
  '''
  @staticmethod
  def FMeasureClass(class_i,CM):
    l = len(CM)
    precClass = Metrics.PrecisionForAClass(class_i,CM)
    recClass = Metrics.RecallForAClass(class_i,CM)
    if precClass + recClass != 0:
      return 2*precClass*recClass/(precClass+recClass)
    #Took care of the edge case here!
    truePositives = CM[class_i][class_i]
    falsePositives = sum(CM[j][class_i] for j in range(l))
    falsePositives-=truePositives
    falseNegatives = sum(CM[class_i][j] for j in range(l))
    falseNegatives-=truePositives
    trueNegatives=0
    #calculate trueNegatives
    for i in range(l):
      if i!=class_i:
        for j in range(l):
          trueNegatives+=CM[i][j]
        trueNegatives-=CM[i][class_i]
    return 2*truePositives / (2*truePositives + falsePositives + falseNegatives)


  '''
  @param CM - The confusion matrix
  AvgFMeasure represents the average of FMeasures of all the classes in
  consideration.
  '''
  @staticmethod
  def AvgFMeasure(CM):
    l=len(CM)
    avgF = sum(Metrics.FMeasureClass(i,CM) for i in range(l))
    avgF = avgF/l
    return avgF

  '''
  @param class_i - Index of the class in the confusion matrix
  @param CM - The confusion matrix
  Lift represents the ratio of the (%positives > threshold) to
  the (%total > threshold). Positive class decides the threshold.
  '''
  @staticmethod
  def LiftForAClass(class_i,CM):
    l=len(CM)
    #pgt - positives greater than threshold
    pgt = 0
    #tgt - total greater than threshold
    tgt = 0
    total = 0
    for i in range(l):
      pgt = pgt + CM[class_i][i]
    pgt = (1/pgt) * CM[class_i][class_i]
    for j in range(l):
      tgt = tgt + CM[j][0]
    for i in range(l):
      for j in range(l):
        total = total + CM[i][j]
    tgt = tgt/total
    return pgt/tgt


  '''
  @param CM - The confusion matrix
  Lift represents the ratio of the (%positives > threshold) to
  the (%total > threshold). Positive class decides the threshold.
  To convert this binary class measure into multi-class measure, we
  have used the LiftForAClass method to obtain Lifts for each class
  applying the One vs All technique.
  '''
  @staticmethod
  def LiftMultiClass(CM):
    l=len(CM)
    AvgLift = sum(Metrics.LiftForAClass(i,CM) for i in range(l))
    AvgLift/=l
    return AvgLift


  '''
  @param class_i - Index of the class in the confusion matrix
  @param CM - The confusion matrix
  MCC is a balanced measure which returns values between +1 and -1.
  A coefficient of +1 represents a perfect prediction, 0 no better than random
  prediction and -1 indicates total disagreement between
  prediction and observation.
  '''
  @staticmethod
  def MatthewsCorrelationCoefficientClass(class_i, CM):
    l=len(CM)
    truePositives = CM[class_i][class_i]
    falsePositives = sum(CM[j][class_i] for j in range(l))
    falsePositives-=truePositives
    falseNegatives = sum(CM[class_i][j] for j in range(l))
    falseNegatives-=truePositives
    trueNegatives=0
    #calculate trueNegatives
    for i in range(l):
      if i!=class_i:
        for j in range(l):
          trueNegatives+=CM[i][j]
        trueNegatives-=CM[i][class_i]
    Numerator = (truePositives*trueNegatives) - (falsePositives*falseNegatives)
    Denominator=math.sqrt((truePositives + falsePositives)*
                            (truePositives + falseNegatives)*
                            (trueNegatives + falsePositives)*
                            (trueNegatives + falseNegatives))
    return Numerator/Denominator if Denominator != 0 else 0


  '''
  @param CM - The confusion matrix
  MCC is a balanced measure which returns values between +1 and -1.
  A coefficient of +1 represents a perfect prediction, 0 no better
  than random prediction and -1 indicates total disagreement between
  prediction and observation. We use the MCC for a single class as
  obtained by applying the One vs All approach in the above method
  below.
  '''
  @staticmethod
  def MCCMultiClass(CM):
    l=len(CM)
    MCC = sum(Metrics.MatthewsCorrelationCoefficientClass(i,CM) for i in range(l))
    MCC/=l
    return MCC

  '''
  @param truelabelFile - Name of the file which contains the true label
  for the instance
  @param probabilities - Name of the file which contains the probabilities
  for that instance to be in a particular class (CSV)
  @param CM - The confusion matrix
  Mean squared error for classifiers which return probabilities can be
  implemented in terms of the Quadratic Loss function as defined below.
  '''
  @staticmethod
  def MeanSquaredError(truelabelFile, probabilities, CM):
    #l : Number of classes
    l=len(CM)
    #trueVec : Vector/list with trueVec[index]=1 for the true class, 0 otherwise
    Vec = np.genfromtxt(truelabelFile,delimiter=',')
    instances=len(Vec)
    trueVec=[]
    for i in range(instances):
      vec = [0 for _ in range(l)]
      for _ in range(l):
        vec[int(Vec[i])-1]=1
      trueVec.append(vec)
    #trueArray : 2D numpy array after converting trueVec
    trueArray=np.array(trueVec)
    #probVec : 2D numpy array with trueVec[index]=probability for the instance
    #to be in that class.
    probVec = np.genfromtxt(probabilities,delimiter=',')
    diffArray = trueArray - probVec
    #Quadratic Loss Function
    quadraticLoss=[]
    for i in range(len(diffArray)):
      squaredloss=0
      for j in range(len(diffArray[i])):
        squaredloss+=diffArray[i][j]*diffArray[i][j]
        quadraticLoss.append(squaredloss)
    quadraticLoss=np.array(quadraticLoss)
    #Divide the total squared loss for each instance by the number of classes
    quadraticLoss = quadraticLoss/l
    totalLoss = sum(quadraticLoss[i] for i in range(len(quadraticLoss)))
    return totalLoss/instances


  '''
  @param truelabels - Name of the file which contains the true label
  for the instance
  @param predictedlabels - Name of the file which contains the predicted
  labels for the instance
  Mean predictive information is a metric closely related to cross
  entropy and conveniently gives easily interpretable results.
  The below implementation is only for binary classifiers.
  '''
  @staticmethod
  def MeanPredictiveInformationClass(class_i, truelabels, predictedlabels):
    predicted=np.genfromtxt(predictedlabels, delimiter=',')
    actual=np.genfromtxt(truelabels, delimiter=',')
    instances=len(actual)
    predictiveSum=0
    count=0
    for i in range(instances):
      if actual[i] == class_i:
        count+=1
        '''
        predictiveSum+=((actual[i] * math.log(predicted[i],2))+
                          ((1-actual[i]) * math.log(1-predicted[i],2)))
        We take actual[i] to be 0. Hence, the formula :
        We take 0.05 instead of absolute 0 and 0.95 instead of absolute 1
        to guarantee that an absolute 0 value doesn't become an argument
        to logarithm.
        '''
        predicted_val=0.05
        actual_val=0.05
        if predicted[i] != actual[i]:
          predicted_val = 0.95

        predictiveSum+=((actual_val*math.log(predicted_val,2)) + (predicted_val*math.log(1 - predicted_val,2)))

    if count != 0:
      predictiveSum/=count
    predictiveSum+=1
    return predictiveSum

  @staticmethod
  def MPIArrayClass(class_i, truelabels, predictedlabels):
    instances=len(truelabels)
    predictiveSum=0
    count=0
    for i in range(instances):
      if truelabels[i] == class_i:
        count+=1
        '''
        predictiveSum+=((actual[i] * math.log(predicted[i],2))+
                          ((1-actual[i]) * math.log(1-predicted[i],2)))
        We take actual[i] to be 0. Hence, the formula :
        We take 0.05 instead of absolute 0 and 0.95 instead of absolute 1
        to guarantee that an absolute 0 value doesn't become an argument
        to logarithm.
        '''
        predicted_val=0.05
        actual_val=0.05
        if predictedlabels[i] != truelabels[i]:
          predicted_val = 0.95

        predictiveSum+=((actual_val*math.log(predicted_val,2)) + (predicted_val*math.log(1 - predicted_val,2)))

    if count != 0:
      predictiveSum/=count
    predictiveSum+=1
    return predictiveSum

  '''
  This method extracts all the labels from the truelabels file in a list
  and returns this list. We can get the actual label value of a particular
  row in the CM using this list.
  '''
  @staticmethod
  def GetActualLabels(truelabels):
    labels = [truelabels[0]]
    for i in range(len(truelabels)):
      if truelabels[i] not in labels:
        labels.append(truelabels[i])
    return labels


  '''
  @param CM - The confusion matrix
  @param truelabels - File with true labels for each instance
  @param predictedlabels - File with predicted label for each instance
  This is the average mean predictive information measure. We calculate
  MPI for each class applying the One vs All approach and take the average.
  '''
  @staticmethod
  def AvgMeanPredictiveInformation(CM, truelabels, predictedlabels):
    predicted=np.genfromtxt(predictedlabels, delimiter=',')
    actual=np.genfromtxt(truelabels, delimiter=',')
    all_labels = Metrics.GetActualLabels(actual)
    mpi = sum(
        Metrics.MeanPredictiveInformationClass(
            all_labels[i], truelabels, predictedlabels) for i in range(len(CM)))
    mpi/=len(CM)
    return mpi

  '''
  @param CM - The confusion matrix
  @param truelabels - Array with true labels for each instance
  @param predictedlabels - Array with predicted label for each instance
  This is the average mean predictive information measure. We calculate
  MPI for each class applying the One vs All approach and take the average.
  '''
  @staticmethod
  def AvgMPIArray(CM, truelabels, predictedlabels):
    all_labels = Metrics.GetActualLabels(truelabels)
    mpi = sum(
        Metrics.MPIArrayClass(all_labels[i], truelabels, predictedlabels)
        for i in range(len(CM)))
    mpi/=len(CM)
    return mpi

  '''
  @param truelabels - Array containing the true labels for the test data
  @param predictedlabels - Array containing the predicted labels for test data
  This method computes the Mean Squared Error based on the true labels and
  predicted labels from a classifier. We use this method when we donot get the
  required probabilities to compute quadratic loss function.
  '''
  @staticmethod
  def SimpleMeanSquaredError(truelabels, predictedlabels):
    simplemse = 0
    n = len(truelabels)
    for i in range(n):
      difference = truelabels[i] - predictedlabels[i]
      simplemse += difference * difference
    simplemse /= n
    return simplemse
