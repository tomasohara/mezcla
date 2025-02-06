#! /usr/bin/env python
#
# Audio Module
#
# This provides an Audio wraper interface to extract
# multiples properties that you can implement on your
# projects and also provides an argument processing class
# to easily use from terminal to use different features.
#
#
# Python code example using Audio wraper interface:
# | some_audio = Audio(path="./path/to/audio.wav")
# | print(some_audio.speech_to_text(engine="sphinx"))
#
# Example using the terminal:
# $ python audio.py path/to/folder
# $ python audio.py --speech sphinx path/to/audio.wav
#
#
# The Audio wraper provides for now four (OLD: three) engines to extract speech:
# - CMUSphinx     (aka "sphinx")
# - Houndify      (aka "houndify")
# - IBM Watson    (aka "watson")
# - HuggingFace   (aka "huggingface") [NEW]
#
# You can find the UML diagram related to this module on:
# - ./docs/audio_uml.svg
#
# TODO3: print => system.print_error
#

"""
Audio Module

This provides an Audio wraper interface to extract
multiples properties that you can implement on your
projects and also provides an argument processing class
to easily use from terminal to use different features.

Python code example using Audio wraper interface:
| some_audio = Audio(path="./path/to/audio.wav")
| print(some_audio.speech_to_text(engine="sphinx"))

Example using the terminal:
$ python audio.py path/to/folder
$ python audio.py --speech sphinx path/to/audio.wav

The Audio wraper provides for now four (OLD: three) engines to extract speech:
- CMUSphinx     (aka "sphinx")
- Houndify      (aka "houndify")
- IBM Watson    (aka "watson")
- HuggingFace   (aka "huggingface") [NEW]
"""
#
# TODO2: reduce redundancy in header comments and docstring
# TODO3: format code example using IPython example syntax (i.e., '>>>')
# TODO4: make docstring concise (as per template.py tip)

# Standard packages
from abc import ABCMeta, abstractmethod
import re

# Installed packages
## OLD:
## import librosa
## import speech_recognition as sr
## from ibm_watson import SpeechToTextV1
## from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
## from transformers import pipeline
sr = None
librose = None
sr = None
SpeechToTextV1 = None
pipeline = None

# Local packages
from mezcla.main import Main
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Command-line labels constants
SOURCE  = 'source'
OUTPUT  = 'output'
SPEECH  = 'speech'
VERBOSE = 'verbose'


# Constants
AUDIO_FORMATS = ['aac', 'au', 'flac', 'm4a', 'mp3', 'ogg', 'wav']


# Authentications.
# This is optional; empty values must be completed with
# your credentials if you want to use some of these platforms.
IBM_WATSON_KEY = ''
IBM_WATSON_URL = ''
HOUNDIFY_ID  = ''
HOUNDIFY_KEY = ''


class AudioArgumentProcessing(Main):
    """Argument processing class"""


    # Class-level member variables for arguments (avoids need for class constructor)
    audios  = []
    output  = ''
    speech  = ''
    verbose = False

    def setup(self):
        """Process arguments"""
        debug.trace(7, f'AudioArgumentProcessing.setup({self})')

        # Check the command-line options
        source       = self.get_parsed_argument(SOURCE, "")
        self.output  = self.get_parsed_option(OUTPUT, self.output)
        self.speech  = self.get_parsed_option(SPEECH, self.speech)
        self.verbose = self.get_parsed_option(VERBOSE)

        # Process source
        source_match = re.search(r'(?P<path>[\w\-\/]+)\.*(?P<ext>[a-zA-Z0-9]+)* *$', source)
        extension = source_match.group('ext') if source_match else ''
        path      = source_match.group('path') if source_match else ''

        # Check if is a valid audio file
        if extension in AUDIO_FORMATS:
            self.audios = [source]

        # Check if is a list of audios
        elif extension == 'list':
            self.audios = gh.read_lines(source)

        # Check if is a folder
        elif path and not extension:
            # pylint: disable=import-outside-toplevel, disable=redefined-outer-name
            import librosa
            self.audios = librosa.util.find_files(source, ext=AUDIO_FORMATS, recurse=True)

        else:
            print('Not valid audio files founded.')

        # Initializate audios
        for index, audio_path in enumerate(self.audios):
            self.audios[index] = Audio(path = audio_path)

        debug.trace(7, f'AudioArgumentProcessing.setup() - audios founded from ({source}): {self.audios}')


    def run_main_step(self):
        """Process main script"""
        debug.trace(7, f'AudioArgumentProcessing.run_main_step({self})')


        for current_audio in self.audios:
            debug.trace(7, f'AudioArgumentProcessing.run_main_step() - processing {current_audio}')

            output = ''

            if self.verbose:
                output += f'Audio: {current_audio.get_path()}\n'

            # Extract speech
            if self.speech:
                if self.verbose:
                    output += '- speech recognized:\n'
                output += current_audio.speech_to_text(engine = self.speech)
                output += '\n'

            print(output.rstrip('\n'))

            # Save on output
            ## TODO: WORK-IN-PROGRESS


class SpeechEngine(metaclass=ABCMeta):
    """SpeechEngine abstract class"""


    # Global state
    _IDENTIFIER = 'generic'

    def __init__(self):
        """Class initializer"""
        debug.trace_object(5, self, label="SpeechEngine instance")

    def setup(self):
        """Post-init setup (e.g., import dynamic packages)"""
        debug.trace(4, "SpeechEngine.setup()")
        raise NotImplementedError()

    def get_identifier(self):
        """Returns engine identifier string"""
        debug.trace(7, f'SpeechEngine.get_identifier() => {self._IDENTIFIER}')
        return self._IDENTIFIER

    def check_credentials(self):
        """Check if credentials are valid"""

        is_valid = True
        ## TODO: WORK-IN-PROGRESS

        debug.trace(7, f'SpeechEngine.check_credentials() => {is_valid}')
        return is_valid

    @abstractmethod
    def particular_check_audio(self, path):
        """Check if audio in PATH is valid"""
        is_valid = True
        if path:
            raise NotImplementedError()
        debug.trace(7, f'SpeechEngine.particular_check_audio({path}) => {is_valid}; self={self}')
        return is_valid

    @abstractmethod
    def particular_speech_to_text(self, path):
        """Extract speech from audio in PATH using particular speech engine"""
        result = ''
        debug.trace(7, f'SpeechEngine.particular_speech_to_text({path}) => {result}; self={self}')
        if path:
            raise NotImplementedError()
        return result

    def speech_to_text(self, path):
        """Transcribe speech from audio in PATH"""
        self.setup()
        result = ''

        if not self.check_credentials():
            print(f'Invalid credentials for {self._IDENTIFIER}.')
            return result

        if not self.particular_check_audio(path):
            print(f'Invalid audio ({path}) for {self._IDENTIFIER}.')
            return result

        result = self.particular_speech_to_text(path)

        debug.trace(7, f'SpeechEngine.speech_to_text({path}) => {result}')
        return result

class IBMWatson(SpeechEngine):
    """
    Speech recognition engine for IBM Watson.
    Docs: https://cloud.ibm.com/apidocs/speech-to-text?code=python#recognize
    """
    ## TODO: solve getting very short responses (not full transcription)

    # Global state
    _IDENTIFIER = 'watson'

    def __init__(self, api_key='', api_url=''):
        self.api_key = api_key
        self.api_url = api_url
        super().__init__()
        self.IAMAuthenticator = None
        self.SpeechToTextV1 = None
        debug.trace_object(5, self, label="IBMWatson instance")

    def setup(self):
        # pylint: disable=import-outside-toplevel, disable=redefined-outer-name, import-error
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
        from ibm_watson import SpeechToTextV1
        self.IAMAuthenticator = IAMAuthenticator
        self.SpeechToTextV1 = SpeechToTextV1

    def particular_check_audio(self, _path):
        pass
        
    def particular_speech_to_text(self, path):
        """Transcribe speech from audio in PATH"""
        result = ''

        # Get extension
        extension = ''
        for ext in AUDIO_FORMATS:
            if f'.{ext}' in path:
                extension = ext

        # Setup Service
        authenticator = self.IAMAuthenticator(self.api_key)
        stt = self.SpeechToTextV1(authenticator=authenticator)
        stt.set_service_url(self.api_url)

        # Perform conversion
        with open(path, 'rb') as path_audio:
            res = stt.recognize(audio=path_audio,
                                content_type=f'audio/{extension}',
                                model='en-US_NarrowbandModel',
                                inactivity_timeout=30).get_result()

        ## result = res['results'][0]['alternatives'][0]['transcript']
        result = str(res)

        debug.trace(7, f'SpeechEngine.speech_to_text({path}) => {result}')
        return result

