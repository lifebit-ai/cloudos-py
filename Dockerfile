# Full contents of Dockerfile

FROM continuumio/miniconda3:4.10.3	
LABEL description="Base docker image with conda and util libraries"

# Use the base conda env to not be reliant on conda activate when using pip
ARG ENV_NAME="base"

# Install mamba for faster installation in the subsequent step
RUN conda install -c conda-forge mamba -y

# Install the conda environment
COPY environment.yml /
RUN mamba env update --quiet --name ${ENV_NAME} --file /environment.yml && conda clean -a

# Add conda installation dir to PATH (instead of doing 'conda activate')
ENV PATH /opt/conda/envs/${ENV_NAME}/bin:$PATH

# Dump the details of the installed packages to a file for posterity
RUN mamba env export --name ${ENV_NAME} > ${ENV_NAME}_exported.yml

# Install ps to avoid Nextflow problems in cloudOS
RUN apt-get update \
  && apt-get install procps -y

# Copy local package files to be able to install
COPY . /
# Add the created folder to PATH so that tools are accessible
ENV PATH  /cloudos:$PATH
# Install from local files, -e / points to where the setup.py file is located
RUN pip install -e /
# Make the python files executable from anyone (user, group, owner)
RUN chmod ugo+x /cloudos/*py
RUN chmod ugo+x /cloudos/jobs/*py
RUN chmod ugo+x /cloudos/utils/*py
