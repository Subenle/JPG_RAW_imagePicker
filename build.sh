#!/bin/bash
exeName="jpg_raw_imagePicker.exe"

clean_pyinstaller() {
    rm -rf build dist *.spec
    echo "清理完成: build、dist 目录和 .spec 文件已删除。"
}

clean_pyinstaller

pyinstaller --onefile --noconsole --windowed \
    --add-data "resources/weChat.JPEG;resources" \
    --add-data "resources/icon.ico;resources" \
    --icon="resources/icon.ico" \
    --name ${exeName} \
    main.py