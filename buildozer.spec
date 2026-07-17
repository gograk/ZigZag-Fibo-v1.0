[app]

# Informasi aplikasi
title = ZIGZAG_FIBO
package.name = zigzagfibo
package.domain = com.zigzagfibo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

# Entry point
entrypoint = main.py

# Dependensi Python
requirements = python3,kivy,requests,websocket-client,plyer

# Orientasi
orientation = portrait

# Android permission
android.permissions = INTERNET,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,VIBRATE,POST_NOTIFICATIONS

# Android SDK / NDK
android.minapi = 21
android.api = 33
android.ndk = 25b
android.ndk_api = 21
android.build_tools_version = 34.0.0
android.accept_sdk_license = True

# NDK
android.archs = arm64-v8a, armeabi-v7a

# Ikon APK
icon.filename = %(source.dir)s/icon.png
#presplash.filename = %(source.dir)s/presplash.png

android.allow_backup = True

# Fullscreen
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
