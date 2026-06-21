# Industrial-Grade Completeness Standards

This document defines the strict criteria for code completeness enforced by the `no-simplify-implementation` protocol. As an AI Agent, you are evaluated against these exact patterns. Any match will result in a rejected output and force a rewrite.

## 1. Absolute Prohibition of Placeholders

You must never use comment-based placeholders to skip implementation details. The internal linter uses the following Regular Expression patterns to detect lazy behavior across all programming languages:

### Explicit Lazy Keywords
The linter performs case-insensitive matching against these exact tokens:
- `\bTODO\b`
- `\bFIXME\b`
- `\bPLACEHOLDER\b`
- `\bHACK\b`
- `\bXXX\b`

### Directive Phrasing (English)
Do not write instructions to the user to finish the code:
- `implement here`
- `insert logic`
- `add code later`
- `fill in details`
- `left as an exercise`

### Directive Phrasing (Chinese)
Any Chinese phrases implying truncation or delegation are strictly forbidden:
- `此处省略` (Omitted here)
- `具体实现` (Specific implementation [left blank])
- `自行添加` (Add it yourself)
- `自行处理` (Handle it yourself)
- `后续补充` / `后续实现` (To be added/implemented later)
- `简化处理` / `简化实现` (Simplified handling/implementation)
- `未完待续` (To be continued)
- `为了演示` (For demonstration purposes [implying non-production])

### Ellipsis Truncation
Never use consecutive dots to skip logic:
- `\.{3,}` (Matches `...`, `....`, etc. in comments, strings, or code bodies).

## 2. Structural Completeness Rules

Beyond comments, the structure of the code itself must represent a fully functioning system.

### No Empty Error Blackholes
If you catch an exception or check for an error, you must handle it. 
- **Forbidden:** `try { ... } catch (Exception e) {}`
- **Forbidden:** `if err != nil {}`
- **Required:** Log the error, implement exponential backoff retries, map it to a domain-specific error code, or gracefully terminate the process.

### No Empty Functions or Classes
- **Python:** Functions containing only `pass`, `...`, or raising `NotImplementedError` will trigger an immediate failure.
- **C-Style (JS, TS, Go, Java, C++):** Functions with an empty body `{}` without returning a valid fallback type or implementing the logic are flagged as lazy.

## 3. Data and Edge Case Exhaustiveness

To meet the industrial-grade standard, your code must demonstrate:
- **Comprehensive Boundary Checks:** Validate nulls, empty strings, array bounds, and invalid types before processing.
- **Full Configuration:** Do not hardcode parameters. Implement environment variable loading or configuration file parsing.
- **Robust Resource Management:** Ensure database connections, file handles, and network sockets are strictly closed using `defer`, `finally`, or context managers (`with`), even when exceptions occur.
