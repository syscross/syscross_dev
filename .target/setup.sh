
git clone https://github.com/jackyzha0/quartz .ignore/quartz

cd .ignore/quartz

npm i

cat << 'EOF' >> quartz/styles/custom.scss
div.explorer { display: none; }
h1.article-title { display: none; }
p.content-meta { display: none; }
div.markdown-rendered {
  font-family: "Noto Sans Mono CJK JP", monospace;
}
EOF
