{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    uv
    ngrok
  ];

  shellHook = ''
    uv --version
  '';
}
