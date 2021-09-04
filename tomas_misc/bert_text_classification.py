#! /usr/bin/env python
# 
# Text categorized based on BERT model. This allows for multiclass categorization. The
# input is a tabbed delimited file of the format:
#     category<TAB>token1<DELIM>token2<DELIM>...tokenN
# where DELIM is either whitespace and/or punctuation (e.g., ' ' or '. ' or ' $').
# The tokens are alphanumeric as well as including dashes and underscores.
#
# Notes:
# - This is based on following online article:
#       https://analyticsindiamag.com/step-by-step-guide-to-implement-multi-class-classification-with-bert-tensorflow
# - Godawful code organization (e.g., double embedded functions).
# - Default text categories:
#      Politics: 0
#      Technology: 1
#      Entertainment: 2
#      Business: 3
#
# - Data Preprocessing
#
#   The BERT model accepts only a specific type of input and the datasets are usually structured to have have the following four features:
#      guid : A unique id that represents an observation.
#      text_a : The text we need to classify into given categories
#      text_b: It is used when we're training a model to understand the relationship between sentences and it does not apply for classification problems.
#      label: It consists of the labels or classes or categories that a given text belongs to.
#
#  In our dataset we have text_a and label. The code will create objects for each of the above mentioned features for all the records in our dataset using the InputExample class provided in the BERT library.
#
# - To cache the tensorflow hub version of the BERT data, uses following steps,
#   based on https://medium.com/@xianbao.qian/how-to-run-tf-hub-locally-without-internet-connection-4506b850a915:
#      local_hub_dir = /tmp/tf-hub
#      mkdir local_hub_dir
#      os.environ["TFHUB_CACHE_DIR"] = "/tmp/tf-hub"
#      cache_subdir = hashlib.sha1(BERT_MODEL_HUB.encode("utf8")).hexdigest()
#      tf_hub_url = BERT_MODEL_HUB.replace("https://tfhub.dev/", "https://storage.googleapis.com/tfhub-modules/")
#      curl tf_hub_url /tmp/
#      cd local_hub_dir
#      tar xvfz /tmp/1.tar.gz
#      move * cache_subdir
#  For hub instance "https://tfhub.dev/google/bert_uncased_L-12_H-768_A-12/1",
#  this downloads https://storage.googleapis.com/tfhub-modules/bert_uncased_L-12_H-768_A-12/1.tr.gz" and places the tar contents in /tmp/
#
#--------------------------------------------------------------------------------
# TODO:
# - Determine the depencies between the versions of TensorFlow and BERT. This
# doesn't work with TensorFlow 2.0 and BERT from 2018.
#

"""Run text categorization over input file (or Predict the News Category Hackathon)"""

## TODO: drop re import if not needed
from datetime import datetime
import os
import pandas as pd
import re

## OLD: from google.colab import drive

import tensorflow as tf
import tensorflow_hub as hub
from sklearn.model_selection import train_test_split

#Importing BERT modules
import bert
from bert import run_classifier
from bert import optimization
from bert import tokenization

from main import Main
import debug
import system
import glue_helpers as gh

# Get training data
# TODO: replace with file specified on input
## OLD: drive.mount("/GD")

# Show TensorFlow info
# note: 1.15.0 and 0.7.0 for blog example
print("tensorflow version : ", tf.__version__)
print("tensorflow_hub version : ", hub.__version__)

# Set the output directory for saving model file
## OUTPUT_DIR = '/GD/My Drive/Colab Notebooks/BERT/bert_news_category'
USER = system.getenv_text("USER", "user")
BASE_DIR = system.getenv_text("BASE_DIR", ".")
TRAINING_FILE = "Data_Train.xlsx"
TESTING_FILE = "Data_Test.xlsx"
TYPICAL_INPUT_DIR = system.form_path(USER, "data", "hackathon-news-prediction")
DEFAULT_INPUT_DIR = "." if system.file_exists(TRAINING_FILE) else TYPICAL_INPUT_DIR
INPUT_DIR = system.getenv_text("INPUT_DIR", DEFAULT_INPUT_DIR)
TRAINING_PATH = system.form_path(INPUT_DIR, TRAINING_FILE)
TESTING_PATH = system.form_path(INPUT_DIR, TESTING_FILE)
OUTPUT_DIR = system.getenv_text("OUTPUT_DIR",
                                system.form_path(INPUT_DIR, "output"))
