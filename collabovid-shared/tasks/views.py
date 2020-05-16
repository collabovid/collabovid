from django.http import JsonResponse, HttpResponseNotFound

from tasks.definitions import SERVICE_TASKS, SERVICE_TASK_DEFINITIONS, PrimitivesHelper
from tasks.task_runner import TaskRunner

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def start_task(request, task_id):

    if request.method == "POST":

        definition = SERVICE_TASK_DEFINITIONS[task_id]

        started_by = request.POST.get("started_by")

        if not started_by:
            return HttpResponseNotFound()

        task_arguments = {
            "started_by": started_by
        }

        for parameter in definition['parameters']:
            name = parameter['name']

            if parameter['is_primitive']:

                if parameter['required'] and name not in request.POST:
                    return HttpResponseNotFound()

                if parameter['type'] == 'bool':

                    if name in request.POST:
                        task_arguments[name] = True
                    else:
                        task_arguments[name] = False
                else:

                    default = None
                    if not parameter["required"]:
                        default = parameter['default']

                    task_arguments[name] = PrimitivesHelper.convert(parameter['type'],
                                                                    request.POST.get(name, default))
        task_cls = SERVICE_TASKS[task_id]
        task = TaskRunner.run_task_async(task_cls, **task_arguments)

        return JsonResponse({"task": task.pk})

    return HttpResponseNotFound()

