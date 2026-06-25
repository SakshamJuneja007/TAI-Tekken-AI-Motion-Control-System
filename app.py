"""
TAI — Motion-to-Intent Combat Engine
=====================================

Camera
 ↓
MediaPipe
 ↓
Atomic Actions
 ↓
Action Buffer
 ↓
ML Intent Brain
 ↓
Combat Resolver
 ↓
Executor
"""

import threading
import time
import logging
from pathlib import Path


import streamlit as st
from streamlit_autorefresh import st_autorefresh


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# ============================================================
# WEBRTC
# ============================================================

try:

    from streamlit_webrtc import (
        webrtc_streamer,
        VideoProcessorBase,
        WebRtcMode,
    )

    import av

    WEBRTC_AVAILABLE=True


except Exception as e:

    logger.warning(
        "WebRTC unavailable %s",
        e
    )

    WEBRTC_AVAILABLE=False




# ============================================================
# IMPORTS
# ============================================================


from vision.mediapipe_processor import MediaPipeProcessor
from vision.velocity import VelocityEstimator
from vision.detector import AtomicActionDetector


from core.buffer import ActionBuffer
from core.models import SelectedMove


from configs.constants import Config


from intelligence.predictor import IntentPredictor


from combat.executor import MoveExecutor
from combat.resolver import CombatResolver




# ============================================================
# SHARED STATE
# ============================================================

class SharedState:


    def __init__(self):

        self.lock=threading.Lock()

        self.actions=[]

        self.intent=None

        self.move=None

        self.fps=0

        self.times=[]




    def update(
        self,
        actions,
        intent,
        move
    ):


        now=time.time()


        with self.lock:


            self.actions=actions

            self.intent=intent


            if move:

                self.move=move



            self.times.append(now)

            self.times=self.times[-30:]



            if len(self.times)>2:

                self.fps=(

                    len(self.times)-1

                ) / max(

                    self.times[-1]
                    -
                    self.times[0],

                    0.001
                )





    def get(self):

        with self.lock:

            return (

                self.actions,
                self.intent,
                self.move,
                round(self.fps,1)

            )






# ============================================================
# PIPELINE
# ============================================================

class TAIPipeline:



    def __init__(
        self,
        dry_run=True
    ):



        self.mp=MediaPipeProcessor()


        self.velocity=VelocityEstimator()


        self.detector=AtomicActionDetector()


        self.buffer=ActionBuffer()



        self.predictor=IntentPredictor(

            "models/intent_brain.pth"

        )



        # IMPORTANT
        # Resolver is now the only move selector

        self.resolver=CombatResolver()



        self.executor=MoveExecutor(

            dry_run=dry_run

        )





    # ------------------------------------------------


    def process_frame(
        self,
        frame
    ):



        landmarks,frame=self.mp.process(
            frame
        )



        if landmarks is None:

            return [],None,None





        velocities=self.velocity.update(
            landmarks
        )



        actions=self.detector.detect(

            landmarks,

            velocities

        )



        self.buffer.push_many(
            actions
        )



        snapshot=self.buffer.snapshot()





        # ==========================
        # ML INTENT
        # ==========================

        intent=self.predictor.predict(

            snapshot.action_sequence

        )



        move=None



        if intent:


            logger.info(

                "[INTENT] %s %.2f",

                intent.intent.name,

                intent.confidence

            )



            # ==========================
            # RESOLVER DECIDES MOVE
            # ==========================

            if not self.executor.is_busy:



                move=self.resolver.resolve(

                    intent

                )



                if move:



                    logger.info(

                        "[MOVE] %s",

                        move.name

                    )



                    threading.Thread(

                        target=self.executor.execute,

                        args=(move,),

                        daemon=True

                    ).start()





        return actions,intent,move







# ============================================================
# UI
# ============================================================

def main():



    st.set_page_config(

        page_title=Config.APP_TITLE,

        page_icon="🥷",

        layout="wide"

    )



    st.title(
        "🥷 TAI Motion Combat AI"
    )



    if "shared" not in st.session_state:

        st.session_state.shared=SharedState()



    if "pipeline" not in st.session_state:

        st.session_state.pipeline=TAIPipeline()



    shared=st.session_state.shared

    pipeline=st.session_state.pipeline




    st_autorefresh(

        interval=500,

        key="tai"

    )



    cam,debug=st.columns([2,1])



    with cam:



        if WEBRTC_AVAILABLE:



            class Processor(
                VideoProcessorBase
            ):


                def recv(
                    self,
                    frame
                ):


                    img=frame.to_ndarray(

                        format="bgr24"

                    )


                    actions,intent,move=\
                        pipeline.process_frame(

                            img

                        )



                    shared.update(

                        actions,

                        intent,

                        move

                    )



                    return av.VideoFrame.from_ndarray(

                        img,

                        format="bgr24"

                    )





            webrtc_streamer(

                key="tai-camera",

                mode=WebRtcMode.SENDRECV,

                video_processor_factory=Processor,

                async_processing=True

            )



        else:

            st.error(
                "streamlit-webrtc missing"
            )





    with debug:



        actions,intent,move,fps=shared.get()



        st.metric(
            "FPS",
            fps
        )



        st.write(

            "Actions:",

            [

                a.action.name

                for a in actions

            ]

        )



        if intent:

            st.success(

                f"{intent.intent.name} "
                f"{intent.confidence:.2f}"

            )

        else:

            st.caption(
                "No intent"
            )





        if move:

            st.success(
                move.name
            )

        else:

            st.caption(
                "No move"
            )







if __name__=="__main__":

    main()