SHOW_PLOTS = system.getenv_bool("SHOW_PLOTS", False)
TFHUB_CACHE_DIR = system.getenv_text("TFHUB_CACHE_DIR")
if TFHUB_CACHE_DIR:
    debug.trace_fmt(3, "Using local TensorFlow Hub cache: {c}", c=TFHUB_CACHE_DIR)

## #@markdown Whether or not to clear/delete the directory and create a new oneu
## DO_DELETE = False #@param {type:"boolean"}
DO_DELETE = system.getenv_bool("DO_DELETE", False)

# Do sanity check on input files
debug.assertion(system.non_empty_file(TRAINING_PATH))
debug.assertion(system.non_empty_file(TESTING_PATH))

# Delete previous run if desired. The (re-)create the output directory if needed.

debug.assertion(system.is_directory(INPUT_DIR))
if DO_DELETE:
    try:
        ## tf.gfile.DeleteRecursively(OUTPUT_DIR)
        gh.issue("/bin/rm --verbose --recursive {od}", od=OUTPUT_DIR)
    except:
        ## pass
        system.print_stderr("Problem deleting dir: {od}", od=OUTPUT_DIR)
if not system.is_directory(OUTPUT_DIR):
    system.create_directory(OUTPUT_DIR)

## tf.gfile.MakeDirs(OUTPUT_DIR)
print('***** Model output directory: {} *****'.format(OUTPUT_DIR))
    
## TODO: Constants for switches omitting leading dashes (e.g., DEBUG_MODE = "debug-mode")
## Note: Run following in Emacs to interactively replace TODO_ARGn with option label
##    M-: (query-replace-regexp "todo\\([-_]\\)argn" "arg\\1name")
## where M-: is the emacs keystroke short-cut for eval-expression.
## TODO_ARG1 = False
## TODO_ARG2 = "TODO-arg2"
## TODO_FILENAME = "TODO-filename"

