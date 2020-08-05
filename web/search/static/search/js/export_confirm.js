window.show_confirm_export_dialog = function(){
    return confirm('Please be aware that the entries are generated automatically and might contain minor errors.');

};

$(document).on('click', '.export-dropdown a', function () {
    return window.show_confirm_export_dialog();
});