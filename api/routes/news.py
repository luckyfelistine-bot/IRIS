"""IRIS v9 News Routes"""
from flask import Blueprint, request, jsonify
from modules.news_module import news_module

news_bp = Blueprint('news', __name__, url_prefix='/api/news')

@news_bp.route('/latest', methods=['GET'])
def news_latest():
    return jsonify(news_module.get_latest(request.args.get('category', 'general'), request.args.get('limit', 10, type=int)))

@news_bp.route('/search', methods=['GET'])
def news_search():
    return jsonify(news_module.search(request.args.get('q', ''), request.args.get('limit', 10, type=int)))

@news_bp.route('/summary', methods=['GET'])
def news_summary():
    return jsonify({"success": True, "summary": news_module.get_headlines_summary(request.args.get('category', 'general'))})
