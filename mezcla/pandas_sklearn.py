#! /usr/bin/env python
#
# Runs training data through a variety of supervised classifiers, as an
# illustration on how to use pandas and sklearn to do machine learning.
#
# This was initially for the Iris dataset, based on following:
#    https://medium.com/codebagng/basic-analysis-of-the-iris-data-set-using-python-2995618a6342.
#
# Notes:
# - Environment variables:
#   DATA_FILE  FIELD_SEP  SCORING_METRIC  SEED  SKIP_DEVEL  SKIP_PLOTS  USE_DATAFRAME  VALIDATE_ALL  VALIDATION_CLASSIFIER  VERBOSE 
# - Currently only supports cross-validation (i.e., partitions of single datafile).
# - This partititions training data into development and validation sets.
# - Also does k-fold cross validation over development data split using 1/k-th as test.
# - That is, the training data is partitioned twice.
# - As an expediency to disable validation, epsilon is used for validation percent (e.g., 1e-6), because sklearn doesn't allow the percent to be specified as zero.
#
# TODO:
# - Add exception handling throughout.
# - Replace iris.csv with non-trivial ML data (e.g., to serve in benchmarking).
# - Make sure validation used in same tense as standard practice.
# - Rename (e.g., pandas_sklearn.py => evaluate_classifiers.py).
# 

"""Illustrates sklearn classification over data with panda csv-based import"""

## TEST: allow for global logging.basicConfig initialization
from tomas_misc import debug            # pylint: disable=ungrouped-imports

# Standard packages
import sys

# Installed pckages
import numpy as np
import pandas as pd
from pandas.plotting import scatter_matrix
from sklearn import model_selection
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import precision_recall_curve
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.svm import SVC

# Local packages
## OLD (put above for proper logging initialization):
## from tomas_misc import debug
from tomas_misc import data_utils as du
from tomas_misc import glue_helpers as gh
from tomas_misc import system
from tomas_misc import text_utils
from tomas_misc.system import round_num, getenv_bool, getenv_int, getenv_number, getenv_text, getenv_value
from tomas_misc.text_utils import getenv_ints

#................................................................................
# Constants (e.g., environment-based options)

VERBOSE = getenv_bool("VERBOSE", False)
DATA_FILE = getenv_text("DATA_FILE", "tests/iris.csv")
FIELD_SEP = getenv_text("FIELD_SEP", ",",
                        description="Field separator (delimiter)")
SKIP_DATAFRAME = getenv_bool("SKIP_DATAFRAME", False)
USE_DATAFRAME = getenv_bool("USE_DATAFRAME", not SKIP_DATAFRAME)
IGNORE_FIELDS = text_utils.extract_string_list(getenv_text("IGNORE_FIELDS", ""))
INCLUDE_PLOTS = getenv_bool("INCLUDE_PLOTS", False)
DATASET_PLOTS = getenv_bool("DATASET_PLOTS", INCLUDE_PLOTS,
                            "Include plots summarizing dataset")
SKIP_PLOTS = getenv_bool("SKIP_PLOTS", not INCLUDE_PLOTS)
OUTPUT_CSV = getenv_bool("OUTPUT_CSV", False)
SKIP_VALIDATION = getenv_bool("SKIP_VALIDATION", False)
KERAS_CLASSIFIER = "Keras"
KNN_CLASSIFIER = "KNN"
XGB_CLASSIFIER = "XGB"
DEFAULT_CLASSIFIER = getenv_text("CLASSIFIER", "LR")
DEFAULT_DEVEL_CLASSIFIER = DEFAULT_CLASSIFIER if (not SKIP_VALIDATION) else None
DEVEL_CLASSIFIER = getenv_text("DEVEL_CLASSIFIER", DEFAULT_DEVEL_CLASSIFIER)
INCLUDE_ALL = getenv_bool("INCLUDE_ALL", False,
                          description="Include all classifiers (for devel and validation)")
INCLUDE_ALL_DEVEL = getenv_bool("INCLUDE_ALL_DEVEL", INCLUDE_ALL,
                                description="Evaluate all classifiers over development test data")
INCLUDE_MISC_CLASSIFIERS = getenv_bool("INCLUDE_MISC", INCLUDE_ALL,
                                       description="Include miscellaneous classifiers like CART")
EPSILON = 1.0e-6
DEFAULT_VALIDATION_PCT = 0.20 if (not SKIP_VALIDATION) else EPSILON
VALIDATION_PCT = getenv_number("VALIDATION_PCT", DEFAULT_VALIDATION_PCT)
VALIDATE_ALL = getenv_bool("VALIDATE_ALL", INCLUDE_ALL,
                           description="Evaluate all classifiers over validation over data")
DEFAULT_VALIDATION_CLASSIFIER = DEFAULT_CLASSIFIER if (not SKIP_VALIDATION) else None
VALIDATION_CLASSIFIER = getenv_text("VALIDATION_CLASSIFIER", DEFAULT_VALIDATION_CLASSIFIER)
## TEST: debug.assertion(False)
SKIP_DEVEL = getenv_bool("SKIP_DEVEL", False)
TEST_PCT = getenv_number("TEST_PCT", 0.10)
SEED = getenv_bool("SEED", 7919)
SCORING_METRIC = getenv_text("SCORING_METRIC", "accuracy")
CLASS_VAR = getenv_text("CLASS_VAR", "")
## TEST: 
## SKIP_XGB = getenv_bool("SKIP_XGB", False)
## USE_XGB = getenv_bool("USE_XGB", not SKIP_XGB)
DEFAULT_INCLUDE_XGB = XGB_CLASSIFIER in [DEFAULT_DEVEL_CLASSIFIER, DEFAULT_VALIDATION_CLASSIFIER]
INCLUDE_XGB = getenv_bool("INCLUDE_XGB", DEFAULT_INCLUDE_XGB or INCLUDE_ALL)
## BAD: XGB_BOOSTER = getenv_text("XGB_BOOSTER", None)
XGB_BOOSTER = getenv_value("XGB_BOOSTER", None)
XGB_SKIP_GPU = getenv_bool("XGB_SKIP_GPU", False)
XGB_USE_GPU = (not XGB_SKIP_GPU)
# TODO: standardize with respect to text_categorizer.py
XGB_USE_GPUS = XGB_USE_GPU
XGB_VERBOSITY = getenv_int("XGB_VERBOSITY", 0, "Degree of verbosity from 0 to 3")
#
COERCE_FLOAT = getenv_bool("COERCE_FLOAT", False,
                           "Coerce all data values to floating point, excluding class column")
ENCODE_CLASSES = getenv_bool("ENCODE_CLASSES", False,
                             "Encode classes using enumeration")
NUMERIC_CLASSES = getenv_bool("NUMERIC_CLASSES", False,
                              "Encode classes as number")
#
DEFAULT_INCLUDE_KERAS_CLASSIFIER = KERAS_CLASSIFIER in [DEFAULT_DEVEL_CLASSIFIER, DEFAULT_VALIDATION_CLASSIFIER]
INCLUDE_KERAS = getenv_bool("INCLUDE_KERAS", DEFAULT_INCLUDE_KERAS_CLASSIFIER or INCLUDE_ALL)
SKIP_KERAS = getenv_bool("SKIP_KERAS", not INCLUDE_KERAS)
HIDDEN_UNIT_VALUES = getenv_ints("HIDDEN_UNIT_VALUES", "50, 100, 50")
NUM_EPOCHS = getenv_int("NUM_EPOCHS", 100)
BATCH_SIZE = getenv_int("BATCH_SIZE", None)

GPU_DEVICE = system.getenv_text("GPU_DEVICE", "",
                                "Device number for GPU (e.g., shown under nvidia-smi)")
SHOW_ABLATION = getenv_bool("SHOW_ABLATION", False,
                            "Show ablation plot for accuracy")
PRECISION_RECALL = getenv_bool("PRECISION_RECALL", False,
                               "Plot precision/recall curve")

#...............................................................................
# Optional packahes

if INCLUDE_PLOTS:
    # pylint: disable=import-outside-toplevel, import-error
    import matplotlib.pyplot as plt

if INCLUDE_XGB:
    # pylint: disable=import-outside-toplevel, import-error
    import xgboost as xgb
    if getenv_text("USE_XGB"):
        system.print_stderr("Warning: deprecated option USE_XGB")
## Mote: Following added for tracking down segmentation fault
## DEBUG: print("after xgboost import")
    
if INCLUDE_KERAS:
    # pylint: disable=import-outside-toplevel, ungrouped-imports, import-error
    from tomas_misc.keras_param_search import MyKerasClassifier, create_keras_model
