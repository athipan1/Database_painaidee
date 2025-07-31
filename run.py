#!/usr/bin/env python3
"""
Main application entry point for development.
"""
import os
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )