# -*- coding: utf-8 -*-

import time

from buildbot import config
from buildbot.interfaces import LatentWorkerFailedToSubstantiate
from buildbot.worker.docker import DockerLatentWorker
from twisted.internet import defer
from twisted.python import log

try:
    import docker
    from docker import client
    from docker.errors import NotFound

    _hush_pyflakes = [docker, client]
    docker_py_version = float(docker.__version__.rsplit(".", 1)[0])
except ImportError:
    docker = None
    client = None
    docker_py_version = 0.0


class DockerSwarmLatentWorker(DockerLatentWorker):
    """DockerSwarmLatentWorker class is docker latent worker for swarm."""

    def checkConfig(
        self,
        name,
        password,
        docker_host,
        image=None,
        command=None,
        volumes=None,
        followStartupLogs=False,
        masterFQDN=None,
        autopull=False,
        alwaysPull=False,
        registryAuth=None,
        environment=None,
        networks=None,
        placementConstraints=None,
        secrets=None,
        **kwargs,
    ):
        super().checkConfig(
            name,
            password,
            docker_host,
            image=image,
            volumes=volumes,
            masterFQDN=masterFQDN,
            **kwargs,
        )

    @defer.inlineCallbacks
    def reconfigService(
        self,
        name,
        password,
        docker_host,
        image=None,
        command=None,
        volumes=None,
        followStartupLogs=False,
        masterFQDN=None,
        autopull=False,
        alwaysPull=False,
        registryAuth=None,
        environment=None,
        networks=None,
        placementConstraints=None,
        secrets=None,
        **kwargs,
    ):
        yield super().reconfigService(
            name,
            password,
            docker_host,
            image=image,
            command=command,
            volumes=volumes,
            followStartupLogs=followStartupLogs,
            masterFQDN=masterFQDN,
            autopull=autopull,
            alwaysPull=alwaysPull,
            **kwargs,
        )

        self.client_args = {"base_url": docker_host, "tls": False}
        # Prepare the parameters for the Docker Client object.
        self.environment = environment or []
        self.networks = networks or []
        self.placementConstraints = placementConstraints or []
        self.registryAuth = registryAuth or {}
        self.secrets = secrets or []

    def _getDockerClient(self, client_args):
        return client.APIClient(**client_args)

    def _thd_start_instance(
        self,
        docker_host,
        image,
        dockerfile,
        volumes,
        host_config,
        custom_context,
        encoding,
        target,
        buildargs,
        hostname,
    ):
        curr_client_args = self.client_args.copy()
        curr_client_args["base_url"] = docker_host

        docker_client = self._getDockerClient(curr_client_args)
        # log.msg(docker_client.version())

        if self.registryAuth:
            try:
                docker_client.login(
                    username=self.registryAuth["username"],
                    password=self.registryAuth["password"],
                    registry=self.registryAuth["host"],
                )
            except docker.errors.APIError as e:
                log.msg(f"Error while login to registry host: {str(e)}")

        service_name = self.getContainerName()
        # cleanup the old instances
        instances = docker_client.services(filters=dict(name=service_name))

        for instance in instances:
            try:
                id = instance["ID"]
                log.msg(f"Remove instance {id}")
                docker_client.remove_service(id)
            except NotFound:
                pass

        # found = self._image_exists(docker_client, image)
        # if ((not found) or self.alwaysPull) and self.autopull:
        #     if (not found):
        #         log.msg("Image '%s' not found, pulling from registry" % image)
        #     docker_client.pull(image, auth_config=self.registryAuth)

        # if (not self._image_exists(docker_client, image)):
        #     log.msg("Image '%s' not found" % image)
        #     raise LatentWorkerCannotSubstantiate(
        #         'Image "%s" not found on docker host.' % image
        #     )

        mounts = []
        for volume_string in self.volumes or []:
            try:
                bind, volume = volume_string.split(":", 1)
            except ValueError:
                config.error(
                    f"Invalid volume definition for docker {volume_string}. Skipping..."
                )
                continue

            ro = False
            if volume.endswith(":ro") or volume.endswith(":rw"):
                ro = volume[-2:] == "ro"
                volume = volume[:-3]

            mounts.append(docker.types.Mount(volume, bind, read_only=ro))

        env = self.createEnvironment()
        env.update(self.environment)

        secretsArr = []
        for secret in self.secrets:
            secretsArr.append(
                docker.types.SecretReference(
                    secret_id=secret["id"],
                    secret_name=secret["name"],
                    filename=secret["file"],
                    mode=secret["mode"],
                )
            )

        placement = docker.types.Placement(constraints=self.placementConstraints)
        container_spec = docker.types.ContainerSpec(
            image=image,
            command=self.command,
            env=env,
            mounts=mounts,
            secrets=secretsArr,
        )
        task_tmpl = docker.types.TaskTemplate(
            container_spec, networks=self.networks, placement=placement
        )
        instance = docker_client.create_service(
            task_tmpl, name=self.getContainerName(), networks=self.networks
        )

        if instance.get("ID") is None:
            log.msg("Failed to create the service")
            raise LatentWorkerFailedToSubstantiate("Failed to start service")
        id = instance["ID"]
        shortid = id[:6]
        log.msg(f"Service created, ID: {shortid} ...")
        instance["image"] = image
        self.instance = instance
        self._curr_client_args = curr_client_args

        if self.followStartupLogs:
            logs = docker_client.service_logs(
                instance, stdout=True, stderr=True, follow=True
            )
            for line in logs:
                log.msg(f"docker VM {shortid}: {line.strip()}")
                if self.conn:
                    break
            del logs
        return [id, image]

    # def stop_instance(self, fast=False):
    #     log.msg('stop_instance executed ...')
    #     super().stop_instance(fast)

    def _thd_stop_instance(self, instance, curr_client_args, fast):
        docker_client = self._getDockerClient(curr_client_args)
        # log.msg(docker_client.version())
        id = instance["ID"]
        log.msg("Stopping service {} ...".format(id[:6]))
        # docker_client.stop(id)
        # if not fast:
        #     docker_client.wait(id)
        try:
            if docker_client.remove_service(id):
                log.msg("Stopped service {} ...".format(id[:6]))
            else:
                log.msg("Stopped service {} failed".format(id[:6]))
        except NotFound:
            pass

        time.sleep(30)

        # Skip remove image

        # if self.image is None: # This is case where image create locally from Dockerfile.
        #     try:
        #         docker_client.remove_image(image=instance['image'])
        #     except docker.errors.APIError as e:
        #         log.msg('Error while removing the image: %s', e)
