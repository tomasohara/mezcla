#! /usr/bin/env python3
#
# via https://scikit-learn.org/1.0/auto_examples/model_selection/plot_precision_recall.html
#
"""
================
Precision-Recall
================

Example of Precision-Recall metric to evaluate classifier output quality.

Precision-Recall is a useful measure of success of prediction when the
classes are very imbalanced. In information retrieval, precision is a
measure of result relevancy, while recall is a measure of how many truly
relevant results are returned.

The precision-recall curve shows the tradeoff between precision and
recall for different threshold. A high area under the curve represents
both high recall and high precision, where high precision relates to a
low false positive rate, and high recall relates to a low false negative
rate. High scores for both show that the classifier is returning accurate
results (high precision), as well as returning a majority of all positive
results (high recall).

A system with high recall but low precision returns many results, but most of
its predicted labels are incorrect when compared to the training labels. A
system with high precision but low recall is just the opposite, returning very
few results, but most of its predicted labels are correct when compared to the
training labels. An ideal system with high precision and high recall will
return many results, with all results labeled correctly.

Precision (:math:`P`) is defined as the number of true positives (:math:`T_p`)
over the number of true positives plus the number of false positives
(:math:`F_p`).

:math:`P = \\frac{T_p}{T_p+F_p}`

Recall (:math:`R`) is defined as the number of true positives (:math:`T_p`)
over the number of true positives plus the number of false negatives
(:math:`F_n`).

:math:`R = \\frac{T_p}{T_p + F_n}`

These quantities are also related to the (:math:`F_1`) score, which is defined
as the harmonic mean of precision and recall.

:math:`F1 = 2\\frac{P \\times R}{P+R}`

Note that the precision may not decrease with recall. The
definition of precision (:math:`\\frac{T_p}{T_p + F_p}`) shows that lowering
the threshold of a classifier may increase the denominator, by increasing the
number of results returned. If the threshold was previously set too high, the
new results may all be true positives, which will increase precision. If the
previous threshold was about right or too low, further lowering the threshold
will introduce false positives, decreasing precision.

Recall is defined as :math:`\\frac{T_p}{T_p+F_n}`, where :math:`T_p+F_n` does
not depend on the classifier threshold. This means that lowering the classifier
threshold may increase recall, by increasing the number of true positive
results. It is also possible that lowering the threshold may leave recall
unchanged, while the precision fluctuates.

The relationship between recall and precision can be observed in the
stairstep area of the plot - at the edges of these steps a small change
in the threshold considerably reduces precision, with only a minor gain in
recall.

**Average precision** (AP) summarizes such a plot as the weighted mean of
precisions achieved at each threshold, with the increase in recall from the
previous threshold used as the weight:

:math:`\\text{AP} = \\sum_n (R_n - R_{n-1}) P_n`

where :math:`P_n` and :math:`R_n` are the precision and recall at the
nth threshold. A pair :math:`(R_k, P_k)` is referred to as an
*operating point*.

AP and the trapezoidal area under the operating points
(:func:`sklearn.metrics.auc`) are common ways to summarize a precision-recall
curve that lead to different results. Read more in the
:ref:`User Guide <precision_recall_f_measure_metrics>`.

Precision-recall curves are typically used in binary classification to study
the output of a classifier. In order to extend the precision-recall curve and
average precision to multi-class or multi-label classification, it is necessary
to binarize the output. One curve can be drawn per label, but one can also draw
a precision-recall curve by considering each element of the label indicator
matrix as a binary prediction (micro-averaging).

.. note::

    See also :func:`sklearn.metrics.average_precision_score`,
             :func:`sklearn.metrics.recall_score`,
             :func:`sklearn.metrics.precision_score`,
             :func:`sklearn.metrics.f1_score`
"""
# %%
# In binary classification settings
# ---------------------------------
#
# Dataset and model
# .................
#
# We will use a Linear SVC classifier to differentiate two types of irises.
import numpy as np
import sklearn
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

# pylint: disable=ungrouped-imports

from mezcla import debug
from mezcla import text_utils
from mezcla.text_utils import version_to_number as version2num
debug.assertion(version2num(sklearn.__version__) >= version2num("1.0"))

