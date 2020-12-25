import speech_recognition as sr

'''
Built-in Input
Built-in Output
DisplayPort
SteelSeries Arctis 1 Wireless
MMAudio Device
MMAudio Device (UI Sounds)
Soundflower (2ch)
Soundflower (64ch)
ZoomAudioDevice
Quicktime Input
Screen Record Audio
'''
r = sr.Recognizer()
mic = sr.Microphone(device_index=3)

with mic as source:
    while True:
        audio = r.listen(source)
        print(audio)
        try:
            print(r.recognize_google(audio))
        except:
            pass