{
  description = "Dagger Runtime Containers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default-linux";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        pythonPulumi = pkgs.dockerTools.buildLayeredImage {
          name = "python-pulumi";
          contents = with pkgs; [
            python312
            uv
            pulumi
          ];
        };
      });
}
