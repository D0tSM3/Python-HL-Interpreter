"""
Name: Castillo, Carl Rohan
Course and Section: CSS125L - AM3
Procedures: Simple HL Language Interpreter (HLInt)

Start
    PROCEDURE 1 (Castillo): Read the .HL source file.
    PROCEDURE 2 (Castillo): Remove spaces and write NOSPACES.TXT.
    PROCEDURE 3 (Castillo): Perform lexical analysis (tokenize the source).
    PROCEDURE 4 (Castillo): Write reserved words and symbols to RES_SYM.TXT.
    PROCEDURE 5 (Castillo): Perform syntax analysis (parse tokens into AST).
    PROCEDURE 6 (Castillo): Interpret and execute the AST if no errors.
    PROCEDURE 7 (Castillo): Report ERROR or NO ERROR(S) FOUND.
End
"""

import sys


# ============================================================
# TOKEN TYPES
# ============================================================

# Each token is a tuple: (token_type, value).
# Used across PROCEDURE 3 (Castillo) - lexical analysis,
# PROCEDURE 4 (Castillo) - RES_SYM.TXT output,
# and PROCEDURE 5 (Castillo) - syntax analysis.
# Token types:
TOKEN_KEYWORD    = "KEYWORD"       # integer, double, output, if
TOKEN_IDENTIFIER = "IDENTIFIER"    # single lowercase letter (a-z)
TOKEN_INT_LIT    = "INT_LITERAL"   # e.g. 5, 3, 42
TOKEN_DOUBLE_LIT = "DOUBLE_LITERAL"# e.g. 2.35, 1.25
TOKEN_STRING_LIT = "STRING_LITERAL"# e.g. "hello"
TOKEN_OPERATOR   = "OPERATOR"      # +, -, <, >, ==, !=
TOKEN_SYMBOL     = "SYMBOL"        # :, ;, :=, =, <<, (, )
TOKEN_NEWLINE    = "NEWLINE"       # line breaks (used to track lines)
TOKEN_EOF        = "EOF"           # end of input

# Keywords recognized by HL
KEYWORDS = {"integer", "double", "output", "if"}


# ============================================================
# PROCEDURES 1 & 2 (Castillo): FILE READING AND SPACE REMOVAL
# ============================================================

# Reads the .HL source file and returns its content as a list of lines.
# Called during PROCEDURE 1 (Castillo) - see main().
def read_source(filename):
    """Read the .HL source file and return its content as a list of lines."""
    try:
        with open(filename, "r") as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)


# Removes all space characters from each line, preserving newlines.
# Called during PROCEDURE 2 (Castillo) - see main().
def remove_spaces(lines):
    """Remove all space characters from each line, preserving newlines.
    Returns a list of cleaned lines (without trailing newline characters)."""
    cleaned = []
    for line in lines:
        # Strip the newline, remove all spaces, keep the rest
        cleaned_line = line.rstrip("\n").replace(" ", "")
        cleaned.append(cleaned_line)
    return cleaned


# Writes the space-removed source to NOSPACES.TXT.
# Called during PROCEDURE 2 (Castillo) - see main().
def write_nospaces(cleaned_lines, filename="NOSPACES.TXT"):
    """Write the space-removed source to NOSPACES.TXT."""
    with open(filename, "w") as f:
        for line in cleaned_lines:
            if line:  # skip blank lines
                f.write(line + "\n")


# ============================================================
# PROCEDURE 3 (Castillo): LEXER (LEXICAL ANALYSIS)
# ============================================================

