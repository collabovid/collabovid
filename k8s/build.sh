output_dir=$(dirname "$0")/dist
path=$1
env=$2

kustomize build $path | kubesplit -o $output_dir/$env -p
rm -rf $output_dir/jobs/$env && mkdir -p $output_dir/jobs/$env
rm -rf $output_dir/cronobs/$env && mkdir -p $output_dir/cronjobs/$env
if [ "`echo $output_dir/$env/job*`" != "$output_dir/$env/job*" ]; then
    mv $output_dir/$env/job* $output_dir/jobs/$env/
fi
if [ "`echo $output_dir/$env/cronjob*`" != "$output_dir/$env/cronjob*" ]; then
    mv $output_dir/$env/cronjob* $output_dir/cronjobs/$env/
fi