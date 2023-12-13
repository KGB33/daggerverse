from dataclasses import dataclass
from time import time
import dagger
from dagger.mod import function


@function
async def cli() -> dagger.Container:
    control = node("control_foo")
    worker1 = node("worker1_foo")
    worker2 = node("worker2_foo")
    await control.start()
    await worker1.start()
    await worker2.start()
    return (
        dagger.container()
        .from_("alpine")
        .with_file("/bin/kubectl", kubectl(), permissions=755)
        .with_file("/bin/talosctl", talosctl(), permissions=755)
        .with_env_variable("CACHE_BUSTER", str(time()))
        .with_service_binding("control", control)
        .with_service_binding("worker1", worker1)
        .with_service_binding("worker2", worker2)
        .with_exec(["talosctl", "gen", "config", "daged", "https://control:6443"])
        .with_env_variable("TALOSCONFIG", "/talosconfig")
        .with_exec(
            [
                "talosctl",
                "apply-config",
                "--insecure",
                "--nodes",
                "control",
                "--file",
                "controlplane.yaml",
            ]
        )
        .with_exec(
            [
                "talosctl",
                "apply-config",
                "--insecure",
                "--nodes",
                "worker1",
                "--file",
                "worker.yaml",
            ]
        )
        .with_exec(
            [
                "talosctl",
                "apply-config",
                "--insecure",
                "--nodes",
                "worker2",
                "--file",
                "worker.yaml",
            ]
        )
        # .with_exec(
        #     ["talosctl", "bootstrap", "--nodes", "control", "--endpoints", "control"]
        # )
    )


def node(name: str) -> dagger.Service:
    """
    Each name needs to be unique.
    """
    return (
        dagger.container()
        .from_("ghcr.io/siderolabs/talos")
        .with_env_variable("PLATFORM", "container")
        .with_new_file("/etc/hostname", contents=name)
        # Tempfs-s
        .with_mounted_temp("/run")
        .with_mounted_temp("/system")
        .with_mounted_temp("/tmp")
        # Volumes
        .with_mounted_cache("/system/state", dagger.cache_volume(f"{name}-system-state"))
        .with_mounted_cache("/var", dagger.cache_volume(f"{name}-var"))
        .with_mounted_cache("/etc/cni", dagger.cache_volume(f"{name}-etc-cni"))
        .with_mounted_cache("/etc/kubernetes", dagger.cache_volume(f"{name}-etc-kubernetes"))
        .with_mounted_cache("/usr/libexec/kubernetes", dagger.cache_volume(f"{name}-usr-libexec-kubernetes"))
        .with_mounted_cache("/usr/etc/udev", dagger.cache_volume(f"{name}-usr-etc-udev"))
        .with_mounted_cache("/opt", dagger.cache_volume(f"{name}-opt"))
        .with_exposed_port(6443, skip_health_check=True)  # Kubectl
        .with_exposed_port(50000)  # Talosctl
        .with_exec([], insecure_root_capabilities=True)
        .as_service()
    )


def talosctl() -> dagger.File:
    return (
        dagger.wolfi()
        .base()
        .with_packages(["curl"])
        .container()
        .with_exec(
            [
                "curl",
                "-sLO",
                "https://github.com/siderolabs/talos/releases/latest/download/talosctl-linux-amd64",
            ]
        )
        .file("/talosctl-linux-amd64")
    )


def kubectl(version="v1.28.4") -> dagger.File:
    return (
        dagger.wolfi()
        .base()
        .with_packages(["curl"])
        .container()
        .with_exec(
            [
                "curl",
                "-sLO",
                f"https://dl.k8s.io/release/{version}/bin/linux/amd64/kubectl",
            ]
        )
        .file("kubectl")
    )
