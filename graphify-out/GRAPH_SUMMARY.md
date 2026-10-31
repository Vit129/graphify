# Graph Summary — delivery-workflow-completion
_Auto-generated from GRAPH_REPORT.md · do not edit manually_
_Regen: `graphify update .`_

## Summary
- 11152 nodes · 20895 edges · 795 communities (607 shown, 188 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 318 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output


## Graph Freshness
- Built from commit: `bc858c65`
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
3. `Changelog` - bridges 51 areas (81 edges)
4. `Graph` - bridges 42 areas (195 edges)
5. `build_from_json()` - bridges 41 areas (132 edges)
6. `_make_id()` - bridges 34 areas (103 edges)
7. `_rebuild_code()` - bridges 34 areas (80 edges)
8. `_file_stem()` - bridges 33 areas (84 edges)
9. `ingest_scip_json()` - bridges 32 areas (85 edges)

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


_Full map → GRAPH_REPORT.md · query: `graphify query "..."`_
