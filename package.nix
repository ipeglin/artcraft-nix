# One ArtCraft app at one version, built from its upstream release AppImage.
#
# The AppImages bundle no libraries: a Rust GUI binary (usually with a `-cli`
# companion) linked only against glibc/libgcc and ALSA, which dlopen()s its
# graphics stack at runtime. So the payload is extracted and autoPatchelf'd,
# with that dlopen set on the RPATH via runtimeDependencies, instead of running
# inside wrapType2's bubblewrap FHS env. scripts/verify.py rejects any release
# that references a library outside this set.
{
  lib,
  stdenv,
  fetchurl,
  appimageTools,
  autoPatchelfHook,
  makeWrapper,
  # linked
  alsa-lib,
  # dlopen()ed
  dbus,
  libGL,
  vulkan-loader,
  wayland,
  libx11,
  libxcb,
  libxcursor,
  libxi,
  libxkbcommon,
  libva,
  # from default.nix
  app,
  version,
  release,
  info,
  mirrors,
}:

stdenv.mkDerivation {
  pname = release.bin;
  inherit version;

  src = appimageTools.extract {
    pname = release.bin;
    inherit version;
    # Upstream first, then this flake's mirrors. fetchurl names the store path
    # after the file, so `nix-store --add-fixed sha256 <file>` also satisfies
    # it with no network at all.
    src = fetchurl {
      urls = [
        "https://github.com/${info.repo}/releases/download/${release.tag}/${release.file}"
        "https://github.com/${mirrors.github}/releases/download/mirror-${app}/${release.file}"
        "https://gitlab.com/api/v4/projects/${lib.escapeURL mirrors.gitlab}/packages/generic/${app}/${version}/${release.file}"
      ];
      inherit (release) hash;
    };
  };

  nativeBuildInputs = [ autoPatchelfHook makeWrapper ];
  buildInputs = [ stdenv.cc.cc.lib alsa-lib ];
  # lib.getLib: some of these (dbus) keep their shared objects in a separate
  # `lib` output, and the default output on the RPATH holds no library at all.
  runtimeDependencies = map lib.getLib [
    dbus
    libGL
    vulkan-loader
    wayland
    libx11
    libxcb
    libxcursor
    libxi
    libxkbcommon
    libva
  ];
  # NVIDIA's libcuda / libnvcuvid / libnvidia-encode (FilmCraft's NVDEC/NVENC)
  # ship with the driver, not nixpkgs; NixOS exposes them here. Elsewhere the
  # directory is absent and the app falls back to software decode/encode.
  appendRunpaths = [ "/run/opengl-driver/lib" ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    install -Dm755 -t $out/bin usr/bin/*
    if [ -d usr/share ]; then cp -r usr/share $out/share; fi
    runHook postInstall
  '';

  # Some apps preflight their libraries with `ldconfig -p`, which can't see the
  # RPATH above (dlopen finds them fine), then warn or refuse to start.
  postFixup = ''
    for bin in $out/bin/*; do
      var="$(basename "$bin" | tr 'a-z-' 'A-Z_')_SKIP_LIB_CHECK"
      if grep -qa "$var" "$bin"; then
        wrapProgram "$bin" --set-default "$var" 1
      fi
    done
  '';

  meta = {
    description = "${info.title}: ${info.summary} (ArtCraft)";
    homepage = "https://github.com/${info.repo}";
    license = with lib.licenses; [ mit asl20 ];
    mainProgram = release.bin;
    platforms = [ "x86_64-linux" ];
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
  };
}
