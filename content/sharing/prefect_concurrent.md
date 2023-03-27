title: Limiting Task Concurrency in Prefect
date: 2023-03-02

# Migrating to Prefect, Part 3: Rate limiting API calls

*This post is the third in a series about migrating off of Civis and
onto Prefect as our orchestration tool. The [first post here]() is
about the limitations of Civis, and the [second post here]() is about
setting up Prefect with AWS ECS.*

A common, basic workflow in a data pipeline is to make concurrent,
rate-limited API calls to fetch or post data to a service.
One obstacle I hit early on when attempting to move our data pipelines
into Prefect was around setting up rate-limited API calls.

[Skip to solution](#solution)

## Implementing rate-limited API calls in standard python

[Python has two paradigms for executing IO-bound concurrency](https://realpython.com/python-concurrency/#when-is-concurrency-useful): asyncio
and multithreading.

asyncio is a very powerful framework, but involves a somewhat
substantial change to python patterns. It cannot be easily added to
existing code without rewriting the entire codebase for compatibility
with asyncio. It also represents a technical hurdle and maintenance
burden on smaller teams. For a simple workflow like rate-limited API
calls, using asyncio would be significant overkill.

Multithreading can be complicated to set up, but the python standard
library includes a high-level API to simplify the use of
multithreading: `concurrency.futures`. I like to use the
`ThreadPoolExecutor`, which can be easily configured to limit the
number of active threads. 

A standard implementation of concurrent rate-limited API calls in
python can look like this:

```
from concurrent.futures import ThreadPoolExecutor
import requests

def make_api_call(payload: dict) -> requests.models.Response:
    response = requests.post(api_url_endpoint, json=payload)
	return response

with ThreadPoolExecutor(max_workers=3) as executor:
    payloads: list[dict] = ...
    responses = executor.map(make_api_call, payloads)
```

This code will execute an API call on each payload in the list of
payloads, with 3 threads running simultaneously, each executing one
API call at a time. If each call takes 1 full second, executing 30
calls will take about 10 seconds to complete.

This represents a speed increase of 3x over using a for loop, which
would take a full 30 seconds to complete. 

```
responses = []

for payload in payloads:
    response = make_api_call(payload)
	responses.append(response)
```

## Implementing concurrency in Prefect

Prefect has several different configurable mechanisms for
orchestrating concurrent execution of python code.

Prefect is built on top of an asyncio implementation called AnyIO and
can seamlessly work with python scripts written using asyncio. For
reasons described above, I don't want to use asyncio.

Prefect tasks are main building block of flows in Prefect, and are
also the main mechanism for orchestrating concurrency. Prefect tasks
called with `task.submit()` or `task.map()` are sent to a [Task Runner](https://docs.prefect.io/concepts/task-runners/)
for (potentially) concurrenct execution. Sequential, concurrent or parallel
execution will occur depending on which task runner is used. The
default task runner is a ConcurrentTaskRunner.

Tasks submitted to a concurrent runner will all execute as soon as
they are not waiting for any upstream values.

```
import requests
from prefect import flow, task

@task
def make_api_call(payload: dict) -> requests.models.Response:
    response = requests.post(api_url_endpoint, payload)
	return response
	
@flow
def my_flow():
    payloads = ...
	responses = make_api_call.map(payloads)
```

Using prefect makes concurrent execution of python code wonderfully
simple.

In the above implementation, if each API call takes 1 second to
complete and there are 30 total API calls, the full flow will be done
in about 1 second, because all the calls execute simultaneously.

## Rate limiting concurrency in Prefect

We still need to implement rate limiting on our API calls in
Prefect. The code above will execute every API call across all the
payloads simultaneously. This will generally get your API calls
temporarily or permanently blocked.

Prefect offers a native solution for limiting concurrency on tasks:
simply enough, a [task run concurreny limit](https://docs.prefect.io/concepts/tasks/#task-run-concurrency-limits). It is simple to set up and
use. Concurrency limit values must be deployed to the server with

```
$ prefect concurrency-limit create limit_concurrency_10 10
```

And then prefect tasks can be rate limited by tagging them with the
name of the concurrency limit:

```
@task(tag="limit_concurrency_10")
def make_api_call(payload: dict):
   pass
```

However, rather than limiting the number of tasks that can run at any
given moment, this mechanism limits the number of tasks that can run
in any given 30 second block. Prefect tasks with a rate limit check
for an open slot, and if none is available, wait 30 seconds to check
again for an open slot. 

This is quite problematic, as it results in very significant slowdowns
of rate-limited execution over the standard python use of
multithreading. If you only want 3 calls at a time, you must set up a
concurrency limit of 3. However, after those 3 calls execute, no more
calls will begin to execute until that initial 30 second window has
closed. If each call takes 1 full second, running 30 calls will take
15 minutes to complete!

The Prefect team is aware of this issue and is working on an improved
implementation of the task-concurrency feature. See [this github issue](https://github.com/PrefectHQ/prefect/issues/8873),
[this github PR](https://github.com/PrefectHQ/prefect/pull/7013), and this [slack discussion](https://prefect-community.slack.com/archives/C03D12VV4NN/p1677533662427229).

## Solution

One simple solution would be to use normal python mulithreading code
within a prefect task. In Prefect, however, a Prefect task is intended
to be the smallest unit of concurrency. It breaks intended Prefect
patterns to use multithreading from within a prefect task. Some Prefect
utilities are incompatible with multithreaded task code. [*See
discussion here.*](https://github.com/PrefectHQ/prefect/issues/8652)

In the end, the approach I settled on with some help from the Prefect
development team involved using a python [`threading.Semaphore`](https://superfastpython.com/thread-semaphore/). A
Semaphore is a standard approach for rate limiting multithreaded python
code, used behind the scenes by high-level APIs like
`concurrent.futures.ThreadPoolExecutor`. Each thread attempts to access
an open "slot" from the Semaphore, and waits until a slot is available
to run. While it runs, it holds a slot, and releases that slot once it
is complete.

When Prefect tasks are submitted to a ConcurrentTaskRunner, they are
executed in the same python process using multithreading behind the
scenes, which means using a Semaphore is a natural solution.

My implementation of the prefect-compatible semaphore-based
concurrency rate limiting can be found below or in my template
repository [here](https://github.com/austinweisgrau/prefect-ecs-template/blob/main/utilities/concurrency.py), and its use ends up being very simple:

```
import requests
from prefect import flow, task
from utilities.concurrency import limit_concurrency

@task
@limit_concurrency(max_workers=3)
def make_api_call(payload: dict) -> requests.models.Response:
    response = requests.post(api_url_endpoint, payload)
	return response
	
@flow
def my_flow():
    payloads = ...
	responses = make_api_call.map(payloads)
```

Identical to the implementation with `ThreadPoolExecutor` above,
executing 30 API calls that take 1 second each will take about 10
seconds with this implementation.

## My concurrency limiting task decorator

```
from functools import wraps
from threading import Semaphore
from typing import Callable


def limit_concurrency(max_workers: int) -> Callable[[Callable], Callable]:
    """Wraps methods to implement concurrency limit
	
    Prefect task concurrency limits use a 30 second delay between each
    check for an available slot. This is a more performative approach
    using a threading.Semaphore.
	
    Prefect must be using a "local" task runner for this to work (the
    ConcurrentTaskRunner) and not a distributed task runner like Dask
    or Ray.
	
	Usage:
	  from prefect import task
	  
	  @task
	  @limit_concurrency(max_workers=5)
	  def my_task():
  	      pass
    """

    semaphore = Semaphore(max_workers)

    def pseudo_decorator(func: Callable):
        @wraps(func)
        def limited_concurrent_func(*args, **kwargs):
            with semaphore:
                return func(*args, **kwargs)

        return limited_concurrent_func

    return pseudo_decorator
```
