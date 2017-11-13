#!/usr/bin/env python
#
# Command line client for transcription

import sys
import os
import gi
gi.require_version('Gst', '1.0')

from gi.repository import GObject, Gst

class DemoApp(object):
    def __init__(self, model='final.mdl', fst='HCLG.fst', words='words.txt', mfcc_conf='conf/mfcc.conf',
                 ivector_extr_conf='conf/ivector_extractor.fixed.conf', phones='phones.txt',
                 word_boundary='word_boundary.int'):
        """ Initialize gstreamer pipeline and run transcription. """

        if self.check_files([model, fst, words, mfcc_conf, ivector_extr_conf, phones, word_boundary]):
            self.model = model
            self.fst = fst
            self.words = words
            self.mfcc_conf = mfcc_conf
            self.ivector_extr_conf = ivector_extr_conf
            self.phones = phones
            self.word_boundary = word_boundary
        else:
            sys.exit(1)

        Gst.init()
        mainloop = GObject.MainLoop()
        self.init_gst()
        mainloop.run()

    def check_files(self, files, stderr_output=True):
        """ Check if all files are present.
        Args:
            files:  list of files to be checked
        Returns:
            True if all files exist, else - False
        """
        check = True

        for f in files:
            if not os.path.isfile(f):
                sys.stderr.write('{0} is missing\n'.format(f))
                check = False

        return check

    def setup_asr(self):
        """ Sets up the ASR factory.
        Returns:
            GstElementFactory or None (sys.exit emitted)
        """
        asr = Gst.ElementFactory.make('kaldinnet2onlinedecoder', 'asr')
        if not asr:
            sys.stderr.write('Couldn\'t create the kaldinnet2onlinedecoder element. \n')
            if os.environ.has_key('GST_PLUGIN_PATH'):
                sys.stderr.write('Have you compiled the Kaldi GStreamer plugin?\n')
            else:
                sys.stderr.write('You probably need to set the GST_PLUGIN_PATH envoronment variable\n')
                sys.stderr.write('Try running: GST_PLUGIN_PATH=../src {0}'.format(sys.argv[0]))
            sys.exit(1)

        config = {
            'use-threaded-decoder': True,
            'model': self.model,
            'fst': self.fst,
            'word-syms': self.words,
            'phone-syms': self.phones,
            'word-boundary-file': self.word_boundary,
            'num-nbest': 3,
            'num-phone-alignment': 3,
            'do-phone-alignment': True,
            'feature-type': 'mfcc',
            'mfcc-config': self.mfcc_conf,
            'ivector-extraction-config': self.ivector_extr_conf,
            'max-active': 7000,
            'beam': 11.0,
            'lattice-beam': 5.0,
            'do-endpointing': True,
            'endpoint-silence-phones': '1:2:3:4:5:6:7:8:9:10',
            'chunk-length-in-secs': 0.2
        }

        print(config)

        # TODO: Python3 compatibility
        for key, value in config.iteritems():
            asr.set_property(key, value)

        return asr

    def init_gst(self):
        """ Initialize pipeline.

        Pipeline structure:
            filesrc -> decodebin -> audioconvert -> audioresample -> asr -> fakesink
        """
        self.filesrc = Gst.ElementFactory.make('filesrc', 'filesrc')
        self.decodebin = Gst.ElementFactory.make('mad', 'decoder')  # TODO: change decoder depending on input
        self.audioconvert = Gst.ElementFactory.make('audioconvert', 'audioconvert')
        self.audioresample = Gst.ElementFactory.make('audioresample', 'audioresample')
        self.asr = self.setup_asr()
        self.filesink = Gst.ElementFactory.make('fakesink', 'filesink')

        self.filesrc.set_property('location', '{0}'.format(os.path.abspath(sys.argv[1])))
        # self.filesink.set_property('location', '/dev/stdout')
        # self.filesink.set_property('buffer-mode', 2)

        self.pipeline = Gst.Pipeline()
        for elem in [self.filesrc, self.decodebin, self.audioconvert, self.audioresample, self.asr, self.filesink]:
            self.pipeline.add(elem)

        self.filesrc.link(self.decodebin)
        self.decodebin.link(self.audioconvert)
        self.audioconvert.link(self.audioresample)
        self.audioresample.link(self.asr)
        self.asr.link(self.filesink)

        # Signals for asr
        self.asr.connect('partial-result', self.on_partial_result)
        self.asr.connect('final-result', self.on_final_result)
        self.asr.connect('full-final-result', self.on_full_final_result)

        self.pipeline.set_state(Gst.State.PLAYING)
        self.filesrc.set_state(Gst.State.PLAYING)

    def on_partial_result(self, asr, hyp):
        """ Just print partial result. """
        print('Partial: {0}'.format(hyp))

    def on_final_result(self, asr, hyp):
        """ Just print the final result. """
        print('Final: {0}'.format(hyp))

    def on_full_final_result(self, asr, hyp):
        print('FULL FINAL: {0}'.format(hyp))

if __name__ == '__main__':
    app = DemoApp()
