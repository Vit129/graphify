# Graph Report - graphify-refresh  (2026-10-31)

## Corpus Check
- 713 files · ~863,038 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 11152 nodes · 20895 edges · 797 communities (609 shown, 188 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 318 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ca7452c1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## God Nodes (most connected - your core abstractions)
1. `extract()` - 282 edges
2. `main()` - 264 edges
3. `Graph` - 195 edges
4. `build_from_json()` - 132 edges
5. `_read_text()` - 109 edges
6. `_make_id()` - 103 edges
7. `extract_js()` - 97 edges
8. `ingest_scip_json()` - 85 edges
9. `_file_stem()` - 84 edges
10. `Changelog` - 81 edges

## Cross-Cutting Nodes (span the most distinct areas of the codebase)
A high-degree node isn't always architecturally central - a widely-used
utility/config file can rack up more edges than a real coupler while only
ever touching one area. This ranks by how many DIFFERENT communities a
node's neighbors span, not by raw edge count.
1. `main()` - bridges 82 areas (264 edges)
2. `extract()` - bridges 62 areas (282 edges)
3. `Changelog` - bridges 53 areas (81 edges)
4. `Graph` - bridges 42 areas (195 edges)
5. `build_from_json()` - bridges 41 areas (132 edges)
6. `_make_id()` - bridges 34 areas (103 edges)
7. `_rebuild_code()` - bridges 34 areas (80 edges)
8. `_file_stem()` - bridges 33 areas (84 edges)
9. `ingest_scip_json()` - bridges 32 areas (85 edges)
10. `_read_text()` - bridges 19 areas (109 edges)

## Surprising Connections (you probably didn't know these)
- `test_find_node_resolves_paraphrased_query_across_conventions()` --calls--> `_find_node()`  [INFERRED]
  tests/test_real_world_naming_conventions.py → graphify/query.py
- `main()` --calls--> `_build()`  [INFERRED]
  graphify/__main__.py → tests/test_indirect_dispatch.py
- `test_affected_cli_source_file_path_uses_file_level_node()` --calls--> `main()`  [EXTRACTED]
  tests/test_affected_cli.py → graphify/__main__.py
- `test_cli_help_lists_cypher()` --calls--> `main()`  [EXTRACTED]
  tests/test_cypher.py → graphify/__main__.py
- `test_diagnose_multigraph_cli_usage_errors()` --calls--> `main()`  [EXTRACTED]
  tests/test_multigraph_diagnostics.py → graphify/__main__.py

## Import Cycles
- 1-file cycle: `tests/fixtures/sample.sv -> tests/fixtures/sample.sv`

## Communities (797 total, 188 thin omitted)

### Community 0 - "extract.py"
Cohesion: 0.02
Nodes (139): _apply_symbol_resolution_facts(), _augment_js_reexport_edges(), _augment_symbol_resolution_edges(), _augment_systemverilog_semantics(), _c_collect_type_refs(), _collect_js_symbol_resolution_facts(), _collect_python_symbol_resolution_facts(), _csharp_classify_base() (+131 more)

### Community 1 - "test_extract.py"
Cohesion: 0.02
Nodes (125): collect_files(), extract_bash(), extract_json(), Extract functions, source imports, and cross-function calls from a .sh file., Extract structure and dependency edges from a *config/manifest* .json file., _semantic_reference_edge(), _source_location(), by_label_by_id() (+117 more)

### Community 2 - "__main__.py"
Cohesion: 0.03
Nodes (126): _agents_install(), _agents_platform_install(), _agents_platform_uninstall(), _agents_uninstall(), _always_on(), _amp_install(), _amp_legacy_cleanup(), _amp_uninstall() (+118 more)

### Community 3 - "_read_text"
Cohesion: 0.03
Nodes (113): _cpp_collect_type_refs(), _cpp_declarator_name(), _cpp_local_var_types(), _csharp_method_receiver_types(), _csharp_pre_scan_interfaces(), _dynamic_import_js(), extract_dmi(), _extract_generic() (+105 more)

### Community 4 - "extract_js"
Cohesion: 0.02
Nodes (100): extract_js(), Extract classes, functions, arrow functions, and imports from a .js/.ts/.tsx fil, Functions defined alongside a JSX-returning component must be captured., Calls inside JSX expressions like `{fmtDate(now)}` must yield call edges.      R, export { X } from './mod' must emit re_exports edges for each named specifier., Barrel file must emit file-level imports_from edges to source modules., re_exports edges should have context='re-export'., export function/const in a barrel file must still create nodes. (+92 more)

### Community 5 - "test_analyze.py"
Cohesion: 0.04
Nodes (100): _cross_language(), _file_category(), find_import_cycles(), god_nodes(), graph_diff(), Return the top_n most-connected real entities - the core abstractions.      File, Find connections that are genuinely surprising - not obvious from file structure, Return the first path component - used to detect cross-repo edges. (+92 more)

### Community 6 - "test_detect.py"
Cohesion: 0.03
Nodes (97): detect(), _is_sensitive(), _is_skipped_file(), Return True if this file likely contains secrets and should be skipped., Files matching .graphifyignore patterns are excluded from detect()., .graphifyignore is evaluated after .gitignore, so a `!` negation in it can     r, Files inside .worktrees/ are never indexed (#947)., Files inside .claude/worktrees/ (nested placement) are never indexed (#1023). (+89 more)

### Community 7 - "cluster"
Cohesion: 0.04
Nodes (95): cluster(), Run Leiden community detection. Returns {community_id: [node_ids]}.      Communi, backup_if_protected(), _cypher_escape(), _cypher_label(), existing_graph_node_count(), _git_head(), _html_script() (+87 more)

### Community 8 - "test_serve.py"
Cohesion: 0.04
Nodes (94): _blast_radius_hops(), _pick_seeds(), Walk outward from `nid` hop by hop, direction-aware (callers/callees/both)., Select BFS seed nodes, stopping when score drops too far below the top.      `ga, _community_header(), Body of the `shortest_path` MCP tool (module-level so tests can call it     with, _shortest_path_text(), _directed_chain() (+86 more)

### Community 9 - "detect.py"
Cohesion: 0.03
Nodes (92): _auto_follow_symlinks(), convert_office_file(), _could_contain_included_path(), count_words(), detect_incremental(), docx_to_markdown(), extract_pdf_text(), _file_within_size_cap() (+84 more)

### Community 10 - "test_install.py"
Cohesion: 0.03
Nodes (90): gemini_install(), gemini_uninstall(), _kilo_uninstall(), _kilo_uninstall_global(), Remove the graphify section from GEMINI.md, uninstall hook, and remove skill fil, Remove Kilo always-on project wiring and global skill/command files., Copy skill file, write GEMINI.md section, and install BeforeTool hook., _agents_install() (+82 more)

### Community 11 - "classify_file"
Cohesion: 0.03
Nodes (91): Enum, classify_file(), FileType, Return the interpreter name from a shebang line.      Handles forms that a naive, Peek at the first line of an extensionless file for a shebang., _shebang_file_type(), _shebang_interpreter(), str (+83 more)

### Community 12 - "main"
Cohesion: 0.04
Nodes (76): load_community_names(), Path, Community labels written next to graph.json (empty when absent or unreadable)., global_path(), provider_base_url_ok(), Structural safety check for a custom-provider base_url.      A custom provider r, main(), _print_install_usage() (+68 more)

### Community 13 - "test_languages.py"
Cohesion: 0.04
Nodes (77): extract_dmf(), extract_fortran(), extract_julia(), extract_swift(), Extract windows and controls from a .dmf interface file., Extract classes, structs, protocols, functions, imports, and calls from a .swift, Extract modules, structs, functions, imports, and calls from a .jl file., Extract programs, modules, subroutines, functions, use statements, and calls fro (+69 more)

### Community 14 - "test_import_extension_resolution.py"
Cohesion: 0.05
Nodes (75): Resolve a JS/TS module path or specifier to a local source file.      With a Pat, _resolve_js_module_path(), _import_targets(), Path, Tests for #716 — TypeScript bare-path imports, Svelte 5 rune file imports (`from, JS variant of the rune file pattern: a `.svelte.js` file (used in     JavaScript, When both `.svelte.ts` and `.svelte.js` exist (hybrid project mid-     migration, If `foo.svelte` IS a real markup file, importing `./foo.svelte`     must resolve (+67 more)

### Community 15 - "extract"
Cohesion: 0.08
Nodes (71): _canonicalize_csharp_namespace_nodes(), _check_tree_sitter_version(), extract(), Collapse duplicate C# namespace node entries to one canonical node per label., Raise a clear error if tree-sitter is too old for the new Language API., Extract AST nodes and edges from a list of code files.      Two-pass process:, _defs(), _node_by_id() (+63 more)

### Community 16 - "test_multilang.py"
Cohesion: 0.05
Nodes (71): extract_go(), extract_rust(), Extract functions, methods, type declarations, and imports from a .go file., Extract functions, structs, enums, traits, impl methods, and use declarations fr, Methods on the same receiver type must share one canonical type node., Type node id should be scoped to directory, not file stem., test_go_receiver_methods_share_type_node(), test_go_receiver_uses_pkg_scope() (+63 more)

### Community 17 - "_make_graph"
Cohesion: 0.04
Nodes (71): _bfs(), _dfs(), _embedding_corpus_hash(), _embedding_seed_fallback(), _embedding_similarity_map(), _filter_graph_by_context(), _fuse_embedding_rrf(), _get_embedding_index() (+63 more)

### Community 18 - "Path"
Cohesion: 0.04
Nodes (69): _contained_in_package(), _cpp_preprocess(), _decldef_class_stem(), _disambiguate_colliding_node_ids(), extract_lua(), _extract_parallel(), _extract_sequential(), _extract_single_file() (+61 more)

### Community 19 - "test_csharp_member_calls.py"
Cohesion: 0.06
Nodes (68): _calls(), _find(), C# receiver-typed member-call resolution (#1609).  `recv.Method()` where `recv`, `Svc` exists in namespaces A and B; a caller file `using A;` must bind an     `A, No using directive and `Svc` in two foreign namespaces: genuinely     ambiguous, A caller in namespace A resolves `Svc` to A.Svc even though B.Svc also     exist, A local `Other x` shadowing a field `Server x` makes the name's type     conflic, `var x = Compute();` (untypable) redeclaring a typed field poisons the     name: (+60 more)

### Community 20 - "test_codebuddy.py"
Cohesion: 0.05
Nodes (66): codebuddy_install(), codebuddy_uninstall(), Install the graphify skill and CODEBUDDY.md section for CodeBuddy., Remove the graphify skill tree (SKILL.md + references/) and the CODEBUDDY.md sec, _codebuddy_install_user(), _codebuddy_md_path(), Tests for graphify codebuddy install / uninstall commands., The installed hook must include Read|Glob matcher for file-read interception. (+58 more)

### Community 21 - "test_chunking.py"
Cohesion: 0.04
Nodes (66): BaseException, extract_corpus_parallel(), _extract_with_adaptive_retry(), _looks_like_context_exceeded(), _merge_into(), _pack_chunks_by_tokens(), Greedily pack files/slices into chunks that fit a token budget.      Units are f, Heuristically classify an exception as a context-window overflow.      Different (+58 more)

### Community 22 - "test_dotnet.py"
Cohesion: 0.05
Nodes (65): extract_sln(), extract_slnx(), extract_xaml(), _project_xml_is_safe(), Reject XML that declares DTDs or entities.      Stdlib ``xml.etree.ElementTree``, Extract projects and inter-project dependencies from a .sln file., Extract projects and inter-project dependencies from a .slnx file.      .slnx is, Extract WPF/XAML structure, bindings, x:Class, and event handler references. (+57 more)

### Community 23 - "test_pascal.py"
Cohesion: 0.07
Nodes (60): extract_delphi_form(), extract_lazarus_form(), extract_lazarus_package(), extract_pascal(), Extract units, classes, procedures, uses-imports, and calls from Pascal/Delphi f, Extract component hierarchy from Lazarus .lfm form files.      .lfm is a text-ba, Extract component hierarchy from Delphi .dfm form files.      .dfm files come in, Extract package metadata from Lazarus .lpk package files (XML format).      .lpk (+52 more)

### Community 24 - "to_wiki"
Cohesion: 0.06
Nodes (63): _community_article(), _cross_community_links(), _god_node_article(), _index_md(), _md_link(), Path, Make a label safe for use as a filename across platforms.      Substitutes chara, Generate a Wikipedia-style wiki from the graph.      Writes:       - index.md (+55 more)

### Community 25 - "test_llm_backends.py"
Cohesion: 0.05
Nodes (62): _call_openai_compat(), _model_requires_default_temperature(), True if `model` is a reasoning model that rejects an explicit temperature., Resolve the temperature to send, honouring GRAPHIFY_LLM_TEMPERATURE.      Preced, Detect a successful HTTP response that yielded no usable extraction.      A loca, Call any OpenAI-compatible API (Kimi, OpenAI, etc.) and return parsed JSON., _resolve_temperature(), _response_is_hollow() (+54 more)

### Community 26 - "test_lsp_resolve.py"
Cohesion: 0.09
Nodes (50): callee_name(), _caller_callee_keys(), confine(), _definition_site(), find_column(), format_summary(), LspClient, LspError (+42 more)

### Community 27 - "make_id"
Cohesion: 0.05
Nodes (58): graph_has_legacy_ids(), _old_file_stems(), Path, Pre-migration stem forms a semantic fragment may have used for ``rel``.      Ord, Re-derive non-AST node ids from ``source_file`` using the canonical     full-pat, Whether a loaded graph still uses pre-#1504 node IDs (parent-dir / filename, _semantic_id_remap(), _extract_pascal_regex() (+50 more)

### Community 28 - "Graph"
Cohesion: 0.08
Nodes (54): Heuristic dead-code scan: function nodes unreachable from any recognized entry p, unreachable_functions(), _find_node_core(), _find_node_tied_group(), _find_node_tiers(), Same matching as `_find_node_core`, but returns each precedence tier     (source, Return node IDs whose label or ID matches the search term (diacritic-insensitive, Nodes tied for the top precedence tier `_find_node` would resolve to -     i.e. (+46 more)

### Community 29 - "_labels"
Cohesion: 0.04
Nodes (60): extract_csproj(), extract_groovy(), extract_kotlin(), Extract packages, project refs, and target framework from a .csproj/.fsproj/.vbp, Extract classes, methods, constructors, and imports from a .groovy/.gradle file., Extract classes, objects, functions, and imports from a .kt/.kts file., extract_apex(), Path (+52 more)

### Community 30 - "test_js_import_resolution.py"
Cohesion: 0.15
Nodes (59): _file_node_id(), File-level node ID matching the skill.md spec: ``{parent_dir}_{stem}`` —     one, _extract_for(), _has_edge(), _has_no_symbol_to_symbol_edge(), _has_symbol_edge(), _has_symbol_to_symbol_edge(), Path (+51 more)

### Community 31 - "test_fuzzy_fallback.py"
Cohesion: 0.06
Nodes (59): _apply_vocabulary_corrections(), _correct_term(), _damerau_levenshtein(), _find_node(), _fuzzy_substring_distance(), _fuzzy_substring_seeds(), _get_vocabulary(), _find_node_core, with one vocabulary-correction retry (P5) if the     label matc (+51 more)

### Community 32 - "test_semantic_cleanup.py"
Cohesion: 0.06
Nodes (56): _normalize_hyperedge_members(), Canonicalize a hyperedge's member list onto the `nodes` key, in place.      If `, _append_rationale_attr(), _is_sentence_like_rationale_label(), load_validated_semantic_fragment(), Path, Load and validate a semantic chunk, rejecting oversize files before parsing., Clean up a semantic extraction fragment in-place.      Operations:     1. Remove (+48 more)

### Community 33 - "test_multigraph_diagnostics.py"
Cohesion: 0.09
Nodes (55): _canonical_edge(), _count_extra(), diagnose_extraction(), diagnose_file(), _edge_list(), _exact_signature(), format_diagnostic_json(), format_diagnostic_report() (+47 more)

### Community 34 - "llm.py"
Cohesion: 0.06
Nodes (54): _anthropic_content(), _azure_client(), _backend_env_keys(), _bedrock_content(), _bedrock_inference_config(), _call_azure(), _call_bedrock(), _call_claude() (+46 more)

### Community 35 - "build_from_json"
Cohesion: 0.06
Nodes (56): build_from_json(), dedupe_edges(), edge_data(), edge_datas(), Return one edge attribute dict for (u, v), tolerating MultiGraph.      For Multi, Return every edge attribute dict for (u, v); always a list., Collapse exact parallel edges by ``(source, target, relation)``, keeping the, Build a NetworkX graph from an extraction dict.      directed=True produces a Di (+48 more)

### Community 36 - "Changelog"
Cohesion: 0.04
Nodes (55): [0.14.0] - 2026-07-02, [0.20.0] - 2026-07-24, [0.24.3] - 2026-08-24, [0.26.1] - 2026-10-03, [0.3.12] - 2026-04-08, [0.3.13] - 2026-04-08, [0.3.14] - 2026-04-08, [0.4.11] - 2026-04-13 (+47 more)

### Community 37 - "test_watch.py"
Cohesion: 0.04
Nodes (50): Spawn a detached, non-blocking background rebuild for ``project_root``.      For, trigger_background_update(), Tests for watch.py - file watcher helpers (no watchdog required)., _merge_changed_paths preserves first-seen order and drops dupes., Verify that _rebuild_code reads and applies config settings from pyproject.toml., A graph.html left over from an earlier run (built without --no-viz) must be, _TRIGGER_BODY is passed as a subprocess -c argument, not imported - a     syntax, Paths travel as argv, not templated into the child's source text, so a     path (+42 more)

### Community 38 - "test_devin.py"
Cohesion: 0.05
Nodes (51): _devin_rules_install(), Write .windsurf/rules/graphify.md for always-on Devin context., _devin_install_user(), Tests for graphify devin install / uninstall commands., The rules file installed by devin must use query-first policy., Installing rules twice does not change content and prints 'no change'., Project-scope install prints a git add hint covering .devin/ and .windsurf/., User-scope uninstall removes the skill file. (+43 more)

### Community 39 - "README.ja-JP.md"
Cohesion: 0.05
Nodes (40): Co získáte, Instalace, Jak to funguje, Použití, Soukromí, Brug, Hvad du får, Installation (+32 more)

### Community 40 - "_edge_labels"
Cohesion: 0.05
Nodes (51): extract_java(), extract_scala(), extract_verilog(), Extract classes, interfaces, methods, constructors, and imports from a .java fil, Extract classes, objects, functions, and imports from a .scala file., Extract modules, functions, tasks, package imports, instantiations, and     Syst, _edge_labels(), _node_by_label() (+43 more)

### Community 41 - "test_install_references.py"
Cohesion: 0.05
Nodes (48): _check_skill_version(), Warn if the installed skill is from an older graphify version., Parse a version string into a comparable integer tuple (``0.9.2`` -> ``(0, 9, 2), _version_tuple(), _build_wheel_names(), fake_bundle(), _first_unbuilt_progressive_host(), _install() (+40 more)

### Community 42 - "test_reflect.py"
Cohesion: 0.09
Nodes (49): aggregate_lessons(), Aggregate parsed memory docs into a deterministic lessons structure.      ``now`, Render the aggregate into the deterministic LESSONS.md markdown body., render_lessons_md(), _days_before(), _doc(), Tests for `graphify reflect` and the work-memory reflection layer.  `graphify re, Corroboration (k>=2) + sign decide the bucket, not raw frequency:     A is usefu (+41 more)

### Community 43 - "deduplicate_entities"
Cohesion: 0.07
Nodes (47): build(), Merge multiple extraction results into one graph.      directed=True produces a, deduplicate_entities(), Deduplicate near-identical entities in a knowledge graph.      Args:         nod, build() passes root through to build_from_json (#932)., test_build_relativizes_absolute_source_file(), _make_nodes(), Tests for graphify/dedup.py entity deduplication pipeline. (+39 more)

### Community 44 - "test_security.py"
Cohesion: 0.07
Nodes (46): check_graph_file_size_cap(), Any, Path, Resolve *path* and verify it stays inside *base*.      *base* defaults to the `g, Reject *path* if its size exceeds the configured graph-file cap.      Protects c, Return a control-character-free, HTML-escaped, bounded string., Sanitize a metadata value while preserving simple JSON-compatible types., Sanitize metadata keys and values before graph export.      Metadata is less con (+38 more)

### Community 45 - "extract_yaml"
Cohesion: 0.08
Nodes (44): _is_value_coupling_service_verb(), _is_value_coupling_ui_file(), P15 (opt-in): emit low-confidence `shares_value:<v>` edges between file     node, _resolve_value_coupling(), extract_yaml(), _is_identifier_leaf(), Path, _pf() (+36 more)

### Community 46 - "test_indirect_dispatch.py"
Cohesion: 0.10
Nodes (44): _build(), _extract(), _extract_dir(), _extract_js_dir(), Indirect dispatch edges.  A function passed BY NAME as a call argument (`executo, No recall regression: a real module fn passed by name still emits an edge., Regression: when the scan root relativizes node ids (cache_root == project     r, Soundness carries across files: an imported name shadowed by a parameter     is (+36 more)

### Community 47 - "test_cypher.py"
Cohesion: 0.10
Nodes (43): parse_cypher(), Run a read-only Cypher-subset query on `G`.      `limit` is the default row limi, Parse a Cypher-subset query; raises CypherError on anything unsupported., run_cypher(), _big_graph(), _col(), G(), _graph() (+35 more)

### Community 48 - "extract_python"
Cohesion: 0.07
Nodes (43): extract_python(), Extract classes, functions, and imports from a .py file via tree-sitter AST., All edge sources must reference a known node (targets may be external imports)., contains / method / inherits / imports edges must always be EXTRACTED., Call-graph pass must produce INFERRED calls edges., AST-resolved call edges are deterministic and should be EXTRACTED/1.0., run_analysis() calls compute_score() - must appear as a calls edge., Analyzer.process() calls run_analysis() - cross class→function calls edge. (+35 more)

### Community 49 - "extract_files_direct"
Cohesion: 0.08
Nodes (42): detect_backend(), extract_files_direct(), _get_backend_api_key(), _ollama_host_is_link_local_or_metadata(), Extract semantic nodes/edges from a list of files using the given backend., True if *host* is, or resolves to, a link-local / cloud-metadata address.      R, Warn if OLLAMA_BASE_URL looks unsafe; hard-block link-local/metadata (F3)., Return the name of whichever backend has an API key set, or None.      Priority: (+34 more)

### Community 50 - "parse_and_execute_pattern"
Cohesion: 0.09
Nodes (42): _apply_where_op(), parse_and_execute_pattern(), _parse_varlen(), _parse_where_clauses(), PatternQueryError, Any, Execute a Cypher-like pattern query against G.      Examples:         MATCH (a:f, Parse a `*`, `*N`, `*N..M`, `*..M`, or `*N..` quantifier into (min, max) hops. (+34 more)

### Community 51 - "reflect.py"
Cohesion: 0.09
Nodes (43): _build_id_label_maps(), build_learning_overlay(), _code_fingerprint(), _content_hash(), _decay(), _dedupe_by_question(), _empty_bucket(), _finalize_sources() (+35 more)

### Community 52 - "gen.py"
Cohesion: 0.05
Nodes (42): Namespace, On a shallow checkout (no origin/v8) the validators skip with exit 0.      CI se, test_git_show_validators_skip_cleanly_without_origin_v8(), bless(), _enum_lines(), _expected_path(), _is_cache_unlink_fix_line(), _is_chunk_cleanup_line() (+34 more)

### Community 53 - "generate"
Cohesion: 0.09
Nodes (39): _partition(), Community detection on NetworkX graphs. Uses Leiden (graspologic) if available,, Context manager to suppress stdout/stderr during library calls.      graspologic, Run community detection. Returns {node_id: community_id}.      Tries Leiden (gra, Run a second Leiden pass on a community subgraph to split it further., score_all(), _split_community(), _suppress_output() (+31 more)

### Community 54 - "test_file_slice.py"
Cohesion: 0.10
Nodes (41): _best_cut(), bisect_slice(), expand_oversized_files(), FileSlice, is_splittable_text(), Path, Intra-file slicing for oversized text documents (#1369).  The extraction packer, Replace each oversized splittable-text file with a list of ``FileSlice``s. (+33 more)

### Community 55 - "test_skillgen.py"
Cohesion: 0.07
Nodes (42): _platform_artifacts(), Tests for the tools/skillgen generator and the claude lean-core split.  skillgen, windows: graphify name (must match the .claude/skills/graphify/ install folder),, codex: spawn/wait/close_agent dispatch needing multi_agent = true., codex (was 4-value) and windows (was 5-value) now carry the superset., The extraction variant differs: codex compact, windows verbose., #1325: the unified query reference ships BOTH the vocab-expansion step and     t, No split host emits a trigger: field — not part of Agent Skills spec (#1180). (+34 more)

### Community 56 - "_score_nodes"
Cohesion: 0.06
Nodes (41): _bm25_confident_pick(), Last-resort tier: the same cross-field BM25 ranking query/explain/path     alrea, _bm25_idf(), Standard Okapi BM25 IDF (Robertson-Sparck Jones form), floored at a     small po, _score_nodes(), Regression coverage for P3 (camelCase/snake_case/kebab-case tokenization) ground, run-tests-btn / hint-btn / next-lesson-btn all end in "-btn" — only     "run" +, progress-bar-fill vs progress-label share "progress" — "bar" and     "fill" must (+33 more)

### Community 57 - "test_global_graph.py"
Cohesion: 0.11
Nodes (40): prefix_graph_for_global(), prune_repo_from_graph(), Return a copy of G with all node IDs prefixed with repo_tag::.      Labels are p, Remove all nodes tagged with repo_tag from G in-place. Returns count removed., _file_hash(), global_add(), global_list(), global_remove() (+32 more)

### Community 58 - "extract_objc"
Cohesion: 0.05
Nodes (42): extract_objc(), Extract interfaces, implementations, protocols, methods, and imports from .m/.mm, `@protocol Derived <Base>` must emit an implements edge Derived->Base.     Proto, `[self speak]` inside Dog.fetch must produce a calls edge. The method-body     s, `+ (…)shared` is a class method and must be labeled +shared, not -shared (#1475), A compound message `[self a:x b:y]` resolves to the compound method def (#1475)., `NSArray<Product *> *` must reference the element type Product (and the     cont, `@import Foundation;` / `@import UIKit.UIView;` produce imports edges (#1475). (+34 more)

### Community 59 - "extract_markdown"
Cohesion: 0.06
Nodes (40): extract_markdown(), _normalize_frontmatter_list(), _parse_yaml_frontmatter(), Parse leading YAML frontmatter delimited by ^---$ lines.      Returns (frontmatt, Normalize frontmatter scalar or list into a list of non-empty strings., Extract structural nodes and edges from a Markdown file.      Produces nodes for, Path, [TS-MD-005] Markdown without frontmatter continues to parse headings and links a (+32 more)

### Community 60 - "test_mcp_ingest.py"
Cohesion: 0.11
Nodes (36): extract_mcp_config(), Path, Parse an MCP config file into Graphify nodes and edges.      Behaviour matches o, _label_by_kind(), Path, Tests for graphify.mcp_ingest — MCP config file extraction., _relations(), test_dispatch_does_not_reroute_generic_json() (+28 more)

### Community 61 - "validate_extraction"
Cohesion: 0.09
Nodes (36): introspect_postgres(), _quote_ident(), Connect to PostgreSQL, reconstruct DDL, and extract via extract_sql()., Double-quote a PostgreSQL identifier, escaping embedded double-quotes., assert_valid(), Validate an extraction JSON dict against the graphify schema.     Returns a list, Raise ValueError with all errors if extraction is invalid., validate_extraction() (+28 more)

### Community 62 - "_search_tokens"
Cohesion: 0.07
Nodes (40): _get_bm25_corpus(), _get_trigram_index(), _node_search_text(), Split text into word tokens on punctuation/underscore/hyphen *and*     camelCase, Character trigrams of `text`; for <3-char text the whole string is the key., Concatenate every field _score_nodes / _find_node match a query against., Lazily build and cache a trigram -> node-position postings map on the graph., Node IDs whose text could contain any `needle` as a substring, via the     trigr (+32 more)

### Community 63 - "ingest_scip_json"
Cohesion: 0.05
Nodes (40): ingest_scip_json(), Convert a SCIP-style JSON document into Graphify nodes and edges.      Parameter, Result passes Graphify's validate_extraction and build_from_json keeps the edges, A symbol with `relationships: None` ingests without error and emits no edges., A symbol with `kind` as a non-string falls back to 'unknown'., `display_name` as a non-string falls back to the symbol suffix., `documentation` first entry that isn't a string yields empty description (not cr, A non-dict entry in `documents` is silently skipped. (+32 more)

### Community 64 - "test_cli_export.py"
Cohesion: 0.11
Nodes (39): _make_graph(), CompletedProcess, Path, Integration tests for graphify export subcommands and CLI commands.  Each test b, #1423: `graphify extract` honours GRAPHIFY_OUT for where it WRITES, not only, cluster-only must not crash with FileNotFoundError when graphify-out/ is absent, Build a minimal graph.json + analysis/labels files in tmp_path/graphify-out/., cluster-only must invoke remap_communities_to_previous so the existing     .grap (+31 more)

### Community 65 - "test_path_cli.py"
Cohesion: 0.08
Nodes (39): _arrow_line(), _diamond_graph(), _flipped_marker_graph(), P16: --target-path narrows a duplicate label to one dir, so the query     resolv, A shorter 2-hop route through a builtin-primitive hub ("Int") and a     longer 3, The shorter route goes through a builtin-primitive node ("Int") - path     must, A project-specific type ("CustomHubType") that is NOT in     _BUILTIN_NOISE_LABE, A structurally over-connected node with NO builtin-noise-label match     (a proj (+31 more)

### Community 66 - "sample.swift"
Cohesion: 0.06
Nodes (29): Bool, Foundation, NSObject, NSString, SampleDelegate, Animal, -initWithName, -speak (+21 more)

### Community 67 - "analyze.py"
Cohesion: 0.08
Nodes (37): _cross_community_surprises(), cross_cutting_nodes(), _cross_file_surprises(), _is_builtin_noise_label(), _is_concept_node(), _is_file_node(), _is_json_key_node(), _node_community_map() (+29 more)

### Community 68 - "_get_extractor"
Cohesion: 0.07
Nodes (32): _get_extractor(), _is_cpp_header(), _is_objc_header(), Any, Whether a `.h` file is Objective-C rather than C/C++ (#1475).      `.h` is share, Whether a `.h` file is C++ rather than plain C (#1547).      Mirrors `_is_objc_h, Return the correct extractor function for a file, or None if unsupported., Resolve an `exports` map value (string or condition object) to a     relative ta (+24 more)

### Community 69 - "test_image_vision.py"
Cohesion: 0.09
Nodes (38): _backend_supports_vision(), _build_image_refs(), _custom_providers_path(), _file_to_text(), _is_vision_image(), _load_custom_providers(), _partition_semantic_files(), Path (+30 more)

### Community 70 - "_query_graph_text"
Cohesion: 0.06
Nodes (39): _query_graph_text(), End-to-end: a compound-span typo longer than the n-gram window must     still re, test_query_graph_text_falls_through_to_bitap_tier_when_ngram_insufficient(), _make_callers_graph(), _make_noisy_graph(), _make_path_scope_graph(), semantic_fusion="off" must never even consult the embedding index,     regardles, FooBarService error handling' should expand from FooBarService,     not from err (+31 more)

### Community 71 - "extract_dm"
Cohesion: 0.06
Nodes (38): extract_c(), extract_dm(), Extract types, procs, includes, and calls from a .dm/.dme file., Extract functions and includes from a .c/.h file., _calls(), _edges_with_relation(), Regression test for the call-walker `simple_identifier` /     `identifier` renam, test_c_call_edges_have_call_context() (+30 more)

### Community 72 - "test_hooks.py"
Cohesion: 0.10
Nodes (37): _hooks_dir(), install(), Return the git hooks directory, respecting core.hooksPath if set (e.g. Husky)., Install graphify post-commit and post-checkout hooks in the nearest git repo., Check if graphify hooks are installed., status(), _make_git_repo(), Tests for hooks.py - git hook install/uninstall. (+29 more)

### Community 73 - "test_transcribe.py"
Cohesion: 0.08
Nodes (35): build_whisper_prompt(), download_audio(), _get_whisper(), _get_yt_dlp(), is_url(), _model_name(), Path, Transcribe a video/audio file or URL to a .txt transcript.      If video_path is (+27 more)

### Community 74 - "query.py"
Cohesion: 0.09
Nodes (35): _best_anchor_neighbor(), find_path_with_disambiguation(), _infer_context_filters(), _is_concept_node_for_seeding(), _is_prose_node_for_seeding(), _normalize_context_filters(), Query engine: tokenize -> score -> seed -> traverse -> render.  Extracted from s, Best-effort file anchor for a concept node that has neither a     source_file no (+27 more)

### Community 75 - "_rebuild_code"
Cohesion: 0.10
Nodes (35): _norm_source_file(), Normalize path separators and relativize absolute paths.      Converts backslash, load_learning_for_report(), Assemble the report's work-memory inputs from sibling artifacts.      Reads the, Condense a full GRAPH_REPORT.md into a ~50-line digest for auto-loading     into, summarize(), _apply_resource_limits(), _canonical_graph_for_compare() (+27 more)

### Community 76 - "test_labeling.py"
Cohesion: 0.12
Nodes (33): _community_label_lines(), generate_community_labels(), label_communities(), _placeholder_community_labels(), One prompt line per community (largest first), sampling up to ``top_k``     repr, Return a complete ``{cid: name}`` map using ``backend`` for naming.      Communi, CLI entry point: resolve a backend, name communities, and degrade to     ``Commu, _graph() (+25 more)

### Community 77 - "test_serve_http.py"
Cohesion: 0.15
Nodes (35): _build_http_app(), Build the Starlette ASGI app for the Streamable HTTP transport.      Split out f, TestClient, _call_tool(), _client(), _graph_file(), _init_session(), _project_with_graph() (+27 more)

### Community 78 - "test_scip_ingest.py"
Cohesion: 0.06
Nodes (35): Comprehensive tests for graphify.scip_ingest., Symbol ending with '#' and no display_name must produce a non-empty label., Cross-document relationship resolves to the target document's node id., When a target symbol is defined in exactly ONE other document, the edge     stil, When a target symbol is defined in 2+ documents AND the source is in a     third, Control characters in SCIP description must not survive into the graph., SCIP relationship payloads embedded in edge metadata must be sanitized., When occurrences key is missing entirely, falls back to empty source_location. (+27 more)

### Community 79 - "test_benchmark.py"
Cohesion: 0.14
Nodes (33): _estimate_tokens(), _hr(), print_benchmark(), _query_subgraph_tokens(), Token-reduction benchmark - measures how much context graphify saves vs naive fu, Print a human-readable benchmark report., Return unicode_char if stdout can encode it, else ascii_fallback.      Windows c, Horizontal rule that survives non-UTF-8 stdout (e.g. Windows cp1252 console). (+25 more)

### Community 80 - "_call_claude_cli"
Cohesion: 0.08
Nodes (33): _call_claude_cli(), estimate_cost(), Call Claude via the locally-installed Claude Code CLI (`claude -p`).      Routes, Estimate USD cost for a given token count using published pricing., Honour GRAPHIFY_API_TIMEOUT env var override, else use default (seconds)., _resolve_api_timeout(), Tests for the `claude-cli` backend (#855/#856).  Mocks subprocess.run + shutil.w, On Windows, npm installs `claude.ps1` alongside `claude.cmd`.     `CreateProcess (+25 more)

### Community 81 - "test_querylog.py"
Cohesion: 0.11
Nodes (33): _log_path(), log_query(), _log_responses(), nodes_from_result(), Any, Path, Query logging for graphify — append-only JSONL, fail-silent., Append one JSONL record to the query log. Never raises. (+25 more)

### Community 82 - "/graphify"
Cohesion: 0.06
Nodes (32): For always-on context in Devin sessions, For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For --update (incremental re-extraction) (+24 more)

### Community 83 - "symbol_resolution.py"
Cohesion: 0.09
Nodes (32): build_python_symbol_index(), existing_edge_pairs(), _file_node_id_for_path(), find_unique_python_symbol(), ImportedSymbol, _module_stem(), _node_source_stem(), parse_python_import_aliases() (+24 more)

### Community 84 - "/graphify"
Cohesion: 0.06
Nodes (32): For always-on context in Devin sessions, For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For --update (incremental re-extraction) (+24 more)

### Community 85 - "/graphify"
Cohesion: 0.06
Nodes (32): For always-on context in Devin sessions, For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For --update (incremental re-extraction) (+24 more)

### Community 86 - "HttpClient"
Cohesion: 0.10
Nodes (25): __global__, AuthedHttpClient, token_, Connection, resource, string, T, HttpClient (+17 more)

### Community 87 - "dedup.py"
Cohesion: 0.09
Nodes (27): _crossfile_fileanchored_blocked(), _is_code(), _is_variant_pair(), _llm_tiebreak(), _make_minhash(), _numeric_tokens_differ(), _pick_winner(), Entity deduplication pipeline for graphify knowledge graphs.  Pipeline: exact no (+19 more)

### Community 88 - "CsharpNameResolver"
Cohesion: 0.10
Nodes (22): _find_body(), LanguageConfig, Get the name from a node using config.name_field, falling back to child types., Find the body node using config.body_field, falling back to child types., _resolve_name(), _build_csharp_type_def_index(), CsharpNameResolver, _merge_csharp_partial_class_nodes() (+14 more)

### Community 89 - "test_manifest_ingest.py"
Cohesion: 0.11
Nodes (28): _coerce_deps(), extract_package_manifest(), is_package_manifest_path(), _parse_apm(), _parse_apm_fallback(), _parse_pyproject(), _pep508_name(), _pkg_id() (+20 more)

### Community 90 - "prs.py"
Cohesion: 0.20
Nodes (29): attach_graph_impact(), bold(), _c(), _ci_icon(), cmd_prs(), cyan(), dim(), fetch_prs() (+21 more)

### Community 91 - "test_symbol_resolution.py"
Cohesion: 0.10
Nodes (31): Resolve Bash source/import edges and source-backed function calls.      Defensiv, resolve_bash_source_edges(), Path, Tests for graphify.symbol_resolution., Strong regression for #cycle-2.7-Codex-v2: monkeypatch the alias parser     so t, When a callee function is defined in multiple sourced files, skip it., Non-bash raw_calls inside sourced-file per_file entries are ignored., A `bash_sources` entry missing `target_path` must not raise KeyError. (+23 more)

### Community 92 - "README.fa-IR.md"
Cohesion: 0.06
Nodes (29): Adding a new language extractor, Architecture, Confidence labels, Extraction output schema, Module responsibilities, Pipeline, Reading aids, Security (+21 more)

### Community 93 - "RuntimeError"
Cohesion: 0.11
Nodes (30): load_graph(), apply_to_stops(), _build_prompt(), collect_items(), community_key(), describe_main(), descriptions_path(), _excerpt() (+22 more)

### Community 94 - "build_merge"
Cohesion: 0.10
Nodes (30): build_merge(), _infer_merge_root(), Best-effort scan root for relativizing paths in build_merge when the caller, Load existing graph.json, merge new chunks into it, and save back.      Re-extra, _he_ids(), Path, Incremental --update: hyperedge preservation (#1574) and root-less prune (#1571), A symlinked scan root (macOS /var -> /private/var, symlinked home/worktree) (+22 more)

### Community 95 - "test_minhash.py"
Cohesion: 0.12
Nodes (23): _lsh_integrate(), _mh_coeffs(), MinHash, MinHashLSH, _optimal_lsh_params(), MinHash + band-LSH — datasketch-compatible drop-in (no scipy).  datasketch.lsh h, MinHash sketch — same API as datasketch.MinHash for the subset used here., Numerical integration — replaces scipy.integrate.quad for LSH param search. (+15 more)

### Community 96 - "/graphify"
Cohesion: 0.06
Nodes (30): For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For native CLAUDE.md integration, For --update (incremental re-extraction) (+22 more)

### Community 97 - "test_describe.py"
Cohesion: 0.12
Nodes (26): build_tour(), _community_of(), format_tour(), _is_test_path(), Return up to max_steps tour stops, ordered from entry points toward foundations., _cache(), _cli_out(), _describe() (+18 more)

### Community 98 - "/graphify"
Cohesion: 0.06
Nodes (30): For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For native CLAUDE.md integration, For --update (incremental re-extraction) (+22 more)

### Community 99 - "/graphify"
Cohesion: 0.06
Nodes (30): For --cluster-only, For git commit hook, For /graphify add, For /graphify explain, For /graphify path, For /graphify query, For native CLAUDE.md integration, For --update (incremental re-extraction) (+22 more)

### Community 100 - "_Exec"
Cohesion: 0.19
Nodes (10): _eq(), _Exec, _hkey(), _is_num(), NodePat, Any, A bound pattern variable: tag n (node id), e (edge index) or p (tuple of edge in, _Ref (+2 more)

### Community 101 - "test_hypergraph.py"
Cohesion: 0.09
Nodes (29): attach_hyperedges(), Store hyperedges in the graph's metadata dict., _alias_extraction(), _make_report(), Tests for hyperedge support in graphify., Write graph.json then reload it - hyperedges must survive., Three hyperedges, one per member-key spelling: nodes / members / node_ids., Alias normalization must run BEFORE the semantic id-remap loop so a     `members (+21 more)

### Community 102 - "TestSubprocessEncoding"
Cohesion: 0.07
Nodes (18): Regression tests for UnicodeEncodeError on Windows cp1252 console.  On Windows w, Writing a file with → ✅ ≥ then passing its content through         _call_claude_, _call_llm with backend='claude-cli' must also use encoding='utf-8'., extract_corpus_parallel must surface chunk failures loudly — either via     non-, When chunks fail, extract_corpus_parallel must record failed_chunks > 0, A summary line must appear on stderr when ≥1 chunk fails., When all chunks succeed, failed_chunks must be 0 and no failure         summary, Exercises the same code path as the rsl-siege-manager reproduction     without r (+10 more)

### Community 103 - "test_indirect_call_function_expression_shadow.py"
Cohesion: 0.12
Nodes (29): _extract_js_dir(), _indirect(), Function expressions (including generator FEs and TSX) must shadow indirect_call, The bindings are scoped to the expression: a same-named module callable     refe, Two function expressions in one initializer are SEPARATE scopes: the     first o, Widening the shadow set must not blanket-suppress inside the body: an     unshad, Adding a type to `function_boundary_types` must not change WHERE calls are     a, The TS config carries its own copy of the set; both were missing the type. (+21 more)

### Community 104 - "test_affected_cli.py"
Cohesion: 0.10
Nodes (28): _parse_git_diff_hunks(), Parse `git diff --unified=0` output into {file: [(start_line, end_line), ...]}, resolve_seed(), #2309: affected must recover caller/callee direction from _src/_tgt markers, graphify's `extract` writes graph.json with an "edges" key (not networkx's     d, A trailing path separator must not change the match (parity with explain's     _, Several nodes share a source_file but none is the L1 file node and none's     ba, A bare --relation filter (no ':') must also match P15-style parameterized     re (+20 more)

### Community 105 - "write_callflow_html"
Cohesion: 0.09
Nodes (28): build_section_node_map(), CallflowOptions, classify_edges(), detect_lang(), html_comment_text(), infer_project_name(), load_labels(), load_report() (+20 more)

### Community 106 - "_key"
Cohesion: 0.08
Nodes (27): _is_type_like_definition(), _lang_family(), _lang_is_case_insensitive(), _merge_swift_extensions(), _node_label_key(), True when the file's language resolves identifiers case-insensitively (#1581)., Interop family of the file's language, or None when unknown/not code., Map unresolved no-source stubs to a unique real definition with the same label. (+19 more)

### Community 107 - "check_for_update"
Cohesion: 0.14
Nodes (27): check_for_update(), _is_newer(), _latest_version(), Self-update check for the graphify CLI.  PyPI-backed sibling of the npm-based ``, Best-effort, non-fatal: warn (and optionally auto-upgrade) if PyPI has a     new, Parse a dotted version string into a comparable integer tuple.      Duplicated (, _read_config(), _resolve_auto_update() (+19 more)

### Community 109 - "claude_install"
Cohesion: 0.10
Nodes (27): claude_install(), Write the graphify section to the local CLAUDE.md., Tests for graphify claude install / uninstall commands., claude_install also writes .claude/settings.json with PreToolUse hook., Running claude_install twice does not duplicate the PreToolUse hook., Creates CLAUDE.md when none exists., claude_uninstall removes the PreToolUse hook from settings.json., Written section includes the three rules. (+19 more)

### Community 110 - "test_prs.py"
Cohesion: 0.13
Nodes (12): build_community_labels(), _classify(), format_prs_text(), Plain-text PR summary for MCP output (no ANSI)., Return {community_id: [top_labels]} extracted from graph node data., make_pr(), datetime, Tests for graphify/prs.py. (+4 more)

### Community 111 - "_make_symbol_doc"
Cohesion: 0.07
Nodes (28): _make_symbol_doc(), Helper to build a minimal SCIP document with one symbol., is_reference → relation 'scip_ref'., is_definition → relation 'scip_def'., is_implementation → relation 'scip_impl' (takes priority over is_definition)., is_type_definition → relation 'scip_typed'., Implementation > TypeDefinition > Definition > Reference., When none of is_* flags are set, relation defaults to 'scip_ref'. (+20 more)

### Community 112 - "render"
Cohesion: 0.09
Nodes (26): Every platform now carries one unified frontmatter description, byte for byte., aider and devin render one inline body, no split and no references dir., The four #1392 data-loss/correctness fixes are present in both monoliths.      T, devin renders inline, so its 4+-field frontmatter is preserved verbatim., The agents skill body is amp's body verbatim (it re-homes amp's bundle).      Th, test_agents_body_matches_amp_modulo_hooks_wording(), test_descriptions_are_unified(), test_devin_keeps_its_multi_field_frontmatter() (+18 more)

### Community 113 - "graphify.toml"
Cohesion: 0.08
Nodes (18): no_viz, Tests for ANTHROPIC_BASE_URL / ANTHROPIC_MODEL overrides on the claude backend., Resource-cap guards for parsing untrusted office/PDF files (F2).  .docx/.xlsx ar, A tiny file that expands far past the ratio threshold is rejected., The live converters bail out (return "") on a bomb before parsing., A normal multi-member office zip passes the streaming-ceiling pass., With a low decompressed cap, content whose actual bytes exceed it is rejected., A PDF larger than the raw cap is skipped before pypdf opens it. (+10 more)

### Community 114 - "test_dataflow.py"
Cohesion: 0.23
Nodes (26): format_flow(), _prune(), Any, Pattern, trace_flow(), _calls(), _project(), Path (+18 more)

### Community 115 - "_load_graphifyignore"
Cohesion: 0.10
Nodes (27): _is_ignored(), _is_noise_dir(), _load_graphifyignore(), Return True if this directory name looks like a venv, cache, or dep dir., Read .graphifyignore files and return (anchor_dir, pattern) pairs.      Patterns, Return True if the path should be ignored per .graphifyignore patterns.      Use, _xaml_csharp_class_nodes(), A ! re-include cannot un-ignore a file whose parent dir is excluded (#882). (+19 more)

### Community 116 - "_relations"
Cohesion: 0.09
Nodes (27): extract_php(), Extract classes, functions, methods, namespace uses, and calls from a .php file., Module-level arrow functions must still emit a node and capture their calls (#10, _relations(), test_java_finds_imports(), test_js_module_level_arrow_produces_node_and_call_edges(), test_php_config_helper_target_matches_first_segment(), test_php_constructor_property_promotion_contexts() (+19 more)

### Community 117 - "paths.py"
Cohesion: 0.11
Nodes (24): _atomic_replace(), out_path(), Path, Single source of truth for the graphify output-directory name.  The output direc, A path inside the configured output dir, e.g. ``out_path("cache")``.      ``Path, Atomically replace ``path`` with content written by ``write_fn(f)``.      Writes, Atomically write ``text`` (UTF-8) to ``path``. See :func:`_atomic_replace`., Atomically write ``obj`` as JSON to ``path``, streaming the encode into the (+16 more)

### Community 118 - "scip_ingest.py"
Cohesion: 0.11
Nodes (26): _build_scip_metadata(), _coerce_str(), _emit_relationships(), _emit_symbol_node(), _first_occurrence_line(), _is_true(), Any, scip_ingest.py — SCIP JSON ingestion (simplified subset).  Reads a simplified SC (+18 more)

### Community 119 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (26): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+18 more)

### Community 120 - "README.md"
Cohesion: 0.07
Nodes (26): Common commands, Credits, Cypher subset (`graphify cypher`), Development setup, Environment variables, Full command reference, Git workflow, Ignoring files (+18 more)

### Community 121 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (26): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+18 more)

### Community 122 - "edit.py"
Cohesion: 0.22
Nodes (25): _check_syntax(), delete_symbol(), _diff(), EditError, _eol(), _finish(), format_edit_result(), insert_after_symbol() (+17 more)

### Community 123 - "test_vue_extraction.py"
Cohesion: 0.17
Nodes (23): extract_vue(), Blank everything outside ``<script>`` bodies, keeping ``\\r``/``\\n``.      Repl, Extract imports, symbols, and type refs from a ``.vue`` SFC.      Masks the non-, _vue_mask_non_script(), Path, Tests for ``.vue`` SFC extraction.  Feeding a whole SFC to the JS grammar produc, Vue allows a classic ``<script>`` plus ``<script setup>``; both are TS., The SFC must not be parsed as one JS blob.      With the bug, a real SFC yields (+15 more)

### Community 124 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Kilo-specific rules (+17 more)

### Community 125 - "test_snippet.py"
Cohesion: 0.21
Nodes (24): format_snippet(), node_snippet(), Any, Path, Source snippets for graph nodes.  AST nodes carry ``source_location`` (start lin, Return ``{file, start, end, node_end, truncated, lines}`` for ``nid`` or None wh, Snippets for the first ``limit`` code nodes listed in a ``query`` result. File-l, _resolve() (+16 more)

### Community 126 - "search_text"
Cohesion: 0.21
Nodes (24): _clean(), _enclosing(), format_text_hits(), _graph_files(), Any, Path, Exact-text / regex search over the files the graph knows about.  Graph queries m, rel path -> absolute path, for graph source files that exist inside ``root``. (+16 more)

### Community 127 - "test_agents_platform.py"
Cohesion: 0.10
Nodes (25): Tests for the generic `agents` platform and its `skills` alias (#1432).  `graphi, `graphify uninstall --platform agents|skills` (global) clears ~/.agents/skills., `graphify uninstall --project` (no platform) removes the agents project skill, `graphify install --project --platform agents` writes ./.agents/skills and     l, `graphify agents install` is the amp-twin: skill at ~/.agents/skills PLUS a, Running `graphify agents install` twice leaves a single AGENTS.md section., `graphify skills install`/`uninstall` behaves exactly like the agents form:, `graphify install` (no platform) stays single-platform claude/windows and     ne (+17 more)

### Community 128 - "test_swift_cross_file_calls.py"
Cohesion: 0.20
Nodes (25): _edge_labels(), _extension_fixture(), _issue_fixture(), _label(), Path, #1356 cont'd: a bare method name declared 2+ times in the same type     (real Sw, Overload disambiguation must be additive: a type with only one method by a     g, #1604: `let x = Type.shared` cached into a local var, then `x.method()` on a (+17 more)

### Community 129 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (25): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Kilo-specific rules (+17 more)

### Community 130 - "callflow_html.py"
Cohesion: 0.11
Nodes (24): build_community_index(), _community_text(), derive_sections_from_communities(), generate_header(), generate_nav(), html_anchor_id(), _keyword_score(), label_for_community() (+16 more)

### Community 131 - "cypher.py"
Cohesion: 0.11
Nodes (18): _cell(), _check_regex_shape(), _compile_regex(), CypherError, CypherResult, format_table(), Pattern, Query (+10 more)

### Community 132 - "test_edit.py"
Cohesion: 0.28
Nodes (24): replace_symbol_body(), _project(), Path, Graph-guided symbol edits: replace body, insert after, rename, safe delete.  Saf, _read(), test_cli_edit_error_exits_nonzero(), test_cli_rename_dry_run_then_apply(), test_delete_is_refused_while_something_depends_on_it() (+16 more)

### Community 133 - "check_git_clone_update"
Cohesion: 0.18
Nodes (23): check_git_clone_update(), _fetch_remote_version(), _find_git_root(), _is_working_tree_dirty(), Path, Git-clone update check for the graphify CLI.  Separate track from ``update_check, Best-effort, non-fatal: never raises, never blocks a non-interactive run     for, _read_config() (+15 more)

### Community 134 - "convert_google_workspace_file"
Cohesion: 0.14
Nodes (23): convert_google_workspace_file(), _extract_file_id_from_url(), _extract_resource_key(), google_workspace_enabled(), Any, Path, Optional Google Workspace shortcut export support.  Google Drive for desktop sto, Export a Google Workspace shortcut to a Markdown sidecar.      Returns the conve (+15 more)

### Community 135 - "multigraph_compat.py"
Cohesion: 0.15
Nodes (19): _build_probe_graph(), CapabilityCheck, _check(), MultigraphCapabilityResult, _probe_duplicate_key_overwrite_semantics(), _probe_keyed_parallel_edges(), probe_multigraph_capabilities(), _probe_node_link_round_trip() (+11 more)

### Community 136 - "_query_terms"
Cohesion: 0.09
Nodes (24): _expand_synonyms(), _is_searchable(), _query_terms(), Split a query into searchable terms, drop stopwords (falling back to     the unf, True if term is non-English or an English word longer than 2 chars., Tests for lightweight query expansion (P8 semantic-search alternative). Chosen o, log in' spans a filtered stopword ('in'), so this can only work via     phrase-l, End-to-end: a node labeled purely with the target concept word must     be found (+16 more)

### Community 137 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 138 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 139 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 140 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 141 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 142 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 143 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 144 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 145 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 146 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 147 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 148 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 149 - "DataProcessor"
Cohesion: 0.13
Nodes (11): Override, ExtendedService, HttpClient, List, String, BaseProcessor, DataProcessor, Processor (+3 more)

### Community 150 - "test_read_hook.py"
Cohesion: 0.12
Nodes (22): The Read|Glob PreToolUse hook nudges toward the graph instead of raw reads.  Clo, A nudge is additionalContext only - the hook must exit 0, never deny., Reading the graph's own report must not start a go-read-the-graph loop., .astro/.vue/.svelte are real source types and must nudge (regression)., Config files must stay silent: '.json' must not match the '.js' extension., A real trailing extension must win on multi-dot names (the segment split):     a, Backslash-separated paths split on the real final segment, then its ext., An extension that sits on a directory component, not the final segment,     must (+14 more)

### Community 151 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 152 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 153 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 154 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 155 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 156 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 157 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 158 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 159 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 160 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 161 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 162 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 163 - "build.py"
Cohesion: 0.12
Nodes (21): Detect and link cross-language bridges (React Native, Expo, Swift <-> ObjC)., _read_source(), resolve_cross_language_bridges(), dedupe_nodes(), deduplicate_by_label(), _norm_label(), Collapse nodes sharing an ``id``, last-writer-wins on attributes.      Mirrors w, Canonical dedup key — Unicode-aware, preserves CJK/word characters. (+13 more)

### Community 164 - "generate_section_flowchart"
Cohesion: 0.11
Nodes (24): generate_overview_graph(), generate_section_flowchart(), group_nodes_by_file(), mermaid_class_defs(), mermaid_init(), mermaid_section_id(), node_kind(), node_label() (+16 more)

### Community 165 - "test_ruby_resolution.py"
Cohesion: 0.18
Nodes (23): extract_ruby(), Extract classes, methods, singleton methods, and calls from a .rb file., `class Sub < Base` must emit an inherits edge.      Ruby exposes the base class, test_ruby_inherits_edge(), test_ruby_no_error(), _find_raw_call(), _has_call_edge(), _labels() (+15 more)

### Community 166 - "test_install_roundtrip.py"
Cohesion: 0.10
Nodes (23): _copy_in_tmp(), fake_progressive_bundle(), _has_real_bundle(), _install_via_entrypoint(), Full per-platform install + uninstall round-trip suite.  Every platform graphify, amp's project-scope skill lands under .agents/skills, an Amp search root., Drive the high-level install() entry point with home + cwd in tmp_path., Run _copy_skill_file with home + cwd redirected into tmp_path, restoring cwd. (+15 more)

### Community 167 - "load_platforms"
Cohesion: 0.12
Nodes (24): Regression for #1461: every skill body that describes Step 3 extraction must, The committed codex/windows artifacts match a fresh render and expected/., The committed artifacts and the expected/ snapshot match a fresh render.      Th, check + audit-coverage pass for every rendered progressive host., Rendering twice yields byte-identical output (no timestamps/versions)., Generated artifacts use LF newlines and end in exactly one newline., A full render carries the always-on files; a --platform render does not., No generated artifact carries the package version string. (+16 more)

### Community 168 - "audit_coverage"
Cohesion: 0.10
Nodes (24): Every v8 heading single-homes for the cli-inline split hosts too., Every v8 heading lands in the lean core or exactly one reference., Every split host's render single-homes its own v8 body's headings., The audit baseline is the host's OWN v8 skill body, not claude's monolith., Re-inducing the trae regression (claude-flavored hooks) fails the audit.      Po, A core fragment that drops a real v8 heading fails the audit.      Guards that t, The per-host audit (the guard amp is the exact case for) passes for amp.      am, `agents` is a post-v8 platform, so its audit baseline is amp's v8 body. (+16 more)

### Community 169 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (23): For /graphify add and --watch, For /graphify query, For the commit hook and native @@HOOKS_TARGET@@ integration, For --update and --cluster-only, /graphify, Interpreter guard for subcommands, Part A - Structural extraction for code files, Part B - Semantic extraction (parallel subagents) (+15 more)

### Community 170 - "dataflow.py"
Cohesion: 0.14
Nodes (18): AST, Exception, _callee_index(), FlowError, _function(), _names(), _propagate(), Path (+10 more)

### Community 171 - "css.py"
Cohesion: 0.15
Nodes (20): extract_css(), extract_scss(), _extract_stylesheet(), Path, CSS/SCSS extractor (tree-sitter). New — .css/.scss files previously had no extra, Tests for the CSS extractor. .css files previously had no extractor at all. See, The same selector appearing both at top level and inside @media must     produce, test_extract_css_class_selector_produces_node() (+12 more)

### Community 172 - "_parse_llm_json"
Cohesion: 0.12
Nodes (22): _parse_llm_json(), Strip optional markdown fences and parse JSON. Returns empty fragment on failure, _make_envelope(), Tests for `_parse_llm_json` robustness and the `_call_claude_cli` subprocess arg, The hollow-response root cause was --append-system-prompt     layering graphify', GRAPHIFY_CLAUDE_CLI_MODEL must be forwarded to claude -p --model., Default behaviour: when the env var is not set, --model is not     added so clau, Claude often prefixes the JSON with a short preamble before the     ```json fenc (+14 more)

### Community 173 - "RFC: file-level node summaries"
Cohesion: 0.09
Nodes (20): Confidence tagging, How community detection works, How graphify works, Parallel extraction, Search & query algorithms, SHA256 cache, The graph format, The three passes (+12 more)

### Community 174 - "introspect_cargo"
Cohesion: 0.17
Nodes (20): introspect_cargo(), _load_toml(), _member_manifest_paths(), Any, Path, Cargo manifest introspection for workspace-internal crate dependencies., Return crate nodes and internal dependency edges from Cargo manifests., Real workspace: pin raw graph fields while excluding registry-only deps. (+12 more)

### Community 175 - "extract_powershell"
Cohesion: 0.09
Nodes (22): extract_powershell(), Extract functions, classes, methods, and using statements from a .ps1 file., Import-Module Foo at top level emits an imports_from edge., Import-Module -Name Bar.psm1 resolves to module stem 'bar'., Dot-source `. ./Shared.psm1` emits an imports_from edge., Dot-source `. .\\Utils.ps1` (backslash path) emits an imports_from edge., Import-Module inside a function body still produces an imports_from edge., Import-Module must not appear in raw_calls (it is an import, not a function call (+14 more)

### Community 176 - "test_onboard.py"
Cohesion: 0.18
Nodes (19): detect_layers(), layer_of_path(), Architecture-layer heuristic: group files by well-known directory names.  No LLM, Return [{name, description, node_count, files}] for layers that have nodes, larg, build_onboarding(), _communities(), Onboarding guide: one markdown page for someone new to the codebase.  Assembled, `descriptions` is the optional output of `graphify describe` (load_descriptions) (+11 more)

### Community 177 - "_check_shrink"
Cohesion: 0.12
Nodes (22): _check_shrink(), Return True (ok to proceed) or False (shrink refused).      When False, cleans u, Build a minimal graph-data dict with *n* placeholder nodes., Default case: smaller new graph + no force + no declared deletions = refuse., force=True bypasses the guard regardless of node delta., Caller declared deletions → shrink is expected → guard skipped silently., First-run case: no existing graph → guard inert., #1116: a symbol removed from a re-extracted file is a legitimate shrink —     ev (+14 more)

### Community 178 - "sample.kt"
Cohesion: 0.12
Nodes (17): MutableList, ChatType, GROUP, NORMAL, SYSTEM, Clock, createClient(), Duration (+9 more)

### Community 179 - "test_indirect_call_external_import_shadow.py"
Cohesion: 0.18
Nodes (21): _extract_js_dir(), An import from outside the corpus must shadow indirect_call resolution.  `_js_lo, A `paths` entry pointing a package at its own installed copy resolves to a     r, The counter-test that bounds the fix: an import of a file INSIDE the corpus, Widening the shadow set must not blanket-suppress a file that also happens to, The precise collision the fix must survive: a name that is BOTH imported     ext, A baseUrl-relative import ('utils/helper') must not be falsely classified     as, An unresolved non-relative import whose path matches a local file in the     dir (+13 more)

### Community 180 - "_corpus"
Cohesion: 0.13
Nodes (22): _assert_no_dangling(), _corpus(), _nodes_with_label(), Run the full extract() pipeline on fixture files (absolute, resolved     paths s, Foo.h (class) + Foo.cpp (Foo::bar def) + Main.cpp must yield exactly ONE     Foo, `void bar();` in Foo.h and `void Foo::bar() {}` in Foo.cpp must collapse to, Foo.cpp and Main.cpp `#include "Foo.h"` must resolve to the real Foo.h file, Widget.h (@interface) + Widget.m (@implementation) -> ONE Widget class node (+14 more)

### Community 181 - "README.uk-UA.md"
Cohesion: 0.10
Nodes (20): Використання графу напряму, Вимоги, Вирішення проблем, Встановлення, Додаткові пакети (опціонально), Дізнатися більше, Запуск тестів, Змусьте асистента завжди використовувати граф (+12 more)

### Community 182 - "affected.py"
Cohesion: 0.15
Nodes (20): affected_nodes(), AffectedHit, _bare_name(), format_affected(), format_ci_affected_tests(), format_git_diff_affected(), _format_location(), git_diff_changed_ranges() (+12 more)

### Community 183 - "cache.py"
Cohesion: 0.16
Nodes (20): _absolutize_source_files_in(), cached_files(), check_semantic_cache(), _cleanup_stale_ast_entries(), _ensure_stat_index(), _flush_stat_index(), load_cached(), _normalize_path() (+12 more)

### Community 184 - "Counter"
Cohesion: 0.12
Nodes (21): derive_flow_chain(), edge_score(), generate_overview_cards(), node_degree_scores(), node_importance(), preferred_edges(), Counter, Aggregate inter-section edge counts and relation names. (+13 more)

### Community 185 - "ingest.py"
Cohesion: 0.18
Nodes (20): _detect_url_type(), _download_binary(), _fetch_arxiv(), _fetch_html(), _fetch_tweet(), _fetch_webpage(), _html_to_markdown(), ingest() (+12 more)

### Community 186 - "save_query_result"
Cohesion: 0.15
Nodes (20): Save a Q&A result as markdown so it gets extracted into the graph on next --upda, save_query_result(), Tests for graphify.ingest.save_query_result, An outcome signal is written to both frontmatter (for `reflect`) and an     ## O, Backward compatible: a result without an outcome looks exactly as before., test_answer_in_body(), test_correction_in_frontmatter_and_body(), test_file_created() (+12 more)

### Community 187 - "security.py"
Cohesion: 0.11
Nodes (16): _ip_is_blocked(), _max_graph_file_bytes(), Resolve *host* once and return (family, validated_ip) for the first     address, HTTPConnection that resolves + validates DNS once, then connects to the     exac, HTTPSConnection variant of _SSRFGuardedHTTPConnection.      Connects to the vali, urllib handler that routes http:// through _SSRFGuardedHTTPConnection., urllib handler that routes https:// through _SSRFGuardedHTTPSConnection., Return the graph.json size cap in bytes.      Honors the ``GRAPHIFY_MAX_GRAPH_BY (+8 more)

### Community 188 - "test_explain_cli.py"
Cohesion: 0.19
Nodes (20): Regression tests for `graphify explain` arrow direction (#853)., No sidecar => no Lesson line; output identical to pre-feature., Two nodes sharing the same label across different files - e.g. an     overloaded, P16: --path narrows a duplicate label to one file, so explain resolves     deter, _run(), test_callee_shows_callers_as_inbound(), test_caller_shows_callee_as_outbound(), test_explain_context_filter_narrows_connections() (+12 more)

### Community 189 - "_write_raw_doc"
Cohesion: 0.13
Nodes (21): _overlay_corpus(), _overlay_graph(), Path, Write a memory doc with a controlled date so ordering is deterministic to assert, Write a minimal graph.json under ``out`` with the given node dicts., A corpus with: a PREFERRED node (2 useful), a TENTATIVE node (1 useful),     a C, reflect with a graph writes .graphify_learning.json next to graph.json with, Two reflect runs on identical input + fixed `now` produce a byte-identical     s (+13 more)

### Community 190 - "ci_affected_tests"
Cohesion: 0.13
Nodes (20): ci_affected_tests(), Sorted, deduplicated test-file paths whose coverage is touched by the     curren, _init_git_repo(), CLI wiring: `graphify affected --git-diff` runs without a positional query., CLI wiring: `graphify affected --ci` implies git-diff mode and prints a     lean, Regression: a fixture (or other non-code asset) living under a test     director, Regression: conftest.py/__init__.py are test-dir infra, not runnable     test ta, Regression: when a rationale/document node shares a line with the real     file (+12 more)

### Community 191 - "test_cache.py"
Cohesion: 0.14
Nodes (17): _body_content(), Strip YAML frontmatter from Markdown content, returning only the body., Tests for graphify/cache.py., _body_content correctly strips YAML frontmatter., _body_content returns content unchanged when no frontmatter present., A document opening with a ``----`` thematic break has no frontmatter;     a late, ``--- title`` on the first line is prose, not an open delimiter., ``--- text`` and ``----`` lines inside opened frontmatter are not the     close; (+9 more)

### Community 192 - "file_hash"
Cohesion: 0.10
Nodes (20): file_hash(), SHA256 of file contents + path relative to root.      Uses a stat-based fastpath, A .md file with no frontmatter is hashed by its full content., Non-.md files are still hashed by their full content., Editing content above a mid-document ``----`` break must change the     hash --, Same file gives same hash on repeated calls., Different file contents give different hashes., Entries written by pre-versioning graphify (flat cache/ or unversioned     cache (+12 more)

### Community 193 - "pick_text"
Cohesion: 0.13
Nodes (20): _describe_node(), format_node_refs(), generate_call_table_rows(), generate_section_cards(), generate_section_intro(), is_zh(), pick_text(), Render node references as readable labels instead of internal IDs. (+12 more)

### Community 194 - "extract_cpp"
Cohesion: 0.10
Nodes (20): extract_cpp(), Extract functions, classes, and includes from a .cpp/.cc/.cxx/.hpp file., Regression for #915: `class Derived : public Base {}` should emit an inherits ed, Structs use the same `: Base` syntax as classes and must also emit inherits., `class PooledClient : public Connection<HttpClient>` must emit the inherits, test_cpp_class_inherits_edge(), test_cpp_field_and_template_argument_contexts(), test_cpp_finds_class() (+12 more)

### Community 195 - "test_cpp_objc_cross_file_calls.py"
Cohesion: 0.28
Nodes (19): _call_edges(), _label(), Path, Cross-file member-call and include resolution for C++ (#1547) and ObjC (#1556)., {(source_label, relation, target_label, confidence)} for the given relations., The headline #1547 fix: a paired class no longer islands — Main.cpp's use of, test_cpp_cross_file_member_call_connects_with_relative_paths(), test_cpp_godnode_guard_ambiguous_and_unknown_receiver() (+11 more)

### Community 196 - "test_install_upgrade.py"
Cohesion: 0.15
Nodes (19): _assert_no_report_first(), _assert_query_first(), Installer-level regression tests for upgrade-in-place behavior (issue #580).  Pr, The Claude install must also rewrite a stale .claude/settings.json hook     payl, Same upgrade behavior for AGENTS.md (Codex / OpenCode / Aider / Trae)., Same upgrade behavior for GEMINI.md., Same upgrade behavior for .github/copilot-instructions.md (VS Code)., Same upgrade behavior for .cursor/rules/graphify.mdc.     The Cursor rule file i (+11 more)

### Community 197 - "_run"
Cohesion: 0.10
Nodes (20): CompletedProcess, argparse `choices` rejects an unknown outcome before save_query_result runs., --answer-file lets callers pass a long/multiline answer via a file instead     o, Neither --answer nor --answer-file -> clean argparse error, not a crash., First run with no graphify-out/memory/ still succeeds and writes a valid doc., With a real graph.json present, reflect auto-detects it and groups lessons     u, Through reflect()/CLI with a real graph.json: a cited node that isn't in the, `reflect --if-stale` skips the rebuild when LESSONS.md is already current,     a (+12 more)

### Community 198 - "ToolkitViewModel"
Cohesion: 0.13
Nodes (15): Email, RefreshCommand, ObservableObject, RelayCommand, Task, string, ToolkitViewModel, Email (+7 more)

### Community 199 - "string"
Cohesion: 0.14
Nodes (10): double, Get-Data(), Invoke-Main(), Process-Items(), string, Circle, DataProcessor, Shape (+2 more)

### Community 200 - "test_cluster.py"
Cohesion: 0.18
Nodes (18): cohesion_score(), Ratio of actual intra-community edges to maximum possible., Remap community IDs to maximize overlap with a previous assignment.      Uses gr, remap_communities_to_previous(), make_graph(), Clustering should not emit ANSI escape codes or other output.      graspologic's, Same as above but for stderr — ANSI codes can go to either stream., test_cluster_covers_all_nodes() (+10 more)

### Community 201 - "test_semantic_similarity.py"
Cohesion: 0.16
Nodes (18): _make_extraction_with_semantic_edge(), _make_graph_with_semantic_edge(), _make_report_with_semantic_surprise(), _make_two_edge_graph(), Tests for semantically_similar_to edge support., Two nodes in separate files connected by a semantically_similar_to edge., Non-semantic edges must not get the [semantically similar] tag., report renders [documents known bug] for a bug-doc -> file edge (G2/item 2). (+10 more)

### Community 202 - "_claude_artifacts"
Cohesion: 0.11
Nodes (19): _claude_artifacts(), The default code-corpus run must be fully described inside the core., No reference fragment may duplicate the core build pipeline., Every references/<name>.md the core points at is actually rendered., The query section heading is the lean-core stub; query.md re-homes the rest., claude renders exactly the eight on-demand fragments from the design., The fence-aware heading scanner must skip '#' lines inside code fences., Decision A: the file_type enum is the full six-value superset. (+11 more)

### Community 203 - "save_cached"
Cohesion: 0.11
Nodes (18): Save extraction result for this file.      Stores as graphify-out/cache/{kind}/{, save_cached(), The on-disk cache JSON contains forward-slash relative source_file     entries —, ``load_cached`` returns the same absolute-path shape that a fresh     extraction, End-to-end portability: a cache entry written at one root can be     consumed at, An AST entry written by version X must not be served after upgrading     to vers, The semantic cache is deliberately not versioned: entries are produced     by th, Save then load returns the same result dict. (+10 more)

### Community 204 - "extract_dart"
Cohesion: 0.14
Nodes (10): extract_dart(), Extract classes, mixins, functions, imports, generic calls, and annotations from, Test that the universal parser successfully extracts generic relationships, anno, Test complex Dart 3+ syntax and precise Riverpod/Bloc mappings., Test that the parser successfully handles namespaces in extends/implements, and, Test typedefs, mixin on, factories, constructor DI types, and universal navigati, Test all 5 roadmap bug fixes (Bug A, B, C, D, E)., TestDart (+2 more)

### Community 205 - "test_src_layout_import_resolution.py"
Cohesion: 0.15
Nodes (17): _probe_python_module_candidate(), Resolve one module-path candidate to a .py file (dir+__init__, exact, or     wit, Repoint Python absolute-import edges to the real file node under a nested     (e, _repoint_python_package_imports(), _resolve_python_module_path(), _import_edges(), Path, #2072: Python import resolution must not depend on the scan root.  A src-layout (+9 more)

### Community 206 - "uninstall"
Cohesion: 0.16
Nodes (17): _git_root(), _install_hook(), Path, Walk up to find .git directory., Raise if a hooks path looks like a Windows absolute path (#1385).      On POSIX/, # NOTE: do NOT pass --path-format=absolute — added in git 2.31; older git, Install a single git hook, appending if an existing hook is present., Remove graphify section from a git hook using start/end markers. (+9 more)

### Community 207 - "sample.php"
Cohesion: 0.15
Nodes (8): Authenticator, HasName, Loggable, ApiClient, BaseProcessor, DataProcessor, Result, Service

### Community 208 - "test_incremental.py"
Cohesion: 0.20
Nodes (16): _edges(), _make_docs_corpus(), CompletedProcess, Path, Integration tests for incremental graphify extract behavior., #1521: when an import is deleted from a file, `graphify update` must prune     t, After a full extract run, manifest.json must exist (or run fails before writing, If manifest.json + graph.json exist, incremental mode message is shown. (+8 more)

### Community 209 - "test_kotlin_object_literal.py"
Cohesion: 0.28
Nodes (16): _edges(), _extract(), _find(), Kotlin anonymous-object members (#2347).  `object : Foo { ... }` (node type `obj, Keep-the-bar: named `object` declarations and plain classes extract     exactly, Regression test: anonymous object literal node must not steal supertype's     na, Anonymous objects assigned to class properties must extract their owner node,, Anonymous objects assigned to top-level properties must extract cleanly. (+8 more)

### Community 210 - "test_provider_registry.py"
Cohesion: 0.12
Nodes (16): A provider whose base_url uses a non-http(s) scheme is skipped on load (F1)., provider_base_url_ok rejects bad schemes and warns on plaintext-http egress (F1), Custom providers appear after all built-ins in detect_backend() priority., Missing pricing field defaults to zero so estimate_cost doesn't blow up., Built-in provider names are protected from being overridden., Full round-trip: add → list → show → remove via providers.json., A project-local ./.graphify/providers.json is NOT loaded by default (F1).      I, With explicit opt-in the project-local file is honoured (F1). (+8 more)

### Community 211 - "test_python_module_qualified_calls.py"
Cohesion: 0.40
Nodes (16): _calls(), _nid(), Path, `module.func()` calls resolve to the module's top-level function (gap found in l, _run(), test_aliased_import(), test_ambiguous_module_name_creates_no_edge(), test_dotted_import_with_alias() (+8 more)

### Community 212 - "platforms.toml"
Cohesion: 0.12
Nodes (16): platform.agents, platform.aider, platform.amp, platform.claude, platform.claw, platform.codex, platform.copilot, platform.devin (+8 more)

### Community 213 - "Window"
Cohesion: 0.14
Nodes (15): MoneyConverter, TaxConverter, Invoice.Tax, Order.Total, User.Name, ModeText, RootPanel, SaveButton (+7 more)

### Community 214 - "cache_dir"
Cohesion: 0.15
Nodes (16): cache_dir(), prune_semantic_cache(), Returns the cache directory for ``kind`` - creates it if needed.      kind is "a, Remove orphaned semantic cache entries, returning the count pruned.      The sem, Cache entries written by an older graphify (with absolute source_file     inside, Upgrading removes AST entries left behind by previous versions so the     cache, Changing a file's content leaves the old content-hash entry orphaned;     prunin, Pruning against the FULL live set must keep every live entry — guards     the tr (+8 more)

### Community 215 - "extract_html"
Cohesion: 0.19
Nodes (15): extract_html_with_scripts(), extract_html's DOM-id nodes, plus a JS extraction pass over inline     <script>, extract_html(), Path, Tests for the HTML extractor. .html files previously had no extractor at all. Sc, A class-only element (no id) is deliberately not extracted — every     HTML docu, A function defined inside an inline <script> block was previously     invisible, No <script> body at all -> extract_html_with_scripts must not add or     change (+7 more)

### Community 216 - "extract_powershell_manifest"
Cohesion: 0.12
Nodes (16): extract_powershell_manifest(), Extract module dependency edges from a PowerShell .psd1 manifest file.      .psd, RootModule = 'MyModule.psm1' produces an imports_from edge to 'mymodule'., NestedModules = @('Helpers.psm1', 'Logger.psm1') produces edges for both., RequiredModules string form 'PSReadLine' produces an imports_from edge., RequiredModules hashtable form @{{ ModuleName='Pester' }} produces an imports_fr, ModuleVersion values ('5.0', '1.0.0') must NOT appear as import targets., All imports_from edge sources must exist in the node set. (+8 more)

### Community 217 - "test_terraform.py"
Cohesion: 0.30
Nodes (15): extract_terraform(), Extract Terraform/HCL blocks and the references between them via tree-sitter., _labels(), Path, Tests for the Terraform/HCL extractor (graphify/extract.py, issue #187)., _rel_pairs(), test_cross_file_references_resolve_after_merge(), test_depends_on_edge() (+7 more)

### Community 218 - "test_robot_extraction.py"
Cohesion: 0.19
Nodes (15): extract_robot(), Path, Tests for the Robot Framework extractor (P6). .robot files previously had no ext, `Resource    common.resource` is the RF mechanism for pulling in     keywords de, A call to a keyword not defined in this file (imported from a     .resource) mus, Open Browser/Should Contain/etc. are library keywords, not locally     defined —, *** Settings *** / *** Variables *** sections have no test-case/     keyword def, test_extract_robot_call_to_builtin_keyword_produces_no_calls_edge() (+7 more)

### Community 219 - "run_language_resolvers"
Cohesion: 0.21
Nodes (14): Path, Registry for cross-file, language-specific resolution passes.  Some call/referen, Return a copy of the registered resolvers, in registration order., Run every resolver whose suffix appears in ``paths``.      Behaviorally identica, registered_resolvers(), run_language_resolvers(), _make_resolver(), Tests for the language resolver registry (graphify.resolver_registry).  The regi (+6 more)

### Community 220 - "_make_scip_node_id"
Cohesion: 0.12
Nodes (16): _make_scip_node_id(), Derive a stable Graphify node ID from a SCIP symbol identifier.      Uses SHA-1, Symbol with # uses suffix after last #., Symbol without # uses the full symbol (sanitised) as suffix., Non-alphanumeric characters are replaced with underscores., Same inputs always produce the same id., Different source_file produces different hash., Different symbol produces different hash. (+8 more)

### Community 221 - "test_incomplete_build_guard.py"
Cohesion: 0.24
Nodes (15): _arm_extract(), _arm_no_cluster(), _make_docs_corpus(), Tests for the incomplete-build shrink-guard on `graphify extract`.  A full build, A present-but-unparseable existing graph.json (corrupt or mid-write) could     b, Patch export.to_json to record the ``force`` it was called with and return     a, _seed_existing_graph(), _seed_to_json_recorder() (+7 more)

### Community 222 - "test_indirect_call_for_of_binding_shadow.py"
Cohesion: 0.23
Nodes (15): _extract_js_dir(), _indirect(), A `for...of` / `for...in` loop binding must shadow indirect_call references.  `_, A loop binding in `for (const entry of rows)` is block-scoped to the loop     bo, A loop binding in `for (const entry of rows)` is block-scoped to the loop     bo, `for (var entry of rows)` is function-scoped in JS, so it shadows throughout, The reported shape: a `for...of` binding `entry` used in an     object-shorthand, A destructured loop binding (`for (const { entry } of xs)`) must shadow     the (+7 more)

### Community 223 - "test_indirect_call_nested_closure_shadow.py"
Cohesion: 0.22
Nodes (15): _extract_js_dir(), JS/TS closure-body descent with parameter and local shadowing (#2241).  Descend, A const-assigned arrow IS separately tracked (its own caller_nid, own     local_, Blast-radius traversal must not include a caller that only reached the     targe, The fix must hold on a warm-cache re-extraction, not just a cold run —     the s, Reported shape (#2241): a one-letter test helper `r` must not become a     fabri, The same nested-arrow shape must still capture a REAL by-name reference     that, Shadowing must compound through two levels of untracked inline     closures: an (+7 more)

### Community 224 - "AccountService"
Cohesion: 0.15
Nodes (7): delete, insert, update, AccountService, AccountStatus, Account, Notifiable

### Community 225 - "load_graph"
Cohesion: 0.17
Nodes (14): first_list(), load_graph(), _node_link_payload(), Return the first list from a set of possible schema locations., Read current graphify graph.json via NetworkX's node-link parser., Load graph.json. Returns normalized (nodes, edges, hyperedges, metadata)., _make_graphify_out(), Path (+6 more)

### Community 226 - "label_communities_by_hub"
Cohesion: 0.26
Nodes (14): community_member_sigs(), label_communities_by_hub(), Per-community membership fingerprints: ``{cid: sha256(sorted member ids)}``., Deterministic, LLM-free community labels: name each community after its     high, _g(), Deterministic, LLM-free community labels — `label_communities_by_hub`.  Names ea, test_absent_members_fall_back_to_placeholder(), test_community_member_sigs_are_deterministic_and_order_independent() (+6 more)

### Community 227 - "extract_astro"
Cohesion: 0.28
Nodes (14): extract_astro(), Extract imports from .astro files: frontmatter (TS) + template regex fallback., _import_targets(), Path, Tests for `.astro` extraction (#850).  Astro files have a TypeScript frontmatter, Astro permits frontmatter-less files (pure-HTML pages). Must not raise., Without this, detect.py silently drops `.astro` from the AST pass (#850)., test_astro_is_in_code_extensions() (+6 more)

### Community 228 - "test_stale_hint.py"
Cohesion: 0.45
Nodes (14): One-line stderr note when files the graph covers changed since graph.json was bu, _warn_if_graph_stale(), _commit_file(), _git(), _graph(), Path, The CLI's "graph may be stale" hint must follow CONTENT, not commit identity.  A, _repo() (+6 more)

### Community 229 - "test_install_strings.py"
Cohesion: 0.14
Nodes (11): _skill_registration(), Regression tests for install-time instruction strings.  These strings live in gr, The fix demotes GRAPH_REPORT.md, it doesn't delete the reference.     Most insta, Assert the structure of _POST_EDIT_HOOK and that its embedded Python code is val, All ten install surfaces must point the assistant at `graphify query`     as the, The pre-fix instructions told assistants to read GRAPH_REPORT.md as     their fi, test_every_install_surface_recommends_graphify_query(), test_no_install_surface_demands_reading_the_full_report_first() (+3 more)

### Community 230 - "routes.py"
Cohesion: 0.19
Nodes (14): _path_proximity_winner(), Pick the candidate whose source file is closest to the call site.      ``candida, extract_js_routes(), extract_python_routes(), _make_route_id(), Any, Path, path is the source file's own path (see _file_stem's docstring for why     this (+6 more)

### Community 231 - "resolve_cross_file_raw_calls"
Cohesion: 0.13
Nodes (15): Resolve unqualified raw calls conservatively after all files are known.      Thi, resolve_cross_file_raw_calls(), Two genuine NON-test defs of the same name: the god-node guard must still     ho, A real cross-file call must resolve to the SRC definition even when a     same-n, One src def plus many same-named test stubs: exactly one edge to src., A test file calling save() with both a src def and a test-local def present, The python cross-file resolver returns [] (not crash) on bad raw_calls., test_resolve_cross_file_raw_calls_call_site_is_test_prefers_test_local() (+7 more)

### Community 232 - "Window"
Cohesion: 0.18
Nodes (11): RoutedEventArgs, RootPanel, SaveButton, UserNameBox, Window, UserName, MainWindow, Button (+3 more)

### Community 233 - "TDataProcessor"
Cohesion: 0.16
Nodes (7): IProcessor, TObject, SampleUnit, TBaseProcessor, TDataProcessor, Process(), Reset()

### Community 234 - "typescript_advanced.ts"
Cohesion: 0.14
Nodes (8): DEFAULT_ROLES, IUserRepository, USER_CONFIG, USER_REPOSITORY, UserId, UserModule, UserService, UserStatus

### Community 235 - "test_file_node_id_spec.py"
Cohesion: 0.13
Nodes (13): Regression tests for issue #1033: AST file-level node IDs must match the skill.m, Changing the file-id format must not orphan import edges: the import     target, match/script/pipeline_step.py -> file node id 'match_script_pipeline_step'     (, A file directly at the project root collapses to just its stem., A SYMBOL in a root-level file must use the bare-stem prefix (`setup_configure`),, Regression guard: nested files (immediate parent identical in abs/rel form), Symbol ids already use {parent}_{stem}_{name}; the file node must share     that, test_cross_file_import_edges_stay_connected() (+5 more)

### Community 236 - "extract_csharp"
Cohesion: 0.14
Nodes (14): extract_csharp(), Extract C# type declarations, methods, namespaces, and usings from a .cs file., test_csharp_call_edges_have_call_context(), test_csharp_finds_class(), test_csharp_finds_interface(), test_csharp_finds_methods(), test_csharp_finds_usings(), test_csharp_implements_iprocessor() (+6 more)

### Community 237 - "safe_fetch"
Cohesion: 0.18
Nodes (14): _build_opener(), Fetch *url* and return raw bytes.      Protections applied:     - URL scheme val, Fetch *url* and return decoded text (UTF-8, replacing bad bytes).      Wraps saf, safe_fetch(), safe_fetch_text(), OpenerDirector, _make_mock_response(), test_safe_fetch_raises_on_non_2xx() (+6 more)

### Community 238 - "sample.sv"
Cohesion: 0.18
Nodes (12): leaf, math_pkg, leaf, Payload, BaseProcessor, Config, DataProcessor, build (+4 more)

### Community 239 - "test_indirect_call_catch_binding_shadow.py"
Cohesion: 0.25
Nodes (13): _extract_js_dir(), `catch (e)` bindings must shadow indirect_call args — inside the clause only.  `, ES2019 `catch { }` is a real catch_clause with no `parameter` field — the     `p, Reported shape: a minified bundle's private `k` must not become a fabricated, `catch ({ cause })` binds through the same field via a pattern — the     destruc, The binding is scoped to the clause: a same-named module callable referenced, Widening the shadow set must not blanket-suppress indirect_call inside a catch, _rels() (+5 more)

### Community 240 - "test_pascal_resolution.py"
Cohesion: 0.21
Nodes (13): _call_edge(), _find_raw_call(), _labels(), Tests for cross-file Pascal/Delphi inherited-method-call resolution.  The per-fi, When a base class file exists on disk (under the project root) but is     exclud, Sanity check for the gap this resolver closes: the per-file extractor     alone, TDerivedGadget inherits only from TBaseGadget. TOtherGadget declares an     unre, Two unrelated Pascal classes in separate files, with a same-named lowercase (+5 more)

### Community 241 - "test_pipeline.py"
Cohesion: 0.23
Nodes (13): Path, End-to-end pipeline test: detect → extract → build → cluster → analyze → report, Second run on unchanged corpus should produce identical node/edge counts., Run the full pipeline on the fixtures directory. Returns a dict of outputs., run_pipeline(), test_pipeline_all_nodes_have_community(), test_pipeline_detection_finds_code_and_docs(), test_pipeline_extraction_confidence_labels() (+5 more)

### Community 242 - "Geometry"
Cohesion: 0.21
Nodes (11): Base, Base.Threads, Float64, LinearAlgebra, ParentModule, area(), describe(), Circle (+3 more)

### Community 243 - "sample.razor"
Cohesion: 0.15
Nodes (12): ComponentBase, CounterRecord, DataGrid, ICounterService, Microsoft.AspNetCore.Components, MyApp.Services, NavigationManager, route:/counter (+4 more)

### Community 244 - "geometry"
Cohesion: 0.22
Nodes (11): constants, geometry, double_val(), circle_area(), geometry, main, point, origin() (+3 more)

### Community 245 - "DataProcessor"
Cohesion: 0.26
Nodes (7): GraphifyDemo, HttpClient, List, DataProcessor, IProcessor, Processor, Result

### Community 246 - "sample.go"
Cohesion: 0.26
Nodes (9): BaseProcessor, DataProcessor, Logger, Reader, ReaderLogger, Result, Server, main() (+1 more)

### Community 247 - "build_label_index"
Cohesion: 0.17
Nodes (13): build_label_index(), node_is_resolvable_symbol(), normalise_callable_label(), Normalize a node label into the key used for call resolution., Return True when a node is suitable for deterministic symbol lookup.      Requir, Build label -> node id list for conservative cross-file resolution., Document/paper/image/concept nodes MUST NOT be indexed as call targets,     even, label index must not include document/paper/image nodes even when     label and (+5 more)

### Community 248 - "sample.dmf"
Cohesion: 0.15
Nodes (12): elem "info" [CHILD], elem "infowindow" [MAIN], elem "map" [MAP], elem "mapwindow" [MAIN], elem "output" [OUTPUT], elem "outputwindow" [MAIN], elem "stat" [INFO], elem "statwindow" [MAIN] (+4 more)

### Community 249 - "ScopedCallsUnit"
Cohesion: 0.23
Nodes (12): TObject, ScopedCallsUnit, TBaseWidget, Prepare(), TDerivedWidget, Run(), TFirstWidget, Configure() (+4 more)

### Community 250 - "test_csharp_partial_classes.py"
Cohesion: 0.31
Nodes (12): _extract(), _find(), _nodes_labeled(), C# partial classes split across files (#2332).  `partial class Foo` declared in, Nested partial types are excluded: their ids omit the enclosing type     name, s, Beta() in half B calls Alpha() declared in half A — an in-class     unqualified, test_cross_file_caller_resolves_into_both_halves(), test_cross_half_unqualified_in_class_call_resolves() (+4 more)

### Community 251 - "test_ts_inheritance.py"
Cohesion: 0.35
Nodes (12): _has_inherits(), Path, Regression tests for issue #1095: TypeScript inheritance capture.  Two gaps on v, Regression guard: the originally-working imported-class case must stay., test_class_extends_same_file(), test_class_implements_same_file_interface(), test_imported_class_extends_still_works(), test_interface_extends_generic_base_same_file() (+4 more)

### Community 252 - "graphify"
Cohesion: 0.17
Nodes (12): `graph.json`을 LLM과 함께 사용하기, graphify, 개인정보 보호, 결과물, 기술 스택, 동작 원리, 사용법, 설치 (+4 more)

### Community 253 - "bench_extract.py"
Cohesion: 0.27
Nodes (11): clear_cache(), Delete all cache entries (ast/, semantic/, and legacy flat entries)., _count_by_ext(), _format_languages(), main(), Path, Run extraction, return (elapsed_seconds, node_count, edge_count)., Count files by extension. (+3 more)

### Community 254 - "extract_elixir"
Cohesion: 0.17
Nodes (12): extract_elixir(), Path, Extract modules, functions, imports, and calls from a .ex/.exs file., `alias Foo.{Bar, Baz}` must emit one imports edge per expanded module.      The, test_elixir_call_edges_have_call_context(), test_elixir_finds_calls(), test_elixir_finds_functions(), test_elixir_finds_imports() (+4 more)

### Community 255 - "extract_fish"
Cohesion: 0.24
Nodes (10): extract_fish(), Path, Fish shell extractor. New — .fish files previously had no extractor at all. No t, Tests for the fish shell extractor. .fish files previously had no extractor at a, Real fish scripts commonly guard function definitions behind an     `if`/`end` b, test_extract_fish_comment_mentioning_function_is_not_a_node(), test_extract_fish_dispatches_from_extract_module(), test_extract_fish_file_contains_edge_to_function() (+2 more)

### Community 256 - "extract_gherkin"
Cohesion: 0.26
Nodes (10): extract_gherkin(), Path, Gherkin (.feature) extractor. New — .feature files previously had no extractor a, Tests for the Gherkin (.feature) extractor. .feature files previously had no ext, test_extract_gherkin_dispatches_from_extract_module(), test_extract_gherkin_feature_produces_node(), test_extract_gherkin_scenario_nests_under_its_feature(), test_extract_gherkin_scenario_outline_produces_child_node() (+2 more)

### Community 257 - "default_graph_json"
Cohesion: 0.20
Nodes (12): default_graph_json(), Default ``graph.json`` path under the configured output dir.      The package-wi, _filter_blank_stdin(), _main(), Filter blank lines from stdin before MCP reads it.      Some MCP clients (Claude, Start the MCP server over stdio (the default, per-developer transport)., Start the MCP server over Streamable HTTP (MCP spec 2025-03-26).      Serves the, serve() (+4 more)

### Community 258 - "disambiguate_ambiguous_candidates"
Cohesion: 0.27
Nodes (11): disambiguate_ambiguous_candidates(), _is_test_path(), Classify a source path as a test path (case-insensitive, segment-aware).      Sh, Resolve an ambiguous bare-name call to one candidate, or ``None``.      Shared g, Tests for graphify.paths — the shared test-path classifier (#1553)., test_disambiguate_bails_on_two_nontest_candidates(), test_disambiguate_drops_test_candidate_for_nontest_call_site(), test_disambiguate_path_proximity_same_dir() (+3 more)

### Community 259 - "_build_server"
Cohesion: 0.23
Nodes (7): fetch_pr_files(), fetch_worktrees(), Returns {branch: worktree_path}., _build_server(), Build the configured low-level MCP Server (shared by every transport).      All, A detached HEAD (no branch line) must not associate its path with the         ne, TestFetchWorktrees

### Community 260 - "sample.json"
Cohesion: 0.17
Nodes (11): dependencies, axios, react, devDependencies, typescript, name, scripts, build (+3 more)

### Community 261 - "test_extraction_spec_ids.py"
Cohesion: 0.27
Nodes (11): _ast_symbol_id(), _examples(), Path, Drift guard for the node-ID spec shown to LLM semantic subagents.  `tools/skillg, Reproduce the symbol ID the AST extractor emits for a file + symbol, using     t, Guard the guard: if the spec moves or the example format changes so nothing, The canonical spec warns against the filename-only and full-path ID forms.     L, _spec_files() (+3 more)

### Community 262 - "test_indirect_dispatch_getattr.py"
Cohesion: 0.38
Nodes (11): _extract(), _ind(), Reflective dispatch via getattr string literals — #1566 slice 3.  ``getattr(obj,, test_dynamic_getattr_names_emit_nothing(), test_getattr_feeds_affected(), test_getattr_non_callable_name_emits_nothing(), test_getattr_string_literal_emits_indirect_call(), test_getattr_string_not_shadowed_by_param() (+3 more)

### Community 263 - "test_java_type_resolution.py"
Cohesion: 0.44
Nodes (11): _label_edges(), _node_by_id(), Path, test_java_ambiguous_implements_disambiguated_by_import(), test_java_cross_file_constructor_call_resolves(), test_java_cross_file_implements_resolves_to_real_def(), test_java_implements_edge_survives_build(), test_java_record_becomes_type_node() (+3 more)

### Community 264 - "test_mcp_stdio.py"
Cohesion: 0.38
Nodes (7): _Client, _project(), Path, End-to-end over real stdio: the MCP server must start, list every tool (building, _started(), test_calls_over_stdio_search_and_dry_run_edit(), test_tools_list_builds_every_tool_schema()

### Community 265 - "test_python_import_resolution.py"
Cohesion: 0.47
Nodes (11): _has_edge(), _node_id(), Path, Refactoring a module into a package directory (graphs.py -> graphs/__init__.py), test_ordinary_relative_import_still_resolves(), test_overdeep_relative_import_is_unresolved_not_fatal(), test_python_package_reexport_resolves_import_and_call_to_origin_symbol(), test_python_parameter_return_and_generic_contexts() (+3 more)

### Community 266 - "Demo.ViewModels"
Cohesion: 0.18
Nodes (6): Demo.ViewModels, PrismOrderViewModel, SettingsViewModel, UserControl, SettingsView, UserControl

### Community 267 - "graphify"
Cohesion: 0.18
Nodes (11): graphify, アシスタントに常にグラフを使わせる（推奨）, インストール, スター履歴, プライバシー, プラットフォームサポート, 仕組み, 使い方 (+3 more)

### Community 268 - "load_project_config"
Cohesion: 0.29
Nodes (9): load_project_config(), Any, Path, Load configuration from graphify.toml or [tool.graphify] in pyproject.toml., test_load_project_config_graphify_toml_nested(), test_load_project_config_graphify_toml_toplevel(), test_load_project_config_no_config(), test_load_project_config_override_precedence() (+1 more)

### Community 269 - "_norm"
Cohesion: 0.18
Nodes (11): _entropy(), _norm(), Lowercase + collapse non-alphanumeric runs to space (Unicode-aware)., Shannon entropy in bits/char of the normalised label., The prefix-extension guard must not fire for same-length pairs — only strict, The prefix-extension guard must fire for pairs where one is a strict prefix, test_entropy_empty_string(), test_entropy_normal_label_high() (+3 more)

### Community 270 - "compute_pr_impact"
Cohesion: 0.35
Nodes (4): compute_pr_impact(), Return (communities_touched, nodes_affected) for a set of changed files.      Bu, 3 nodes across 2 communities, 2 distinct source files., TestComputePrImpact

### Community 271 - "_hop_distances"
Cohesion: 0.18
Nodes (11): _hop_distances(), BFS distance in hops from the nearest seed, over the edges actually     discover, _make_graph_with_god_node(), A hub with many low-value edges that would win a pure degree-sort, plus     a lo, Omitting hop_distances/relevance_scores preserves the exact old     degree-sort, With hop_distances/relevance_scores supplied, a node one hop closer to     the s, Edge direction in the (u, v) tuple must not affect hop distance - a     caller a, test_hop_distances_from_seed() (+3 more)

### Community 272 - "parse_memory_doc"
Cohesion: 0.18
Nodes (11): parse_memory_doc(), Parse the frontmatter of a memory doc into a dict, or None if it has none., Reverse the double-quoted escaping that ingest._yaml_str applies., _yaml_unescape(), parse_memory_doc reads back exactly what save_query_result wrote, including, A plain markdown file with no frontmatter is skipped, not crashed on., save -> parse preserves tricky characters in the question, the correction,     a, test_parse_handles_crlf() (+3 more)

### Community 273 - "validate_url"
Cohesion: 0.18
Nodes (10): _NoFileRedirectHandler, Raise ValueError if *url* is not http or https, or targets a private/internal IP, Redirect handler that re-validates every redirect target.      Prevents open-red, validate_url(), test_validate_url_accepts_http(), test_validate_url_accepts_https(), test_validate_url_rejects_data(), test_validate_url_rejects_empty_scheme() (+2 more)

### Community 274 - "_rebuild_lock"
Cohesion: 0.18
Nodes (11): Per-repo advisory lock around a rebuild.      Yields True if acquired, False if, _rebuild_lock(), GH-858: lock file must be unlinked once the rebuild completes so     downstream, GH-858: each acquisition truncates and rewrites the PID line rather     than app, GH-858: a non-blocking caller that fails to acquire the lock must not     trunca, #1059: when the rebuild lock is held, an incremental hook must queue     its cha, test_rebuild_code_queues_on_lock_contention(), test_rebuild_lock_does_not_accumulate_pids_across_runs() (+3 more)

### Community 275 - "barrel_reexport.ts"
Cohesion: 0.25
Nodes (4): readCookie(), writeCookie(), basePathRewrite(), getFullUrl()

### Community 276 - "TMainForm"
Cohesion: 0.18
Nodes (5): TButton, TPanel, TMainForm, TMemo, TStatusBar

### Community 277 - "test_indirect_dispatch_assign_return.py"
Cohesion: 0.42
Nodes (10): _extract(), _ind(), Indirect dispatch via assignment + return references — #1566 slice 2.  A functio, test_assignment_and_return_emit_indirect_call(), test_assignment_feeds_affected(), test_local_shadow_emits_nothing(), test_module_level_assignment_emits_indirect_call(), test_multiple_assignment_emits_for_each() (+2 more)

### Community 278 - "test_swift_builtin_noise.py"
Cohesion: 0.24
Nodes (10): _labels_by_id(), Swift/Foundation/SwiftUI builtins must not become god nodes or bind to user symb, Non-Swift files defining symbols named like Swift builtins (Color, View, Calenda, Non-Swift nodes labeled 'Color' or 'View' must not be filtered by Swift noise la, Swift framework symbols must be filtered from god_nodes output.      Constructs, test_god_nodes_excludes_swift_builtin_labels(), test_god_nodes_preserves_non_swift_symbols_matching_swift_builtins(), test_non_swift_symbols_matching_swift_builtins_resolve_call_edges() (+2 more)

### Community 279 - "Docker MCP Toolkit + SQLite MCP server"
Cohesion: 0.20
Nodes (9): Docker MCP Toolkit + SQLite MCP server, Install, Prerequisites, Smoke test, Storage layout, Troubleshooting, Uninstall / reset, Why SQLite (and not `sqlite-mcp-server`) (+1 more)

### Community 280 - "README.de-DE.md"
Cohesion: 0.20
Nodes (9): Assistenten immer den Graphen nutzen lassen (empfohlen), Datenschutz, Installation, Plattformunterstützung, So funktioniert es, Star-Verlauf, Tech-Stack, Verwendung (+1 more)

### Community 281 - "README.es-ES.md"
Cohesion: 0.20
Nodes (9): Cómo funciona, Hacer que el asistente siempre use el grafo (recomendado), Historial de estrellas, Instalación, Privacidad, Qué obtienes, Soporte de plataformas, Stack técnico (+1 more)

### Community 282 - "README.fr-FR.md"
Cohesion: 0.20
Nodes (9): Ce que vous obtenez, Comment ça fonctionne, Confidentialité, Historique des étoiles, Installation, Stack technique, Support des plateformes, Toujours utiliser le graphe (recommandé) (+1 more)

### Community 283 - "README.pt-BR.md"
Cohesion: 0.20
Nodes (9): Como funciona, Fazer o assistente sempre usar o grafo (recomendado), Histórico de estrelas, Instalação, O que você obtém, Privacidade, Stack técnico, Suporte a plataformas (+1 more)

### Community 284 - "README.ru-RU.md"
Cohesion: 0.20
Nodes (9): Заставить ассистента всегда использовать граф (рекомендуется), Использование, История звёзд, Как это работает, Конфиденциальность, Поддержка платформ, Технологический стек, Установка (+1 more)

### Community 285 - "README.uz-UZ.md"
Cohesion: 0.20
Nodes (9): Foydalanish, Maxfiylik, Nima olasiz, O'rnatish, Platforma qo'llab-quvvatlash, Qanday ishlaydi, Texnologiyalar to'plami, Yordamchini har doim grafdan foydalanishga majbur qilish (tavsiya etiladi) (+1 more)

### Community 286 - "graphify"
Cohesion: 0.20
Nodes (10): graphify, Worked examples, 你会得到什么, 安装, 工作原理, 平台支持, 技术栈, 用法 (+2 more)

### Community 287 - "changed_seeds"
Cohesion: 0.20
Nodes (10): changed_seeds(), _nodes_by_file(), {source_file: [(line, node_id, end_line), ...]} sorted ascending, for     nodes, Map git-diff changed line ranges to graph node ids.      Returns {file: [node_id, End-to-end against a real git repo (real subprocess git diff, not mocked) --, Regression (#2): a change in the gap AFTER a node's known end_line (blank     li, Nodes with no end_line (most extractors haven't been threaded through     #2 yet, test_changed_seeds_maps_real_git_diff_to_nearest_node() (+2 more)

### Community 288 - "push_to_falkordb"
Cohesion: 0.27
Nodes (9): push_to_falkordb(), Push graph directly to a running FalkorDB instance via the Python SDK.      Requ, _connect(), db(), Integration test for push_to_falkordb against a real FalkorDB instance.  Runs fo, Return a connected FalkorDB client, or skip if none is reachable., MERGE-based push is safe to re-run - counts must not grow., test_push_to_falkordb_creates_expected_graph() (+1 more)

### Community 289 - "extract_toml"
Cohesion: 0.31
Nodes (9): extract_toml(), Path, Tests for the TOML extractor. .toml files previously had no extractor at all — a, test_extract_toml_dispatches_from_extract_module(), test_extract_toml_dotted_table_key_produces_node(), test_extract_toml_file_contains_edge_to_table(), test_extract_toml_repeated_array_of_tables_produces_distinct_nodes(), test_extract_toml_root_level_pair_produces_node() (+1 more)

### Community 290 - "tree_html.py"
Cohesion: 0.38
Nodes (9): build_tree(), _common_root(), emit_html(), _make_truncation_leaf(), Any, Path, tree_html — emit a D3 v7 collapsible-tree HTML view of a graph.  A self-containe, Build a ``{name, total_count, children}`` hierarchy.      Each leaf is either a (+1 more)

### Community 291 - "sample.rs"
Cohesion: 0.31
Nodes (8): HashMap, GraphEvent, GraphPair, Logger, T, DataProcessor, Processor, Result

### Community 292 - "test_ingest_scip_cli.py"
Cohesion: 0.33
Nodes (9): `graphify ingest-scip` — CLI wiring for graphify/scip_ingest.py's ingest_scip_js, The documented workflow: ingest, then feed the result into the     existing merg, _run(), test_ingest_scip_invalid_json_exits_nonzero(), test_ingest_scip_missing_file_exits_nonzero(), test_ingest_scip_no_args_shows_usage(), test_ingest_scip_respects_out_flag(), test_ingest_scip_then_merge_semantic_combines_with_existing_extraction() (+1 more)

### Community 293 - "monolith_roundtrip"
Cohesion: 0.20
Nodes (10): Each monolith is diff-clean vs v8 except the file_type enum unification., Every line that differs from pristine v8 is a sanctioned change-class.      The, test_monolith_roundtrip_passes_for_aider_and_devin(), test_monoliths_change_only_sanctioned_lines(), _is_sanctioned_monolith_diff(), _is_trigger_line(), monolith_roundtrip(), Whether a single added/removed monolith line is an allowed change. (+2 more)

### Community 294 - "render_always_on"
Cohesion: 0.24
Nodes (10): render_always_on yields exactly the six always-on instruction files., Each always_on/*.md reproduces its former __main__.py constant byte for byte., test_always_on_renders_six_blocks(), test_always_on_roundtrip_is_byte_faithful(), _always_on_constants(), always_on_roundtrip(), Parse the always-on string constants out of a __main__.py blob.      Reads the m, Assert each always_on/*.md reproduces its former constant byte for byte.      Th (+2 more)

### Community 295 - "test_swift_computed_properties.py"
Cohesion: 0.47
Nodes (4): _labels(), Regression tests for #2181.  Swift computed properties (`var body: some View { …, _rel(), TestSwiftComputedProperties

### Community 296 - "test_wheel_packaging.py"
Cohesion: 0.29
Nodes (9): _expected_artifacts(), _has_build(), Path, Packaging guard (#1121 follow-up): the 5 skillgen guards check the *repo tree*,, Every distinct skill body a platform installs (the SKILL.md is copied from     o, Every committed skill body + references/*.md (per host) + always_on/*.md block., _skill_bodies(), test_skill_artifact_ships_in_wheel() (+1 more)

### Community 297 - "README.ar-SA.md"
Cohesion: 0.22
Nodes (8): الاستخدام, التثبيت, الخصوصية, المكدس التقني, دعم المنصات, سجل النجوم, كيف يعمل, ما ستحصل عليه

### Community 298 - "sample.csproj"
Cohesion: 0.22
Nodes (6): net8.0, FluentValidation (11.9.0), MediatR (12.2.0), Microsoft.AspNetCore.Authentication.JwtBearer (8.0.0), Swashbuckle.AspNetCore (6.5.0), Microsoft.NET.Sdk.Web

### Community 299 - "extract_dmm"
Cohesion: 0.22
Nodes (9): _dmm_type_path(), extract_dmm(), Extract type-path references from a .dmm map file's tile dictionary., _split_dmm_tile(), test_dmm_extracts_type_paths_as_uses_edges(), test_dmm_handles_multiline_tile_definition(), test_dmm_no_error(), test_dmm_skips_grid_section() (+1 more)

### Community 300 - "_detect_default_branch"
Cohesion: 0.33
Nodes (4): _detect_default_branch(), Auto-detect the repo's default branch via gh, then git, then fall back to 'main', gh returns data but with no defaultBranchRef — should still fall back., TestDetectDefaultBranch

### Community 302 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 303 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 304 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 305 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 306 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 307 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 308 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 309 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 310 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 311 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 312 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 313 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 314 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 315 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 316 - "Widget"
Cohesion: 0.28
Nodes (4): Widget, -refresh, -render, String

### Community 317 - "TBaseGadget"
Cohesion: 0.28
Nodes (7): BaseGadget, TObject, TBaseGadget, Prepare(), DerivedGadget, TDerivedGadget, Run()

### Community 319 - "Config"
Cohesion: 0.36
Nodes (7): BaseClient, HttpClientFactory, Int, Loggable, String, Config, HttpClient

### Community 320 - "sample_calls.py"
Cohesion: 0.39
Nodes (5): Analyzer, compute_score(), normalize(), Fixture: functions and methods that call each other - for call-graph extraction, run_analysis()

### Community 321 - "/datum/weapon/sword"
Cohesion: 0.36
Nodes (8): /datum/weapon, /datum/weapon/attack(), /datum/weapon/New(), /datum/weapon/sword, /datum/weapon/sword/attack(), /datum/weapon/sword/sharpen(), log_event(), RunTest()

### Community 322 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 323 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 324 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 325 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 326 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 327 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 328 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 329 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 330 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 331 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 332 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 333 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 334 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 335 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 336 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 337 - "saxpy"
Cohesion: 0.29
Nodes (7): constant, kernel, dot3(), device, saxpy(), Vec3, uint

### Community 338 - "README.hi-IN.md"
Cohesion: 0.25
Nodes (7): Star इतिहास, आपको क्या मिलता है, इंस्टॉलेशन, उपयोग, गोपनीयता, प्लेटफॉर्म समर्थन, यह कैसे काम करता है

### Community 339 - "first_present"
Cohesion: 0.29
Nodes (8): endpoint_id(), first_present(), normalize_edge(), normalize_node(), Return the first non-empty value for any candidate key., Normalize edge endpoints that may be strings or node-like objects., Normalize a graphify node across common graph.json schema variants., Normalize graphify edges while preserving original fields.

### Community 340 - "Migrating a language extractor out of extract.py"
Cohesion: 0.25
Nodes (7): Helper classification, Invariants (non-negotiable), Migrating a language extractor out of extract.py, Pre-flight, Status, Steps, What NOT to do

### Community 341 - "_backend_pkg_hint"
Cohesion: 0.36
Nodes (7): _backend_pkg_hint(), Package-missing message that works for the recommended `uv tool` install.      `, _extras(), The claude backend must be installable via an extra, and the missing-package mes, test_anthropic_extra_exists(), test_anthropic_in_all_extra(), test_backend_pkg_hint_points_at_uv_tool_and_extra()

### Community 342 - "_auto_open_browser"
Cohesion: 0.54
Nodes (7): _auto_open_browser(), Path, `graphify update` / `cluster-only` must not pop a browser tab from agents, hooks, _spy(), test_browser_opens_in_a_real_terminal(), test_env_var_disables_it_even_in_a_terminal(), test_no_browser_when_stdout_is_not_a_terminal()

### Community 343 - "load_memory_docs"
Cohesion: 0.25
Nodes (8): load_memory_docs(), Parse every memory doc under ``memory_dir``, sorted by date then filename., Determinism hinges on this sort: docs come back oldest-first, filename as tiebre, dead_ends/corrections are appended in doc order, so their determinism rides on, test_dead_ends_and_corrections_follow_doc_order(), test_load_memory_docs_missing_dir_is_empty(), test_load_memory_docs_orders_by_date_then_filename(), test_load_memory_docs_skips_foreign_and_sorts()

### Community 344 - "iter_raw_calls"
Cohesion: 0.25
Nodes (8): iter_raw_calls(), Return raw calls from all per-file extraction fragments.      Parameter is ``Seq, A non-dict per_file entry (e.g. junk fragment) must be silently skipped., `raw_calls` that isn't a list must yield empty., Items inside `raw_calls` list that aren't dicts must be dropped., test_iter_raw_calls_drops_non_dict_items_in_list(), test_iter_raw_calls_skips_non_dict_per_file_entries(), test_iter_raw_calls_skips_non_list_raw_calls()

### Community 345 - "check_update"
Cohesion: 0.25
Nodes (8): check_update(), Check for pending semantic update flag and notify the user if set.      Cron-saf, check_update returns True and is silent when needs_update flag is absent., check_update returns True and prints notification when flag exists., check_update never removes the needs_update flag (clearing is LLM's job)., test_check_update_does_not_clear_flag(), test_check_update_no_flag_returns_true(), test_check_update_with_flag_returns_true_and_prints()

### Community 346 - "watch"
Cohesion: 0.25
Nodes (8): _notify_only(), Write a flag file and print a notification (fallback for non-code-only corpora)., Watch watch_path for new or modified files and auto-update the graph.      For c, watch(), test_notify_only_creates_flag(), test_notify_only_creates_flag_dir(), test_notify_only_idempotent(), test_watch_raises_without_watchdog()

### Community 347 - "Security Model"
Cohesion: 0.25
Nodes (7): Optional network calls, Reporting a Vulnerability, Security Model, Security Policy, Supported Versions, Threat Surface, What graphify does NOT do

### Community 348 - "sample.zig"
Cohesion: 0.32
Nodes (6): add(), Color, multiply(), main(), Point, Shape

### Community 349 - "compilerOptions"
Cohesion: 0.25
Nodes (7): compilerOptions, module, outDir, strict, target, extends, include

### Community 350 - "test_case_sensitive_resolution.py"
Cohesion: 0.54
Nodes (7): _extract(), _labels(), Cross-file name resolution respects case in case-sensitive languages (#1581).  C, test_case_sensitive_cross_file_ref_respects_case(), test_exact_case_cross_file_still_resolves(), test_php_case_insensitive_resolution_preserved(), test_python_Path_does_not_resolve_to_shell_PATH()

### Community 351 - "_write"
Cohesion: 0.32
Nodes (8): _cli(), Path, tools/list must still build (a Python-source JSON `false` once crashed it) and c, test_cli_errors(), test_cli_json_and_limit(), test_cli_table(), test_mcp_tool_is_declared_with_valid_schema_over_stdio(), _write()

### Community 352 - "schema_singleton"
Cohesion: 0.25
Nodes (8): The file_type enum is the six-value superset in every rendered artifact., The guard's line scanner flags 4- and 5-value pipe enums, not the superset., test_schema_singleton_catches_legacy_enums(), test_schema_singleton_passes_across_all_platforms(), legacy_enum_lines(), Return lines carrying a legacy (sub-superset) file_type enum.      A line counts, Assert the file_type enum block is byte-identical across every platform.      Ev, schema_singleton()

### Community 353 - "test_swift_import_resolution.py"
Cohesion: 0.61
Nodes (7): _import_edges(), _module_nodes(), Path, test_swift_import_edges_survive_build(), test_swift_import_resolves_to_module_node(), test_swift_same_module_imported_twice_collapses_to_one_node(), _write()

### Community 354 - "release-graph.yml"
Cohesion: 0.29
Nodes (6): jobs, build-graph, name, on, release, workflow_dispatch

### Community 355 - "_path_match"
Cohesion: 0.43
Nodes (3): _path_match(), True if graph_src and pr_file refer to the same file (path-boundary safe)., TestPathMatch

### Community 356 - "lessons_fresh"
Cohesion: 0.29
Nodes (7): lessons_fresh(), True if ``out_path`` exists and is at least as new as every input that     feeds, test_lessons_fresh_false_when_graph_newer(), test_lessons_fresh_false_when_graph_sidecar_newer(), test_lessons_fresh_false_when_memory_newer(), test_lessons_fresh_missing_output_is_not_fresh(), test_lessons_fresh_true_when_output_newer_than_inputs()

### Community 357 - "Foo"
Cohesion: 0.33
Nodes (3): Foo, bar, value

### Community 358 - "sample_php_listen.php"
Cohesion: 0.43
Nodes (6): EventServiceProvider, NotifyAdmins, OrderPlaced, SendWelcomeEmail, ShipOrder, UserRegistered

### Community 359 - "test_kustomization_extraction.py"
Cohesion: 0.29
Nodes (6): Tests for the Kustomize overlay extractor (Feature 1, IaC indexing) - see agent-, A `resources:` entry pointing at a file not in the corpus (excluded,     renamed, test_extract_kustomization_dispatches_from_extract_module(), test_extract_kustomization_imports_edge_resolves_to_target_file(), test_extract_kustomization_missing_target_produces_no_dangling_edge(), test_extract_kustomization_produces_module_node()

### Community 360 - "test_serve_search_text.py"
Cohesion: 0.52
Nodes (6): _graph(), Path, MCP search_text tool: registered, dispatched, and returns hits with their enclos, test_search_text_is_registered_as_an_mcp_tool(), test_search_text_text_reports_invalid_regex_instead_of_raising(), test_search_text_text_returns_hit_with_enclosing_symbol()

### Community 361 - "README.fi-FI.md"
Cohesion: 0.33
Nodes (5): Asennus, Käyttö, Miten se toimii, Mitä saat, Yksityisyys

### Community 362 - "README.fil-PH.md"
Cohesion: 0.33
Nodes (5): Ano ang Makukuha Mo, Paano Gumagana, Pag-install, Paggamit, Privacy

### Community 363 - "README.hu-HU.md"
Cohesion: 0.33
Nodes (5): Adatvédelem, Használat, Hogyan működik, Mit kap, Telepítés

### Community 364 - "README.it-IT.md"
Cohesion: 0.33
Nodes (5): Come funziona, Cosa ottieni, Installazione, Privacy, Utilizzo

### Community 365 - "README.nl-NL.md"
Cohesion: 0.33
Nodes (5): Gebruik, Hoe het werkt, Installatie, Privacy, Wat je krijgt

### Community 366 - "README.pl-PL.md"
Cohesion: 0.33
Nodes (5): Co otrzymujesz, Instalacja, Jak to działa, Prywatność, Użycie

### Community 367 - "README.sv-SE.md"
Cohesion: 0.33
Nodes (5): Användning, Hur det fungerar, Installation, Integritet, Vad du får

### Community 368 - "README.tr-TR.md"
Cohesion: 0.33
Nodes (5): Gizlilik, Kullanım, Kurulum, Nasıl çalışır, Ne elde edersiniz

### Community 369 - "README.vi-VN.md"
Cohesion: 0.33
Nodes (5): Cài đặt, Cách hoạt động, Những gì bạn nhận được, Quyền riêng tư, Sử dụng

### Community 370 - "humanize_label"
Cohesion: 0.33
Nodes (6): humanize_label(), node_display_name(), Readable node label for tables and summaries., Truncate without splitting Mermaid syntax., Convert graph labels into short labels people can scan in a diagram., truncate_text()

### Community 371 - "_csharp_type_parameters_in_scope"
Cohesion: 0.33
Nodes (6): _csharp_attribute_names(), _csharp_collect_type_refs(), _csharp_type_parameters_in_scope(), Return C# type-parameter names visible from ``node``., Walk a C# type expression; append (name, role, qualified, qualifier) tuples., Collect attribute names from a C# method/declaration's attribute_list children.

### Community 372 - "_gas_collect_action_arms"
Cohesion: 0.33
Nodes (6): _find_first_bare_call_expression(), _gas_binary_string_literal(), _gas_collect_action_arms(), For a `<binary_expression>` shaped `identifier === 'literal'` (either     operan, First `call_expression` in a subtree whose callee is a plain     identifier (`ge, Walk an `if`/`else if` chain, yielding `(action_literal, callee_name,     line)`

### Community 373 - "_compute_idf"
Cohesion: 0.33
Nodes (6): _compute_idf(), IDF weights for query terms, cached in G.graph['_idf_cache']., A term matching only 1 of N nodes should get IDF > 1., A term matching most nodes should get IDF < 1., test_idf_common_term_gets_low_weight(), test_idf_rare_term_gets_high_weight()

### Community 374 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 375 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 376 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 377 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 378 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 379 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 380 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 381 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 382 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 383 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 384 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 385 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 386 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 387 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 388 - "sample.c"
Cohesion: 0.47
Nodes (5): Rectangle, main(), make_rect(), process(), validate()

### Community 389 - "Deploy Guide"
Cohesion: 0.33
Nodes (5): Database Migration, Deploy Guide, Full Deploy, Prerequisites, Rollback

### Community 391 - "sample.sh"
Cohesion: 0.53
Nodes (5): APP_ENV, build(), deploy(), sample.sh script, test_suite()

### Community 392 - "TSampleForm"
Cohesion: 0.33
Nodes (4): TPanel, TLabel, TSampleForm, TTimer

### Community 393 - "sample_php_container.php"
Cohesion: 0.67
Nodes (4): AppServiceProvider, CashierGateway, PaymentGateway, StripeGateway

### Community 394 - "SampleSpec"
Cohesion: 0.33
Nodes (4): SampleSpec, "should handle #input and return #expected", "should not change value when it's already correct", "should process valid input"

### Community 395 - "_launcher_payload"
Cohesion: 0.33
Nodes (6): _launcher_payload(), Extract the `python -c "<payload>"` the hook hands to GRAPHIFY_PYTHON.      The, The launcher is carried inside a shell double-quoted `-c "..."` argument,     so, Both the launcher and the rebuild body it re-executes must parse, so a     quoti, test_launcher_and_rebuild_body_are_valid_python(), test_launcher_payload_is_shell_quote_safe()

### Community 396 - "test_posix_custom_hookspath_still_works"
Cohesion: 0.33
Nodes (6): Path, A Windows-style core.hooksPath must raise (loud failure), not silently     creat, A legitimate POSIX core.hooksPath (Husky-style) must still install., _set_hookspath(), test_posix_custom_hookspath_still_works(), test_windows_hookspath_rejected_no_junk_dir_on_posix()

### Community 397 - "test_http_calls_linking.py"
Cohesion: 0.33
Nodes (5): Tests for the cross-file http_calls resolver (Feature 2 Task 8, iac-http-linking, A repo with no doGet/doPost anywhere must never even attempt     resolution - ch, test_http_calls_interpolated_call_site_gets_no_edge(), test_http_calls_links_fetch_call_site_to_action_handler_target(), test_http_calls_no_gas_handlers_in_corpus_is_a_no_op()

### Community 398 - "test_merge_graphs_cli.py"
Cohesion: 0.47
Nodes (5): Path, `graphify merge-graphs` tolerates inputs that disagree on graph type (#1606).  P, _run(), test_merge_graphs_mixed_directed_and_multigraph(), _write()

### Community 399 - "_seed_semantic_doc_graph"
Cohesion: 0.33
Nodes (6): Build a code-only graph, then add guide.md represented ONLY semantically.      M, #1915: a full _rebuild_code must not AST-quick-scan a doc whose semantic     (LL, #1915: an incremental rebuild whose change set includes a semantic-backed     do, _seed_semantic_doc_graph(), test_rebuild_code_incremental_preserves_semantic_doc_nodes_and_edges(), test_rebuild_code_semantic_doc_not_double_represented_on_full_rebuild()

### Community 400 - "_seed_semantic_doc_graph_concept_only"
Cohesion: 0.33
Nodes (6): Like ``_seed_semantic_doc_graph``, but guide.md's semantic layer is     ONLY con, #1954: a doc represented ONLY by concept/rationale nodes (no     file_type=="doc, #1954: incremental analogue — a concept/rationale-only semantic doc     must not, _seed_semantic_doc_graph_concept_only(), test_rebuild_code_concept_only_semantic_doc_not_double_represented_on_full_rebuild(), test_rebuild_code_incremental_preserves_concept_only_semantic_doc_nodes_and_edges()

### Community 401 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 402 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 403 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 404 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 405 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 406 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 407 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 408 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 409 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 410 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 411 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 412 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 413 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 414 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 415 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 416 - "[0.15.0] - 2026-07-03"
Cohesion: 0.40
Nodes (5): [0.15.0] - 2026-07-03, Added, Changed, Documentation, Fixed

### Community 417 - "[0.24.2] - 2026-08-24"
Cohesion: 0.40
Nodes (5): [0.24.2] - 2026-08-24, Added, Changed, Documentation, Fixed

### Community 418 - "[0.3.1] - 2026-04-06"
Cohesion: 0.40
Nodes (5): [0.3.1] - 2026-04-06, Added, Changed, Documentation, Fixed

### Community 419 - "[0.8.39] - 2026-06-12"
Cohesion: 0.40
Nodes (5): [0.8.39] - 2026-06-12, Added, Changed, Documentation, Fixed

### Community 420 - "[0.8.40] - 2026-06-16"
Cohesion: 0.40
Nodes (5): [0.8.40] - 2026-06-16, Added, Changed, Documentation, Fixed

### Community 421 - "[0.9.5] - 2026-07-02"
Cohesion: 0.40
Nodes (5): [0.9.5] - 2026-07-02, Added, Changed, Documentation, Fixed

### Community 422 - "[1.0.0] - 2026-04-05"
Cohesion: 0.40
Nodes (5): [1.0.0] - 2026-04-05, Added, Changed, Documentation, Fixed

### Community 423 - "SamplePackage"
Cohesion: 0.40
Nodes (5): FCL, LCL, sampleutils, sample, SamplePackage

### Community 424 - "resolve_pascal_inherited_calls"
Cohesion: 0.50
Nodes (4): _pascal_raw_calls(), Cross-file resolution for Pascal/Delphi calls to inherited methods.  The per-fil, Resolve Pascal/Delphi calls to a method inherited across file boundaries.      P, resolve_pascal_inherited_calls()

### Community 425 - "_bash_make_id"
Cohesion: 0.40
Nodes (5): _bash_make_id(), Bash symbol node ID via the single shared recipe (#1378).      Previously an inl, _bash_make_id must produce identical output to _make_id for Unicode inputs., test_bash_make_id_identical_to_make_id(), test_bash_make_id_unicode_matches_make_id()

### Community 426 - "TOtherGadget"
Cohesion: 0.40
Nodes (3): OtherGadget, TObject, TOtherGadget

### Community 427 - "sample.sql"
Cohesion: 0.60
Nodes (3): active_users, organizations, users

### Community 428 - "MyApp.Accounts.User"
Cohesion: 0.50
Nodes (3): MyApp.Accounts.User, create(), validate()

### Community 432 - "sample.sln"
Cohesion: 0.70
Nodes (3): Domain, WebApi, Tests

### Community 433 - "UserControl"
Cohesion: 0.40
Nodes (3): DesignViewModel, DesignView, UserControl

### Community 434 - "MainViewModel"
Cohesion: 0.40
Nodes (3): MainViewModel, MainWindow, Window

### Community 435 - "AGENTS.md"
Cohesion: 0.50
Nodes (3): Agent Memory, graphify, Skills & Rules

### Community 436 - "[0.10.0] - 2026-07-01"
Cohesion: 0.50
Nodes (4): [0.10.0] - 2026-07-01, Added, Documentation, Fixed

### Community 437 - "[0.16.0] - 2026-07-04"
Cohesion: 0.50
Nodes (4): [0.16.0] - 2026-07-04, Added, Documentation, Fixed

### Community 438 - "[0.17.0] - 2026-07-18"
Cohesion: 0.50
Nodes (4): [0.17.0] - 2026-07-18, Added, Documentation, Fixed

### Community 439 - "[0.18.0] - 2026-07-19"
Cohesion: 0.50
Nodes (4): [0.18.0] - 2026-07-19, Added, Documentation, Fixed

### Community 440 - "[0.21.0] - 2026-07-25"
Cohesion: 0.50
Nodes (4): [0.21.0] - 2026-07-25, Added, Documentation, Fixed

### Community 441 - "[0.22.0] - 2026-07-26"
Cohesion: 0.50
Nodes (4): [0.22.0] - 2026-07-26, Added, Documentation, Fixed

### Community 442 - "[0.23.0] - 2026-07-30"
Cohesion: 0.50
Nodes (4): [0.23.0] - 2026-07-30, Changed, Documentation, Fixed

### Community 443 - "[0.25.0] - 2026-09-16"
Cohesion: 0.50
Nodes (4): [0.25.0] - 2026-09-16, Added, Documentation, Fixed

### Community 444 - "[0.26.0] - 2026-10-03"
Cohesion: 0.50
Nodes (4): [0.26.0] - 2026-10-03, Added, Documentation, Fixed

### Community 445 - "[0.27.0] - 2026-10-22"
Cohesion: 0.50
Nodes (4): [0.27.0] - 2026-10-22, Added, Documentation, Fixed

### Community 446 - "[0.4.0] - 2026-04-10"
Cohesion: 0.50
Nodes (4): [0.4.0] - 2026-04-10, Added, Documentation, Fixed

### Community 447 - "[0.6.7] - 2026-05-02"
Cohesion: 0.50
Nodes (4): [0.6.7] - 2026-05-02, Added, Documentation, Fixed

### Community 448 - "[0.7.19] - 2026-05-14"
Cohesion: 0.50
Nodes (4): [0.7.19] - 2026-05-14, Added, Documentation, Fixed

### Community 449 - "[0.7.8] - 2026-05-06"
Cohesion: 0.50
Nodes (4): [0.7.8] - 2026-05-06, Added, Documentation, Fixed

### Community 450 - "[0.8.16] - 2026-05-22"
Cohesion: 0.50
Nodes (4): [0.8.16] - 2026-05-22, Added, Documentation, Fixed

### Community 451 - "[0.8.18] - 2026-05-24"
Cohesion: 0.50
Nodes (4): [0.8.18] - 2026-05-24, Added, Documentation, Fixed

### Community 452 - "[0.8.22] - 2026-05-27"
Cohesion: 0.50
Nodes (4): [0.8.22] - 2026-05-27, Added, Documentation, Fixed

### Community 453 - "[0.8.25] - 2026-05-29"
Cohesion: 0.50
Nodes (4): [0.8.25] - 2026-05-29, Added, Documentation, Fixed

### Community 454 - "[0.8.32] - 2026-06-05"
Cohesion: 0.50
Nodes (4): [0.8.32] - 2026-06-05, Added, Documentation, Fixed

### Community 455 - "[0.8.34] - 2026-06-07"
Cohesion: 0.50
Nodes (4): [0.8.34] - 2026-06-07, Added, Documentation, Fixed

### Community 456 - "[0.8.38] - 2026-06-11"
Cohesion: 0.50
Nodes (4): [0.8.38] - 2026-06-11, Added, Documentation, Fixed

### Community 457 - "[0.8.47] - 2026-06-24"
Cohesion: 0.50
Nodes (4): [0.8.47] - 2026-06-24, Added, Documentation, Fixed

### Community 458 - "[0.8.49] - 2026-06-25"
Cohesion: 0.50
Nodes (4): [0.8.49] - 2026-06-25, Added, Changed, Fixed

### Community 459 - "[0.8.50] - 2026-06-27"
Cohesion: 0.50
Nodes (4): [0.8.50] - 2026-06-27, Added, Documentation, Fixed

### Community 460 - "[0.8.51] - 2026-06-28"
Cohesion: 0.50
Nodes (4): [0.8.51] - 2026-06-28, Added, Documentation, Fixed

### Community 461 - "[0.9.0] - 2026-06-28"
Cohesion: 0.50
Nodes (4): [0.9.0] - 2026-06-28, Added, Documentation, Fixed

### Community 462 - "[0.9.2] - 2026-06-29"
Cohesion: 0.50
Nodes (4): [0.9.2] - 2026-06-29, Added, Documentation, Fixed

### Community 463 - "[0.9.3] - 2026-06-30"
Cohesion: 0.50
Nodes (4): [0.9.3] - 2026-06-30, Added, Documentation, Fixed

### Community 464 - "[0.9.4] - 2026-07-01"
Cohesion: 0.50
Nodes (4): [0.9.4] - 2026-07-01, Added, Documentation, Fixed

### Community 465 - "_env_command_args"
Cohesion: 0.50
Nodes (4): _env_command_args(), Re-tokenize an `env -S`/`--split-string` packed command, prepending the     oper, Strip leading env(1) options and var assignments, return the trailing     comman, _split_env_s()

### Community 466 - "_csharp_receiver_type_name"
Cohesion: 0.50
Nodes (4): _csharp_receiver_type_name(), Resolve a C# type name, whether it was qualified, and its qualifier prefix., Resolve a C# declared type to a receiver-typable class name, or None.      A gen, _read_csharp_type_name()

### Community 467 - "_java_collect_type_refs"
Cohesion: 0.50
Nodes (4): _java_collect_type_refs(), _java_type_parameters_in_scope(), Walk a Java type expression; append (name, role) tuples., Return Java type-parameter names visible from ``node``.

### Community 468 - "_kotlin_extract_object_literals"
Cohesion: 0.50
Nodes (4): _kotlin_extract_object_literals(), _kotlin_user_type_name(), Return the head identifier text from a Kotlin user_type node (without generics)., Scan scope_node for object_literal descendants and emit owner nodes/edges/member

### Community 469 - "_detached_launch"
Cohesion: 0.50
Nodes (4): _detached_launch(), Return a POSIX-sh line that runs ``rebuild_body`` as a detached background     P, The launcher must run via the resolved $GRAPHIFY_PYTHON, not a bare     `python`, test_detached_launch_targets_graphify_python()

### Community 470 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 471 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 472 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 473 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 474 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 475 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 476 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 477 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 478 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 479 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 480 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 481 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 482 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 483 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 484 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 485 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 486 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 487 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 488 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 489 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 490 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 491 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 492 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 493 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 494 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 495 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 496 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 497 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 498 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 499 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 500 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 501 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 502 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 503 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 504 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration (Trae), graphify reference: commit hook and native AGENTS.md integration

### Community 505 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 506 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 507 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 508 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 509 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 510 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 511 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 513 - "repos"
Cohesion: 0.50
Nodes (3): repos, repos[0], repos[1]

### Community 518 - "App"
Cohesion: 0.83
Nodes (3): App(), fmtCount(), fmtDate()

### Community 521 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 522 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 523 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 524 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 525 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 526 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 527 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 528 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 529 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 530 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 531 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 532 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 533 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 534 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 535 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 536 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 537 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 538 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 539 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 540 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 541 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 542 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 543 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 544 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 545 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 546 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 547 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 548 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 549 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 550 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 551 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 552 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 553 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 554 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 555 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration (Trae), graphify reference: commit hook and native AGENTS.md integration

### Community 556 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 557 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 558 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 559 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 560 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 561 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 562 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 563 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration@@AGENTS_HEADING_SUFFIX@@, graphify reference: commit hook and native AGENTS.md integration

### Community 564 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 565 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 566 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 567 - "[0.11.1] - 2026-07-02"
Cohesion: 0.67
Nodes (3): [0.11.1] - 2026-07-02, Added, Fixed

### Community 568 - "[0.19.0] - 2026-07-19"
Cohesion: 0.67
Nodes (3): [0.19.0] - 2026-07-19, Added, Fixed

### Community 569 - "[0.24.0] - 2026-08-24"
Cohesion: 0.67
Nodes (3): [0.24.0] - 2026-08-24, Documentation, Fixed

### Community 570 - "[0.25.1] - 2026-09-18"
Cohesion: 0.67
Nodes (3): [0.25.1] - 2026-09-18, Added, Documentation

### Community 571 - "[0.7.10] - 2026-05-07"
Cohesion: 0.67
Nodes (3): [0.7.10] - 2026-05-07, Changed, Fixed

### Community 572 - "[0.7.18] - 2026-05-13"
Cohesion: 0.67
Nodes (3): [0.7.18] - 2026-05-13, Documentation, Fixed

### Community 573 - "[0.7.9] - 2026-05-07"
Cohesion: 0.67
Nodes (3): [0.7.9] - 2026-05-07, Added, Fixed

### Community 574 - "[0.8.11] - 2026-05-18"
Cohesion: 0.67
Nodes (3): [0.8.11] - 2026-05-18, Changed, Fixed

### Community 575 - "[0.8.20] - 2026-05-26"
Cohesion: 0.67
Nodes (3): [0.8.20] - 2026-05-26, Added, Fixed

### Community 576 - "[0.8.26] - 2026-05-30"
Cohesion: 0.67
Nodes (3): [0.8.26] - 2026-05-30, Added, Documentation

### Community 577 - "[0.8.33] - 2026-06-06"
Cohesion: 0.67
Nodes (3): [0.8.33] - 2026-06-06, Added, Fixed

### Community 578 - "[0.8.35] - 2026-06-07"
Cohesion: 0.67
Nodes (3): [0.8.35] - 2026-06-07, Added, Fixed

### Community 579 - "[0.8.36] - 2026-06-08"
Cohesion: 0.67
Nodes (3): [0.8.36] - 2026-06-08, Added, Fixed

### Community 580 - "[0.8.37] - 2026-06-10"
Cohesion: 0.67
Nodes (3): [0.8.37] - 2026-06-10, Changed, Fixed

### Community 581 - "[0.8.41] - 2026-06-17"
Cohesion: 0.67
Nodes (3): [0.8.41] - 2026-06-17, Added, Fixed

### Community 582 - "[0.8.46] - 2026-06-23"
Cohesion: 0.67
Nodes (3): [0.8.46] - 2026-06-23, Changed, Fixed

### Community 583 - "[0.9.1] - 2026-06-28"
Cohesion: 0.67
Nodes (3): [0.9.1] - 2026-06-28, Documentation, Fixed

## Knowledge Gaps
- **2014 isolated node(s):** `github`, `name`, `release`, `workflow_dispatch`, `build-graph` (+2009 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **188 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.
- **15 possibly unreachable function(s):** `Config`, `CounterRecord`, `DataGrid`, `WeatherDisplay`, `_ApiKeyMiddleware` (+10 more)
  Not reached from any recognized entry point - could be dead code, or dynamically dispatched/decorator-registered.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `main` to `__main__.py`, `test_analyze.py`, `test_detect.py`, `cluster`, `detect.py`, `test_install.py`, `extract`, `_make_graph`, `test_codebuddy.py`, `test_chunking.py`, `to_wiki`, `test_lsp_resolve.py`, `make_id`, `Graph`, `test_fuzzy_fallback.py`, `test_multigraph_diagnostics.py`, `llm.py`, `build_from_json`, `test_devin.py`, `test_install_references.py`, `deduplicate_entities`, `test_security.py`, `test_indirect_dispatch.py`, `test_cypher.py`, `extract_files_direct`, `parse_and_execute_pattern`, `reflect.py`, `generate`, `test_global_graph.py`, `validate_extraction`, `ingest_scip_json`, `test_path_cli.py`, `analyze.py`, `test_image_vision.py`, `_query_graph_text`, `test_hooks.py`, `query.py`, `_rebuild_code`, `test_labeling.py`, `test_benchmark.py`, `_call_claude_cli`, `prs.py`, `RuntimeError`, `build_merge`, `test_describe.py`, `test_affected_cli.py`, `write_callflow_html`, `check_for_update`, `claude_install`, `test_dataflow.py`, `paths.py`, `edit.py`, `test_snippet.py`, `search_text`, `test_agents_platform.py`, `cypher.py`, `test_edit.py`, `check_git_clone_update`, `build.py`, `introspect_cargo`, `test_onboard.py`, `affected.py`, `cache.py`, `ingest.py`, `save_query_result`, `test_explain_cli.py`, `ci_affected_tests`, `file_hash`, `test_cluster.py`, `uninstall`, `cache_dir`, `test_incomplete_build_guard.py`, `label_communities_by_hub`, `test_stale_hint.py`, `load_project_config`, `push_to_falkordb`, `tree_html.py`, `_auto_open_browser`, `check_update`, `watch`, `_write`, `lessons_fresh`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `extract()` connect `extract` to `extract.py`, `test_extract.py`, `disambiguate_ambiguous_candidates`, `_read_text`, `__main__.py`, `test_edit.py`, `extract_gherkin`, `test_java_type_resolution.py`, `test_mcp_stdio.py`, `test_python_import_resolution.py`, `test_swift_cross_file_calls.py`, `main`, `test_http_calls_linking.py`, `test_languages.py`, `test_multilang.py`, `Path`, `test_csharp_member_calls.py`, `test_dotnet.py`, `test_swift_builtin_noise.py`, `make_id`, `test_js_import_resolution.py`, `extract_toml`, `test_ruby_resolution.py`, `_edge_labels`, `css.py`, `extract_yaml`, `test_indirect_dispatch.py`, `test_indirect_call_external_import_shadow.py`, `_corpus`, `cache.py`, `extract_markdown`, `test_cpp_objc_cross_file_calls.py`, `_get_extractor`, `_rebuild_code`, `test_src_layout_import_resolution.py`, `test_kotlin_object_literal.py`, `test_python_module_qualified_calls.py`, `extract_html`, `CsharpNameResolver`, `test_manifest_ingest.py`, `test_robot_extraction.py`, `run_language_resolvers`, `test_case_sensitive_resolution.py`, `test_indirect_call_for_of_binding_shadow.py`, `test_indirect_call_nested_closure_shadow.py`, `test_swift_import_resolution.py`, `test_indirect_call_function_expression_shadow.py`, `test_kustomization_extraction.py`, `test_serve_search_text.py`, `_key`, `test_file_node_id_spec.py`, `test_vue_extraction.py`, `test_indirect_call_catch_binding_shadow.py`, `test_pascal_resolution.py`, `test_pipeline.py`, `test_dataflow.py`, `test_snippet.py`, `test_csharp_partial_classes.py`, `test_ts_inheritance.py`, `bench_extract.py`, `search_text`, `extract_fish`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `build_from_json()` connect `build_from_json` to `test_swift_cross_file_calls.py`, `__main__.py`, `_read_text`, `test_edit.py`, `test_analyze.py`, `extract_js`, `cluster`, `test_java_type_resolution.py`, `test_mcp_stdio.py`, `main`, `test_languages.py`, `make_id`, `Graph`, `test_semantic_cleanup.py`, `test_multigraph_diagnostics.py`, `push_to_falkordb`, `build.py`, `test_reflect.py`, `deduplicate_entities`, `extract_python`, `generate`, `validate_extraction`, `ingest_scip_json`, `test_cli_export.py`, `test_cpp_objc_cross_file_calls.py`, `test_cluster.py`, `test_semantic_similarity.py`, `_rebuild_code`, `test_src_layout_import_resolution.py`, `test_scip_ingest.py`, `test_manifest_ingest.py`, `test_terraform.py`, `test_swift_import_resolution.py`, `test_hypergraph.py`, `routes.py`, `test_serve_search_text.py`, `test_pascal_resolution.py`, `test_pipeline.py`, `test_dataflow.py`, `test_snippet.py`, `search_text`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `main()` (e.g. with `_file_hash()` and `_save_manifest()`) actually correct?**
  _`main()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `github`, `name`, `release` to the rest of the system?**
  _4490 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `extract.py` be split into smaller, more focused modules?**
  _Cohesion score 0.02137791286727457 - nodes in this community are weakly interconnected._
- **Should `test_extract.py` be split into smaller, more focused modules?**
  _Cohesion score 0.02071220930232558 - nodes in this community are weakly interconnected._