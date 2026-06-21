# No-Simplify Implementation Skill
[中文](README_CN.md)

## **No**` // Simplified implementation`, **No**` // Omitted here`, **No` // Simple implementation is used here... actual needs...`!
**Industrial-Grade Integrity Enforcement Protocol** — Absolutely no acceptance of any form of laziness, placeholders, simplifications, or toy-level demos.

## Introduction

`no-simplify-implementation` is a high-constraint Skill designed specifically for code generation scenarios. It forces the AI to produce **100% complete, production-ready, and ready-to-deploy** code, completely eradicating TODOs, FIXMEs, "...", empty exception handling, empty functions, mock implementations, and any traces of "simplified demonstration."

Unlike most "code assistance" tools on the market, this Skill has a built-in **hybrid dynamic + static** rigorous analyzer (including AST parsing, structural metrics, and heuristic mock detection), capable of performing industrial-grade integrity verification immediately after generation. Only code that passes the linter (exit code 0) is considered qualified.

### Core Philosophy

Existing Skills and projects often boast "conciseness + guaranteed robustness," which sounds professional but actually provides more opportunities for models to take advantage. Those Skill projects that claim to have beautiful code structures and shout loud slogans (frequently using terms like "industrial grade" or "enterprise level"), while in reality being just toy-level demos, are precisely what give the most room for lazy implementation to survive—appearing clean and tidy on the surface, while being empty inside, always leaving "to be added later" or a pretty comment where robust logic is truly needed. This "elegant laziness" is the most dangerous. **We choose the opposite:** we would rather write one extra line of real logic than accept one line of seemingly refined nonsense.

## Features

- **Multi-language Laziness Detection**: Supports mainstream languages such as Python, JS/TS, Go, Java, C/C++, etc.
- **Context-Aware Lexer**: Distinguishes between strings, comments, and real code to avoid false positives.
- **Hardcore Structural Analyzer**: Detects empty exceptions, empty functions, constant returns, print-only mock implementations, and "complexly named" functions with abnormally low complexity.
- **Full Coverage of Chinese/English/Symbols**: Includes various placeholders such as "omitted here," "simplified implementation," "for simplicity," "...", etc.
- **Incremental Repair Loop**: Locates, edits, and re-verifies issues immediately upon discovery until passing.
- **Parallel Scanning + Rich Reporting**: Supports directory batch scanning, JSON output, and colored terminal reports.

## Installation and Usage (OpenClaw Environment)

```bash clawhub install no-simplify-implementation

``` Manually run `/no-simplify-implementation` during the dialog (the model will not call it automatically)

### Recommended Workflow

1. Activate this Skill before any task that requires code generation.

2. The model begins writing industrial-grade code.

3. Deliver to the user (you) only after the entire project has passed a final scan.

**Core linter command** (in the workspace directory):
```bash
python3 skills/no-simplify-implementation/scripts/main.py workspace/
# Or for a single file
python3 skills/no-simplify-implementation/scripts/main.py workspace/yourfile.py
```

## Use Cases

- Development of large-scale system components.
- Implementation of production-grade scripts / services / toolchains.
- Refactoring legacy code with a requirement for total elimination of technical debt.
- Teams or individuals who need to gatekeep the quality of AI output.

## Why You Need It

Because most AI-generated code, under the packaging of "concise and elegant," cannot actually withstand scrutiny. Once it encounters a real production environment (boundary conditions, error handling, resource management, configuration loading), it immediately reveals its toy nature.

The purpose of `no-simplify-implementation` is to kill such "looks like, but isn't" code directly before delivery. It accepts no compromises, no "demonstration purposes," and no "to be improved later." It only accepts a complete implementation that is **runnable, maintainable, and deployable.**

## License and Contribution

MIT License. PRs to enhance detection rules or support more languages are welcome.

---

**After using this Skill, what you deliver will no longer be "code that looks good," but a truly industrial-grade, complete implementation that can withstand scrutiny.**

Welcome to strictly execute it in your actual projects — it will make you (and the model) become more honest.
