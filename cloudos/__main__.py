#!/usr/bin/env python3

import click
import cloudos.jobs.job as jb
from cloudos.clos import Cloudos
import json
import time
import sys
from ._version import __version__

# GLOBAL VARS
JOB_COMPLETED = 'completed'
JOB_FAILED = 'failed'
JOB_ABORTED = 'aborted'
REQUEST_INTERVAL = 30


@click.group()
@click.version_option(__version__)
def run_cloudos_cli():
    """CloudOS python package: a package for interacting with CloudOS."""
    print(run_cloudos_cli.__doc__ + '\n')
    print('Version: ' + __version__ + '\n')


@run_cloudos_cli.group()
def job():
    """CloudOS job functionality: run and check jobs in CloudOS."""
    print(job.__doc__ + '\n')


@run_cloudos_cli.group()
def workflow():
    """CloudOS workflow functionality: list workflows in CloudOS."""
    print(workflow.__doc__ + '\n')


@run_cloudos_cli.group()
def cromwell():
    """Cromwell server functionality: check status, start and stop."""
    print(cromwell.__doc__ + '\n')


@job.command('run')
@click.option('-k',
              '--apikey',
              help='Your CloudOS API key',
              required=True)
@click.option('-c',
              '--cloudos-url',
              help=('The CloudOS url you are trying to access to. ' +
                    'Default=https://cloudos.lifebit.ai.'),
              default='https://cloudos.lifebit.ai')
@click.option('--workspace-id',
              help='The specific CloudOS workspace id.',
              required=True)
@click.option('--project-name',
              help='The name of a CloudOS project.',
              required=True)
@click.option('--workflow-name',
              help='The name of a CloudOS workflow or pipeline.',
              required=True)
@click.option('--job-config',
              help=('A config file similar to a nextflow.config file, ' +
                    'but only with the parameters to use with your job.'))
@click.option('-p',
              '--parameter',
              multiple=True,
              help=('A single parameter to pass to the job call. It should be in the ' +
                    'following form: parameter_name=parameter_value. E.g.: ' +
                    '-p input=s3://path_to_my_file. You can use this option as many ' +
                    'times as parameters you want to include.'))
@click.option('--nextflow-profile',
              help=('A comma separated string indicating the nextflow profile/s ' +
                    'to use with your job.'))
@click.option('--git-commit',
              help=('The exact whole 40 character commit hash to run for ' +
                    'the selected pipeline. ' +
                    'If not specified it defaults to the last commit ' +
                    'of the default branch.'))
@click.option('--git-tag',
              help=('The tag to run for the selected pipeline. ' +
                    'If not specified it defaults to the last commit ' +
                    'of the default branch.'))
@click.option('--job-name',
              help='The name of the job. Default=new_job.',
              default='new_job')
@click.option('--resumable',
              help='Whether to make the job able to be resumed or not.',
              is_flag=True)
@click.option('--batch',
              help='Whether to make use the batch executor instead of the default ignite.',
              is_flag=True)
@click.option('--instance-type',
              help='The type of AMI to use. Default=c5.xlarge.',
              default='c5.xlarge')
@click.option('--instance-disk',
              help='The amount of disk storage to configure. Default=500.',
              type=int,
              default=500)
@click.option('--spot',
              help='Whether to make a spot instance.',
              is_flag=True)
@click.option('--storage-mode',
              help=('Either \'lustre\' or \'regular\'. Indicates if the user wants to select ' +
                    'regular or lustre storage. Default=regular.'),
              default='regular')
@click.option('--lustre-size',
              help=('The lustre storage to be used when --storage-mode=lustre, in GB. It should ' +
                    'be 1200 or a multiple of it. Default=1200.'),
              type=int,
              default=1200)
@click.option('--wait-completion',
              help=('Whether to wait to job completion and report final ' +
                    'job status.'),
              is_flag=True)
@click.option('--wait-time',
              help=('Max time to wait (in seconds) to job completion. ' +
                    'Default=3600.'),
              default=3600)
@click.option('--wdl-mainfile',
              help='For WDL workflows, which mainFile (.wdl) is configured to use.',)
