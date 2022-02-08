"""
This is the main class for interacting with cohort browser cohorts.
"""

import requests
import pandas as pd
from cloudos.utils.errors import BadRequestException
from .query import Query
from sys import stderr


class Cohort(object):
    """Class to store and operate cohorts.

    Parameters
    ----------
    apikey : string
        Your CloudOS API key.
    cloudos_url : string
        The CloudOS service url.
    workspace_id : string
        The specific Cloudos workspace id.
    cohort_id : string
        The ID of a Cohort Browser cohort (Optional).
    cohort_name : string
        The name of a Cohort Browser cohort - can be used instead of cohort_id (Optional).
    """
    def __init__(self, apikey, cloudos_url, workspace_id, cohort_id=None, cohort_name=None):
        self.apikey = apikey
        self.cloudos_url = cloudos_url
        self.workspace_id = workspace_id

        self.cohort_name = None
        self.num_participants = None
        self.query = None
        self.columns = None
        self.query_type = None

        if cohort_id is not None:
            self.cohort_id = cohort_id
        elif cohort_name is not None:
            self.cohort_id = self.fetch_cohort_id(cohort_name)
        else:
            raise ValueError('One of cohort_id or cohort_name must be set.')

        # Fill in cohort info from API
        self.update()

    @classmethod
    def load(cls, apikey, cloudos_url, workspace_id, cohort_id=None, cohort_name=None):
        """Load an existing cohort using its ID.

        Parameters
        ----------
        apikey : string
            Your CloudOS API key.
        cloudos_url : string
            The CloudOS service url.
        workspace_id : string
            The specific Cloudos workspace id.
        cohort_id : string
            The ID of a Cohort Browser cohort (Optional).
        cohort_name : string
            The name of a Cohort Browser cohort - can be used instead of cohort_id (Optional).

        Returns
        -------
        Cohort
        """
        return cls(apikey, cloudos_url, workspace_id, cohort_id, cohort_name)

    @classmethod
    def create(cls, apikey, cloudos_url, workspace_id, cohort_name, cohort_desc=""):
        """Create a new cohort in the Cohort Browser.

        Parameters
        ----------
        apikey : string
            Your CloudOS API key.
        cloudos_url : string
            The CloudOS service url.
        workspace_id : string
            The specific Cloudos workspace id.
        cohort_name : string
            The name to assign to the new cohort.
        cohort_desc : string
            The description to assign to the new cohort. (Optional)

        Returns
        -------
        Cohort
        """
        headers = {"apikey": apikey,
                   "Accept": "application/json, text/plain, */*",
                   "Content-Type": "application/json;charset=UTF-8"}
        params = {"teamId": workspace_id}
        data = {"name": cohort_name,
                "description": cohort_desc}
        r = requests.post(f"{cloudos_url}/cohort-browser/v2/cohort",
                          params=params, headers=headers, json=data)
        if r.status_code >= 400:
            raise BadRequestException(r)
        r_json = r.json()
        return cls(apikey, cloudos_url, workspace_id, cohort_id=r_json['_id'])

    @property
    def column_ids(self) -> list:
        return [ item['field']['id'] for item in self.columns ]

    def update(self):
        """Update the stored cohort information in the cohort object instance with
        the latest information from the Cohort Browser server."""

        headers = {"apikey": self.apikey,
                   "Accept": "application/json, text/plain, */*",
                   "Content-Type": "application/json;charset=UTF-8"}
        params = {"teamId": self.workspace_id}
        r = requests.get(f"{self.cloudos_url}/cohort-browser/v2/cohort/{self.cohort_id}",
                         params=params, headers=headers)
        if r.status_code >= 400:
            raise BadRequestException(r)
        r_json = r.json()
        self.cohort_name = r_json['name']
        self.cohort_desc = r_json.get('description')
        self.num_participants = r_json['numberOfParticipants']
        self.columns = r_json['columns']
        self.query_type = r_json['type']

        query_dict = r_json.get('query')
        if query_dict is not None:
            self.query = Query.from_api_dict(query_dict)
        else:
            self.query = None

    def fetch_cohort_id(self, name):
        return NotImplemented

    def preview_participant_count(self, query=None, keep_query=True):
        """Retrieve the number of participants in the cohort if the supplied query were to be
        applied.

        Parameters
        ----------
        query : Query | PhenoFilter
            The query for which to retrieve the participant count.
        keep_query : bool
            If True, the query argument will be combined with the existing query. If False, the
            query argument will be considered in place of the existing query. (Default: True)

        Returns
        -------
        dict
        """
        if query is None:
            query = Query('AND', [])

        if keep_query:
            query = self.query & query
        else:
            query = Query('AND', [query])

        query.strip_singletons()

        if len(query.subqueries) > 0:
            data = {"query": query.to_api_dict()}
        else:
            data = None

        headers = {"apikey": self.apikey,
                   "Accept": "application/json, text/plain, */*",
                   "Content-Type": "application/json;charset=UTF-8"}
        params = {"teamId": self.workspace_id}
        r = requests.post(f"{self.cloudos_url}/cohort-browser/v2/cohort/{self.cohort_id}/filter/participants",
                          params=params, headers=headers, json=data)
        if r.status_code >= 400:
            raise BadRequestException(r)
        r_json = r.json()

        return r_json

    def apply_query(self, query=None, keep_query=True):
        """Apply the supplied query to the cohort.

        Parameters
        ----------
        query : Query | PhenoFilter
            The query to apply.
        keep_query : bool
            If True, the query argument will be combined with the existing query. If False, the
            query argument will be considered in place of the existing query. (Default: True)

        Returns
        -------
        None
        """
        if query is None:
            query = Query('AND', [])

        if keep_query:
            query = Query('AND', [self.query]) & query
        else:
            query = Query('AND', [query])

        query.strip_singletons()

        # keep_query is False because we have already combined the query if needed
        new_count = self.preview_participant_count(query, keep_query=False)['count']

        data = {'name': self.cohort_name,
                'description': self.cohort_desc,
                'columns': self.__get_column_json(),
                'type': 'advanced',
                'numberOfParticipants': new_count}

        if len(query.subqueries) > 0:
            data['query'] = query.to_api_dict()
        else:
            data['query'] = None

        headers = {"apikey": self.apikey,
                   "Accept": "application/json, text/plain, */*",
                   "Content-Type": "application/json;charset=UTF-8"}
        params = {"teamId": self.workspace_id}
        r = requests.put(f"{self.cloudos_url}/cohort-browser/v2/cohort/{self.cohort_id}",
                         params=params, headers=headers, json=data)
        if r.status_code >= 400:
            raise BadRequestException(r)

        self.update()

    def get_participants_table(self, cols=None, page_number="all", page_size=5000):
        """Fetch the participant data table for the cohort.

        Parameters
        ----------
        cols: int list or None
            List of phenotype IDs to determine the table columns. If None, use the columns saved
            in the cohort. (Default: None)
        page_number: int or "all"
            Page number to fetch from the paginated table. (Default: 'all')
        page_number: page_size
            The size of page to get. (Default: 5000)

        Returns
        -------
        pandas.DataFrame
        """
        if page_size == 0:
            raise ValueError("page_size can't be 0")
        if page_number != "all" and isinstance(page_number, int) is not True:
            raise ValueError("page_number must be integer or 'all'")
        if page_number == "all":
            iter_all = True
        else:
            iter_all = False

        if cols is None:
            columns = self.__get_column_json()
        else:
            columns = self.__make_column_json(cols)

        r_body = {"criteria": {"pagination": {"pageNumber": page_number, "pageSize": page_size},
                               "cohortId": self.cohort_id},
                  "columns": columns}
        if self.query:
            r_body['query'] = self.query.to_api_dict()

        r_json = self.__fetch_table(r_body, iter_all)

        col_names = {"_id": "_id", "i": "i"}
        col_types = {"_id": "object", "i": "object"}
        for col in r_json['header']:
            if col['array']['type'] == "exact":
                long_id = f'f{col["id"]}i{col["instance"]}a{col["array"]["value"]}'
            else:
                long_id = f'f{col["id"]}i{col["instance"]}aall'
            col_names[long_id] = col['field']['name']
            if col['field']['valueType'] == "":
                col_types[long_id] = "object"
            elif col['field']['valueType'] == "Integer":
                col_types[long_id] = "Int64"
            elif col['field']['valueType'] == "Continuous":
                col_types[long_id] = "float64"
            else:
                col_types[long_id] = "object"
        res_df = pd.json_normalize(r_json['data'])
        for k, v in col_types.items():
            try:
                res_df[k] = res_df[k].astype(v)
            except TypeError as e:
                print(f'Warning: values in the column \"{col_names[k]}\" do not fit the '
                      f'data type ({v}) specified in the Cohort Browser metadata. '
                      f'Leaving data type as `object`.',
                      file=stderr)
        res_df = res_df.rename(columns=col_names)
        res_df.drop('_id', axis=1, inplace=True)
        return res_df

    def __fetch_table(self, r_body, iter_all=False):
        """Requests information on a cohort of interest specified based on dict
        made in get_participants_table.

        Parameters
        ----------
        r_body: dict
            The ids of the phenotypes of interest.
        iter_all: boolean
            Get all information.

        Returns
        -------
        Dict
        """
        page_size = r_body["criteria"]["pagination"]["pageSize"]
        headers = {"apikey": self.apikey,
                   "Accept": "application/json, text/plain, */*",
                   "Content-Type": "application/json;charset=UTF-8"}
        params = {"teamId": self.workspace_id}
        if r_body["criteria"]["pagination"]["pageNumber"] == "all":
            r_body["criteria"]["pagination"]["pageNumber"] = 0

        r = requests.post(f"{self.cloudos_url}/cohort-browser/v2/cohort/participants/search",
                          params=params, headers=headers, json=r_body)
        if r.status_code >= 400:
            raise BadRequestException(r)
        r_json = r.json()
        header = r_json["header"]
        data = r_json["data"]
        total = r_json["total"]

        if iter_all is True:
            iters = (total // page_size)
            for i in range(1, (iters + 1)):
                r_body["criteria"]["pagination"]["pageNumber"] = i
                r_body["criteria"]["pagination"]["pageSize"] = page_size
                r = requests.post(f"{self.cloudos_url}/cohort-browser/v2/cohort/participants/search",
                                  params=params, headers=headers, json=r_body)
                if r.status_code >= 400:
                    raise BadRequestException(r)
                r_json = r.json()
                data.extend(r_json["data"])
        result = {"total": total, "header": header, "data": data}

        return result

    def __get_column_json(self):
        """Make a list of all columns for a cohort that will be quieried in
        get_participants_table.

        Parameters
        ----------

        Returns
        -------
        list
        """
        cohort_columns = []
        if len(self.columns) == 0:
            return cohort_columns
        for col in self.columns:
            col_temp = {"id": col['field']['id'],
                        "instance": col["instance"],
                        "array": col["array"]}
            cohort_columns.append(col_temp)

        return cohort_columns

    def __make_column_json(self, col_ids):
        """Make a list of columns of interest for a cohort that will be quieried
        in get_participants_table.

        Parameters
        ----------
        col_ids : int list
            The ids of the phenotypes of interest.

        Returns
        -------
        list
        """
        cohort_columns = []
        for col_id in col_ids:
            phenotype = self.get_phenotype_metadata(col_id)
            if phenotype["array"] > 1:
                array = {"type": "all", "value": 0}
            else:
                array = {"type": "exact", "value": 0}
            col_temp = {"id": col_id,
                        "instance": "0",
                        "array": array}
            cohort_columns.append(col_temp)

        return cohort_columns

    def get_phenotype_metadata(self, pheno_id):
        """Get metadata of a phenotype. Based on the Cohort_browser class function
        get_phenotype_metadata. Made here to avoid circule imports.

        Parameters
        ----------
        pheno_id : int
            The id of the phenotype of interest.

        Returns
        -------
        Dict
        """
        headers = {"apikey": self.apikey,
                   "Accept": "application/json, text/plain, */*",
                   "Content-Type": "application/json;charset=UTF-8"}
        params = {"teamId": self.workspace_id}
        r = requests.get(f"{self.cloudos_url}/cohort-browser/v2/cohort/filter/{pheno_id}/metadata",
                         params=params, headers=headers)
        if r.status_code >= 400:
            raise BadRequestException(r)
        r_json = r.json()

        return r_json
