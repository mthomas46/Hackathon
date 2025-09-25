"""
Workflows domain routes
Handles workflow orchestration and distributed processing endpoints
"""

# Workflow routes will be moved here from main.py
# This follows DDD+REST architecture principles

# TODO: Extract workflow endpoints from main.py:
# - /workflows/events (process_workflow_event_endpoint)
# - /workflows/{workflow_id} (get_workflow_status_endpoint)
# - /workflows/queue/status (get_workflow_queue_status_endpoint)
# - /workflows/webhook/config (configure_webhook_endpoint)
# - /distributed/tasks (submit_distributed_task_endpoint)
# - /distributed/tasks/batch (submit_batch_distributed_tasks_endpoint)
# - /distributed/tasks/{task_id} (get_task_status_endpoint)
# - /distributed/tasks/{task_id} (cancel_task_endpoint)
# - /distributed/workers (get_workers_status_endpoint)
# - /distributed/stats (get_distributed_stats_endpoint)
# - /distributed/workers/scale (scale_distributed_workers_endpoint)
# - /distributed/start (start_distributed_processing_endpoint)
# - /distributed/load-balancing/strategy (set_load_balancing_strategy_endpoint)
# - /distributed/queue/status (get_queue_status_endpoint)
# - /distributed/load-balancing/config (configure_load_balancing_endpoint)
