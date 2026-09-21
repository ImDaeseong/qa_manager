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