# Character-by-character scanner that produces a list of tokens
# from the space-removed source text.
# Called during PROCEDURE 3 (Castillo) - see main().
class Lexer:
    """Character-by-character scanner that produces a list of tokens
    from the space-removed source text.

    How it works:
      - Walk through each character in the source
      - Recognize keywords, identifiers, numbers, strings, operators, symbols
      - Return a list of (token_type, value) tuples
    """

    def __init__(self, text):
        self.text = text       # the full source (spaces already removed)
        self.pos = 0           # current position in text
        self.tokens = []       # accumulated tokens
        self.has_error = False  # set to True if an unknown character is found

    def peek(self):
        """Look at the current character without consuming it."""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def advance(self):
        """Consume and return the current character."""
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def tokenize(self):
        """Scan the entire source and return the list of tokens."""
        while self.pos < len(self.text):
            ch = self.peek()

            # --- Skip newlines (track them but don't produce meaningful tokens) ---
            if ch == "\n":
                self.advance()
                continue

            # --- Identifiers and keywords ---
            # Start with a letter → could be a keyword or identifier
            if ch.isalpha():
                self._read_word()

            # --- Numbers (integer or double literals) ---
            elif ch.isdigit():
                self._read_number()

            # --- String literals ---
            elif ch == '"':
                self._read_string()

            # --- Two-character symbols and operators ---
            elif ch == ':':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append((TOKEN_SYMBOL, ":="))
                else:
                    self.tokens.append((TOKEN_SYMBOL, ":"))

            elif ch == '<':
                self.advance()
                if self.peek() == '<':
                    self.advance()
                    self.tokens.append((TOKEN_SYMBOL, "<<"))
                else:
                    self.tokens.append((TOKEN_OPERATOR, "<"))

            elif ch == '=':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append((TOKEN_OPERATOR, "=="))
                else:
                    self.tokens.append((TOKEN_SYMBOL, "="))

            elif ch == '!':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append((TOKEN_OPERATOR, "!="))
                else:
                    # Standalone '!' is not valid in HL, but we tokenize it
                    # and let the parser report the error
                    self.tokens.append((TOKEN_SYMBOL, "!"))

            elif ch == '>':
                self.advance()
                self.tokens.append((TOKEN_OPERATOR, ">"))

            # --- Single-character symbols ---
            elif ch == ';':
                self.advance()
                self.tokens.append((TOKEN_SYMBOL, ";"))

            elif ch == '(':
                self.advance()
                self.tokens.append((TOKEN_SYMBOL, "("))

            elif ch == ')':
                self.advance()
                self.tokens.append((TOKEN_SYMBOL, ")"))

            elif ch == '+':
                self.advance()
                self.tokens.append((TOKEN_OPERATOR, "+"))

            elif ch == '-':
                self.advance()
                self.tokens.append((TOKEN_OPERATOR, "-"))

            else:
                # Unrecognized character — flag a lexical error
                self.has_error = True
                self.advance()

        self.tokens.append((TOKEN_EOF, ""))
        return self.tokens

    def _read_word(self):
        """Read a word (letters only). Determine if it's a keyword or identifier."""
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isalpha():
            self.pos += 1
        word = self.text[start:self.pos]

        # Case-insensitive keyword check
        if word.lower() in KEYWORDS:
            self.tokens.append((TOKEN_KEYWORD, word.lower()))
        else:
            self.tokens.append((TOKEN_IDENTIFIER, word))

    def _read_number(self):
        """Read an integer or double literal."""
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1

        # Check for decimal point → double literal
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            self.pos += 1  # consume the '.'
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
            self.tokens.append((TOKEN_DOUBLE_LIT, self.text[start:self.pos]))
        else:
            self.tokens.append((TOKEN_INT_LIT, self.text[start:self.pos]))

    def _read_string(self):
        """Read a string literal enclosed in double quotes."""
        self.advance()  # consume opening "
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            if self.text[self.pos] == '\n':
                # Unterminated string — stop at newline
                break
            self.pos += 1

        value = self.text[start:self.pos]

        if self.pos < len(self.text) and self.text[self.pos] == '"':
            self.advance()  # consume closing "
        else:
            # Missing closing quote — flag a lexical error
            self.has_error = True

        self.tokens.append((TOKEN_STRING_LIT, value))


# Writes reserved words and symbols/operators to RES_SYM.TXT.
# Called during PROCEDURE 4 (Castillo) - see main().
def write_res_sym(tokens, filename="RES_SYM.TXT"):
    """Write reserved words and symbols/operators to RES_SYM.TXT.
    Excludes identifiers, literals, and EOF."""
    with open(filename, "w") as f:
        for token_type, value in tokens:
            if token_type in (TOKEN_KEYWORD, TOKEN_SYMBOL, TOKEN_OPERATOR):
                f.write(value + "\n")


