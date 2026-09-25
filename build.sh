#!/bin/bash

echo "[*] build started..."

rm -rf .target
mkdir -p .target

CSS="<style>
    body { font-family: monospace; background: #121212; color: #e0e0e0; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }
    h1, h2, h3 { color: #ffffff; }
    a { color: #5fb0fc; text-decoration: none; }
    pre { background: #1e1e1e; padding: 1rem; overflow-x: auto; border: 1px solid #333; }
    code { background: #2a2a2a; padding: 0.1rem 0.3rem; border-radius: 3px; }
</style>"

find . -type f -name "*.md" -not -path "*/\.*" | while read -r md_file; do
    
    dir_path=$(dirname -- "$md_file")
    base_name=$(basename -- "$md_file" .md)
    
    if [ "${base_name^^}" = "README" ] || [ "${base_name^^}" = "INDEX" ]; then
        base_name="index"
    fi
    
    target_dir=".target/${dir_path#./}"
    mkdir -p "$target_dir"
    
    html_file="$target_dir/$base_name.html"
    
    echo "  -> 컴파일 중: $md_file => $html_file"
    
    cat <<EOF > "$html_file"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$base_name - SysCross</title>
    $CSS
</head>
<body>
$(awk 'NR==1 && /^---/ {y=1; next} y && /^---/ {y=0; next} !y {print}' "$md_file" | cmark --unsafe)
</body>
</html>
EOF

done

echo "[*] build finished!"
