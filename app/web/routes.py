from flask import render_template, request, redirect, url_for, jsonify
from app.web import web_bp
from app import db
from app.database.models import Subscription
from config import Config

@web_bp.route("/")
def index():
    """Home page - subscription list"""
    subscriptions = Subscription.query.all()
    return render_template("index.html",
                     subscriptions=subscriptions,
                     default_cron=Config.DEFAULT_INTERVAL_CRON)

@web_bp.route("/subscription/add", methods=["GET", "POST"])
def add_subscription():
    """Add subscription page"""
    if request.method == "POST":
        media_type = request.form.get("media_type")
        media_name = request.form.get("media_name")
        media_id = request.form.get("media_id")
        source_plugin = request.form.get("source_plugin", "btbtla")

        subscription = Subscription(
            media_type=media_type,
            media_name=media_name,
            media_id=media_id,
            source_plugin=source_plugin
        )
        db.session.add(subscription)
        db.session.commit()
        return redirect(url_for("web.index"))

    return render_template("subscription.html", action="add")

@web_bp.route("/subscription/<int:sub_id>/delete", methods=["POST"])
def delete_subscription(sub_id):
    """Delete subscription"""
    subscription = Subscription.query.get_or_404(sub_id)
    db.session.delete(subscription)
    db.session.commit()
    return redirect(url_for("web.index"))

@web_bp.route("/subscription/<int:sub_id>/edit", methods=["GET", "POST"])
def edit_subscription(sub_id):
    """Edit subscription - update current episode"""
    subscription = Subscription.query.get_or_404(sub_id)

    if request.method == "POST":
        current_episode = request.form.get("current_episode")
        subscription.current_episode = current_episode if current_episode else None
        db.session.commit()
        return redirect(url_for("web.index"))

    return render_template("edit_subscription.html", subscription=subscription)

@web_bp.route("/subscription/<int:sub_id>/update-episode", methods=["POST"])
def update_episode_ajax(sub_id):
    """Update current episode via AJAX"""
    subscription = Subscription.query.get_or_404(sub_id)
    data = request.get_json()

    subscription.current_episode = data.get("current_episode")
    db.session.commit()

    return jsonify({"success": True, "current_episode": subscription.current_episode})

@web_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """全局设置页面"""
    if request.method == "POST":
        default_cron = request.form.get("default_cron")
        # 保存到 config 对象
        Config.DEFAULT_INTERVAL_CRON = default_cron
        return redirect(url_for("web.settings"))

    return render_template("settings.html", default_cron=Config.DEFAULT_INTERVAL_CRON)