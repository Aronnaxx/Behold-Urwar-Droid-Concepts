#!/usr/bin/env python3
"""
Simple static site generator for GitHub Pages
Converts templates to static HTML files without Flask dependencies
"""

import os
import json
import re
import shutil
from pathlib import Path

def load_duck_config():
    """Load duck configuration without Flask dependencies"""
    config_dir = Path('app/config/ducks')
    duck_types = {}
    
    for file_path in config_dir.glob('*.json'):
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
                duck_id = config.get('id')
                if duck_id:
                    duck_types[duck_id] = config
        except Exception as e:
            print(f"Error loading duck configuration file {file_path}: {e}")
    
    return duck_types

def generate_static_site():
    """Generate static HTML files from templates"""
    
    # Output directory for static site
    output_dir = Path('docs')
    output_dir.mkdir(exist_ok=True)
    
    # Copy static assets
    static_output = output_dir / 'static'
    if static_output.exists():
        shutil.rmtree(static_output)
    
    # Copy CSS, JS, and other static files
    if Path('app/static').exists():
        shutil.copytree('app/static', static_output)
        print("Copied static assets")
    
    # Generate index page
    print("Generating index page...")
    duck_types = load_duck_config()
    
    # Read base template
    with open('app/templates/base.html', 'r') as f:
        base_template = f.read()
    
    # Simple template processing for static generation
    rendered_html = generate_static_index(duck_types, base_template)
    
    with open(output_dir / 'index.html', 'w') as f:
        f.write(rendered_html)
    
    # Generate duck pages
    for duck_id, duck_data in duck_types.items():
        print(f"Generating pages for {duck_data['name']}...")
        duck_dir = output_dir / duck_id
        duck_dir.mkdir(exist_ok=True)
        
        # Generate main duck page for each variant
        for variant_id, variant_data in duck_data.get('variants', {}).items():
            duck_html = generate_static_duck_page(duck_data, variant_data, base_template)
            filename = f'{variant_id}.html' if variant_id != 'v2' else 'index.html'
            with open(duck_dir / filename, 'w') as f:
                f.write(duck_html)
    
    # Generate learning pages
    learning_dir = output_dir / 'learning'
    learning_dir.mkdir(exist_ok=True)
    
    learning_topics = ['motion_generation', 'training', 'playground', 'awd']
    for topic in learning_topics:
        print(f"Generating learning page: {topic}...")
        topic_html = generate_static_learning_page(topic, base_template)
        with open(learning_dir / f'{topic}.html', 'w') as f:
            f.write(topic_html)
    
    print(f"Static site generated in {output_dir}")

