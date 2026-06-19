#cd /mnt/user-data/outputs && python3 -c "
import ast
for f in ['app.py', 'agent.py']:
    with open(f) as fh:
        code = fh.read()
    try:
        ast.parse(code)
        print(f'{f}: Syntax OK')
    except SyntaxError as e:
        print(f'{f}: Syntax error:', e)
#"
