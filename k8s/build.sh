BASEDIR=$(dirname "$0")
OUTPUT_DIR="dist"

rm -rf ${BASEDIR}/${OUTPUT_DIR}

generate_config() {
  kustomize build $1 | kubesplit -o ${BASEDIR}/${OUTPUT_DIR}/$2 -p
  mkdir --parents ${BASEDIR}/${OUTPUT_DIR}/jobs/$2
  mkdir --parents ${BASEDIR}/${OUTPUT_DIR}/cronjobs/$2
  mv ${BASEDIR}/${OUTPUT_DIR}/$2/job* ${BASEDIR}/${OUTPUT_DIR}/jobs/$2/
  mv ${BASEDIR}/${OUTPUT_DIR}/$2/cronjob* ${BASEDIR}/${OUTPUT_DIR}/cronjobs/$2/
}

generate_config $1 $2