X, y = load_iris(return_X_y=True)
debug.trace_expr(5, X, y)

# Add noisy features
random_state = np.random.RandomState(0)
n_samples, n_features = X.shape
X = np.concatenate([X, random_state.randn(n_samples, 200 * n_features)], axis=1)
debug.trace_expr(5, X)

# Limit to the two first classes, and split into training and test
X_train, X_test, y_train, y_test = train_test_split(
    X[y < 2], y[y < 2], test_size=0.5, random_state=random_state
)
debug.trace_expr(5, X_train, X_test, y_train, y_test)

# %%
# Linear SVC will expect each feature to have a similar range of values. Thus,
# we will first scale the data using a
# :class:`~sklearn.preprocessing.StandardScaler`.
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

classifier = make_pipeline(StandardScaler(), LinearSVC(random_state=random_state))
debug.trace_expr(5, classifier)
classifier.fit(X_train, y_train)
debug.trace_object(5, classifier)

## TODO: ???
y_score = classifier.decision_function(X_test)
debug.trace_object(5, y_score)

# %%
# Plot the Precision-Recall curve
# ...............................
#
# To plot the precision-recall curve, you should use
# :class:`~sklearn.metrics.PrecisionRecallDisplay`. Indeed, there is two
# methods available depending if you already computed the predictions of the
# classifier or not.
#
# Let's first plot the precision-recall curve without the classifier
# predictions. We use
# :func:`~sklearn.metrics.PrecisionRecallDisplay.from_estimator` that
# computes the predictions for us before plotting the curve.

## TODO
## from sklearn.metrics import PrecisionRecallDisplay

## display = PrecisionRecallDisplay.from_estimator(
##     classifier, X_test, y_test, name="LinearSVC"
## )
## _ = display.ax_.set_title("2-class Precision-Recall curve")
## debug.trace_expr(5, display, _)


## TODO: ???
from sklearn.metrics import average_precision_score
average_precision = average_precision_score(y_test, y_score)

print('Average precision-recall score: {0:0.2f}'.format(
      average_precision))

from sklearn.metrics import precision_recall_curve
from sklearn.metrics import plot_precision_recall_curve
import matplotlib.pyplot as plt

disp = plot_precision_recall_curve(classifier, X_test, y_test)
disp.ax_.set_title('2-class Precision-Recall curve: '
                   'AP={0:0.2f}'.format(average_precision))

## TODO
## # %%
## # If we already got the estimated probabilities or scores for
## # our model, then we can use
## # :func:`~sklearn.metrics.PrecisionRecallDisplay.from_predictions`.
## y_score = classifier.decision_function(X_test)
## 
## display = PrecisionRecallDisplay.from_predictions(y_test, y_score, name="LinearSVC")
## _ = display.ax_.set_title("2-class Precision-Recall curve")
## debug.trace_expr(5, display, _)


# %%
# In multi-label settings
# -----------------------
#
# The precision-recall curve does not support the multilabel setting. However,
# one can decide how to handle this case. We show such an example below.
#
# Create multi-label data, fit, and predict
# .........................................
#
# We create a multi-label dataset, to illustrate the precision-recall in
# multi-label settings.

from sklearn.preprocessing import label_binarize

# Use label_binarize to be multi-label like settings
Y = label_binarize(y, classes=[0, 1, 2])
n_classes = Y.shape[1]
debug.trace_expr(5, Y, n_classes)

# Split into training and test
X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=0.5, random_state=random_state
)
debug.trace_expr(5, X_train, X_test, Y_train, Y_test)

# %%
# We use :class:`~sklearn.multiclass.OneVsRestClassifier` for multi-label
# prediction.
from sklearn.multiclass import OneVsRestClassifier

classifier = OneVsRestClassifier(
    make_pipeline(StandardScaler(), LinearSVC(random_state=random_state))
)
classifier.fit(X_train, Y_train)
y_score = classifier.decision_function(X_test)
debug.trace_expr(5, y_score)
debug.trace_object(5, classifier)

# %%
# The average precision score in multi-label settings
# ...................................................
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score

