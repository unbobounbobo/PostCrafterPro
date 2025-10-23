"""
Main page routes
"""
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Main application page
    """
    return render_template('index.html')


@main_bp.route('/batch')
def batch():
    """
    Batch processing page (future feature)
    """
    return render_template('batch.html')