class SpeechRecognition(SpeechEngine):
    """SpeechRecognition abstract class for speech_recognition module"""

    ## OLD:
    ## # Global state
    ## _recognition = sr.Recognizer()

    def __init__(self):
        super().__init__()
        self.sr = None
        self._recognition = None
        debug.trace_object(5, self, label="SpeechRecognition instance")

    def setup(self):
        # pylint: disable=import-outside-toplevel, disable=redefined-outer-name
        import speech_recognition as sr
        self.sr = sr
        self._recognition = sr.Recognizer()
        
    def particular_check_audio(self, _path):
        pass

    def particular_speech_to_text(self, _path):
        pass

    def get_instance(self):
        """Returns recognition instance"""
        return self._recognition

    def read_audio(self, path):
        """Read audio file"""

        with self.sr.AudioFile(path) as source:
            audio = self.get_instance().record(source)

        debug.trace(7, 'SpeechEngine.read_audio()')
        return audio

class CMUSphinx(SpeechRecognition):
    """CMUSphinx Speech Recognition class"""

    # Global state
    _IDENTIFIER = 'sphinx'

    def __init__(self):
        super().__init__()
        debug.trace_object(5, self, label="CMUSphinx instance")

    def setup(self):
        # pylint: disable=import-outside-toplevel, disable=redefined-outer-name
        import speech_recognition as sr
        self.sr = sr
        
    def particular_check_audio(self, path):
        """Check if audio in PATH is valid"""
        is_valid = True

        ## TODO: WORK-IN-PROGRESS
        ## NOTE: sphinx does not support mp3 format

        debug.trace(7, f'SpeechEngine.particular_check_audio({path}) => {is_valid}')
        return is_valid

    def particular_speech_to_text(self, path):
        """Transcribe speech from audio in PATH"""
        result = ''

        # Read audio
        audio = self.read_audio(path)

        ## TODO: use decorator to avoid duplicated code.
        try:
            result = self.get_instance().recognize_sphinx(audio)
        except self.sr.UnknownValueError:
            print(f'Sphinx could not understand {path}')
        except self.sr.RequestError as error:
            print(f'Sphinx error; {error}')

        debug.trace(7, f'CMUSphinx.speech_to_text({path}) => {result}')
        return result

class Houndify(SpeechRecognition):
    """Houndify Speech Recognition class"""

    # Global state
    _IDENTIFIER = 'houndify'

    def __init__(self, client_id='', client_key=''):
        super().__init__()
        self.client_id  = client_id
        self.client_key = client_key
        debug.trace_object(5, self, label="Houndify instance")

    def setup(self):
        # pylint: disable=import-outside-toplevel, disable=redefined-outer-name
        import speech_recognition as sr
        self.sr = sr
        
    def particular_check_audio(self, path):
        """Check if audio in PATH is valid"""
        is_valid = True

        ## TODO: WORK-IN-PROGRESS
        ## NOTE: Houndify only can be used with audios less than a 1min.

        debug.trace(7, f'Houndify.particular_check_audio({path}) => {is_valid}')
        return is_valid

    def particular_speech_to_text(self, path):
        """Transcribe speech from audio in PATH"""
        result = ''

        # Read audio
        audio = self.read_audio(path)

        # Extract speech
        try:
            result = self.get_instance().recognize_houndify(audio,
                                                            client_id=self.client_id,
                                                            client_key=self.client_key)
        except self.sr.UnknownValueError:
            print(f'Houndify could not understand {path}')
        except self.sr.RequestError as error:
            print("Could not request results from Houndify service; {0}".format(error))

        debug.trace(7, f'Houndify.speech_to_text({path}) => {result}')
        return result

