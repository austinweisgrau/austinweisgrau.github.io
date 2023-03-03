title: Migration to Prefect. Part 1: Civis Woes
date: 2023-02-22

This is the first post in a series of blog posts about our migration
to Prefect at Working Families Party. I'll start by describing our
current orchestration and execution platform, Civis, and its many
limitations.

[Civis](https://civisanalytics.com) is a widely used platform across the progressive space. This is
largely because access to Civis is included with membership in [The
Movement Cooperative](https://movementcooperative.org/), and is an afforadable and accessible platform
for writing and running SQL and python in a cloud environment. 

The Civis web app is intended to be easy to use for staff who aren't
necessarily engineers. There are many integrations that make Civis
especially simple to use in some cases, for example running a SQL
query and loading new rows to a Google Sheet. Civis has a lot going
for it and there are good reasons it is popular.

However, Civis is not really an appropriate production tool for a
mature data or engineering team. Civis has many limitations, and many
of its design choices in favor of ease-of-use end up as liabilities in
the long term. For any team that is regularly running SQL and python
scripts with nontrivial logic, it is important to explore issues with
Civis as a production tool.

## Version control

Version control is a critically important tool for engineering at
every level. It enables collaboration, oversight, institutional
memory, an additional form of documentation, and more. There are tons
of resources online expounding the benefits and necessities of version
control.

Using Civis as a production environment severely limits the extent to
which version controlling is possible. This problem alone is
significant enough to make Civis a bad choice, even if there were no
other issues. 

Scripts that are stored in Civis are not version controlled. It is
possible to exclusively use Civis container scripts to run scripts
that are version controlled through Civis. But even in that scenario,
none of the configuration parameters, automated scheduling, workflow
dependencies, or credentials are version controlled. 

Much more common is to have a large proliferation of production and
development scripts stored, shared and run exclusively in Civis.

As an example to demonstrate why this is problematic, imagine
that a team member accidentally deletes a single character from a SQL
script while they are reading the script one day, causing the output
of the SQL script to change slightly in a problematic way that isn't
obvious. Next week, another team notices that there are issues in a
database table that didn't previously exist. Your job is to determine
why this table isn't populating correctly, even though officially no
one has touched any of the relevant code in many months.

If the pipeline is complicated in any way, you will have to pull up
each individual script in Civis and check to see if the file was
updated recently. You find that this SQL script was updated last week,
but you can't see what the change was. You have to parse and test the
entire SQL script manually to determine why the results aren't correct,
and invent a new solution that hopefully restores the original intended
behavior. 

If version control was in place, your first step would be to check the
logs, and see that a small change was made last week that wasn't
intended, and to revert the change. More realistically, the change
would never have been made, because your team member would have had to
commit the change, issue a PR, have the PR approved, and merge the
change before it showed up in the production environment at all.

There are many, many other scenarios where version control is a
critical element of keeping a team functioning in the long term.

## Permissions and visibility

Civis lacks an effective way to administer permissions and access to
resources between users. No user can be granted access to everything
in Civis. Instead, each individual user must manually share their
assets with other users. If a user doesn't have access to an asset in
Civis, Civis will report that the asset does not exist, rather than
identifying the permissions issue.

This is problematic because it means team members can create scripts
that run on production services without that activity being visible to
anyone else. There is no way to compile a list of all Civis scripts
running on production services and be sure that it is a complete
list. This creates a fundamental problem with oversight.

## Environment variables

A Civis container can run a python script fetched from a github repo
on a Docker container of your choosing. A common pattern for fetching
credentials in python is to fetch them from environment variables
that aren't directly stored in the code. Environment variables can be
set in Civis container scripts as "Parameters." Parameters can be set
to credentials that are saved separately at a User level in Civis.

Credentials saved in Civis can ONLY be made availabe in the
environment using a `_USERNAME` and `_PASSWORD` suffix. That is, if
your credential is named `SLACK_API_KEY`, Civis forces you to make
secret values available in the environment using keys
`SLACK_API_KEY_USERNAME` and `SLACK_API_KEY_PASSWORD`. This choice clearly
doesn't always make sense and requires a workaround for every
credential that does not fit this pattern.

Setting up civis scripts with parameters and credentials is a somewhat
tedious manual process. The Civis API does make some, but not all, of
this process scriptable.

## Programmatic configuration of orchestration

Often data pipelines will have some non-trivial logic for how and when
different steps should be triggered, which steps are dependent on
others to complete first, etc. It is possible to set up these kinds of
dependencies and automated scheduling in Civis using the web
app. Automated scheduling is also possible to set up using the API,
however as far as I can tell, it is not possible programmatically
configure dependent workflows outside of the GUI.

Orchestration logic reflects important technical and business
considerations and should not be exclusively configured in a
web app. Having a web-app-first or web-app-exclusive interface for
configuring orchestration means that changes to the configuration
can happen without anyone noticing, and reverting changes can be
difficult. Orchestration logic should be explicitly configured in the
same version-controlled code repository that the code itself lives
in.

## Conclusion

Hopefully this blog post illustrates some of the important limitations
on using Civis as a production platform for a data or engineering
team. Civis has its benefits that are appropriate in certain
circumstances, but a team of any maturity should be careful to avoid
leaning on Civis for any critical workflows.