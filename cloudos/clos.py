"""
This is the main class of the package.
"""

import requests
import json
from dataclasses import dataclass
from cloudos.utils.errors import BadRequestException
import pandas as pd


@dataclass
class Cloudos:
    """A simple class to contain the required connection information.

    Parameters
    ----------
    apikey : string
        Your CloudOS API key.
    cloudos_url : string
        The CloudOS service url.
    """
    apikey: str
    cloudos_url: str

    def get_job_status(self, j_id):
        """Get job status from CloudOS.

        Parameters
        ----------
        j_id : string
            The CloudOS job id of the job just launched.

        Returns
        -------
        r : requests.models.Response
            The server response
        """
        cloudos_url = self.cloudos_url
        apikey = self.apikey
        headers = {
            "Content-type": "application/json",
            "apikey": apikey
        }
        r = requests.get("{}/api/v1/jobs/{}".format(cloudos_url,
                                                    j_id),
                         headers=headers)
        if r.status_code >= 400:
            raise BadRequestException(r)
        return r

    def get_job_list(self, workspace_id):
        """Get all the jobs from a CloudOS workspace.

        Parameters
        ----------
        workspace_id : string
            The CloudOS workspace id from to collect the jobs.

        Returns
        -------
        r : requests.models.Response
            The server response
        """
        data = {"apikey": self.apikey}
        r = requests.get("{}/api/v1/jobs?teamId={}".format(self.cloudos_url,
                                                           workspace_id),
                         params=data)
        if r.status_code >= 400:
            raise BadRequestException()
        return r

    @staticmethod
    def process_job_list(r, full_data=False):
        """Process a server response from a self.get_job_list call.

        Parameters
        ----------
        r : requests.models.Response
            The server response. It should contain a field named 'jobs' and
            the required columns (hard-coded in the function).
        full_data : bool. Default=False
            Whether to return a reduced version of the DataFrame containing
            only the selected columns or the full DataFrame.

        Returns
        -------
        df : pandas.DataFrame
            A DataFrame with the requested columns from the jobs.
        """
        COLUMNS = ['_id',
                   'team',
                   'name',
                   'parameters',
                   'status',
                   'startTime',
                   'endTime',
                   'createdAt',
                   'updatedAt',
                   'computeCostSpent',
                   'masterInstanceStorageCost',
                   'resumeWorkDir',
                   'user.id',
                   'workflow._id',
                   'workflow.name',
                   'workflow.description',
                   'workflow.createdAt',
                   'workflow.updatedAt',
                   'workflow.workflowType',
                   'project._id',
                   'project.name',
                   'project.user',
                   'project.team',
                   'project.createdAt',
                   'project.updatedAt',
                   'masterInstance.usedInstance.type',
                   'spotInstances.usedInstance.asSpot'
                   ]
        my_jobs = json.loads(r.content)
        df_full = pd.json_normalize(my_jobs['jobs'])
        if full_data:
            df = df_full
        else:
            df = df_full.loc[:, COLUMNS]
        return df
