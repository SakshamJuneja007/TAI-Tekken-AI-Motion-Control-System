# 🥊 TAI — Tekken AI Motion Intelligence Engine

### Real-Time Human Motion → Intent Understanding → Combat Execution

TAI (Tekken AI) is an experimental AI system that translates human body movements into intelligent in-game actions using **Computer Vision**, **Machine Learning**, **Temporal Reasoning**, and **Combat Decision-Making**.

Unlike traditional gesture-control systems that directly map gestures to keyboard inputs, TAI uses a layered architecture that attempts to understand the player's **intent** before selecting and executing a combat action.

---

## 🎯 Project Goal

Most gesture-controlled game systems follow a simple approach:

```text
Punch → Key 1
Kick → Key 2
```

TAI instead follows:

```text
Human Motion
    ↓
Action Detection
    ↓
Intent Prediction
    ↓
Combat Reasoning
    ↓
Move Selection
    ↓
Game Execution
```

This enables the system to reason about **what the player is trying to do**, rather than reacting to individual gestures alone.

---

## 🏗️ System Architecture

```text
┌───────────────────────┐
│ Webcam Input          │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ MediaPipe Pose        │
│ Landmark Extraction   │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Motion Analysis       │
│ Velocity Estimation   │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Atomic Action         │
│ Detection             │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Action Buffer         │
│ Temporal Memory       │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Intent Predictor      │
│ LSTM Neural Network   │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Combat Resolver       │
│ Decision Layer        │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Move Brain            │
│ Move Selection Engine │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Executor              │
│ Keyboard Emulation    │
└───────────────────────┘
```

---

## 🚀 Features

### 👁️ Computer Vision

- Real-time pose tracking using MediaPipe
- Landmark extraction and processing
- Motion velocity estimation
- Directional movement detection

### 🎮 Action Recognition

- Punch detection
- Kick detection
- Forward movement detection
- Backward movement detection
- Crouch detection
- Composite action analysis

### 🧠 Temporal Intelligence

- Action buffering
- Temporal sequence analysis
- Context-aware interpretation
- Intent prediction from action history

### 🤖 Machine Learning

- LSTM-based intent classification
- Sequence modelling
- Synthetic training data generation
- Multi-class combat intent prediction

**Supported Intents**

- PRESSURE
- AGGRESSIVE
- LOW_ATTACK
- LAUNCHER
- MOVEMENT
- DEFENSIVE
- IDLE

### ⚔️ Combat Intelligence

- Intent-driven move selection
- Combat resolver layer
- Move categorization
- Dynamic move execution

### ⌨️ Game Integration

- Keyboard emulation
- Automated move execution
- Real-time gameplay interaction

---

## 📊 Training Pipeline

A major challenge was the absence of publicly available datasets that map human body movements directly to Tekken actions.

To overcome this limitation:

1. Tekken move data was extracted and structured.
2. Combat moves were converted into motion-oriented labels.
3. Synthetic action sequences were generated programmatically.
4. An LSTM model was trained on the generated dataset.
5. The trained model predicts player intent from detected action sequences.

This allowed rapid experimentation without requiring expensive motion-capture datasets.

---

## 🛠️ Tech Stack

| Category | Technology |
|-----------|-----------|
| Language | Python |
| Computer Vision | OpenCV, MediaPipe |
| Machine Learning | TensorFlow, Keras |
| Numerical Computing | NumPy |
| Input Automation | pynput |
| UI / Visualization | OpenCV Rendering |

---

## 📈 Example Pipeline Output

```text
Detected Actions:
[CROUCH, LEFT_PUNCH]

Predicted Intent:
LOW_ATTACK (97.9%)

Selected Move:
Dragon Uppercut to Spinning Low Kick

Executed Inputs:
Forward → Down → Punch → Kick
```

---

## ⚠️ Current Challenges

The project is currently in the research and prototyping phase.

Known limitations include:

- Webcam quality affects tracking accuracy
- Continuous state spam (e.g., repeated crouch detection)
- Limited diagonal input support
- Synthetic-to-real data gap
- Standing-player assumption
- No direct game-state awareness

These challenges are part of ongoing development and experimentation.

---

## 🔮 Future Improvements

### Short-Term

- State-transition based action detection
- Improved move diversity
- Better action filtering
- Diagonal input support
- Real motion dataset collection

### Mid-Term

- Transformer-based intent prediction
- Combo planning engine
- Reinforcement learning assisted move selection
- Context-aware combat strategies

### Long-Term

- Full-body motion intelligence engine
- Adaptive player modelling
- Vision-based game-state understanding
- Autonomous combat agent

---

## 🎓 Learning Outcomes

This project explores how multiple AI domains can be combined into a single real-time system:

- Computer Vision
- Human Motion Analysis
- Sequence Modelling
- Intent Recognition
- Decision Systems
- Intelligent Agents
- Real-Time AI Pipelines

---

## 💡 Why This Project Exists

TAI was built to explore how human motion can be transformed into higher-level intent and converted into intelligent game actions.

Rather than creating a simple gesture-to-key mapper, the objective was to build a complete:

**Perception → Reasoning → Decision → Execution**

pipeline capable of operating in real time.

---


## Installation

```bash
git clone https://github.com/SakshamJuneja007/TAI.git

cd TAI

pip install -r requirements.txt
```

Run:

```bash
python run_tai.py
```
## Why This Project Is Interesting

Most gesture-control systems directly map gestures to keyboard inputs.

TAI instead uses a layered AI pipeline:

Motion → Actions → Intent → Combat Reasoning → Move Selection → Execution

This architecture separates perception, reasoning, and execution, making the system extensible to future applications such as:

- Sports coaching
- Physical therapy
- Sign language recognition
- Human-computer interaction

## 👨‍💻 Author

**Saksham Juneja**

B.Tech — Artificial Intelligence & Machine Learning

**Areas of Interest**
- Computer Vision
- Machine Learning
- Intelligent Agents
- Real-Time AI Systems
- Human-AI Interaction

---

⭐ If you found this project interesting, consider giving it a star.
