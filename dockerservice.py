# -*- coding: utf-8 -*-

from twisted.internet import defer
from twisted.python import log

from buildbot import config
from buildbot.interfaces import LatentWorkerCannotSubstantiate
from buildbot.interfaces import LatentWorkerFailedToSubstantiate

from buildbot.worker.docker import DockerLatentWorker

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

    def checkConfig(self, name, password, docker_host, image=None, command=None,
                    volumes=None, followStartupLogs=False,
                    masterFQDN=None, autopull=False, alwaysPull=False, registryAuth=None,
                    environment=None, networks=None,
                    placementConstraints=None, secrets=None, **kwargs):
        super().checkConfig(name, password, docker_host, image=image, volumes=volumes, masterFQDN=masterFQDN, **kwargs)

    @defer.inlineCallbacks
    def reconfigService(self, name, password, docker_host, image=None, command=None,
                        volumes=None, followStartupLogs=False,
                        masterFQDN=None, autopull=False, alwaysPull=False, registryAuth=None,
                        environment=None, networks=None,
                        placementConstraints=None, secrets=None, **kwargs):

        yield super().reconfigService(name, password, docker_host, image=image, command=command, volumes=volumes, followStartupLogs=followStartupLogs, masterFQDN=masterFQDN, autopull=autopull, alwaysPull=alwaysPull, **kwargs)

        self.client_args = {'base_url': docker_host, 'tls': False}
        # Prepare the parameters for the Docker Client object.
        self.environment = environment or []
        self.networks = networks or []
        self.placementConstraints = placementConstraints or []
        self.registryAuth = registryAuth or {}
        self.secrets = secrets or []

    def _thd_start_instance(self, image, dockerfile, volumes, custom_context, encoding, buildargs):
        docker_client = self._getDockerClient()

        if self.registryAuth:
            try:
                docker_client.login(username=self.registryAuth['username'],
                                    password=self.registryAuth['password'],
                                    registry=self.registryAuth['host'])
            except docker.errors.APIError:
                log.msg('Error while login to registry host: %s', e)

        service_name = self.getContainerName()
        # cleanup the old instances
        instances = docker_client.services(
            filters=dict(name=service_name))

        for instance in instances:
            try:
                docker_client.remove_service(instance['ID'])
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
        for volume_string in (self.volumes or []):
            try:
                bind, volume = volume_string.split(":", 1)
            except ValueError:
                config.error("Invalid volume definition for docker "
                             "%s. Skipping..." % volume_string)
                continue

            ro = False
            if volume.endswith(':ro') or volume.endswith(':rw'):
                ro = volume[-2:] == 'ro'
                volume = volume[:-3]

            mounts.append(docker.types.Mount(volume, bind, read_only=ro))

        env = self.createEnvironment()
        env.update(self.environment)

        secretsArr = []
        for secret in self.secrets:
            secretsArr.append(docker.types.SecretReference(
                secret_id=secret['id'],
                secret_name=secret['name'],
                filename=secret['file'],
                mode=secret['mode'],))

        placement = docker.types.Placement(constraints=self.placementConstraints)
        container_spec = docker.types.ContainerSpec(image=image,
            command=self.command, env=env, mounts=mounts, secrets=secretsArr)
        task_tmpl = docker.types.TaskTemplate(container_spec,
            networks=self.networks, placement=placement)
        instance = docker_client.create_service(task_tmpl,
            name=self.getContainerName(),
            networks=self.networks)

        if instance.get('ID') is None:
            log.msg('Failed to create the service')
            raise LatentWorkerFailedToSubstantiate(
                'Failed to start service'
            )
        shortid = instance['ID'][:6]
        log.msg('Service created, ID: %s ...' % (shortid,))
        instance['image'] = image
        self.instance = instance

        if self.followStartupLogs:
            logs = docker_client.service_logs(instance, stdout=True, stderr=True, follow=True)
            for line in logs:
                log.msg("docker VM %s: %s" % (shortid, line.strip()))
                if self.conn:
                    break
            del logs
        return [instance['ID'], image]

    def _thd_stop_instance(self, instance, fast):
        docker_client = self._getDockerClient()
        log.msg('Stopping service %s ...' % instance['ID'][:6])
        docker_client.remove_service(instance['ID'])
        if self.image is None: # This is case where image create locally from Dockerfile.
            try:
                docker_client.remove_image(image=instance['image'])
            except docker.errors.APIError as e:
                log.msg('Error while removing the image: %s', e)