# ============================================================
# AST NODE DEFINITIONS
# ============================================================
# Data structures that connect PROCEDURE 5 (Castillo) - syntax analysis
# to PROCEDURE 6 (Castillo) - interpretation.
# The parser produces these nodes. The interpreter walks them.

class DeclarationNode:
    """Variable declaration: x:integer; or y:double;"""
    def __init__(self, name, var_type):
        self.name = name          # e.g. "x"
        self.var_type = var_type   # "integer" or "double"

    def __repr__(self):
        return f"Declare({self.name}: {self.var_type})"


class AssignmentNode:
    """Assignment with :=   e.g. x:=5;"""
    def __init__(self, name, value_expr):
        self.name = name
        self.value_expr = value_expr  # an expression node

    def __repr__(self):
        return f"Assign({self.name} := {self.value_expr})"


class MathAssignmentNode:
    """Assignment with =   e.g. x = 3 + 2;"""
    def __init__(self, name, value_expr):
        self.name = name
        self.value_expr = value_expr

    def __repr__(self):
        return f"MathAssign({self.name} = {self.value_expr})"


class OutputNode:
    """Output statement: output<<expr; or output<<"string";"""
    def __init__(self, value):
        self.value = value  # a StringNode or expression node

    def __repr__(self):
        return f"Output({self.value})"


class IfNode:
    """One-way conditional: if(condition) statement"""
    def __init__(self, condition, body):
        self.condition = condition  # a ConditionNode
        self.body = body            # a single statement node

    def __repr__(self):
        return f"If({self.condition}) then {self.body}"


class BinOpNode:
    """Binary operation: left op right (for + and -)"""
    def __init__(self, left, op, right):
        self.left = left
        self.op = op        # "+" or "-"
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class ConditionNode:
    """Comparison: left op right (for <, >, ==, !=)"""
    def __init__(self, left, op, right):
        self.left = left
        self.op = op        # "<", ">", "==", "!="
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class NumberNode:
    """An integer or double literal."""
    def __init__(self, value, num_type):
        self.value = value        # the numeric value (int or float)
        self.num_type = num_type  # "integer" or "double"

    def __repr__(self):
        return f"{self.value}"


