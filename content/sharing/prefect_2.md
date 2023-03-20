title: Prefect Execution Layer: AWS ECS with a dedicated IP address
date: 2023-03-07

# Migrating to Prefect, Part 2: Prefect & AWS ECS

In my [previous blog post](), I explained the limitations with Civis
as a production tool for a data/engineering team. These limitations
led our data team at Working Families Party to choose to move our
orchestration tooling off of Civis and into another tool. After
evaluating a few tools, we have chosen to use Prefect.

This post will explain how we set up Prefect and some of the choices
we made along the way. You can follow along with the full set up as a
template repository [here](https://github.com/austinweisgrau/prefect-ecs-template).

First, just one vocabulary word that will make the rest of this post
more readable:

- Prefect "Flow": this is more generically called a script or data
  pipeline. Prefect is fundamentally about the orchestration and
  execution of flows.

## Orchestration and Execution in Prefect

Orchestration tools handle the separation of orchestration and
execution differently. Some tools, like Civis and Airflow, handle both
of these in the same layer. The same platform that schedules and
triggers workflows is also responsible for executing them, often in
the same compute environment.

Prefect handles this a bit differently and clearly separates the
orchestration and compute layers. The orchestration layer is run in an
"Orion" server instance, which is a web application with a UI for
viewing and interacting with prefect assets. Prefect offers a managed,
hosted version of the Orion server called the Prefect Cloud, with a
generous free tier.

The prefect execution layer happens separately, and there is currently
no managed option. A prefect "agent" is a program that runs in the
execution environment, frequently polls the prefect orion server, and
executes any flows that have been triggered by the server. Prefect
users are responsible for setting up the environment for a prefect
agent to run.

## Cloud execution options

While it is possible to run prefect flows locally, for example on the
laptops of your team's staff, a more common solution is to run a
prefect agent in a cloud computing environment. There are many
different ways to accomplish this.

A common method is to use cloud "serverless" compute infrastructure to
run the prefect agent. Some popular options include AWS EC2, AWS ECS,
Azure Container Apps, or Google Cloud Run.

Some organizations with more resources might even choose to run their
execution layer in a cloud-hosted Kubernetes cluster. Kubernetes is
very configurable and scalable, but has a steeper and more complicated
learning curve.

## Tutorials and templates

One of the limitations of using prefect is that the tool is newer, the
community is smaller, and there are not a ton of resources available
yet from the community demonstrating how to accomplish various
set-ups. However, there are a few excellent templates and tutorials
for getting the Prefect execution layer set up in various cloud
environments.

We used this [tutorial](https://towardsdatascience.com/prefect-aws-ecs-fargate-github-actions-make-serverless-dataflows-as-easy-as-py-f6025335effc) and [template](https://github.com/anna-geller/dataflow-ops) to get our set up started in AWS
ECS. We chose to use AWS ECS largely because we use AWS Redshift and
AWS S3 as our primary database and data storage layers, and there are
significant performance benefits to using AWS services together.

Alternatively, [this tutorial](https://medium.com/@nwosupaul141/serverless-deployment-of-a-prefect-data-pipeline-on-google-cloud-run-8c48765f2480) looks good for getting started in Google
Cloud Run. We may switch to this implementation if we end up moving
off of Redshift and into Google Biguery at some point.

## Needing a dedicated IP for access to TMC redshift

There are some modifications we needed to make to the dataflow-ops
template to fit our needs. You can see our modified version of the
dataflow-ops template [here](https://github.com/austinweisgrau/prefect-ecs-template).

First, we needed to enable a dedicated IP address for our execution
layer so that we could have our IP address whitelisted by TMC in order
to access the Redshift instance. Setting up a dedicated IP address for
an ECS Task involved an understanding of some networking concepts and
tools in AWS.

The dataflow-ops template included an AWS CloudFormation Script for
setting up the ECS Task and its networking infrastructure. I modified
that script using [this template](https://gist.github.com/jbesw/f9401b4c52a7446ef1bb71ceea8cc3e8) to enable the use of an "elastic IP"
address in AWS for our ECS tasks. I also needed to modify the
`prefect_aws.ECSTask` block stored in our Prefect Cloud instance to
always use the correct VPC subnets (see our [full configuration script
for CloudFormation here](https://github.com/austinweisgrau/prefect-ecs-template/blob/main/infrastructure/ecs_cluster_prefect_agent.yml)).

## Deploying Changes

There are two different ways a prefect flow can be deployed which
determine how the code is passed to the prefect agent and
executed.

1. The prefect agent and/or ECSTask can run on a docker image that
   contains the flow code
2. The [flow deployment can be built](https://docs.prefect.io/concepts/deployments/#deployment-build-options) with a [cloud "storage block"](https://docs.prefect.io/concepts/deployments/#block-identifiers) (for
   example, S3), where the flow code will be uploaded on deployment
   and downloaded when the flow is triggered by the agent to run.
   
When changes are made to flow code, the updates can be pushed into
production either by recreating and reuploading the docker image for
strategy 1, or by rebuilding the flow deployment using a storage block
for strategy 2, which uploads the new code to the storage block.

I found the docker strategy to be somewhat simpler, so I modified the
Github Actions deployment script included in the dataflow-ops template
to rebuild and reupload the docker image anytime the code is
updated. Our flow deployments do not include a storage block.

See our [deployment Github Actions script here](https://github.com/austinweisgrau/prefect-ecs-template/blob/main/.github/workflows/main.yaml).


