"""
A generated module for Flyio functions.
"""

import dagger
from dagger import dag, function, object_type

JQ_JSON_CAPTURE = r"(?<json>{(.|\n)*})"


@object_type
class Flyio:
    fly_api_token: dagger.Secret | None = None

    @property
    def _token(self) -> dagger.Secret:
        if self.fly_api_token is None:
            raise ValueError(
                "'--fly-api-token' is not set, cannot preform actions that need authentication."
            )
        return self.fly_api_token

    @function
    def base(self) -> dagger.Container:
        """
        A simple container with the FLY_API_TOKEN environment variable set and 'flyctl' installed.
        """
        return (
            dag.container()
            .from_("alpine")
            .with_file("/usr/bin/flyctl", self.flyctl())
            .with_exec(["mkdir", "/fly"])
            .with_workdir("/fly")
            .with_secret_variable("FLY_API_TOKEN", self._token)
        )

    @function
    async def launch(self, fly_toml: dagger.File) -> str:
        """
        Launches the provided fly.toml.
        """
        return await (
            self.base()
            .with_file("/fly/fly.toml", fly_toml)
            .with_exec(
                [
                    "flyctl",
                    "launch",
                    "--copy-config",
                    "--auto-confirm",
                    "--ha=false",
                    "--now",
                ]
            )
            .stdout()
        )

    @function
    async def cert_add(self, domain: str) -> str:
        """
        Adds a fly cert for the provided domain, then
        returns a json string to verify the cert.
        """
        try:
            _ = self.base().with_exec(["fly", "certs", "add", domain])
        except dagger.DaggerError:
            pass  # The cert already exists
        return await self.cert_check(domain)

    @function
    async def cert_check(self, domain: str) -> str:
        """
        Returns a json string from `fly cert check`.
        """
        return await (
            self.base()
            .with_exec(
                [
                    "sh",
                    "-c",
                    f"fly cert check {domain}"
                    + f"| jq -R -s 'capture({JQ_JSON_CAPTURE}) | .json | fromjson'",
                ]
            )
            .stdout()
        )

    @function
    def flyctl(self, version: str = "latest") -> dagger.File:
        """
        Returns the flyctl file from Fly.io
        """
        INSTALL_DIR = "/tmp"
        return (
            dag.container()
            .from_("alpine")
            .with_exec(["apk", "add", "curl"])
            .with_env_variable("FLYCTL_INSTALL", INSTALL_DIR)
            .with_exec(["curl", "-LO", "https://fly.io/install.sh"])
            .with_exec(["sh", "install.sh", version])
            .file(f"{INSTALL_DIR}/bin/flyctl")
        )
