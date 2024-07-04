"""
Dagger module to build Dagger Runtime Containers.
"""

import dagger
import asyncio
from dagger import dag, function, object_type


@object_type
class RuntimeContainers:
    @function
    async def publish(self, ghcr_token: dagger.Secret):
        """
        Publishes all containers to GHCR.
        """
        ctrs = [
            self.python_pulumi,
        ]
        with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    ctr()
                    .with_registry_auth("ghcr.io", "kgb33", ghcr_token)
                    .publish(address=f"ghcr.io/kgb33/daggerverse/{ctr.__name__}:latest")
                )
                for ctr in ctrs
            ]
        return "\n".join(t.result() for t in tasks)

    @function
    def python_pulumi(self) -> dagger.Container:
        """
        "python:3.11-slim" with the Pulumi CLI installed.
        """
        cli = (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "add", "curl"])
            .with_exec(["sh", "-c", "curl -fsSL https://get.pulumi.com | sh"])
            .file("/root/.pulumi/bin/pulumi")
        )
        return (
            dag.container().from_("python:3.11-slim").with_file("/usr/bin/pulumi", cli)
        )
