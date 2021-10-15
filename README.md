# cloudos

__Date:__ 2021-10-15\
__Version:__ 0.0.4

Python package for interacting with CloudOS

## Requirements

The package requires Python >= 3.8 and the following python packages:

```
click
requests
```

## Installation

### Docker image
It is recommended to install it as a docker image using the `Dockerfile`
and the `environment.yml` files provided.

To run the existing docker image at `quay.io`:

```
docker run --rm -it quay.io/lifebitai/cloudos-py:v0.0.4
```

### From Github

You will need Python >= 3.8 and pip installed.

Clone the repo and install it using pip:

```
git clone https://github.com/lifebit-ai/cloudos-py
cd cloudos-py
pip install -r requirements.txt
pip install .
```

## Usage

The package is meant to be used both as a CLI tool and as a regular package to
import to your own scripts.

### Usage as a Command Line Interface tool

To get general information about the tool:

```
$ cloudos --help
Usage: cloudos [OPTIONS] COMMAND [ARGS]...

  CloudOS python package: a package for interacting with CloudOS.

Options:
  --help  Show this message and exit.

Commands:
  job  CloudOS job functionality: run and check jobs in CloudOS.
``` 

This will tell you the implemented commands. Each implemented command has its
own subcommands with its own `--help`:

```
$ cloudos job run --help
CloudOS python package: a package for interacting with CloudOS.

CloudOS job functionality: run and check jobs in CloudOS.

Usage: cloudos job run [OPTIONS]

  Submit a job to CloudOS.

Options:
  -k, --apikey TEXT        Your CloudOS API key  [required]
  -c, --cloudos-url TEXT   The CloudOS url you are trying to access to.
                           Default=https://cloudos.lifebit.ai.
  --workspace-id TEXT      The specific CloudOS workspace id.  [required]
  --project-name TEXT      The name of a CloudOS project.  [required]
  --workflow-name TEXT     The name of a CloudOS workflow or pipeline.
                           [required]
  --job-config TEXT        A nextflow.config file or similar, with the
                           parameters to use with your job.  [required]
  --job-name TEXT          The name of the job. Default=new_job.
  --resumable              Whether to make the job able to be resumed or not.
  --instance-type TEXT     The type of AMI to use. Default=c5.xlarge.
  --instance-disk INTEGER  The amount of disk storage to configure.
                           Default=500.
  --spot                   Whether to make a spot instance.
  --wait-completion        Whether to wait to job completion and report final
                           job status.
  --wait-time INTEGER      Max time to wait (in seconds) to job completion.
                           Default=3600.
  --verbose                Whether to print information messages or not.
  --help                   Show this message and exit.
```

#### Send a job to CloudOS

First, configure your local environment to ease parameters input. We will
try to submit a small toy example already available.

```bash
MY_API_KEY="xxxxx"
WORKSPACE_ID="5c6d3e9bd954e800b23f8c62"
PROJECT_NAME="API jobs"
WORKFLOW_NAME="rnatoy"
JOB_PARAMS="cloudos/examples/rnatoy.config"
```

As you can see, a file with the job parameters is required to configure the
job. This file could be a regular `nextflow.config` file or any file with the
following structure:

```
params {
    reads   = s3://lifebit-featured-datasets/pipelines/rnatoy-data
    genome  = s3://lifebit-featured-datasets/pipelines/rnatoy-data/ggal_1_48850000_49020000.Ggal71.500bpflank.fa
    annot   = s3://lifebit-featured-datasets/pipelines/rnatoy-data/ggal_1_48850000_49020000.bed.gff
}
```

To submit our job:

```bash
cloudos job run \
    -k $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --project-name "$PROJECT_NAME" \
    --workflow-name $WORKFLOW_NAME \
    --job-config $JOB_PARAMS \
    --resumable \
    --spot
```

If everything went well, you should see something like:

```
CloudOS python package: a package for interacting with CloudOS.

CloudOS job functionality: run and check jobs in CloudOS.

Executing run...
	Job successfully launched to CloudOS, please check the following link: https://cloudos.lifebit.ai/app/jobs/6138ec6e31de9201a5bf3786
	Your assigned job id is: 6138ec6e31de9201a5bf3786
	Your current job status is: initializing
	To further check your job status you can either go to https://cloudos.lifebit.ai/app/jobs/6138ec6e31de9201a5bf3786 or use the following command:
cloudos job status \
    --apikey $MY_API_KEY \
    --cloudos-url https://cloudos.lifebit.ai \
    --job-id 6138ec6e31de9201a5bf3786

```

