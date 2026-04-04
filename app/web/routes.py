from flask import render_template, request, redirect, url_for, jsonify
from app.web import web_bp
from app import db
from app.database.models import Subscription, Setting
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
        fetch_retry_count = request.form.get("fetch_retry_count", "3")

        # 保存到数据库
        setting = Setting.query.get("default_interval_cron")
        if setting:
            setting.value = default_cron
        else:
            setting = Setting(key="default_interval_cron", value=default_cron)
            db.session.add(setting)

        retry_setting = Setting.query.get("fetch_retry_count")
        if retry_setting:
            retry_setting.value = fetch_retry_count
        else:
            retry_setting = Setting(key="fetch_retry_count", value=fetch_retry_count)
            db.session.add(retry_setting)

        db.session.commit()
        # 更新内存中的值
        Config.DEFAULT_INTERVAL_CRON = default_cron
        Config.FETCH_RETRY_COUNT = int(fetch_retry_count)
        return redirect(url_for("web.settings"))

    # 获取 fetch_retry_count
    retry_setting = Setting.query.get("fetch_retry_count")
    fetch_retry_count = retry_setting.value if retry_setting else str(Config.FETCH_RETRY_COUNT)

    return render_template("settings.html",
                           default_cron=Config.DEFAULT_INTERVAL_CRON,
                           fetch_retry_count=fetch_retry_count)