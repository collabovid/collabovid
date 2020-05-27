let deletionTaskId = -1;
$('#modal').on('show.bs.modal', function (event) {
    let button = $(event.relatedTarget);
    deletionTaskId = button.data('id');
});
$('#modal-delete-btn').click(function () {
    console.log(deletionTaskId);
    let input = $("<input>")
        .attr("type", "hidden")
        .attr("name", "id").val(deletionTaskId);
    let form = $('#delete-form');
    form.append(input);
    form.submit();
});