## DEBUG: print("after keras_param_search import")

if (INCLUDE_ALL and (not (INCLUDE_XGB or INCLUDE_KERAS))):
    debug.trace(4, "Warning: Need to specify INCLUDE_(XGB/KERAS) separately")

#...............................................................................
# Utility functions

def create_feature_mapping(label_values):
    """Return hash mapping elements from LABEL_VALUES into integers"""
    # EX: create_feature_mapping(['c', 'b, 'b', 'a']) => {'c':0, 'b':1, 'a':2}
    in_label_values = label_values
    if not isinstance(label_values, list):
        label_values = list(label_values)
    id_hash = {}
    for item in label_values:
        if (item not in id_hash):
            id_hash[item] = len(id_hash)
    debug.trace_fmtd(7, "create_feature_mapping({l}) => {h}", l=in_label_values, h=id_hash)
    return id_hash

#...............................................................................
# Main processing

def main():
    """Entry point for script"""
    debug.trace(4, "main()")

    # Misc. initialization
    system.PRECISION = 3

    # TODO: convert into using main.py's Main class
    data_file = None
    args = system.get_args()
    if ((len(args) > 1) and (args[1] == "--help")):
        script = gh.basename(args[0])
        system.print_stderr("Usage: {scr} [--help] [data-file]", scr=script)
        system.print_stderr("")
        system.print_stderr("where data-file is in CSV format")
        system.print_stderr("")
        ## TODO: show_details = VERBOSE or debug.debugging()
        if debug.debugging(2):
            ## TODO: add legend
            system.print_stderr("\t" + system.formatted_environment_option_descriptions(include_all=True))
        system.exit("")
    if ((len(args) > 1) and (not args[1].startswith("-"))):
        data_file = args[1]
    debug.trace(4, f"data_file={data_file}")
    if data_file is None:
        data_file = gh.resolve_path(DATA_FILE)

    # Read the data
    ##
    ## BAD
    ## extra_read_args = {}
    ## if COERCE_FLOAT:
    ##     extra_read_args['dtype'] = np.float64
    ## dataset = pandas.read_csv(DATA_FILE, sep=FIELD_SEP, comment="#", **extra_read_args)
    ##
    try:
        dataset = du.read_csv(data_file, sep=FIELD_SEP, comment="#")
    except:
        system.print_exception_info("du.read_csv")
        debug.trace(3, "Using pandas read_csv directly as fallback")
        dataset = pd.read_csv(data_file, sep=FIELD_SEP)

    # Reorder columns so classication variable last
    if (CLASS_VAR and (CLASS_VAR != dataset.columns[-1])):
        debug.trace_fmtd(4, "Re-arranging columns")
        columns = system.difference(list(dataset.columns), CLASS_VAR)
        columns.append(CLASS_VAR)
        dataset = dataset[columns]

    # Show features proper and classificaiton variable
    feature_names = list(dataset.columns[0:-1])
    class_var = dataset.columns[-1]
    debug.trace_fmtd(4, "class_var={c} features:{f}",
                     f=feature_names, c=class_var)
    debug.trace_object(7, dataset, "dataset")

    # Optionally remove specified fields from data
    if IGNORE_FIELDS:
        debug.assertion(not system.difference(IGNORE_FIELDS, feature_names))
        dataset = dataset.drop(IGNORE_FIELDS, axis=1)
        feature_names = list(dataset.columns[0:-1])

    # Show samples from the data along with summary statistics and other information
    try:
        # Show first 10 rows
        print("Sample of data set (head, tail, random):")
        print(dataset.head())
        # SHow last 10 row
        print(dataset.tail())
        # Show 5 random rows
        print(dataset.sample(5))
        # Show a statistical summary about the dataset.
        print("statistical summary:")
        print(dataset.describe())
        # Show how many null entries are in the dataset.
        print("Null count:")
        print(dataset.isnull().sum())
    except:
        debug.trace_fmtd(2, "Error: Problem during dataset illustration, etc.: {exc}",
                         exc=sys.exc_info())
        debug.raise_exception(6)
    
    # Optionally show some plot
    ## OLD: if (not SKIP_PLOTS):
    if DATASET_PLOTS:
            
        # box and whisker plots
        dataset.plot(kind="box", subplots=True, layout=(2, 2), sharex=False, sharey=False)
        plt.show()
        
        # histograms
        dataset.hist()
        plt.show()
        
        # scatter plot matrix
        scatter_matrix(dataset)
        plt.show()

    # Split-out validation dataset
    if USE_DATAFRAME:
        features_indices = dataset.columns
        num_features = len(features_indices) - 1
        X = dataset[features_indices[0:num_features]]
        y = dataset[features_indices[num_features]]
        if COERCE_FLOAT:
            X = X.astype(np.float64)
        if NUMERIC_CLASSES:
            y = y.astype(np.float64)
    else:
        array = dataset.values
        debug.trace_object(7, array, "array")
        num_features = (array.shape[1] - 1)
        X = array[:, 0:num_features]
        y = array[:, num_features]
        # TODO: COERCE_FLOAT
        # TODO: NUMERIC_CLASSES
    if ENCODE_CLASSES:
        y_encodings = create_feature_mapping(y)
        y = np.array([y_encodings[v] for v in y])
        # TODO: COERCE_FLOAT
    debug.trace_fmtd(7, "X={X}\ny={y}", X=X, y=y)
    if OUTPUT_CSV:
        # TODO: drop pandas index column (first one; no header)
        debug.assertion(USE_DATAFRAME)
        debug.assertion(not (COERCE_FLOAT or NUMERIC_CLASSES or ENCODE_CLASSES))
        basename = system.remove_extension(data_file)
        X.to_csv(basename + "-X.csv.list", sep=FIELD_SEP, index=False)
        y.to_csv(basename + "-y.csv.list", sep=FIELD_SEP, index=False)
        debug.assertion(system.file_exists(basename + "-X.csv.list"))
    X_train, X_validation, y_train, y_validation = model_selection.train_test_split(X, y, test_size=VALIDATION_PCT, random_state=SEED)
    ## TODO:
    debug.trace_fmtd(6, "X_train={xt}\nX_valid={xv}\ny_train={yt}\ny_valid={yv}", xt=X_train, xv=X_validation, yt=y_train, yv=y_validation)
    
    # Test options and evaluation metric
    ## NOTE: precision and recall currently not supported (see below)
    y_values = list(y.values) if isinstance(y, pd.Series) else y
    num_classes = len(create_feature_mapping(y_values))
    is_binary = (num_classes == 2)
    
    # Spot check algorithms
    # TODO: Add legend for non-standard abbreviations.
    models = []

    # TODO: drop n_gpus (thanks a lot, XGBoost: WTH?!)
    ## TEST: XGB_UPDATER = 'grow_gpu' if XGB_NUM_GPUS else ''
    ## TEST: models.append((XGB_CLASSIFIER, xgb.XGBClassifier(booster=XGB_BOOSTER, n_gpus=XGB_NUM_GPUS, updater=XGB_UPDATER)))
    if INCLUDE_XGB:
        ## OLD
        ## XGB_TREE_METHOD = 'gpu_hist' if XGB_USE_GPU else None
        ## models.append((XGB_CLASSIFIER, xgb.XGBClassifier(booster=XGB_BOOSTER, tree_method=XGB_TREE_METHOD)))
        ## TODO: misc_xgb_params = {}
        misc_xgb_params = {'booster': XGB_BOOSTER, 'verbosity': XGB_VERBOSITY}
        if XGB_USE_GPUS:
            misc_xgb_params.update({'tree_method': 'gpu_hist'})
            misc_xgb_params.update({'predictor': 'gpu_predictor'})
        if GPU_DEVICE:
            misc_xgb_params.update({'gpu_id': GPU_DEVICE})
        debug.trace_fmt(4, 'misc_xgb_params={m}', m=misc_xgb_params)
        models.append((XGB_CLASSIFIER, xgb.XGBClassifier(**misc_xgb_params)))
    if INCLUDE_KERAS:
        create_model_fn = lambda: create_keras_model(num_input_features=num_features,
                                                     num_classes=num_classes)
        models.append((KERAS_CLASSIFIER,
                       MyKerasClassifier(hidden_units=HIDDEN_UNIT_VALUES, epochs=NUM_EPOCHS,
                                         batch_size=BATCH_SIZE, build_fn=create_model_fn)))
    models.append(("LR", LogisticRegression()))
    if INCLUDE_MISC_CLASSIFIERS:
        models.append(("LDA", LinearDiscriminantAnalysis()))
        models.append((KNN_CLASSIFIER, KNeighborsClassifier()))
        models.append(("CART", DecisionTreeClassifier()))        #  Classification and Regression Trees
        models.append(("GNB", GaussianNB()))
        models.append(("MNB", MultinomialNB()))
        models.append(("SVM", SVC()))

    # Evaluate each model in turn.
    # TODO: show precision, recall, F1, as well as accuracy
    # Sample results:
    # name  acc    stdev
    # LR    0.967  0.041
    # LDA   0.975  0.038
    # KNN   0.983  0.033
    # CART  0.975  0.038
    # GNB   0.975  0.053
    # SVM   0.982  0.025
    #    
    summaries = []
    if (not SKIP_DEVEL):
        print("Sample development test set results using scoring method '{sm}'".format(sm=SCORING_METRIC))
        ## TODO: average = "micro" if (not is_binary) else None
        for name, model in models:
            if ((name != DEVEL_CLASSIFIER) and (not INCLUDE_ALL_DEVEL)):
                debug.trace_fmt(5, "Skipping classifier {n} (not devel and not include all)", n=name)
                continue
            kfold = model_selection.KFold(n_splits=10, shuffle=True, random_state=SEED)
            ## TODO: cv_results = model_selection.cross_val_score(model, X_train, y_train, cv=kfold, scoring=SCORING_METRIC, average=average)
            ## TODO: get this to work when SCORING_METRIC is not accuracy (which leads to not supported error for multicalss data)
            ## (e.g., add environment variable so that sklearn uses micro or macro average
            try:
                cv_results = model_selection.cross_val_score(model, X_train, y_train, cv=kfold, scoring=SCORING_METRIC)
                summaries.append("{n}\t{avg}\t{std}".format(n=name, avg=system.round_num(cv_results.mean()), std=system.round_num(cv_results.std())))

                # Show confusion matrix for sample split of training data
                if VERBOSE:
                    X_devel, X_test, y_devel, y_test = model_selection.train_test_split(X_train, y_train, test_size=TEST_PCT, random_state=SEED)
                    model.fit(X_devel, y_devel)
                    debug.trace_fmtd(4, "devel data score: {s}", s=model.score(X_devel, y_devel))
                    model.fit(X_test, y_test)
                    debug.trace_fmtd(4, "test data score: {s}", s=model.score(X_test, y_test))
                    predictions = model.predict(X_test)
                    print("Development test set confusion matrix:")
                    print(confusion_matrix(y_test, predictions))
                    print("Development test classification report:")
                    print(classification_report(y_test, predictions))

                    # Model-specific information (e.g., feature importance)
                    if (name == XGB_CLASSIFIER):
                        print("Feature importance:")
                        ## print(model.get_score())
                        print(sorted(zip(feature_names, model.feature_importances_),
                                     ## TODO: key=(lambda name, score: score),
                                     key=lambda name_score: name_score[1],
                                     reverse=True))
                                          
            except:
                debug.trace_fmtd(2, "Error: Problem during training evaluation: {exc}",
                                 exc=sys.exc_info())
                summaries.append("Exception for " + name)
                debug.raise_exception(6)
        print("Cross validation results over development test set")
        print("name\tacc\tstdev")
        print("\n".join(summaries))
    
    # Make predictions on validation dataset
    # Sample output:
    # Confusion matrix:
    # [[ 7  0 0]
    #  [ 0 11 1]
    #  [ 0  2 9]]
    # classification report:
    #              precision recall  f1  support
    # Iris-setosa     1.00   1.00  1.00  7
    # Iris-versicolor 0.85   0.92  0.88  12
    # Iris-virginica  0.90   0.82  0.86  11
    # avg / total     0.90   0.90  0.90  30
    # TODO: rework so that loop bypassed if no validation set
    average = "micro" if (not is_binary) else "binary"
    num_run = 0
    for name, model in models:
        if ((name != VALIDATION_CLASSIFIER) and (not VALIDATE_ALL)):
            debug.trace_fmt(5, "Skipping classifier {n} (not validation and not include all)", n=name)
            continue
        try:
            ## DEBUG: debug.trace(5, f"X/Y_train types: {[type(v) for v in [X_train, y_train]]}")
            ## DEBUG: debug.trace(5, f"X/Y_train head: {[v.head() for v in [X_train, y_train]]}")
            if VALIDATE_ALL:
                print("." * 80)
            print("Results over validation data for {n}:".format(n=name))
            num_run += 1
            model.fit(X_train, y_train)
            debug.trace_fmtd(4, "training data score: {s}", s=model.score(X_train, y_train))
            if debug.debugging(4):
                print("training confusion matrix:")
                training_predictions = model.predict(X_train)
                print(confusion_matrix(y_train, training_predictions))

            predictions = model.predict(X_validation)
            print("validation confusion matrix:")
            print(confusion_matrix(y_validation, predictions))
            ## TODO: drop accurracy ... F1 (provide in report)
            if VERBOSE:
                print("accuracy:", end=" ")
                print(round_num(accuracy_score(y_validation, predictions)))
                print("precision:", end=" ")
                print(round_num(precision_score(y_validation, predictions, average=average)))
                print("recall:", end=" ")
                print(round_num(recall_score(y_validation, predictions, average=average)))
                print("F1:", end=" ")
                print(round_num(f1_score(y_validation, predictions, average=average)))
            else:
                debug.trace_fmtd(4, "Use VERBOSE=1 for validation score breakdown")
            print("classification report:")
            print(classification_report(y_validation, predictions))
            if PRECISION_RECALL:
                show_precision_recall(name, model, X_train, y_train, X_validation, y_validation)
            if SHOW_ABLATION:
                show_ablation(name, model, X_train, y_train, X_validation, y_validation)
        except:
            ## OLD:
            ## debug.trace_fmtd(2, "Error: Problem during validation evaluation: {exc}",
            ##                  exc=sys.exc_info())
            debug.trace_exception(2, "validation evaluation")
            debug.raise_exception(6)
    if ((num_run == 0) and VALIDATION_CLASSIFIER):
        system.print_stderr("Error: Validation classifier '{clf}' not supported", clf=VALIDATION_CLASSIFIER)

