# cloudos

[![codecov](https://codecov.io/gh/lifebit-ai/cloudos-py/branch/main/graph/badge.svg?token=kTob8bynPx)](https://codecov.io/gh/lifebit-ai/cloudos-py)

__Date:__ 2022-07-14\
__Version:__ 0.1.2


Python package for interacting with CloudOS

## Requirements

The package requires Python >= 3.8 and the following python packages:

```
click
requests
pandas
```

## Installation

### Docker image
It is recommended to install it as a docker image using the `Dockerfile`
and the `environment.yml` files provided.

To run the existing docker image at `quay.io`:

```bash
docker run --rm -it quay.io/lifebitaiorg/cloudos-py:v0.1.2
```

### From Github

You will need Python >= 3.8 and pip installed.

Clone the repo and install it using pip:

```bash
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

```bash
cloudos --help
```
```console
Usage: cloudos [OPTIONS] COMMAND [ARGS]...

  CloudOS python package: a package for interacting with CloudOS.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  cromwell  Cromwell server functionality: check status, start and stop.
  job       CloudOS job functionality: run and check jobs in CloudOS.
  workflow  CloudOS workflow functionality: list workflows in CloudOS.
``` 

This will tell you the implemented commands. Each implemented command has its
own subcommands with its own `--help`:

```bash
cloudos job run --help
```
```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS job functionality: run and check jobs in CloudOS.

Usage: cloudos job run [OPTIONS]

  Submit a job to CloudOS.

Options:
  -k, --apikey TEXT            Your CloudOS API key  [required]
  -c, --cloudos-url TEXT       The CloudOS url you are trying to access to.
                               Default=https://cloudos.lifebit.ai.
  --workspace-id TEXT          The specific CloudOS workspace id.  [required]
  --project-name TEXT          The name of a CloudOS project.  [required]
  --workflow-name TEXT         The name of a CloudOS workflow or pipeline.
                               [required]
  --job-config TEXT            A config file similar to a nextflow.config
                               file, but only with the parameters to use with
                               your job.
  -p, --nextflow-profile TEXT  A comma separated string indicating the
                               nextflow profile/s to use with your job.
  --git-commit TEXT            The exact whole 40 character commit hash to run
                               for the selected pipeline. If not specified it
                               defaults to the last commit of the default
                               branch.
  --git-tag TEXT               The tag to run for the selected pipeline. If
                               not specified it defaults to the last commit of
                               the default branch.
  --job-name TEXT              The name of the job. Default=new_job.
  --resumable                  Whether to make the job able to be resumed or
                               not.
  --batch                      Whether to make use the batch executor instead
                               of the default ignite.
  --instance-type TEXT         The type of AMI to use. Default=c5.xlarge.
  --instance-disk INTEGER      The amount of disk storage to configure.
                               Default=500.
  --spot                       Whether to make a spot instance.
  --storage-mode TEXT          Either 'lustre' or 'regular'. Indicates if the
                               user wants to select regular or lustre storage.
                               Default=regular.
  --lustre-size INTEGER        The lustre storage to be used when --storage-
                               mode=lustre, in GB. It should be 1200 or a
                               multiple of it. Default=1200.
  --wait-completion            Whether to wait to job completion and report
                               final job status.
  --wait-time INTEGER          Max time to wait (in seconds) to job
                               completion. Default=3600.
  --wdl-mainfile TEXT          For WDL workflows, which mainFile (.wdl) is
                               configured to use.
  --wdl-importsfile TEXT       For WDL workflows, which importsFile (.zip) is
                               configured to use.
  -t, --cromwell-token TEXT    Specific Cromwell server authentication token.
                               Only required for WDL jobs.
  --repository-platform TEXT   Name of the repository platform of the
                               workflow. Default=github.
  --verbose                    Whether to print information messages or not.
  --help                       Show this message and exit.
```

#### Send a job to CloudOS

First, configure your local environment to ease parameters input. We will
try to submit a small toy example already available.

```bash
MY_API_KEY="xxxxx"
CLOUDOS="https://cloudos.lifebit.ai"
WORKSPACE_ID="xxxxx"
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
    --cloudos-url $CLOUDOS \
    --apikey $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --project-name "$PROJECT_NAME" \
    --workflow-name $WORKFLOW_NAME \
    --job-config $JOB_PARAMS \
    --resumable \
    --spot
```

If everything went well, you should see something like:

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS job functionality: run and check jobs in CloudOS.

Executing run...
	Job successfully launched to CloudOS, please check the following link: https://cloudos.lifebit.ai/app/jobs/62c83a1191fe06013b7ef355
	Your assigned job id is: 62c83a1191fe06013b7ef355
	Your current job status is: initializing
	To further check your job status you can either go to https://cloudos.lifebit.ai/app/jobs/62c83a1191fe06013b7ef355 or use the following command:
    cloudos job status \
        --apikey $MY_API_KEY \
        --cloudos-url https://cloudos.lifebit.ai \
        --job-id 62c83a1191fe06013b7ef355
```

As you can see, the current status is `initializing`. This will change
while the job progresses. To check the status, just apply the suggested
command.

Another option is to set the `--wait-completion` parameter, which run the same
job run command but waiting for its completion:

```bash
cloudos job run \
    --cloudos-url $CLOUDOS \
    --apikey $MY_API_KEY \
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

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS job functionality: run and check jobs in CloudOS.

Executing run...
	Job successfully launched to CloudOS, please check the following link: https://cloudos.lifebit.ai/app/jobs/62c83a6191fe06013b7ef363
	Your assigned job id is: 62c83a6191fe06013b7ef363
	Please, wait until job completion or max wait time of 3600 seconds is reached.
	Your current job status is: initializing.
	Your current job status is: running.
	Your job took 420 seconds to complete successfully.
```

#### Check job status

To check the status of a submitted job, just use the suggested command:

```bash
cloudos job status \
    --apikey $MY_API_KEY \
    --cloudos-url $CLOUDOS \
    --job-id 62c83a1191fe06013b7ef355
```

The expected output should be something similar to:

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS job functionality: run and check jobs in CloudOS.

Executing status...
	Your current job status is: completed

	To further check your job status you can either go to https://cloudos.lifebit.ai/app/jobs/62c83a1191fe06013b7ef355 or repeat the command you just used.
```

#### Get a list of your jobs from a CloudOS workspace

You can get a summary of your last 30 submitted jobs in two different formats:

- CSV: this is a table with a minimum predefined set of columns by default, or all the
available columns using the `--all-fields` argument.
- JSON: all the available information from your jobs, in JSON format.

To get a list with your last 30 submitted jobs to a given workspace, in CSV format, use
the following command:

```bash
cloudos job list \
    --cloudos-url $CLOUDOS \
    --apikey $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --output-format csv \
    --all-fields
```

The expected output is something similar to:

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS job functionality: run and check jobs in CloudOS.

Executing list...
	Job list collected with a total of 30 jobs.
	Job list saved to joblist.csv
```

In addition, a file named `joblist.csv` is created.

To get the same information, but in JSON format, use the following command:

```bash
cloudos job list \
    --cloudos-url $CLOUDOS \
    --apikey $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --output-format json
```
```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS job functionality: run and check jobs in CloudOS.

Executing list...
	Job list collected with a total of 30 jobs.
	Job list saved to joblist.json
```

#### Get a list of all available workflows from a CloudOS workspace

You can get a summary of all the available workspace workflows in two different formats:
- CSV: this is a table with a minimum predefined set of columns by default, or all the
available columns using the `--all-fields` parameter.
- JSON: all the available information from workflows, in JSON format.

To get a CSV table with all the available workflows for a given workspace, use
the following command:

```bash
cloudos workflow list \
    --cloudos-url $CLOUDOS \
    --apikey $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --output-format csv \
    --all-fields
```

The expected output is something similar to:

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS workflow functionality: list workflows in CloudOS.

Executing list...
	Workflow list collected with a total of 609 workflows.
	Workflow list saved to workflow_list.csv
```

To get the same information, but in JSON format, use the following command:

```bash
cloudos workflow list \
    --cloudos-url $CLOUDOS \
    --apikey $MY_API_KEY \
    --workspace-id $WORKSPACE_ID \
    --output-format json
```

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS workflow functionality: list workflows in CloudOS.

Executing list...
	Workflow list collected with a total of 609 workflows.
	Workflow list saved to workflow_list.json
```

### WDL pipeline support

#### Cromwell server managing

In order to run WDL pipelines, a Cromwell server in CloudOS should be running. This server can
be accessed to check its status, restart it or stop it, using the following commands:

```bash
# Cromwell server requires its particular token
CROMWELL_TOKEN="xxxx"

# Check Cromwell status
cloudos cromwell status \
    -c $CLOUDOS \
    -t $CROMWELL_TOKEN \
    --workspace-id $WORKSPACE_ID
```

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

Cromwell server functionality: check status, start and stop.

Executing status...
	Current Cromwell server status is: Stopped
```

```bash    
# Cromwell start
cloudos cromwell start \
    -c $CLOUDOS \
    -t $CROMWELL_TOKEN \
    --workspace-id $WORKSPACE_ID
```

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

Cromwell server functionality: check status, start and stop.

Starting Cromwell server...
	Current Cromwell server status is: Initializing

	Current Cromwell server status is: Running
```

```bash
# Cromwell stop
cloudos cromwell stop \
    -c $CLOUDOS \
    -t $CROMWELL_TOKEN \
    --workspace-id $WORKSPACE_ID
```

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

Cromwell server functionality: check status, start and stop.

Stopping Cromwell server...
	Current Cromwell server status is: Stopped
```

#### Running WDL workflows

To run WDL workflows, `cloudos job run` command can be used normally, but adding two extra
parameters:

- `--wdl-mainfile`: name of the mainFile (*.wdl) file used by the CloudOS workflow.
- `--wdl-importsfile`: name of the worfklow imported file (importsFile, *.zip).
- `--cromwell-token`: specific token for Cromwell server, different from the presonal API token.

All the rest of the `cloudos job run` functionality is available.

> NOTE: WDL does not support `profiles` and therefore, `--nextflow-profile` option is not
available. Instead, only `--job-config` could be used. The format of the job config file is
expected to be the same as for nextflow pipelines.

Example of job config file for WDL workflows:

```bash
params {
 test.hello.name = aasdajdad
  test.bye.nameTwo = asijdadads
  test.number.x = 2
  test.greeter.morning = true
  test.wf_hello_in = bomba
  test.arrayTest = ["lala"]
  test.mapTest = {"some":"props"}
}
```

```bash
# Configure variables
MY_API_KEY="xxxxx"
CROMWELL_TOKEN="xxxx"
CLOUDOS="https://cloudos.lifebit.ai"
WORKSPACE_ID="xxxxx"
PROJECT_NAME="wdl-test"
WORKFLOW_NAME="wdl- test"
MAINFILE="hello.wdl"
IMPORTSFILE="imports_7mb.zip"
JOB_PARAMS="cloudos/examples/wdl.config"

# Run job
cloudos job run \
  --cloudos-url $CLOUDOS \
  --apikey $MY_API_KEY \
  --workspace-id $WORKSPACE_ID \
  --project-name $PROJECT_NAME \
  --workflow-name "$WORKFLOW_NAME" \
  --wdl-mainfile $MAINFILE \
  --wdl-importsfile $IMPORTSFILE \
  --cromwell-token $CROMWELL_TOKEN \
  --job-config $JOB_PARAMS \
  --wait-completion
```

```console
CloudOS python package: a package for interacting with CloudOS.

Version: 0.1.2

CloudOS job functionality: run and check jobs in CloudOS.

Executing run...
    WDL workflow detected

    Current Cromwell server status is: Stopped

    Starting Cromwell server...

    Current Cromwell server status is: Initializing


    Current Cromwell server status is: Running

    *******************************************************************************
    [WARNING] Cromwell server is now running. Plase, remember to stop it when your
    job finishes. You can use the following command:
    cloudos cromwell stop \
        --cromwell-token $CROMWELL_TOKEN \
        --cloudos-url $CLOUDOS \
        --workspace-id $WORKSPACE_ID
    *******************************************************************************

	Job successfully launched to CloudOS, please check the following link: ****
	Your assigned job id is: ****
	Please, wait until job completion or max wait time of 3600 seconds is reached.
	Your current job status is: initializing.
	Your current job status is: running.
	Your job took 60 seconds to complete successfully.
```

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
cromwell_token = 'xxxx'
cloudos_url = 'https://cloudos.lifebit.ai'
workspace_id = 'xxxxx'
project_name = 'API jobs'
workflow_name = 'rnatoy'
job_config = 'cloudos/examples/rnatoy.config'
```

First, create the `Job` object:

```python
j = jb.Job(cloudos_url, apikey, cromwell_token, workspace_id, project_name, workflow_name)
print(j)
```

Then, send the job:

```python
j_id = j.send_job(job_config)
```

To check the status:

```python
j_status = j.get_job_status(j_id)
j_status_h = json.loads(j_status.content)["status"]
print(j_status_h)
```

The status will change while your job progresses, so to check again just
repeat the above code.

You can also collect your last 30 submitted jobs for a given workspace using the
following command.

```python
my_jobs_r = j.get_job_list(workspace_id)
my_jobs = j.process_job_list(my_jobs_r)
print(my_jobs)
```

Or inspect all the available workflows for a given workspace using the
following command.

```python
my_workflows_r = j.get_workflow_list(workspace_id)
my_workflows = j.process_workflow_list(my_workflows_r)
print(my_workflows)
```

#### Running WDL pipelines using your own scripts

You can even run WDL pipelines. First check the Cromwell server status and restart it if Stopped:

```python
import cloudos.clos as cl
import cloudos.jobs.job as jb
import json


# GLOBAL VARS.
apikey = 'xxxxx'
cromwell_token = 'xxxx'
cloudos_url = 'https://cloudos.lifebit.ai'
workspace_id = 'xxxxx'
project_name = 'wdl-test'
workflow_name = 'wdl- test'
mainfile = 'hello.wdl'
importsfile = 'imports_7mb.zip'
job_config = 'cloudos/examples/wdl.config'

# First create cloudos object
cl = cl.Cloudos(cloudos_url, apikey, cromwell_token)

# Then, check Cromwell status
c_status = cl.get_cromwell_status(workspace_id)
c_status_h = json.loads(c_status.content)["status"]
print(c_status_h)

# Start Cromwell server
cl.cromwell_switch(workspace_id, 'restart')

# Check again Cromwell status (wait until status: 'Running')
c_status = cl.get_cromwell_status(workspace_id)
c_status_h = json.loads(c_status.content)["status"]
print(c_status_h)

# Send a job (wait until job has status: 'Completed')
j = jb.Job(cloudos_url, apikey, cromwell_token, workspace_id, project_name, workflow_name, mainfile,
           importsfile)
j_id = j.send_job(job_config, workflow_type='wdl', cromwell_id=json.loads(c_status.content)["_id"])
j_status = j.get_job_status(j_id)
j_status_h = json.loads(j_status.content)["status"]
print(j_status_h)

# Stop Cromwell server
cl.cromwell_switch(workspace_id, 'stop')

# Check again Cromwell status
c_status = cl.get_cromwell_status(workspace_id)
c_status_h = json.loads(c_status.content)["status"]
print(c_status_h)
```

### unit testing

Unit tests require 3 additional packages:

```
requests-mock
pandas
pytest
```

Currently the Clos class function process_job_list and the Job class convert_nextflow_to_json are tested. To run untests run 

```
python -m pytest -s -v
``` 

from the cloudos-py main folder and 7 tests should pass. 
