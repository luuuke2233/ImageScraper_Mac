#!/bin/bash

cd "$(dirname "$0")"

APP_NAME="ImageScraper.app"

rm -rf "$APP_NAME"
mkdir -p "$APP_NAME/Contents/MacOS"

cat > "$APP_NAME/Contents/MacOS/ImageScraper" << 'SCRIPT'
#!/bin/bash
cd "$(dirname "$0")/../../.."
python3 main.py
SCRIPT

chmod +x "$APP_NAME/Contents/MacOS/ImageScraper"

cat > "$APP_NAME/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ImageScraper</string>
    <key>CFBundleIdentifier</key>
    <string>com.imagecrawler.app</string>
    <key>CFBundleName</key>
    <string>图片爬虫</string>
    <key>CFBundleDisplayName</key>
    <string>图片爬虫</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

echo "已创建 $APP_NAME"
echo "双击即可运行"
