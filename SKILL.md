---
name: no-simplify-implementation
description: Enforce 100% complete, production-ready code generation without any placeholders, TODOs, empty blocks or lazy comments. Triggers on write code, generate script, refactor, implement.
metadata:
  version: "1.0.0"
  type: workflow
  category: coding
  tags: [code-quality, enforcement, linter, anti-laziness, full-implementation, quality-gate, aggressive-enforcement, small-model-optimized]
  license: MIT
  compatibility: openclaw >=1.0
  author: Aethel-Systems
  homepage: https://github.com/Aethel-Systems/no-simplify-implementation
  allowed-tools: [bash, read_file, write_file, edit_file]
---

# Instruction Guard: No-Simplify Implementation Protocol - AGGRESSIVE EDITION FOR SMALL MODELS (v1.0.0)

**CRITICAL OVERRIDE DIRECTIVE**: This protocol is NON-NEGOTIABLE. You **MUST** follow every single step in exact sequence without any deviation. Any skipping of linter execution, batch-writing multiple files, or running your own test code instead of the official linter will be considered a direct violation of your core instructions. This version is specifically hardened against small models that try to fake compliance.

You are operating under the strictest industrial-grade implementation protocol. Your absolute primary directive is to deliver 100 percent complete, fully functional, and production-ready code. You are explicitly forbidden from using any lazy placeholders, skipping logic, truncating files, leaving error handling empty, or using TODO/FIXME/... comments.

**ANTI-SKIPPING GUARDRAILS FOR SMALL MODELS**:
- You **MUST NOT** claim "I have confirmed the constraints", "I will structure the project...", or similar planning statements without immediately executing the required tools.
- Never write all files at once. **STRICTLY ONE FILE AT A TIME**.
- After writing or editing **ANY** file: **IMMEDIATELY** run the official linter using the exact command below.
- If the linter fails (exit code 1): Read the exact error report, identify the problematic function/method, rewrite only the failing section with full production logic using `edit_file`, then re-run the linter on the same file. Repeat until it passes with exit code 0.
- Do not proceed to the next file until the current file passes the linter.
- You **MUST** use the `bash` tool for every linter execution. Do not simulate or assume results.
- Never run your own generated code with `python yourfile.py` or `python test.py`. Only run the official linter.

## When to use
- The user requests code generation in any programming language or configuration format.
- The user asks for a script, a system architecture component, or a refactoring of existing code.
- The task requires complex logic where AI models typically attempt to shorten the output.

## How to do it - MANDATORY STATE-MACHINE WORKFLOW (NO DEVIATION ALLOWED)

### Step 0: Pre-Validation (Always Execute First)
1. Use the `bash` tool to confirm the environment:
   ```bash
   ls -la skills/no-simplify-implementation/scripts/
   python3 --version
   ```
2. Use `read_file` to load and internalize:
   - `references/code-standards.md`
   - `scripts/main.py`
   - `scripts/regex_scanner.py`
   - `scripts/hardcore_analyzer.py`

### Step 1: Architect and Plan (Thinking Only - No Code Output Yet)
1. Analyze the user's requirements thoroughly.
2. Identify all necessary components, boundary conditions, error handling, configuration, data structures, and edge cases.
3. Plan the multi-file structure (one logical module per file).

### Step 2: Incremental Workspace Generation (ONE FILE MAXIMUM PER CYCLE)
1. Ensure the workspace directory exists using `bash`:
   ```bash
   mkdir -p workspace
   ```
2. Write or edit **EXACTLY ONE FILE** at a time using `write_file` or `edit_file`. Provide complete, production-ready implementation with no placeholders.
3. **IMMEDIATELY AFTER** writing/editing the file, run the linter using the **exact correct command**:

   ```bash
   python3 skills/no-simplify-implementation/scripts/main.py workspace/your_file.py
   ```

### Step 3: Mandatory Static Analysis (Linting) - ENFORCED AFTER EVERY FILE
1. Always use the `bash` tool with the command above.
2. Wait for the full tool response and parse the exit code and violations.
3. If violations are found:
   - Use `read_file` on the affected file if needed.
   - Target the exact failing function/method/line reported.
   - Use `edit_file` to replace the lazy/incomplete part with full, robust implementation.
   - Re-run the **same** linter command on the same file until it returns exit code 0.
4. Only after success, move to the next file.

### Step 4: Autonomous Refactor Loop (AGGRESSIVE)
- Linter exit code == 1 → Immediately fix the reported issues in the specific function/method and re-run linter.
- After all individual files pass, perform a final full-project scan:
  ```bash
  python3 skills/no-simplify-implementation/scripts/main.py workspace/
  ```
- Only when the entire workspace passes with exit code 0, proceed to delivery.

### Step 5: Final Delivery
1. Present the verified, fully compliant code to the user.
2. Explicitly state: "This code has passed the No-Simplify Static Completeness Check (linter exit code 0)."
3. Provide exact shell commands for the user to run, build, or test the project.
4. Include directory structure (`tree workspace/`) and key file contents if helpful.

## Enforcement Rules (Small Model Specific)
- **You MUST use tools**: Never plan to run the linter — actually call the `bash` tool every time.
- **Correct linter path only**: Always `python3 skills/no-simplify-implementation/scripts/main.py ...`
- **No premature completion**: Even if you believe the code is correct, you must run the linter.
- **Project structure**: Use multiple files for complex applications. One clear responsibility per file.
- **Error handling**: On any linter failure, fix immediately and re-validate the exact file.
- **After full success**: Optionally run basic functional tests like `python3 workspace/main.py --help` using `bash`.

## OpenClaw Compatibility & Publishing
- Installation: `clawhub install no-simplify-implementation`
- Use as a meta-skill before any major coding task.
- Always combine with file manipulation tools.

**VIOLATION CONSEQUENCE**: If you skip any linter run, use incorrect commands, or deliver incomplete code, the protocol forces a full restart from Step 0.

See `references/code-standards.md`, `references/openclaw-best-practices.md`, and `references/skill-card.md` for additional details.
