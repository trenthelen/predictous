"""Docker utilities."""

import logging
from pathlib import Path

import docker
import docker.errors

logger = logging.getLogger(__name__)


def build_image(
    docker_client: docker.DockerClient,
    path: Path,
    image_tag: str,
) -> None:
    """Build a Docker image from a Dockerfile."""
    logger.info(f"Building Docker image: {image_tag} from {path}")

    try:
        _, build_logs = docker_client.images.build(
            path=str(path), tag=image_tag, rm=True, forcerm=True, quiet=False
        )

        for log in build_logs:
            if "stream" in log:
                logger.debug(f"Docker build: {log['stream'].strip()}")
            elif "error" in log:
                logger.error(f"Docker build error: {log['error']}")

        logger.info(f"Docker image built successfully: {image_tag}")

    except docker.errors.BuildError as e:
        logger.error(f"Docker build failed: {e}")
        raise RuntimeError(f"Docker build failed: {e}") from e


def image_exists(docker_client: docker.DockerClient, image_tag: str) -> bool:
    """Check if a Docker image exists."""
    try:
        docker_client.images.get(image_tag)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception:
        return False
