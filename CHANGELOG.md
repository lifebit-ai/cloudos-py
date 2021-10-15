## lifebit-ai/cloudos-py: changelog

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
