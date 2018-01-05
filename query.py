grammar = """
query : expr

?expr : or_expr

?or_expr  : or_expr "|" and_expr
          | or_expr "or" and_expr
          | and_expr

?and_expr : and_expr "&" not_expr
          | and_expr "and" not_expr
          | not_expr

?not_expr : "!" not_expr
          | "not" not_expr
          | cmp_expr

?cmp_expr : atom "==" atom -> eq
          | atom "!=" atom -> neq
          | atom ">" atom  -> gt
          | atom "<" atom  -> lt
          | atom ">=" atom -> geq
          | atom "<=" atom -> leq
          | atom "in" atom -> in_expr
          | atom

?atom : WORD
      | INT -> integer
      | PHRASE
      | "(" expr ")"

%import common.ESCAPED_STRING -> PHRASE
%import common.WORD
%import common.INT
%import common.WS_INLINE

%ignore WS_INLINE
"""
from lark import Lark, Transformer

def get_parser():
  return Lark(grammar, parser='lalr', start='query')

class QueryLambdaTransformer(Transformer):
  """
  Transform the AST produced by lark-parser into a predicate for whether a
  provided object matches the query.
  """
  def query(self, s):
    return s[0]

  def eq(self, s):
    l, r = s
    return lambda x: x[l] == r

  def neq(self, s):
    l, r = s
    return lambda x: x[l] != r

  def lt(self, s):
    l, r = s
    return lambda x: x[l] < r

  def gt(self, s):
    l, r = s
    return lambda x: x[l] > r

  def leq(self, s):
    l, r = s
    return lambda x: x[l] <= r

  def geq(self, s):
    l, r = s
    return lambda x: x[l] >= r

  def integer(self, s):
    return int(s[0])

  def and_expr(self, s):
    l, r = s
    return lambda x: l(x) and r(x)

  def or_expr(self, s):
    l, r = s
    return lambda x: l(x) or r(x)

  def in_expr(self, s):
    l, r = s
    return lambda x: l in x[r]

if __name__ == '__main__':
  parser = get_parser()

  # Some sample queries
  q1 = "year == 2017 and authors == Foobar"
  q2 = "year > 1915 and Turner in authors"

  x = {'authors': 'C.J.Turner, Z.Papic', 'year': 2017, 'title': 'Abstract nonsense'}
  for q in [q1, q2]:
    tree = parser.parse(q)
    print(tree.pretty())
    predicate = QueryLambdaTransformer().transform(tree)
    print(predicate(x))
