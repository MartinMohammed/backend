{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    uv
<<<<<<< HEAD
=======
    ngrok
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
  ];

  shellHook = ''
    uv --version
  '';
}