As you can see, the current status is `initializing`. This will change
while the job progresses. To check the status, just apply the suggested
command.

Another option is to set the `--wait-completion` parameter, which run the same
job run command but waiting for its completion:

```bash
cloudos job run \
    -k $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --project-name "$PROJECT_NAME" \
    --workflow-name $WORKFLOW_NAME \
    --job-config $JOB_PARAMS \
    --resumable \
    --spot \
    --wait-completion
```

If the job takes less than `--wait-time` (3600 seconds by default), the
previous command should have an output similar to:

```
CloudOS python package: a package for interacting with CloudOS.

CloudOS job functionality: run and check jobs in CloudOS.

Executing run...
	Job successfully launched to CloudOS, please check the following link: https://cloudos.lifebit.ai/app/jobs/6138f04331de9201a5bf387d
	Your assigned job id is: 6138f04331de9201a5bf387d
	Please, wait until job completion or max wait time of 3600 seconds is reached.
	Your current job status is: initializing.
	Your current job status is: running.
	Your job took 303 seconds to complete successfully.
```

#### Check job status

To check the status of a submitted job, just use the suggested command:

```bash
cloudos job status \
    --apikey $MY_API_KEY \
    --cloudos-url https://cloudos.lifebit.ai \
    --job-id 6138ec6e31de9201a5bf3786
```

You will see the following output while the job is running:

```
CloudOS python package: a package for interacting with CloudOS.

CloudOS job functionality: run and check jobs in CloudOS.

Executing status...
	Your current job status is: running

	To further check your job status you can either go to https://cloudos.lifebit.ai/app/jobs/6138ec6e31de9201a5bf3786 or repeat the command you just used.
```

And eventually, if everything went correctly:

```
CloudOS python package: a package for interacting with CloudOS.

CloudOS job functionality: run and check jobs in CloudOS.

Executing status...
	Your current job status is: completed

	To further check your job status you can either go to https://cloudos.lifebit.ai/app/jobs/6138ec6e31de9201a5bf3786 or repeat the command you just used.
```

#### Get a list of all your jobs from a CloudOS workspace

To get a CSV table with all of your submitted jobs to a given workspace, use
the following command:

```bash
cloudos job list \
    --apikey $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --outfile my_job_list.csv
```

The expected output is something similar to:

```
CloudOS python package: a package for interacting with CloudOS.

CloudOS job functionality: run and check jobs in CloudOS.

Executing list...
	Job list collected with a total of 19 jobs.
	Job list table saved to my_job_list.csv
```

In addition, a file named `my_job_list.csv` is created, with all your jobs
information, in CSV format.

### Import the functionality to your own python scripts

To illustrate how to import the package and use its functionality inside
your own python scripts, we will perform a job submission and check its
status from inside a python script.

Again, we will set up the environment to ease the work:

```python
import cloudos.jobs.job as jb
import json


# GLOBAL VARS.
apikey = 'xxxxx'
cloudos_url = 'https://cloudos.lifebit.ai'
workspace_id = '5c6d3e9bd954e800b23f8c62'
project_name = 'API jobs'
workflow_name = 'rnatoy'
job_config = 'cloudos/examples/rnatoy.config'
job_name = 'new_job'
resumable = True
instance_type = 'c5.xlarge'
instance_disk = 500
spot = True
```

First, create the `Job` object:

```python
j = jb.Job(apikey, cloudos_url, workspace_id, project_name, workflow_name)
print(j)
```

Then, send the job:

```python
j_id = j.send_job(job_config,
                  job_name,
                  resumable,
                  instance_type,
                  instance_disk,
                  spot)
```

To check the status:

```python
j_status = j.get_job_status(j_id)
j_status_h = json.loads(j_status.content)["status"]
print(j_status_h)
```

The status will change while your job progresses, so to check again just
repeat the above code.

You can also collect all your submitted jobs for a given workspace using the
following command.

```python
my_jobs_r = j.get_job_list(workspace_id)
my_jobs = j.process_job_list(my_jobs_r)
print(my_jobs)
```
