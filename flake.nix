{
  description = "vatic — AI-driven vault editor for personal knowledge management";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; config.allowUnfree = true; };
        python = pkgs.python3;
        pythonPackages = python.pkgs;
      in
      {
        devShells.default = pkgs.mkShell {
          name = "vatic-dev";
          buildInputs = with pkgs; [
            # Python and package management
            python
            pythonPackages.pip
            pythonPackages.setuptools
            pythonPackages.wheel

            # Project dependencies
            pythonPackages.click
            pythonPackages.platformdirs
            pythonPackages.tomli-w

            # Optional dev dependencies
            pythonPackages.pytest
            pythonPackages.pytest-cov
            pythonPackages.black
            pythonPackages.ruff
            pythonPackages.mypy

            # External tools
            obsidian
          ];

          shellHook = ''
            # Install the vatic package in editable mode
            if [ ! -d ".venv" ]; then
              ${python}/bin/python -m venv .venv
            fi
            source .venv/bin/activate
            pip install -e .
          '';
        };
      }
    );
}