#------------------------------------------------------------------------

def show_ablation(name, model, X_train, y_train, X_validation, y_validation):
    """Show ablation result for X_TRAIN, Y_TRAIN, X_VALIDATION, Y_VALIDATION"""
    # Note: plots the data unless SKIP_PLOTS
    debug.trace(4, f"show_ablation{tuple([name, model, X_train, y_train, X_validation, y_validation])}")
    num_training = len(X_train)
    accuracies = []
    for size in range(num_training):
        try:
            model.fit(X_train[:size], y_train[:size])
            predictions = model.predict(X_validation)
            accuracy = accuracy_score(y_validation, predictions)
            accuracies.append(accuracy)
            debug.trace_expr(5, size, accuracy)
        except:
            system.print_exception_info("show_ablation")
    if (not SKIP_PLOTS):
        plt.plot(accuracies)
        plt.show()
    else:
        print("ablation accuracy:")
        print(accuracies)  
    debug.trace(5, "end show_ablation")
    return

def show_precision_recall(name, model, X_train, y_train, X_validation, y_validation):
    """Show precision/recall results for X_TRAIN, Y_TRAIN, X_VALIDATION, Y_VALIDATION"""
    # based on https://www.statology.org/precision-recall-curve-python/
    precision = recall = thresholds = []
    debug.trace(4, f"show_precision_recall{tuple([name, model, X_train, y_train, X_validation, y_validation])}")
    try:
        model.fit(X_train, y_train)
        y_scores = model.predict_proba(X_validation)[:, 1]
        precision, recall, thresholds = precision_recall_curve(y_validation, y_scores)
    except:
        system.print_exception_info("show_precision_recall")
    if (not SKIP_PLOTS):
        plt.plot(recall, precision)
        ## TODO: plt.yticks(thresholds)
        plt.xlabel("recall")
        plt.ylabel("precision")
        plt.title("precision recall curve")
        plt.show()
    else:
        ## TODO:
        ## print("precision, recall:")
        ## print(list(zip(precision, recall)))
        ## print(thresholds)
        print("precision:\n\t{vals!r}".format(vals=precision))
        print("recall:\n\t{vals!r}".format(vals=recall))
        print("thresholds:\n\t{vals!r}".format(vals=thresholds))
    debug.trace(5, "end show_precision_recall")        
    return
    
#------------------------------------------------------------------------

if __name__ == "__main__":
    main()
