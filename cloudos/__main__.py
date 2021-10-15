#!/usr/bin/env python3

import click
import cloudos.jobs.job as jb
from cloudos.clos import Cloudos
import json
import time
import sys


# GLOBAL VARS
JOB_SUCCESS = 'completed'
JOB_FAIL = 'failed'


@click.group()
def run_cloudos_cli():
    """CloudOS python package: a package for interacting with CloudOS."""
    print(run_cloudos_cli.__doc__ + '\n')


@run_cloudos_cli.group()
def job():
    """CloudOS job functionality: run and check jobs in CloudOS."""
    print(job.__doc__ + '\n')


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
              help=('A nextflow.config file or similar, with the ' +
                    'parameters to use with your job.'),
              required=True)
@click.option('--job-name',
              help='The name of the job. Default=new_job.',
              default='new_job')
@click.option('--resumable',
              help='Whether to make the job able to be resumed or not.',
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
@click.option('--wait-completion',
              help=('Whether to wait to job completion and report final ' +
                    'job status.'),
              is_flag=True)
@click.option('--wait-time',
              help=('Max time to wait (in seconds) to job completion. ' +
                    'Default=3600.'),
              default=3600)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def run(apikey,
        cloudos_url,
        workspace_id,
        project_name,
        workflow_name,
        job_config,
        job_name,
        resumable,
        instance_type,
        instance_disk,
        spot,
        wait_completion,
        wait_time,
        verbose):
    """Submit a job to CloudOS."""
    print('Executing run...')
    if verbose:
        print('\t...Preparing objects')
    j = jb.Job(apikey, cloudos_url, workspace_id, project_name, workflow_name)
    if verbose:
        print('\tThe following Job object was created:')
        print('\t' + str(j))
        print('\t...Sending job to CloudOS\n')
    j_id = j.send_job(job_config,
                      job_name,
                      resumable,
                      instance_type,
                      instance_disk,
                      spot)
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
            if j_status_h == JOB_SUCCESS:
                print(f'\tYour job took {elapsed} seconds to complete ' +
                      'successfully.')
                sys.exit(0)
            elif j_status_h == JOB_FAIL:
                print(f'\tYour job took {elapsed} seconds to fail.')
                sys.exit(1)
            else:
                elapsed += 1
                if j_status_h != j_status_h_old:
                    print(f'\tYour current job status is: {j_status_h}.')
                    j_status_h_old = j_status_h
                time.sleep(1)
        j_status = j.get_job_status(j_id)
        j_status_h = json.loads(j_status.content)["status"]
        if j_status_h != JOB_SUCCESS:
            print(f'\tYour current job status is: {j_status_h}. The ' +
                  f'selected wait-time of {wait_time} was exceeded. Please, ' +
                  'consider to set a longer wait-time.')
            print('\tTo further check your job status you can either go to ' +
                  f'{j_url} or use the following command:\n' +
                  'cloudos job status \\\n' +
                  '    --apikey $MY_API_KEY \\\n' +
                  f'    --cloudos-url {cloudos_url} \\\n' +
                  f'    --job-id {j_id}')
            sys.exit(1)
    else:
        j_status = j.get_job_status(j_id)
        j_status_h = json.loads(j_status.content)["status"]
        print(f'\tYour current job status is: {j_status_h}')
        print('\tTo further check your job status you can either go to ' +
              f'{j_url} or use the following command:\n' +
              'cloudos job status \\\n' +
              '    --apikey $MY_API_KEY \\\n' +
              f'    --cloudos-url {cloudos_url} \\\n' +
              f'    --job-id {j_id}')


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
def status(apikey,
           cloudos_url,
           job_id,
           verbose):
    """Check job status in CloudOS."""
    print('Executing status...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(apikey, cloudos_url)
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
@click.option('--outfile',
              help=('Output filename where to save job table. ' +
                    'Default=joblist.csv'),
              default='joblist.csv',
              required=False)
@click.option('--full-data',
              help=('Whether to collect full available data from jobs or ' +
                    'just the preconfigured selected fields.'),
              is_flag=True)
@click.option('--verbose',
              help='Whether to print information messages or not.',
              is_flag=True)
def list(apikey,
         cloudos_url,
         workspace_id,
         outfile,
         full_data,
         verbose):
    """Collect all your jobs from a CloudOS workspace in CSV format."""
    print('Executing list...')
    if verbose:
        print('\t...Preparing objects')
    cl = Cloudos(apikey, cloudos_url)
    if verbose:
        print('\tThe following Cloudos object was created:')
        print('\t' + str(cl) + '\n')
        print('\tSearching for jobs in the following workspace: ' +
              f'{workspace_id}')
    my_jobs_r = cl.get_job_list(workspace_id)
    my_jobs = cl.process_job_list(my_jobs_r, full_data)
    my_jobs.to_csv(outfile, index=False)
    print(f'\tJob list collected with a total of {my_jobs.shape[0]} jobs.')
    print(f'\tJob list table saved to {outfile}')


if __name__ == "__main__":
    run_cloudos_cli()
