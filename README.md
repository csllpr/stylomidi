# stylomidi
Python utility to transform audio import from Stylophone (or other similar instruments) to midi singal.
Environment: python = 3.11
```
conda create -n stylomidi python=3.11
conda install -c conda-forge numpy pyaudio aubio mido
pip install python-rtmidi
```
Usage: 
```
python stylomidi.py [port]
```
