# Drowsiness Alert for Students

A real-time drowsiness detector that watches your eyes through a normal webcam and alerts you when you start dozing off while studying.

## Demo


https://github.com/user-attachments/assets/b4278ade-b3b0-4cd0-abb4-fee06d7442cb













## Features

- Real-time face and eye tracking with MediaPipe Face Mesh
- Eye Aspect Ratio (EAR) based eye-closure detection
- Auto calibration: the threshold is set from your own open-eye EAR in the first 5 seconds, so it adapts to different people, glasses and lighting
- Alarm if eyes stay closed for 2 seconds (normal blinks are ignored)
- Blink counter and drowsy-event counter on screen
- Break reminder after 3 drowsy events
- Session report saved to CSV (date, duration, blinks, blinks per minute, drowsy events, threshold)

## How it works

1. MediaPipe gives 468 face landmarks, 6 of which outline each eye.
2. EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|). It is high when the eye is open and drops when it closes.
3. For the first 5 seconds the program measures your normal EAR and sets the threshold to 75 percent of it.
4. If EAR stays below the threshold for 2 seconds, the alarm sounds.

## Tech stack

Python | OpenCV | MediaPipe | NumPy

## Setup

Python 3.10 to 3.12 is recommended (MediaPipe may not install on 3.13).

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python drowsiness_v2.py

Press q in the camera window to quit and save the session report.

## Settings

You can change these values at the top of drowsiness_v2.py:

- CALIBRATION_SECONDS: length of calibration (default 5)
- THRESHOLD_RATIO: share of open-eye EAR used as threshold (default 0.75)
- CLOSED_SECONDS: how long eyes must stay closed before the alarm (default 2.0)
- BREAK_AFTER_EVENTS: drowsy events before the break reminder (default 3)

## Future ideas

- Yawn detection using Mouth Aspect Ratio
- Head-nod detection
- Streamlit dashboard for session history

## Author

Aastha patidar 
