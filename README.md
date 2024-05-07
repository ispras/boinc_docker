
# boinc_docker

`boinc_docker` is the easiest way to run your own [BOINC](http://boinc.berkeley.edu/) server. You can run the server on a Linux machine, in which case the requirements are, 

* [Docker](https://docs.docker.com/engine/installation/) (>=17.09.0ce)
* [docker-compose](https://docs.docker.com/compose/install/) (>=1.17.0 but !=1.19.0 due to a [bug](https://github.com/docker/docker-py/issues/1841))
* git

## Documentation
boinc_docker is project, that gives an opportunity to run BOINC (Volunteer system) jobs directly in a Docker. The solution is based on [boinc-server-docker](https://github.com/marius311/boinc-server-docker). It allows to automatically set up a BOINC server in Docker with a special module [boinc2docker](https://github.com/marius311/boinc2docker). Boinc2docker is a plugin written in Python, which allows sending Docker workunits to BOINC clients. The execution of Docker containers takes place inside virtual machine of Virtualbox hypervisor. 

New version of boinc2docker is a python module that automates the process of creating BOINC application and sending BOINC workunit. Bash script is considered as executable code for UNIX OS, while bat-file is for Windows. In both cases, the script is run under BOINC wrapper. The content of bash/bat file includes commands to run user-written bash script, which in turn initiates Docker container work. The user's bash script is passed along with the other input files of the BOINC workunit. Downloading a Docker image to a volunteer node can be done in one of two ways:
    * With the help of docker pull command in a user bash script;
    * Docker image is downloaded to the BOINC server and sliced into layers. Each layer is packed into an archive and then passed to the BOINC client along with other user input files;

![boinc_docker](https://github.com/ispras/boinc_docker/assets/62812801/92e469bc-d7d6-4f45-b958-b0c188460ac8)

### Start

1. To start boinc_docker: 
```bash
git clone https://github.com/ispras/boinc_docker.git
cd boinc_docker
```
2. Change IP address from 127.0.0.1 to host's IP address in URL_BASE variable;
3. In order to get suitable version of BOINC server:
```bash
git submodule init
git submodule update
```
4. Start building the application:
```bash
make up
```

You can now visit the server webpage and connect clients to the server at http://ip_address/boincserver. 

### Run BOINC job with Docker

1. Get in Docker container with BOINC server configured: 

```bash
docker exec -it boincdocker_apache_1 /bin/bash
```

2. Create bash script with Docker/Docker compose commands:

![docker_gpu_script](https://github.com/ispras/boinc_docker/assets/62812801/95798b29-23f8-47cc-951e-da1f1e353749)

3. Run bin/boinc2docker_create_work with necessary parameters: 

![boinc_docker_gpu_workunit](https://github.com/ispras/boinc_docker/assets/62812801/49f5a3d0-b9bf-4312-a1ed-7b197ca080bf)


List of the module parameters that are available for user to change are presented below: 

  * appname - BOINC application name;
  * new_app - flag for creating new BOINC application. If user wants to send new BOINC workunit of already created BOINC application, the parameter must not be used;  
  * image - list of user Docker images. The flag is used, if user wants to send a Docker image as several archives;
  * docker_registry - list of docker login options for using users' docker registry: user, password, docker registry name. The parameter must be used with image;
  * input_files - list of user input files names, except bash script and archive of the Docker images;
  * output_files_names - list of files with computational results;
  * bash_script_path - path to users' bash script;
  * plan_class_name - plan class name;
  * plan_class_new - flag for creating new plan class;
  * use_docker_compose - parameter for plan class, that requires docker-compose (old version) to be installed and available for execution on BOINC client;
  * use_compose - parameter for plan class, that requires docker compose (new version) to be installed and available for execution on BOINC client;
  * gpu_type - BOINC plan class parameter (gpu type);
  * ngpus - BOINC plan class parameter (amount of gpus);
  * min_gpu_ram_mb, gpu_ram_used, driver_versions, cuda_versions, use_ati_libs, use_amd_libs, min_ncpus, max_threads, mem_usage_base_mb, mem_usage_per_cpu_mb - [BOINC plan class parameters](https://boinc.berkeley.edu/trac/wiki/AppPlanSpec);

4. Check the results in upload directory on BOINC server:

![boinc_docker_gpu_result](https://github.com/ispras/boinc_docker/assets/62812801/46dcc270-7946-46a1-baf9-3926743393cf)

