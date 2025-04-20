# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('icons/bluecircle.ico', '.'),
        ('icons/star_white.svg', '.'),
        ('icons/star_white_filled.svg', '.'),
        ('icons/question.svg', '.'),
        ('icons/paypal.svg', '.'),
        ('icons/book.svg', '.'),
        ('icons/amazon_a.svg', '.'),
        ('icons/*.svg', 'icons'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ShittyLifePlanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='appico.ico',
    onefile=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ShittyLifePlanner')
