# ai_test Git history release audit

Audit date: 2026-09-21  
Baseline: `ai_test@31c5aa6`  
Scope: read-only inspection of all 42 local commits; no history rewrite or remote update was performed.

## Findings

- The packed object database is 101.87 MiB. All reachable unique blobs total 239,218,106 uncompressed bytes across 11,256 blob objects.
- Git history contains 10,454 unique deleted paths that are absent from the current source-only HEAD.
- The dominant deleted groups are:
  - `ai-webtoon/output/`: 7,977 generated Markdown/JSON/output paths.
  - `extensions/suno-lyric-downloader/node_modules/`: 2,317 dependency paths, including platform binaries and source maps.
  - former `ai_anime/`: 121 source, test, configuration, and input paths.
- At least 22 deleted paths use media or build-artifact extensions. Large reachable historical blobs include a 41.18 MiB WAV, a 28.28 MiB Visual Studio database, two historical revisions of a 12.75 MiB executable, a 10.13 MiB dependency executable, a 9.06 MiB native Node module, an MP3, reference/input images, and other build files.
- Environment-path review found four `.env.example` files and no path named plain `.env`. Historical log paths were three generated `imagevideo/output/logs/*.log` files.

## Secret-shape scan

All commits were scanned without printing matched values for common OpenAI, Google, GitHub, Slack, and private-key shapes.

- An initial unbounded `sk-` expression reported four matches in two deleted `node_modules/lightningcss` declaration files.
- Re-running with a token boundary reported zero OpenAI-key-shaped matches.
- Google, GitHub, Slack, and PEM private-key patterns reported zero matches in the completed scan.

This is a targeted pattern scan, not proof that history contains no sensitive or private data. It does show that the known removed `.env` paths were examples and that no common live-key form was found.

## Release decision

**HISTORY REWRITE RECOMMENDED BEFORE PUBLIC RELEASE.** The reason is distribution scope and provenance, not a confirmed credential leak: the source-only policy is contradicted by reachable historical media, executables, generated outputs, and `node_modules`. Their rights and intended public availability are not established.

GitHub documents that history rewriting changes commit identities, requires a force push, affects collaborators and pull requests, and cannot clean other clones or forks. The official process uses `git-filter-repo`, followed by verification, coordinated remote replacement, and collaborator cleanup: <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository>.

`git-filter-repo` is not installed on this machine. Its official project documents installation and analysis procedures: <https://github.com/newren/git-filter-repo>.

## HOLD conditions before rewriting

1. Confirm the remote repository visibility, collaborators, forks, open pull requests, protected branches, and whether any old commit IDs must remain referenced elsewhere.
2. Make a recoverable mirror backup outside the working clone and record all current refs.
3. Define the removal set from path rules, not a hand-picked list: generated output directories, `node_modules`, media, executables, and build-state files.
4. Run the rewrite in a disposable fresh mirror clone, then repeat the source-only, license, secret-shape, test, and object-size checks before touching the remote.
5. Obtain explicit approval for force-pushing rewritten refs. Coordinate all other clones so old history is not merged back.

Until these conditions are met, keep the current local and remote history unchanged.

## Disposable-mirror dry run

On 2026-09-21, `git-filter-repo` 2.47.0 was run only against a disposable local mirror. Neither the working repository nor GitHub was updated.

- Removal rules covered `ai-webtoon/output/`, `extensions/suno-lyric-downloader/node_modules/`, media extensions, and executable/build-state extensions. With `core.quotePath=false`, they selected 10,315 historical paths and zero paths at the current HEAD. Disabling path quoting is required when counting or matching the non-ASCII output paths.
- The rewritten history contains zero paths matching those rules. Reachable commits changed from 42 to 41 because one commit became empty.
- Packed size fell from 101.87 MiB to 1.82 MiB. The rewritten HEAD commit is `8ddcfb5`, while its tree remains `38533a2`, exactly matching the original `31c5aa6` HEAD tree.
- The bounded common-secret scan still found zero matching files.
- All 11 registered subproject suites passed in a temporary checkout: 363 tests total.
- The original repository remained at `31c5aa6`, clean, and 1 commit ahead of `origin/main`; its object database remained unchanged.

Dry-run result: **PASS**, but remote replacement remains **HOLD**. Before any force push, complete conditions 1, 2, and 5 above and preserve the exact removal rules and verification evidence from this run.

## Remote state

The unauthenticated GitHub API was checked on 2026-09-21. The repository is already public, uses `main` as its default branch, has one fork, and has one open pull request. Collaborator and branch-protection endpoints returned HTTP 401 without authenticated repository access, so those controls remain unverified. Because a public fork already exists, rewriting the origin cannot remove the old objects from that fork; coordinate with its owner or treat the old history as permanently distributed.

## Recovery backup

A complete pre-rewrite bundle, `ai_test-history-backup-20260921.bundle`, was created outside the repository on 2026-09-21. `git bundle verify` confirmed four refs and complete history; its size is 108,734,717 bytes and SHA-256 is `4BA60509232A0A285DBA1397E75D5D0DECA3ECFCC61C0A1EA6116390330440F8`. A separate restore-check clone passed `git fsck --full --strict` and reproduced HEAD `31c5aa6` with tree `38533a2`. HOLD condition 2 is satisfied.

## Push readiness

The completed MIT/source-boundary commit was pushed normally, moving remote `main` from `a7b2bfa` to `31c5aa6`. An authenticated `git push --dry-run --force-with-lease` then accepted the exact proposed rewrite from `31c5aa6` to `8ddcfb5`. The real force push was not performed: safety review requires explicit approval for rewriting the public default branch after acknowledging the existing fork, open pull request, and unverified authenticated protection settings.
