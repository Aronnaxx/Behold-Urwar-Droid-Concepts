# GitHub Pages Site

This directory contains the static version of the Behold-Urwar Droid Concepts website for GitHub Pages deployment.

The static site is automatically generated from the Flask templates using the `generate_static.py` script when code is pushed to the main branch.

## Local Development

To generate the static site locally:

```bash
python generate_static.py
```

This will create static HTML files in the `docs` directory that can be served by any web server or viewed directly in a browser.

## Structure

- `index.html` - Main landing page
- `static/` - CSS, JavaScript, and other static assets
- `[duck_type]/` - Individual duck droid pages
- `learning/` - Learning center pages

## Note

This is a static version of the dynamic Flask application. Some interactive features may be limited in the static version.
