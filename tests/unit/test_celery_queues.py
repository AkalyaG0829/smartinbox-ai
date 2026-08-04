import pytest
from src.worker import celery_app

def test_celery_task_routes_configuration():
    """
    Verifies that the Celery task routes are explicitly mapping ML tasks
    to the ml_queue and I/O tasks to the routing_queue to prevent starvation.
    """
    routes = celery_app.conf.task_routes
    
    assert 'tasks.process_message_async' in routes, "process_message_async must be explicitly routed"
    assert routes['tasks.process_message_async']['queue'] == 'ml_queue', "ML tasks must go to ml_queue"
    
    assert 'tasks.recalculate_personalization_stats' in routes, "recalculate_personalization_stats must be explicitly routed"
    assert routes['tasks.recalculate_personalization_stats']['queue'] == 'routing_queue', "I/O tasks must go to routing_queue"
    
    assert 'tasks.process_media_async' in routes, "process_media_async must be explicitly routed"
    assert routes['tasks.process_media_async']['queue'] == 'routing_queue', "Media parsing tasks must go to routing_queue"
