# Behold-Urwar-Droid-Concepts (BUDC)

This guide provides detailed instructions and best practices for unifying the **Duck Droid** build ecosystem. It integrates multiple submodules, presents a unified user interface, and explains how to generate reference motion, train ONNX policies, and deploy them onto Jetson Orin Nano boards.

---

## Table of Contents
1. [Introduction](#introduction)
2. [Repository Overview](#repository-overview)
3. [Submodules](#submodules)
4. [Features & Implementation](#features--implementation)
   - [Generate Reference Motion](#generate-reference-motion)
   - [Train ONNX Policies](#train-onnx-policies)
   - [SSH/USB Deployment](#sshusb-deployment)
   - [Open Playground](#open-playground)
   - [Record User Actions](#record-user-actions)
   - [View Training Outputs](#view-training-outputs)
   - [Educational Content](#educational-content)
5. [End-to-End Policy Creation & Deployment](#end-to-end-policy-creation--deployment)
6. [Repository Improvements](#repository-improvements)
   - [Unify Submodules](#unify-submodules)
   - [Single Config File](#single-config-file)
   - [Automated Setup](#automated-setup)
   - [Continuous Integration](#continuous-integration)
7. [Appendix](#appendix)

---

## Introduction

The **Behold-Urwar-Droid-Concepts (BUDC)** repository aims to centralize development for our Duck Droid builds. It ties together:
- **Reference motion generation** (via [Open_Duck_reference_motion_generator](https://github.com/apirrone/Open_Duck_reference_motion_generator))
- **Training pipeline** (via [AWD](https://github.com/rimim/AWD) or equivalent)
- **Front-end web app** with Flask and Python
- **Simulated playground** (via [Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground))
- **Physical robot deployment** (running on Jetson Orin Nano boards)

---

## Repository Overview

- **Technologies**: Python, Flask, ONNX, Jetson Orin Nano (for hardware deployment).
- **Goals**:
  1. Present a user-friendly web interface for generating reference motions, training them, and deploying to real droids.
  2. Provide an educational environment where users can learn how each submodule fits together.

---

## Submodules

We recommend adding and managing your submodules under a single `submodules/` folder in this repository. For instance:
```
submodules/
   Open_Duck_Mini/
   Open_Duck_Playground/
   AWD/
   Open_Duck_reference_motion_generator/
```
Initialize and update them with:
```bash
git submodule add <repo-link> submodules/<submodule-name>
git submodule update --init --recursive
```

---

## Features & Implementation

### Generate Reference Motion

1. **Submodule**: [Open_Duck_reference_motion_generator](https://github.com/apirrone/Open_Duck_reference_motion_generator)
2. **Steps**:
   - Add a Flask route (e.g., `/generate_reference_motion`) to call the generation script.
   - Provide a button in your Flask front-end to trigger this route.
   - Display success/failure messages.

```python
@app.route('/generate_reference_motion', methods=['GET'])
def generate_reference_motion():
    result = subprocess.run(['python', 'generate_motion.py'], capture_output=True, text=True)
    if result.returncode == 0:
        return f"Reference motion generated successfully! {result.stdout}"
    else:
        return f"Error: {result.stderr}", 500
```

### Train ONNX Policies

1. **Submodule**: [AWD](https://github.com/rimim/AWD)
2. **Steps**:
   - Add a Flask route (e.g., `/train_policy`) to call the training script.
   - Pass user-set parameters (epochs, etc.) from a form or config.
   - Export the trained model to `.onnx`.

```python
@app.route('/train_policy', methods=['POST'])
def train_policy():
    epochs = request.form.get('epochs', 10)
    cmd = [
        'python', 'train.py',
        '--data_dir', 'reference_motion_data/',
        '--epochs', str(epochs),
        '--output_onnx', 'trained_models/droid_policy.onnx'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return "ONNX policy trained successfully!"
    else:
        return f"Error: {result.stderr}", 500
```

### SSH/USB Deployment

Allow users to select and upload a trained `.onnx` file to the Jetson Orin Nano via SSH or direct USB.

```python
import paramiko

@app.route('/upload_model', methods=['POST'])
def upload_model():
    model_filename = request.form.get('model_filename', 'droid_policy.onnx')
    jetson_ip = request.form.get('jetson_ip', '192.168.1.10')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(jetson_ip, username='jetson', password='password')

    sftp = ssh.open_sftp()
    sftp.put(f"./trained_models/{model_filename}", f"/home/jetson/models/{model_filename}")
    sftp.close()
    ssh.close()

    return f"Uploaded {model_filename} to {jetson_ip}."
```

### Open Playground

1. **Submodule**: [Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground)
2. **Steps**:
   - Add a route (e.g., `/launch_playground`) that starts the Playground server.
   - Provide a button in the Flask UI to launch or open the Playground interface.

```python
@app.route('/launch_playground', methods=['GET'])
def launch_playground():
    subprocess.Popen(['python', 'submodules/Open_Duck_Playground/playground_server.py'])
    return "Playground launched!"
```

### Record User Actions

Record keyboard inputs in the Playground and save them as JSON or CSV to be used for new training runs.

```javascript
document.addEventListener('keydown', (event) => {
  // Convert event.key into motion data
  // Append motion data to a session array
});

function saveRecording() {
  fetch('/save_playground_recording', {
    method: 'POST',
    body: JSON.stringify(sessionData),
    headers: { 'Content-Type': 'application/json' }
  });
}
```

```python
@app.route('/save_playground_recording', methods=['POST'])
def save_playground_recording():
    data = request.get_json()
    filename = f"playground_recordings/recording_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump(data, f)
    return f"Recording saved to {filename}"
```

### View Training Outputs

Provide a route (e.g., `/training_results`) to display logs, metrics, and final `.onnx` files in a user-friendly format.

```python
@app.route('/training_results', methods=['GET'])
def training_results():
    results_dir = './training_outputs'
    files = os.listdir(results_dir)
    return render_template('training_results.html', files=files)
```

### Educational Content

Add an `/education` route and page with explanations of how each submodule ties into the system, along with relevant robotics/controls knowledge.

---

## End-to-End Policy Creation & Deployment

1. **Reference Motion Generation**  
   - Use `Open_Duck_reference_motion_generator` or record user actions from the Playground.

2. **Model Training**  
   - Run your training script (e.g., from AWD).  
   - Export to `.onnx`.

3. **Deployment**  
   - Transfer the `.onnx` file to Jetson Orin Nano via SSH/USB.  
   - Use ONNX Runtime or TensorRT for inference:
     ```python
     import onnxruntime as ort
     session = ort.InferenceSession("droid_policy.onnx")
     ```

---

## Repository Improvements

### Unify Submodules

Keep them all in `submodules/`:
```bash
git submodule add https://github.com/apirrone/Open_Duck_Mini.git submodules/Open_Duck_Mini
```

### Single Config File

Use a `.env`, `.toml`, or `config.yaml` file for easy updates.

```yaml
jetson:
  ip: 192.168.1.10
  user: jetson
  pass: password

training:
  epochs: 10
  learning_rate: 0.001
```

### Automated Setup

Create a script or Makefile that runs:
```bash
git submodule update --init --recursive
pip install -r requirements.txt
```

### Continuous Integration

(Optional) Use GitHub Actions or similar to run tests and check submodules for consistent integration.

---

## Appendix

- [Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini)
- [Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground)
- [AWD](https://github.com/rimim/AWD)
- [Open_Duck_reference_motion_generator](https://github.com/apirrone/Open_Duck_reference_motion_generator)
- [Behold-Urwar-Droid-Concepts (BUDC)](https://github.com/Aronnaxx/Behold-Urwar-Droid-Concepts)
