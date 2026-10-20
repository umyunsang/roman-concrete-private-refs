
# roma_load — lib/*.py 파일을 Blender 모듈로 불러온다(파일이 원본, 텍스트 블록은 사본)
import bpy, sys, types, os, importlib
LIB = '/Users/um-yunsang/roman-concrete-private-refs/.work/blender/lib'
# roma_mats(옛 Principled·AO·범프 재질과 '받침 옆면' 지층 재질)는 공용으로 불러오지 않는다:
#   벡터 일러스트 규칙(조명·AO·Principled 0)과 팔각 받침 제거(사용자 06:06 "8각형 받침대 제거해")에 맞춘다. 파일은 그대로 둔다.
#   꼭 필요하면 load('roma_mats')로 따로 부른다(현재 쓰는 패키지 없음).
ORDER = ['roma_kit', 'roma_flat', 'roma_geo', 'roma_props', 'roma_layers', 'roma_colo', 'roma_colo_in']

def load(name):
    """lib/<name>.py를 읽어 같은 이름의 텍스트 블록과 sys.modules에 올린다"""
    path = os.path.join(LIB, name + '.py')
    src = open(path, encoding='utf-8').read()
    t = bpy.data.texts.get(name + '.py') or bpy.data.texts.new(name + '.py')
    t.clear(); t.write(src)
    mod = types.ModuleType(name); mod.__file__ = path
    exec(compile(src, path, 'exec'), mod.__dict__)
    sys.modules[name] = mod
    return mod

def load_all(extra=()):
    """공용 모듈(ORDER) + extra를 차례로 다시 불러온다. 같은 이름은 한 번만(b5 bglobal: 중복 불러오기 제거)"""
    out = {}
    for n in dict.fromkeys(list(ORDER) + list(extra)):
        if os.path.exists(os.path.join(LIB, n + '.py')):
            out[n] = load(n)
    return out
