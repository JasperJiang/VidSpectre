"""Update checker - check subscriptions for updates"""
import asyncio
import re
import time
from datetime import datetime
from app import db
from app.database.models import Subscription
from config import Config
from plugins.registry import registry

def parse_episode_number(episode_str):
    """Parse episode string to comparable number. Returns tuple (season, episode) or None."""
    if not episode_str:
        return None
    # Match patterns like "S01E05", "5", "E12", "01"
    s_match = re.search(r'S(\d+)', episode_str, re.IGNORECASE)
    e_match = re.search(r'E(\d+)', episode_str, re.IGNORECASE)
    num_match = re.search(r'(\d+)', episode_str)

    if s_match and e_match:
        return (int(s_match.group(1)), int(e_match.group(1)))
    elif e_match:
        return (1, int(e_match.group(1)))
    elif num_match:
        return (1, int(num_match.group(1)))
    return None

def is_new_episode(user_episode, latest_episode):
    """Check if latest_episode is newer than user's current episode."""
    user_parsed = parse_episode_number(user_episode)
    latest_parsed = parse_episode_number(latest_episode)

    if not user_parsed or not latest_parsed:
        # If can't parse, just compare the strings
        return user_episode != latest_episode

    return latest_parsed > user_parsed

async def check_subscription(subscription: Subscription):
    """Check a single subscription for updates"""
    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return None

    try:
        update_info = await plugin.get_updates(subscription.media_id)
        return update_info
    except Exception as e:
        print(f"Error checking {subscription.media_name}: {e}")
        return None

async def check_all_subscriptions():
    """Check all active subscriptions for updates"""
    subscriptions = Subscription.query.filter_by(status="active").all()
    results = []

    for sub in subscriptions:
        update_info = await check_subscription(sub)
        if update_info:
            # Check if there's a new episode compared to user's progress
            is_new = is_new_episode(sub.current_episode, update_info.latest_episode)
            is_newer_than_recorded = sub.latest_episode != update_info.latest_episode

            if is_new:
                sub.latest_episode = update_info.latest_episode
                sub.latest_update_time = datetime.utcnow()
                db.session.commit()

                results.append({
                    "subscription": sub,
                    "update_info": update_info,
                    "is_new_since_last_watched": True
                })
            elif is_newer_than_recorded:
                # There's update but user already watched it (or skipped)
                sub.latest_episode = update_info.latest_episode
                sub.latest_update_time = datetime.utcnow()
                db.session.commit()

    return results

def run_check():
    """Run check in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(check_all_subscriptions())
    finally:
        loop.close()

def _fetch_and_update_subscription(subscription: Subscription, retry_count: int = None) -> tuple[bool, int | None]:
    """
    抓取订阅的最新集数并更新数据库。
    返回 (是否更新了, 最新集数或None)

    网络错误重试 retry_count 次，业务错误直接跳过。
    """
    if retry_count is None:
        retry_count = Config.FETCH_RETRY_COUNT

    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return False, None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for attempt in range(retry_count + 1):
            try:
                if subscription.media_type == 'movie':
                    result = loop.run_until_complete(plugin.get_movie_links(subscription.media_id))
                else:
                    result = loop.run_until_complete(plugin.get_episode_links(subscription.media_id))

                if result and result.keys():
                    latest = max(int(k) for k in result.keys())
                    if subscription.latest_episode != str(latest):
                        subscription.latest_episode = str(latest)
                        subscription.latest_update_time = datetime.utcnow()
                        db.session.commit()
                        return True, latest
                    return False, latest
                return False, None
            except (asyncio.TimeoutError, ConnectionError) as e:
                # 网络错误，重试
                if attempt < retry_count:
                    time.sleep(2)
                    continue
                # 最后一次也失败，抛出异常
                raise
    finally:
        loop.close()

def run_check_for_subscription(sub_id):
    """检查单个订阅（供调度器调用）"""
    subscription = Subscription.query.get(sub_id)
    if not subscription or subscription.status != 'active':
        return
    _fetch_and_update_subscription(subscription)
