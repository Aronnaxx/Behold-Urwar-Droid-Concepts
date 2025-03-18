const THREE = require('three');
const fs = require('fs');
const path = require('path');

// Helper function to create a simple duck model
function createDuckModel() {
    const group = new THREE.Group();
    
    // Body
    const bodyGeometry = new THREE.SphereGeometry(1, 32, 32);
    const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0xffff00 });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    group.add(body);
    
    // Head
    const headGeometry = new THREE.SphereGeometry(0.5, 32, 32);
    const headMaterial = new THREE.MeshStandardMaterial({ color: 0xffff00 });
    const head = new THREE.Mesh(headGeometry, headMaterial);
    head.position.set(1.5, 0, 0);
    group.add(head);
    
    // Beak
    const beakGeometry = new THREE.ConeGeometry(0.2, 0.5, 32);
    const beakMaterial = new THREE.MeshStandardMaterial({ color: 0xffa500 });
    const beak = new THREE.Mesh(beakGeometry, beakMaterial);
    beak.position.set(2, 0, 0);
    beak.rotation.z = Math.PI / 2;
    group.add(beak);
    
    // Legs
    const legGeometry = new THREE.CylinderGeometry(0.1, 0.1, 0.5, 32);
    const legMaterial = new THREE.MeshStandardMaterial({ color: 0xffa500 });
    
    for (let i = 0; i < 4; i++) {
        const leg = new THREE.Mesh(legGeometry, legMaterial);
        const angle = (i * Math.PI) / 2;
        leg.position.set(
            Math.cos(angle) * 0.8,
            -0.5,
            Math.sin(angle) * 0.8
        );
        leg.rotation.x = Math.PI / 2;
        group.add(leg);
    }
    
    return group;
}

// Helper function to create a motion generation visualization
function createMotionGenerationModel() {
    const group = new THREE.Group();
    
    // Base platform
    const platformGeometry = new THREE.BoxGeometry(2, 0.2, 2);
    const platformMaterial = new THREE.MeshStandardMaterial({ color: 0x808080 });
    const platform = new THREE.Mesh(platformGeometry, platformMaterial);
    platform.position.y = -0.1;
    group.add(platform);
    
    // Motion path
    const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-1, 0.5, -1),
        new THREE.Vector3(0, 1, 0),
        new THREE.Vector3(1, 0.5, 1)
    ]);
    
    const points = curve.getPoints(50);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({ color: 0x00ff00 });
    const line = new THREE.Line(geometry, material);
    group.add(line);
    
    // Animated sphere
    const sphereGeometry = new THREE.SphereGeometry(0.1, 32, 32);
    const sphereMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000 });
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    group.add(sphere);
    
    return group;
}

// Helper function to create a training visualization
function createTrainingModel() {
    const group = new THREE.Group();
    
    // Neural network visualization
    const layers = [4, 6, 4];
    const spacing = 0.5;
    const nodes = [];
    
    layers.forEach((nodeCount, layerIndex) => {
        const layerNodes = [];
        for (let i = 0; i < nodeCount; i++) {
            const geometry = new THREE.SphereGeometry(0.1, 32, 32);
            const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
            const node = new THREE.Mesh(geometry, material);
            node.position.set(
                layerIndex * spacing,
                (i - (nodeCount - 1) / 2) * spacing,
                0
            );
            group.add(node);
            layerNodes.push(node);
        }
        nodes.push(layerNodes);
    });
    
    // Connections
    for (let i = 0; i < layers.length - 1; i++) {
        nodes[i].forEach((node1, j) => {
            nodes[i + 1].forEach((node2, k) => {
                const geometry = new THREE.BufferGeometry().setFromPoints([
                    node1.position,
                    node2.position
                ]);
                const material = new THREE.LineBasicMaterial({ color: 0xffffff });
                const line = new THREE.Line(geometry, material);
                group.add(line);
            });
        });
    }
    
    return group;
}

// Helper function to create a playground visualization
function createPlaygroundModel() {
    const group = new THREE.Group();
    
    // Ground plane
    const groundGeometry = new THREE.PlaneGeometry(4, 4);
    const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x808080 });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.1;
    group.add(ground);
    
    // Obstacles
    const obstacleGeometry = new THREE.BoxGeometry(0.5, 1, 0.5);
    const obstacleMaterial = new THREE.MeshStandardMaterial({ color: 0x8b4513 });
    
    for (let i = 0; i < 4; i++) {
        const obstacle = new THREE.Mesh(obstacleGeometry, obstacleMaterial);
        obstacle.position.set(
            (i % 2) * 2 - 1,
            0.5,
            Math.floor(i / 2) * 2 - 1
        );
        group.add(obstacle);
    }
    
    // Duck
    const duck = createDuckModel();
    duck.scale.set(0.5, 0.5, 0.5);
    duck.position.set(0, 0.5, 0);
    group.add(duck);
    
    return group;
}

// Function to save a model as JSON
function saveModelAsJSON(model, filename) {
    const json = model.toJSON();
    const outputPath = path.join(__dirname, '..', 'models', filename);
    fs.writeFileSync(outputPath, JSON.stringify(json, null, 2));
    console.log(`Saved model to ${outputPath}`);
}

// Generate all models
const models = {
    'hero.json': createDuckModel(),
    'motion_generation.json': createMotionGenerationModel(),
    'training.json': createTrainingModel(),
    'playground.json': createPlaygroundModel(),
    'bdx.json': createDuckModel(),
    'open_duck_mini_v2.json': createDuckModel()
};

// Create models directory if it doesn't exist
const modelsDir = path.join(__dirname, '..', 'models');
if (!fs.existsSync(modelsDir)) {
    fs.mkdirSync(modelsDir, { recursive: true });
}

// Save all models
Object.entries(models).forEach(([filename, model]) => {
    saveModelAsJSON(model, filename);
}); 
