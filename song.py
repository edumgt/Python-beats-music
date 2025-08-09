import json
import numpy as np
import sounddevice
import wave
import struct
import os

import waveimport

# GLOBAL VARIABLES
PRJ_PATH = './db/projects/'
FRAMERATE = waveimport.FRAMERATE

class Sample:
    def __init__(self, data):
        self.__data = data

    @property
    def data(self):
        return self.__data

    def fit(self, nframes, amplitude):
        if amplitude == 'X':
            if nframes < self.data.shape[0]:
                data = self.data[:nframes]
            elif nframes > self.data.shape[0]:
                data = np.append(self.data, np.zeros(nframes - self.data.shape[0]))
            else:
                data = self.data
        else:
            try:
                if nframes < self.data.shape[0]:
                    data = self.data[:nframes] * (int(amplitude) / 10)
                elif nframes > self.data.shape[0]:
                    data = np.append(self.data, np.zeros(nframes - self.data.shape[0])) * (int(amplitude) / 10)
                else:
                    data = self.data * (int(amplitude) / 10)
            except ValueError:
                raise ValueError("AMPLITUDE VALUE MUST BE INTEGER 1-9 OR X")
        return data.astype(np.float32)

class Track:
    def __init__(self, sampledata, pattern, trigger):
        self.__sample = Sample(sampledata)
        self.__trigger = trigger
        self.__pattern = pattern.replace('|', '').replace(' ', '')
        self.__patterns = ''
        self.__getpatterns()
        self.__data = np.empty(0, dtype=np.float32)
        self.__make()

    @property
    def data(self):
        return self.__data

    def __getpatterns(self):
        for i in self.__pattern:
            if i == '.':
                self.__patterns += i
            else:
                self.__patterns += f'|{i}'
        self.__patterns = [p for p in self.__patterns.split('|') if p]

    def __make(self):
        for pat in self.__patterns:
            length = len(pat) * self.__trigger
            amplitude = 0 if pat.startswith('.') else pat[0]
            part = self.__sample.fit(length, amplitude)
            self.__data = np.append(self.__data, part)

class Song:
    def __init__(self, name):
        for filename in os.listdir(PRJ_PATH):
            if filename.endswith('.json'):
                with open(PRJ_PATH + filename, 'r') as songsfile:
                    data = json.load(songsfile)
                    if name in data:
                        song = data[name]
                        break
        else:
            raise ValueError(f"No song named '{name}' found in '{PRJ_PATH}'")

        self.__name = name
        self.__nchannels = song['Channels']
        self.__beat = len(song['Beat'])
        self.__repeat = song['Repeat']
        self.__tracks = song['Tracks']
        self.__tempo = song['Tempo']
        self.__trigger = int(60 / song['Tempo'] * FRAMERATE / self.__beat)

        self.__channels = {}
        self.__maketracks()
        self.__makedata()

    @property
    def name(self):
        return self.__name

    @property
    def nchannels(self):
        return self.__nchannels

    @property
    def repeat(self):
        return self.__repeat

    @property
    def data(self):
        return self.__data

    def __maketracks(self):
        for t, info in self.__tracks.items():
            samplefile = info['SampleName'] + '.wav'
            sampledata = waveimport.import_file_mono(samplefile)
            track = Track(sampledata[info['SampleName']], ''.join(info['Pattern']), self.__trigger)
            self.__channels[t] = {"Align": info['Align'], "Data": track.data}

    def __makedata(self):
        max_length = max(track['Data'].shape[0] for track in self.__channels.values())

        if self.__nchannels == 2:
            left, l = np.zeros(max_length, dtype=np.float32), 0
            right, r = np.zeros(max_length, dtype=np.float32), 0

            for track in self.__channels.values():
                data = track['Data']
                if data.shape[0] < max_length:
                    data = np.pad(data, (0, max_length - data.shape[0]))

                if track['Align'] == 'L':
                    left += data
                    l += 1
                elif track['Align'] == 'R':
                    right += data
                    r += 1
                elif track['Align'] == 'C':
                    left += data
                    right += data
                    l += 1
                    r += 1
                else:
                    raise ValueError("CHANNEL CAN ONLY BE EITHER ['L', 'R', 'C']")

            left = (left / l) if l else left
            right = (right / r) if r else right

            self.__data = np.empty(max_length * 2, dtype=np.float32)
            self.__data[0::2] = left
            self.__data[1::2] = right

        else:
            mono = np.zeros(max_length, dtype=np.float32)
            for track in self.__channels.values():
                data = track['Data']
                if data.shape[0] < max_length:
                    data = np.pad(data, (0, max_length - data.shape[0]))
                mono += data / len(self.__channels)
            self.__data = mono

class Songs:
    def __init__(self):
        self.songs = []
        for filename in os.listdir(PRJ_PATH):
            if filename.endswith('.json'):
                with open(PRJ_PATH + filename, 'r') as songsfile:
                    self.songs.extend(json.load(songsfile).keys())

def play(channels, data, framerate, rep=1):
    datarep = np.tile(data, rep)
    if channels != 1:
        datarep = np.reshape(datarep, (-1, channels))
    sounddevice.play(datarep, framerate)
    sounddevice.wait()

def record(name, channels, data, framerate, rep=1):
    filepath = f'{PRJ_PATH}{name}.wav'
    with wave.open(filepath, 'wb') as output:
        output.setparams((channels, 2, framerate, 0, 'NONE', 'not compressed'))
        data = np.tile(data, rep).astype(np.float16)
        values = [struct.pack('h', int(sample * 32767)) for sample in data]
        output.writeframes(b''.join(values))