@click.option('--wdl-importsfile',
              help='For WDL workflows, which importsFile (.zip) is configured to use.',)
@click.option('-t',
              '--cromwell-token',
              help='Specific Cromwell server authentication token. Only required for WDL jobs.')
@click.option('--repository-platform',
              help='Name of the repository platform of the workflow. Default=github.',
              default='github')
@click.option('--cost-limit',
              help='Add a cost limit to your job. Default=-1 (no cost limit).',
              type=float,
              default=-1)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def run(apikey,
        cloudos_url,
        workspace_id,
        project_name,
        workflow_name,
        job_config,
        parameter,
        git_commit,
        git_tag,
        job_name,
        resumable,
        batch,
        nextflow_profile,
        instance_type,
        instance_disk,
        spot,
        storage_mode,
        lustre_size,
        wait_completion,
        wait_time,
        wdl_mainfile,
        wdl_importsfile,
        cromwell_token,
        repository_platform,
        cost_limit,
        verbose):
    """Submit a job to CloudOS."""
    print('Executing run...')
    if verbose:
        print('\t...Detecting workflow type')
    cl = Cloudos(cloudos_url, apikey, cromwell_token)
    workflow_type = cl.detect_workflow(workflow_name, workspace_id)
    if workflow_type == 'wdl':
        print('\tWDL workflow detected\n')
        if wdl_mainfile is None:
            raise ValueError('Please, specify WDL mainFile using --wdl-mainfile <mainFile>.')
        if wdl_importsfile is None:
            raise ValueError('Please, specify WDL importsFile using --wdl-importsfile <importsFile>.')
        if cromwell_token is None:
            raise ValueError('Please, specify a valid Cromwell token using --cromwell-token <xxx>.')
        c_status = cl.get_cromwell_status(workspace_id)
        c_status_h = json.loads(c_status.content)["status"]
        print(f'\tCurrent Cromwell server status is: {c_status_h}\n')
        if c_status_h == 'Stopped':
            print('\tStarting Cromwell server...\n')
            cl.cromwell_switch(workspace_id, 'restart')
            elapsed = 0
            while elapsed < 300 and c_status_h != 'Running':
                c_status_old = c_status_h
                time.sleep(REQUEST_INTERVAL)
                elapsed += REQUEST_INTERVAL
                c_status = cl.get_cromwell_status(workspace_id)
                c_status_h = json.loads(c_status.content)["status"]
                if c_status_h != c_status_old:
                    print(f'\tCurrent Cromwell server status is: {c_status_h}\n')
        if c_status_h != 'Running':
            raise Exception('Cromwell server did not restarted properly.')
        cromwell_id = json.loads(c_status.content)["_id"]
        print('\t' + ('*' * 80) + '\n' +
              '\t[WARNING] Cromwell server is now running. Please, remember to stop it when ' +
              'your\n' + '\tjob finishes. You can use the following command:\n' +
              '\tcloudos cromwell stop \\\n' +
              '\t\t--cromwell-token $CROMWELL_TOKEN \\\n' +
              f'\t\t--cloudos-url {cloudos_url} \\\n' +
              f'\t\t--workspace-id {workspace_id}\n' +
              '\t' + ('*' * 80) + '\n')
    else:
        cromwell_id = None
    if verbose:
        print('\t...Preparing objects')
    j = jb.Job(cloudos_url, apikey, None, workspace_id, project_name, workflow_name,
               mainfile=wdl_mainfile, importsfile=wdl_importsfile,
               repository_platform=repository_platform)
    if verbose:
        print('\tThe following Job object was created:')
        print('\t' + str(j))
        print('\t...Sending job to CloudOS\n')
    j_id = j.send_job(job_config,
                      parameter,
                      git_commit,
                      git_tag,
                      job_name,
                      resumable,
                      batch,
                      nextflow_profile,
                      instance_type,
                      instance_disk,
                      spot,
                      storage_mode,
                      lustre_size,
                      workflow_type,
                      cromwell_id,
                      cost_limit)
    print(f'\tYour assigned job id is: {j_id}')
    j_url = f'{cloudos_url}/app/jobs/{j_id}'
    if wait_completion:
        print('\tPlease, wait until job completion or max wait time of ' +
              f'{wait_time} seconds is reached.')
        elapsed = 0
        j_status_h_old = ''
        while elapsed < wait_time:
            j_status = j.get_job_status(j_id)
            j_status_h = json.loads(j_status.content)["status"]
            if j_status_h == JOB_COMPLETED:
                print(f'\tYour job took {elapsed} seconds to complete ' +
                      'successfully.')
                sys.exit(0)
            elif j_status_h == JOB_FAILED:
                print(f'\tYour job took {elapsed} seconds to fail.')
                sys.exit(1)
            elif j_status_h == JOB_ABORTED:
                print(f'\tYour job took {elapsed} seconds to abort.')
                sys.exit(1)
            else:
                elapsed += REQUEST_INTERVAL
                if j_status_h != j_status_h_old:
                    print(f'\tYour current job status is: {j_status_h}.')
                    j_status_h_old = j_status_h
                time.sleep(REQUEST_INTERVAL)
        j_status = j.get_job_status(j_id)
        j_status_h = json.loads(j_status.content)["status"]
        if j_status_h != JOB_COMPLETED:
            print(f'\tYour current job status is: {j_status_h}. The ' +
                  f'selected wait-time of {wait_time} was exceeded. Please, ' +
                  'consider to set a longer wait-time.')
            print('\tTo further check your job status you can either go to ' +
                  f'{j_url} or use the following command:\n' +
                  '\tcloudos job status \\\n' +
                  '\t\t--apikey $MY_API_KEY \\\n' +
                  f'\t\t--cloudos-url {cloudos_url} \\\n' +
                  f'\t\t--job-id {j_id}\n')
            sys.exit(1)
    else:
        j_status = j.get_job_status(j_id)
        j_status_h = json.loads(j_status.content)["status"]
        print(f'\tYour current job status is: {j_status_h}')
        print('\tTo further check your job status you can either go to ' +
              f'{j_url} or use the following command:\n' +
              '\tcloudos job status \\\n' +
              '\t\t--apikey $MY_API_KEY \\\n' +
              f'\t\t--cloudos-url {cloudos_url} \\\n' +
              f'\t\t--job-id {j_id}\n')


