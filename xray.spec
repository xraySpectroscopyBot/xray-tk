# -*- mode: python ; coding: utf-8 -*-

#Pack into single executable:
onefile = True
#Show console when launching executable
console = False


hidden_imports = [
#    'pygubu.builder.tkstdwidgets',
    'pygubu.builder.ttkstdwidgets',
#    'pygubu.builder.widgets.editabletreeview',
#    'pygubu.builder.widgets.scrollbarhelper',
    'pygubu.builder.widgets.scrolledframe',
#    'pygubu.builder.widgets.tkscrollbarhelper',
#    'pygubu.builder.widgets.tkscrolledframe',
#    'pygubu.builder.widgets.pathchooserinput',
    'pygubu.builder.widgets.combobox',
	'pygubu.builder.widgets.dialog',
    'PIL._tkinter_finder',
#	'scipy.special._ufuncs_cxx',
#	'scipy.interpolate',
#	'_ufuncs'
#	'scipy.interpolate.make_interp_spline',
#	'scipy.special._ufuncs_cxx',
#	'scipy.linalg.cython_blas',
#	'scipy.linalg.cython_lapack',
#	'scipy.integrate',
#	'scipy.integrate.quadrature',
#	'scipy.integrate.odepack',
#	'scipy.integrate._odepack',
#	'scipy.integrate.quadpack',
#	'scipy.integrate._quadpack',
#	'scipy.integrate._ode',
#	'scipy.integrate.vode',
#	'scipy.integrate._dop',
#	'scipy.integrate.lsoda',
    'pkg_resources.py2_warn'
]

data_files = [
    ('xray.ui', '.'),
    ('images/xray/*.svg', 'images/xray'),
    ('images/plot/*.svg', 'images/plot'),
]


block_cipher = None

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
              console=console,
              icon='images/icon.ico' )
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
              console=console,
              icon='images/icon.ico' )
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   upx_exclude=[],
                   name='xray')
