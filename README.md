# 🧠 AI-Powered Anomaly-Based Web Application Firewall (WAF)

> 🚀 **An intelligent Transformer-based WAF that detects never-seen-before attacks using anomaly detection — not outdated signature lists.**

---

## 🌍 Overview

Traditional Web Application Firewalls (WAFs) rely on static, rule-based detection that struggles against **zero-day exploits** or novel attack vectors.  
This project introduces an **AI-powered, anomaly-based WAF** that **learns what normal traffic looks like** — and flags anything that doesn’t fit.

Instead of relying on blacklists, it uses a **Transformer model (DistilBERT)** to understand and model the *structure of legitimate web requests*.  
Any request that deviates significantly from this learned pattern is considered *anomalous* and potentially malicious.

---

## 🎯 Main Objective

To build a self-learning Web Application Firewall that:
- Learns normal user traffic from web logs.
- Detects abnormal requests (like SQLi, XSS, or bot probing).
- Flags high-risk anomalies in real time.
- Adapts continuously to changing attack vectors.

---

## ✨ Core Concept: “Loss as an Anomaly Score”

The brilliance of this system lies in how it uses **language modeling loss** as a measure of *weirdness*.

### 🧩 Training Phase (`train.py`)
The model is trained on **benign logs** using a **Masked Language Modeling (MLM)** task:
- 15% of tokens are masked.
- The model predicts the missing parts.
- After several epochs, it learns the structure of legitimate requests.

### ⚡ Detection Phase (`detect.py`)
When a new request arrives:
- It’s normalized and fed into the trained model.
- The model computes how *confident* it is in predicting the structure.
- The **loss (anomaly score)** indicates how “normal” or “suspicious” the request is.

| Request Example | Description | Anomaly Score |
|-----------------|--------------|----------------|
| `GET /categories` | Seen many times — normal | 🟢 Low |
| `GET /login.php?user=' OR 1=1 --` | Bizarre pattern — possible attack | 🔴 High |

---

## ⚙️ System Workflow

### 1️⃣ **Log Collection (Nginx)**
**File:** `nginx.conf`  
**Purpose:** Acts as a reverse proxy that captures *all incoming web traffic.*

🔹 Key Features:
- Custom `waf_json` log format.  
- Structured **JSON logging** (request method, URI, headers, body).  
- Includes `$request_body` for POST data inspection.  

---

### 2️⃣ **Data Normalization**
**File:** `normalize.py`  
**Purpose:** Cleans raw logs and replaces user-specific data with placeholders.

🔹 Example Transformations:
GET /recipe?search_query=chicken → GET /recipe?search_query=<STR>
{"phone_number": "+919123456789"} → {"phone_number": "<PHONE>"}
This ensures the model focuses on **structure**, not sensitive or variable data.

---

### 3️⃣ **Benign Traffic Generation**
**File:** `generate_traffic.py`  
**Purpose:** Simulates *legitimate user behavior* to generate baseline training data.

🔹 Simulated Actions:
- Browsing categories  
- Searching recipes  
- Signing up / logging in  
These logs form the foundation for learning “normal” web behavior.

---

### 4️⃣ **Model Training**
**File:** `train.py`  
**Purpose:** Fine-tunes **DistilBERT** on clean, normalized traffic logs.

🔹 Highlights:
- Uses `distilbert-base-uncased` from Hugging Face.
- Automatically performs MLM (Masked Language Modeling).
- Trains over multiple epochs.
- Saves trained weights to `./waf_model`.

📦 Output:
A specialized Transformer model that understands **normal request patterns**.

---

### 5️⃣ **Real-Time Anomaly Detection**
**File:** `detect.py`  
**Purpose:** Continuously monitors live traffic and flags anomalies in real time.

🔹 Key Features:
- Tails Nginx logs via Docker (`tail -F`).
- Normalizes and scores each request.
- Compares against a configurable `ANOMALY_THRESHOLD`.

⚠️ Example Output:
🚨 ANOMALY DETECTED 🚨
Timestamp: 2025-10-22 12:45:23
Request: GET /login.php?user=' OR 1=1 --
Anomaly Score: 0.987 (Threshold: 0.600)

---

## 🧰 Tech Stack

| Layer | Technology |
|--------|-------------|
| **Model** | 🤖 DistilBERT (Transformer-based Language Model) |
| **Web Server** | 🧱 Nginx (Reverse Proxy + JSON Logs) |
| **Preprocessing** | 🧹 Regex-based Normalization |
| **Training & Detection** | 🐍 Python, Hugging Face Transformers |
| **Runtime** | 🐳 Docker for isolation & log streaming |

---

## 🚀 Project Workflow Summary

```mermaid
flowchart TD
A[🌐 Web Requests] --> B[Nginx Reverse Proxy]
B --> C[📜 JSON Log Output]
C --> D[🧹 normalize.py]
D --> E[🧪 train.py - DistilBERT Fine-tuning]
E --> F[🧠 waf_model]
F --> G[⚡ detect.py - Real-Time Scoring]
G --> H{Anomaly Score > Threshold?}
H -->|Yes| I[🚨 Alert: Potential Attack]
H -->|No| J[✅ Safe Traffic]
