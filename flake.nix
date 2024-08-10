{
  description = "Simple mqtt exporter";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
    ...
  } @ inputs: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      overlays = [self.overlay];
    };
  in {
    overlay = final: prev: {
      mqtt_exporter = prev.python3Packages.buildPythonPackage rec {
        pname = "mqtt_exporter";
        version = "0.3.0";

        src = ./.;

        format = "other";

        installPhase = ''
          mkdir -p $out/bin
          cp mqtt_exporter.py $out/bin/mqtt_exporter
        '';

        meta = with pkgs.lib; {
          description = "Simple prometheus exporter from mqtt";
          license = licenses.mit;
        };

        propagatedBuildInputs = with prev; [
          python3Packages.paho-mqtt
          prev.python3Packages.prometheus-client
        ];
      };
    };

    packages.${system}.default = pkgs.mqtt_exporter;

    devShell.${system} = pkgs.mkShell {
      buildInputs = with pkgs; [
        python3.pkgs.prometheus_client
        python3.pkgs.paho-mqtt
      ];
    };
  };
}