def generate_static_index(duck_types, base_template):
    """Generate static index page"""
    
    # Create duck types data structure for template
    duck_types_for_template = {}
    for duck_id, duck_data in duck_types.items():
        duck_types_for_template[duck_id] = {
            'name': duck_data['name'],
            'variants': {}
        }
        for variant_id, variant_data in duck_data.get('variants', {}).items():
            duck_types_for_template[duck_id]['variants'][variant_id] = {
                'name': variant_data['name'],
                'description': variant_data['description'],
                'model_path': variant_data['model_path']
            }
    
    # Generate duck type cards HTML
    duck_cards_html = ""
    for duck_id, duck_info in duck_types_for_template.items():
        first_variant = list(duck_info['variants'].values())[0]
        model_path = first_variant['model_path']
        
        variants_html = ""
        for variant_id, variant in duck_info['variants'].items():
            variants_html += f'''
                    <li>
                        <a href="{duck_id}/{variant_id}.html" class="text-decoration-none">
                            <span class="variant-badge">{variant['name']}</span>
                            {variant['description']}
                        </a>
                    </li>'''
        
        duck_cards_html += f'''
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 duck-card">
                            <div class="card-body">
                                <h5 class="card-title">{duck_info['name']}</h5>
                                <div class="model-viewer">
                                    <model-viewer 
                                        src="{model_path}"
                                        camera-controls
                                        auto-rotate
                                        auto-rotate-delay="0"
                                        rotation-per-second="30deg"
                                        camera-orbit="45deg 65deg {'1.5m' if duck_id == 'bdx' else '2m'}"
                                        min-camera-orbit="auto auto auto"
                                        max-camera-orbit="auto auto auto"
                                        camera-target="0m {'0.4m' if duck_id == 'bdx' else '0m'} 0m"
                                        field-of-view="30deg"
                                        environment-image="neutral"
                                        shadow-intensity="1"
                                        exposure="1"
                                        bounds="tight"
                                        disable-zoom
                                        alt="{duck_info['name']} visualization">
                                    </model-viewer>
                                </div>
                                <p class="card-text">Available variants:</p>
                                <ul class="variant-list">{variants_html}
                                </ul>
                            </div>
                        </div>
                    </div>'''
    
    # Main content HTML
    content_html = f'''
<div class="row">
    <div class="col-md-12 text-center mb-4">
        <h1>Welcome to Duck Droid Concepts</h1>
        <p class="lead">A comprehensive platform for developing and training Duck Droids</p>
    </div>
</div>

<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Available Duck Types</h5>
                <div class="row">{duck_cards_html}
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-12">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Learning Center</h5>
                <p class="card-text">Get started with our comprehensive learning resources:</p>
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-walking fa-3x mb-3"></i>
                                <h6>Motion Generation</h6>
                                <a href="learning/motion_generation.html" class="btn btn-outline-primary btn-sm">Learn More</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-brain fa-3x mb-3"></i>
                                <h6>Training Process</h6>
                                <a href="learning/training.html" class="btn btn-outline-primary btn-sm">Learn More</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-gamepad fa-3x mb-3"></i>
                                <h6>Mujoco Playground</h6>
                                <a href="learning/playground.html" class="btn btn-outline-primary btn-sm">Learn More</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-balance-scale fa-3x mb-3"></i>
                                <h6>Advanced Walking Dynamics</h6>
                                <a href="learning/awd.html" class="btn btn-outline-primary btn-sm">Learn More</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>'''
    
    # Process base template
    html = process_base_template(base_template, 'Behold-Urwar Droid Concepts - Home', content_html)
    html = html.replace('type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"', 
                       'type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"')
    
    return html

def generate_static_duck_page(duck_data, variant_data, base_template):
    """Generate static duck page"""
    
    # Generate duck page content
    content_html = f'''
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="/">Home</a></li>
                    <li class="breadcrumb-item active">{duck_data['name']}</li>
                </ol>
            </nav>
        </div>
    </div>

    <div class="row">
        <div class="col-md-4">
            <div class="duck-specs">
                <h3>{duck_data['name']} - {variant_data['name']}</h3>
                <p>{variant_data['description']}</p>
                
                <model-viewer
                    src="{variant_data['model_path']}"
                    camera-controls
                    auto-rotate
                    auto-rotate-delay="0"
                    rotation-per-second="30deg"
                    camera-orbit="45deg 65deg {'1.5m' if duck_data['id'] == 'bdx' else '2m'}"
                    camera-target="0m {'0.4m' if duck_data['id'] == 'bdx' else '0m'} 0m"
                    field-of-view="30deg"
                    environment-image="neutral"
                    shadow-intensity="1"
                    exposure="1"
                    bounds="tight"
                    alt="{duck_data['name']} {variant_data['name']} model">
                </model-viewer>
                
                <div class="specifications mt-3">
                    <h5>Specifications</h5>'''
    
    # Add specifications if available
    if 'specifications' in variant_data:
        for key, value in variant_data['specifications'].items():
            formatted_key = key.replace('_', ' ').title()
            content_html += f'''
                    <div class="spec-item">
                        <span class="spec-label">{formatted_key}:</span>
                        <span class="spec-value">{value}</span>
                    </div>'''
    
    content_html += '''
                </div>
            </div>
        </div>
        
        <div class="col-md-8">
            <div class="action-card">
                <h3>About This Variant</h3>
                <p>This is a detailed view of the ''' + variant_data['name'] + ''' variant of the ''' + duck_data['name'] + ''' duck droid.</p>
                <p>''' + variant_data['description'] + '''</p>
            </div>

            <div class="action-card">
                <h3>Model Information</h3>
                <p>Interactive 3D model showing the design and structure of this duck droid variant.</p>
                <p>Use your mouse to rotate and examine the model from different angles.</p>
            </div>
        </div>
    </div>
</div>'''
    
    # Process base template
    html = process_base_template(base_template, f'{duck_data["name"]} - {variant_data["name"]} - BUDC', content_html)
    html = html.replace('type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"', 
                       'type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"')
    
    return html

