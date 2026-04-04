"""Update checker - check subscriptions for updates"""
import asyncio
import time
from datetime import datetime
from app import db
from app.database.models import Subscription
from config import Config
from plugins.registry import registry

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
