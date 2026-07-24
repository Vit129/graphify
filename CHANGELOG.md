# Changelog

All notable changes to graphify are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and graphify follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [0.20.0] - 2026-07-24

### Added
- Index Dockerfile/Kustomize/K8s manifests, link fetch() calls to GAS handlers ([#18](https://github.com/Vit129/graphify/pull/18)) ([`e256907`](https://github.com/Vit129/graphify/commit/e2569072be96c48c790e011baa8a95e17b254d71))

## [0.19.0] - 2026-07-19

### Added
- Index JS/TS content-data arrays (lesson/course/quiz entries) ([#17](https://github.com/Vit129/graphify/pull/17)) ([`a841439`](https://github.com/Vit129/graphify/commit/a841439d37f6fd88ecff80ac658f03bcf5b645a1))

### Fixed
- Prefix-match bare --relation filters against parameterized labels ([#16](https://github.com/Vit129/graphify/pull/16)) ([`858c83c`](https://github.com/Vit129/graphify/commit/858c83c2921f70a2ddf2323de5238fe0c61bf599))

## [0.18.0] - 2026-07-19

### Added
- Add Calls view lens to graph.html, code symbols only ([#12](https://github.com/Vit129/graphify/pull/12)) ([`e95104b`](https://github.com/Vit129/graphify/commit/e95104b32967583038e6d5afbc5e8889e30a4667))

### Documentation
- Design PageRank-style symbol/file ranking (P17 item 2) ([#15](https://github.com/Vit129/graphify/pull/15)) ([`9cb83e0`](https://github.com/Vit129/graphify/commit/9cb83e00bc5c51ef54d21ec5563df20e049e218f))

### Fixed
- Decouple test_git_update_check.py from the real CURRENT_VERSION ([`44cc0c4`](https://github.com/Vit129/graphify/commit/44cc0c4dff32781bf2e0d304e5310395b7334597))

## [0.17.0] - 2026-07-18

### Added
- Add File/Dependencies view lenses to graph.html, alongside Community ([`61e8a32`](https://github.com/Vit129/graphify/commit/61e8a32a4c824f4956a43d7a0ce01e1cb526104f))
- Warn on stale graph.json at query time, add diff command ([#10](https://github.com/Vit129/graphify/pull/10)) ([`7c9f93e`](https://github.com/Vit129/graphify/commit/7c9f93ead602f1a84e80beb695241a1aa0ae4a88))
- Self-update check for editable git-clone checkouts ([#11](https://github.com/Vit129/graphify/pull/11)) ([`a7d09b2`](https://github.com/Vit129/graphify/commit/a7d09b2cb7fb9243e5550f2f539abf4c198c98ab))

### Documentation
- Rewrite README as an independent fork, fix PyPI-vs-source install mismatch ([`9d5b7c7`](https://github.com/Vit129/graphify/commit/9d5b7c7982864dd9298a5744f9f2481b3a3483ea))
- Add verified fork-vs-upstream comparison audit (2026-07-05) ([`e2902de`](https://github.com/Vit129/graphify/commit/e2902dee489c5213b03c6d1a561b3dee4f881e55))
- Correct provenance claim — shared code is adopted from upstream, not convergent ([`846942d`](https://github.com/Vit129/graphify/commit/846942d8ba2f994b4754372ef1079b0307046cf8))
- Rewrite "What's different from upstream" with verified findings ([`aa0e81c`](https://github.com/Vit129/graphify/commit/aa0e81c4b6b046805fa6e7e0d52510596e652140))
- Complete the upstream audit with full file-by-file diff + verified fix checklist ([`788c4b9`](https://github.com/Vit129/graphify/commit/788c4b9763c5323eb1175daea249d9ca32a61974))
- Record the 3 shipped fixes in CHANGELOG and mark them resolved in the audit ([`9c4cf4e`](https://github.com/Vit129/graphify/commit/9c4cf4ea024c08a873d7f06469276feb16dfd7b6))
- Document the search/query algorithms in how-it-works.md ([`748b9b4`](https://github.com/Vit129/graphify/commit/748b9b463039a816fef817837e8352474c223e0b))
- Extend the upstream audit to the whole repo, not just graphify/*.py ([`f9dd661`](https://github.com/Vit129/graphify/commit/f9dd661ec09c3288fea746ffd95da5bbdf553d94))
- Rewrite "What's different from upstream" with the full, current picture ([`be3f5a2`](https://github.com/Vit129/graphify/commit/be3f5a2e874c83a9f373d3a278eb2cae19007241))
- Fix confusing "personal/team fork" wording in README disclaimer ([#5](https://github.com/Vit129/graphify/pull/5)) ([`9aa219c`](https://github.com/Vit129/graphify/commit/9aa219ce953d966274976a5a988a0adb36b61286))
- Scrub upstream business branding from all 30 README translations ([#6](https://github.com/Vit129/graphify/pull/6)) ([`13fda48`](https://github.com/Vit129/graphify/commit/13fda48dd8928756d33417690e35b97b93e5bc78))
- Caveman-compress CLAUDE.md to cut input tokens ([`2c9d600`](https://github.com/Vit129/graphify/commit/2c9d6004af6390cd0cc4d32dce5cce0a6c873a8e))
- Add License section to README ([`d006739`](https://github.com/Vit129/graphify/commit/d006739a86129ce3bbc54a4ce7a29a50967dcebb))

### Fixed
- Symlink-containment guard + two JS/TS cross-file false-edge bugs ([`d96143d`](https://github.com/Vit129/graphify/commit/d96143d3f8a6caa2741a87b8f41f82841f3c3dcc))
- Resolve recv.Method() by receiver's declared type, not bare-name match ([#1609](https://github.com/Vit129/graphify/pull/1609)) ([`2c8ed55`](https://github.com/Vit129/graphify/commit/2c8ed55014decb7549a780110c83a0d59dbb0fe4))
- --no-viz didn't remove a stale graph.html on update/re-extract ([`f12f62e`](https://github.com/Vit129/graphify/commit/f12f62eea6d82f7c7c304c5b28b0ad8c000377df))
- Stop self-update check from defaulting to installing upstream's package ([#7](https://github.com/Vit129/graphify/pull/7)) ([`ae4f2bc`](https://github.com/Vit129/graphify/commit/ae4f2bc0545917fe2db0cb1002a471ca8986f68d))
- GRAPHIFY_NO_LLM no longer aborts extract with a false all-chunks-failed error ([#8](https://github.com/Vit129/graphify/pull/8)) ([`9259df9`](https://github.com/Vit129/graphify/commit/9259df927607c110d886b137e3b54831fedfb835))
- Close symlink-containment gap in LLM extraction path ([#9](https://github.com/Vit129/graphify/pull/9)) ([`0f9c9e5`](https://github.com/Vit129/graphify/commit/0f9c9e5d443856963f00f5355ddb910095378fbc))
- Resolve qualified cross-field names; feat(extract): index inline HTML <script> functions ([#13](https://github.com/Vit129/graphify/pull/13)) ([`ef121b0`](https://github.com/Vit129/graphify/commit/ef121b0ff87b519e292832e84914f8289aa2d5e1))

## [0.16.0] - 2026-07-04

### Added
- Gently down-weight doc/prose nodes on seed near-ties ([`d96706d`](https://github.com/Vit129/graphify/commit/d96706d2b37db49bac95748b8733f9605bb698fe))
- Path scoping filter, degree-weighted hub avoidance ([`91d1de6`](https://github.com/Vit129/graphify/commit/91d1de632b22aa8c3abde3b64f8d66ccf6ee2c2e))
- Language-agnostic degree-percentile hub exclusion ([`ff9c21d`](https://github.com/Vit129/graphify/commit/ff9c21d0e01a20aea4f37f35c4ef7100233534b0))
- Source-path scoping flags for path/explain to disambiguate duplicate labels ([`c57161e`](https://github.com/Vit129/graphify/commit/c57161e0473af04968ac215108a1da225abe0185))
- Opt-in cross-file value-coupling edges for config-as-code YAML ([`b52f98b`](https://github.com/Vit129/graphify/commit/b52f98b22b14407c49972e6e82eb20faa37a2912))

### Documentation
- Wire save-result/reflect feedback loop into the recommended workflow ([`4dfb54b`](https://github.com/Vit129/graphify/commit/4dfb54b56cf011773803d58d6400e0323d7e3d71))
- P15 value-coupling + P16 qualified resolution task plans ([`ab960db`](https://github.com/Vit129/graphify/commit/ab960dbf5df20ead01b7a35258fd563dcc5928c1))
- Record P16 Phase 2 and affected --include-contains as rejected ([`23160b1`](https://github.com/Vit129/graphify/commit/23160b17999e30afb5a919781de7ed3e4d1391a8))
- Add CLAUDE.md for graphify's own repo, mirroring AGENTS.md/GEMINI.md ([`ab2f921`](https://github.com/Vit129/graphify/commit/ab2f921687f43d92d1af6a5e29a189fb7b6f5ff7))

### Fixed
- Path candidate retry, backup-file self-ingestion, explain docs ([`e623a6f`](https://github.com/Vit129/graphify/commit/e623a6f3f1c06b997bf1c47c50bfa6b072aace38))
- Warn on ambiguous label match in explain/get_neighbors/blast_radius ([`bdaf9c5`](https://github.com/Vit129/graphify/commit/bdaf9c52abea31cd6f391c6914c19f2a4e92e8b7))
- Close remaining MCP-only ambiguity gaps in get_node/shortest_path ([`e4f3cf3`](https://github.com/Vit129/graphify/commit/e4f3cf353e5c436d873678f314982ce74f9f76fa))
- Value_coupling dropped silently on the real graphify update path ([`d2b6aa4`](https://github.com/Vit129/graphify/commit/d2b6aa41eb27a7e530228c1e8a52f423ca65ebd0))

## [0.15.0] - 2026-07-03

### Added
- Per-project config file + native update --all batch command ([`9196c08`](https://github.com/Vit129/graphify/commit/9196c0854a43ae593199c7e5660d1cf6bdd9b20c))
- Explain --context filter, cross-language primitive god-node noise, documents_bug_in relation ([`1043cae`](https://github.com/Vit129/graphify/commit/1043cae5951df656706110aa391fba845d89964c))
- Query relevance-ranking, cross-cutting god-nodes, concept-node anchoring, local embedding fallback ([`0e7312f`](https://github.com/Vit129/graphify/commit/0e7312f43ef588cc0d6af6ea1ec7d6e0cef3a71a))

### Changed
- Move extract_apex to extractors/apex.py (verbatim) ([`657be98`](https://github.com/Vit129/graphify/commit/657be98cc0c5aa48af3fe3f9d8ac3dd7af8d2070))

### Documentation
- Record recent architectural decisions ([`95e2b93`](https://github.com/Vit129/graphify/commit/95e2b93e006c94dd1685486fa7d9373f03465789))
- Note 0.15.0 release changes ([`25cbbb0`](https://github.com/Vit129/graphify/commit/25cbbb009f3d194dde50886b0684752edb624c0d))

### Fixed
- Exclude import/module anchor nodes from god-node ranking ([`ec9e0e7`](https://github.com/Vit129/graphify/commit/ec9e0e7ae53bb2e0ab367f23093576427816a189))
- Filter package.json boilerplate keys + own generated reports from extraction ([`1f1c49b`](https://github.com/Vit129/graphify/commit/1f1c49bf136ed60b92443f3c7b5d6a60afe72f0c))
- Add similarity floor to embedding fallback, fix CI-only test failure ([`3c04e3e`](https://github.com/Vit129/graphify/commit/3c04e3e8bdbd316afd0b56342bc616fe22e785a5))

## [0.14.0] - 2026-07-02

### Added
- Self-update check against PyPI ([`235a5bc`](https://github.com/Vit129/graphify/commit/235a5bc6a890f3e1d4080b9ef6ab52b1aeb48e83))
- Add lazy-loaded 3D force graph view option to HTML export ([`d79b6fb`](https://github.com/Vit129/graphify/commit/d79b6fb7bb1b7604a5612f69ca58f4ce12c61011))
- Implement Obsidian-like control panel, auto-open browser, and live reload ([`e4e4f9c`](https://github.com/Vit129/graphify/commit/e4e4f9cd69870bedad485745aaa45f29a28a859c))

## [0.9.5] - 2026-07-02

### Added
- Optional project_path for multi-project MCP serving ([`9e7fbcb`](https://github.com/Vit129/graphify/commit/9e7fbcbd6ea95c44d820af4f7fdbbd80b627a93b))

### Changed
- Eliminate multi-second foreground stalls before the detached launch ([`1256d65`](https://github.com/Vit129/graphify/commit/1256d65214adc6cb07889f2f9e06fd1d695c7aac))

### Documentation
- Note 7-language type-reference/inheritance fixes (#1587-#1593) ([`f4a7994`](https://github.com/Vit129/graphify/commit/f4a799492670b3bf9865d4cbd6055407a5192d8e))
- Point LinkedIn badge to Graphify Labs company page ([`5190a4e`](https://github.com/Vit129/graphify/commit/5190a4ede9eee0742dbd85b8720ce2d8bc9a164a))

### Fixed
- Emit field type references for var declarations ([`67b4525`](https://github.com/Vit129/graphify/commit/67b4525f32f7f56de8e2202439e176a3f4ee3b69))
- Emit inherits/implements edges for class base types ([`a129ff2`](https://github.com/Vit129/graphify/commit/a129ff2cd60b423debb9351f793a0551faa9dc71))
- Emit implements edge for protocol-to-protocol adoption ([`cd3a376`](https://github.com/Vit129/graphify/commit/cd3a376030d0dcfdccdac05eac0f4d5c34308fb6))
- Emit type references for promoted constructor properties ([`51f805e`](https://github.com/Vit129/graphify/commit/51f805e9537d01d2bc31b83d3c3fe3f76640b35f))
- Emit type references for properties ([`bb5e519`](https://github.com/Vit129/graphify/commit/bb5e5192df14a522cf0c8ec72ca1bd5452af29da))
- Emit generic_arg references for base-class template arguments ([`21bcb43`](https://github.com/Vit129/graphify/commit/21bcb436b58c5922e437e6abbd3dfbe95a14ad4b))
- Emit references for enum associated-value types ([`ad70152`](https://github.com/Vit129/graphify/commit/ad7015262b8876980c819ed20cd9dabe51facc8b))
- Allow python@ shebang in skill detection ([#1586](https://github.com/Vit129/graphify/pull/1586)) + merge-graphs mixed types ([#1606](https://github.com/Vit129/graphify/pull/1606)) ([`b70a6d7`](https://github.com/Vit129/graphify/commit/b70a6d7126793ae77352cc9c2a4ec0fb69b977c4))
- Resolve calls on a singleton cached into a local var ([#1604](https://github.com/Vit129/graphify/pull/1604)) ([`44c0a5e`](https://github.com/Vit129/graphify/commit/44c0a5e33c7011813dcebf1a8850c1c6005bf500))
- Drop question/filler stopwords from query terms ([`6e97088`](https://github.com/Vit129/graphify/commit/6e9708849351aae91d6300a50385d3ff173aebd7))

## [0.11.1] - 2026-07-02

### Added
- BM25 ranking, typo/fuzzy fallback, and 5 new language extractors ([`2586f03`](https://github.com/Vit129/graphify/commit/2586f036cdd8db9c3082e6a0b6c6062f6312498c))

### Fixed
- Case-sensitive cross-file resolution in case-sensitive languages ([#1581](https://github.com/Vit129/graphify/pull/1581)) ([`784e9c8`](https://github.com/Vit129/graphify/commit/784e9c833ef13ca0ebfd442875c9ec60de157d4e))
- CODE_EXTENSIONS never updated for 0.11.0's new languages ([`cb6ac79`](https://github.com/Vit129/graphify/commit/cb6ac79c7c01f5724bcd045c624cd99132f34778))

## [0.10.0] - 2026-07-01

### Added
- Add opt-in PageRank ranking to god_nodes() ([`136fb84`](https://github.com/Vit129/graphify/commit/136fb84667389485d041c3e3ad29b048d92b6d40))
- Pre-flight notice + GRAPHIFY_NO_LLM opt-out for extraction ([`ece9294`](https://github.com/Vit129/graphify/commit/ece92945ddfd403e82f7d682717ce9d8e5796b68))
- Wire pagerank god-node ranking into graphify update ([`98590e1`](https://github.com/Vit129/graphify/commit/98590e188f47461995aa945ca0315237d122b7ff))
- Remove Obsidian vault/canvas export ([`d47d970`](https://github.com/Vit129/graphify/commit/d47d970511daa231184a86e9fe904eee5d20ce95)) ⚠️ BREAKING
- Generate GRAPH_SUMMARY.md natively, drop external bash script ([`80a5de8`](https://github.com/Vit129/graphify/commit/80a5de8d8beb09bf3860f477c4ebf318d8beb92f))
- Flag possibly-unreachable functions in Knowledge Gaps ([`c0a6386`](https://github.com/Vit129/graphify/commit/c0a638693fd7648838f8ead4adcc306edbafee60))
- Add blast_radius MCP tool for single-repo impact analysis ([`60e7443`](https://github.com/Vit129/graphify/commit/60e74432f9fa04eae6c971cef85590725ece820c))

### Documentation
- Note elixir/fortran/rust extractor fixes (#1577, #1578, #1579) ([`7e24c3b`](https://github.com/Vit129/graphify/commit/7e24c3b7e4910ce43ea5bf7d288a0a8732594c8b))
- Note julia/rust-tuple-struct/systemverilog fixes (#1580, #1582, #1583) ([`532a20e`](https://github.com/Vit129/graphify/commit/532a20e77526d531e5c6a9abf997b55c3cfc5cc7))

### Fixed
- Cross-file indirect_call survives id relativization (0.9.4 regression) ([`e34e27c`](https://github.com/Vit129/graphify/commit/e34e27c24cce8ed20333d36fa28cbc095e33c8d0))
- Detect stale community labels on cluster-only re-cluster ([`8127ff9`](https://github.com/Vit129/graphify/commit/8127ff9a9c153bfd8c90090ca6cf74adc4b553c9))
- Expand multi-alias brace form into per-module imports edges ([`f2ea6a6`](https://github.com/Vit129/graphify/commit/f2ea6a60870b0350722af5f7aa388eabb941f8fe))
- Emit calls edges for function invocations ([`b8f41c7`](https://github.com/Vit129/graphify/commit/b8f41c77eb206a096f30ee50082cd0fa0f6b217b))
- Emit references edges for enum variant field types ([`674184d`](https://github.com/Vit129/graphify/commit/674184d462539f09f35cf53b6926451ef0ae2516))
- Emit imports for qualified, relative, and scoped-selected forms ([`984a6a8`](https://github.com/Vit129/graphify/commit/984a6a8f0ad0c8630d81e18babc75976b7da0387))
- Emit field type references for tuple structs ([`7eb847b`](https://github.com/Vit129/graphify/commit/7eb847bcf7a63a97de638023ff6b4f4e48897bba))
- Emit field references for qualified class properties ([`297075c`](https://github.com/Vit129/graphify/commit/297075c3f39a2085537e7bfddfba2b73e410ce7a))
- Prune backup snapshots older than GRAPHIFY_BACKUP_KEEP_DAYS ([`12fda9b`](https://github.com/Vit129/graphify/commit/12fda9b92a9df83511bed1c2e49e69eaf3e7c204))
- Stop community-hub wikilink targets collapsing to double spaces ([`df12048`](https://github.com/Vit129/graphify/commit/df1204847e9fafd587a95010886fa8bd54a5a375))
- Diversify BFS seeds across communities for multi-term queries ([`dff02a5`](https://github.com/Vit129/graphify/commit/dff02a5a5f33f7350ed781c2be6c3d1bd4fdf30e))
- Rank multi-term seed diversification by term coverage ([`d615849`](https://github.com/Vit129/graphify/commit/d6158498463ea88c5080e4adc3164ededa312b9c))
- Weight multi-term seed coverage by inverse document frequency ([`810adaf`](https://github.com/Vit129/graphify/commit/810adaff031ff2cc14809c0f6a03948cbe415b83))

## [0.9.4] - 2026-07-01

### Added
- Capture indirect dispatch as indirect_call edges ([#1565](https://github.com/Vit129/graphify/pull/1565)) ([`19e7a31`](https://github.com/Vit129/graphify/commit/19e7a31343232a1132fcbe843c1b715be8f90995))
- Resolve cross-file indirect dispatch as indirect_call ([`cf747ab`](https://github.com/Vit129/graphify/commit/cf747abeafb5dadf31fedeb7257202699eb7fef6))
- Capture dispatch tables as indirect_call edges ([#1566](https://github.com/Vit129/graphify/pull/1566)) ([`8288829`](https://github.com/Vit129/graphify/commit/8288829613cab2364b29d7ea89db53ef35d430c3))
- Capture indirect dispatch for JS/TS (#1566 slice 5) ([`6dc1cb0`](https://github.com/Vit129/graphify/commit/6dc1cb0dd7bf521bcf2dd21369691b8048423f84))
- Capture assignment/return indirect_call edges (#1566 slice 2) ([`311e63a`](https://github.com/Vit129/graphify/commit/311e63a7fcd32ef3143b1f1b8b1cbb79cbba834b))
- Capture getattr(obj, "name") indirect_call edges (#1566 slice 3) ([`8fdbf50`](https://github.com/Vit129/graphify/commit/8fdbf501972dc34b0d097b096b9bf87d2938e460))
- Deterministic hub community labels (readable without an LLM) ([`1aab291`](https://github.com/Vit129/graphify/commit/1aab291caf1e792753b79e26587012c71ae3d45b))

### Documentation
- Note assignment/return indirect_call ([#1569](https://github.com/Vit129/graphify/pull/1569)) ([`69b3997`](https://github.com/Vit129/graphify/commit/69b3997386ec94dedf01efe350297bdf7061befb))
- Note getattr slice 3 ([#1575](https://github.com/Vit129/graphify/pull/1575)) and hub labels ([#1576](https://github.com/Vit129/graphify/pull/1576)) ([`20547c4`](https://github.com/Vit129/graphify/commit/20547c47675b0043e03eb69f878851a1ce124e32))
- Correct deduplicate_by_label docstring — dormant, not auto-called ([`93e8e44`](https://github.com/Vit129/graphify/commit/93e8e445ddc51e21ebb63d52f018c9af963efabd))

### Fixed
- Make skill-version warning direction-aware ([#1568](https://github.com/Vit129/graphify/pull/1568)) ([`47033c8`](https://github.com/Vit129/graphify/commit/47033c8b75fede4b14f360591fb86c141b5eeabf))
- Preserve hyperedges + harden prune root in build_merge (#1574, #1571) ([`4f40967`](https://github.com/Vit129/graphify/commit/4f40967e8de8109f31b12151ec87368522b43ee8))
- Harden graph JSON loading against corruption ([#1536](https://github.com/Vit129/graphify/pull/1536)) ([`4a8d6ba`](https://github.com/Vit129/graphify/commit/4a8d6bad9705871607a7be209647eefe585c584b))
- Warn on cross-chunk node ID collision to surface silent data loss ([#1504](https://github.com/Vit129/graphify/pull/1504)) ([`5320aa8`](https://github.com/Vit129/graphify/commit/5320aa8eb1e68069314dbf48627a88148d5565d6))
- Limit Windows hook rebuild workers ([`879c058`](https://github.com/Vit129/graphify/commit/879c05894db669ddd48da9a132c2960bc742871a))
- Emit inherits edge for class superclass ([`a19b9e9`](https://github.com/Vit129/graphify/commit/a19b9e90ec174efed8114512c001a6ec9da6dcda))
- Emit inherits/implements edges for extends/implements ([`64a6093`](https://github.com/Vit129/graphify/commit/64a6093376bab300860bcc4a66d7d6095f317f90))
- Relativize source_file across a symlinked root (#1571 follow-up) ([`de7d362`](https://github.com/Vit129/graphify/commit/de7d362537da7a8e63ceb731472136b7dc22dc1b))

## [0.9.3] - 2026-06-30

### Added
- Resolve TypeScript wildcard path aliases ([#1544](https://github.com/Vit129/graphify/pull/1544)) ([`5746964`](https://github.com/Vit129/graphify/commit/57469641cd6930a464dffd1e7f6360c34d8cd508))
- Resolve namespace re-export bindings (export * as ns from) ([#1552](https://github.com/Vit129/graphify/pull/1552)) ([`c8c604d`](https://github.com/Vit129/graphify/commit/c8c604d08cd717d84eeb9da1fcb6e50b49f35748))
- Resolve this.field.method() calls via constructor-injection types ([#1316](https://github.com/Vit129/graphify/pull/1316)) ([`1801da0`](https://github.com/Vit129/graphify/commit/1801da0634e728533811ddcb648b38d5d4a900eb))
- Dot-syntax property accesses and @selector() call edges (#1475, #1543) ([`0792b41`](https://github.com/Vit129/graphify/commit/0792b419fcdff4db4f02c065da753bf4dc2c8591))
- Work-memory overlay — surface learned verdicts as a graph sidecar ([#1441](https://github.com/Vit129/graphify/pull/1441)) ([`5779767`](https://github.com/Vit129/graphify/commit/5779767fd31b26de9d3045c7b564f7306b08668a))
- Cross-file member-call resolution for C++ and ObjC (#1547, #1556) ([`49252d3`](https://github.com/Vit129/graphify/commit/49252d3cb754e7d6e0241483ba732c4bfa7989e1))
- Namespace-aware cross-file type resolution ([#1562](https://github.com/Vit129/graphify/pull/1562)) ([`b9d8067`](https://github.com/Vit129/graphify/commit/b9d8067d0a658ac986b058cb19c35b4ba755e5fd))

### Documentation
- README work-memory overlay note + Unreleased changelog ([`2cdc212`](https://github.com/Vit129/graphify/commit/2cdc212b43e5043b144d579518c0036917d81747))

### Fixed
- Work-memory staleness false-positive on relative source paths ([`00e00a0`](https://github.com/Vit129/graphify/commit/00e00a0b5f7cbf80a123d878e6e3c40c78c680e6))
- Layout-ordered source resolution for overlay staleness ([#1558](https://github.com/Vit129/graphify/pull/1558)) ([`c865a3c`](https://github.com/Vit129/graphify/commit/c865a3c9b0feea421b391b28340de153ec3b9269))
- Accept members/node_ids alias keys for the member list ([#1561](https://github.com/Vit129/graphify/pull/1561)) ([`bd885cc`](https://github.com/Vit129/graphify/commit/bd885cc97dfafb8ba8a940b434324e57ce827827))
- Test mocks no longer erase the real cross-file call graph ([#1553](https://github.com/Vit129/graphify/pull/1553)) ([`bee3849`](https://github.com/Vit129/graphify/commit/bee3849810fb10853ac736f772cc15f8efaf580e))
- Merge header/impl class fragmentation + C++/ObjC header routing (#1556, #1547) ([`3bc3fee`](https://github.com/Vit129/graphify/commit/3bc3feed545d635a8eec0472109966b05a955636))

## [0.9.2] - 2026-06-29

### Added
- Type-aware member-call resolution via a resolver framework ([#1499](https://github.com/Vit129/graphify/pull/1499)) ([`86ecb76`](https://github.com/Vit129/graphify/commit/86ecb769b694ecd7485eb8143a75966f748cbb8f))
- Resolve workspace subpath exports via package.json exports map ([#1308](https://github.com/Vit129/graphify/pull/1308)) ([`e8dabad`](https://github.com/Vit129/graphify/commit/e8dabadeb070c822f1e1794cc09e7573678706c0))

### Documentation
- Add Discord badge to README ([`1990612`](https://github.com/Vit129/graphify/commit/199061207f6648f116fd6dbb0b2214502c55d90a))
- Add Unreleased changelog section for today's fixes ([`1d8d278`](https://github.com/Vit129/graphify/commit/1d8d278f9e1aae1dc3fc42600e62f702c4e76693))

### Fixed
- Enforce API timeout in the secondary LLM dispatch path ([#1442](https://github.com/Vit129/graphify/pull/1442)) ([`4e4935a`](https://github.com/Vit129/graphify/commit/4e4935a64a3f395a30d5f19be31700dbdd829835))
- GraphML null-attr coercion + save-result --answer-file ([#1502](https://github.com/Vit129/graphify/pull/1502)) ([`407a7f1`](https://github.com/Vit129/graphify/commit/407a7f142de1ed68ab9c92d8d9cc3dc0943734c8))
- Host-generic /graphify install guidance ([#1530](https://github.com/Vit129/graphify/pull/1530)) ([`e3e4198`](https://github.com/Vit129/graphify/commit/e3e4198038088820d4b560052b63d989917d59ca))
- Resolve alias/workspace import edges + honor tsconfig paths fallbacks (#1529, #1531) ([`2133539`](https://github.com/Vit129/graphify/commit/21335399306ee0fc9880640e860fa92a4f625ecb))
- Prune orphan semantic-cache entries at end of extract ([#1527](https://github.com/Vit129/graphify/pull/1527)) ([`7a9cda2`](https://github.com/Vit129/graphify/commit/7a9cda2452220327b8889f8a16485c37ced0eece))
- NS_ASSUME_NONNULL parse failure, dangling .m imports, alloc/init refs ([#1475](https://github.com/Vit129/graphify/pull/1475)) ([`1652dad`](https://github.com/Vit129/graphify/commit/1652dadd60809e9d8505bdcc39d949acf031e664))
- Type-qualified static calls resolve as EXTRACTED, not INFERRED ([#1533](https://github.com/Vit129/graphify/pull/1533)) ([`51fc00a`](https://github.com/Vit129/graphify/commit/51fc00a30ff5161e392037ff634fe394d315d14b))

## [0.9.1] - 2026-06-28

### Documentation
- Document the --timing flag in the extract examples ([#1490](https://github.com/Vit129/graphify/pull/1490)) ([`94e5baf`](https://github.com/Vit129/graphify/commit/94e5bafc8983b4c6db7761c9f51857dcc6dfbad5))
- Add #1515 and #1518 entries to Unreleased ([`67d8c53`](https://github.com/Vit129/graphify/commit/67d8c53ccc6ede7f3d14dbbe8e90a0bad8a7966e))
- Add #1521, #1522, #1519 entries ([`22a5afb`](https://github.com/Vit129/graphify/commit/22a5afb251dbdedc8f414d1aa6fb557d1d844f39))
- Document GRAPHIFY_MAX_RETRIES env var ([#1523](https://github.com/Vit129/graphify/pull/1523)) ([`0ca73bd`](https://github.com/Vit129/graphify/commit/0ca73bd00bd022d0d6a0b9530dd64d30243fcf8c))

### Fixed
- Drop internal origin_file so it stops leaking into graph.json ([#1516](https://github.com/Vit129/graphify/pull/1516)) ([`afa4ade`](https://github.com/Vit129/graphify/commit/afa4aded2e77af6c3591094132a7f29dedb411dc))
- Add origin_file to cross-file stubs in the six dedicated extractors ([#1515](https://github.com/Vit129/graphify/pull/1515)) ([`d177f04`](https://github.com/Vit129/graphify/commit/d177f04270df1625cdd4c46db1334ccefcc1951b))
- Skip Java type-parameter references ([#1518](https://github.com/Vit129/graphify/pull/1518)) ([`8b9a998`](https://github.com/Vit129/graphify/commit/8b9a99828abd8388819650590e033c175b93851c))
- Prune edges owned by a re-extracted file ([#1521](https://github.com/Vit129/graphify/pull/1521)) ([`0080d8a`](https://github.com/Vit129/graphify/commit/0080d8ac43bf5db24c5cc659ed2e873f7b314b33))
- Salt residual separator-collision node IDs injectively ([#1522](https://github.com/Vit129/graphify/pull/1522)) ([`35fb437`](https://github.com/Vit129/graphify/commit/35fb43736555b0e8bf843931e12c8bdaf0483e08))
- Emit Java record component references ([#1519](https://github.com/Vit129/graphify/pull/1519)) ([`981e2b9`](https://github.com/Vit129/graphify/commit/981e2b93cf48b57faa78f9dec33c56c4c547b71a))
- Retry rate-limited (429) requests instead of dropping the chunk ([#1523](https://github.com/Vit129/graphify/pull/1523)) ([`64c1f21`](https://github.com/Vit129/graphify/commit/64c1f210704e8ba3c41a64efc3a53e24a97bfcda))

## [0.9.0] - 2026-06-28

### Added
- --timing flag for per-stage timings on extract and cluster-only ([#1490](https://github.com/Vit129/graphify/pull/1490)) ([`f7f89d7`](https://github.com/Vit129/graphify/commit/f7f89d7d844a53feae4a41530953eb735dd1755e))
- Warn on legacy-id graphs + harden re-key source_file contract ([#1504](https://github.com/Vit129/graphify/pull/1504)) ([`3999dbc`](https://github.com/Vit129/graphify/commit/3999dbc67e5cfbf88f73f03cfd43113616a781a3))

### Documentation
- Document --obsidian-dir and its existing-vault safety ([#1506](https://github.com/Vit129/graphify/pull/1506)) ([`7592244`](https://github.com/Vit129/graphify/commit/75922443866244d4bb6a266b8e085aa82b10dbe7))
- Clarify --force is needed to recover previously-collided nodes ([#1504](https://github.com/Vit129/graphify/pull/1504)) ([`388d1b6`](https://github.com/Vit129/graphify/commit/388d1b64dbd8fd0b55c5cc3b08b33ebc1866fe7d))

### Fixed
- Node IDs include the full repo-relative path (#1504, #1509) ([`b46634e`](https://github.com/Vit129/graphify/commit/b46634ef7aeb1668af68e10a1b0f658051bf5ac2))
- Legacy-id detector only inspects file-level nodes (no Go false-positive) ([`73710d3`](https://github.com/Vit129/graphify/commit/73710d33ce0986401f316cc1532cbaa33caed1f6))

## [0.8.51] - 2026-06-28

### Added
- Resolve C# cross-file type references + enum/struct/record ([#1466](https://github.com/Vit129/graphify/pull/1466)) ([`76b6eab`](https://github.com/Vit129/graphify/commit/76b6eabdb0e8d79d81c3095535f337bf2653cbda))

### Documentation
- Fix `graphify global add` example ([#1489](https://github.com/Vit129/graphify/pull/1489)) ([`1225677`](https://github.com/Vit129/graphify/commit/1225677b8ad19266c35e3f56a009233d169a4c80))
- Uv tool PATH setup + uvx --from graphifyy for macOS ([#1471](https://github.com/Vit129/graphify/pull/1471)) ([`11dc819`](https://github.com/Vit129/graphify/commit/11dc819c3f9cbaf8a3b8c6bb107af88cba359185))

### Fixed
- Go cross-file type refs emit sourceless stubs ([#1500](https://github.com/Vit129/graphify/pull/1500)) ([`36b76ce`](https://github.com/Vit129/graphify/commit/36b76ce8e0c3839ab0d88feff40a4697087e43d9))
- Disambiguate imported type stubs across files without blocking rewire ([#1462](https://github.com/Vit129/graphify/pull/1462)) ([`6509d0c`](https://github.com/Vit129/graphify/commit/6509d0ca6f12ed5e5fda6ad6f18c6598fc313daa))
- Resolve explain/affected when a source-file path matches multiple nodes ([#1503](https://github.com/Vit129/graphify/pull/1503)) ([`1b99496`](https://github.com/Vit129/graphify/commit/1b994965bb82c79cbdd4f16d121b3c4fd8479db2))
- Emit Java enum and annotation declarations as type nodes ([#1512](https://github.com/Vit129/graphify/pull/1512)) ([`940cb53`](https://github.com/Vit129/graphify/commit/940cb53f4d69bd42be9e499f4f3c3216825d5b62))
- Emit Java generic parent relationships ([#1510](https://github.com/Vit129/graphify/pull/1510)) ([`1f3f1c1`](https://github.com/Vit129/graphify/commit/1f3f1c1ca68f5dd15befbae247fc07552c592be4))
- Tolerate non-UTF8 claude-cli output on Windows GBK systems ([#1505](https://github.com/Vit129/graphify/pull/1505)) ([`0e8d92c`](https://github.com/Vit129/graphify/commit/0e8d92cf5fc8b87199d7df362590e53f2de0b151))
- Don't overwrite user notes or .obsidian config in an existing vault ([#1506](https://github.com/Vit129/graphify/pull/1506)) ([`8b177cb`](https://github.com/Vit129/graphify/commit/8b177cb33da3a9a41b20d34a315fd7cd9f6fe197))

## [0.8.50] - 2026-06-27

### Added
- Honor *_BASE_URL for kimi/gemini/deepseek backends ([#1458](https://github.com/Vit129/graphify/pull/1458)) ([`68dba89`](https://github.com/Vit129/graphify/commit/68dba89a999bf3ef21571da5f44557693a3459ab))
- WPF/XAML structural extraction with code-behind bridge ([#1460](https://github.com/Vit129/graphify/pull/1460)) ([`7dc5d96`](https://github.com/Vit129/graphify/commit/7dc5d968a3f07ec7df5714eb7b9eb46cd9ff938d))
- Link XAML views to ViewModels and extract binding references ([#1473](https://github.com/Vit129/graphify/pull/1473)) ([`905e0a7`](https://github.com/Vit129/graphify/commit/905e0a7a2e6a17e6e65d5906883c5689eac3635e))
- Index Metal (.metal) shader files ([#1480](https://github.com/Vit129/graphify/pull/1480)) ([`652ba42`](https://github.com/Vit129/graphify/commit/652ba42e61b63689aeac660a214d164fcfe10516))
- Add --missing-only flag for incremental community naming ([#1481](https://github.com/Vit129/graphify/pull/1481)) ([`a16b5bd`](https://github.com/Vit129/graphify/commit/a16b5bd151d227d7bc885c913389abe2cb1f0a34))

### Documentation
- Present 0.8.49 changes directly (drop internal packaging note) ([`e4ff54f`](https://github.com/Vit129/graphify/commit/e4ff54f4e06f86e5bc47476a7c1371410577943e))

### Fixed
- Case-fold filename dedup so case-only labels don't overwrite ([#1453](https://github.com/Vit129/graphify/pull/1453)) ([`5d63aad`](https://github.com/Vit129/graphify/commit/5d63aad596e00a97646f426e52115f72a929c968))
- Lay out canvas node cards in the box's sqrt(n)-column grid ([#1452](https://github.com/Vit129/graphify/pull/1452)) ([`7278e24`](https://github.com/Vit129/graphify/commit/7278e24d8ad70fa1f91f2ce4bb7a45813950f30c))
- State up front that no API key is required, with a non-subagent fallback ([#1461](https://github.com/Vit129/graphify/pull/1461)) ([`1e3270a`](https://github.com/Vit129/graphify/commit/1e3270a374498b446eb68c8f72a92d6ccf68a0ff))
- Match the real file extension in the Read|Glob hook ([#1463](https://github.com/Vit129/graphify/pull/1463)) ([`9b583a0`](https://github.com/Vit129/graphify/commit/9b583a0dd51061db2f459d4c53a5fc6731bbfbe5))
- Include analysis/labels sidecars in --if-stale freshness check ([#1470](https://github.com/Vit129/graphify/pull/1470)) ([`75a5e6d`](https://github.com/Vit129/graphify/commit/75a5e6d5ffc269d10b827df575f8957863fc5c7b))
- Parse .vue SFC <script> with the right grammar ([#1468](https://github.com/Vit129/graphify/pull/1468)) ([`349465b`](https://github.com/Vit129/graphify/commit/349465b8afb610f22cf660ad8c3f5f5d28435beb))
- Recover dropped Objective-C relationships ([#1475](https://github.com/Vit129/graphify/pull/1475)) ([`8994b55`](https://github.com/Vit129/graphify/commit/8994b5500c9ff1e4d2314cb78abfce56f524a215))
- Emit references for Java field types ([#1485](https://github.com/Vit129/graphify/pull/1485)) ([`31b3752`](https://github.com/Vit129/graphify/commit/31b3752902df70268f1dee2b5eef7f5ce37afec9))
- Emit references for Java type annotations ([#1487](https://github.com/Vit129/graphify/pull/1487)) ([`9b49bfd`](https://github.com/Vit129/graphify/commit/9b49bfd9eb0ada46022676a4f3da18e57f615446))
- Force non-streaming on OpenAI-compatible calls ([#1223](https://github.com/Vit129/graphify/pull/1223)) ([`ff47316`](https://github.com/Vit129/graphify/commit/ff47316b8aca38599e75e9c29d6174ddb60e1bb5))
- Portable relative markdown links so navigation works outside Obsidian ([#1444](https://github.com/Vit129/graphify/pull/1444)) ([`7a94f72`](https://github.com/Vit129/graphify/commit/7a94f72779f81cba47b6b362a8df275f2ad7845a))

## [0.8.49] - 2026-06-25

### Added
- --if-stale to skip redundant runs; agent uses it at session start ([`d193b62`](https://github.com/Vit129/graphify/commit/d193b6277de26538b031c28ecb102f85c9eb152d))
- Parallel community labeling via --max-concurrency / --batch-size ([#1390](https://github.com/Vit129/graphify/pull/1390)) ([`22a58ff`](https://github.com/Vit129/graphify/commit/22a58ffc20d75fb8eebe22f4ddde6922c857ee41))

### Changed
- Begin per-language extractor split ([#1212](https://github.com/Vit129/graphify/pull/1212)) ([`b3ab221`](https://github.com/Vit129/graphify/commit/b3ab2217626e4984430645448f6969947dc2ee78))

### Fixed
- Agent self-refreshes LESSONS.md so work-memory works without the hook ([`c06db05`](https://github.com/Vit129/graphify/commit/c06db053512d15a4f9262062f2e7c30dacaed920))
- Dedupe dead-ends and corrections by question ([`1a14e94`](https://github.com/Vit129/graphify/commit/1a14e94e53466a357c74bc35486d455f0d0afad7))
- Show community name in get_community MCP output ([#1448](https://github.com/Vit129/graphify/pull/1448)) ([`f9ded63`](https://github.com/Vit129/graphify/commit/f9ded6335069f156ce96cedb5f2b15f9a3f847d5))

## [0.8.47] - 2026-06-24

### Added
- Add cross-framework `agents` platform (+ `skills` alias) ([`ad6cb75`](https://github.com/Vit129/graphify/commit/ad6cb753c024d42e2de003545358c5c3d26c6414))
- Self-improving work-memory — save-result outcomes + graphify reflect ([#1441](https://github.com/Vit129/graphify/pull/1441)) ([`89dd00f`](https://github.com/Vit129/graphify/commit/89dd00f1404bf50355c2565627a910205fc32377))
- Zero-config work-memory adoption via skill + git hooks ([#1441](https://github.com/Vit129/graphify/pull/1441)) ([`6d9617a`](https://github.com/Vit129/graphify/commit/6d9617a44fd7701287bc663125d3938beed611c1))

### Documentation
- Add #1447 entry (non-hashable id/endpoint crash fix) ([`b448c16`](https://github.com/Vit129/graphify/commit/b448c16cbdfde363ff956c63765d47ef49c24da7))

### Fixed
- Resolve Python ClassName.method() qualified calls to class-method nodes ([#1446](https://github.com/Vit129/graphify/pull/1446)) ([`c390456`](https://github.com/Vit129/graphify/commit/c390456c6cab3aaa32a34c470153d299260baef7))
- File-aware shrink-guard so removed symbols prune without --force ([`533859d`](https://github.com/Vit129/graphify/commit/533859dc51976b9c050754c62d2a5fe6177bb6c3))

## [0.8.46] - 2026-06-23

### Changed
- Trigram candidate prefilter to cut O(N) query latency ([`53edd27`](https://github.com/Vit129/graphify/commit/53edd27e6aa5f49691a2acc5037cea4ec68c241d))

### Fixed
- Catch OSError when Cargo.toml is missing during --cargo introspection ([`aa06e10`](https://github.com/Vit129/graphify/commit/aa06e10fa5159aeb6c4417d1d188a6f42fcf0165))
- Strip backticks from plugin reminder to prevent silent command substitution ([#1413](https://github.com/Vit129/graphify/pull/1413)) ([`2323ce1`](https://github.com/Vit129/graphify/commit/2323ce1937447fe97c7793b7e0ac3a9f8cadab68))
- Resolve F821 undefined name 'nx' in prs.py ([`0b96b61`](https://github.com/Vit129/graphify/commit/0b96b616092edf8691a38fb987cd92fe5afc973e))
- Never emit punctuation-only Obsidian filenames (e.g. @.md) ([`30cc4c0`](https://github.com/Vit129/graphify/commit/30cc4c067010f094793237636a602d347c6016a4))

## [0.8.42] - 2026-06-18

### Fixed
- Pin extraction source_file + root the full build, prune deleted-only ([`5b98897`](https://github.com/Vit129/graphify/commit/5b988974ca6f2aa93c8923c07daea85d5ac3beda))

## [0.8.41] - 2026-06-17

### Added
- PowerShell .psd1 manifest parsing & Import-Module / dot-source edge emission ([#1331](https://github.com/Vit129/graphify/pull/1331)) ([#1341](https://github.com/Vit129/graphify/pull/1341)) ([`f117aac`](https://github.com/Vit129/graphify/commit/f117aaccc6a1446b8dff749a2f415e91ed136b7d))

### Fixed
- Replace re-extracted files instead of accumulating stale edges ([#1344](https://github.com/Vit129/graphify/pull/1344)) ([`fd463de`](https://github.com/Vit129/graphify/commit/fd463deb0318547b31aa9987329d39cd0ff4fae4))

## [0.8.40] - 2026-06-16

### Added
- Custom endpoints via OPENAI_BASE_URL/OPENAI_MODEL and ANTHROPIC_BASE_URL/ANTHROPIC_MODEL ([#1273](https://github.com/Vit129/graphify/pull/1273)) ([`61836ce`](https://github.com/Vit129/graphify/commit/61836ce0e8fa806ed8619dad35d7cb4bf2a0aedc))
- Extract JS/TS this.X=, exports.X=, prototype, class arrow fields, function expressions ([#1323](https://github.com/Vit129/graphify/pull/1323)) ([`09da529`](https://github.com/Vit129/graphify/commit/09da5294e4b783c860ef2d406d69701cfe9913db))

### Changed
- Convert _walk_js_tree from recursive generator to iterative ([`a7c6980`](https://github.com/Vit129/graphify/commit/a7c69808ac11f938e509d64348eb9413e869ab21))
- Parallelize save_manifest file hashing with ThreadPoolExecutor ([`0f6d46f`](https://github.com/Vit129/graphify/commit/0f6d46f8228e53f0cd0f364abff64238b7f2d936))

### Documentation
- Add RFC for file-level node summaries ([`1ad47ec`](https://github.com/Vit129/graphify/commit/1ad47ec05e1b7055c77686c0acf66523d02d096a))
- Detail proposed node summary contents ([`3e8afc9`](https://github.com/Vit129/graphify/commit/3e8afc9192283805df52f52cc07da85856815c14))
- Add --graph flag example to graphify-mcp usage ([#1304](https://github.com/Vit129/graphify/pull/1304)) ([`fd470fa`](https://github.com/Vit129/graphify/commit/fd470faeee16e9f42e3f47204824a2002a1f899c))

### Fixed
- Four production bugs — Windows crashes, ghost-merge collision, version probe ([`b830862`](https://github.com/Vit129/graphify/commit/b83086297fa032774794ed38471408da055dfac2))
- Community names blank in query/MCP after cluster-only; --graph for graphify-mcp ([`85de47e`](https://github.com/Vit129/graphify/commit/85de47e1214a0ecb9fa4e988be3912228db6ae93))

## [0.8.39] - 2026-06-12

### Added
- Add model override for community labeling ([`b304331`](https://github.com/Vit129/graphify/commit/b304331d24fe2b484dad3393bc97a60f36460af4))
- Add FalkorDB export backend ([#1175](https://github.com/Vit129/graphify/pull/1175)) ([`7aa3007`](https://github.com/Vit129/graphify/commit/7aa300709f36e35fa7024fefac9eeb426f3c8af6))
- Add --falkordb/--falkordb-push skill shorthands, use falkordb:// URI ([`bf0ace1`](https://github.com/Vit129/graphify/commit/bf0ace17596888fec4e06aafb7b202523985a882))

### Changed
- Fix O(n^2) -> O(n) LSH neighbor lookup in dedup ([`c4d6b41`](https://github.com/Vit129/graphify/commit/c4d6b412cabf422bbac72874933e43e196568690))
- Rename neo4j_* push vars to push_* (shared by neo4j + falkordb) ([`418604f`](https://github.com/Vit129/graphify/commit/418604f32a45540f52754368c53b1efe2dd5b371))

### Documentation
- Add Persian (فارسی) translation and language selector link ([`0e74c04`](https://github.com/Vit129/graphify/commit/0e74c0401e79c400d0b6b1cb1813a4291fc2d53f))

### Fixed
- Handle "edges"-keyed graph.json in load_graph (KeyError: 'links') ([`2ab2302`](https://github.com/Vit129/graphify/commit/2ab2302112ff1ef81785e6accbb078a60292863c))
- Negation pattern no longer disables all directory pruning ([`e8ab8f4`](https://github.com/Vit129/graphify/commit/e8ab8f417296ea989527e4eeb39ec41b9d554cda))
- Correct FalkorDB cypher.txt import guidance ([`1261522`](https://github.com/Vit129/graphify/commit/12615226e41b8f9a4343031fce7fee3b18ed31e0))

## [0.8.38] - 2026-06-11

### Added
- SystemVerilog class-level extraction; Dart with-clause mixin fix ([`b525549`](https://github.com/Vit129/graphify/commit/b525549a24275087f7801696f2132c8f92fd3afe))
- Add opt-in --cargo crate dependency extractor ([`b56a415`](https://github.com/Vit129/graphify/commit/b56a415388ec20d76453366e568946dfd2cd99bd))

### Documentation
- Update tree-sitter grammar count from 28 to 36 ([`3a47091`](https://github.com/Vit129/graphify/commit/3a47091021e94da07d5dfaa52e679d4f1d307385))

### Fixed
- Skip .md/.txt files in release-graph to avoid LLM API key requirement ([`ba1921f`](https://github.com/Vit129/graphify/commit/ba1921fe76c2797ec32c210943f13e7db0a90762))
- Add cluster-only step to generate GRAPH_REPORT.md in release-graph ([`565026d`](https://github.com/Vit129/graphify/commit/565026d3d10fb2d69bd01a5437433f278683fd8b))
- LLM calls-edge direction reversal and ghost-node merge ([`cce2673`](https://github.com/Vit129/graphify/commit/cce26730212baab6d92ce5f390ef5aae56268f31))
- Pick pass-2 winner from the verified pair only ([#1247](https://github.com/Vit129/graphify/pull/1247)) ([`4f8de1e`](https://github.com/Vit129/graphify/commit/4f8de1e42bcec55cf73ebf6f54a6f44ed56cf455))
- Rewire edges to deduplicated external nodes ([#1250](https://github.com/Vit129/graphify/pull/1250)) ([`444d73e`](https://github.com/Vit129/graphify/commit/444d73e1c893de30f741ae0fc71a83f6f57a0383))
- Namespace AST cache by graphify version ([#1252](https://github.com/Vit129/graphify/pull/1252)) ([`8401c50`](https://github.com/Vit129/graphify/commit/8401c50178c903970a672013ec26c8648949a18a))
- Require whole --- lines as frontmatter delimiters ([#1259](https://github.com/Vit129/graphify/pull/1259)) ([`7b5e625`](https://github.com/Vit129/graphify/commit/7b5e625066768ff6556c4ae0ac3d2fd7d4959476))
- Collect files in a single pruned walk instead of one rglob per extension ([#1261](https://github.com/Vit129/graphify/pull/1261)) ([`d26a32a`](https://github.com/Vit129/graphify/commit/d26a32a30c61b13003f71a815531bc32603034e9))
- Handle JSON-array envelope from Claude Code CLI >= 2.1 ([`edfe581`](https://github.com/Vit129/graphify/commit/edfe5812f72724b00e46b5fdb658243ebd06cb52))
- Anchor extraction cache at --out root so external output leaves the scanned project clean ([`7cb5e86`](https://github.com/Vit129/graphify/commit/7cb5e86fc1b0882102ab154ee2f61791a9d9fc87))
- Resolve_seed matches bare names against ()-decorated callable labels ([`58efceb`](https://github.com/Vit129/graphify/commit/58efcebd83df56ea2ae3ea14d556f0eb2937fb70))
- Claude-cli backend works headlessly on Windows npm installs ([`96585ba`](https://github.com/Vit129/graphify/commit/96585badd0c6b7af5637b1fa4eb965b92373f586))
- Resolve tsconfig path aliases relative to baseUrl ([`ec04152`](https://github.com/Vit129/graphify/commit/ec04152a90a0d7ffd2f6cdfd6e0781eba28d2fb2))
- Emit symbol edges for default imports/exports ([`6dc23db`](https://github.com/Vit129/graphify/commit/6dc23db90f1bc5e2241b2eba6e90b19223c97a0b))

## [0.8.37] - 2026-06-10

### Changed
- Replace datasketch with pure-numpy MinHash; memoize detect ignore checks ([`5504c84`](https://github.com/Vit129/graphify/commit/5504c84324fc9249eb4c9d0cca86da7140250032))

### Fixed
- Security hardening, dedup correctness, and large-graph support ([`6695f0a`](https://github.com/Vit129/graphify/commit/6695f0aefddc6bd8e2467b3a6606ab29985ac66a))
- Obsidian crash, NFC/NFD dedup, JSON data nodes, OpenAI temperature, JSON config detection ([`a37672f`](https://github.com/Vit129/graphify/commit/a37672f25fe10265d6a13e6a9c95ef049f7c67ac))
- Correct three bugs in release-graph workflow ([`1513e62`](https://github.com/Vit129/graphify/commit/1513e6271a3f15eebe862c8b8dfb113e4d2122f4))

## [0.8.36] - 2026-06-08

### Added
- Add graphify-mcp console script entry point ([#1190](https://github.com/Vit129/graphify/pull/1190)) ([`42d1b8d`](https://github.com/Vit129/graphify/commit/42d1b8d02ff643b1595a3ba62fa25bbbdb73a014))
- Add .slnx solution file support ([#1189](https://github.com/Vit129/graphify/pull/1189)) ([`29e57cd`](https://github.com/Vit129/graphify/commit/29e57cd295219773b8d300f1c134e41cc7133f05))
- Extra_body for custom providers + multi-batch label_communities ([#1197](https://github.com/Vit129/graphify/pull/1197)) ([`7477b46`](https://github.com/Vit129/graphify/commit/7477b469ee001b207f52178e44a8addfdac5cfd1))

### Fixed
- Remove non-spec trigger: field from skill frontmatter ([#1180](https://github.com/Vit129/graphify/pull/1180)) ([`8a04560`](https://github.com/Vit129/graphify/commit/8a04560bf5d5eaeef8e466bce084270b7f68faae))
- Guard label/text normalizers against None node labels ([#1195](https://github.com/Vit129/graphify/pull/1195)) ([`3602c80`](https://github.com/Vit129/graphify/commit/3602c8031ed886c79171623a55803845ffe765e6))
- Three correctness bugs — cycle hang, label token budget, fuzzy dedup prefix merge ([`e477825`](https://github.com/Vit129/graphify/commit/e477825a9729bff2d9a36f7473f05f42d0e4cd29))

## [0.8.35] - 2026-06-07

### Added
- Add CodeBuddy platform support ([#1136](https://github.com/Vit129/graphify/pull/1136)) ([`9e1ad42`](https://github.com/Vit129/graphify/commit/9e1ad425a9da27049f6c97a167785f162dd03df2))

### Fixed
- Prevent fuzzy dedup from collapsing distinct same-named symbols on --update ([#1178](https://github.com/Vit129/graphify/pull/1178)) ([`12a9b5e`](https://github.com/Vit129/graphify/commit/12a9b5e812549728f05a2af26d349dc5d3eb8998))
- Install SKILL.md in codebuddy install subcommand + fix README hook description ([`660d2d3`](https://github.com/Vit129/graphify/commit/660d2d32cfb7865a7ac52b8f90a4c3fe3ec78aab))

## [0.8.34] - 2026-06-07

### Added
- Add Streamable HTTP transport to MCP server ([#1143](https://github.com/Vit129/graphify/pull/1143)) ([`2a683aa`](https://github.com/Vit129/graphify/commit/2a683aac2eab905dabaae9dbbe2f2269e3fa3415))
- Land PRs #1118 #1110 #1159 #1107 #1103 (graph quality + new features) ([`7467c1b`](https://github.com/Vit129/graphify/commit/7467c1b6a41505495a5a0adea430431759aef8d6))

### Documentation
- Add Streamable HTTP transport section to README ([#1155](https://github.com/Vit129/graphify/pull/1155)) ([`7b4c8df`](https://github.com/Vit129/graphify/commit/7b4c8df6e967df4562301c0b030f1a113f97a3d4))
- Update README for Apex, Azure, and PostgreSQL additions ([`079b34d`](https://github.com/Vit129/graphify/commit/079b34da7851e6f7c7ae8347853c4dfd93f818ff))

### Fixed
- Numpy Python 3.13 pin + codex skill dir (#1154 #1160) ([`f146be3`](https://github.com/Vit129/graphify/commit/f146be3ea274363c1506da790a474651269487ef))
- Land PRs #1170 #1169 #1165 (hooks, sensitive filter, score_nodes) ([`a8dbbe5`](https://github.com/Vit129/graphify/commit/a8dbbe59cfa7bb87d124fb85297b475d8d3fdb91))
- Four bugs — affected direction, hook root, glob fish/zsh, manifest drift (#1174 #1173 #1172 #1163) ([`6a549e4`](https://github.com/Vit129/graphify/commit/6a549e42d5751d0e09e4e1dfc081450d9ca6f632))

## [0.8.33] - 2026-06-06

### Added
- Add amber brain banner on graphify install ([`3405c1f`](https://github.com/Vit129/graphify/commit/3405c1fb96c119fc928307d91fc6c190a7118e36))

### Fixed
- Three graph quality fixes (#1145 #1146 #1147) ([`a380b34`](https://github.com/Vit129/graphify/commit/a380b347397e77282df48b4587630d41a05185f8))

## [0.8.32] - 2026-06-05

### Added
- Add Terraform/HCL AST extraction via tree-sitter-hcl ([#1129](https://github.com/Vit129/graphify/pull/1129)) ([`200edec`](https://github.com/Vit129/graphify/commit/200edecea54098133f69c7eb9ec23e3ba71c0ee6))

### Documentation
- Clarify .graphifyignore vs .gitignore fallback behaviour ([#1137](https://github.com/Vit129/graphify/pull/1137)) ([`6e860e0`](https://github.com/Vit129/graphify/commit/6e860e018a32cfc1d4b84e275107b166f0d90b72))
- Clarify code-only extract needs no API key ([#1122](https://github.com/Vit129/graphify/pull/1122)) ([`9c2f2f5`](https://github.com/Vit129/graphify/commit/9c2f2f566366481952307379d96ebe7bb5c83a65))
- Add Terraform/HCL to file types table and optional extras ([#1129](https://github.com/Vit129/graphify/pull/1129)) ([`e3499e0`](https://github.com/Vit129/graphify/commit/e3499e069cc187b7a4c09836ea2b9584f88ad569))
- Bump grammar count to 28 (tree-sitter-hcl added in #1129) ([`23acb41`](https://github.com/Vit129/graphify/commit/23acb41910c2e2dd9b83e8939f9fcf0813b88d36))

### Fixed
- Correct language grammar count to 27 tree-sitter grammars in README ([`fff1c98`](https://github.com/Vit129/graphify/commit/fff1c980acb789de36d207d1c715e0833f728278))
- Skip Terraform tests when tree-sitter-hcl not installed ([`30f6f6f`](https://github.com/Vit129/graphify/commit/30f6f6fb85660ed5ee321cc71da67c3aa60fad1e))
- Route kiro install/uninstall through shared progressive helper ([#1142](https://github.com/Vit129/graphify/pull/1142)) ([`3a4bdf5`](https://github.com/Vit129/graphify/commit/3a4bdf54cce728c616d3059b05c86a67fb00f585))
- Don't require LLM API key for code-only corpus ([#1122](https://github.com/Vit129/graphify/pull/1122)) ([`f85339b`](https://github.com/Vit129/graphify/commit/f85339bcb136b511cc3c86ddec00a95883d78439))

## [0.8.31] - 2026-06-03

### Fixed
- Relativize manifest, .graphify_root, and cache source_file fields ([#777](https://github.com/Vit129/graphify/pull/777)) ([`25df580`](https://github.com/Vit129/graphify/commit/25df580061abd7ce5679cc3ff27af5b1e0c8a427))

## [0.8.29] - 2026-06-02

### Added
- Progressive-disclosure split for all platforms (generator + drift fence) ([#1121](https://github.com/Vit129/graphify/pull/1121)) ([`fbe1e99`](https://github.com/Vit129/graphify/commit/fbe1e9977fcfe37533f768e660941f78c8ee5212))

## [0.8.28] - 2026-06-01

### Added
- Add Kilo Code support ([#512](https://github.com/Vit129/graphify/pull/512)) ([`a8005c2`](https://github.com/Vit129/graphify/commit/a8005c218a6a3cdc567c56efa6e6657416bccbce))
- Modernize AST parser, support nested generics and part-of redirection ([#1098](https://github.com/Vit129/graphify/pull/1098)) ([`ec3cb5e`](https://github.com/Vit129/graphify/commit/ec3cb5eb3ebd31d88402d0310fa3be388493bfae))

## [0.8.26] - 2026-05-30

### Added
- Detect circular import dependencies at file level ([#961](https://github.com/Vit129/graphify/pull/961)) ([`c066511`](https://github.com/Vit129/graphify/commit/c066511bf2850e5cdb77f25a479db1516899d96c))

### Documentation
- Add Filipino (fil-PH) README translation ([`5056c72`](https://github.com/Vit129/graphify/commit/5056c72e67a696863b881b0b7f4de0bdf668c364))

## [0.8.25] - 2026-05-29

### Added
- Semantic type-reference edges for Swift, Kotlin, PHP, Rust, and Go ([#1015](https://github.com/Vit129/graphify/pull/1015)) ([`32aa053`](https://github.com/Vit129/graphify/commit/32aa053e6ca1fdfe5afb1460fa955c1a9178852b))
- Add objc, julia, c, c++, scala, fortran, powershell semantic contexts ([`0080fbd`](https://github.com/Vit129/graphify/commit/0080fbd13c3992b6bef94e015f88be4d922a221c))

### Documentation
- Add --mode deep to graphify extract CLI reference ([`a1706ff`](https://github.com/Vit129/graphify/commit/a1706ff7fdba2979b34a1518256ac1d826b2f22c))

### Fixed
- Eliminate hollow-response loop from system-prompt conflict ([`379d35e`](https://github.com/Vit129/graphify/commit/379d35e08892a6266e95703e73b10b1221570b98))

## [0.8.22] - 2026-05-27

### Added
- BYOND DreamMaker support, --mode deep flag, changelog fixes (#884, #1030) ([`dacbdb5`](https://github.com/Vit129/graphify/commit/dacbdb539a89ad425c684192534e5829b0d3fc10))

### Documentation
- Add Amp platform, .svh extension, fix opencode uninstall in README ([`740382a`](https://github.com/Vit129/graphify/commit/740382af511b53c0c59647329433e16e2ad0f82d))

### Fixed
- Memory-dir gitignore leak, Pass 2 dedup cross-file identical merge, decorated method node ID mismatch (#1047, #1046, #1050) ([`9f73400`](https://github.com/Vit129/graphify/commit/9f73400cbc16304360622522eef308588836b1e5))
- Remap hyperedges in community-aggregated meta-graph view ([#1006](https://github.com/Vit129/graphify/pull/1006)) ([`c09fbef`](https://github.com/Vit129/graphify/commit/c09fbef401f22901722cd7148217236c8bf93884))
- Cap zlib decompression in extract_dmi, add size guard in extract_dmm ([`cfc945a`](https://github.com/Vit129/graphify/commit/cfc945a507e9cc8be42c3be8763fdb114111e166))

## [0.8.21] - 2026-05-27

### Fixed
- Evict stale nodes in full re-extraction path when changed_paths is None ([#1007](https://github.com/Vit129/graphify/pull/1007)) ([`d1d5751`](https://github.com/Vit129/graphify/commit/d1d5751fa4e3f687b7945bc3a641e9bb517e2f2e))
- Make graph output deterministic (stop graphify-out churn) ([#1010](https://github.com/Vit129/graphify/pull/1010)) ([`a54a542`](https://github.com/Vit129/graphify/commit/a54a542b6c1d5b95e2691ecb3ffe4663033473a9))
- OpenCode project path, hook loop guard, deterministic output, Amp platform, punctuation search, builtin god-node filter, .svh Verilog (#1040, #1018, #1037, #948, #994, #916, #1042) ([`80301a0`](https://github.com/Vit129/graphify/commit/80301a06bf6b3f1f94265be1299af1a086853afb))

## [0.8.20] - 2026-05-26

### Added
- MCP config extractor (.mcp.json, claude_desktop_config.json, mcp.json) ([`2c01a89`](https://github.com/Vit129/graphify/commit/2c01a89b28fdc7c52998c0e66179b2d3e0962c84))

### Fixed
- Apply remap_communities_to_previous in cluster-only path ([#1028](https://github.com/Vit129/graphify/pull/1028)) ([`9abaa77`](https://github.com/Vit129/graphify/commit/9abaa77c62bb874e48299604dbf5f5151443d847))
- Use _file_stem instead of str(path) for child node IDs to prevent machine-specific absolute paths in graph.json ([#999](https://github.com/Vit129/graphify/pull/999)) ([`baaab5f`](https://github.com/Vit129/graphify/commit/baaab5f2a9d7c593dd959a09d59231d990937883))

## [0.8.19] - 2026-05-26

### Added
- Add Devin CLI support (graphify devin install/uninstall) ([#1020](https://github.com/Vit129/graphify/pull/1020)) ([`065a621`](https://github.com/Vit129/graphify/commit/065a621fa6091409a558920c68e4223c7276f8ce))

## [0.8.18] - 2026-05-24

### Added
- Add cross-language semantic contexts for Python, JS/TS, C#, and Java ([#996](https://github.com/Vit129/graphify/pull/996)) ([`ab4e542`](https://github.com/Vit129/graphify/commit/ab4e5424ca5019b05d7304f8273016afe3df59f6))

### Documentation
- Update Ukrainian README translation to v8 ([#995](https://github.com/Vit129/graphify/pull/995)) ([`32effb1`](https://github.com/Vit129/graphify/commit/32effb10a97187875e59f66d3b53db3179a2b21c))

### Fixed
- Bypass shrink-guard when caller declared explicit deletions ([#1000](https://github.com/Vit129/graphify/pull/1000)) ([`6fba4e4`](https://github.com/Vit129/graphify/commit/6fba4e4594f25c1d408d0f039a1fb97656f27217))
- Reconstruct communities from per-node attribute when sidecar missing ([#1001](https://github.com/Vit129/graphify/pull/1001)) ([`d778e2c`](https://github.com/Vit129/graphify/commit/d778e2c36bf46868f487a31e788984bc4f41ba09))

## [0.8.16] - 2026-05-22

### Added
- Add runtime compatibility probe ([#956](https://github.com/Vit129/graphify/pull/956)) ([`b6127aa`](https://github.com/Vit129/graphify/commit/b6127aa5a7cf289aba80051dcc94f00646853410))
- Add v8 affected and import-resolution support ([`e44e6e9`](https://github.com/Vit129/graphify/commit/e44e6e986c44abab38d28ab865f95deea242dcf6))
- Track JS/TS barrel re-exports as explicit graph edges ([`1494874`](https://github.com/Vit129/graphify/commit/1494874e25c6af89cdaed10fa3d9a8e09498b5a5))
- Add project-scoped skill installs ([#931](https://github.com/Vit129/graphify/pull/931)) ([`b347492`](https://github.com/Vit129/graphify/commit/b3474924c2d1d0f3f9d93b2f2e7157f24a630987))

### Documentation
- Add Uzbek (uz-UZ) README translation ([#982](https://github.com/Vit129/graphify/pull/982)) ([`38cebd3`](https://github.com/Vit129/graphify/commit/38cebd321f359001c2bab7f58bd77dc210ab9d5f))

### Fixed
- Honor GRAPHIFY_MAX_OUTPUT_TOKENS for OpenAI-compatible backends ([#973](https://github.com/Vit129/graphify/pull/973)) ([`06a9b72`](https://github.com/Vit129/graphify/commit/06a9b72a38a3b0edd75a0e4ac96923656190e71e))
- CJK/Unicode labels silently skipped in _norm/_norm_label dedup (follow-up to #811) ([#937](https://github.com/Vit129/graphify/pull/937)) ([`86109e9`](https://github.com/Vit129/graphify/commit/86109e9f272606abff3c4c08beaef01b5f6138a9))
- Add .ets (ArkTS) extension to CODE_EXTENSIONS ([#926](https://github.com/Vit129/graphify/pull/926)) ([`52d75bd`](https://github.com/Vit129/graphify/commit/52d75bd988d71a1ad2dd406dd77bdddfa6c96fcb))

## [0.8.13] - 2026-05-18

### Documentation
- Clarify code-only corpora skip semantic extraction (closes #836) ([`9f8b8b0`](https://github.com/Vit129/graphify/commit/9f8b8b0072d88565cc2826b6f85dbec4095d9de2))

## [0.8.11] - 2026-05-18

### Changed
- Reuse degrees for surprise scoring ([#914](https://github.com/Vit129/graphify/pull/914)) ([`a4a475c`](https://github.com/Vit129/graphify/commit/a4a475c8b65fec4e29a6d0e9d00ececcd02e90c7))

### Fixed
- Guard against empty choices and None message in LLM responses ([#924](https://github.com/Vit129/graphify/pull/924)) ([`f5fea13`](https://github.com/Vit129/graphify/commit/f5fea13dbc235438e8090cd9a142acce383ec107))
- Remove invalid general-purpose agent guidance ([#911](https://github.com/Vit129/graphify/pull/911)) ([`4aa04dd`](https://github.com/Vit129/graphify/commit/4aa04ddc7df9f6a49368fc81169c068048c84e44))
- Keep graph-first guidance with dirty graph output ([#913](https://github.com/Vit129/graphify/pull/913)) ([`f0d29a1`](https://github.com/Vit129/graphify/commit/f0d29a1c6d28b02a28f48ff7241b11416d53c62d))

## [0.8.9] - 2026-05-17

### Fixed
- Force UTF-8 encoding on _call_claude_cli subprocess + loud failure on chunk errors ([#906](https://github.com/Vit129/graphify/pull/906)) ([`6018831`](https://github.com/Vit129/graphify/commit/60188311933f5b99ccb2d735136b6c412b0eaf8b))
- Exclude npm dep-block keys from god-node selection ([#905](https://github.com/Vit129/graphify/pull/905)) ([`2aaa216`](https://github.com/Vit129/graphify/commit/2aaa216825e93fa6bec616f743e5967182c744d5))
- Accept edges-only graph JSON for wiki export ([#909](https://github.com/Vit129/graphify/pull/909)) ([`ec4c87c`](https://github.com/Vit129/graphify/commit/ec4c87c86e6b42d8c8148980b0e8607ba6d0a88b))

## [0.8.6] - 2026-05-16

### Added
- Auto-detect symlinked children when follow_symlinks is unset ([`5e178b9`](https://github.com/Vit129/graphify/commit/5e178b9cd4d708741a6a083109790c5f9ac6ff25))

## [0.7.19] - 2026-05-14

### Added
- Add .astro support ([#850](https://github.com/Vit129/graphify/pull/850)) ([`c0048d0`](https://github.com/Vit129/graphify/commit/c0048d0a61ccfc8431094101d0527ca1f7850204))
- Add .astro support (#850, PR #852, spindle79) ([`fcafec7`](https://github.com/Vit129/graphify/commit/fcafec708122ce66b33d799091a9870cd7e62529))

### Documentation
- Clarify that no provider API key is read for semantic extraction ([`a08f0de`](https://github.com/Vit129/graphify/commit/a08f0de53b089014ad815addac6e7f7cc8dece36))
- Clarify no provider API key is read for semantic extraction (PR #864, Jstottlemyer) ([`6c78a74`](https://github.com/Vit129/graphify/commit/6c78a74776820c71fca92330017e6eacfc790458))

### Fixed
- Unlink .rebuild.lock on release and rewrite single PID line ([#858](https://github.com/Vit129/graphify/pull/858)) ([`2c975ee`](https://github.com/Vit129/graphify/commit/2c975ee9fbdeba5fc7ff649d682bc56ff9ca7af0))
- Unlink .rebuild.lock on release, rewrite single PID line (PR #859, voidborne-d) ([`cfe18ea`](https://github.com/Vit129/graphify/commit/cfe18ea947f4b2c49c603550fd7be42d53a98c71))

## [0.7.18] - 2026-05-13

### Documentation
- Comprehensive README overhaul with prerequisites, extras, env vars, troubleshooting, dev setup ([`2db5d96`](https://github.com/Vit129/graphify/commit/2db5d966f26ec26ee1ca75bf2175ef759b256f4c))
- Add prerequisites, extras table, env vars, troubleshooting, dev setup (PR #833, sachinampity) ([`ddb9822`](https://github.com/Vit129/graphify/commit/ddb98226df24fe37d5f14d80e8e922152fbf3f25))

### Fixed
- Deterministic clustering, topology short-circuit on unchanged graph, --no-cluster for update (PR #824, FatahChan) ([`1b8b768`](https://github.com/Vit129/graphify/commit/1b8b76816e9870de9dcd633454d55d319452a066))

## [0.7.17] - 2026-05-13

### Added
- Add --backend claude-cli (routes through Claude Code, no API key needed) ([#855](https://github.com/Vit129/graphify/pull/855)) ([`258d260`](https://github.com/Vit129/graphify/commit/258d2600cd7004d012875ea878488c9a8519964a))

## [0.7.13] - 2026-05-09

### Added
- Add Pascal/Delphi and Lazarus IDE support ([#781](https://github.com/Vit129/graphify/pull/781)) ([`32bf8b4`](https://github.com/Vit129/graphify/commit/32bf8b4a37427ab93d7fbaeb57b4be9dfd0f1fbf))
- Add callflow HTML export with Mermaid architecture diagrams ([`db66b87`](https://github.com/Vit129/graphify/commit/db66b8727bc39467769d01122f1712829079242b))

## [0.7.11] - 2026-05-09

### Fixed
- Add ALTER TABLE FK extraction + schema-qualified name support for SQL ([#779](https://github.com/Vit129/graphify/pull/779)) ([`5d03925`](https://github.com/Vit129/graphify/commit/5d0392524a77ae7cd7e50bf0c954705e1bd99bff))
- Unblock pipeline on Windows consoles + missing __main__ guards ([#788](https://github.com/Vit129/graphify/pull/788)) ([`e5f263b`](https://github.com/Vit129/graphify/commit/e5f263ba98e81ed68e0d02558bf5cf5062291f46))

## [0.7.10] - 2026-05-07

### Changed
- Strengthen agent instructions sections with forceful graph-first directives ([#775](https://github.com/Vit129/graphify/pull/775)) ([`e16ea14`](https://github.com/Vit129/graphify/commit/e16ea149aa9b636a3db5233915a3cf443bfa287f))

### Fixed
- Use language_tsx for .tsx files to enable JSX-aware parsing ([#766](https://github.com/Vit129/graphify/pull/766)) ([`8489b26`](https://github.com/Vit129/graphify/commit/8489b26d0670c0347cc9dafbfdfa472ba3413b3c))
- Rewrite YAML descriptions from pipeline-only to trigger-oriented ([#774](https://github.com/Vit129/graphify/pull/774)) ([`a15cb36`](https://github.com/Vit129/graphify/commit/a15cb36dfcdb1630044a3140c981bea9954b95aa))

## [0.7.9] - 2026-05-07

### Added
- Add .qmd file extension support ([`1026695`](https://github.com/Vit129/graphify/commit/1026695da79fe64805e344abe43c1012bf71a74a))
- Extract interface, enum, type_alias, const literal, new_expression ([`eca3277`](https://github.com/Vit129/graphify/commit/eca3277fb964f06ea1ef00dafc5d0113038d80c1))

### Fixed
- Surface tree-sitter version-mismatch hint instead of bare TypeError ([`189847e`](https://github.com/Vit129/graphify/commit/189847eb473e92747da083e955a0508713b5fb96))
- Silence "invalid file_type 'None'" warning on legacy graphs ([#660](https://github.com/Vit129/graphify/pull/660)) ([`f87d064`](https://github.com/Vit129/graphify/commit/f87d0649c5e88d9451b5e8d91b6bbcd61d506159))
- Extract CommonJS require() imports as EXTRACTED edges ([`c902ae9`](https://github.com/Vit129/graphify/commit/c902ae952bd0c940be19e6adccf36e5f5185b787))
- Promote cross-file call edges to EXTRACTED when import evidence exists ([`2dd6ee6`](https://github.com/Vit129/graphify/commit/2dd6ee6a9c2e24ec5d83ccbf72a859db3bc656fb))

## [0.7.8] - 2026-05-06

### Added
- Add Markdown structural extraction + sync collect_files extensions ([`68081c1`](https://github.com/Vit129/graphify/commit/68081c1c894364071bff309d0e897cfdb2af0aff))
- Add Groovy and Spock support ([`dc69020`](https://github.com/Vit129/graphify/commit/dc69020a4743b4bdd8d870cd2073637f9b1480d0))

### Documentation
- Add fork install instructions and feature comparison to README ([`cddf9cf`](https://github.com/Vit129/graphify/commit/cddf9cf9bfd29b34d95a04623a20dec0f21ec04d))

### Fixed
- Forward follow_symlinks from detect_incremental to detect ([`64585cf`](https://github.com/Vit129/graphify/commit/64585cf8892edea1e321347dee28cb92c8c30774))
- V-003 security vulnerability ([`6fa2ba2`](https://github.com/Vit129/graphify/commit/6fa2ba2318f7441ffc27261cb18395da373820ea))
- Include .md/.mdx document files in graphify update rebuild path ([`09b33b7`](https://github.com/Vit129/graphify/commit/09b33b795b9a24513afb7defaf0db1bf6bd0a9e6))
- TS bare-path / .svelte.ts / index.ts import resolution ([`2b1efe8`](https://github.com/Vit129/graphify/commit/2b1efe8f08247bbbd118e5464b2b231bc2a94857))
- Generalize resolver to multi-dot filenames + rename ([`49c3b50`](https://github.com/Vit129/graphify/commit/49c3b50b5f94c3a77f0562e2748c9aacf58accd5))
- Prefer file matches over directory matches in resolver ([`0dfc26e`](https://github.com/Vit129/graphify/commit/0dfc26e57f7479f52ecef58b560722461d0b3e09))
- Apply resolver fixups to JS/TS dynamic_import handler ([`b68ec63`](https://github.com/Vit129/graphify/commit/b68ec63494ded5848710bc5db667ac05dda4d8b1))

## [0.6.8] - 2026-05-03

### Added
- Implement parallel AST extraction using ProcessPoolExecutor with benchmarking support ([`0fc2dc6`](https://github.com/Vit129/graphify/commit/0fc2dc6ad3760f6a073f09a628b14d39d14f6bb3))

## [0.6.7] - 2026-05-02

### Added
- Add VB.NET (.vb) language support via tree-sitter ([`5dbbcf7`](https://github.com/Vit129/graphify/commit/5dbbcf7dadbee0482d34fd4d1d1419a06eee55b8))
- Add extraction support for VB.NET files ([`af15e33`](https://github.com/Vit129/graphify/commit/af15e33f577f3ae11d2892a779d0a3e14f829fac))
- Add VB.NET (.vb) language support via tree-sitter ([#648](https://github.com/Vit129/graphify/pull/648)) ([`7237cd3`](https://github.com/Vit129/graphify/commit/7237cd32908b958a84a377ad5d877ed4ddaf68c2))
- Pack chunks by token budget, parallelise, accept tiktoken ([`cc5c545`](https://github.com/Vit129/graphify/commit/cc5c54574d7b99e1c0d0476d65dd821b80ce6cbc))
- Split and retry chunks that hit max_completion_tokens truncation ([`2d13a17`](https://github.com/Vit129/graphify/commit/2d13a17c3b49f74904895a9d5946798aeb6bc1a2))
- Graphify tree — D3 v7 collapsible-tree HTML emitter ([`c3ba79f`](https://github.com/Vit129/graphify/commit/c3ba79f5aae7f41488646df46fcbf82232afb94b))
- Add cross-language edge contexts and context-aware queries ([`3ff7188`](https://github.com/Vit129/graphify/commit/3ff7188fbf276af8cb447a978e32f5c5f75ccd14))
- Add dynamic import() extraction for JS/TS ([`a1dc610`](https://github.com/Vit129/graphify/commit/a1dc610079970e450ebc0f7d5360cfc8b63f9066))

### Documentation
- Add Pi coding agent to README platform table and install docs ([`893219d`](https://github.com/Vit129/graphify/commit/893219d66f423e7a207f5f3f849d1630fb52ed48))
- Add Pi to pyproject.toml description and keywords ([`58271fb`](https://github.com/Vit129/graphify/commit/58271fb5af4c0c123ddbad9c689ee1e220360be8))
- Add Docker MCP Toolkit + SQLite MCP runbook ([`abb1450`](https://github.com/Vit129/graphify/commit/abb1450b244a327a1b0317539c050a32153d5a9e))
- Add Docker MCP Toolkit + SQLite MCP runbook ([#620](https://github.com/Vit129/graphify/pull/620)) ([`66e61c7`](https://github.com/Vit129/graphify/commit/66e61c76b1fb4ee0b871351c1d954e31ed927c2c))
- Remove VB.NET from README language count and file type table ([`bd92ab6`](https://github.com/Vit129/graphify/commit/bd92ab67d64ffcf2cf087954cd808ff38d9e339a))

### Fixed
- Emit symbol-level edges for TS/JS named imports ([`5a342e3`](https://github.com/Vit129/graphify/commit/5a342e385cbf3e0f6ef7083a493e2abbcdb171d7))
- Escape title, header, and JSON blob in emit_html ([`a523509`](https://github.com/Vit129/graphify/commit/a52350940a1d1aae8a0b723a3d275005ceefadc6))
- Add context=import to JS/TS named-import edges (caught by PR #573 test) ([`bfe18f0`](https://github.com/Vit129/graphify/commit/bfe18f0c838aeb0d6450e50a380381c27a913a8d))
- Drop Python <3.14 upper bound ([`88e2b83`](https://github.com/Vit129/graphify/commit/88e2b832f7037d4649b770638d295d2da00c649d))
- Skip dynamic template literals in import() args ([`563ee80`](https://github.com/Vit129/graphify/commit/563ee80494a9da01a7890504f1a8c63bdea37347))

## [0.6.5] - 2026-05-02

### Added
- Replace show/hide buttons with checkbox-based multi-select controls ([#647](https://github.com/Vit129/graphify/pull/647)) ([`8e01d68`](https://github.com/Vit129/graphify/commit/8e01d686f73ea363aecd0e0cdd631fdbbd49b758))

## [0.5.0] - 2026-04-23

### Added
- Graphify clone <github-url> — clone any repo and run full pipeline on it ([`2c49da2`](https://github.com/Vit129/graphify/commit/2c49da24f0a81086e0cd5cea0df2aaea00c4b544))
- Cross-repo merge-graphs; fix #527 CLAUDE_CONFIG_DIR; fix #524 graphify-out excluded from source scan ([`2faeed9`](https://github.com/Vit129/graphify/commit/2faeed99a2e9939772e304ceec61d918be8d022f))

## [0.4.27] - 2026-04-22

### Fixed
- Deterministic GRAPH_REPORT on large graphs, stable edge node IDs, correct common-root inference ([`d9b2928`](https://github.com/Vit129/graphify/commit/d9b2928da151e690ac299bdfef1c78d3d9e32815))

## [0.4.26] - 2026-04-22

### Fixed
- Wiki encoding+collisions, hook rebase guard, detect path resolve, readme gitignore docs ([`f8fd8f8`](https://github.com/Vit129/graphify/commit/f8fd8f8479240337a449030a632cc76c20203844))

## [0.4.25] - 2026-04-21

### Fixed
- Complete empty-community fix — hubs, summary count, thin-community gaps; add graph-query CLI rules to install sections ([`7cb639a`](https://github.com/Vit129/graphify/commit/7cb639ae5dedbf7cb20070cb73a4f845e5977d2e))

## [0.4.19] - 2026-04-17

### Documentation
- Add Verilog/SystemVerilog to language count and list ([`ac265ec`](https://github.com/Vit129/graphify/commit/ac265ec495d784593b9cb7b3e7aa6cb11571b5fe))
- V5 design spec -- rustworkx backend + GitHub repo ingestion ([`c8a9a6c`](https://github.com/Vit129/graphify/commit/c8a9a6cdbc5aad4adad988a7f7bf43aca68e27e2))
- Revise v5 spec after senior engineering review -- GraphBundle, correct rustworkx APIs, git fetch strategy ([`2a4608c`](https://github.com/Vit129/graphify/commit/2a4608cbb003f0d3e403b3c6476ac8953a62375a))
- V5.0 and v5.1 design specs -- enterprise foundation ([`022feee`](https://github.com/Vit129/graphify/commit/022feee5fb24a9aa08a45e2ecad991409fe11f99))

## [0.4.11] - 2026-04-13

### Documentation
- Add Hermes platform, Dart to language list, 22→23 languages ([`e737f5b`](https://github.com/Vit129/graphify/commit/e737f5bf586319180c89bbf2c27209f2534efbe9))

## [0.4.0] - 2026-04-10

### Added
- Add Trae and Trae CN platform support ([`76bbb37`](https://github.com/Vit129/graphify/commit/76bbb37c745e580ff229dc1db6300bd869df68a9))

### Documentation
- Add graph.json + LLM workflow example to README ([`f937fc6`](https://github.com/Vit129/graphify/commit/f937fc6ce18cb90674a0447aa763bcc506f65c4d))
- Add Japanese README ([`a87be41`](https://github.com/Vit129/graphify/commit/a87be4143a3a8068eba68fbeb1d5edc1800dd86e))
- Add .jsx .tsx .jl to extensions table, bump to 20 languages ([`dbcb125`](https://github.com/Vit129/graphify/commit/dbcb1253e8df1e589f42df308b100d2ca0e054c8))

### Fixed
- Detect correct Python interpreter for pipx installs in git hooks ([`ba7c395`](https://github.com/Vit129/graphify/commit/ba7c395ce38760aa43621024fd551ee23a1f7a84))
- Suppress graspologic ANSI output that corrupts PowerShell scroll buffer ([`22f79db`](https://github.com/Vit129/graphify/commit/22f79db72f9da463153a436856a00cc1949e134e))
- Skill-droid.md missing from package-data, louvain kwargs version-safe ([`21a081b`](https://github.com/Vit129/graphify/commit/21a081b5143633342be302004db1e63b8b7d6cf3))
- XSS in legend innerHTML and shebang allowlist in hooks ([`2b3accf`](https://github.com/Vit129/graphify/commit/2b3accfe6654abef8cb8bac354ddf68b65138386))
- Shebang allowlist validation in all skill files ([`359ef86`](https://github.com/Vit129/graphify/commit/359ef86dd4cf8d7201eb69a1564fc81a784ae84e))
- Switch star history chart to starchart.cc (no auth required) ([`b4180a5`](https://github.com/Vit129/graphify/commit/b4180a50dcf585892174f94a292b1676ab686f1b))

## [0.3.14] - 2026-04-08

### Fixed
- Codex PreToolUse hook + --update ghost node pruning (#86, #51) ([`2d64c0c`](https://github.com/Vit129/graphify/commit/2d64c0cd10c13d796b15625ded8b50b674db2dab))

## [0.3.13] - 2026-04-08

### Fixed
- Ensure Cypher node label always starts with a letter ([#84](https://github.com/Vit129/graphify/pull/84)) ([`ffd8906`](https://github.com/Vit129/graphify/commit/ffd8906c6c3b323359ff9c3f23234fa129445145))
- Hook JSON format, Go pkg scoping, xcassets PDF, cross-file guard, skill file paths (#83, #85, #52, #81) ([`bd24ddb`](https://github.com/Vit129/graphify/commit/bd24ddb1d6df10af9a411e3f7f043f266e02d26f))

## [0.3.12] - 2026-04-08

### Fixed
- Sanitize_label double-encoding and --wiki missing from skill (#66, #55) ([`92b70ce`](https://github.com/Vit129/graphify/commit/92b70ce5f4f208bb7ea4d4e796f70e52e40418eb))

## [0.3.1] - 2026-04-06

### Added
- GraphML export (--graphml flag) for Gephi and yEd ([`7e82212`](https://github.com/Vit129/graphify/commit/7e82212304c6e14db37305ee217ba2d2b065996b))
- Composite surprise score — cross-type, cross-repo, community distance, peripheral→hub ([`693d2ba`](https://github.com/Vit129/graphify/commit/693d2ba99169deceb57648c7d274a7089f741c87))
- Vis.js HTML graph, token reduction benchmark, repo cleanup ([`d4b24d8`](https://github.com/Vit129/graphify/commit/d4b24d86093f30446927b5f259c6016274987e8c))
- Multi-platform skill files and install routing (Codex, OpenCode, OpenClaw) ([`38d967f`](https://github.com/Vit129/graphify/commit/38d967fc6325af38ca66cbe97eafaa5c3ce9bea4))
- Always-on hooks and README updates for all platforms ([`1a54f16`](https://github.com/Vit129/graphify/commit/1a54f16b8028892300bfdaa63fcfe4c4a03af05d))
- Swift language support ([`477465a`](https://github.com/Vit129/graphify/commit/477465ae0dda86c3a04468f3fed35c4acb5c3d80))
- Lua language support ([`9eda155`](https://github.com/Vit129/graphify/commit/9eda1558c25da0fa5997ea9634560e38767d032b))

### Changed
- Larger chunks + code-only fast path + timing estimates ([`ef8c2fe`](https://github.com/Vit129/graphify/commit/ef8c2fef505a6bb0cfb402a31284ed558119a443))

### Documentation
- Update surprising connections description, test count ([`5db8f7c`](https://github.com/Vit129/graphify/commit/5db8f7ce392afef7f7999baa02dcd5b46a2eca3d))
- Add Simplified Chinese README ([`79b8d8d`](https://github.com/Vit129/graphify/commit/79b8d8d9b28a536c786e32ecefab462dd373dfb8))

### Fixed
- 5 skill gaps - graphml usage, manifest timing, graph existence checks, no-viz clarity ([`d8b1e82`](https://github.com/Vit129/graphify/commit/d8b1e820793a66a4357d17e965ae7d8d3368326b))
- HTML always generated by default in Step 6, not flag-gated ([`cb4ec5d`](https://github.com/Vit129/graphify/commit/cb4ec5d39d782b0c978f8995b7d198ef8204ab62))
- Use correct Python interpreter for pipx installs ([`07de9d5`](https://github.com/Vit129/graphify/commit/07de9d5c22457835ee6ba82e8bd3eafc95c3ea21))

## [1.0.0] - 2026-04-05

### Added
- Core pipeline ([`77966a7`](https://github.com/Vit129/graphify/commit/77966a76225725c1b492c9ac9ad77949f656c504))
- Claude Code skill, Obsidian vault, install, tests ([`ce47198`](https://github.com/Vit129/graphify/commit/ce47198be149da8ae0b33b6e5d6ea0e7a2fe8b9c))
- Cache, multi-language extraction, MCP, memory feedback ([`e7a03a0`](https://github.com/Vit129/graphify/commit/e7a03a0539709aac93161cf5f7d6341121557ba8))
- 13-language AST support and token benchmark ([`81a43f0`](https://github.com/Vit129/graphify/commit/81a43f028ff1d3fd9a0893318272348a38dad660))
- GraphML export (--graphml flag) for Gephi and yEd ([`a7f9106`](https://github.com/Vit129/graphify/commit/a7f910667d8000bc5d2e56aa5736fabe5d9b646e))
- Composite surprise score — cross-type, cross-repo, community distance, peripheral→hub ([`258eff3`](https://github.com/Vit129/graphify/commit/258eff3e9fafbb77d89bdccc2bfcda16628c8162))
- Vis.js HTML graph, token reduction benchmark, repo cleanup ([`8708333`](https://github.com/Vit129/graphify/commit/87083334847b3e1c932766e7c3b25b4ac648aa8b))

### Changed
- Parallel extraction, faster imports, bug fixes ([`0b7460a`](https://github.com/Vit129/graphify/commit/0b7460a9e3dca374c5d9a30d157793740ea8b973))
- Larger chunks + code-only fast path + timing estimates ([`c88528d`](https://github.com/Vit129/graphify/commit/c88528dfa3bf077c007ec17150c9e51afad432b6))
- Dead imports, node_community helper, split to_html and call_tool ([`a1be5ab`](https://github.com/Vit129/graphify/commit/a1be5abb245e806982c9b7b153b3cd30aa88cfda))

### Documentation
- Lead with Karpathy problem → graphify answer framing ([`cf7f42d`](https://github.com/Vit129/graphify/commit/cf7f42d3e74771f49d15ab3ede785a4177ca9510))
- Update surprising connections description, test count ([`a7d1969`](https://github.com/Vit129/graphify/commit/a7d1969f02cac9c44b3c2b282dccd2074c8775dc))

### Fixed
- 5 skill gaps - graphml usage, manifest timing, graph existence checks, no-viz clarity ([`0061b36`](https://github.com/Vit129/graphify/commit/0061b36c2923a8b78df2d66a9956e06e8cd85445))
- HTML always generated by default in Step 6, not flag-gated ([`e98c1b6`](https://github.com/Vit129/graphify/commit/e98c1b629792691259c253a488ef65bc1d914440))

