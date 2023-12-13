import dagger
from dagger import dag, function


@function
async def base(toolchain: dagger.File | None = None) -> dagger.Container:
    ctr = dag.container().from_("rust")
    if toolchain is None:
        ctr = ctr.with_new_file(
            "/rust-toolchain.toml", contents='[toolchain]\nchannel="nightly"'
        )
    else:
        ctr = ctr.with_file("/rust-toolchain.toml", toolchain)

    return ctr.with_exec(["cargo", "version"])


@function
async def build(
    src: dagger.Directory,
    name: str,
    toolchain: dagger.File | None = None,
    target: str = "x86_64-unknown-linux-gnu",
) -> dagger.File:
    ctr = await base(toolchain)
    return (
        ctr.with_directory("/src", src)
        .with_workdir("/src")
        .with_exec(["mv", "/rust-toolchain.toml", "/src/rust-toolchain.toml"])
        .with_env_variable(
            "RUSTFLAGS", "-C target-feature=+crt-static -C relocation-model=static"
        )
        .with_exec(["cargo", "build", "--release", "--target", target])
        .file(f"/src/target/{target}/release/{name}")
    )