@job.command('status')
@click.option('-k',
              '--apikey',
              help='Your CloudOS API key',
              required=True)
@click.option('-c',
              '--cloudos-url',
              help=('The CloudOS url you are trying to access to. ' +
                    'Default=https://cloudos.lifebit.ai.'),
              default='https://cloudos.lifebit.ai')
@click.option('--job-id',
              help='The job id in CloudOS to search for.',
              required=True)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def job_status(apikey,
               cloudos_url,
               job_id,
               verbose):
    """Check job status in CloudOS."""
    print('Executing status...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(cloudos_url, apikey, None)
    if verbose:
        print('\tThe following Cloudos object was created:')
        print('\t' + str(cl) + '\n')
        print(f'\tSearching for job id: {job_id}')
    j_status = cl.get_job_status(job_id)
    j_status_h = json.loads(j_status.content)["status"]
    print(f'\tYour current job status is: {j_status_h}\n')
    j_url = f'{cloudos_url}/app/jobs/{job_id}'
    print(f'\tTo further check your job status you can either go to {j_url} ' +
          'or repeat the command you just used.')


@job.command('list')
@click.option('-k',
              '--apikey',
              help='Your CloudOS API key',
              required=True)
@click.option('-c',
              '--cloudos-url',
              help=('The CloudOS url you are trying to access to. ' +
                    'Default=https://cloudos.lifebit.ai.'),
              default='https://cloudos.lifebit.ai')
@click.option('--workspace-id',
              help='The specific CloudOS workspace id.',
              required=True)
@click.option('--output-basename',
              help=('Output file base name to save jobs list. ' +
                    'Default=joblist'),
              default='joblist',
              required=False)
@click.option('--output-format',
              help='The desired file format (file extension) for the output.',
              type=click.Choice(['csv', 'json'], case_sensitive=False),
              default='csv')
@click.option('--all-fields',
              help=('Whether to collect all available fields from jobs or ' +
                    'just the preconfigured selected fields. Only applicable ' +
                    'when --output-format=csv'),
              is_flag=True)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def list_jobs(apikey,
              cloudos_url,
              workspace_id,
              output_basename,
              output_format,
              all_fields,
              verbose):
    """Collect all your jobs from a CloudOS workspace in CSV format."""
    outfile = output_basename + '.' + output_format
    print('Executing list...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(cloudos_url, apikey, None)
    if verbose:
        print('\tThe following Cloudos object was created:')
        print('\t' + str(cl) + '\n')
        print('\tSearching for jobs in the following workspace: ' +
              f'{workspace_id}')
    my_jobs_r = cl.get_job_list(workspace_id)
    if output_format == 'csv':
        my_jobs = cl.process_job_list(my_jobs_r, all_fields)
        my_jobs.to_csv(outfile, index=False)
        print(f'\tJob list collected with a total of {my_jobs.shape[0]} jobs.')
    elif output_format == 'json':
        with open(outfile, 'w') as o:
            o.write(my_jobs_r.text)
        print(f'\tJob list collected with a total of {len(json.loads(my_jobs_r.content)["jobs"])} jobs.')
    else:
        raise ValueError('Unrecognised output format. Please use one of [csv|json]')
    print(f'\tJob list saved to {outfile}')


@workflow.command('list')
@click.option('-k',
              '--apikey',
              help='Your CloudOS API key',
              required=True)
@click.option('-c',
              '--cloudos-url',
              help=('The CloudOS url you are trying to access to. ' +
                    'Default=https://cloudos.lifebit.ai.'),
              default='https://cloudos.lifebit.ai')
@click.option('--workspace-id',
              help='The specific CloudOS workspace id.',
              required=True)
@click.option('--output-basename',
              help=('Output file base name to save workflow list. ' +
                    'Default=workflow_list'),
              default='workflow_list',
              required=False)
@click.option('--output-format',
              help='The desired file format (file extension) for the output.',
              type=click.Choice(['csv', 'json'], case_sensitive=False),
              default='csv')
@click.option('--all-fields',
              help=('Whether to collect all available fields from workflows or ' +
                    'just the preconfigured selected fields. Only applicable ' +
                    'when --output-format=csv'),
              is_flag=True)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def list_workflows(apikey,
                   cloudos_url,
                   workspace_id,
                   output_basename,
                   output_format,
                   all_fields,
                   verbose):
    """Collect all workflows from a CloudOS workspace in CSV format."""
    outfile = output_basename + '.' + output_format
    print('Executing list...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(cloudos_url, apikey, None)
    if verbose:
        print('\tThe following Cloudos object was created:')
        print('\t' + str(cl) + '\n')
        print('\tSearching for workflows in the following workspace: ' +
              f'{workspace_id}')
    my_workflows_r = cl.get_workflow_list(workspace_id)
    if output_format == 'csv':
        my_workflows = cl.process_workflow_list(my_workflows_r, all_fields)
        my_workflows.to_csv(outfile, index=False)
        print(f'\tWorkflow list collected with a total of {my_workflows.shape[0]} workflows.')
    elif output_format == 'json':
        with open(outfile, 'w') as o:
            o.write(my_workflows_r.text)
        print(f'\tWorkflow list collected with a total of {len(json.loads(my_workflows_r.content))} workflows.')
    else:
        raise ValueError('Unrecognised output format. Please use one of [csv|json]')
    print(f'\tWorkflow list saved to {outfile}')


@cromwell.command('status')
@click.version_option()
@click.option('-t',
              '--cromwell-token',
              help='Specific Cromwell server authentication token.',
              required=True)
@click.option('-c',
              '--cloudos-url',
              help=('The CloudOS url you are trying to access to. ' +
                    'Default=https://cloudos.lifebit.ai.'),
              default='https://cloudos.lifebit.ai')
@click.option('--workspace-id',
              help='The specific CloudOS workspace id.',
              required=True)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def cromwell_status(cromwell_token,
                    cloudos_url,
                    workspace_id,
                    verbose):
    """Check Cromwell server status in CloudOS."""
    print('Executing status...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(cloudos_url, None, cromwell_token)
    if verbose:
        print('\tThe following Cloudos object was created:')
        print('\t' + str(cl) + '\n')
        print(f'\tChecking Cromwell status in {workspace_id} workspace')
    c_status = cl.get_cromwell_status(workspace_id)
    c_status_h = json.loads(c_status.content)["status"]
    print(f'\tCurrent Cromwell server status is: {c_status_h}\n')


@cromwell.command('start')
@click.version_option()
@click.option('-t',
              '--cromwell-token',
              help='Specific Cromwell server authentication token.',
              required=True)
@click.option('-c',
              '--cloudos-url',
              help=('The CloudOS url you are trying to access to. ' +
                    'Default=https://cloudos.lifebit.ai.'),
              default='https://cloudos.lifebit.ai')
@click.option('--workspace-id',
              help='The specific CloudOS workspace id.',
              required=True)
@click.option('--wait-time',
              help=('Max time to wait (in seconds) to Cromwell restart. ' +
                    'Default=300.'),
              default=300)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def cromwell_restart(cromwell_token,
                     cloudos_url,
                     workspace_id,
                     wait_time,
                     verbose):
    """Restart Cromwell server in CloudOS."""
    action = 'restart'
    print('Starting Cromwell server...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(cloudos_url, None, cromwell_token)
    if verbose:
        print('\tThe following Cloudos object was created:')
        print('\t' + str(cl) + '\n')
        print(f'\tStarting Cromwell server in {workspace_id} workspace')
    cl.cromwell_switch(workspace_id, action)
    c_status = cl.get_cromwell_status(workspace_id)
    c_status_h = json.loads(c_status.content)["status"]
    print(f'\tCurrent Cromwell server status is: {c_status_h}\n')
    elapsed = 0
    while elapsed < wait_time and c_status_h != 'Running':
        c_status_old = c_status_h
        time.sleep(REQUEST_INTERVAL)
        elapsed += REQUEST_INTERVAL
        c_status = cl.get_cromwell_status(workspace_id)
        c_status_h = json.loads(c_status.content)["status"]
        if c_status_h != c_status_old:
            print(f'\tCurrent Cromwell server status is: {c_status_h}\n')
    if c_status_h != 'Running':
        print(f'\tYour current Cromwell status is: {c_status_h}. The ' +
              f'selected wait-time of {wait_time} was exceeded. Please, ' +
              'consider to set a longer wait-time.')
        print('\tTo further check your Cromwell status you can either go to ' +
              f'{cloudos_url} or use the following command:\n' +
              '\tcloudos cromwell status \\\n' +
              f'\t\t--cloudos-url {cloudos_url} \\\n' +
              '\t\t--cromwell-token $CROMWELL_TOKEN \\\n' +
              f'\t\t--workspace-id {workspace_id}')
        sys.exit(1)


@cromwell.command('stop')
@click.version_option()
@click.option('-t',
              '--cromwell-token',
              help='Specific Cromwell server authentication token.',
              required=True)
@click.option('-c',
              '--cloudos-url',
              help=('The CloudOS url you are trying to access to. ' +
                    'Default=https://cloudos.lifebit.ai.'),
              default='https://cloudos.lifebit.ai')
@click.option('--workspace-id',
              help='The specific CloudOS workspace id.',
              required=True)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def cromwell_stop(cromwell_token,
                  cloudos_url,
                  workspace_id,
                  verbose):
    """Stop Cromwell server in CloudOS."""
    action = 'stop'
    print('Stopping Cromwell server...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(cloudos_url, None, cromwell_token)
    if verbose:
        print('\tThe following Cloudos object was created:')
        print('\t' + str(cl) + '\n')
        print(f'\tRestarting Cromwell server in {workspace_id} workspace')
    cl.cromwell_switch(workspace_id, action)
    c_status = cl.get_cromwell_status(workspace_id)
    c_status_h = json.loads(c_status.content)["status"]
    print(f'\tCurrent Cromwell server status is: {c_status_h}\n')


if __name__ == "__main__":
    run_cloudos_cli()
