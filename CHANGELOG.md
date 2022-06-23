## lifebit-ai/cloudos-py: changelog

### 0.0.8bi - 2022-06-23
- Adds `verify=False` parameter to all `requests.get` and `requests.post`
calls. That effectively disables the SSL certification verification. That
was a temporary solution to the BI's certification problem.

### 0.0.8 - 2022-06-16
- Adds `--nextflow-profile` parameter to accept nextflow profiles. It
also makes `--job-config` parameter optional, as a run with only
profiles is possible.

### 0.0.7a - 2022-04-07
- Hotfix: extends the wait time from 1s to 60s when checking for job
status (`--wait-completion true`). This helps preventing API call
errors from CloudOS API server.

### 0.0.7 - 2021-03-10
- Adds support for aborted jobs
- Adds `--batch` option to `job` subtool to be able to use `batch`
executor instead of the default `ignite` in CloudOS.

### 0.0.6 - 2021-12-09
- Unittests added for method `process_job_list` from class `Cloudos`
- Unittests added for method `convert_nextflow_to_json` from class `Jobs`

### 0.0.5b - 2021-11-24
- Adds Cohort class

### 0.0.5 - 2021-11-16
- Adds `git-commit` and `--git-tag` optional arguments to 
`cloudos job run` to be able to set the github commit or tag
to run.

### 0.0.4 - 2021-10-15
- Changes `--job-params` to `--job-config`
- Removes the collection of the `project.description` column from the 
returned json when listing all jobs, as this column is not available
in all the CloudOS workspaces.

### 0.0.3 - 2021-09-08
- Adds `cloudos job list` command.
- Minor changes in `stdout` of the other commands to improve
readability.
- Adds a small docstring to each command.

### 0.0.2 - 2021-09-07
- Refactors `runjob` and `jobstatus` commands. Now, the main
`cloudos` tool have the `job` subtool which in turn has its
`run` and `status` commands performing the previous
functionality. This way, now the tool can be used with:
`cloudos job run [OPTIONS]` and `cloudos job status [OPTIONS]`.
- Adding `--wait-completion` option to `cloudos job run` command,
to be able to wait until job completion or failure.

### 0.0.1 - 2021-08-18
Initial implementation of the `cloudos` python package:
- Implements `runjob` and `jobstatus` commands to send jobs and get
their status, respectively.
