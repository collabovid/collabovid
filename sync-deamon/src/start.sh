(cd /app && /usr/local/bin/python sync.py)
for name in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY S3_HOST BUCKET AWS_BASE_DIR
do
  echo "export ${name}=${!name}" >> /app/envs
done
cron -f