import numpy as np
import pandas as pd
from torch.autograd import Variable
import torch.nn.functional as F


class BinaryMetrics:
    """
    Metrics measuring model performance.
    """

    def __init__(self, ref_array, score_array, pred_array=None):
        """
        Params:
            ref_array (ndarray): Array of ground truth
            score_array (ndarray): Array of pixels scores of positive class
            pred_array (ndarray): Boolean array of predictions telling whether
                                 a pixel belongs to a specific class.
        """

        self.tp = None
        self.fp = None
        self.fn = None
        self.tn = None
        self.eps = 10e-6
        self.observation = ref_array.flatten()
        self.score = score_array.flatten()
        if pred_array is not None:
            self.prediction = pred_array.flatten()
        # take score over 0.5 as prediction if predArray not provided
        else:
            self.prediction = np.where(self.score > 0.5, 1, 0)
        self.confusion_matrix = self.confusion_matrix()

        assert self.observation.shape == self.score.shape, "Inconsistent input shapes"

    def __add__(self, other):
        """
        Add two BinaryMetrics instances
        Params:
            other (''BinaryMetrics''): A BinaryMetrics instance
        Return:
            ''BinaryMetrics''
        """

        return BinaryMetrics(np.append(self.observation, other.observation),
                             np.append(self.score, other.score),
                             np.append(self.prediction, other.prediction))

    def __radd__(self, other):
        """
        Add a BinaryMetrics instance with reversed operands
        Params:
            other
        Returns:
            ''BinaryMetrics
        """

        if other == 0:
            return self
        else:
            return self.__add__(other)

    def confusion_matrix(self):
        """
        Calculate confusion matrix of given ground truth and predicted label
        Returns:
            "pandas.dataframe" of observation on the column and prediction on the row
        """

        ref_array = self.observation
        pred_array = self.prediction

        if ref_array.max() > 1 or pred_array.max() > 1:
            raise Exception("Invalid array")
        predArray = pred_array * 2
        sub = ref_array - predArray

        self.tp = np.sum(sub == -1)
        self.fp = np.sum(sub == -2)
        self.fn = np.sum(sub == 1)
        self.tn = np.sum(sub == 0)

        confusionMatrix = pd.DataFrame(data=np.array([[self.tn, self.fp], [self.fn, self.tp]]),
                                       index=['observation = 0', 'observation = 1'],
                                       columns=['prediction = 0', 'prediction = 1'])
        return confusionMatrix

    def ir(self):
        """
        Imbalance Ratio (IR) is defined as the proportion between positive and negative
        instances of the label. This value lies within the [0, ∞] range, having a value
        IR = 1 in the balanced case.
        Returns:
                float
        """
        try:
            ir = (self.tp + self.fn) / (self.fp + self.tn)

        except ZeroDivisionError:
            ir = (self.tp + self.fn) / (self.fp + self.tn + self.eps)

        return ir

    def accuracy(self):
        """
        Calculate Overall (Global) Accuracy.
        Returns:
            float scalar
        """
        try:
            oa = (self.tp + self.tn) / (self.tp + self.tn + self.fp + self.fn)

        except ZeroDivisionError:
            oa = (self.tp + self.tn) / (self.tp + self.tn + self.fp + self.fn + self.eps)

        return oa

    def precision(self):
        """
        Calculate User’s Accuracy (Positive Prediction Value (PPV) | UA).
        Returns:
            float
        """
        try:
            ua = self.tp / (self.tp + self.fp)

        except ZeroDivisionError:
            ua = self.tp / (self.tp + self.fp + self.eps)

        return ua

    def recall(self):
        """
        Calculate Producer's Accuracy (True Positive Rate |Sensitivity |hit rate | recall).
        Returns:
            float
        """
        try:
            pa = self.tp / (self.tp + self.fn)

        except ZeroDivisionError:
            pa = self.tp / (self.tp + self.fn + self.eps)

        return pa

    def false_positive_rate(self):
        """
        Calculate False Positive Rate(FPR) aka. False Alarm Rate (FAR), or Fallout.
        Returns:
             float
        """
        try:
            fpr = self.fp / (self.tn + self.fp)

        except ZeroDivisionError:
            fpr = self.fp / (self.tn + self.fp + self.eps)

        return fpr

    def iou(self):
        """
        Calculate interception over union for the positive class.
        Returns:
            float
        """

        try:
            iou = self.tp / (self.tp + self.fp + self.fn)
        except ZeroDivisionError:
            iou = self.tp / (self.tp + self.fp + self.fn + self.eps)

        return iou

    def f1_measure(self):
        """
        Calculate F1 score.
        Returns:
            float
        """

        try:
            precision = self.tp / (self.tp + self.fp)
            recall = self.tp / (self.tp + self.fn)
            f1 = (2 * precision * recall) / (precision + recall)

        except ZeroDivisionError:
            precision = self.tp / (self.tp + self.fp + self.eps)
            recall = self.tp / (self.tp + self.fn + self.eps)
            f1 = (2 * precision * recall) / (precision + recall + self.eps)

        return f1

    def tss(self):
        """
        Calculate true skill statistic (TSS)
        Returns:
            float
        """

        return self.tp / (self.tp + self.fn) + self.tn / (self.tn + self.fp) - 1


def do_accuracy_evaluation(eval_data, model, filename, gpu=True):
    r"""
    Evaluate the model on a separate Landsat scene.

    Arguments:
    eval_data -- Batches of image chips from PyTorch custom dataset(AquacultureData)
    model -- Choice of segmentation Model to train.
    filename -- (str) Name of the csv file to report metrics.
    gpu --(binary) If False the model will run on CPU instead of GPU. Default is True.

    Note: to harden the class prediction around a higher probability, drop 'class_pred' argument
          and increase the threshold of 'predArray' in the 'BinaryMetrics' class '__init__' function.

    """

    model.eval()

    metrics_ls = []

    # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    for img_chips, label in eval_data:

        img = Variable(img_chips, requires_grad=False)  # size: batch size X channels X W X H
        label = Variable(label, requires_grad=False)  # size: batch size X W X H

        if gpu:
            img = img.cuda()
            label = label.cuda()

        pred = model(img)  # size: batch size x number of categories X W x H
        pred_prob = F.softmax(pred, 1)
        batch, n_class, height, width = pred_prob.size()

        for i in range(batch):
            label_batch = label[i, :, :].cpu().numpy()
            batch_pred = pred_prob.max(dim=1)[1][:, :, :].data[i].cpu().numpy()

            for n in range(1, n_class):
                class_prob = pred_prob[:, n, :, :].data[i].cpu().numpy()
                class_pred = np.where(batch_pred == n, 1, 0)
                class_label = np.where(label_batch == n, 1, 0)
                chip_metrics = BinaryMetrics(class_label, class_prob, class_pred)

                try:
                    metrics_ls[n - 1].append(chip_metrics)
                except:
                    metrics_ls.append([chip_metrics])

    metrics = [sum(m) for m in metrics_ls]

    report = pd.DataFrame({
        "Imbalance Ratio": [m.ir() for m in metrics],
        "Overall Accuracy": [m.accuracy() for m in metrics],
        "Precision (UA or PPV)": [m.precision() for m in metrics],
        "Recall (PA or TPR or Sensitivity)": [m.recall() for m in metrics],
        "False Positive Rate": [m.false_positive_rate() for m in metrics],
        "IoU": [m.iou() for m in metrics],
        "F1-score": [m.f1_measure() for m in metrics],
        "TSS": [m.tss() for m in metrics]
    }, ["class_{}".format(m) for m in range(1, len(metrics) + 1)])

    report.to_csv(filename, index=False)