{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
    uv
  ];

  shellHook = ''
    echo "Python 3.12 and uv development environment"
    python3 --version
    uv --version
  '';
}
