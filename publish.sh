
if [ $# -eq 0 ]; then
    msg="sync"
else
    msg="$@"
fi

git add .

git commit -am "$msg"

git pull

sh build.sh

git add .

git commit -am "$msg"

git push
