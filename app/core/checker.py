"""Update checker - check subscriptions for updates"""
import asyncio
import time
from datetime import datetime
from app import db
from app.database.models import Subscription
from config import Config
from plugins.registry import registry

def _fetch_and_update_subscription(subscription: Subscription, retry_count: int = None) -> tuple[bool, int | None, list]:
    """
    抓取订阅的最新集数并更新数据库。
    返回 (是否更新了, 最新集数或None, 下载链接列表)

    网络错误重试 retry_count 次，业务错误直接跳过。
    """
    if retry_count is None:
        retry_count = Config.FETCH_RETRY_COUNT

    plugin = registry.get_data_source(subscription.source_plugin)
    if not plugin:
        return False, None, []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for attempt in range(retry_count + 1):
            try:
                # 获取资源列表（统一使用 get_episode_links 和 get_movie_links）
                if subscription.media_type == 'movie':
                    episodes = loop.run_until_complete(plugin.get_movie_links(subscription.media_id))
                else:
                    episodes = loop.run_until_complete(plugin.get_episode_links(subscription.media_id))

                if not episodes:
                    return False, None, []

                # 电影类型：只返回是否有资源，latest_episode 为 None
                if subscription.media_type == 'movie':
                    latest_links = []
                    for links in episodes.values():
                        latest_links.extend(links)
                    # 电影只要有资源就视为更新
                    if latest_links:
                        if subscription.latest_episode != "有资源":
                            subscription.latest_episode = "有资源"
                            subscription.latest_update_time = datetime.utcnow()
                            db.session.commit()
                            return True, None, latest_links
                        return False, None, latest_links
                    return False, None, []

                # TV 类型：提取最新集数和对应链接
                latest_ep_num = max(int(k) for k in episodes.keys())
                latest_links = episodes.get(str(latest_ep_num), [])

                if subscription.latest_episode != str(latest_ep_num):
                    subscription.latest_episode = str(latest_ep_num)
                    subscription.latest_update_time = datetime.utcnow()
                    db.session.commit()
                    return True, latest_ep_num, latest_links
                return False, latest_ep_num, latest_links

            except (asyncio.TimeoutError, ConnectionError) as e:
                # 网络错误，重试
                if attempt < retry_count:
                    time.sleep(2)
                    continue
                # 最后一次也失败，抛出异常
                raise
    finally:
        loop.close()


def _run_all_subscriptions():
    """遍历所有活跃订阅并执行抓取，返回 (results, failed_count)"""
    from app.database.models import Subscription

    results = []
    failed_count = 0
    subscriptions = Subscription.query.filter_by(status='active').all()

    for sub in subscriptions:
        try:
            updated, latest, links = _fetch_and_update_subscription(sub)
            results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "media_type": sub.media_type,
                "status": "success" if updated else "no_update",
                "latest_episode": str(latest) if latest else None,
                "download_links": links
            })
        except Exception as e:
            results.append({
                "subscription_id": sub.id,
                "name": sub.media_name,
                "media_type": sub.media_type,
                "status": "error",
                "error": str(e),
                "download_links": []
            })
            failed_count += 1

    return results, failed_count
