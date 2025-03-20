// Reference Motions Handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('motion-form');
    const modeSelect = document.getElementById('mode-select');
    const generationType = document.getElementById('generation-type');
    const singleMotionParams = document.getElementById('single-motion-params');
    const previewSection = document.querySelector('.preview-section');
    const progressBar = document.querySelector('.progress-bar');
    const logOutput = document.querySelector('.log-output');
    const downloadButton = document.getElementById('download-motion');
    let currentMotionData = null;

    // Initialize UI state
    function initializeUI() {
        // Show/hide parameters based on generation type
        generationType.addEventListener('change', function() {
            singleMotionParams.style.display = this.value === 'single' ? 'block' : 'none';
        });

        // Initial state
        singleMotionParams.style.display = generationType.value === 'single' ? 'block' : 'none';
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset UI
        progressBar.style.width = '0%';
        logOutput.innerHTML = '';
        previewSection.style.display = 'none';
        
        try {
            // Show initial progress
            progressBar.style.width = '25%';
            addLogEntry('Starting motion generation process...');
            
            // Submit form data
            const formData = new FormData(form);
            const response = await fetch(`/${duckType}/generate_motion`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error);
            }
            
            // Log each completed step
            if (data.steps_completed) {
                data.steps_completed.forEach((step, index) => {
                    const progress = ((index + 1) / data.steps_completed.length) * 100;
                    progressBar.style.width = `${progress}%`;
                    addLogEntry(step, 'success');
                });
            }
            
            // Store motion data and show preview
            currentMotionData = data.motion_data;
            if (currentMotionData) {
                previewSection.style.display = 'block';
                initializePreview(currentMotionData);
            }
            
            // Log any command output for debugging
            if (data.output) {
                addLogEntry(`Command output: ${data.output}`, 'info');
            }
            
        } catch (error) {
            progressBar.style.width = '100%';
            addLogEntry(`Error: ${error.message}`, 'error');
        }
    });

    // Handle motion download
    downloadButton.addEventListener('click', async function() {
        if (!currentMotionData) return;
        
        try {
            const response = await fetch(`/${duckType}/download_motion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentMotionData)
            });
            
            if (!response.ok) throw new Error('Download failed');
            
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `motion_${new Date().toISOString().slice(0,19).replace(/:/g, '')}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            addLogEntry(`Download error: ${error.message}`, 'error');
        }
    });

    function addLogEntry(message, type = '') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `
            <span class="log-timestamp">[${new Date().toLocaleTimeString()}]</span>
            <span class="log-message">${message}</span>
        `;
        logOutput.appendChild(entry);
        logOutput.scrollTop = logOutput.scrollHeight;
    }

    function initializePreview(motionData) {
        const canvas = document.getElementById('motion-preview');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw preview based on motion data
        if (motionData && motionData.frames) {
            // Calculate scale factors
            const maxX = Math.max(...motionData.frames.map(f => Math.abs(f.position[0])));
            const maxY = Math.max(...motionData.frames.map(f => Math.abs(f.position[1])));
            const scaleX = (canvas.width * 0.8) / (maxX * 2);
            const scaleY = (canvas.height * 0.8) / (maxY * 2);
            const scale = Math.min(scaleX, scaleY);
            
            // Draw motion path
            ctx.beginPath();
            ctx.strokeStyle = '#007bff';
            ctx.lineWidth = 2;
            
            motionData.frames.forEach((frame, i) => {
                const x = canvas.width/2 + frame.position[0] * scale;
                const y = canvas.height/2 + frame.position[1] * scale;
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
        } else {
            // Draw placeholder text if no data
            ctx.fillStyle = '#007bff';
            ctx.textAlign = 'center';
            ctx.fillText('Motion Preview', canvas.width/2, canvas.height/2);
        }
    }

    // Initialize UI when page loads
    initializeUI();
}); 