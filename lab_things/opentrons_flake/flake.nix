{
  description = "Nix shell for running Opentrons AppImages with proper libcrypt support";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        appimage-run-with-crypt = pkgs.appimage-run.override {
          extraPkgs = pkgs: [
            pkgs.glibc
            pkgs.libxcrypt-legacy
          ];
        };
      in {
        devShells.default = pkgs.mkShell {
          packages = [
            appimage-run-with-crypt
          ];

          shellHook = ''
            echo "🔬 Welcome to the Opentrons AppImage shell."

            # Find first matching AppImage and run it if found
            opentrons_appimage=$(find . -maxdepth 1 -type f -name 'Opentrons*.AppImage' | head -n 1)
            if [ -n "$opentrons_appimage" ]; then
              echo "🚀 Launching: $opentrons_appimage"
              appimage-run "$opentrons_appimage"
              exit
            else
              echo "⚠️  No Opentrons*.AppImage found in the current directory."
            fi
          '';
        };
      });
}
