# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Auto-updater
        'updater',
        # PySimpleGUI dependency
        'pydoc',
        # Selenium
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.common.by',
        'selenium.webdriver.common.action_chains',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        # WebDriver Manager
        'webdriver_manager',
        'webdriver_manager.chrome',
        'webdriver_manager.core.utils',
        'webdriver_manager.core.driver_cache',
        # Requests
        'requests',
        'requests.adapters',
        'requests.packages',
        'urllib3',
        'certifi',
        'charset_normalizer',
        # Win10Toast
        'win10toast',
        # PySimpleGUI
        'PySimpleGUI',
        # Standart lib
        'threading',
        'uuid',
        'hashlib',
        'base64',
        're',
        'json',
        # xml (pkg_resources dependency)
        'xml',
        'xml.etree',
        'xml.etree.ElementTree',
        'xml.etree.ElementPath',
        'xml.etree.ElementInclude',
        'xml.parsers',
        'xml.parsers.expat',
        'xml.dom',
        'xml.dom.minidom',
        'xml.sax',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MaybachBot_v3_new',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
)
