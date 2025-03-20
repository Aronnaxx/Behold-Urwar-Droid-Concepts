// Workflow state management
let currentStep = 1;
let generatedMotions = [];
let trainedModels = [];

// DOM Elements
const motionForm = document.getElementById('motion-form');
const trainingForm = document.getElementById('training-form');
const testingForm = document.getElementById('testing-form');
const motionTypeSelect = document.getElementById('motion-type');
const walkParams = document.getElementById('walk-params');
const motionPreview = document.getElementById('motion-preview');
const trainingProgress = document.getElementById('training-progress');
const playgroundViewer = document.getElementById('playground-viewer');

// Event Listeners
motionTypeSelect.addEventListener('change', toggleMotionParams);
motionForm.addEventListener('submit', handleMotionGeneration);
trainingForm.addEventListener('submit', handleTraining);
testingForm.addEventListener('submit', handleTesting);

// Toggle motion parameters based on motion type
function toggleMotionParams() {
    walkParams.style.display = motionTypeSelect.value === 'walk' ? 'block' : 'none';
}

// Handle motion generation
async function handleMotionGeneration(e) {
    e.preventDefault();
    const formData = new FormData(motionForm);
    const data = Object.fromEntries(formData.entries());
    
    try {
        updateStepStatus(1, 'Generating motion...', 'info');
        const response = await fetch('/workflow/generate-motion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate motion');
        }
        
        const result = await response.json();
        generatedMotions.push(result.motion_file);
        updateReferenceMotionSelect();
        
        // Display motion preview
        displayMotionPreview(result.motion_file);
        
        updateStepStatus(1, 'Motion generated successfully!', 'success');
        enableStep(2);
    } catch (error) {
        console.error('Error generating motion:', error);
        updateStepStatus(1, 'Failed to generate motion', 'error');
    }
}

// Handle training
async function handleTraining(e) {
    e.preventDefault();
    const formData = new FormData(trainingForm);
    const data = Object.fromEntries(formData.entries());
    
    try {
        updateStepStatus(2, 'Starting training...', 'info');
        const response = await fetch('/workflow/train', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to start training');
        }
        
        const result = await response.json();
        pollTrainingStatus(result.task_id);
    } catch (error) {
        console.error('Error starting training:', error);
        updateStepStatus(2, 'Failed to start training', 'error');
    }
}

// Poll training status
async function pollTrainingStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/workflow/status/${taskId}`);
            if (!response.ok) {
                throw new Error('Failed to get training status');
            }
            
            const result = await response.json();
            updateTrainingProgress(result.progress);
            
            if (result.status === 'completed') {
                clearInterval(interval);
                trainedModels.push(result.model_file);
                updateTrainedModelSelect();
                updateStepStatus(2, 'Training completed successfully!', 'success');
                enableStep(3);
            } else if (result.status === 'failed') {
                clearInterval(interval);
                updateStepStatus(2, 'Training failed', 'error');
            }
        } catch (error) {
            console.error('Error polling training status:', error);
            clearInterval(interval);
            updateStepStatus(2, 'Failed to get training status', 'error');
        }
    }, 1000);
}

// Handle testing
async function handleTesting(e) {
    e.preventDefault();
    const formData = new FormData(testingForm);
    const data = Object.fromEntries(formData.entries());
    
    try {
        updateStepStatus(3, 'Loading model in playground...', 'info');
        const response = await fetch('/workflow/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to load model in playground');
        }
        
        const result = await response.json();
        displayPlaygroundViewer(result.playground_url);
        
        updateStepStatus(3, 'Model loaded in playground!', 'success');
    } catch (error) {
        console.error('Error loading model in playground:', error);
        updateStepStatus(3, 'Failed to load model in playground', 'error');
    }
}

// Update step status
function updateStepStatus(step, message, type) {
    const statusElement = document.getElementById(`step${step}-status`);
    statusElement.textContent = message;
    statusElement.className = `step-status ${type}`;
}

// Enable step
function enableStep(step) {
    const stepElement = document.getElementById(`step${step}`);
    stepElement.classList.add('enabled');
}

// Update reference motion select
function updateReferenceMotionSelect() {
    const select = document.getElementById('reference-motion');
    select.innerHTML = generatedMotions.map(motion => 
        `<option value="${motion}">${motion}</option>`
    ).join('');
}

// Update trained model select
function updateTrainedModelSelect() {
    const select = document.getElementById('trained-model');
    select.innerHTML = trainedModels.map(model => 
        `<option value="${model}">${model}</option>`
    ).join('');
}

// Display motion preview
function displayMotionPreview(motionFile) {
    // Implementation depends on how motion previews are rendered
    // This could be a 3D viewer, animation, or other visualization
    motionPreview.innerHTML = `<div class="preview-placeholder">Motion preview for ${motionFile}</div>`;
}

// Update training progress
function updateTrainingProgress(progress) {
    trainingProgress.innerHTML = `
        <div class="progress">
            <div class="progress-bar" role="progressbar" 
                 style="width: ${progress}%" 
                 aria-valuenow="${progress}" 
                 aria-valuemin="0" 
                 aria-valuemax="100">
                ${progress}%
            </div>
        </div>
    `;
}

// Display playground viewer
function displayPlaygroundViewer(playgroundUrl) {
    playgroundViewer.innerHTML = `
        <iframe src="${playgroundUrl}" 
                width="100%" 
                height="600px" 
                frameborder="0" 
                allowfullscreen>
        </iframe>
    `;
} 