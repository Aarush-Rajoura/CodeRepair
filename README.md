# Automated Code Corrector

An end-to-end, LLM- and RL-powered pipeline that automatically detects, repairs, and verifies single-line defects in Python programs (QuixBugs). I combine a transformer-based defect classifier, a strategy mapper, a Gemini-based repair agent orchestrated by an FSM, and a PPO-trained policy to optimize tool selection.

---

## 🚀 Features

- **Defect Classification**  
  Automatically predicts one of 14 common bug classes (off-by-one, wrong operator, missing guard, etc.) using a fine-tuned CodeBERT model.

- **Strategy Mapping**  
  Maps each defect class to a tailored LLM prompt template so the agent focuses on the right kind of repair.

- **LLM Repair Agent + Tools**  
  Uses an LLM (e.g. Google Gemini) as an agent with developer-like tools:  
  - `READCODE(file, range)`  
  - `RUNTESTS()`  
  - `SEARCHCODE(query)`  
  - `APPLYPATCH(patch)`  
  - `FINISH()`

- **Finite State Machine (FSM)**  
  Organizes the repair workflow into states:  
  **Understand → Collect → Attempt Fix → Validate → Done**.

- **PPO-Based RL Policy**  
  Learns which tool to invoke in each FSM state to minimize wasted LLM calls and maximize successful repairs.

- **Test-Driven Repair**  
  Each candidate fix is automatically validated against the provided test harness (`tester.py`).

---

## 📂 Repository Structure

```plaintext
.
├── README.md                     ← (this file)
├── LICENSE
├── config/                       ← Experiment / hyperparameter configs
│   └── classifier_config.json
├── data/
│   └── quixbugs/                 ← QuixBugs code & testcases
├── defect_classifier_model/      ← Tokenizer + model files
│   ├── config.json
│   ├── merges.txt
│   ├── special_tokens_map.json
│   ├── tokenizer_config.json
│   └── vocab.json
│   └── model.safetensors         ← (optional: large weights via Git LFS)
├── src/
│   ├── classifier.py             ← CodeBERT-based defect classifier
│   ├── strategy_router.py        ← Maps defect class → tool sequence & prompt
│   ├── fsm.py                    ← RepairAgent finite‐state machine
│   ├── middleware.py             ← LLM-to-tool invocation & prompt management
│   ├── rl_env.py                 ← Gym environment wrapping FSM + tools
│   ├── train_rl.py               ← PPO training script
│   ├── evaluate.py               ← Evaluation harness over QuixBugs
│   └── tools.py                  ← Implements `READCODE`, `RUNTESTS`, etc.
├── logs/                         ← Training & evaluation logs
├── models/
│   ├── defect_clf.pt             ← (optional) Classifier weights
│   └── ppo_policy.zip            ← (optional) Trained PPO policy
└── utils.py                      ← Helper functions (diff, comparison, etc.)
```

---

## 🔧 Prerequisites:

- `Python 3.8+`

- `pip install -r requirements.txt`

---

## ⚙️ Installation

- **Clone the repo**

```
git clone https://github.com/yourusername/auto-code-corrector.git
cd auto-code-corrector
```

- **Install dependencies**
```
pip install --upgrade pip
pip install -r requirements.txt
```

- **Download QuixBugs data**
  - `Place the Python programs in data/quixbugs/python_programs/ and their test JSON files in data/quixbugs/json_testcases/.`

---

## ▶️ Usage

- **1.Evaluate on QuixBugs**
  ```
  python src/evaluate.py
  ```
- **2.Train the RL Policy (PPO)**
  ```
  python src/train_rl.py

  ```

- **3.Repair a Single File**
  ```
  python src/repair_single.py \
  --code data/quixbugs/python_programs/bitcount.py \
  --tests data/quixbugs/json_testcases/bitcount.json

  ```

---

## 📋 Configuration
- `config/classifier_config.json: Hyperparameters for defect classifier training.`

- `src/train_rl.py: Adjust RL hyperparameters (learning rate, batch size, discount factor).`

- `src/tools.py: Path to tester.py and code directories.`

---

## 📜 License
This project is released under the MIT License.

