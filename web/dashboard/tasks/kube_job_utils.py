import string
import random
from kubernetes import client, config
import kubernetes.client
from kubernetes.client.rest import ApiException


def create_job_object(name, container_image, command, args=None, namespace="default", container_name="jobcontainer",
                      env_vars=None, restart_policy='Never', ttl_finished=180, secret_names=None, backoff_limit=0):
    if env_vars is None:
        env_vars = {}
    if secret_names is None:
        secret_names = []
    if args is None:
        args = []

    body = client.V1Job(api_version="batch/v1", kind="Job")
    # metadata and status are required
    body.metadata = client.V1ObjectMeta(namespace=namespace, name=name)
    body.status = client.V1JobStatus()

    template = client.V1PodTemplate()
    template.template = client.V1PodTemplateSpec()

    # Set env variables
    env_list = []
    for env_name, env_value in env_vars.items():
        env_list.append(client.V1EnvVar(name=env_name, value=env_value))

    env_from = []
    for secret_name in secret_names:
        env_from.append(client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=secret_name)))

    # set container options
    container = client.V1Container(name=container_name, image=container_image, env=env_list,
                                   command=command, args=args, env_from=env_from)

    # set pod options
    template.template.spec = client.V1PodSpec(containers=[container], restart_policy=restart_policy)

    body.spec = client.V1JobSpec(ttl_seconds_after_finished=ttl_finished, template=template.template, backoff_limit=backoff_limit)
    return body


def run_job(job_object: client.V1Job):
    config.load_incluster_config()
    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(configuration))
    try:
        api_response = api_instance.create_namespaced_job("default", job_object, pretty=True)
        print(api_response)
    except ApiException as e:
        print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)
    return


def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
