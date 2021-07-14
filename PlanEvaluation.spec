# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['PlanEvaluation.py'],
             pathex=['I:\\'],
             binaries=[],
             datas=[('.\\Data', 'Data'), ('.\\DVH Files', 'DVH Files'), ('.\\Icons', 'Icons'), ('.\\Output', 'Output'), ('PlanEvaluationConfig.xml', '.')],
             hiddenimports=['tkinter', 'scipy.spatial.transform._rotation_groups'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='PlanEvaluation',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='Icons\\Chart_Graph_Ascending.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='PlanEvaluation')
