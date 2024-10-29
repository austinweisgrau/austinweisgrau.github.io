title: Tooling for Big Data Transformations
date: 2024-10-29

Data teams sometimes struggle to find appropriate tooling for large
analytics workflows. A common pattern is for an analyst to work
primarily using the R tidyverse or Python pandas. This works fine for
awhile, but as the workflow scales up and the amount of data being
processed increases, eventually these tools struggle to keep up. Even
running these workflows on cloud servers with massive amounts of CPU
and RAM doesn't scale well.

In my opinion, the only truly appropriate tooling for data
transformations above a very small scale is to load the data into an
OLAP data warehouse and execute your transformations using SQL (or,
ideally, [dbt](https://getdbt.com)).

However, sometimes you need a drop-in solution that can scale-up
dataframe-based transformations. 

Traditionally, the usual approach was to use distributed computing
frameworks like Spark or Hadoop to execute dataframe transformations
at scale. However, these require pretty elaborate and complex cloud
infrastructure.

These days, there are much better tools for working with big data on a
single machine, using columnar data storage locally like an OLAP
database. 

- Apache Arrow is a CSV-alternative typed columnar data storage format
  that enables pandas-alternatives like [polars](https://github.com/pola-rs/polars).

- duckdb is a sqlite-like dead simple local database that uses
  columnar storage behind the scenes, and can be used as a backend for
  [Spark](https://duckdb.org/docs/api/python/spark_api) workflows
  
I [previously wrote](https://austinweisgrau.github.io/deduplicating-everyaction.html) about how at Working Families Party we use duckdb
as the backend for a machine learning identity resolution workflow
([splink](https://moj-analytical-services.github.io/splink/getting_started.html)).

For an overview of the larger trends in cloud computing and big data
transformations, see this really good article by Mother Duck, the
company behind DuckDB: [The Simple Joys of Scaling Up](https://motherduck.com/blog/the-simple-joys-of-scaling-up/)
