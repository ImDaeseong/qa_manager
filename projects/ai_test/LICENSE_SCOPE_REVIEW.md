# ai_test license scope review

This is a release-planning record, not legal advice. Final licensing requires the copyright holder's confirmation and, where employment or contract rights may apply, qualified legal review.

## Audited release boundary

- Baseline: `ai_test@a7b2bfa`, source-only distribution.
- Git tracks 769 files across 18 subprojects. Media, audio, video, compiled executables, and build-state files are excluded at HEAD by `scripts/check_source_only.py`.
- The repository has 41 commits. Git history shows two author display names (`daesung`, `ImDaeseong`) using the same email address. This supports, but does not prove, a single-author history; it does not establish employer, client, or upstream rights.
- No tracked minified bundles or generated `dist`/`build` directories were found.

## Code included in the repository

| Scope | Current evidence | Licensing consequence |
|---|---|---|
| Owner-authored source and documentation | No root `LICENSE`; no other commit email; no per-file license headers | Copyright remains reserved until the owner selects a license. |
| Vendored JsonCpp 1.7.2 source | `run_game/run_game/json/`; upstream 1.7.2 notice restored in the same directory; integrity guard passes | Preserve JsonCpp's own MIT/public-domain notice. A root license must explicitly exclude third-party code governed by its own notice. |
| Package manifests and lockfiles | Dependencies are named and version-locked; dependency source is not tracked | A root license covers this repository's original files, not packages downloaded by package managers. Users remain subject to each dependency's terms. |

## Dependency boundary requiring a visible warning

Three subprojects depend on Remotion packages:

- `ai-webtoon_capcut/remotion`: Remotion 4.0.473
- `ai_anime_production`: Remotion 4.0.500
- `lyricvideo`: Remotion 4.0.500

Their lockfiles label the core Remotion packages `SEE LICENSE IN LICENSE.md`. Remotion's official license is source-available with eligibility and use restrictions; it is not an OSI-approved permissive license. Licensing the repository's original code under MIT or Apache-2.0 would not relicense Remotion or guarantee that every user may run it. The release README must direct users to the [Remotion license](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) before installing or using those subprojects.

Other directly declared JavaScript dependencies in the lockfiles are marked MIT or Apache-2.0. Python and Go dependencies are installed separately and are not vendored, but a complete dependency-license/SBOM review is still required before distributing binaries or bundled environments.

## Owner-code license options

### Recommended default: MIT

Use MIT if the intended outcome is simple, permissive worldwide source reuse with attribution and warranty disclaimer. The [OSI MIT text](https://opensource.org/license/mit) requires preservation of the copyright and permission notice. This is the smallest fit for a personal multi-project source repository and aligns with the included JsonCpp notice without replacing it.

### Alternative: Apache-2.0

Use Apache-2.0 if an explicit contributor patent grant and patent-termination provision are desired. The [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) carries more notice and modification obligations. It does not solve provenance or dependency-license uncertainty.

Neither option makes third-party packages, APIs, media, or historical excluded files available under the chosen root license.

## Owner confirmations required before adding a root license

1. Confirm that the source intended for licensing was created personally or can legally be relicensed, and contains no employer, client, or confidential code.
2. Confirm that outside snippets, templates, AI-assisted output, and copied project scaffolding were reviewed and that the owner has the rights needed for the selected license.
3. Choose `MIT` (recommended) or `Apache-2.0`, and choose the copyright holder name/year to place in the license.
4. Accept the explicit exclusions: JsonCpp remains under its bundled notice; Remotion and all installed dependencies remain under their own terms; external API/content terms are separate.
5. Decide separately whether old Git history containing removed media/build files will remain public or be rewritten before release.

## Current decision

**HOLD.** The technical scope is narrow enough to license, but no root license should be added until the owner completes the confirmations above. The Remotion warning and third-party exclusion must accompany whichever owner-code license is selected.