def generate_static_learning_page(topic, base_template):
    """Generate static learning page"""
    
    topic_info = {
        'motion_generation': {
            'title': 'Motion Generation',
            'description': 'Learn about generating realistic motion patterns for duck droids.'
        },
        'training': {
            'title': 'Training Process', 
            'description': 'Understand the machine learning training process for duck droid behaviors.'
        },
        'playground': {
            'title': 'Mujoco Playground',
            'description': 'Explore the physics simulation environment used for testing.'
        },
        'awd': {
            'title': 'Advanced Walking Dynamics',
            'description': 'Deep dive into the complex dynamics of bipedal locomotion.'
        }
    }
    
    info = topic_info.get(topic, {'title': topic.replace('_', ' ').title(), 'description': f'Learning content for {topic}'})
    
    content_html = f'''
<div class="container mt-4">
    <div class="row">
        <div class="col-md-12">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="/">Home</a></li>
                    <li class="breadcrumb-item"><a href="/">Learning Center</a></li>
                    <li class="breadcrumb-item active">{info['title']}</li>
                </ol>
            </nav>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-12">
            <h1>{info['title']}</h1>
            <div class="alert alert-info">
                <h4>Learning Content Coming Soon!</h4>
                <p>{info['description']}</p>
                <p>This learning module is under development and will be available soon.</p>
                <a href="/" class="btn btn-primary">Return to Home</a>
            </div>
        </div>
    </div>
</div>'''
    
    return process_base_template(base_template, f'{info["title"]} - Learning Center', content_html)

def process_base_template(base_template, title, content):
    """Process base template with title and content"""
    
    # Replace template blocks
    html = base_template
    
    # Replace title block
    html = re.sub(r'{%\s*block\s+title\s*%}.*?{%\s*endblock\s*%}', title, html, flags=re.DOTALL)
    
    # Replace content block  
    html = re.sub(r'{%\s*block\s+content\s*%}.*?{%\s*endblock\s*%}', content, html, flags=re.DOTALL)
    
    # Replace extra CSS and JS blocks with empty content
    html = re.sub(r'{%\s*block\s+extra_css\s*%}.*?{%\s*endblock\s*%}', '', html, flags=re.DOTALL)
    html = re.sub(r'{%\s*block\s+extra_js\s*%}.*?{%\s*endblock\s*%}', 
                 '<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>', 
                 html, flags=re.DOTALL)
    
    # Replace Flask template syntax with static equivalents
    html = re.sub(r"url_for\('static',\s*filename='([^']+)'\)", r"'static/\1'", html)
    html = re.sub(r"url_for\('main\.index'\)", "'/'", html)
    html = re.sub(r"{{\s*url_for\('static',\s*filename='([^']+)'\)\s*}}", r"static/\1", html)
    html = re.sub(r"{{\s*url_for\('main\.index'\)\s*}}", "/", html)
    
    # Remove any remaining Flask template syntax
    html = re.sub(r'{%.*?%}', '', html, flags=re.DOTALL)
    html = re.sub(r'{{.*?}}', '', html, flags=re.DOTALL)
    
    return html

if __name__ == '__main__':
    generate_static_site()
