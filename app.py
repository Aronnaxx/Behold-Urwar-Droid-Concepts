import os
from app import create_app

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create the application
app = create_app()

if __name__ == '__main__':
    # Get port from environment variable or default to 5001
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(debug=debug, port=port) 
