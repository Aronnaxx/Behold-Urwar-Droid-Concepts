// Reference Motions Handler
document.addEventListener('DOMContentLoaded', function() {
    console.log("INIT: reference_motions.js loading...");
    const form = document.getElementById('motion-form');
    const modeSelect = document.getElementById('mode-select');
    const generationType = document.getElementById('generation-type');
    const singleMotionParams = document.getElementById('single-motion-params');
    const previewSection = document.querySelector('.preview-section');
    const progressBar = document.querySelector('.progress-bar');
    const logOutput = document.querySelector('.log-output');
    const downloadButton = document.getElementById('download-motion');
    let currentMotionData = null;
    
    // Find the generate motion button
    const generateMotionButton = form ? form.querySelector('button[type="submit"]') : null;
    
    if (generateMotionButton) {
        console.log("DEBUG: Found generate motion button:", generateMotionButton);
    } else {
        console.error("DEBUG: Could not find generate motion button in the form!");
    }

    // Get the current duck type from the URL
    function getCurrentDuckType() {
        const path = window.location.pathname;
        console.log("DEBUG: Getting duck type from path:", path);
        
        // Extract duck type from path
        const pathParts = path.split('/').filter(p => p);
        console.log("DEBUG: Path parts:", pathParts);
        
        if (pathParts.length > 0) {
            const urlDuckType = pathParts[0];
            console.log("DEBUG: Extracted duck type from URL:", urlDuckType);
            
            // Get URL parameters for variant
            const urlParams = new URLSearchParams(window.location.search);
            const variant = urlParams.get('variant');
            console.log("DEBUG: URL params variant:", variant);
            
            // NOTE: We no longer need to map to internal duck type in JS
            // The server will handle the mapping from URL path to internal type
            
            // Return the URL path duck type (not internal name)
            return urlDuckType;
        }
        
        console.log("DEBUG: No duck type in path, using default: open_duck_mini");
        return 'open_duck_mini';
    }

    // Initialize UI state
    function initializeUI() {
        console.log("DEBUG: Initializing UI...");
        
        // Show/hide parameters based on generation type
        generationType.addEventListener('change', function() {
            console.log("DEBUG: Generation type changed to:", this.value);
            singleMotionParams.style.display = this.value === 'single' ? 'block' : 'none';
        });

        // Initial state
        singleMotionParams.style.display = generationType.value === 'single' ? 'block' : 'none';
        
        const duckType = getCurrentDuckType();
        // Log initial state
        console.log("DEBUG: UI initialized. Duck type:", duckType);
        
        // Add direct click handler to generate motion button for debugging
        if (generateMotionButton) {
            console.log("DEBUG: Adding click handler to generate motion button");
            generateMotionButton.addEventListener('click', function(e) {
                console.log("DEBUG: Generate motion button clicked directly");
                
                // Only do manual submission if not already being handled by form submit
                if (!window.motionSubmissionInProgress) {
                    console.log("DEBUG: Manually triggering form submission via direct button handler");
                    submitMotionForm();
                }
            });
        }
    }

    // Extract form submission logic to a separate function for reuse
    async function submitMotionForm() {
        // Set flag to prevent duplicate submissions
        window.motionSubmissionInProgress = true;
        
        try {
            console.log("DEBUG: Beginning motion form submission function");
            // Reset UI
            progressBar.style.width = '0%';
            logOutput.innerHTML = '';
            previewSection.style.display = 'none';
            
            // Show progress
            progressBar.style.width = '20%';
            addLogEntry('Preparing motion generation request...');
            
            // Get URL parameters for variant
            const urlParams = new URLSearchParams(window.location.search);
            const variant = urlParams.get('variant');
            
            // Get form values and log them
            const formData = new FormData(form);
            const duckType = getCurrentDuckType(); // Get duck type from URL
            
            console.log(`DEBUG: Generating motion for duck type: ${duckType}, variant: ${variant}`);
            console.log("DEBUG: Form data being submitted (key-value pairs):");
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }
            
            // Extract the URL path part
            const urlPath = window.location.pathname.split('/').filter(p => p)[0] || 'open_duck_mini';
            console.log("DEBUG: URL path for request:", urlPath);
            
            // Add step indicator
            progressBar.style.width = '40%';
            addLogEntry('Sending request to server...');
            
            // Submit form data to the URL path with variant as query param
            const url = `/${urlPath}/generate_motion${variant ? `?variant=${variant}` : ''}`;
            console.log("DEBUG: Submitting to URL:", url);
            
            // Log right before fetch to see if we get this far
            console.log("DEBUG: About to execute fetch request to:", url);
            
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            
            console.log("DEBUG: Fetch request completed");
            
            // Log response status
            console.log("DEBUG: Server response status:", response.status);
            progressBar.style.width = '60%';
            addLogEntry('Processing server response...');
            
            const data = await response.json();
            console.log("DEBUG: Server response data:", data);
            
            // Check for error
            if (!data.success) {
                progressBar.style.width = '100%';
                const errorMessage = data.error || 'Unknown error occurred';
                addLogEntry(`Error: ${errorMessage}`, 'error');
                
                // Display detailed error if available
                if (data.details) {
                    console.error("DEBUG: Error details:", data.details);
                    if (data.details.output) {
                        addLogEntry("Command output:", 'info');
                        addLogEntry(data.details.output, 'code');
                    }
                    if (data.details.traceback) {
                        addLogEntry("Error traceback:", 'info');
                        addLogEntry(data.details.traceback, 'code');
                    }
                }
                
                throw new Error(errorMessage);
            }
            
            // Update progress
            progressBar.style.width = '80%';
            addLogEntry('Motion generated successfully!', 'success');
            
            // Process and display output if available
            if (data.motion_data && data.motion_data.output) {
                console.log("DEBUG: Command output available");
                addLogEntry("Command output:", 'info');
                addLogEntry(data.motion_data.output, 'code');
            }
            
            // Store motion data for preview
            if (data.motion_data && data.motion_data.frames) {
                console.log("DEBUG: Motion data frames available for preview");
                currentMotionData = {
                    frames: data.motion_data.frames
                };
                previewSection.style.display = 'block';
                initializePreview(currentMotionData);
            } else {
                console.log("DEBUG: No motion frames available for preview");
                addLogEntry("Motion generated but no preview available", 'warning');
            }
            
            progressBar.style.width = '100%';
            addLogEntry('Process completed successfully', 'success');
        } catch (error) {
            console.error("DEBUG: Error in motion generation:", error);
            progressBar.style.width = '100%';
            addLogEntry(`Error: ${error.message}`, 'error');
        } finally {
            // Reset submission flag
            window.motionSubmissionInProgress = false;
        }
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log("DEBUG: Form submitted - START OF SUBMIT HANDLER");
        console.log("DEBUG: Form element:", form);
        console.log("DEBUG: Button that triggered submit:", document.activeElement);
        
        // Use the shared submission function
        await submitMotionForm();
    });

    // Handle motion download
    downloadButton.addEventListener('click', async function() {
        try {
            console.log("DEBUG: Download motion button clicked");
            if (!currentMotionData) {
                addLogEntry("No motion data available to download", 'error');
                return;
            }
            
            // Get URL parameters for variant
            const urlParams = new URLSearchParams(window.location.search);
            const variant = urlParams.get('variant');
            
            // Get the URL path (not internal name)
            const urlPath = window.location.pathname.split('/').filter(p => p)[0] || 'open_duck_mini';
            
            // Build download URL with variant
            const downloadUrl = `/${urlPath}/download_motion${variant ? `?variant=${variant}` : ''}`;
            console.log("DEBUG: Downloading from URL:", downloadUrl);
            
            addLogEntry("Preparing download...");
            
            const response = await fetch(downloadUrl, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Download failed');
            }
            
            console.log("DEBUG: Download response received");
            addLogEntry("Creating download link...");
            
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `motion_${urlPath}_${variant || 'default'}_${new Date().toISOString().slice(0,19).replace(/:/g, '')}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            addLogEntry("Motion file downloaded successfully", 'success');
            
        } catch (error) {
            console.error("DEBUG: Error downloading motion:", error);
            addLogEntry(`Download error: ${error.message}`, 'error');
        }
    });

    function addLogEntry(message, type = '') {
        console.log(`DEBUG: Log entry (${type}): ${message}`);
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        
        if (type === 'code') {
            // Format as code block
            const pre = document.createElement('pre');
            pre.textContent = message;
            entry.appendChild(pre);
        } else {
            entry.textContent = message;
        }
        
        logOutput.appendChild(entry);
        logOutput.scrollTop = logOutput.scrollHeight;
    }

    function initializePreview(motionData) {
        console.log("DEBUG: Initializing motion preview");
        const canvas = document.getElementById('motion-preview');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw preview based on motion data
        if (motionData && motionData.frames && motionData.frames.length > 0) {
            console.log(`DEBUG: Drawing motion path with ${motionData.frames.length} frames`);
            
            try {
                // Calculate scale factors
                const positions = motionData.frames.map(f => f.position || [0, 0]);
                const validPositions = positions.filter(p => p && p.length >= 2);
                
                if (validPositions.length === 0) {
                    console.warn("DEBUG: No valid positions found in motion data");
                    ctx.fillStyle = '#007bff';
                    ctx.textAlign = 'center';
                    ctx.fillText('No position data found', canvas.width/2, canvas.height/2);
                    return;
                }
                
                const maxX = Math.max(...validPositions.map(p => Math.abs(p[0])));
                const maxY = Math.max(...validPositions.map(p => Math.abs(p[1])));
                const scaleX = (canvas.width * 0.8) / (maxX * 2 || 1);
                const scaleY = (canvas.height * 0.8) / (maxY * 2 || 1);
                const scale = Math.min(scaleX, scaleY);
                
                console.log(`DEBUG: Drawing scale: ${scale} (from maxX: ${maxX}, maxY: ${maxY})`);
                
                // Draw motion path
                ctx.beginPath();
                ctx.strokeStyle = '#007bff';
                ctx.lineWidth = 2;
                
                let drawnPoints = 0;
                motionData.frames.forEach((frame, i) => {
                    if (!frame.position || frame.position.length < 2) return;
                    
                    const x = canvas.width/2 + frame.position[0] * scale;
                    const y = canvas.height/2 + frame.position[1] * scale;
                    
                    if (i === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                    drawnPoints++;
                });
                
                ctx.stroke();
                console.log(`DEBUG: Drew motion path with ${drawnPoints} points`);
                
                // Add start and end markers
                if (validPositions.length > 0) {
                    // Start point (green)
                    const startPos = validPositions[0];
                    const startX = canvas.width/2 + startPos[0] * scale;
                    const startY = canvas.height/2 + startPos[1] * scale;
                    
                    ctx.fillStyle = '#28a745';
                    ctx.beginPath();
                    ctx.arc(startX, startY, 5, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // End point (red)
                    const endPos = validPositions[validPositions.length - 1];
                    const endX = canvas.width/2 + endPos[0] * scale;
                    const endY = canvas.height/2 + endPos[1] * scale;
                    
                    ctx.fillStyle = '#dc3545';
                    ctx.beginPath();
                    ctx.arc(endX, endY, 5, 0, 2 * Math.PI);
                    ctx.fill();
                }
            } catch (error) {
                console.error("DEBUG: Error drawing motion preview:", error);
                ctx.fillStyle = '#dc3545';
                ctx.textAlign = 'center';
                ctx.fillText('Error drawing preview', canvas.width/2, canvas.height/2);
            }
        } else {
            console.warn("DEBUG: No frames in motion data for preview");
            // Draw placeholder text if no data
            ctx.fillStyle = '#007bff';
            ctx.textAlign = 'center';
            ctx.fillText('Motion Preview', canvas.width/2, canvas.height/2);
        }
    }

    // Initialize the UI
    console.log("DEBUG: Starting UI initialization");
    initializeUI();
    console.log("DEBUG: reference_motions.js loaded successfully");
}); 