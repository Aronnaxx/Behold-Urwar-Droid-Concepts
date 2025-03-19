# Simplified Project Overview

## End-to-End Process Chart

```mermaid
graph LR
    A[Clone BUDC Repository] --> B[Initialize Submodules]
    B --> C[Setup Environment]
    
    subgraph "Phase 1: Motion Generation"
        C --> D[Generate Reference Motion]
        D --> E[Fit Polynomials]
        E --> F[Validate Motion]
    end
    
    subgraph "Phase 2: Training Options"
        F --> G1[AWD Training Framework]
        F --> G2[Open Duck Playground Training]
        G1 --> H1[Export AWD ONNX Model]
        G2 --> H2[Export Playground ONNX Model]
    end
    
    subgraph "Phase 3: Validation & Deployment"
        H1 --> I[Test in Playground]
        H2 --> I
        I --> J[Deploy to Robot]
    end

    %% Feedback loops
    I --> F
    J --> I
```

## Quick Start Guide

1. **Clone and Setup**
```bash
# Clone main repository
git clone https://github.com/your-org/BUDC.git
cd BUDC

# Initialize submodules
git submodule update --init --recursive

# Install dependencies
pip install -r requirements.txt
```

2. **Generate Reference Motion**
```bash
# Generate motion
cd submodules/open_duck_reference_motion_generator
uv run scripts/auto_waddle.py --duck open_duck_mini_v2 --num 1 --output_dir ../motion_data

# Fit polynomials
uv run scripts/fit_poly.py --ref_motion ../motion_data/motion_0.json
```

3. **Choose Training Framework**

Option A: AWD Training Framework
```bash
# Train using AWD (Isaac Gym-based)
cd ../awd
python awd/run.py --task DucklingCommand --num_envs 8 \
    --cfg_env awd/data/cfg/open_duck_mini_v2/duckling_command.yaml \
    --cfg_train awd/data/cfg/open_duck_mini_v2/train/amp_duckling_task.yaml \
    --motion_file ../motion_data/motion_0.json

# Export trained model
python export.py --checkpoint runs/latest/model.pt --output ../../trained_models/awd_policy.onnx
```

Option B: Open Duck Playground Training
```bash
# Train using Open Duck Playground (MuJoCo-based)
cd ../open_duck_playground
uv run playground/train.py \
    --motion ../motion_data/motion_0.json \
    --output ../../trained_models/playground_policy.onnx \
    --num_envs 8 \
    --training_steps 1000000
```

4. **Test and Deploy**
```bash
# Test in playground (for either AWD or Playground trained models)
cd ../open_duck_playground
uv run playground/open_duck_mini_v2/mujoco_infer.py -o ../../trained_models/[model_name].onnx

# Deploy to robot
cd ../open_duck_mini
python deploy.py --model ../../trained_models/[model_name].onnx --target raspberrypi.local
```

## Submodule Overview

### 1. Open Duck Reference Motion Generator
**Purpose**: Creates reference motions for training
- Input: Motion parameters (speed, direction, etc.)
- Output: JSON files containing reference motions
- Key Feature: Generates parametric gaits using Placo

### 2. AWD (Adversarial Waddle Dynamics)
**Purpose**: Trains policies using reference motions
- Input: Reference motion JSON files
- Output: Trained ONNX policy models
- Key Feature: Uses Isaac Gym for physics simulation

### 3. Open Duck Playground
**Purpose**: Provides both training and testing capabilities
- Input: Reference motion JSON files (for training) or ONNX policy models (for testing)
- Output: Trained ONNX models or performance metrics/visualizations
- Key Features: 
  - MuJoCo-based physics simulation for training
  - Comprehensive testing environment
  - Visualization tools for motion validation

### 4. Open Duck Mini
**Purpose**: Physical robot implementation
- Input: ONNX policy models
- Output: Robot movements
- Key Feature: Runs on Raspberry Pi Zero 2W

## Data Flow Between Submodules

```mermaid
flowchart LR
    A["Reference Motion Generator"] -- "motion.json" --> B1["AWD Training"]
    A -- "motion.json" --> B2["Playground Training"]
    B1 -- "policy.onnx" --> C["Playground Testing"]
    B2 -- "policy.onnx" --> C
    C -- "validated_policy.onnx" --> D["Robot Deployment"]
    C -- "feedback" --> A

    style A fill:#f9f,stroke:#000000,stroke-width:2px,color:#000000
    style B1 fill:#bbf,stroke:#000000,stroke-width:2px,color:#000000
    style B2 fill:#bbf,stroke:#000000,stroke-width:2px,color:#000000
    style C fill:#bfb,stroke:#000000,stroke-width:2px,color:#000000
    style D fill:#fbb,stroke:#000000,stroke-width:2px,color:#000000
```

## File Format Specifications

### Reference Motion Format
```json
{
    "timesteps": [...],
    "joint_angles": {...},
    "metadata": {
        "speed": 1.0,
        "direction": [0, 1, 0]
    }
}
```

### ONNX Model Requirements
- Input shape: `[batch_size, state_dim]`
- Output shape: `[batch_size, action_dim]`
- State space: Joint angles, velocities, IMU data
- Action space: Joint torques/positions

## Common Integration Points

1. **Motion Generation → Training**
   - Motion files must match both AWD and Playground expected formats
   - Joint names must be consistent across both frameworks
   - Timing must be properly synchronized
   - Choose training framework based on needs:
     - AWD: Better for adversarial training, requires GPU
     - Playground: Simpler setup, MuJoCo-based physics

2. **Training → Playground**
   - ONNX model must match playground's input/output specs
   - State space normalization must be consistent
   - Action space scaling must match

3. **Playground → Robot**
   - Hardware limits must be respected
   - Control frequency must be maintained
   - Safety checks must be implemented

## Best Practices

1. **Motion Generation**
   - Generate diverse motions for robust training
   - Validate joint limits before training
   - Document motion parameters

2. **Training**
   - Start with simple behaviors
   - Use curriculum learning
   - Monitor training metrics

3. **Testing**
   - Test in simulation first
   - Validate edge cases
   - Monitor resource usage

4. **Deployment**
   - Implement safety limits
   - Monitor battery levels
   - Log performance metrics

## Troubleshooting Tips

1. **Motion Generation Issues**
   - Check joint naming consistency
   - Verify motion file format
   - Validate polynomial fitting

2. **Training Problems**
   - Check GPU memory usage
   - Verify motion file paths
   - Monitor reward curves

3. **Deployment Failures**
   - Check network connectivity
   - Verify hardware compatibility
   - Monitor system resources
