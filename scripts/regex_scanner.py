#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Regex Scanner Engine with Lexical Context Awareness.
Resolves false positives by segregating Strings, Comments, and Raw Code.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

# ==============================================================================
# Token Definitions & Lexical Models
# ==============================================================================

class TokenType:
    CODE = "CODE"
    STRING_LITERAL = "STRING_LITERAL"
    SINGLE_COMMENT = "SINGLE_COMMENT"
    BLOCK_COMMENT = "BLOCK_COMMENT"

@dataclass
class Token:
    token_type: str
    content: str
    start_line: int
    end_line: int

@dataclass
class TokenizedFile:
    original_lines: List[str]
    tokens: List[Token]

# ==============================================================================
# Rule Sets
# ==============================================================================

class LinterRules:
    # ==============================================================================
    # 1. 显式懒惰关键字 (不区分大小写，严格匹配字边界)
    # ==============================================================================
    KEYWORD_PATTERNS = [
        (re.compile(r'(?i)\bTODO\b'), "Contains forbidden keyword 'TODO'"),
        (re.compile(r'(?i)\bFIXME\b'), "Contains forbidden keyword 'FIXME'"),
        (re.compile(r'(?i)\bPLACEHOLDER\b'), "Contains forbidden keyword 'PLACEHOLDER'"),
        (re.compile(r'(?i)\bXXX\b'), "Contains forbidden keyword 'XXX'"),
        (re.compile(r'(?i)\bunimplemented\b'), "Contains forbidden keyword 'unimplemented'"),
        # 新增扩展：常见缩写与占位标记
        (re.compile(r'(?i)\bTBD\b'), "Contains forbidden keyword 'TBD' (To Be Decided/Defined)"),
        (re.compile(r'(?i)\bSTUB\b'), "Contains forbidden keyword 'STUB'"),
        (re.compile(r'(?i)\bMOCK\b'), "Contains forbidden keyword 'MOCK'"),
    ]

    # ==============================================================================
    # 2. 英文指令与妥协短语 (覆盖度扩展 3x+)
    # ==============================================================================
    ENGLISH_PATTERNS = [
        # --- 原始规则 ---
        (re.compile(r'(?i)(implement\s+here)'), "Delegates implementation to the user ('implement here')"),
        (re.compile(r'(?i)(insert\s+logic)'), "Delegates implementation to the user ('insert logic')"),
        (re.compile(r'(?i)(add\s+code\s+later)'), "Postpones implementation ('add code later')"),
        (re.compile(r'(?i)(fill\s+in\s+details)'), "Delegates implementation to the user ('fill in details')"),
        
        # --- 维度 1: 简化与演示 (针对 "Simple" 系列) ---
        (re.compile(r'(?i)(simple\s+implementation)'), "Admits simplified/incomplete logic ('simple implementation')"),
        (re.compile(r'(?i)(simplified\s+(?:version|code|logic|handling|processing|impl))'), "Explicitly uses a simplified placeholder version"),
        (re.compile(r'(?i)(for\s+simplicity)'), "Skips robust logic under the guise of simplicity ('for simplicity')"),
        (re.compile(r'(?i)(for\s+(?:demo|demonstration|illustration)\s+purposes?)'), "Non-production mock/demo code detected"),
        (re.compile(r'(?i)(illustration\s+only)'), "Non-production demonstration code ('illustration only')"),
        
        # --- 维度 2: 委派与推卸 (Delegation to User) ---
        (re.compile(r'(?i)(left\s+as\s+an\s+exercise)'), "Delegates implementation to the reader/user ('left as an exercise')"),
        (re.compile(r'(?i)(insert\s+(?:actual|real|your|business)\s+logic)'), "Delegates writing real logic ('insert actual logic')"),
        (re.compile(r'(?i)(your\s+code\s+(?:here|goes\s+here))'), "Uses a placeholder for user code ('your code here')"),
        (re.compile(r'(?i)(write\s+your\s+own)'), "Delegates work back to the user ('write your own')"),
        (re.compile(r'(?i)(to\s+be\s+implemented)'), "Leaves logic unwritten ('to be implemented')"),
        (re.compile(r'(?i)(fill\s+this\s+in)'), "Delegates placeholder filling to user ('fill this in')"),
        (re.compile(r'(?i)(add\s+(?:your\s+)?custom\s+logic)'), "Delegates custom logic ('add custom logic')"),
        
        # --- 维度 3: 省略与截断 (Omission & Truncation) ---
        (re.compile(r'(?i)(omitted\s+(?:for\s+brevity|here|for\s+simplicity))'), "Omits necessary implementation ('omitted for brevity')"),
        (re.compile(r'(?i)(details?\s+omitted)'), "Details are skipped rather than coded ('details omitted')"),
        (re.compile(r'(?i)(code\s+truncated)'), "Files are lazy-truncated ('code truncated')"),
        (re.compile(r'(?i)(rest\s+of\s+the\s+(?:code|logic|implementation))'), "Refuses to output full codebase ('rest of the code')"),
        (re.compile(r'(?i)(other\s+(?:properties|fields|attributes|methods|parameters)\s+omitted)'), "Incomplete data structures ('other properties omitted')"),
        
        # --- 维度 4: 临时与暂缓 (Temporary & Postponement) ---
        (re.compile(r'(?i)((?:temporary|temp)\s+(?:stub|mock|implementation))'), "Uses a temporary/mock stub instead of real logic"),
        (re.compile(r'(?i)(stub\s+method)'), "Uses empty mock/stub declaration ('stub method')"),
        (re.compile(r'(?i)(skip(?:ped)?\s+for\s+now)'), "Skips logic implementation ('skip for now')"),
        (re.compile(r'(?i)(will\s+implement\s+later)'), "Postpones logic to future ('will implement later')"),
        (re.compile(r'(?i)(add\s+later)'), "Incomplete, intends to add later ('add later')"),
        (re.compile(r'(?i)(placeholder\s+only)'), "Expressly marks code as empty placeholder ('placeholder only')")
    ]

    # 3. Chinese laziness (High Priority - Applied heavily to comments)
    CHINESE_PATTERNS = [
        (re.compile(r'此处(?:省略|简化|添加|实现|补充|处理)'), "Chinese truncation phrase detected ('此处...')"),
        (re.compile(r'这里(?:省略|简化|添加|实现|补充|处理)'), "Chinese truncation phrase detected ('这里...')"),
        (re.compile(r'具体实现'), "Missing implementation phrase detected ('具体实现')"),
        (re.compile(r'自行(?:添加|补充|实现|处理)'), "Delegates work to user ('自行...')"),
        (re.compile(r'后续(?:补充|实现|处理)'), "Postpones implementation ('后续...')"),
        (re.compile(r'简化(?:处理|实现)'), "Admitted simplification ('简化...')"),
        (re.compile(r'未完待续'), "Incomplete marker ('未完待续')"),
        (re.compile(r'为了演示'), "Non-production demonstration code ('为了演示')"),
        (re.compile(r'等其他属性'), "Incomplete definition ('等其他属性')"),
        (re.compile(r'其它属性省略'), "Properties omitted ('其它属性省略')"),
    ]

    # 4. Symbol truncation (Applied ONLY to RAW CODE and COMMENTS, avoids strings like "Initializing...")
    SYMBOL_PATTERNS = [
        (re.compile(r'\.{3,}'), "Ellipsis truncation detected ('...')"),
    ]

