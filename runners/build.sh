#!/bin/bash

# Usage: bash build.sh [--push] [ language ... ]

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function build_image {
    LANGUAGE=$1

    echo Building $LANGUAGE...
    docker build . -f $LANGUAGE/Dockerfile -t $OC_DOCKERIMAGE_BASE-$LANGUAGE-runner
    
}

cd $DIR

source ../open-contest.config

if [ "$1" == "--push" ]; then
    DOPUSH=1
    shift
fi

if [ $# -eq 0 ]; then
    echo "Rebuilding all images"
    LANGS=*
else
    LANGS=$*
fi

for LANG in $LANGS
do
    if [ -d $LANG ]; then
        build_image $LANG
        if [ "$DOPUSH" = 1 ]; then
            docker push $OC_DOCKERIMAGE_BASE-$LANG-runner
        fi
    fi
done
