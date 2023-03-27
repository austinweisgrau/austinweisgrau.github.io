title: Migrating a Script from Civis to Prefect
date: 2023-03-27

# Migrating to Prefect, Part 4: Moving a Script from Civis to Prefect

*This post is the fourth in a series about migrating off of Civis and
onto Prefect as our orchestration tool. The [first post]() is about
the limitations of Civis, and the [second]() and [third]() posts are about
setting up and using Prefect.*

Once Prefect was adequately set up, we were ready to start moving our
scripts out of Civis and into Prefect. This process involves the
following steps:

Basic necessary steps:

1. Copy the code and tests into a module in the Prefect repository
2. Add task and flow decorators, potentially rearranging and
   encapsulating the code
3. Swap out loggers and credential fetching methods
4. Add entry to scheduling module
5. Run locally and ensure everything works
6. Deploy and run in production and ensure everything works
7. Turn off civis automation, archive script in Civis
8. Update relevant team documentation

Bonus steps:

9. Refactor control flow to take advantage of prefect orchestration
   (concurrency, retries, etc)
10. Refactor, expand tests and documentation

## Example Civis Script

We can use the following Civis script as an example to work with.

This script pulls a list of VAN IDs from a Redshift table and updates these VAN IDs in EveryAction with an origin source code.

```
import os
from parsons import Redshift, Table, VAN

van_source_code = 12345

van_client = VAN(db="EveryAction", api_key=os.environ["VAN_API_KEY_PASSWORD"])

query_results: Table = Redshift.query("select vanid from some_important_table")

for result in query_results:
    van_client.apply_person_code(result['vanid'], van_source_code)
    
print("Finished applying source codes.")
	
```

## Copy the code, add task and flow decorators, encapsulate

Prefect is intended to be simple to implement with existing code. The
minimum change necessary to make a Prefect flow out of existing code
is to encapsulate the code within a method that has the
`prefect.flow()` decorator applied.

```
import os
from parsons import Redshift, Table, VAN
from prefect import flow


van_source_code = 12345

@flow(name="Update VAN Source Codes Sync")
def update_van_source_codes():
    van_client = VAN(db="EveryAction", api_key=os.environ["VAN_API_KEY_PASSWORD"])
    
    query_results: Table = Redshift.query("select vanid from some_important_table")
    
    for result in query_results:
        van_client.apply_person_code(result['vanid'], van_source_code)
        
    print("Finished applying source codes.")
	
if __name__ == '__main__':
    update_van_source_codes()
	
```

Better yet is to break out some of the methods within the flow as
prefect tasks, to gain greater oversight and control over the flow.

```
import os
from parsons import Redshift, Table, VAN
from prefect import flow, task


van_source_code = 12345

@task
def fetch_query_results() -> Table:
    query_results = Redshift.query("select vanid from some_important_table")
	return query_results
	
@task
def apply_origin_source_code(van_id: int, source_code: int) -> None:
    van_client.apply_person_code(van_id, source_code)

@flow(name="Update VAN Source Codes Sync")
def update_van_source_codes():
    van_client = VAN(db="EveryAction", api_key=os.environ["VAN_API_KEY_PASSWORD"])
	
	query_results = fetch_query_results()
	
    for result in query_results:
        apply_origin_source_code(result['vanid'], van_source_code)
        
    print("Finished applying source codes.")
	
```

## Swap out loggers

Prefect is capable of capturing print statements as logs, but this
behavior is not enabled by default. If your code uses print
statements, you can define your flow with:

```
...

@flow(name="Update VAN Source Codes Sync", log_prints=True)
def update_van_source_codes():
   ...
   
```

Alternatively, you can use the prefect logger.

```
from prefect import flow, task, get_run_logger

...

@flow(name="Update VAN Source Codes Sync")
def update_van_source_codes():

	... 
	
    get_run_logger().info("Finished apply source codes.")
```

The prefect run logger has issues working in a test environment, so I
prefer to use an intermediate method which can return a fallback
logger if the run logger is not available. This module is included in
my prefect template [here](https://github.com/austinweisgrau/prefect-ecs-template/blob/main/utilities/logging.py).

```
import logging

from prefect import get_run_logger
from prefect.exceptions import MissingContextError

# Configure fallback prefect logger
# Note that this logger should only be used in development
logger = logging.getLogger("prefect-development")
logger.setLevel(logging.DEBUG)


def get_logger() -> logging.Logger:
    """Returns prefect.get_run_logger() except in a test environment

    prefect.get_run_logger() is incompatible with testing task functions
    outside of a flow context. See
    https://github.com/PrefectHQ/prefect/issues/8568"""
    try:
        result = prefect.get_run_logger()
    except MissingContextError:
        result = logging.getLogger("prefect-development")
    return result

```

## Swap out credential fetching methods

Now that we're out of Prefect, we're not bound to using environment
variables with those pesky mandatory`_PASSWORD` suffixes!

You can fetch credentials using any implementation that makes sense
for your team and Prefect stack. You can add environment variables
to your Docker image, or fetch them from a secret store like AWS
Secrets Manager or use Prefect Blocks to store credentials. 

## Add entry to scheduling module

In my prefect template, automated flow scheduling is controlled by [a
scheduling module](https://github.com/austinweisgrau/prefect-ecs-template/blob/main/scheduling.py) that is run by a [github actions script](https://github.com/austinweisgrau/prefect-ecs-template/blob/b03c2db49209ae4f76f9a1c73db39d4bf0d8634d/.github/workflows/main.yaml#L151) if changes are
pushed to the main branch.

When a new flow is created, a block needs to be added to the
scheduling module to set up automated runs for this flow.

```
def update_deployment_schedules() -> None:

    ...
	
    schedule_deployment(
        "update_van_source_codes",
        "Update VAN Source Codes Sync",
        datetime.timedelta(days=1),  # Daily
        datetime.datetime.today().replace(hour=21, minute=5, second=0),  # At 9:05 pm
    )
```

## Run locally and ensure everything works

```
$ python flows/update_van_source_codes/update_van_source_codes_flow.py
```

## Deploy 

If you are using a continuous deployment script, you can push the new
code to your main branch and let that script create the new deployment
in the Prefect Cloud. You can also create the deployment manually by
running a command like

```
$ prefect deployment build flows/update_van_source_codes/update_van_source_codes_flow.py:update_van_source_codes -a -n update_van_source_codes -ib ecs-task/prod
```

## Refactor control flow to take advantage of prefect orchestration

Instead of the for loop for executing our API calls, we can use
task.submit() or task.map() to take advantage of prefect concurrency.

Using our custom [task concurrency limiter](), we can set a rate limit of
3 as advised by the [EveryAction documentation](https://docs.ngpvan.com/docs/throttling-guidelines).


```
from utilities.concurrency import limit_concurrency

...

@task
@limit_concurrency(max_workers=3)
def apply_origin_source_code(van_id: int, source_code: int) -> None:
    van_client.apply_person_code(van_id, source_code)


@flow(name="Update VAN Source Codes Sync")
def update_van_source_codes():
    van_client = VAN(db="EveryAction", api_key=os.environ["VAN_API_KEY_PASSWORD"])
	
	query_results = fetch_query_results()
	
	van_ids = [result['vanid'] for result in query_results]
	
	# Await results before finishing flow
	for future in apply_origin_source_code.map(van_ids, van_source_code):
	    future.wait()
        
    print("Finished applying source codes.")

```

## Refactor, expand tests and documentation

Every time you are looking anew at a script is a great opportunity to
clean up the code, notice where it is unclear, and documentation to
clarify technical logic and business logic, and add tests to validate
important pieces of the code!
