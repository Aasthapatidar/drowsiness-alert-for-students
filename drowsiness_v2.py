import time
import math
import csv
import os
import datetime
import cv2
import mediapipe as mp

CALIBRATION_SECONDS = 5
THRESHOLD_RATIO = 0.75     # khuli aankh ke EAR ka 75%
CLOSED_SECONDS = 2.0
ALARM_COOLDOWN = 3.0
BREAK_AFTER_EVENTS = 3
REPORT_FILE = "session_report.csv"

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def eye_aspect_ratio(pts):
    p1, p2, p3, p4, p5, p6 = pts
    return (dist(p2, p6) + dist(p3, p5)) / (2.0 * dist(p1, p4))


def play_alarm():
    try:
        import winsound
        winsound.Beep(1500, 700)
    except ImportError:
        print("\a", end="", flush=True)


def save_report(duration_min, blinks, events, threshold):
    new_file = not os.path.exists(REPORT_FILE)
    bpm = blinks / duration_min if duration_min > 0 else 0
    with open(REPORT_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["date", "time", "duration_min", "blinks",
                        "blinks_per_min", "drowsy_events", "threshold"])
        now = datetime.datetime.now()
        w.writerow([now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
                    round(duration_min, 2), blinks, round(bpm, 1),
                    events, round(threshold, 3)])
    print("Report saved in", os.path.abspath(REPORT_FILE))


def main():
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    cap = cv2.VideoCapture(0)

    threshold = None
    cal_samples = []
    cal_start = None

    eyes_closed_since = None
    last_alarm = 0
    blink_count = 0
    was_closed = False
    drowsy_events = 0
    session_start = time.time()

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)
        now = time.time()

        status, color = "No face", (200, 200, 200)

        if result.multi_face_landmarks:
            lm = result.multi_face_landmarks[0].landmark

            def get(idx_list):
                return [(lm[i].x * w, lm[i].y * h) for i in idx_list]

            left, right = get(LEFT_EYE), get(RIGHT_EYE)
            ear = (eye_aspect_ratio(left) + eye_aspect_ratio(right)) / 2.0

            for (x, y) in left + right:
                cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 0), -1)

            cv2.putText(frame, "EAR: %.2f" % ear, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            if threshold is None:
                # ---- Calibration phase ----
                if cal_start is None:
                    cal_start = now
                cal_samples.append(ear)
                left_sec = max(0, CALIBRATION_SECONDS - (now - cal_start))
                status, color = "Calibrating... %.0fs" % left_sec, (255, 200, 0)
                cv2.putText(frame, "Look at camera, eyes normal, blink naturally",
                            (10, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (255, 255, 0), 2)
                if now - cal_start >= CALIBRATION_SECONDS and len(cal_samples) >= 20:
                    cal_samples.sort()
                    open_ear = cal_samples[int(0.7 * len(cal_samples))]
                    threshold = open_ear * THRESHOLD_RATIO
                    print("Open EAR: %.3f  Threshold: %.3f" % (open_ear, threshold))
                    session_start = time.time()
            else:
                # ---- Detection phase ----
                if ear < threshold:
                    was_closed = True
                    if eyes_closed_since is None:
                        eyes_closed_since = now
                    closed_for = now - eyes_closed_since
                    status, color = "Eyes closed", (0, 165, 255)
                    if closed_for >= CLOSED_SECONDS:
                        status, color = "DROWSY! WAKE UP!", (0, 0, 255)
                        if now - last_alarm > ALARM_COOLDOWN:
                            play_alarm()
                            last_alarm = now
                            drowsy_events += 1
                else:
                    if was_closed and eyes_closed_since is not None:
                        if now - eyes_closed_since < CLOSED_SECONDS:
                            blink_count += 1
                    was_closed = False
                    eyes_closed_since = None
                    status, color = "Alert", (0, 200, 0)
        else:
            eyes_closed_since = None
            was_closed = False

        cv2.putText(frame, status, (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)

        if threshold is not None:
            mins = (time.time() - session_start) / 60
            info = "Blinks: %d  Drowsy: %d  Time: %.1f min" % (
                blink_count, drowsy_events, mins)
            cv2.putText(frame, info, (10, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if drowsy_events >= BREAK_AFTER_EVENTS:
            cv2.putText(frame, "Take a 5 min break!", (10, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)

        cv2.imshow("Drowsiness Alert v2", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if threshold is not None:
        duration_min = (time.time() - session_start) / 60
        save_report(duration_min, blink_count, drowsy_events, threshold)


if __name__ == "__main__":
    main()
