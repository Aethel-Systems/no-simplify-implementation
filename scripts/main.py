#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Industrial-Grade Laziness Linter for AI-Generated Code - Core Orchestrator.
Version: 4.0.0 (Enterprise Edition)
Author: Industrial Compliance Engine
Description: Main entry point providing multiprocessing, configuration management,
and rich reporting. It delegates to the RegexScanner and HardcoreAnalyzer.
"""

import argparse
import concurrent.futures
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Ensure local imports work correctly when run from different directories
sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    from regex_scanner import RegexScanner, TokenizedFile
    from hardcore_analyzer import HardcoreAnalyzer
except ImportError as e:
    print(f"FATAL ERROR: Failed to import submodules. Ensure regex_scanner.py and hardcore_analyzer.py are in the same directory as main.py. Details: {e}")
    sys.exit(2)

# ==============================================================================
# Domain Models & Configuration
# ==============================================================================

@dataclass
class Violation:
    file_path: str
    line_number: int
    rule_name: str
    snippet: str
    suggestion: str
    severity: str = "ERROR" # ERROR, WARNING, CRITICAL

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class ScanResult:
    file_path: str
    is_success: bool
    violations: List[Violation]
    execution_time_ms: float
    error_message: Optional[str] = None

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class LoggerSetup:
    @staticmethod
    def configure(level: int = logging.INFO) -> logging.Logger:
        logger = logging.getLogger("LinterCore")
        logger.setLevel(level)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(f'%(asctime)s - %(name)s - {Colors.BOLD}%(levelname)s{Colors.ENDC} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

# ==============================================================================
# Core Orchestration Engine
# ==============================================================================

class LinterOrchestrator:
    def __init__(self, debug: bool = False, max_workers: int = 4):
        self.logger = LoggerSetup.configure(logging.DEBUG if debug else logging.INFO)
        self.max_workers = max_workers
        self.allowed_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.rs', '.php', '.rb', '.swift', '.kt', '.sh', '.bash'
        }
        self.regex_scanner = RegexScanner()
        self.hardcore_analyzer = HardcoreAnalyzer()

    def discover_files(self, targets: List[str]) -> List[Path]:
        """Deep traversal of target directories to find supported source files."""
        discovered: set[Path] = set()
        for target in targets:
            path = Path(target).resolve()
            if not path.exists():
                self.logger.warning(f"Target path does not exist: {path}")
                continue

            if path.is_file():
                if path.suffix.lower() in self.allowed_extensions:
                    discovered.add(path)
                else:
                    self.logger.warning(f"File extension not supported for deep analysis, but will run regex: {path}")
                    discovered.add(path)
            elif path.is_dir():
                for root, _, files in os.walk(path):
                    for file_name in files:
                        file_path = Path(root) / file_name
                        if file_path.suffix.lower() in self.allowed_extensions:
                            discovered.add(file_path)

        sorted_files = sorted(list(discovered))
        self.logger.info(f"Discovered {len(sorted_files)} source files for strict validation.")
        return sorted_files

    def read_file_safely(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Reads file with aggressive encoding fallback strategies."""
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'gbk']
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content, None
            except UnicodeDecodeError:
                continue
            except Exception as e:
                return None, f"OS/IO Error reading file: {str(e)}"
        return None, "Exhausted all decoding strategies. File appears to be binary or corrupted."

    def process_single_file(self, file_path: Path) -> ScanResult:
        """Pipeline for executing all scanners on a single file."""
        start_time = time.time()
        violations: List[Violation] = []
        
        self.logger.debug(f"Initiating strict scan on: {file_path}")

        content, err = self.read_file_safely(file_path)
        if err or content is None:
            violation = Violation(
                file_path=str(file_path),
                line_number=0,
                rule_name="IO_UNREADABLE",
                snippet="N/A",
                suggestion="Ensure the file is a valid text file with UTF-8 encoding.",
                severity="CRITICAL"
            )
            return ScanResult(str(file_path), False, [violation], (time.time() - start_time) * 1000, err)

        if not content.strip():
            violation = Violation(
                file_path=str(file_path),
                line_number=1,
                rule_name="EMPTY_FILE",
                snippet="<EOF>",
                suggestion="The file is completely empty. You must implement the logic.",
                severity="CRITICAL"
            )
            return ScanResult(str(file_path), False, [violation], (time.time() - start_time) * 1000)

        # 1. Regex Scanner (Context-Aware)
        try:
            tokenized_file = self.regex_scanner.tokenize_source(content, file_path.suffix)
            regex_violations_data = self.regex_scanner.scan_tokenized_file(str(file_path), tokenized_file)
            for v_data in regex_violations_data:
                violations.append(Violation(**v_data))
        except Exception as e:
            self.logger.error(f"RegexScanner crashed on {file_path}: {e}")
            violations.append(Violation(
                file_path=str(file_path), line_number=0, rule_name="SCANNER_CRASH",
                snippet=str(e), suggestion="Internal engine error during regex scanning. Check syntax.", severity="ERROR"
            ))
            return ScanResult(str(file_path), False, violations, (time.time() - start_time) * 1000)

        # 2. Hardcore Dynamic/Static Analyzer
        try:
            hardcore_violations_data = self.hardcore_analyzer.analyze(str(file_path), content, file_path.suffix)
            for v_data in hardcore_violations_data:
                violations.append(Violation(**v_data))
        except Exception as e:
            self.logger.error(f"HardcoreAnalyzer crashed on {file_path}: {e}")
            violations.append(Violation(
                file_path=str(file_path), line_number=0, rule_name="ANALYZER_CRASH",
                snippet=str(e), suggestion="Internal engine error during deep structural analysis.", severity="ERROR"
            ))

        exec_time = (time.time() - start_time) * 1000
        return ScanResult(str(file_path), len(violations) == 0, violations, exec_time)

    def execute_pipeline(self, target_paths: List[str]) -> List[ScanResult]:
        """Runs the complete execution pipeline utilizing parallel processing."""
        files = self.discover_files(target_paths)
        if not files:
            self.logger.warning("No target files matched the criteria. Aborting run.")
            return []

        results: List[ScanResult] = []
        
        # Parallel Execution
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.process_single_file, fp): fp for fp in files}
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    self.logger.error(f"Process crashed while processing {file_path}. Reason: {exc}")
                    fallback_violation = Violation(str(file_path), 0, "FATAL_PROCESS_CRASH", str(exc), "Engine failure.")
                    results.append(ScanResult(str(file_path), False, [fallback_violation], 0.0, str(exc)))

        # Sort results by file path for deterministic output
        results.sort(key=lambda x: x.file_path)
        return results

