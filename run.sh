#!/usr/bin/env bash

VENV_PATH=venv

install_required() {
    pip install -r requirements.txt
    shasum -a 256 requirements.txt > ${VENV_PATH}/.installed
}


PYTHON=python3.8
${PYTHON} -c 'print()' >/dev/null 2>/dev/null || PYTHON=python3
${PYTHON} -c 'print()' >/dev/null 2>/dev/null || PYTHON=python

[ -d ${VENV_PATH} ] || ${PYTHON} -m venv ${VENV_PATH}

source ${VENV_PATH}/bin/activate

if [ -e ${VENV_PATH}/.installed ]; then
    shasum -a 256 -c ${VENV_PATH}/.installed >/dev/null 2>/dev/null || install_required
else
    install_required
fi

${PYTHON} script.py $@
