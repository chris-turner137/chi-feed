grammar = """
query : expr

?expr : or_expr

?or_expr  : or_expr "|" and_expr -> or
          | or_expr "or" and_expr -> or
          | and_expr

?and_expr : and_expr "&" not_expr -> and
          | and_expr "and" not_expr -> and
          | not_expr

?not_expr : "!" not_expr -> not
          | "not" not_expr -> not
          | cmp_expr

?cmp_expr : atom "==" atom -> eq
          | atom "!=" atom -> neq
          | atom ">" atom  -> gt
          | atom "<" atom  -> lt
          | atom ">=" atom -> geq
          | atom "<=" atom -> leq
          | atom

?atom : WORD
      | INT
      | PHRASE
      | "(" expr ")"

%import common.ESCAPED_STRING -> PHRASE
%import common.WORD
%import common.INT
%import common.WS_INLINE

%ignore WS_INLINE
"""
from lark import Lark

if __name__ == '__main__':
  l = Lark(grammar, parser='lalr', start='query')
  print(l.parse("A and B and not 12"))
  print(l.parse("year > 1915 and author == Turner"))
