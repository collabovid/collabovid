function show_confirm_export_dialog() {
    return confirm('Please be aware that the ordering of the authors in the exported file might be incorrect. ' +
        'We are working hard to fix this issue and will release an updated version soon.');

}

$(document).on('click', '.export-dropdown a', function () {
    return show_confirm_export_dialog();
});