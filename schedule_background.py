import logging
import threading
import time


def schedule_background(
        target,
        args=(),
        kwargs=None,
        delay=0,
        interval=None,
        kill_event=None
):
    """Schedule the target callable in a background thread.
    The target can be run once or periodically on an interval using the interval argument.
    The (first) run can be delayed using the delay argument.
    If running in an interval schedule a kill_event can be used to stop execution.

    Parameters:
    target : callable
        The callable to be scheduled
    args : tuple
    kwargs : dict
        The arguments to use in the call, target(*args, **kwargs)
    delay : float
        Initial delay of the (first) call in seconds(default 0)
    interval : float
        The callable is called every interval seconds if set(default None)
    kill_event : threading.Event
        The background thread is stopped when the event is set. This only works
        when using interval, it will not stop execution of already running tasks.
    """

    if delay < 0:
        raise ValueError("delay >= 0 expected")

    if interval is not None and interval <= 0:
        raise ValueError("interval > 0 expected")

    logging.info(f"Scheduling {target} with delay {delay} and interval {interval}")

    if kwargs is None:
        kwargs = {}

    if not interval:
        def new_target():
            time.sleep(delay)
            target(*args, **kwargs)

    else:
        def new_target():
            time.sleep(delay)
            next_run_time = time.time()
            while kill_event is None or not kill_event.is_set():
                if time.time() < next_run_time:
                    time.sleep(0.1)
                    continue
                next_run_time = time.time() + interval
                target(*args, **kwargs)

    thread = threading.Thread(target=new_target)
    thread.start()
    return thread
