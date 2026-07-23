import difflib

def do_diff(f1, f2):
    try:
        lines1 = open(f1, encoding='utf-8').readlines()
        lines2 = open(f2, encoding='utf-8').readlines()
        return list(difflib.unified_diff(lines1, lines2, fromfile=f1, tofile=f2))
    except Exception as e:
        return [f"Error diffing {f1} and {f2}: {str(e)}\n"]

diffs = do_diff('inventory.py', r'..\JUEGO LUIS - NUEVAS IMPLEMENTACIONES\JUEGO\inventory.py')
diffs += do_diff('loot.py', r'..\JUEGO LUIS - NUEVAS IMPLEMENTACIONES\JUEGO\loot.py')
diffs += do_diff('achievements.py', r'..\JUEGO LUIS - NUEVAS IMPLEMENTACIONES\JUEGO\achievements.py')

open('diff_output.txt', 'w', encoding='utf-8').writelines(diffs)
