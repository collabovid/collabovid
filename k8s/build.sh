BASEDIR=$(dirname "$0")
OUTPUT_DIR="dist"

rm -rf ${BASEDIR}/${OUTPUT_DIR}

generate_config() {
  kustomize build ${BASEDIR}/overlays/$1 | kubesplit -o ${BASEDIR}/${OUTPUT_DIR}/$1 -p
  mkdir --parents ${BASEDIR}/${OUTPUT_DIR}/jobs/$1
  mkdir --parents ${BASEDIR}/${OUTPUT_DIR}/cronjobs/$1
  mv ${BASEDIR}/${OUTPUT_DIR}/$1/job* ${BASEDIR}/${OUTPUT_DIR}/jobs/$1/
  mv ${BASEDIR}/${OUTPUT_DIR}/$1/cronjob* ${BASEDIR}/${OUTPUT_DIR}/cronjobs/$1/
}

for config in "prod" "dev"
do
generate_config $config
done

