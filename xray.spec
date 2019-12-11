# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

hidden_imports = [
#    'pygubu.builder.tkstdwidgets',
    'pygubu.builder.ttkstdwidgets',
#    'pygubu.builder.widgets.dialog',
#    'pygubu.builder.widgets.editabletreeview',
#    'pygubu.builder.widgets.scrollbarhelper',
    'pygubu.builder.widgets.scrolledframe',
#    'pygubu.builder.widgets.tkscrollbarhelper',
#    'pygubu.builder.widgets.tkscrolledframe',
#    'pygubu.builder.widgets.pathchooserinput',
    'pygubu.builder.widgets.combobox',
	'pygubu.builder.widgets.dialog',
    'PIL._tkinter_finder',
]

data_files = [
    ('xray.ui', '.'),
    ('images/xray/*.svg', 'images/xray'),
    ('images/plot/*', 'images/plot'),
]

onefile = False

a = Analysis(['xray.py'],
             pathex=['/home/falk/Schreibtisch/xray-windows/xray-tk'],
             binaries=[],
             datas=data_files,
             hiddenimports=hidden_imports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
if onefile:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              exclude_binaries=False,
              name='xray',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              console=True )
else:
    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='xray',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              console=True )
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   upx_exclude=[],
                   name='xray')
