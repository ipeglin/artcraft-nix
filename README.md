# artcraft-nix

Nix packages and a NixOS module for the [ArtCraft](https://github.com/storytold) apps,
open-source native alternatives to the Adobe suite, and MsOffice built from their official
release AppImages. Every release is verified and mirrored, so installs keep
working even if the upstream releases disappear.

| App | Replaces | Package |
|---|---|---|
| PhotoCraft | Photoshop | `photocraft` |
| VectorCraft | Illustrator | `vectorcraft` |
| DesignCraft | InDesign | `designcraft` |
| LightCraft | Lightroom | `lightcraft` |
| FilmCraft | Premiere Pro | `filmcraft` |
| EffectCraft | After Effects | `effectcraft` |
| PdfCraft (formerly PrintCraft) | Acrobat | `pdfcraft` |
| WordCraft | Word | `wordcraft` |
| GridCraft | Excel | `gridcraft` |
| DeckCraft | PowerPoint | `deckcraft` |
| SoundCraft | Avid Pro Tools | `soundcraft` |
| CADCraft | autoCAD | `cadcraft` |

Unofficial: not affiliated with the ArtCraft authors. x86_64-linux only for now.

## Try an app

```sh
nix run github:ipeglin/artcraft-nix#photocraft
```

Each package ships the GUI and its `<app>-cli` companion.

## Install on NixOS

```nix
# flake.nix
inputs.artcraft.url = "github:ipeglin/artcraft-nix";

# in your nixosSystem modules
modules = [
  inputs.artcraft.nixosModules.default
  { programs.artcraft.enable = true; }
];
```

The module installs every app, enables `fonts.fontDir` and links
`/usr/share/fonts` to the system fonts. The apps' text tools only look there,
not through fontconfig. Options:

```nix
programs.artcraft = {
  enable = true;
  apps = [ "photocraft" "vectorcraft_0_4_0" ];  # default: every app, newest version
  linkFonts = false;                            # if you manage /usr/share/fonts yourself
};
```

Alternatives: `inputs.artcraft.packages.x86_64-linux.<app>`, or
`overlays.default`, which adds `pkgs.artcraft.<app>` built against your
nixpkgs. `nix profile install github:ipeglin/artcraft-nix` installs all of them.

## Versions

- `<app>` is the newest release; `<app>_<x>_<y>_<z>` pins a version
  (e.g. `photocraft_0_3_0`). Every stable release ever published is kept.
- `nix flake update artcraft` picks up new releases; until then your
  `flake.lock` keeps you where you are.

## Where the files come from

Each version lists three download sources, tried in order:

1. the upstream GitHub release
2. this repo's release `mirror-<app>`
3. the GitLab package registry of [ipeglin/artcraft-nix](https://gitlab.com/ipeglin/artcraft-nix)

All of them serve byte-identical files, pinned by the sha256 that upstream
published, so a mirror cannot substitute anything. If GitHub becomes
unavailable, the flake is also mirrored to GitLab: use
`gitlab:ipeglin/artcraft-nix`.

Completely offline, from any copy of an AppImage with its original filename:

```sh
nix-store --add-fixed sha256 photocraft-0.3.0-linux-x86_64.AppImage
```

Nix then finds it in the store and never downloads it.

The source code is mirrored too, at `gitlab.com/ipeglin/<repo>-mirror`
(e.g. [photocraft-mirror](https://gitlab.com/ipeglin/photocraft-mirror)). Pushes
are never forced, so upstream deleting history does not erase the mirror.

## How it stays current

[`.github/workflows/update.yml`](.github/workflows/update.yml) runs daily
([`scripts/update.py`](scripts/update.py)):

1. finds new stable releases and their published sha256
2. builds each one, runs `<app>-cli --version`, and checks that the binary
   loads no library outside the set in [`package.nix`](package.nix)
3. commits passing versions to [`versions.json`](versions.json) (failing ones are
   retried the next day and reported)
4. fills any gaps in both binary mirrors and pushes the source mirrors
5. on Mondays, bumps nixpkgs, and keeps it only if every app still builds

### Maintainer notes

- **GitLab token:** the `GITLAB_TOKEN` repo secret is a GitLab personal access
  token (scopes `api`, `write_repository`) and expires yearly. GitLab emails
  before it does. To renew it, create a new token and run
  `gh secret set GITLAB_TOKEN -R ipeglin/artcraft-nix`. Until then the
  GitLab steps fail; the next run after renewal fills in whatever is missing.
- **"references unknown libraries":** upstream started loading something new.
  Add the nixpkgs package to `runtimeDependencies` in `package.nix` and the
  library name to `KNOWN_LIBS` in `scripts/verify.py`.
- **New app:** add an entry under `apps` in `versions.json` with an empty
  `versions` object; the next run fills it in.
- **Local run:** `python3 scripts/update.py --no-mirror` discovers and
  verifies without uploading.

## License

The packaging in this repo is MIT ([LICENSE](LICENSE)). The ArtCraft apps are
licensed MIT OR Apache-2.0 by their authors. Their license files are attached
to every mirror release and GitLab package.
