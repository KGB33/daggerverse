"""
Dagger module to build Dagger Runtime Containers.
"""

import dagger
from dagger import dag, function, object_type


@object_type
class RuntimeContainers:
    @function
    def python_pulumi(self) -> dagger.Container:
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
