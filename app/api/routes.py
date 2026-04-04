from flask import jsonify, request
from app.api import api_bp
from app import db
from app.database.models import Subscription
from plugins.registry import registry
from config import Config
from app.core.task_manager import TaskManager
from app.core.checker import _fetch_and_update_subscription
from datetime import datetime
import asyncio

@api_bp.route("/subscriptions", methods=["GET"])
def list_subscriptions():
    """List all subscriptions"""
    subscriptions = Subscription.query.all()
    return jsonify([s.to_dict() for s in subscriptions])

@api_bp.route("/subscriptions", methods=["POST"])
def add_subscription():
    """Add a new subscription"""
    data = request.json

    media_type = data.get("media_type")
    media_name = data.get("media_name")
    media_id = data.get("media_id")
    source_plugin = data.get("source_plugin", "btbtla")

    if not all([media_type, media_name]):
        return jsonify({"error": "media_type and media_name are required"}), 400

    subscription = Subscription(
        media_type=media_type,
        media_name=media_name,
        media_id=media_id,
        source_plugin=source_plugin
    )
    db.session.add(subscription)
    db.session.commit()

    return jsonify(subscription.to_dict()), 201

@api_bp.route("/subscriptions/<int:sub_id>", methods=["DELETE"])
def delete_subscription(sub_id):
    """Delete a subscription"""
    subscription = Subscription.query.get_or_404(sub_id)
    db.session.delete(subscription)
    db.session.commit()
    return "", 204

@api_bp.route("/subscriptions/<int:sub_id>", methods=["PUT"])
def update_subscription(sub_id):
    """Update a subscription (e.g., current_episode, search_keywords)"""
    subscription = Subscription.query.get_or_404(sub_id)
    data = request.json

    if "current_episode" in data:
        subscription.current_episode = data["current_episode"]
    if "status" in data:
        subscription.status = data["status"]
    if "search_keywords" in data:
        subscription.search_keywords = data["search_keywords"]

    db.session.commit()
    return jsonify(subscription.to_dict())

@api_bp.route("/subscriptions/<int:sub_id>", methods=["GET"])
def get_subscription(sub_id):
    """Get a specific subscription"""
    subscription = Subscription.query.get_or_404(sub_id)
    return jsonify(subscription.to_dict())

@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["GET"])
def get_subscription_interval(sub_id):
    """获取订阅的爬取周期"""
    subscription = Subscription.query.get_or_404(sub_id)
    interval = subscription.interval_cron or Config.DEFAULT_INTERVAL_CRON
    return jsonify({"interval_cron": interval})

@api_bp.route("/subscriptions/<int:sub_id>/interval", methods=["PUT"])
def update_subscription_interval(sub_id):
    """更新订阅的爬取周期"""
    subscription = Subscription.query.get_or_404(sub_id)
    data = request.json
    interval_cron = data.get("interval_cron")
    # None 或空字符串表示使用全局默认值
    subscription.interval_cron = interval_cron if interval_cron else None
    db.session.commit()
    return jsonify({"success": True})

@api_bp.route("/subscriptions/<int:sub_id>/fetch", methods=["POST"])
def fetch_subscription(sub_id):
    """手动触发单个订阅的爬取"""
    subscription = Subscription.query.get_or_404(sub_id)

    _, latest = _fetch_and_update_subscription(subscription)

    if latest is None:
        return jsonify({"error": "Failed to fetch episodes"}), 500

    return jsonify({"success": True, "latest_episode": subscription.latest_episode})

@api_bp.route("/search", methods=["GET"])
def search_media():
    """Search media from data source"""
    keyword = request.args.get("q", "")
    source = request.args.get("source", "btbtla")

    if not keyword:
        return jsonify({"error": "keyword is required"}), 400

    plugin = registry.get_data_source(source)
    if not plugin:
        return jsonify({"error": f"Source plugin '{source}' not found"}), 404

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(plugin.search(keyword))
    finally:
        loop.close()

    return jsonify([item.to_dict() for item in results])

@api_bp.route("/plugins", methods=["GET"])
def list_plugins():
    """List available plugins"""
    return jsonify({
        "data_sources": registry.list_data_sources(),
        "notifiers": registry.list_notifiers()
    })

@api_bp.route("/subscriptions/<int:sub_id>/episodes", methods=["GET"])
def get_episodes(sub_id):
    """Get all episodes for a subscription, filtered by search_keywords"""
    subscription = Subscription.query.get_or_404(sub_id)

    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return jsonify({"error": "Plugin not found"}), 404

    # Get user's search keywords
    keywords = subscription.search_keywords or ""
    keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        episodes = loop.run_until_complete(plugin.get_episode_links(subscription.media_id))
    finally:
        loop.close()

    # Filter links based on keywords
    result = {}
    for ep_num, links in episodes.items():
        filtered_links = links

        # If keywords are set, filter links
        if keyword_list:
            filtered_links = []
            for link in links:
                title = link.get("title", "").lower()
                # Include link if it matches ALL keywords
                if all(k in title for k in keyword_list):
                    filtered_links.append(link)

        if filtered_links:
            result[str(ep_num)] = [
                {
                    "title": link.get("title", ""),
                    "url": link.get("url", ""),
                    "type": link.get("type", "")
                }
                for link in filtered_links
            ]

    return jsonify(result)

@api_bp.route("/download-link", methods=["GET"])
def get_download_link():
    """Get the actual magnet download link from a tdown page"""
    tdown_url = request.args.get("url")
    source = request.args.get("source", "btbtla")

    if not tdown_url:
        return jsonify({"error": "url is required"}), 400

    plugin = registry.get_data_source(source)
    if not plugin:
        return jsonify({"error": "Plugin not found"}), 404

    # Try to get the parser's get_magnet_link method
    if hasattr(plugin, "parser") and hasattr(plugin.parser, "get_magnet_link"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            magnet = loop.run_in_executor(None, plugin.parser.get_magnet_link, tdown_url)
            magnet = loop.run_until_complete(magnet)
        finally:
            loop.close()

        if magnet:
            return jsonify({"magnet": magnet})
        else:
            return jsonify({"error": "No magnet link found"}), 404
    else:
        return jsonify({"error": "Plugin doesn't support magnet links"}), 501

@api_bp.route("/fetch-all", methods=["POST"])
def trigger_fetch_all():
    """手动触发所有订阅的爬取"""
    task_id = TaskManager.create_task()
    task = TaskManager.get_task(task_id)

    subscriptions = Subscription.query.filter_by(status='active').all()
    task.total = len(subscriptions)

    for sub in subscriptions:
        try:
            updated, latest = _fetch_and_update_subscription(sub)
            task.results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "status": "success" if updated else "no_update",
                "latest_episode": str(latest) if latest else None
            })
            task.completed += 1
        except Exception as e:
            task.results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "status": "error",
                "error": str(e)
            })
            task.failed += 1

    task.status = "completed"
    task.finished_at = datetime.utcnow()

    return jsonify({"task_id": task_id})

@api_bp.route("/fetch-all/<task_id>", methods=["GET"])
def get_fetch_all_status(task_id):
    """获取 fetch-all 任务状态"""
    task = TaskManager.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict())