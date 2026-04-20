#!/usr/bin/env python3
"""
Registry Validator CLI Tool for Diamond-OS

Validates the structure of 01_CENTRAL_TASK_REGISTRY.md and reports issues.
Usage: python validate_registry.py [--fix]
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidationIssue:
    level: str  # ERROR, WARNING, INFO
    line: int
    message: str
    suggestion: str


def _h2_section_lines(lines: List[str], heading_prefix: str) -> Optional[List[str]]:
    """Return lines inside the H2 section starting with heading_prefix (until next H2 at column 0)."""
    start: Optional[int] = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and not line.startswith("###"):
            if line.strip().startswith(heading_prefix):
                start = i + 1
                break
    if start is None:
        return None
    out: List[str] = []
    for j in range(start, len(lines)):
        line = lines[j]
        if line.startswith("## ") and not line.startswith("###"):
            break
        out.append(line)
    return out


class RegistryValidator:
    """Validates 01_CENTRAL_TASK_REGISTRY.md structure."""
    
    # Epic header patterns
    EPIC_HEADER_STD = re.compile(r"^### Epic:\s*(.+?)\s*\(Ref:\s*`([^`]+)`\)", re.IGNORECASE)
    EPIC_HEADER_LEGACY = re.compile(
        r"^### Epic:\s*(.+?)(?:\s+—\s+|\s*\(Task\s+|\s*\(Ref:|\s*\(Dossier|\s*$)",
        re.IGNORECASE,
    )
    EPIC_REF_BODY = re.compile(r"[-*]\s+\*\*Referenz:\*\*\s*`([^`]+)`")
    
    # Macro table pattern
    MACRO_TABLE_LINE = re.compile(
        r"^\|\s*([^|]+)\s*\|\s*(\d+|—)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|" +
        r"\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
    )
    
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.issues: List[ValidationIssue] = []
        self.lines: List[str] = []
        
    def load(self) -> bool:
        """Load registry file."""
        try:
            self.lines = self.registry_path.read_text(encoding="utf-8").splitlines()
            return True
        except FileNotFoundError:
            self.issues.append(ValidationIssue(
                "ERROR", 0, f"Registry file not found: {self.registry_path}",
                "Create 01_CENTRAL_TASK_REGISTRY.md"
            ))
            return False
    
    def validate_epic_headers(self):
        """Validate Epic header format."""
        for i, line in enumerate(self.lines, 1):
            if line.startswith("### Epic:"):
                # Check for standard format
                if self.EPIC_HEADER_STD.match(line):
                    continue  # OK
                
                # Check for legacy format
                if self.EPIC_HEADER_LEGACY.match(line):
                    self.issues.append(ValidationIssue(
                        "WARNING", i,
                        f"Legacy Epic header format: {line[:60]}...",
                        "Convert to: ### Epic: Name (Ref: `path/to/file.md`)"
                    ))
                else:
                    self.issues.append(ValidationIssue(
                        "ERROR", i,
                        f"Unrecognized Epic header: {line[:60]}...",
                        "Use format: ### Epic: Name (Ref: `path/to/file.md`)"
                    ))
    
    def validate_epic_references(self):
        """Validate that Epics have references (header Ref: or body **Referenz:**)."""
        in_epic = False
        epic_start_line = 0
        epic_has_ref = False
        
        for i, line in enumerate(self.lines, 1):
            if line.startswith("### Epic:"):
                if in_epic and not epic_has_ref:
                    self.issues.append(ValidationIssue(
                        "WARNING", epic_start_line,
                        f"Epic at line {epic_start_line} has no reference (no Ref: in header or **Referenz:** in body)",
                        "Add: ### Epic: Name (Ref: `path.md`) or - **Referenz:** `path.md`",
                    ))
                in_epic = True
                epic_start_line = i
                epic_has_ref = bool(self.EPIC_HEADER_STD.match(line))
            
            if in_epic and self.EPIC_REF_BODY.match(line):
                epic_has_ref = True
            
            if in_epic and line.startswith("## ") and not line.startswith("###"):
                if not epic_has_ref:
                    self.issues.append(ValidationIssue(
                        "WARNING", epic_start_line,
                        f"Epic at line {epic_start_line} has no reference (no Ref: in header or **Referenz:** in body)",
                        "Add: ### Epic: Name (Ref: `path.md`) or - **Referenz:** `path.md`",
                    ))
                in_epic = False
    
    def validate_macro_table(self):
        """Validate the active Macro-Dashboard (Copy/Paste) 12-column table only."""
        section = _h2_section_lines(self.lines, "## Macro-Dashboard (Copy/Paste")
        if not section:
            return
        in_table = False
        column_count = 0
        
        for i, line in enumerate(section, 1):
            if "| Task-ID |" in line and "Modell |" in line and "Master-Prompt" in line:
                in_table = True
                column_count = line.count("|") - 1
                if column_count != 12:
                    self.issues.append(ValidationIssue(
                        "WARNING", i,
                        f"Active Macro-Dashboard table has {column_count} columns, expected 12",
                        "Use format: | Task-ID | CU | Status | App | Modell | Prio | Cache | Tags | Meilenstein | Master-Prompt | Referenzen | Ergebnis |",
                    ))
                continue
            
            if in_table and line.strip().startswith("|---------"):
                continue
            
            if in_table and (line.strip() == "---" or (line.startswith("## ") and not line.startswith("###"))):
                break
            
            if in_table and line.strip().startswith("|"):
                row_columns = line.count("|") - 1
                if row_columns != column_count and row_columns > 0:
                    self.issues.append(ValidationIssue(
                        "ERROR", i,
                        f"Macro row has {row_columns} columns, expected {column_count}",
                        "Fix column alignment in this row",
                    ))
    
    def validate_task_epic_linkage(self):
        """Check that Macro-Tasks reference valid Epics."""
        # Extract epic names from registry
        epic_names = set()
        for line in self.lines:
            if line.startswith("### Epic:"):
                # Extract name
                match = re.match(r"^### Epic:\s*(.+?)(?:\s*\(|\s*$)", line)
                if match:
                    epic_names.add(match.group(1).strip())
        
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith("|") and not line.strip().startswith("|---------"):
                if "Epic" not in line or "Epic MCL" in line or "MCL §" in line:
                    continue
                if any(name in line for name in epic_names):
                    continue
                epic_match = re.search(r"Epic\s+(\w+)", line)
                if epic_match:
                    self.issues.append(ValidationIssue(
                        "WARNING", i,
                        f"Task references Epic '{epic_match.group(1)}' but no matching Epic header found",
                        f"Ensure Epic header exists or use one of: {', '.join(list(epic_names)[:3])}...",
                    ))
    
    def validate_task_id_uniqueness(self):
        """Task-IDs must be unique across both Macro-Dashboard tables (active + archiv)."""
        task_ids: dict[str, int] = {}

        def scan_macro_table_rows(section_lines: List[str], base_line: int) -> None:
            in_table = False
            for offset, line in enumerate(section_lines, start=1):
                abs_line = base_line + offset - 1
                if "| Task-ID |" in line and "Modell |" in line and "Master-Prompt" in line:
                    in_table = True
                    continue
                if in_table and line.strip().startswith("|---------"):
                    continue
                if in_table and (
                    line.strip() == "---"
                    or (line.startswith("## ") and not line.startswith("###"))
                ):
                    break
                if in_table and line.strip().startswith("|"):
                    cols = [c.strip() for c in line.split("|")]
                    if len(cols) >= 2:
                        tid = cols[1].strip().replace("**", "")
                        if tid and tid != "Task-ID":
                            if tid in task_ids:
                                self.issues.append(ValidationIssue(
                                    "ERROR",
                                    abs_line,
                                    f"Duplicate Task-ID: '{tid}' (first seen at line {task_ids[tid]})",
                                    "Each Task-ID must appear once across active and archive macro tables",
                                ))
                            else:
                                task_ids[tid] = abs_line

        active = _h2_section_lines(self.lines, "## Macro-Dashboard (Copy/Paste")
        if active:
            start_ln = next(
                (i for i, L in enumerate(self.lines, 1) if L.startswith("## Macro-Dashboard (Copy/Paste")),
                1,
            )
            scan_macro_table_rows(active, start_ln)
        arch = _h2_section_lines(self.lines, "## Macro-Dashboard Archiv")
        if arch:
            start_ln = next(
                (i for i, L in enumerate(self.lines, 1) if L.startswith("## Macro-Dashboard Archiv")),
                1,
            )
            scan_macro_table_rows(arch, start_ln)

        numeric_ids = [tid for tid in task_ids.keys() if tid.isdigit()]
        if numeric_ids:
            print(f"\nMacro Task-IDs (numeric): {', '.join(sorted(numeric_ids))}")
    
    def validate_markdown_structure(self):
        """Check that markdown structure is dashboard-readable (Task 035 layout)."""
        has_epics_section = False
        has_macro_section = False
        has_macro_archiv = False
        has_archived_epics = False
        has_deferred_section = False
        
        for line in self.lines:
            if "## Epics in Entwicklung" in line:
                has_epics_section = True
            if line.startswith("## Macro-Dashboard (Copy/Paste"):
                has_macro_section = True
            if line.startswith("## Macro-Dashboard Archiv"):
                has_macro_archiv = True
            if "## ✅ Archivierte & Erledigte Epics" in line:
                has_archived_epics = True
            if "## DEFERRED Pool" in line:
                has_deferred_section = True
        
        if not has_epics_section:
            self.issues.append(ValidationIssue(
                "ERROR", 0,
                "Missing '## Epics in Entwicklung' section",
                "Add Epic overview section for dashboard display",
            ))
        if not has_macro_section:
            self.issues.append(ValidationIssue(
                "ERROR", 0,
                "Missing '## Macro-Dashboard (Copy/Paste…)' section",
                "Add Macro-Dashboard table for active TODO macros",
            ))
        if not has_macro_archiv:
            self.issues.append(ValidationIssue(
                "ERROR", 0,
                "Missing '## Macro-Dashboard Archiv (DONE / SEALED)' section",
                "Move completed macro rows to an archive table at EOF",
            ))
        if not has_archived_epics:
            self.issues.append(ValidationIssue(
                "ERROR", 0,
                "Missing '## ✅ Archivierte & Erledigte Epics' section",
                "Add archived epic summary section for dashboard totals",
            ))
        if not has_deferred_section:
            self.issues.append(ValidationIssue(
                "WARNING", 0,
                "Missing '## DEFERRED Pool' section",
                "Add DEFERRED section for blocked tasks",
            ))

        dev = _h2_section_lines(self.lines, "## Epics in Entwicklung")
        if dev is not None:
            epic_headers = [ln for ln in dev if ln.startswith("### Epic:")]
            if len(epic_headers) != 1:
                self.issues.append(ValidationIssue(
                    "ERROR", 0,
                    f"'## Epics in Entwicklung' must contain exactly one '### Epic:' block (found {len(epic_headers)})",
                    "Keep only the active Universal Modal epic; move finished epics to Archivierte & Erledigte Epics",
                ))
            else:
                block = "\n".join(dev)
                for pat, label in (
                    (r"\*\*Status:\*\*", "**Status:**"),
                    (r"\*\*Progress:\*\*", "**Progress:**"),
                ):
                    if not re.search(pat, block):
                        self.issues.append(ValidationIssue(
                            "ERROR", 0,
                            f"Active epic block missing {label}",
                            "Restore Status / Progress bullet lines under the epic",
                        ))

        active_macro = _h2_section_lines(self.lines, "## Macro-Dashboard (Copy/Paste")
        h2_idx0 = next(
            (i for i, L in enumerate(self.lines) if L.startswith("## Macro-Dashboard (Copy/Paste")),
            None,
        )
        if active_macro is not None and h2_idx0 is not None:
            in_table = False
            for off, line in enumerate(active_macro):
                if "| Task-ID |" in line and "Modell |" in line:
                    in_table = True
                    continue
                if in_table and line.strip().startswith("|---------"):
                    continue
                if in_table and (line.strip() == "---" or line.startswith("## ")):
                    break
                if in_table and line.strip().startswith("|"):
                    cols = [c.strip() for c in line.split("|")]
                    if len(cols) >= 4:
                        task_id = cols[1].replace("**", "")
                        status_cell = cols[3].upper()
                        if task_id == "Task-ID":
                            continue
                        if "DONE" in status_cell or "SEALED" in status_cell or "COMPLETE" in status_cell:
                            file_line = h2_idx0 + off + 2
                            self.issues.append(ValidationIssue(
                                "ERROR",
                                file_line,
                                f"Active Macro-Dashboard row '{task_id}' must be open work (status column: {cols[3]!r})",
                                "Move DONE/SEALED rows to '## Macro-Dashboard Archiv'",
                            ))

        arch_macro = _h2_section_lines(self.lines, "## Macro-Dashboard Archiv")
        if arch_macro:
            in_table = False
            data_rows = 0
            for line in arch_macro:
                if "| Task-ID |" in line and "Modell |" in line:
                    in_table = True
                    continue
                if in_table and line.strip().startswith("|---------"):
                    continue
                if in_table and line.strip().startswith("|"):
                    cols = [c.strip() for c in line.split("|")]
                    if len(cols) >= 2 and cols[1].replace("**", "") not in ("", "Task-ID"):
                        data_rows += 1
                if in_table and line.startswith("## ") and not line.startswith("###"):
                    break
            if data_rows < 1:
                self.issues.append(ValidationIssue(
                    "ERROR", 0,
                    "Macro-Dashboard Archiv table has no data rows",
                    "Paste completed macro rows into the archive table",
                ))
    
    def validate_task_to_epic_assignment(self):
        """Validate that Macro rows referencing an Epic align with active epic headers (MCL shorthand allowed)."""
        epics: dict[str, set] = {}
        current_epic = None
        
        for line in self.lines:
            if line.startswith("### Epic:"):
                match = re.match(r"^### Epic:\s*(.+?)(?:\s*\(|$)", line)
                if match:
                    current_epic = match.group(1).strip()
                    epics[current_epic] = set()
            
            if current_epic:
                task_refs = re.findall(r"Task\s+(\d+)|M\d+|Phase\s+\d+", line, re.IGNORECASE)
                for ref in task_refs:
                    if ref:
                        epics[current_epic].add(ref)
        
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith("|") and not line.strip().startswith("|---------"):
                cols = [c.strip() for c in line.split("|")]
                if len(cols) >= 12:
                    task_id = cols[1]
                    references = cols[11]
                    
                    if references and "Epic" in references:
                        if "MCL" in references or "Universal" in references or "Modal" in references:
                            continue
                        epic_found = False
                        for epic_name in epics.keys():
                            if epic_name.split()[0] in references or any(
                                word in references for word in epic_name.split()[:2]
                            ):
                                epic_found = True
                                break
                        
                        if not epic_found:
                            epic_match = re.search(r"Epic\s+([A-Za-z]+)", references)
                            if epic_match:
                                self.issues.append(ValidationIssue(
                                    "WARNING", i,
                                    f"Task '{task_id}' references Epic '{epic_match.group(1)}' not found in Epic headers",
                                    "Check Epic name or add missing Epic to '## Epics in Entwicklung' section",
                                ))
    
    def run_all_validations(self) -> List[ValidationIssue]:
        """Run all validation checks."""
        if not self.load():
            return self.issues
        
        self.validate_epic_headers()
        self.validate_epic_references()
        self.validate_macro_table()
        self.validate_task_epic_linkage()
        self.validate_task_id_uniqueness()
        self.validate_markdown_structure()
        self.validate_task_to_epic_assignment()
        
        return self.issues

    
    def print_report(self):
        """Print validation report."""
        errors = [i for i in self.issues if i.level == "ERROR"]
        warnings = [i for i in self.issues if i.level == "WARNING"]
        infos = [i for i in self.issues if i.level == "INFO"]
        
        print("=" * 70)
        print(f"REGISTRY VALIDATION REPORT: {self.registry_path}")
        print("=" * 70)
        
        if not self.issues:
            print("OK: All validations passed. Registry is Diamond-compliant.")
            return 0
        
        print(f"\nSummary: {len(errors)} Errors, {len(warnings)} Warnings, {len(infos)} Info")
        print("-" * 70)
        
        if errors:
            print("\nERRORS (must fix):")
            for issue in errors[:10]:  # Show first 10
                print(f"  Line {issue.line:4d}: {issue.message}")
                print(f"           -> {issue.suggestion}")
        
        if warnings:
            print("\nWARNINGS:")
            for issue in warnings[:10]:
                print(f"  Line {issue.line:4d}: {issue.message}")
                print(f"           -> {issue.suggestion}")
        
        if len(errors) > 10 or len(warnings) > 10:
            print(f"\n... and {len(errors) + len(warnings) - 20} more issues")
        
        print("\n" + "=" * 70)
        return 1 if errors else 0


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate 01_CENTRAL_TASK_REGISTRY.md structure"
    )
    parser.add_argument(
        "--registry", "-r",
        type=Path,
        default=Path("01_CENTRAL_TASK_REGISTRY.md"),
        help="Path to registry file (default: 01_CENTRAL_TASK_REGISTRY.md)"
    )
    parser.add_argument(
        "--strict", "-s",
        action="store_true",
        help="Treat warnings as errors"
    )
    
    args = parser.parse_args()
    
    validator = RegistryValidator(args.registry)
    validator.run_all_validations()
    exit_code = validator.print_report()
    
    if args.strict and any(i.level == "WARNING" for i in validator.issues):
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
