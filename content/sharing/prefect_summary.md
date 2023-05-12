title: Migrating from Civis to Prefect
date: 2023-04-17

## The Problem: Data Orchestration in Civis

Like many progressive political organizations, Working Families Party
has worked with Civis to set up and access our data
infrastructure. Civis is a user-friendly orchestration platform and
web application for executing SQL and python that interacts with our
redshift data warehouse.

Civis is an excellent tool for many progressive campaigns and
organizations that have limited engineering resources. Civis provides a
simple and accessible platform for analysts to easily interact with
data without worrying about data engineering concerns. However, for
more mature and organizations that operate beyond a single political
cycle with sophisticated data needs, Civis has many limitations that
make it [an inappropriate tool]({filename}/sharing/prefect_1.md).

Civis trades off many important data engineering best-practices in
favor of ease-of-use. Civis' design leads users to make minimal use of
version control, offers users limited visibility over production
resources, and is mostly incompatible with the Infrastructure-As-Code
paradigm.

As a large organization with a long term political vision, we
determined that Working Families Party required a much more mature
toolset for its data stack.

## Prefect to the Rescue

There are a lot of orchestration tools out there, and we wanted to
choose the best tool for the job. I had prior experience with Apache
Airflow, which is one of the most popular and mature data
orchestration tools on the market. Several colleagues in the
progressive data space had been eyeing alternatives to Civis for the
same reasons we were, and suggested Prefect as an attractive new tool
worth evaluating. 

Prefect offers most of the features of Airflow, but was more compelling
to us for a few reasons. Airflow can be complicated to set up, and
managed deployments like Astronomer or AWS MWAA can end up being quite
expensive. Prefect offers a lower infrastructural lift for getting
started.

Another advantage of Prefect over Airflow is that migrating existing
Python code to Prefect is much simpler than migrating to
Airflow. Airflow has an idiosyncratic implementation in Python, but
existing Python code can be turned into a working Prefect flow by
simply wrapping it in a decorator.

Overall, what Prefect offered us was the opportunity to implement many
data-engineering best practices that were difficult or impossible to
achieve in Civis. With Prefect, all of our code, containers,
orchestration, and deployments are configured together as code in a
single version-controlled repository.

[Our execution infrastructure]({filename}/sharing/prefect_2.md) is configured declaratively using an AWS
CodeFormation script to set up an execution layer in AWS ECS. We use
Github Actions to automate our continuous integration &
deployment. Changes to Prefect flows, orchestration, and other parts
of our configuration are seamlessly deployed to Prefect Cloud & ECS on
pushes to main.

[Migrating scripts from Civis to Prefect]({filename}/sharing/prefect_migrating_script.md) involves a trivial amount of
refactoring, but also offers opportunities to use Prefect features for
[concurrent execution]({filename}/sharing/prefect_concurrent.md), integrated logging, secret management, automated
orchestration, and testing.

Now that we have worked in Prefect for several months, we've seen many
improvements to our development cycle and workflow. We have more
complete visibility over our production resources, which is really
important as we work to understand & refactor a significant amount of
legacy code.

With everything version-controlled, all changes are easy to coherently
organize using version control best practices, which enables our whole
team to better understand, track, and debug ongoing changes to our
codebase. 

Version-controlled and automatically deployed orchestration
configuration is also a welcome improvement for us. When business
logic requires changes to the automations controlling when and how
scripts are triggered to run, we can make those changes in our
repository, push them, and trust that those changes will be reflected
in production without any further work.

## Wrapping Up

In conclusion, migrating from Civis to Prefect has been a major
upgrade for the data team at Working Families Party. While Civis
served us well in the past, its limitations became evident as our
organization grew and our data needs became more sophisticated. Prefect
offered us a mature and comprehensive toolset for data orchestration,
enabling us to implement best practices and streamline our development
cycle.

Overall, Prefect has provided us with a powerful and flexible solution
for data orchestration, empowering our organization to meet the
demands of our long-term political vision. By embracing Prefect, we
have set ourselves up for success in managing our data infrastructure
and driving our progressive campaigns forward. 
