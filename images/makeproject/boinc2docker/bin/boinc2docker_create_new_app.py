import subprocess
import os
from os.path import join, exists, basename
from zipfile import ZipFile
import xml.etree.cElementTree as ET
from xml.dom import minidom
from functools import partial
from textwrap import dedent
from inspect import currentframe
import pwd
import stat

def create_directories(dir):
        if not exists(dir):
            os.makedirs(dir)

def sh(cmd):
    return subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT).strip()

def download(f, appfolder):
        tgt = join(appfolder, basename(f))
        sh('wget --progress=bar:force --content-disposition --no-check-certificate %s -O %s' % (f, tgt))
        return tgt

def get_wrapper(platform, appfolder, wrapper):
        """
        Download and unzip wrapper executables from http://boinc.berkeley.edu/dl
        """
        wrapper_root = "wrapper_" + wrapper[platform] + "_" + platform
        wrapper_file = join(appfolder, wrapper_root +
                            ('.exe' if 'windows' in platform else ''))
        if not exists(wrapper_file):
            with ZipFile(download('http://boinc.berkeley.edu/dl/' + wrapper_root + '.zip', appfolder)) as zf:
                with open(wrapper_file, 'wb') as f:
                    zi = {basename(z.filename): z for z in zf.filelist}[
                        basename(wrapper_file)]
                    f.write(zf.read(zi))
                    os.fchmod(f.fileno(), 0o775)

        return wrapper_file

def create_version_desc(wrapper_file, app_name, appfolder):

        wrapper = basename(wrapper_file)

        if "windows" in wrapper:
            ok_app_name = app_name + ".bat"
        else:
            ok_app_name = app_name

        root = ET.Element("version")

        fileinfo = ET.SubElement(root, "file")
        ET.SubElement(fileinfo, "physical_name").text = wrapper
        ET.SubElement(fileinfo, "main_program")

        fileinfo = ET.SubElement(root, "file")
        ET.SubElement(fileinfo, "physical_name").text = ok_app_name
        ET.SubElement(fileinfo, "logical_name").text = app_name

        fileinfo = ET.SubElement(root, "file")
        ET.SubElement(fileinfo, "physical_name").text = app_name + ".xml"
        ET.SubElement(fileinfo, "logical_name").text = "job.xml"


        version_path = appfolder + "/" + "version.xml"
        open(version_path,'w').write(minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent=" "*4))

def create_script(appfolder, app_name, platform):

        fmt = partial(lambda s,f: s.format(**dict(globals(),**f.f_locals)),f=currentframe())

        if "windows" in platform:
            script = fmt(dedent("""wsl chmod 777 %1
wsl bash %1"""))

        else:
            script = fmt(dedent("""#!/bin/bash
chmod 777 $1

./$1"""))

        script_path = appfolder + "/" + app_name + (".bat" if "windows" in platform else "")

        with open(script_path, "w") as script_create:
                script_create.write(script)

        os.chmod(script_path, stat.S_IRWXU | stat.S_IRWXG)

def create_job_description_file(app_name, appfolder):

        root = ET.Element("job_desc")

        task = ET.SubElement(root, "task")

        ET.SubElement(task, "application").text = app_name
        ET.SubElement(task, "command_line").text = "boinc_docker"

        job_path = appfolder + "/" + app_name + ".xml"

        open(job_path,'w').write(minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent=" "*4))

def add_new_app_to_project(app_name):

    line = "    <app>\n" + "        <name>" + app_name + "</name>\n" + \
            "        <user_friendly_name>" + app_name + \
            "</user_friendly_name>\n" + "    </app>\n"

    with open("project.xml", "r+") as project_config:
        contents = project_config.readlines()
        exists = 0
        line_app = "        <user_friendly_name>" + app_name + \
            "</user_friendly_name>\n"
        for j in contents:
            if (line_app in j):
                exists = 1
        len_contents = len(contents)
        if (exists == 0):
           for i in range(len_contents):
             if i == (len_contents - 1):
                  contents.insert(i, line)
    with open("project.xml", "r") as file:
        file.close()

    with open("project.xml", "w") as project_config:
        project_config.writelines(contents)


def add_new_app(app_name, plan_class_name, input_files, ngpus, output_files_names):

        uid = pwd.getpwnam('boincadm').pw_uid
        gid = pwd.getpwnam('boincadm').pw_gid

        #path for app directories
        approot = "/home/boincadm/project/"

        app_path = ["apps", app_name, "1.0.0"]

        for path in app_path:
            approot = approot + path + "/"
            create_directories(approot)
            os.chown(approot, uid, gid)

        #get wrapper, version, docker_script, job.xml to app_directories
        platforms = ["x86_64-pc-linux-gnu", "windows_x86_64", "x86_64-apple-darwin"]
        wrapper = {"x86_64-pc-linux-gnu": "26015", "windows_x86_64": "26015", "x86_64-apple-darwin":"26015"}
        for platform in platforms:

                # create app directories
                appfolder = join(approot, platform + '__' + plan_class_name)
                create_directories(appfolder)
                os.chown(appfolder, uid, gid)

                # get wrapper
                wrapper_file = get_wrapper(platform, appfolder, wrapper)
                os.chown(wrapper_file, uid, gid)

                # create version description
                create_version_desc(wrapper_file, app_name, appfolder)
                os.chown(appfolder + "/version.xml", uid, gid)

                # create docker script
                create_script(appfolder, app_name, platform)
                if "windows" in platform:
                    os.chown(appfolder + "/" + app_name + ".bat", uid, gid)
                else: 
                    os.chown(appfolder + "/" + app_name, uid, gid)

                # create job.xml file
                create_job_description_file(app_name, appfolder)
                os.chown(appfolder + "/" + app_name + ".xml", uid, gid)

                if platform != "windows_x86_64":
                    if os.path.isfile(wrapper_file + ".zip"):
                        os.remove(wrapper_file + ".zip")
                else:
                    if os.path.isfile(appfolder + "/wrapper_26015_windows_x86_64.zip"):
                        os.remove(appfolder + "/wrapper_26015_windows_x86_64.zip")

        #add new application to project.xml
        add_new_app_to_project(app_name)

        # run command bin/xadd for adding new application
        sh("/home/boincadm/project/bin/xadd")

        # run command bin/update_versions for adding application version
        sh("yes | /home/boincadm/project/bin/update_versions")

        os.chown("/home/boincadm/project/download/" + app_name + ".bat", uid, gid)
        os.chown("/home/boincadm/project/download/" + app_name, uid, gid)

        os.chown("/home/boincadm/project/download/" + app_name + ".xml", uid, gid)

        for i in wrapper:
            if i != "windows_x86_64":
                os.chown("/home/boincadm/project/download/wrapper_" + wrapper[i] + "_" + i, uid, gid)
            else:
                os.chown("/home/boincadm/project/download/wrapper_" + wrapper[i] + "_" + i + ".exe", uid, gid)
