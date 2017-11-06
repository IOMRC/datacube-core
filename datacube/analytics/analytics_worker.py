"""Analytics Engine Celery worker.
This worker will be cloned in the AE cluster.
Currently JRO service calls e.g. updates are handled by this worker.
If performance is not as responsive as requried, a new cluster for
JRO service calls will be created.
"""

from __future__ import absolute_import, print_function

from sys import modules
from threading import Thread
from celery import Celery

from .analytics_engine2 import AnalyticsEngineV2
from .update_engine2 import UpdateEngineV2
from datacube.execution.execution_engine2 import ExecutionEngineV2
from datacube.config import LocalConfig


# Engines need to be declared globally because of celery
# pylint: disable=invalid-name
# analytics_engine = None
# pylint: disable=invalid-name
# execution_engine = None
# pylint: disable=invalid-name
# update_engine = None
# pylint: disable=invalid-name
config = None


def celery_app(store_config=None):
    if store_config is None:
        local_config = LocalConfig.find()
        store_config = local_config.redis_celery_config
    _app = Celery('ee_task', broker=store_config['url'], backend=store_config['url'])
    _app.conf.update(
        task_serializer='pickle',
        result_serializer='pickle',
        accept_content=['pickle'])
    return _app


# def initialise_engines(config=None):
#     # pylint: disable=global-statement
#     global analytics_engine, execution_engine, update_engine
#     analytics_engine = AnalyticsEngineV2(config)
#     execution_engine = ExecutionEngineV2(config)
#     update_engine = UpdateEngineV2(config)

# pylint: disable=invalid-name
app = celery_app()

# TODO: In production environment, the engines need to be started using a local config identified
# through `find()`. This is not desirable in pytest as it will use the default config which is
# invalid and crashes all the tests. For now, we simply check whether this is run within
# pytest. This must be addressed another way.
# if 'pytest' not in modules:
# initialise_engines()


def launch_ae_worker(local_config):
    """Only used for pytests"""
    if not local_config:
        local_config = LocalConfig.find()
    global config
    config = local_config
    store_config = local_config.redis_celery_config
    # initialise_engines(local_config)
    thread = Thread(target=launch_worker_thread, args=(store_config['url'],))
    thread.start()
    return thread


def launch_worker_thread(url):
    """Only used for pytests"""
    app.conf.update(result_backend=url,
                    broker_url=url)
    argv = ['worker', '-A', 'datacube.analytics.analytics_worker', '-l', 'DEBUG', '--autoscale=1,0']
    app.worker_main(argv)


def stop_worker():
    """Only used for pytests"""
    app.control.shutdown()


@app.task
def run_python_function_base(function, data, storage_params=None, *args, **kwargs):
    '''Process the function and data submitted by the user.'''
    analytics_engine = AnalyticsEngineV2(config)
    if not analytics_engine:
        raise RuntimeError('Analytics engine must be initialised by calling `initialise_engines`')
    jobs, jro, base_results = analytics_engine.analyse(function, data, storage_params, *args, **kwargs)
    results = []
    for job in jobs:
        results.append(run_python_function_subjob.delay(job, base_results, *args, **kwargs))
    return (jro, results)


@app.task
def run_python_function_subjob(job, base_results, *args, **kwargs):
    '''Process a subjob, created by the base job.'''
    execution_engine = ExecutionEngineV2(config)
    if not execution_engine:
        raise RuntimeError('Execution engine must be initialised by calling `initialise_engines`')
    result = execution_engine.execute(job, base_results, *args, **kwargs)
    return result


@app.task
def get_update(action, item_id):
    '''Return an update on a job or result.'''
    update_engine = UpdateEngineV2(config)
    if not update_engine:
        raise RuntimeError('Update engine must be initialised by calling `initialise_engines`')
    result = update_engine.execute(action, item_id)
    return result
