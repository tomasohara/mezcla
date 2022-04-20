#! /usr/bin/env python
#
# Audio Module
#
# This is a wraper for audio processing tools.
#
# This provides an Audio wraper interface to extract
# multiples properties that you can implement on your
# proyects and also provides an argument processing class
# to use it from terminal.
#
# For now only two speech recognition engines are implemented:
# CMUSphinx and Houndify, only CMUSphinx works offline.
#


"""
Audio Module

This provides an Audio wraper interface to extract
multiples properties that you can implement on your
proyects and also provides an argument processing class
to use it from terminal.

For now only two speech recognition engines are implemented:
CMUSphinx and Houndify, only CMUSphinx works offline.

Usage example:
$ python audio.py path/to/folder                    => find audio files on path.
$ python audio.py --speech sphinx path/to/audio.wav => extract speech using CMUSphinx.
"""


# Standard packages
import re


# Installed packages
import librosa
import speech_recognition as sr


# Local packages
from mezcla.main import Main
from mezcla      import debug
from mezcla      import glue_helpers as gh


# Command-line labels constants
SOURCE  = 'source'
OUTPUT  = 'output'
SPEECH  = 'speech'
VERBOSE = 'verbose'


# Constants
AUDIO_FORMATS = ['aac', 'au', 'flac', 'm4a', 'mp3', 'ogg', 'wav']


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
        self.output  = self.get_parsed_argument(OUTPUT, self.output)
        self.speech  = self.get_parsed_argument(SPEECH, self.speech)
        self.verbose = self.get_parsed_option(VERBOSE)

        # Process source
        source_match = re.search(r'(?P<path>[\w\-\/]+)\.*(?P<ext>[a-zA-Z0-9]+)* *$', source)
        extension = source_match.group('ext') if source_match else ''
        path      = source_match.group('path') if source_match else ''

        # Check if is a valid audio file
        if extension in AUDIO_FORMATS:
            self.audios = [source]
            debug.trace(7, f'AudioArgumentProcessing.setup() - audio entered: {self.audios}')

        # Check if is a list of audios
        elif extension == 'list':
            self.audios = gh.read_lines(source)
            debug.trace(7, f'AudioArgumentProcessing.setup() - list of audios entered: {self.audios}')

        # Check if is a folder
        elif path and not extension:
            self.audios = librosa.util.find_files(source, ext=AUDIO_FORMATS, recurse=True)
            debug.trace(7, f'AudioArgumentProcessing.setup() - folder with audios entered ({source}): {self.audios}')


    def run_main_step(self):
        """Process main script"""
        debug.trace(7, f'AudioArgumentProcessing.run_main_step({self})')

        source = Audio()

        for audio in self.audios:
            debug.trace(7, f'AudioArgumentProcessing.run_main_step() - processing {audio}')

            output = ''

            if self.verbose:
                output += f'Audio founded: {audio}\n'

            # Extract speech
            if self.speech:
                if self.verbose:
                    output += '- speech recognized:\n'
                output += source.get_speech(path=audio, engine=self.speech)
                output += '\n'

            print(output.rstrip('\n'))

            # Save on output
            ## TODO: WORK-IN-PROGRESS


class SpeechEngine:
    """SpeechEngine class"""


    def __init__(self, identifier=''):
        self._identifier = identifier


    def get_identifier(self):
        """Returns engine identifier string"""
        debug.trace(7, f'SpeechEngine.get_identifier() => {self._identifier}')
        return self._identifier


    # pylint: disable=no-self-use
    def read_audio(self, path):
        """Read audio file from PATH"""
        ## OVERRIDE THIS
        debug.trace(7, f'SpeechEngine.read_audio({path})')


    # pylint: disable=no-self-use
    def get_speech(self, path):
        """Get speech from audio in PATH"""
        result = ''
        ## OVERRIDE THIS
        debug.trace(7, f'SpeechEngine.get_speech({path}) => {result}')
        return result


class SpeechRecognition(SpeechEngine):
    """SpeechRecognition class for speech_recognition module"""


    def __init__(self, identifier=''):
        super().__init__(identifier)
        self._recognition = sr.Recognizer()


    def get_instance(self):
        """Returns recognition instance"""
        return self._recognition


    def read_audio(self, path):
        """Read audio file"""
        with sr.AudioFile(path) as source:
            audio = self.get_instance().record(source)
        debug.trace(7, f'SpeechEngine.read_audio()')
        return audio


class CMUSphinx(SpeechRecognition):
    """CMUSphinx Speech Recognition class"""


    def get_speech(self, path):
        """Get speech from audio in PATH"""

        result = ''

        audio = self.read_audio(path)

        ## TODO: use decorator to avoid duplicated code.
        try:
            result = self.get_instance().recognize_sphinx(audio)
        except sr.UnknownValueError:
            print(f'Sphinx could not understand {path}')
        except sr.RequestError as error:
            print('Sphinx error; {0}'.format(error))

        debug.trace(7, f'CMUSphinx.get_speech({path}) => {result}')
        return result


class Houndify(SpeechRecognition):
    """Houndify Speech Recognition class"""


    def __init__(self, identifier, client_id='', client_key=''):
        super().__init__(identifier)
        self.client_id  = client_id
        self.client_key = client_key


    def get_speech(self, path):
        """Get speech from audio in PATH"""
        result = ''

        audio = self.read_audio(path)

        try:
            result = self.get_instance().recognize_houndify(audio,
                                                            client_id=self.client_id,
                                                            client_key=self.client_key)
        except sr.UnknownValueError:
            print(f'Houndify could not understand {path}')
        except sr.RequestError as error:
            print("Could not request results from Houndify service; {0}".format(error))

        debug.trace(7, f'Houndify.get_speech({path}) => {result}')
        return result


class Audio:
    """
    This is a wraper interface for audio processing.
    """


    # Global class constants
    SPEECH_ENGINES = [CMUSphinx('sphinx'),
                      Houndify('houndify', client_id='CLIENT_ID_HERE', client_key='CLIENT_KEY_HERE')]


    def __init__(self, path=''):
        self._path = path


    def set_path(self, path):
        """Set new audio PATH"""
        debug.trace(7, f'Audio.set_path(path={path})')
        self._path = path


    def get_path(self):
        """Get audio PATH"""
        debug.trace(7, f'Audio.get_path() => {self._path}')
        return self._path


    def get_speech(self, path='', engine=''):
        """Get speech from PATH using specified ENGINE"""

        # Default speech engine
        speech_engine = self.SPEECH_ENGINES[0]

        # Check path
        path = path if path else self._path

        # Get engine
        if engine:
            for sengine in self.SPEECH_ENGINES:
                if sengine.get_identifier().lower() == engine.lower():
                    speech_engine = sengine
                    break

        # Extract speech
        result = speech_engine.get_speech(path)

        debug.trace(7, f'Audio.get_speech(path={path}, engine={engine}) => {result}')
        return result


if __name__ == '__main__':
    app = AudioArgumentProcessing(description          = __doc__,
                                  positional_arguments = [(SOURCE, 'audio source file')],
                                  text_options         = [(OUTPUT, 'output folder'),
                                                          (SPEECH, 'speech engine')],
                                  boolean_options      = [(VERBOSE, 'verbose print')],
                                  manual_input         = True)
    app.run()
