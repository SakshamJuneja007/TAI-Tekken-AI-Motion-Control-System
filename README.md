# 🥊 TAI — Tekken AI Motion Intelligence Engine

### Real-Time Human Motion → Intent Prediction → Combat Execution

TAI is an experimental AI system that converts human body movements into intelligent Tekken actions using a multi-stage perception and reasoning pipeline.

Instead of directly mapping gestures to keyboard inputs, TAI attempts to understand **player intent** before selecting and executing a combat move.

Built as an exploration of:

- Computer Vision
- Human Motion Analysis
- Temporal Sequence Modeling
- Intent Recognition
- Decision Systems
- Real-Time AI Pipelines

---

## 🚀 What Makes TAI Different?

Most gesture-controlled systems work like this:

```text
Punch  → Key 1
Kick   → Key 2
Crouch → Key Down
```

TAI introduces an additional reasoning layer:

```text
Human Motion
      ↓
Atomic Actions
      ↓
Temporal Memory
      ↓
Intent Prediction
      ↓
Combat Reasoning
      ↓
Move Selection
      ↓
Game Execution
```

Instead of reacting to individual gestures, the system attempts to infer:

> "What is the player trying to do?"

and then chooses an appropriate combat action.

---

# 🏗️ System Architecture

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
│ LSTM Intent Predictor │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Combat Resolver       │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Move Brain            │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Executor              │
│ Keyboard Emulation    │
└───────────────────────┘
```

---

# ⚙️ Core Components

## 👁️ Perception Layer

Real-time motion capture using:

- OpenCV
- MediaPipe Pose
- Landmark Tracking
- Velocity Estimation

Detected actions include:

- Left Punch
- Right Punch
- Kicks
- Forward Movement
- Backward Movement
- Crouch
- Composite Movements

---

## 🧠 Temporal Intelligence Layer

Unlike frame-by-frame gesture systems, TAI maintains short-term memory.

Features:

- Action Buffer
- Temporal Context
- Sequence Analysis
- Event History Tracking

Example:

```text
Punch
↓
Punch
↓
Forward
↓
Kick

≠

Single Punch Detection
```

The order of actions matters.

---

## 🤖 Intent Prediction Layer

An LSTM neural network analyzes recent action sequences and predicts high-level combat intent.

Supported intents:

```text
PRESSURE
AGGRESSIVE
LOW_ATTACK
LAUNCHER
MOVEMENT
DEFENSIVE
IDLE
```

Example:

```text
Detected Actions:
[CROUCH, LEFT_PUNCH]

↓

Predicted Intent:
LOW_ATTACK
```

---

## ⚔️ Combat Intelligence Layer

Once an intent is predicted:

1. Combat Resolver validates intent confidence
2. Move Brain searches suitable moves
3. Candidate moves are filtered
4. A move is selected for execution

Example:

```text
Intent:
LOW_ATTACK

↓

Selected Move:
Dragon Uppercut to Spinning Low Kick
```

---

## ⌨️ Execution Layer

The selected move is converted into game inputs and executed through keyboard emulation.

Example:

```text
Move:
Dragon Uppercut to Spinning Low Kick

↓

Inputs:
Forward → Down → Punch → Kick
```

---

# 📊 Training Pipeline

One of the biggest challenges was the lack of publicly available datasets linking human body motion directly to Tekken actions.

To overcome this:

### Step 1

Extracted and structured Tekken move data.

### Step 2

Converted move notation into motion-oriented action labels.

### Step 3

Generated synthetic combat sequences.

### Step 4

Created a labeled intent dataset.

### Step 5

Trained an LSTM sequence model.

This allowed rapid experimentation without requiring expensive motion-capture hardware or large-scale data collection.

---

# 🛠️ Tech Stack

| Category | Technology |
|-----------|-----------|
| Language | Python |
| Computer Vision | OpenCV, MediaPipe |
| Deep Learning | TensorFlow / Keras |
| Numerical Computing | NumPy |
| Input Automation | pynput |
| Motion Processing | Custom Velocity Engine |
| Sequence Modeling | LSTM |

---

# 📂 Project Structure

```text
vision/
 ├── detector.py
 ├── mediapipe_processor.py
 └── velocity.py

core/
 ├── buffer.py
 ├── models.py
 └── notation.py

intelligence/
 ├── intents.py
 ├── predictor.py
 ├── move_brain.py
 └── combat.py

combat/
 ├── executor.py
 ├── resolver.py
 └── jin_moves.json

ml/
 ├── dataset.py
 └── intent_model.py
```

---

# 📈 Example Runtime Output

```text
FPS: 30

Detected Actions:
CROUCH
LEFT_PUNCH

Intent:
LOW_ATTACK (97.9%)

Selected Move:
Dragon Uppercut to Spinning Low Kick

Executed Inputs:
Forward → Down → Punch → Kick
```

---

# ⚠️ Current Limitations

TAI is currently a research prototype.

Known issues:

- Webcam quality impacts tracking accuracy
- Continuous state spam (repeated crouch events)
- Limited diagonal input handling
- Synthetic-to-real data gap
- Standing-player assumption
- No game-state awareness

---

# 🔮 Future Roadmap

## Near-Term

- State transition detection
- Better move diversity
- Improved action filtering
- Full diagonal input support
- Real-world motion dataset collection

## Mid-Term

- Transformer-based intent prediction
- Combo planning engine
- Context-aware combat logic
- Reinforcement learning assisted move selection

## Long-Term

- Vision-based game-state understanding
- Adaptive player modeling
- Full-body motion intelligence
- Autonomous combat agent

---

# 🎓 Key Engineering Concepts Demonstrated

This project combines multiple AI disciplines into a single real-time system:

- Computer Vision
- Motion Analysis
- Deep Learning
- Sequence Modeling
- Intent Recognition
- Decision Systems
- Human-Computer Interaction
- Real-Time Inference Pipelines

---

# 💻 Installation

```bash
git clone https://github.com/SakshamJuneja007/TAI-Tekken-AI-Motion-Control-System.git

cd TAI-Tekken-AI-Motion-Control-System

pip install -r requirements.txt
```

Run:

```bash
python run_tai.py
```

---

# 👨‍💻 Author

## Saksham Juneja

B.Tech — Artificial Intelligence & Machine Learning

### Interests

- Computer Vision
- Machine Learning
- Intelligent Agents
- Real-Time AI Systems
- Human-AI Interaction

---

## ⭐ Support

If you found this project interesting, consider giving it a star.

It helps others discover the project and supports future development.