# ==============================================================================
# UI and Reporting Layer
# ==============================================================================

class Reporter:
    @staticmethod
    def report_terminal(results: List[ScanResult]):
        total_files = len(results)
        total_violations = sum(len(res.violations) for res in results)
        
        print("\n" + "="*80)
        print(f" {Colors.BOLD}NO-SIMPLIFY INDUSTRIAL LINTER v4.0.0 - EXECUTION REPORT{Colors.ENDC} ".center(80 + len(Colors.BOLD) + len(Colors.ENDC), "="))
        print("="*80)

        if total_violations == 0:
            print(f"\n{Colors.OKGREEN}🟢 LINTER PASSED: ZERO LAZINESS DETECTED{Colors.ENDC}")
            print(f"Successfully verified {total_files} file(s).")
            print("The codebase has passed the industrial completeness check.")
            print("You may proceed to deliver the final code to the user.\n")
            print("="*80 + "\n")
            return 0

        print(f"\n{Colors.FAIL}🚨 LAZINESS VIOLATION: LINTER FAILED (Found {total_violations} issues in {total_files} files) 🚨{Colors.ENDC}\n")
        
        issue_counter = 1
        for res in results:
            if not res.violations:
                continue
                
            print(f"{Colors.OKBLUE}File:{Colors.ENDC} {Colors.BOLD}{res.file_path}{Colors.ENDC}")
            for v in res.violations:
                severity_color = Colors.FAIL if v.severity in ["ERROR", "CRITICAL"] else Colors.WARNING
                print(f"  {severity_color}[Issue #{issue_counter}]{Colors.ENDC} Line {v.line_number}")
                print(f"    {Colors.BOLD}Rule:{Colors.ENDC} {v.rule_name}")
                print(f"    {Colors.BOLD}Code:{Colors.ENDC} {v.snippet}")
                print(f"    {Colors.BOLD}Fix :{Colors.ENDC} {v.suggestion}")
                print("  " + "-"*76)
                issue_counter += 1
            print()

        print(f"{Colors.WARNING}[AGENT INSTRUCTION]:{Colors.ENDC}")
        print("You MUST rewrite the identified sections to be fully complete.")
        print("Placeholders, empty error handlers, Mock-implementations, and missing logic are strictly forbidden.")
        print("Re-run the linter after applying your exhaustive fixes.\n")
        print("="*80 + "\n")
        return 1

    @staticmethod
    def report_json(results: List[ScanResult]):
        total_violations = sum(len(res.violations) for res in results)
        output = {
            "status": "SUCCESS" if total_violations == 0 else "FAILED",
            "metrics": {
                "total_files_scanned": len(results),
                "total_violations": total_violations
            },
            "results": [
                {
                    "file": res.file_path,
                    "is_success": res.is_success,
                    "execution_time_ms": round(res.execution_time_ms, 2),
                    "violations": [v.to_dict() for v in res.violations]
                }
                for res in results if not res.is_success
            ]
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0 if total_violations == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Strict static analyzer to prevent lazy code generation (Industrial Grade).")
    parser.add_argument("target", type=str, nargs="+", help="File(s) or directory to scan.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging.")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers (default: 4).")
    
    args = parser.parse_args()
    
    orchestrator = LinterOrchestrator(debug=args.debug, max_workers=args.workers)
    results = orchestrator.execute_pipeline(args.target)
    
    if not results:
        print("No valid target files found. Exiting with code 0.")
        sys.exit(0)
        
    if args.json:
        exit_code = Reporter.report_json(results)
    else:
        exit_code = Reporter.report_terminal(results)
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
