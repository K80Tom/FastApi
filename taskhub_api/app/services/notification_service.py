import logging

logger = logging.getLogger("taskhub.notifications")


def log_task_created(task_id: int) -> None:
    # 示例后台任务：真实系统应先把通知持久化，再交给可靠 Worker。
    logger.info("background notification created for task_id=%s", task_id)
