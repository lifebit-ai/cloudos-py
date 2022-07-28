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
    cloudos_url : string
        The CloudOS service url.
    apikey : string
        Your CloudOS API key.
    cromwell_token : string
        Cromwell server token.
    workspace_id : string
        The specific Cloudos workspace id.
    project_name : string
        The name of a CloudOS project.
    workflow_name : string
        The name of a CloudOS workflow or pipeline.
    mainfile : string
        The name of the mainFile used by the workflow. Required for WDL pipelines as different
        mainFiles could be loaded for a single pipeline.
    importsfile : string
        The name of the importsFile used by the workflow. Required for WDL pipelines as different
        importsFiles could be loaded for a single pipeline.
    repository_platform : string
        The name of the repository platform of the workflow.
    project_id : string
        The CloudOS project id for a given project name.
    workflow_id : string
        The CloudOS workflow id for a given workflow_name.
    """
    workspace_id: str
    project_name: str
    workflow_name: str
    mainfile: str = None
    importsfile: str = None
    repository_platform: str = 'github'
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
                self.workflow_name,
                self.mainfile,
                self.importsfile,
                self.repository_platform)
        else:
            # Let the user define the value.
            self._workflow_id = v

    def fetch_cloudos_id(self,
                         apikey,
                         cloudos_url,
                         resource,
                         workspace_id,
                         name,
                         mainfile=None,
                         importsfile=None,
                         repository_platform='github'):
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
        mainfile : string
            The name of the mainFile used by the workflow. Only used when resource == 'workflows'.
            Required for WDL pipelines as different mainFiles could be loaded for a single
            pipeline.
        importsfile : string
            The name of the importsFile used by the workflow. Required for WDL pipelines as different
            importsFiles could be loaded for a single pipeline.
        repository_platform : string
            The name of the repository platform of the workflow resides.

        Returns
        -------
        project_id : string
            The CloudOS project id for a given project name.
        """
        allowed_resources = ['projects', 'workflows']
        if resource not in allowed_resources:
            raise ValueError('Your specified resource is not supported. ' +
                             f'Use one of the following: {allowed_resources}')
        data = {"apikey": apikey}
        r = requests.get("{}/api/v1/{}?teamId={}".format(cloudos_url,
                                                         resource,
                                                         workspace_id),
                         params=data)
        if r.status_code >= 400:
            raise BadRequestException(r)
        for element in json.loads(r.content):
            if resource == 'workflows':
                if (element["name"] == name and element["repository"]["platform"] == repository_platform):
                    if mainfile is None:
                        return element["_id"]
                    elif importsfile is None:
                        raise ValueError('Please, indicate importsfile when mainfile is used')
                    # Not all the wdl pipelines have importsFile field
                    elif "importsFile" in element.keys():
                        if element["mainFile"] == mainfile and element["importsFile"] == importsfile:
                            return element["_id"]
            elif resource == 'projects':
                if element["name"] == name:
                    return element["_id"]
        if mainfile is not None:
            raise ValueError(f'[ERROR] A workflow named \'{name}\' with a mainFile \'{mainfile}\'' +
                             f' and an importsFile \'{importsfile}\' was not found')
        else:
            raise ValueError(f'[ERROR] No {name} element in {resource} was found')

    def convert_nextflow_to_json(self,
                                 job_config,
                                 parameter,
                                 git_commit,
                                 git_tag,
                                 project_id,
                                 workflow_id,
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
                                 cost_limit):
        """Converts a nextflow.config file into a json formatted dict.

        Parameters
        ----------
        job_config : string
            Path to a nextflow.config file with parameters scope.
        parameter : tuple
            Tuple of strings indicating the parameters to pass to the pipeline call.
            They are in the following form: ('param1=param1val', 'param2=param2val', ...)
        git_commit : string
            The exact commit of the pipeline to use. Equivalent to -r
            option in Nextflow. If not specified, the last commit of the
            default branch will be used.
        git_tag : string
            The tag of the pipeline to use. If not specified, the last
            commit of the default branch will be used.
        project_id : string
            The CloudOS project id for a given project name.
        workflow_id : string
            The CloudOS workflow id for a given workflow_name.
        job_name : string.
            The name to assign to the job.
        resumable: bool
            Whether to create a resumable job or not.
        batch: bool
            Whether to create a batch job instead of the default ignite.
        nextflow_profile: string
            A comma separated string with the profiles to be used.
        instance_type : string
            Name of the AMI to choose.
        instance_disk : int
            The disk space of the instance, in GB.
        spot : bool
            Whether to create a spot instance or not.
        storage_mode : string
            Either 'lustre' or 'regular'. Indicates if the user wants to select regular
            or lustre storage.
        lustre_size : int
            The lustre storage to be used when --storage-mode=lustre, in GB. It should be 1200 or
            a multiple of it.
        workflow_type : str
            The type of workflow to run. Either 'nextflow' or 'wdl'.
        cromwell_id : str
            Cromwell server ID.
        cost_limit : float
            Job cost limit. -1 means no cost limit.

        Returns
        -------
        params : dict
            A JSON formatted dict.
        """
        workflow_params = []
        if workflow_type == 'wdl':
            # This is required as non-resumable jobs fails always using WDL workflows.
            resumable = True
        if nextflow_profile is None and job_config is None and len(parameter) == 0:
            raise ValueError('No --job-config, --nextflow_profile or --parameter were specified,' +
                             '  please use at least one of these options.')
        if workflow_type == 'wdl' and job_config is None and len(parameter) == 0:
            raise ValueError('No --job-config or --parameter were provided. At least one of ' +
                             'these are required for WDL workflows.')
        if job_config is not None:
            with open(job_config, 'r') as p:
                reading = False
                for p_l in p:
                    if 'params' in p_l.lower():
                        reading = True
                    else:
                        if reading:
                            if workflow_type == 'wdl':
                                p_l_strip = p_l.strip().replace(
                                    ' ', '')
                            else:
                                p_l_strip = p_l.strip().replace(
                                    ' ', '').replace('\"', '').replace('\'', '')
                            if len(p_l_strip) == 0:
                                continue
                            elif p_l_strip[0] == '/' or p_l_strip[0] == '#':
                                continue
                            elif p_l_strip == '}':
                                reading = False
                            else:
                                p_list = p_l_strip.split('=')
                                if len(p_list) != 2:
                                    raise ValueError('Please, specify your ' +
                                                     'parameters in ' +
                                                     f'{job_config} using ' +
                                                     'the \'=\' as spacer. ' +
                                                     'E.g: name = my_name')
                                elif workflow_type == 'wdl':
                                    param = {"prefix": "",
                                             "name": p_list[0],
                                             "parameterKind": "textValue",
                                             "textValue": p_list[1]}
                                    workflow_params.append(param)
                                else:
                                    param = {"prefix": "--",
                                             "name": p_list[0],
                                             "parameterKind": "textValue",
                                             "textValue": p_list[1]}
                                    workflow_params.append(param)
            if len(workflow_params) == 0:
                raise ValueError(f'The {job_config} file did not contain any ' +
                                 'valid parameter')
        if len(parameter) > 0:
            for p in parameter:
                p_split = p.split('=')
                if len(p_split) != 2:
                    raise ValueError('Please, specify -p / --parameter using a single \'=\' ' +
                                     'as spacer. E.g: input=value')
                p_name = p_split[0]
                p_value = p_split[1]
                if workflow_type == 'wdl':
                    param = {"prefix": "",
                             "name": p_name,
                             "parameterKind": "textValue",
                             "textValue": p_value}
                    workflow_params.append(param)
                else:
                    param = {"prefix": "--",
                             "name": p_name,
                             "parameterKind": "textValue",
                             "textValue": p_value}
                    workflow_params.append(param)
            if len(workflow_params) == 0:
                raise ValueError(f'The provided parameters are not valid: {parameter}')
        if spot:
            instance_type_block = {
                "instanceType": instance_type,
                "onDemandFallbackInstanceType": instance_type
            }
            instance = "spotInstances"
        else:
            instance_type_block = instance_type
            instance = "instanceType"

        if git_tag is not None and git_commit is not None:
            raise ValueError('Please, specify none or only one of --git-tag' +
                             ' or --git-commit options but not both.')
        if git_commit is not None:
            revision_block = {
                                 "commit": git_commit,
                                 "isLatest": False
                             }
        elif git_tag is not None:
            revision_block = {
                                 "tag": git_tag,
                                 "isLatest": False
                             }
        else:
            revision_block = ""
        if storage_mode == "lustre":
            print('\n[WARNING] Lustre storage has been selected. Please, be sure that this kind of ' +
                  'storage is available in your CloudOS workspace.\n')
            if lustre_size % 1200:
                raise ValueError('Please, specify a lustre storage size of 1200 or a multiple of it. ' +
                                 f'{lustre_size} is not a valid number.')
        if storage_mode not in ['lustre', 'regular']:
            raise ValueError('Please, use either \'lustre\' or \'regular\' for --storage-mode ' +
                             f'{storage_mode} is not allowed')

        params = {
            "parameters": workflow_params,
            "project": project_id,
            "workflow": workflow_id,
            "name": job_name,
            "resumable": resumable,
            "batch": {
                "enabled": batch
            },
            "cromwellCloudResources": cromwell_id,
            "executionPlatform": "aws",
            "storageSizeInGb": instance_disk,
            "execution": {
                "computeCostLimit": cost_limit,
                "optim": "test"
            },
            "lusterFsxStorageSizeInGb": lustre_size,
            "storageMode": storage_mode,
            "revision": revision_block,
            "profile": nextflow_profile,
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
                 job_config=None,
                 parameter=(),
                 git_commit=None,
                 git_tag=None,
                 job_name='new_job',
                 resumable=False,
                 batch=False,
                 nextflow_profile=None,
                 instance_type='c5.xlarge',
                 instance_disk=500,
                 spot=False,
                 storage_mode='regular',
                 lustre_size=1200,
                 workflow_type='nextflow',
                 cromwell_id=None,
                 cost_limit=-1):
        """Send a job to CloudOS.

        Parameters
        ----------
        job_config : string
            Path to a nextflow.config file with parameters scope.
        parameter : tuple
            Tuple of strings indicating the parameters to pass to the pipeline call.
            They are in the following form: ('param1=param1val', 'param2=param2val', ...)
        git_commit : string
            The exact commit of the pipeline to use. Equivalent to -r
            option in Nextflow. If not specified, the last commit of the
            default branch will be used.
        git_tag : string
            The tag of the pipeline to use. If not specified, the last
            commit of the default branch will be used.
        job_name : string
            The name to assign to the job.
        resumable: bool
            Whether to create a resumable job or not.
        batch: bool
            Whether to create a batch job instead of the default ignite.
        nextflow_profile: string
            A comma separated string with the profiles to be used.
        instance_type : string
            Type of the AMI to choose.
        instance_disk : int
            The disk space of the instance, in GB.
        spot : bool
            Whether to create a spot instance or not.
        storage_mode : string
            Either 'lustre' or 'regular'. Indicates if the user wants to select regular
            or lustre storage.
        lustre_size : int
            The lustre storage to be used when --storage-mode=lustre, in GB. It should be 1200 or
            a multiple of it.
        workflow_type : str
            The type of workflow to run. Either 'nextflow' or 'wdl'.
        cromwell_id : str
            Cromwell server ID.
        cost_limit : float
            Job cost limit. -1 means no cost limit.

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
                                               parameter,
                                               git_commit,
                                               git_tag,
                                               project_id,
                                               workflow_id,
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
        r = requests.post("{}/api/v1/jobs?teamId={}".format(cloudos_url,
                                                            workspace_id),
                          data=json.dumps(params), headers=headers)
        if r.status_code >= 400:
            raise BadRequestException(r)
        j_id = json.loads(r.content)["_id"]
        print('\tJob successfully launched to CloudOS, please check the ' +
              f'following link: {cloudos_url}/app/jobs/{j_id}')
        return j_id