# For each class
precision = dict()
recall = dict()
average_precision = dict()
for i in range(n_classes):
    precision[i], recall[i], _ = precision_recall_curve(Y_test[:, i], y_score[:, i])
    average_precision[i] = average_precision_score(Y_test[:, i], y_score[:, i])

# A "micro-average": quantifying score on all classes jointly
precision["micro"], recall["micro"], _ = precision_recall_curve(
    Y_test.ravel(), y_score.ravel()
)
average_precision["micro"] = average_precision_score(Y_test, y_score, average="micro")
debug.trace_expr(5, precision, recall, average_precision)



# %%
# Plot the micro-averaged Precision-Recall curve
# ..............................................

## TODO
## display = PrecisionRecallDisplay(
##     recall=recall["micro"],
##     precision=precision["micro"],
##     average_precision=average_precision["micro"],
## )
## display.plot()
## _ = display.ax_.set_title("Micro-averaged over all classes")
## debug.trace_expr(5, display, _)

plt.figure()
plt.step(recall['micro'], precision['micro'], where='post')

plt.xlabel('Recall')
plt.ylabel('Precision')
plt.ylim([0.0, 1.05])
plt.xlim([0.0, 1.0])
plt.title(
    'Average precision score, micro-averaged over all classes: AP={0:0.2f}'
    .format(average_precision["micro"]))
debug.trace_object(5, plt)

# %%
# Plot Precision-Recall curve for each class and iso-f1 curves
# ............................................................
import matplotlib.pyplot as plt
from itertools import cycle

# setup plot details
colors = cycle(["navy", "turquoise", "darkorange", "cornflowerblue", "teal"])

_, ax = plt.subplots(figsize=(7, 8))
debug.trace_expr(5, colors, _, ax)

f_scores = np.linspace(0.2, 0.8, num=4)
lines, labels = [], []
for f_score in f_scores:
    x = np.linspace(0.01, 1)
    y = f_score * x / (2 * x - f_score)
    (l,) = plt.plot(x[y >= 0], y[y >= 0], color="gray", alpha=0.2)
    plt.annotate("f1={0:0.1f}".format(f_score), xy=(0.9, y[45] + 0.02))
    debug.trace_expr(6, x, y, l, plt)
debug.trace_expr(5, lines, labels)

## TODO
## display = PrecisionRecallDisplay(
##     recall=recall["micro"],
##     precision=precision["micro"],
##     average_precision=average_precision["micro"],
## )
## display.plot(ax=ax, name="Micro-average precision-recall", color="gold")
## debug.trace_object(5, display)
## 
## for i, color in zip(range(n_classes), colors):
##     display = PrecisionRecallDisplay(
##         recall=recall[i],
##         precision=precision[i],
##         average_precision=average_precision[i],
##     )
##     display.plot(ax=ax, name=f"Precision-recall for class {i}", color=color)
##     debug.trace_object(5, display)
## 
## # add the legend for the iso-f1 curves
## handles, labels = display.ax_.get_legend_handles_labels()
## debug.trace_expr(handles, labels)
## handles.extend([l])
## labels.extend(["iso-f1 curves"])
## # set the legend and the axes
## ax.set_xlim([0.0, 1.0])
## ax.set_ylim([0.0, 1.05])
## ax.legend(handles=handles, labels=labels, loc="best")
## ax.set_title("Extension of Precision-Recall curve to multi-class")
## debug.trace_object(5, ax)

lines.append(l)
labels.append('iso-f1 curves')
l, = plt.plot(recall["micro"], precision["micro"], color='gold', lw=2)
lines.append(l)
labels.append('micro-average Precision-recall (area = {0:0.2f})'
              ''.format(average_precision["micro"]))

for i, color in zip(range(n_classes), colors):
    l, = plt.plot(recall[i], precision[i], color=color, lw=2)
    lines.append(l)
    labels.append('Precision-recall for class {0} (area = {1:0.2f})'
                  ''.format(i, average_precision[i]))

fig = plt.gcf()
fig.subplots_adjust(bottom=0.25)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Extension of Precision-Recall curve to multi-class')
plt.legend(lines, labels, loc=(0, -.38), prop=dict(size=14))


plt.show()
