# Harbor images for Buildbot workers

This directory contains Dockerfiles and related files for building images used
by Buildbot workers. These images are published to the Harbor registry at
`harbor.nextgis.net/ngqgis`.

To work with the images in this repository, request access to the
`harbor.nextgis.net/ngqgis` project from the project administrator.

Log in with your LDAP account:

```bash
docker login harbor.nextgis.net
```

Buildbot worker images are stored in the `ngqgis` project (repository
`ngqgis`). New image names and build targets should use simple kebab-case
naming.

Basic workflow:

1. Log in to Harbor.
2. Change directory to `docker/workers`.
3. Build the required target with `docker buildx bake`.
4. Publish the same target with `docker buildx bake --push`.

Example for a specific image:

```bash
cd docker/workers
docker buildx bake ubuntu-worker-jammy
docker buildx bake --push ubuntu-worker-jammy
```

To build and push all images at once:

```bash
cd docker/workers
docker buildx bake all
docker buildx bake --push all
```

When creating a new image, ensure it contains the file `/worker/info/admin`.
Existing worker images already include this file; new images should follow the
same convention.

If an image was uploaded by mistake or is no longer needed, delete it via the
Harbor web interface.
