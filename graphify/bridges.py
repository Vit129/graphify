# Cross-language bridge resolution (Swift <-> ObjC, React Native / Expo Native Modules)
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import networkx as nx


def resolve_cross_language_bridges(G: nx.Graph) -> int:
    """Detect and link cross-language bridges (React Native, Expo, Swift <-> ObjC).

    Returns the number of bridge edges added.
    """
    added_edges = 0

    # 1. Collect native modules (ObjC, Swift, Java, Kotlin)
    # Native module name -> node_id
    native_modules: dict[str, str] = {}
    # (module_name, method_name) -> node_id
    native_methods: dict[tuple[str, str], str] = {}
    # Swift @objc symbols: symbol_name -> node_id
    objc_symbols: dict[str, str] = {}

    for nid, d in G.nodes(data=True):
        label = str(d.get("label", ""))
        source_file = str(d.get("source_file", "")).lower()

        # Swift @objc
        if source_file.endswith(".swift"):
            if "@objc" in label:
                cleaned = label.replace("@objc", "").strip()
                cleaned = re.sub(r"^(?:class|struct|enum|protocol|func|var|let)\s+", "", cleaned)
                bare = cleaned.split("(")[0].strip()
                if bare:
                    objc_symbols[bare] = nid
            elif "RCT_EXPORT" in label or "NativeModule" in label:
                bare = label.split("(")[0].strip()
                native_modules[bare] = nid

        # ObjC native modules
        elif source_file.endswith((".m", ".mm", ".h")):
            rct_mod = re.search(r"""RCT_EXPORT_MODULE\s*\(\s*([a-zA-Z0-9_]+)?\s*\)""", label)
            if rct_mod:
                mod_name = rct_mod.group(1) or Path(source_file).stem
                native_modules[mod_name] = nid
            rct_meth = re.search(r"""RCT_EXPORT_METHOD\s*\(\s*([a-zA-Z0-9_]+)""", label)
            if rct_meth:
                meth_name = rct_meth.group(1)
                mod_stem = Path(source_file).stem
                native_methods[(mod_stem, meth_name)] = nid

        # Kotlin / Java native modules
        elif source_file.endswith((".kt", ".java")):
            if "ReactContextBaseJavaModule" in label or "NativeModule" in label:
                mod_stem = Path(source_file).stem
                native_modules[mod_stem] = nid
            if "@ReactMethod" in label:
                bare = label.replace("@ReactMethod", "").split("(")[0].strip()
                mod_stem = Path(source_file).stem
                native_methods[(mod_stem, bare)] = nid

    # 2. Match JS/TS / ObjC callers
    for nid, d in G.nodes(data=True):
        source_file = str(d.get("source_file", "")).lower()
        label = str(d.get("label", ""))

        # React Native: NativeModules.ModuleName or requireNativeComponent('ModuleName')
        if source_file.endswith((".js", ".jsx", ".ts", ".tsx")):
            rn_matches = re.finditer(r"""(?:NativeModules\.|requireNativeModule\(\s*['"`]|requireNativeComponent\(\s*['"`])([a-zA-Z0-9_]+)""", label)
            for m in rn_matches:
                mod_name = m.group(1)
                target_nid = native_modules.get(mod_name)
                if target_nid and nid != target_nid and not G.has_edge(nid, target_nid):
                    G.add_edge(
                        nid,
                        target_nid,
                        relation="bridges_to",
                        confidence="EXTRACTED",
                        context="react_native_bridge",
                        _src=nid,
                        _tgt=target_nid,
                    )
                    added_edges += 1

        # Swift-ObjC cross-reference (ObjC -> Swift @objc or Swift -> ObjC)
        elif source_file.endswith((".m", ".mm", ".h")):
            for sym_name, target_nid in objc_symbols.items():
                if sym_name in label and nid != target_nid and not G.has_edge(nid, target_nid):
                    G.add_edge(
                        nid,
                        target_nid,
                        relation="bridges_to",
                        confidence="EXTRACTED",
                        context="objc_bridge",
                        _src=nid,
                        _tgt=target_nid,
                    )
                    added_edges += 1

    return added_edges
