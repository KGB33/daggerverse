import dagger
from dagger import dag, function


@function
async def base(toolchain: dagger.File | None = None) -> dagger.Container:
    ctr = (
        dag.container()
        .from_("rust")
        .with_directory("/src", dag.directory())
        .with_workdir("/src")
    )
    print(toolchain)
    if toolchain is None:
        ctr = ctr.with_new_file(
            "/src/rust-toolchain.toml", contents='[toolchain]\nchannel="nightly"'
        )
    else:
        ctr = ctr.with_file("/src/rust-toolchain.toml", toolchain)

    return ctr.with_exec(["cargo", "version"])