# ==============================================================================
# The Context-Aware Lexer
# ==============================================================================

class RegexScanner:
    """
    A smart scanner that tokenizes source code into Strings, Comments, and Logic.
    This prevents `fprintf(stderr, "Initializing...");` from triggering the ellipsis rule,
    while still catching `/* 简化实现 */` correctly spanning multiple lines.
    """

    def tokenize_source(self, content: str, file_suffix: str) -> TokenizedFile:
        """
        A state-machine based lexical scanner.

        """
        lines = content.splitlines()
        tokens: List[Token] = []
        
        is_python = file_suffix == '.py'
        is_bash_or_ruby = file_suffix in ['.sh', '.bash', '.rb', '.yml', '.yaml']
        
        # State machine variables
        i = 0
        length = len(content)
        current_line = 1
        
        buffer = []
        state = "CODE" # CODE, STRING, SINGLE_COMMENT, BLOCK_COMMENT
        string_char = ''
        token_start_line = 1

        def push_token(new_state: str):
            nonlocal buffer, state, token_start_line
            if buffer:
                content_str = "".join(buffer)
                if content_str.strip() or state == "STRING_LITERAL":
                    tokens.append(Token(state, content_str, token_start_line, current_line))
            buffer = []
            state = new_state
            token_start_line = current_line

        while i < length:
            char = content[i]
            next_char = content[i+1] if i + 1 < length else ''
            prev_char = content[i-1] if i > 0 else ''

            if char == '\n':
                current_line += 1

            if state == "CODE":
                # Detect String Start
                if char in ('"', "'", '`'):
                    # In python, check for triple quotes
                    if is_python and i + 2 < length and char == next_char == content[i+2]:
                        push_token("STRING_LITERAL")
                        string_char = char * 3
                        buffer.extend([char, char, char])
                        i += 3
                        continue
                    else:
                        push_token("STRING_LITERAL")
                        string_char = char
                        buffer.append(char)
                        i += 1
                        continue

                # Detect C-style Comments
                if not is_python and not is_bash_or_ruby:
                    if char == '/' and next_char == '/':
                        push_token("SINGLE_COMMENT")
                        buffer.extend(['/', '/'])
                        i += 2
                        continue
                    if char == '/' and next_char == '*':
                        push_token("BLOCK_COMMENT")
                        buffer.extend(['/', '*'])
                        i += 2
                        continue

                # Detect Hash Comments (Python, Bash)
                if is_python or is_bash_or_ruby:
                    if char == '#':
                        push_token("SINGLE_COMMENT")
                        buffer.append('#')
                        i += 1
                        continue

                buffer.append(char)
                i += 1

            elif state == "STRING_LITERAL":
                buffer.append(char)
                # Escaping logic
                if prev_char != '\\':
                    if string_char in ('"""', "'''"):
                        if i + 2 < length and char == content[i+1] == content[i+2] and char == string_char[0]:
                            buffer.extend([content[i+1], content[i+2]])
                            i += 2
                            push_token("CODE")
                    else:
                        if char == string_char:
                            push_token("CODE")
                i += 1

            elif state == "SINGLE_COMMENT":
                buffer.append(char)
                if char == '\n':
                    push_token("CODE")
                i += 1

            elif state == "BLOCK_COMMENT":
                buffer.append(char)
                if char == '*' and next_char == '/':
                    buffer.append('/')
                    i += 1
                    push_token("CODE")
                i += 1

        # Push remaining
        if buffer:
            push_token("CODE")

        return TokenizedFile(lines, tokens)

    def scan_tokenized_file(self, file_path: str, tokenized_file: TokenizedFile) -> List[Dict[str, Any]]:
        violations = []
        
        # Combine rules based on token type
        all_rules = LinterRules.KEYWORD_PATTERNS + LinterRules.ENGLISH_PATTERNS + LinterRules.CHINESE_PATTERNS + LinterRules.SYMBOL_PATTERNS

        for token in tokenized_file.tokens:
            # We explicitly IGNORE STRING_LITERALS to prevent false positives in logging statements
            if token.token_type == TokenType.STRING_LITERAL:
                continue

            # Check logic lines and comments
            for pattern, reason in all_rules:
                # If it's a multi-line token (like block comment), search across it
                match = pattern.search(token.content)
                if match:
                    # Calculate accurate line number within the token
                    lines_before_match = token.content[:match.start()].count('\n')
                    exact_line = token.start_line + lines_before_match
                    
                    # Extract a clean snippet
                    snippet_lines = token.content.split('\n')
                    snippet = snippet_lines[lines_before_match].strip()
                    if len(snippet) > 80:
                        snippet = snippet[:77] + "..."

                    violations.append({
                        "file_path": file_path,
                        "line_number": exact_line,
                        "rule_name": f"REGEX_{token.token_type}_VIOLATION",
                        "snippet": f"[{reason}] -> {snippet}",
                        "suggestion": "Expand placeholder or implementation completely. Do not use shortcuts.",
                        "severity": "ERROR"
                    })

        return violations
