'''
    General TTS library and classes
'''
import subprocess

class TTS(object):
    def speak(self):
        raise NotImplementedError('Override in child class')

try:
    import pyttsx
    class PythonTTS(TTS):
        '''
            Wrapper around pyttsx
        '''
        def __init__(self, rate=150, voice_id=3):
            self.engine = pyttsx.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('voice', voice_id)

        def say(self, msg):
            self.engine.say(msg)
            self.engine.runAndWait()
except:
    pass

class cmdLineTTS(TTS):
    @classmethod
    def say(cls, msg):
        try:
            subprocess.check_call(['say', msg])
        # HACK:: Anshuman 11/04/2017, return code for some reason is
        # none 0, so subprocess is throwing an CalledProcessError
        # swallow for now
        except subprocess.CalledProcessError:
            pass
