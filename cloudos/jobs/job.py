"""
This is the main class to create jobs.
"""

from dataclasses import dataclass
import requests
import json
from cloudos.clos import Cloudos
from cloudos.utils.errors import BadRequestException


@dataclass
class Job(Cloudos):
    """Class to store and operate jobs.

    Parameters
    ----------
    apikey : string
        Your CloudOS API key.
    cloudos_url : string
        The CloudOS service url.
    workspace_id : string
        The specific Cloudos workspace id.
    project_name : string
        The name of a CloudOS project.
    workflow_name : string
        The name of a CloudOS workflow or pipeline.
    project_id : string
        The CloudOS project id for a given project name.
    workflow_id : string
        The CloudOS workflow id for a given workflow_name.
    """
    workspace_id: str
    project_name: str
    workflow_name: str
    project_id: str = None
    workflow_id: str = None

    @property
    def project_id(self) -> str:
        return self._project_id

    @project_id.setter
    def project_id(self, v) -> None:
        if isinstance(v, property):
            # Fetch the value as not defined by user.
            self._project_id = self.fetch_cloudos_id(
                self.apikey,
                self.cloudos_url,
                'projects',
                self.workspace_id,
                self.project_name)
        else:
            # Let the user define the value.
            self._project_id = v

    @property
    def workflow_id(self) -> str:
        return self._workflow_id

    @workflow_id.setter
    def workflow_id(self, v) -> None:
        if isinstance(v, property):
            # Fetch the value as not defined by user.
            self._workflow_id = self.fetch_cloudos_id(
                self.apikey,
                self.cloudos_url,
                'workflows',
                self.workspace_id,
                self.workflow_name)
        else:
            # Let the user define the value.
            self._workflow_id = v

    def fetch_cloudos_id(self,
                         apikey,
                         cloudos_url,
                         resource,
                         workspace_id,
                         name):
        """Fetch the cloudos id for a given name.

        Paramters
        ---------
        apikey : string
            Your CloudOS API key
        cloudos_url : string
            The CloudOS service url.
        resource : string
            The resource you want to fetch from. E.g.: projects.
        workspace_id : string
            The specific Cloudos workspace id.
        name : string
            The name of a CloudOS resource element.

        Returns
        -------
        project_id : string
            The CloudOS project id for a given project name.
        """
        allowed_resources = ['projects', 'workflows']
        if resource not in allowed_resources:
            raise ValueError('Your specified resource is not supported. ' +
                             'Use one of the following: {allowed_resources}')
        data = {"apikey": apikey}
        r = requests.get("{}/api/v1/{}?teamId={}".format(cloudos_url,
                                                         resource,
                                                         workspace_id),
                         params=data)
        if r.status_code >= 400:
            raise BadRequestException(r)
        for element in json.loads(r.content):
            if element["name"] == name:
                return element["_id"]

    def convert_nextflow_to_json(self,
                                 job_config,
                                 project_id,
                                 workflow_id,
                                 job_name,
                                 resumable,
                                 instance_type,
                                 instance_disk,
                                 spot):
        """Converts a nextflow.config file into a json formatted dict.

        Parameters
        ----------
        job_config : string
            Path to a nextflow.config file with parameters scope.
        project_id : string
            The CloudOS project id for a given project name.
        workflow_id : string
            The CloudOS workflow id for a given workflow_name.
        job_name : string.
            The name to assign to the job.
        resumable: bool
            Whether to create a resumable job or not.
        instance_type : string
            Name of the AMI to choose.
        instance_disk : int
            The disk space of the instance, in GB.
        spot : bool
            Whether to create a spot instance or not.

        Returns
        -------
        params : dict
            A JSON formatted dict.
        """
        workflow_params = []
        with open(job_config, 'r') as p:
            reading = False
            for p_l in p:
                if 'params' in p_l.lower():
                    reading = True
                else:
                    if reading:
                        p_l_strip = p_l.strip().replace(
                            ' ', '').replace('\"', '').replace('\'', '')
                        if '}' in p_l_strip:
                            reading = False
                        else:
                            p_list = p_l_strip.split('=')
                            if len(p_list) != 2:
                                raise ValueError('Please, specify your ' +
                                                 'parameters in ' +
                                                 f'{job_config} using ' +
                                                 'the \'=\' char as spacer. ' +
                                                 'E.g: name = my_name')
                            else:
                                param = {"prefix": "--",
                                         "name": p_list[0],
                                         "parameterKind": "textValue",
                                         "textValue": p_list[1]}
                                workflow_params.append(param)
        if len(workflow_params) == 0:
            raise ValueError(f'The {job_config} file did not contain any ' +
                             'valid parameter')
        if spot:
            instance_type_block = {
                "instanceType": instance_type,
                "onDemandFallbackInstanceType": instance_type
            }
            instance = "spotInstances"
        else:
            instance_type_block = instance_type
            instance = "instanceType"

        params = {
            "parameters": workflow_params,
            "project": project_id,
            "workflow": workflow_id,
            "name": job_name,
            "resumable": resumable,
            "executionPlatform": "aws",
            "storageSizeInGb": instance_disk,
            "execution": {
                "computeCostLimit": -1,
                "optim": "test"
            },
            instance: instance_type_block,
            "masterInstance": {
                "requestedInstance": {
                    "type": instance_type,
                    "asSpot": False
                }
            }
        }
        return params

    def send_job(self,
                 job_config,
                 job_name,
                 resumable,
                 instance_type,
                 instance_disk,
                 spot):
        """Send a job to CloudOS.

        Parameters
        ----------
        job_config : string
            Path to a nextflow.config file with parameters scope.
        job_name : string
            The name to assign to the job.
        resumable: bool
            Whether to create a resumable job or not.
        instance_type : string
            Type of the AMI to choose.
        instance_disk : int
            The disk space of the instance, in GB.
        spot : bool
            Whether to create a spot instance or not.

        Returns
        -------
        j_id : string
            The CloudOS job id of the job just launched.
        """
        apikey = self.apikey
        cloudos_url = self.cloudos_url
        workspace_id = self.workspace_id
        workflow_id = self.workflow_id
        project_id = self.project_id
        # Prepare api request for CloudOS to run a job
        headers = {
            "Content-type": "application/json",
            "apikey": apikey
        }
        params = self.convert_nextflow_to_json(job_config,
                                               project_id,
                                               workflow_id,
                                               job_name,
                                               resumable,
                                               instance_type,
                                               instance_disk,
                                               spot)
        r = requests.post("{}/api/v1/jobs?teamId={}".format(cloudos_url,
                                                            workspace_id),
                          data=json.dumps(params), headers=headers)
        if r.status_code >= 400:
            raise BadRequestException(r)
        j_id = json.loads(r.content)["_id"]
        print('\tJob successfully launched to CloudOS, please check the ' +
              f'following link: {cloudos_url}/app/jobs/{j_id}')
        return j_id
