"""
TAI — Tekken AI Motion Controller
===================================

OpenCV standalone runner

Pipeline:

Camera
 ↓
MediaPipeProcessor
 ↓
VelocityEstimator
 ↓
AtomicActionDetector
 ↓
ActionBuffer
 ↓
IntentPredictor
 ↓
CombatResolver
 ↓
MoveExecutor
"""

import time
import sys
import logging
from collections import deque
from typing import Optional

import cv2


from vision.mediapipe_processor import MediaPipeProcessor
from vision.velocity import VelocityEstimator
from vision.detector import AtomicActionDetector

from core.buffer import ActionBuffer
from core.models import SelectedMove

from intelligence.predictor import IntentPredictor
from intelligence.move_brain import MoveBrain

from combat.resolver import CombatResolver
from combat.executor import MoveExecutor



logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s — %(message)s"
)

logger = logging.getLogger("TAI")



# ---------------- HUD ----------------


_GREY=(160,160,160)
_GREEN=(0,220,80)
_CYAN=(220,220,0)
_ORANGE=(0,160,255)
_BLACK=(0,0,0)

_FONT=cv2.FONT_HERSHEY_SIMPLEX



def text(
    frame,
    msg,
    pos,
    scale,
    color,
    thickness=1
):

    x,y=pos

    cv2.putText(
        frame,
        msg,
        (x+1,y+1),
        _FONT,
        scale,
        _BLACK,
        thickness+1,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        msg,
        (x,y),
        _FONT,
        scale,
        color,
        thickness,
        cv2.LINE_AA
    )




def draw_hud(
    frame,
    fps,
    actions,
    intent,
    move
):

    overlay=frame.copy()

    cv2.rectangle(
        overlay,
        (0,0),
        (420,140),
        (20,20,20),
        -1
    )


    cv2.addWeighted(
        overlay,
        .55,
        frame,
        .45,
        0,
        frame
    )


    text(
        frame,
        f"FPS: {fps:.0f}",
        (10,22),
        .55,
        _GREY
    )


    act=" ".join(
        [
            a.action.name
            for a in actions
        ]
    )

    text(
        frame,
        "ACTIONS: "+act,
        (10,55),
        .5,
        _GREEN
    )


    if intent:

        text(
            frame,
            f"INTENT: {intent.intent.name}",
            (10,85),
            .55,
            _CYAN
        )


    if move:

        text(
            frame,
            f"MOVE: {move.name}",
            (10,120),
            .65,
            _ORANGE
        )




class FPSCounter:

    def __init__(self):

        self.last=time.time()
        self.buffer=deque(maxlen=30)


    def tick(self):

        now=time.time()

        self.buffer.append(
            now-self.last
        )

        self.last=now

        if not self.buffer:
            return 0

        return 1/sum(self.buffer)*len(self.buffer)




def run(
    camera_index=0,
    model_path="models/intent_brain.pth"
):


    logger.info(
        "Initialising pipeline ..."
    )


    # -------- vision --------


    mp_processor=MediaPipeProcessor(
        min_detection_confidence=.6,
        min_tracking_confidence=.5
    )


    velocity=VelocityEstimator()

    detector=AtomicActionDetector()



    # -------- memory --------


    buffer=ActionBuffer()



    # -------- ML --------


    predictor=IntentPredictor(
        model_path=model_path
    )



    # -------- combat --------


    move_brain=MoveBrain()


    resolver=CombatResolver(
        move_brain
    )


    executor=MoveExecutor()




    cap=cv2.VideoCapture(
        camera_index
    )


    if not cap.isOpened():

        print(
            "Camera failed"
        )

        return




    fps_counter=FPSCounter()



    last_actions=[]

    last_intent=None

    last_move=None




    logger.info(
        "Started. ESC quit"
    )




    while True:



        ret,frame=cap.read()


        if not ret:
            continue



        fps=fps_counter.tick()


        frame=cv2.flip(
            frame,
            1
        )



        landmarks,frame=mp_processor.process(
            frame
        )



        if landmarks:



            # velocity

            vel=velocity.update(
                landmarks
            )



            # detect actions

            events=detector.detect(
                landmarks,
                vel
            )



            if events:

                buffer.push_many(
                    events
                )

                last_actions=events




            snapshot=buffer.snapshot()


            sequence=snapshot.action_sequence



            prediction=None



            if sequence:

                try:

                    prediction=predictor.predict(
                        sequence
                    )

                    last_intent=prediction


                    print(
                        "[ML INTENT]",
                        prediction
                    )



                except Exception as e:

                    print(
                        "ML ERROR",
                        e
                    )




            selected=None



            if prediction:

                # FIX: resolver.resolve(snapshot, intent_prediction)
                # snapshot is first, prediction is second — matches resolver signature.
                # Previously these were swapped, causing BufferSnapshot to land in the
                # intent_prediction parameter and crash on intent_prediction.intent.

                try:

                    selected=resolver.resolve(
                        snapshot,
                        prediction
                    )


                    if selected:

                        last_move=selected


                        print(
                            "[MOVE]",
                            selected.name
                        )

                except Exception as e:

                    import traceback
                    print("RESOLVER ERROR:", e)
                    traceback.print_exc()

                # FIX: removed duplicate resolver.resolve() call that was here.
                # It was firing every matched move twice and discarding the result.




            if selected:

                try:

                    executor.execute(
                        selected
                    )

                except Exception as e:

                    print(
                        "EXEC ERROR",
                        e
                    )




        draw_hud(
            frame,
            fps,
            last_actions,
            last_intent,
            last_move
        )
        small = cv2.resize(frame,(640,360))
        cv2.imshow(
            "TAI",small)



        key=cv2.waitKey(1)&0xff



        if key==27:

            break



        if key in [
            ord('r'),
            ord('R')
        ]:

            buffer.clear()

            velocity.reset()

            detector.reset()




    cap.release()

    cv2.destroyAllWindows()

    mp_processor.close()




if __name__=="__main__":


    run()