class Script(Main):
    """Input processing class"""
    # TODO: -or-: """Adhoc script class (e.g., no I/O loop, just run calls)"""
    BERT_MODEL_HUB = None
    # This is a path to an uncased (all lowercase) version of BERT
    BERT_MODEL_HUB = "https://tfhub.dev/google/bert_uncased_L-12_H-768_A-12/1"
    MAX_SEQ_LENGTH = 128         # Sequences have at most 128 tokens.
    # These hyperparameters are copied from this colab notebook (https://colab.sandbox.google.com/github/tensorflow/tpu/blob/master/tools/colab/bert_finetuning_with_cloud_tpus.ipynb)
    BATCH_SIZE = 32
    LEARNING_RATE = 2e-5
    NUM_TRAIN_EPOCHS = 3.0
    # Warmup is a period of time where the learning rate is small and gradually increases--usually helps training.
    WARMUP_PROPORTION = 0.1
    # Model configs
    SAVE_CHECKPOINTS_STEPS = 300
    SAVE_SUMMARY_STEPS = 100

    DATA_COLUMN = 'STORY'
    LABEL_COLUMN = 'SECTION'
    # The list containing all the classes (train['SECTION'].unique())
    LABEL_LIST = [0, 1, 2, 3]

    # TODO: add class constructor
    ## def __init__(self, *args, **kwargs):
    ##     debug.trace_fmtd(5, "Script.__init__({a}): keywords={kw}; self={s}",
    ##                      a=",".join(args), kw=kwargs, s=self)
    ##     super(Script, self).__init__(*args, **kwargs)
    
    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(5, "Script.setup(): self={s}", s=self)
        ## TODO:
        ## self.TODO_arg1 = self.get_parsed_option(TODO_ARG1, self.TODO_arg1)
        ## self.TODO_arg2 = self.get_parsed_option(TODO_ARG2, self.TODO_arg2)
        # TODO: self.TODO_filename = self.get_parsed_argument(TODO_FILENAME)
        debug.trace_object(5, self, label="Script instance")

    def create_tokenizer_from_hub_module(self):
        """Get the vocab file and casing info from the Hub module."""
        with tf.Graph().as_default():
            bert_module = hub.Module(self.BERT_MODEL_HUB)
            tokenization_info = bert_module(signature="tokenization_info", as_dict=True)
            with tf.Session() as sess:
                vocab_file, do_lower_case = sess.run(
                    [tokenization_info["vocab_file"],
                     tokenization_info["do_lower_case"]])
                
        return bert.tokenization.FullTokenizer(
            vocab_file=vocab_file, do_lower_case=do_lower_case)

    def create_model(self, is_predicting, input_ids, input_mask, segment_ids,
                     labels, num_labels):
        """Load the BERT model for fine-tuning."""
        bert_module = hub.Module(
            self.BERT_MODEL_HUB,
            trainable=True)
        bert_inputs = dict(
            input_ids=input_ids,
            input_mask=input_mask,
            segment_ids=segment_ids)
        bert_outputs = bert_module(
            inputs=bert_inputs,
            signature="tokens",
            as_dict=True)
    
        # Use "pooled_output" for classification tasks on an entire sentence.
        # Use "sequence_outputs" for token-level output.
        output_layer = bert_outputs["pooled_output"]
        hidden_size = output_layer.shape[-1].value
      
        # Create our own layer to tune for politeness data.
        # TODO: Make this optional (probably specific to Hackathon corpus genre)
        output_weights = tf.get_variable(
            "output_weights", [num_labels, hidden_size],
            initializer=tf.truncated_normal_initializer(stddev=0.02))
        output_bias = tf.get_variable(
            "output_bias", [num_labels], initializer=tf.zeros_initializer())
      
        with tf.variable_scope("loss"):
      
            # Dropout helps prevent overfitting
            output_layer = tf.nn.dropout(output_layer, keep_prob=0.9)
      
            logits = tf.matmul(output_layer, output_weights, transpose_b=True)
            logits = tf.nn.bias_add(logits, output_bias)
            log_probs = tf.nn.log_softmax(logits, axis=-1)
      
            # Convert labels into one-hot encoding
            one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)
      
            predicted_labels = tf.squeeze(tf.argmax(log_probs, axis=-1, output_type=tf.int32))
  
            # If predicting, return predicted labels and the probabiltiies.
            if is_predicting:
                return (predicted_labels, log_probs)
      
            # If in train/eval, compute loss between predicted and actual label
            # Note: returns loss, predicted labels, and the log of the label probs.
            per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
            loss = tf.reduce_mean(per_example_loss)
            return (loss, predicted_labels, log_probs)

    # model_fn_builder actually creates our model function
    # using the passed parameters for num_labels, learning_rate, etc.
    def model_fn_builder(self, num_labels, learning_rate, num_train_steps,
                         num_warmup_steps):
        """Returns `model_fn` closure for TPUEstimator."""

        def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
            """The `model_fn` for TPUEstimator."""
            input_ids = features["input_ids"]
            input_mask = features["input_mask"]
            segment_ids = features["segment_ids"]
            label_ids = features["label_ids"]
            is_predicting = (mode == tf.estimator.ModeKeys.PREDICT)
    
            # TRAIN and EVAL
            if not is_predicting:
                (loss, predicted_labels, log_probs) = self.create_model(
                    is_predicting, input_ids, input_mask, segment_ids, label_ids, num_labels)
    
                train_op = bert.optimization.create_optimizer(
                    loss, learning_rate, num_train_steps, num_warmup_steps, use_tpu=False)
    
                # Calculate evaluation metrics. 
                def metric_fn(label_ids, predicted_labels):
                    accuracy = tf.metrics.accuracy(label_ids, predicted_labels)
                    true_pos = tf.metrics.true_positives(label_ids,
                                                         predicted_labels)
                    true_neg = tf.metrics.true_negatives(label_ids,
                                                         predicted_labels)   
                    false_pos = tf.metrics.false_positives(label_ids,
                                                           predicted_labels)  
                    false_neg = tf.metrics.false_negatives(label_ids,
                                                           predicted_labels)
              
                    return {
                        "eval_accuracy": accuracy,
                        "true_positives": true_pos,
                        "true_negatives": true_neg,
                        "false_positives": false_pos,
                        "false_negatives": false_neg
                    }
      
                eval_metrics = metric_fn(label_ids, predicted_labels)
      
                if mode == tf.estimator.ModeKeys.TRAIN:
                    return tf.estimator.EstimatorSpec(mode=mode,
                                                      loss=loss,
                                                      train_op=train_op)
                else:
                    return tf.estimator.EstimatorSpec(mode=mode,
                                                      loss=loss,
                                                      eval_metric_ops=eval_metrics)
            else:
                (predicted_labels, log_probs) = self.create_model(
                    is_predicting, input_ids, input_mask, segment_ids, label_ids, num_labels)
    
                predictions = {
                    'probabilities': log_probs,
                    'labels': predicted_labels
                }
                return tf.estimator.EstimatorSpec(mode, predictions=predictions)

        # Return the actual model function in the closure
        return model_fn

    def getPrediction(self, in_sentences):
        """A method to get predictions"""
        #A list to map the actual labels to the predictions
        labels = ["Politics", "Technology", "Entertainment", "Business"]
      
        #Transforming the test data into BERT accepted form
        input_examples = [run_classifier.InputExample(guid="", text_a=x, text_b=None, label=0) for x in in_sentences] 
        
        #Creating input features for Test data
        input_features = run_classifier.convert_examples_to_features(input_examples, self.LABEL_LIST, self.MAX_SEQ_LENGTH, tokenizer)
      
        #Predicting the classes 
        predict_input_fn = run_classifier.input_fn_builder(features=input_features, seq_length=self.MAX_SEQ_LENGTH, is_training=False, drop_remainder=False)
        predictions = estimator.predict(predict_input_fn)
        return [(sentence, prediction['probabilities'], prediction['labels'], labels[prediction['labels']]) for sentence, prediction in zip(in_sentences, predictions)]
      
      
    def run_main_step(self):
        """Main processing step"""
        debug.trace_fmtd(5, "Script.run_main_step(): self={s}", s=self)

        # Loading The Data
        ## OLD: We will now load the data from a Google Drive directory and will also split the training set in to training and validation sets.
        ## train = pd.read_excel("/GD/My Drive/Colab Notebooks/News_category/Datasets/Data_Train.xlsx")
        ## test = pd.read_excel("/GD/My Drive/Colab Notebooks/News_category/Datasets/Data_Test.xlsx")
        train = pd.read_excel(system.form_path(INPUT_DIR, TRAINING_PATH))
        test = pd.read_excel(system.form_path(INPUT_DIR, TESTING_PATH))

        train, val =  train_test_split(train, test_size=0.2, random_state=100)
        #Training set sample
        debug.trace_fmt(4, "Train sample:\n{s}", s=train.head(5))
        debug.trace_fmt(4, "Test sample:\n{s}", s=test.head(5))
        print("Training Set Shape :", train.shape)
        print("Validation Set Shape :", val.shape)
        print("Test Set Shape :", test.shape)

        # Features in the dataset
        # ex: Index(['STORY', 'SECTION'], dtype='object')
        debug.trace_fmt(4, "Train columns: {c}", c=train.columns)

        # unique classes
        # ex; array([3, 1, 2, 0])
        debug.trace_fmt(4, "Unique training classes: {c}",
                        c=train['SECTION'].unique())
        
        # Distribution of classes
        # ex: <matplotlib.axes._subplots.AxesSubplot at 0x7ff5921f9ba8>
        if SHOW_PLOTS:
            train['SECTION'].value_counts().plot(kind='bar')

        # Compute train and warmup steps from batch size
        num_train_steps = int(len(train_features) / BATCH_SIZE * NUM_TRAIN_EPOCHS)
        num_warmup_steps = int(num_train_steps * WARMUP_PROPORTION)
        
        # Specify output directory and number of checkpoint steps to save
        run_config = tf.estimator.RunConfig(
            model_dir=OUTPUT_DIR,
            save_summary_steps=SAVE_SUMMARY_STEPS,
            save_checkpoints_steps=SAVE_CHECKPOINTS_STEPS)
        
        # Specify output directory and number of checkpoint steps to save
        run_config = tf.estimator.RunConfig(
            model_dir=OUTPUT_DIR,
            save_summary_steps=SAVE_SUMMARY_STEPS,
            save_checkpoints_steps=SAVE_CHECKPOINTS_STEPS)
        
        
        #Initializing the model and the estimator
        model_fn = self.model_fn_builder(
            num_labels=len(self.LABEL_LIST),
            learning_rate=LEARNING_RATE,
            num_train_steps=num_train_steps,
            num_warmup_steps=num_warmup_steps)
        
        estimator = tf.estimator.Estimator(
            model_fn=model_fn,
            config=run_config,
            params={"batch_size": BATCH_SIZE})
        
        # Read in training data
        # See 'Data preprocessing' notes in the header comments
        train_InputExamples = train.apply(lambda x:
                                          bert.run_classifier.InputExample(
                                              guid=None,
                                              text_a=x[DATA_COLUMN], 
                                              text_b=None, 
                                              label=x[LABEL_COLUMN]),
                                          axis=1)
        val_InputExamples = val.apply(lambda x:
                                      bert.run_classifier.InputExample(
                                          guid=None, 
                                          text_a=x[DATA_COLUMN], 
                                          text_b=None, 
                                          label=x[LABEL_COLUMN]),
                                      axis=1)
        debug.trace_object(5, train_InputExamples, "train_InputExamples")
        debug.trace(4, "Row 0 - guid of training set: {r}", r=train_InputExamples.iloc[0].guid)
        debug.trace(4, "__________\nRow 0 - text_a of training set {t}: ", r=train_InputExamples.iloc[0].text_a)
        debug.trace(4, "__________\nRow 0 - text_b of training set: {t}", t=train_InputExamples.iloc[0].text_b)
        debug.trace(4, "__________\nRow 0 - label of training set: {l}", l=train_InputExamples.iloc[0].label)

        # Convert to BERT format
        tokenizer = self.create_tokenizer_from_hub_module()
        debug.trace_fmt(4, "row 0 tokenized: {t}", t=tokenizer.tokenize(train_InputExamples.iloc[0].text_a))

        # Convert train and validation features to InputFeatures that BERT understands.
        train_features = bert.run_classifier.convert_examples_to_features(
            train_InputExamples, self.LABEL_LIST, self.MAX_SEQ_LENGTH, tokenizer)

        val_features = bert.run_classifier.convert_examples_to_features(
            val_InputExamples, self.LABEL_LIST, self.MAX_SEQ_LENGTH, tokenizer)
        
        # Example on first observation in the training set
        debug.trace_fmt(4, "Sentence: {s}", s=train_InputExamples.iloc[0].text_a)
        debug.trace_fmt(4, "-"*30)
        debug.trace_fmt(4, "Tokens: {t}", t=tokenizer.tokenize(train_InputExamples.iloc[0].text_a))
        debug.trace_fmt(4, "-"*30)
        debug.trace_fmt(4, "Input IDs: {i}", l=train_features[0].input_ids)
        debug.trace_fmt(4, "-"*30)
        debug.trace_fmt(4, "Input Masks: {m}", m-train_features[0].input_mask)
        debug.trace_fmt(4, "-"*30)
        debug.trace_fmt(4, "Segment IDs: {i}", i=train_features[0].segment_ids)

        # Initializing the model and the estimator
        model_fn = self.model_fn_builder(
            num_labels=len(self.LABEL_LIST),
            learning_rate=LEARNING_RATE,
            num_train_steps=num_train_steps,
            num_warmup_steps=num_warmup_steps)

        estimator = tf.estimator.Estimator(
            model_fn=model_fn,
            config=run_config,
            params={"batch_size": BATCH_SIZE})

        # Create an input function for training. drop_remainder=True for using TPUs.
        train_input_fn = bert.run_classifier.input_fn_builder(
            features=train_features,
            seq_length=self.MAX_SEQ_LENGTH,
            is_training=True,
            drop_remainder=False)

        # Create an input function for validating. drop_remainder=True for using TPUs.
        val_input_fn = run_classifier.input_fn_builder(
            features=val_features,
            seq_length=self.MAX_SEQ_LENGTH,
            is_training=False,
            drop_remainder=False)

        # Evaluating the model with Validation set
        estimator.evaluate(input_fn=val_input_fn, steps=None)

        # Evaluate over test set
        pred_sentences = list(test['STORY'])
        predictions = getPrediction(pred_sentences)
        debug.race_fmt(4, predictions[0])


        enc_labels = []
        act_labels = []
        for i in range(len(predictions)):
            enc_labels.append(predictions[i][2])
            act_labels.append(predictions[i][3])

        ## OLD: pd.DataFrame(enc_labels, columns=['SECTION']).to_excel('/GD/My Drive/Colab Notebooks/BERT/submission_bert.xlsx', index=False)
        data_file = system.form_path(INPUT_DIR, "submission_bert.xlsx")
        pd.DataFrame(enc_labels, columns=['SECTION']).to_excel(data_file,
                                                               index=False)

        # Classifying random sentences
        tests = getPrediction(
            ['Mr.Modi is the Indian Prime Minister',
             'Gaming machines are powered by efficient micro processores and GPUs',
             'That HBO TV series is really good',
             'A trillion dollar economy '
            ])
        debug.trace_object(4, tests, "tests")
        return

        
    ## TODO: def wrap_up(self):
    ##           # ...

    ## TODO: def clean_up(self):
    ##           # ...
    ##           super(Script, self).clean_up()

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=debug.QUITE_DETAILED)
    app = Script(
        description=__doc__,
        skip_input=False,
        manual_input=True,
        ## boolean_options=[TODO_ARG1],
        # TODO: positional_options=[TODO_FILENAME],
        ## TODO: text_options=[(TODO_ARG2, "TODO-desc")]
    )
    app.run()
