{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    uv
  ];

  shellHook = ''
    uv --version
  '';
}