class HuggingFace(SpeechRecognition):
    """HuggingFace Speech Recognition class"""

    # SpeechRecognition in HuggingFace requires two core components: asr_model, asr_task
    # A model is created using pipeline method: model = pipeline(asr_model, asr_task)
    # PATH to audio file is provided as: result = model(PATH)
    # result returns a dictionary: {"text": "text_after_audio_recognition"}
    # NOTE[1]: Inspired by mezcla/examples/hugging_face_speechrec.py
    # NOTE[2]: Excluded the use of gradio for UI support
    # TODO: Add more exceptions

    # Global state
    _IDENTIFIER = "huggingface"

    def __init__(self):
        super().__init__()
        self.pipeline = None
        debug.trace_object(5, self, label="HuggingFace instance")

    def setup(self):
        # pylint: disable=import-outside-toplevel, disable=redefined-outer-name
        from transformers import pipeline
        self.pipeline = pipeline
        
    def particular_check_audio(self, path) -> bool:
        """Check if audio in PATH is valid"""
        result = False
        for extension in AUDIO_FORMATS:
            if f".{extension}" in path:
                result = True
                break
        debug.trace(7, f"HuggingFace.particular_check_audio({path}) => {result}")
        return result

    def particular_speech_to_text(self, path) -> str:
        """Transcribe speech from audio in PATH"""
        asr_model = "jonatasgrosman/wav2vec2-large-xlsr-53-english"
        asr_task = "automatic-speech-recognition"
        is_valid_audio = self.particular_check_audio(path)
        result = ""

        try:
            if is_valid_audio:
                model = self.pipeline(task=asr_task, model=asr_model)
                result = model(path)["text"]
            else:
                print(f"Error: Unable to find SOUND_FILE '{path}'")
        except ImportError as e:
            print(f"{e}: PyTorch, TensorFlow >= 2.0, or Flax not found")
        except:
            system.print_exception_info("particular_speech_to_text")

        debug.trace(7, f"HuggingFace.particular_speech_to_text({path}) => {result}")
        return result
    

class Audio:
    """
    This is a wrapper interface for audio processing.
    """

    # Global state
    SPEECH_ENGINES = [CMUSphinx(),
                      Houndify(client_id=HOUNDIFY_ID, client_key=HOUNDIFY_KEY),
                      IBMWatson(api_key=IBM_WATSON_KEY, api_url=IBM_WATSON_URL),
                      HuggingFace()]

    def __init__(self, path=''):
        self._path = path
        debug.trace_object(5, self, label="Audio instance")

    def set_path(self, path):
        """Set new audio PATH"""
        debug.trace(7, f'Audio.set_path(path={path})')
        self._path = path

    def get_path(self):
        """Get audio PATH"""
        debug.trace(7, f'Audio.get_path() => {self._path}')
        return self._path

    def get_extension(self):
        """Get extension of audio file"""

        result = re.search(r'(?P<path>[\w\-\/]+)\.*(?P<ext>[a-zA-Z0-9]+)* *$', self.get_path())
        result = result.group('ext') if result else ''

        debug.trace(7, f'Audio.get_extension() => {result}')
        return result

    def get_vocals(self, output=''):
        """Isolate vocals of an audio in path and save on OUTPUT"""

        ## TODO: WORK-IN-PROGRESS

        debug.trace(7, f'SpeechEngine.get_vocals() => result saved on {output}; self={self}')

    def speech_to_text(self, engine=''):
        """Transcribe speech from audio path using specified ENGINE"""

        # Isolate vocal to improve accuracy
        ## TODO: WORK-IN-PROGRESS

        # Select speech engine.
        speech_engine = None
        for temp_engine in self.SPEECH_ENGINES:
            if temp_engine.get_identifier().lower() == engine.lower():
                speech_engine = temp_engine
                break

        # Extract final speech
        result = ""
        if speech_engine is not None:
            speech_engine.setup()
            result = speech_engine.speech_to_text(self._path)

        debug.trace(7, f'Audio.speech_to_text(path={self._path}, engine={engine}) => {result}')
        return result

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    app = AudioArgumentProcessing(description          = __doc__,
                                  positional_arguments = [(SOURCE, 'audio source file')],
                                  text_options         = [(OUTPUT, 'output folder'),
                                                          (SPEECH, 'speech engine')],
                                  boolean_options      = [(VERBOSE, 'verbose print')],
                                  manual_input         = True)
    app.run()