class IdentifierNode:
    """A variable reference."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.name}"


class StringNode:
    """A string literal."""
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'"{self.value}"'


# ============================================================
# PROCEDURE 5 (Castillo): PARSER (SYNTAX ANALYSIS) — Tokens → AST
# ============================================================

# Recursive-descent parser that reads the token list and produces
# an AST (list of statement nodes). Sets has_error = True if any
# syntax error is found.
# Called during PROCEDURE 5 (Castillo) - see main().
class Parser:
    """Recursive-descent parser that reads the token list and produces
    an AST (list of statement nodes). Sets has_error = True if any
    syntax error is found.

    Grammar (derived from the HL spec):

        program        → statement*
        statement      → declaration | assignment | math_assignment
                       | output_stmt | if_stmt
        declaration    → IDENTIFIER ':' ('integer'|'double') ';'
        assignment     → IDENTIFIER ':=' expression ';'
        math_assignment→ IDENTIFIER '=' expression ';'
        output_stmt    → 'output' '<<' (STRING_LIT | expression) ';'
        if_stmt        → 'if' '(' condition ')' statement
        condition      → expression ('<'|'>'|'=='|'!=') expression
        expression     → term (('+'|'-') term)*
        term           → INT_LIT | DOUBLE_LIT | IDENTIFIER
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.has_error = False
        self.ast = []  # list of statement nodes

    def current(self):
        """Return the current token, or EOF if past the end."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (TOKEN_EOF, "")

    def peek_type(self):
        return self.current()[0]

    def peek_value(self):
        return self.current()[1]

    def consume(self, expected_type=None, expected_value=None):
        """Consume and return the current token.
        If expected_type or expected_value is given, check they match."""
        tok = self.current()
        if expected_type and tok[0] != expected_type:
            self.has_error = True
            return None
        if expected_value and tok[1] != expected_value:
            self.has_error = True
            return None
        self.pos += 1
        return tok

    def parse_program(self):
        """Parse the full token stream as a sequence of statements."""
        while self.peek_type() != TOKEN_EOF:
            if self.has_error:
                break
            stmt = self.parse_statement()
            if stmt is not None:
                self.ast.append(stmt)
            elif not self.has_error:
                # Could not parse a statement and no error flagged — skip token
                self.has_error = True
                break
        return self.ast

    def parse_statement(self):
        """Determine the statement type and dispatch to the right parser."""
        tok_type, tok_val = self.current()

        # --- output statement ---
        if tok_type == TOKEN_KEYWORD and tok_val == "output":
            return self.parse_output()

        # --- if statement ---
        if tok_type == TOKEN_KEYWORD and tok_val == "if":
            return self.parse_if()

        # --- Starts with an identifier: declaration, assignment, or math_assignment ---
        if tok_type == TOKEN_IDENTIFIER:
            return self.parse_identifier_statement()

        # --- Unrecognized token at statement level ---
        self.has_error = True
        return None

    def parse_identifier_statement(self):
        """An identifier can start a declaration, := assignment, or = assignment.
        We look ahead to decide which one."""
        # Save position in case we need to backtrack
        name_tok = self.consume(TOKEN_IDENTIFIER)
        if name_tok is None:
            return None
        name = name_tok[1]

        next_tok = self.current()

        # Declaration: IDENTIFIER ':' TYPE ';'
        if next_tok[0] == TOKEN_SYMBOL and next_tok[1] == ":":
            return self.parse_declaration(name)

        # := Assignment: IDENTIFIER ':=' expression ';'
        if next_tok[0] == TOKEN_SYMBOL and next_tok[1] == ":=":
            return self.parse_assignment(name)

        # = Math assignment: IDENTIFIER '=' expression ';'
        if next_tok[0] == TOKEN_SYMBOL and next_tok[1] == "=":
            return self.parse_math_assignment(name)

        self.has_error = True
        return None

    def parse_declaration(self, name):
        """Parse: (name already consumed) ':' TYPE ';' """
        if self.consume(TOKEN_SYMBOL, ":") is None:
            return None

        type_tok = self.current()
        if type_tok[0] == TOKEN_KEYWORD and type_tok[1] in ("integer", "double"):
            self.consume()
        else:
            self.has_error = True
            return None

        if self.consume(TOKEN_SYMBOL, ";") is None:
            return None

        return DeclarationNode(name, type_tok[1])

    def parse_assignment(self, name):
        """Parse: (name already consumed) ':=' expression ';' """
        if self.consume(TOKEN_SYMBOL, ":=") is None:
            return None

        expr = self.parse_expression()
        if expr is None:
            return None

        if self.consume(TOKEN_SYMBOL, ";") is None:
            return None

        return AssignmentNode(name, expr)

    def parse_math_assignment(self, name):
        """Parse: (name already consumed) '=' expression ';' """
        if self.consume(TOKEN_SYMBOL, "=") is None:
            return None

        expr = self.parse_expression()
        if expr is None:
            return None

        if self.consume(TOKEN_SYMBOL, ";") is None:
            return None

        return MathAssignmentNode(name, expr)

    def parse_output(self):
        """Parse: 'output' '<<' (STRING_LIT | expression) ';' """
        if self.consume(TOKEN_KEYWORD, "output") is None:
            return None
        if self.consume(TOKEN_SYMBOL, "<<") is None:
            return None

        # Check if output value is a string literal
        if self.peek_type() == TOKEN_STRING_LIT:
            str_tok = self.consume(TOKEN_STRING_LIT)
            value = StringNode(str_tok[1])
        else:
            value = self.parse_expression()
            if value is None:
                return None

        if self.consume(TOKEN_SYMBOL, ";") is None:
            return None

        return OutputNode(value)

    def parse_if(self):
        """Parse: 'if' '(' condition ')' statement """
        if self.consume(TOKEN_KEYWORD, "if") is None:
            return None
        if self.consume(TOKEN_SYMBOL, "(") is None:
            return None

        condition = self.parse_condition()
        if condition is None:
            return None

        if self.consume(TOKEN_SYMBOL, ")") is None:
            return None

        body = self.parse_statement()
        if body is None:
            return None

        return IfNode(condition, body)

    def parse_condition(self):
        """Parse: expression ('<'|'>'|'=='|'!=') expression """
        left = self.parse_expression()
        if left is None:
            return None

        tok = self.current()
        if tok[0] == TOKEN_OPERATOR and tok[1] in ("<", ">", "==", "!="):
            op = self.consume()[1]
        else:
            self.has_error = True
            return None

        right = self.parse_expression()
        if right is None:
            return None

        return ConditionNode(left, op, right)

    def parse_expression(self):
        """Parse: term (('+' | '-') term)*
        Handles addition and subtraction with left-to-right evaluation."""
        left = self.parse_term()
        if left is None:
            return None

        while (self.peek_type() == TOKEN_OPERATOR and
               self.peek_value() in ("+", "-")):
            op = self.consume()[1]
            right = self.parse_term()
            if right is None:
                return None
            left = BinOpNode(left, op, right)

        return left

    def parse_term(self):
        """Parse a single term: integer literal, double literal, or identifier."""
        tok_type, tok_val = self.current()

        if tok_type == TOKEN_INT_LIT:
            self.consume()
            return NumberNode(int(tok_val), "integer")

        if tok_type == TOKEN_DOUBLE_LIT:
            self.consume()
            return NumberNode(float(tok_val), "double")

        if tok_type == TOKEN_IDENTIFIER:
            self.consume()
            return IdentifierNode(tok_val)

        self.has_error = True
        return None


# ============================================================
# PROCEDURE 6 (Castillo): INTERPRETER (AST → Execution)
# ============================================================

# Executes the AST produced by the parser.
# Maintains a variable environment (dictionary) that stores
# each variable's declared type and current value.
# Called during PROCEDURE 6 (Castillo) - see main().
class Interpreter:
    """Executes the AST produced by the parser.

    Maintains a variable environment (dictionary) that stores
    each variable's declared type and current value.

    variables = {
        "x": {"type": "integer", "value": 5},
        "y": {"type": "double",  "value": 2.35},
    }
    """

    def __init__(self, ast):
        self.ast = ast
        self.variables = {}

    def run(self):
        """Execute all statements in the AST in order."""
        for node in self.ast:
            self.execute(node)

    def execute(self, node):
        """Execute a single AST node based on its type."""
        if isinstance(node, DeclarationNode):
            self.exec_declaration(node)
        elif isinstance(node, AssignmentNode):
            self.exec_assignment(node)
        elif isinstance(node, MathAssignmentNode):
            self.exec_math_assignment(node)
        elif isinstance(node, OutputNode):
            self.exec_output(node)
        elif isinstance(node, IfNode):
            self.exec_if(node)

    def exec_declaration(self, node):
        """Declare a variable with a default value of 0."""
        if node.var_type == "integer":
            self.variables[node.name] = {"type": "integer", "value": 0}
        elif node.var_type == "double":
            self.variables[node.name] = {"type": "double", "value": 0.0}

    def exec_assignment(self, node):
        """Assign a value using :="""
        value = self.evaluate(node.value_expr)
        if node.name in self.variables:
            var_info = self.variables[node.name]
            if var_info["type"] == "integer":
                var_info["value"] = int(value)
            else:
                var_info["value"] = float(value)
        else:
            # Variable not declared — store it anyway for basic execution
            self.variables[node.name] = {"type": "double", "value": float(value)}

    def exec_math_assignment(self, node):
        """Assign a value using = (expression result)"""
        value = self.evaluate(node.value_expr)
        if node.name in self.variables:
            var_info = self.variables[node.name]
            if var_info["type"] == "integer":
                var_info["value"] = int(value)
            else:
                var_info["value"] = float(value)
        else:
            self.variables[node.name] = {"type": "double", "value": float(value)}

    def exec_output(self, node):
        """Execute an output statement with type-aware formatting.
        If any operand in the expression is a double, the result is
        formatted with 2 decimal places; otherwise it prints as an integer."""
        if isinstance(node.value, StringNode):
            print(node.value.value)
        else:
            result = self.evaluate(node.value)
            has_double = _expr_has_double(node.value, self.variables)
            if has_double:
                print(f"{float(result):.2f}")
            else:
                print(int(result))

    def exec_if(self, node):
        """Execute a one-way if: evaluate condition, execute body if true."""
        if self.eval_condition(node.condition):
            self.execute(node.body)

    def evaluate(self, expr):
        """Evaluate an expression node and return its numeric value."""
        if isinstance(expr, NumberNode):
            return expr.value

        if isinstance(expr, IdentifierNode):
            if expr.name in self.variables:
                return self.variables[expr.name]["value"]
            else:
                # Undeclared variable — return 0
                return 0

        if isinstance(expr, BinOpNode):
            left_val = self.evaluate(expr.left)
            right_val = self.evaluate(expr.right)
            if expr.op == "+":
                return left_val + right_val
            elif expr.op == "-":
                return left_val - right_val

        return 0

    def eval_condition(self, cond):
        """Evaluate a condition node and return True or False."""
        left_val = self.evaluate(cond.left)
        right_val = self.evaluate(cond.right)

        if cond.op == "<":
            return left_val < right_val
        elif cond.op == ">":
            return left_val > right_val
        elif cond.op == "==":
            return left_val == right_val
        elif cond.op == "!=":
            return left_val != right_val

        return False


# ============================================================
# OUTPUT FORMATTING HELPERS
# ============================================================

# Determines if a result should be displayed as integer or double.
# Helper called during PROCEDURE 6 (Castillo) - interpretation.
def format_output(value, variables, expr_node):
    """Determine if a result should be displayed as integer or double.
    If any operand in the expression is a double, the result is double."""
    has_double = _expr_has_double(expr_node, variables)
    if has_double:
        return f"{float(value):.2f}"
    else:
        return str(int(value))


# Recursively checks if any part of an expression involves a double.
# Helper called during PROCEDURE 6 (Castillo) - interpretation.
def _expr_has_double(node, variables):
    """Recursively check if any part of an expression involves a double."""
    if isinstance(node, NumberNode):
        return node.num_type == "double"
    if isinstance(node, IdentifierNode):
        if node.name in variables:
            return variables[node.name]["type"] == "double"
        return False
    if isinstance(node, BinOpNode):
        return _expr_has_double(node.left, variables) or \
               _expr_has_double(node.right, variables)
    return False


# ============================================================
# MAIN — Tie all procedures together
# ============================================================

# Orchestrates PROCEDURES 1–7 (Castillo) in sequence:
# read source → remove spaces → tokenize → write RES_SYM.TXT →
# parse → report status → interpret if valid.
def main():
    # PROCEDURE 1 (Castillo): Read the .HL source file.
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("Enter source file name: ")
    lines = read_source(filename)

    # PROCEDURE 2 (Castillo): Remove spaces and write NOSPACES.TXT.
    cleaned_lines = remove_spaces(lines)
    write_nospaces(cleaned_lines)

    # PROCEDURE 3 (Castillo): Perform lexical analysis (tokenize the source).
    source_text = "\n".join(cleaned_lines)
    lexer = Lexer(source_text)
    tokens = lexer.tokenize()

    # PROCEDURE 4 (Castillo): Write reserved words and symbols to RES_SYM.TXT.
    write_res_sym(tokens)

    # PROCEDURE 5 (Castillo): Perform syntax analysis (parse tokens into AST).
    parser = Parser(tokens)
    ast = parser.parse_program()

    # PROCEDURE 7 (Castillo): Report ERROR or NO ERROR(S) FOUND.
    if lexer.has_error or parser.has_error:
        print("ERROR")
    else:
        print("NO ERROR(S) FOUND")
        # PROCEDURE 6 (Castillo): Interpret and execute the AST if no errors.
        interpreter = Interpreter(ast)
        interpreter.run()


if __name__ == "__main__":
    main()
