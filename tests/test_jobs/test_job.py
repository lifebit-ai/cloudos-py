import pytest
import json

from cloudos.jobs.job import Job

actual_json_file = "tests/test_data/convert_nextflow_to_json_params.json"

param_dict = {
    "config": "cloudos/examples/rnatoy.config",
    "parameter": (),
    "git_commit": None,
    "git_tag": None,
    "project_id": "6054754029b82f0112762b9c",
    "workflow_id": "60b0ca54303ee601a69b42d1",
    "job_name": "new_job",
    "resumable": True,
    "batch": False,
    "nextflow_profile": None,
    "instance_type": "c5.xlarge",
    "instance_disk": 500,
    "spot": True,
    "storage_mode": 'regular',
    "lustre_size": 1200,
    "workflow_type": 'nextflow',
    "cromwell_id": None,
    "cost_limit": -1
}


def test_convert_nextflow_to_json_output_correct():
    job_json = Job.convert_nextflow_to_json(
        1, param_dict["config"],
        parameter=param_dict["parameter"],
        git_commit=param_dict["git_commit"],
        git_tag=param_dict["git_tag"],
        project_id=param_dict["project_id"],
        workflow_id=param_dict["workflow_id"],
        job_name=param_dict["job_name"],
        resumable=param_dict["resumable"],
        batch=param_dict["batch"],
        nextflow_profile=param_dict["nextflow_profile"],
        instance_type=param_dict["instance_type"],
        instance_disk=param_dict["instance_disk"],
        spot=param_dict["spot"],
        storage_mode=param_dict["storage_mode"],
        lustre_size=param_dict["lustre_size"],
        workflow_type=param_dict["workflow_type"],
        cromwell_id=param_dict["cromwell_id"],
        cost_limit=param_dict["cost_limit"]
        )
    with open(actual_json_file) as json_data:
        correct_json = json.load(json_data)
    assert job_json == correct_json


def test_convert_nextflow_to_json_badly_formed_config():
    no_equals_config = "tests/test_data/wrong_params.config"
    with pytest.raises(ValueError) as excinfo:
        job_json = Job.convert_nextflow_to_json(
            1, no_equals_config,
            parameter=param_dict["parameter"],
            git_commit=param_dict["git_commit"],
            git_tag=param_dict["git_tag"],
            project_id=param_dict["project_id"],
            workflow_id=param_dict["workflow_id"],
            job_name=param_dict["job_name"],
            resumable=param_dict["resumable"],
            batch=param_dict["batch"],
            nextflow_profile=param_dict["nextflow_profile"],
            instance_type=param_dict["instance_type"],
            instance_disk=param_dict["instance_disk"],
            spot=param_dict["spot"],
            storage_mode=param_dict["storage_mode"],
            lustre_size=param_dict["lustre_size"],
            workflow_type=param_dict["workflow_type"],
            cromwell_id=param_dict["cromwell_id"],
            cost_limit=param_dict["cost_limit"]
            )
        print(str(excinfo.value))
    assert "Please, specify your parameters in\
            tests/test_data/wrong_params.config\
            using the \'=\' as spacer.\
            E.g: name = my_name".replace("           ", "") in str(excinfo.value)
