#!/bin/bash
exeName="jpg_raw_imagePicker"

clean_pyinstaller() {
    rm -rf build dist *.spec
    echo "清理完成: build、dist 目录和 .spec 文件已删除。"
}

clean_pyinstaller
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    onefileFlag="--onefile"
else
   onefileFlag=""
fi

pyinstaller --noconsole ${onefileFlag} --windowed \
    --add-data "resources/weChat.JPEG:resources" \
    --add-data "resources/icon.ico:resources" \
    --icon="resources/icon.ico" \
    --name ${exeName} \
    main.py